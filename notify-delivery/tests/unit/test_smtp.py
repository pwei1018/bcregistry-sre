# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Test Suites to ensure that the worker is operating correctly."""
import unittest
from http import HTTPStatus
from unittest.mock import patch

import pytest
from notify_api.models import (
    Content,
    ContentRequest,
    Notification,
    NotificationRequest,
    NotificationSendResponse,
    NotificationSendResponses,
)
from simple_cloudevent import SimpleCloudEvent

from notify_delivery.resources.email_smtp import process_message


@pytest.mark.usefixtures("client_smtp")
class TestEmailSMTP(unittest.TestCase):
    """Test Email SMTP worker."""

    # pylint: disable=no-member

    def test_invalid_endpoints(self):
        """Return a 4xx when endpoint is invalid"""
        response = self.client.post("/")
        assert response.status_code == HTTPStatus.NOT_FOUND

        response = self.client.post("")
        assert response.status_code == HTTPStatus.NOT_FOUND

        response = self.client.post("/gcnotify")
        assert response.status_code == HTTPStatus.NOT_FOUND

        response = self.client.post("/smto")
        assert response.status_code == HTTPStatus.NOT_FOUND

        response = self.client.post("/smtp/test")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_without_jwt(self):
        """Return a 4xx when jwt."""
        response = self.client.post("/smtp")
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @patch("notify_delivery.services.gcp_queue.gcp_auth.verify_jwt")
    @patch("notify_delivery.resources.email_smtp.process_message")
    def test_worker_no_data(self, mock_process_message, mock_verify_jwt):
        """Test worker with no data."""
        mock_verify_jwt.return_value = None
        response = self.client.post("/smtp", data=None)
        assert response.status_code == HTTPStatus.OK
        mock_process_message.assert_not_called()

    @patch("notify_delivery.services.gcp_queue.gcp_auth.verify_jwt")
    @patch("notify_delivery.resources.email_smtp.queue.get_simple_cloud_event")
    def test_worker_no_cloud_event(self, mock_get_simple_cloud_event, mock_verify_jwt):
        """Test worker with no cloud event."""
        mock_verify_jwt.return_value = None
        mock_get_simple_cloud_event.return_value = None
        response = self.client.post("/smtp", data="{}")
        assert response.status_code == HTTPStatus.OK
        mock_get_simple_cloud_event.assert_called_once()

    @patch("notify_delivery.services.gcp_queue.gcp_auth.verify_jwt")
    @patch("notify_delivery.resources.email_smtp.queue.get_simple_cloud_event")
    @patch("notify_delivery.resources.email_smtp.process_message")
    def test_worker_valid_event(self, mock_process_message, mock_get_simple_cloud_event, mock_verify_jwt):
        """Test worker with valid cloud event."""
        mock_verify_jwt.return_value = None
        mock_get_simple_cloud_event.return_value = SimpleCloudEvent(
            type="bc.registry.notify.smtp",
            data={"notificationRequest": "test_notification_request", "notificationProvider": "SMTP"},
        )
        response = self.client.post("/smtp", data="{}")
        assert response.status_code == HTTPStatus.OK
        mock_process_message.assert_called_once_with(
            {"notificationRequest": "test_notification_request", "notificationProvider": "SMTP"}
        )

    @patch("notify_delivery.services.gcp_queue.gcp_auth.verify_jwt")
    @patch("notify_delivery.resources.email_smtp.queue.get_simple_cloud_event")
    @patch("notify_delivery.resources.email_smtp.process_message")
    def test_worker_invalid_event_type(self, mock_process_message, mock_get_simple_cloud_event, mock_verify_jwt):
        """Test worker with invalid cloud event type."""
        mock_verify_jwt.return_value = None
        mock_get_simple_cloud_event.return_value = SimpleCloudEvent(
            type="invalid.event.type",
            data={"notificationRequest": "test_notification_request", "notificationProvider": "SMTP"},
        )
        response = self.client.post("/smtp", data="{}")
        assert response.status_code == HTTPStatus.OK
        mock_process_message.assert_not_called()

    @patch("notify_delivery.resources.email_smtp.NotificationRequest.model_validate_json")
    @patch("notify_delivery.resources.email_smtp.Notification.create_notification")
    def test_process_message_no_notification_data(self, mock_create_notification, mock_model_validate_json):
        """Test process_message with no notification data."""
        mock_model_validate_json.return_value = None
        with pytest.raises(Exception) as e:
            process_message({"notificationRequest": None, "notificationProvider": "SMTP"})
        assert str(e.value) == "Notification data not found."

    @patch("notify_delivery.resources.email_smtp.NotificationRequest.model_validate_json")
    @patch("notify_delivery.resources.email_smtp.Notification.create_notification")
    def test_process_message_no_notification_provider(self, mock_create_notification, mock_model_validate_json):
        """Test process_message with no notification provider."""
        mock_model_validate_json.return_value = None
        with pytest.raises(Exception) as e:
            process_message({"notificationRequest": "test_notification_request", "notificationProvider": None})
        assert str(e.value) == "Notification provider not found."

    @patch("notify_delivery.resources.email_smtp.NotificationRequest.model_validate_json")
    @patch("notify_delivery.resources.email_smtp.Notification.create_notification")
    def test_process_message_invalid_notification_provider(self, mock_create_notification, mock_model_validate_json):
        """Test process_message with invalid notification provider."""
        mock_model_validate_json.return_value = None
        with pytest.raises(Exception) as e:
            process_message({"notificationRequest": "test_notification_request", "notificationProvider": "INVALID"})
        assert str(e.value) == "Notification provider is incorrect."

    @patch("notify_delivery.resources.email_smtp.EmailSMTP.send")
    @patch("notify_delivery.resources.email_smtp.NotificationRequest.model_validate_json")
    @patch("notify_delivery.resources.email_smtp.Notification.create_notification")
    @patch("notify_delivery.resources.email_smtp.NotificationHistory.create_history")
    @patch("notify_delivery.resources.email_smtp.Notification.update_notification")
    @patch("notify_delivery.resources.email_smtp.Notification.delete_notification")
    def test_process_message_success(
        self,
        mock_delete_notification,
        mock_update_notification,
        mock_create_history,
        mock_create_notification,
        mock_model_validate_json,
        mock_send,
    ):
        """Test process_message with successful notification delivery."""
        notification_request = NotificationRequest(
            content=[
                ContentRequest(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="abc@gmail.com",
        )
        mock_model_validate_json.return_value = notification_request
        mock_create_notification.return_value = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="abc@gmail.com",
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )
        mock_send.return_value = NotificationSendResponses(
            recipients=[NotificationSendResponse(recipient="abc@gmail.com", response_id="some_id")]
        )
        process_message({"notificationRequest": "test_notification_request", "notificationProvider": "smtp"})
        mock_model_validate_json.assert_called_once_with("test_notification_request")
        mock_create_notification.assert_called_once()
        mock_send.assert_called_once()
        mock_update_notification.assert_called_once()
        mock_create_history.assert_called_once_with(mock_create_notification.return_value, "abc@gmail.com", "some_id")
        mock_delete_notification.assert_called_once()

    @patch("notify_delivery.resources.email_smtp.EmailSMTP.send")
    @patch("notify_delivery.resources.email_smtp.NotificationRequest.model_validate_json")
    @patch("notify_delivery.resources.email_smtp.Notification.create_notification")
    @patch("notify_delivery.resources.email_smtp.Notification.update_notification")
    def test_process_message_failure(
        self,
        mock_update_notification,
        mock_create_notification,
        mock_model_validate_json,
        mock_send,
    ):
        """Test process_message with failed notification delivery."""
        notification_request = NotificationRequest(
            content=[
                ContentRequest(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="abc@gmail.com",
        )
        mock_model_validate_json.return_value = notification_request
        mock_create_notification.return_value = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="abc@gmail.com",
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )
        mock_send.return_value = None
        result = process_message({"notificationRequest": "test_notification_request", "notificationProvider": "smtp"})
        mock_model_validate_json.assert_called_once_with("test_notification_request")
        mock_create_notification.assert_called_once()
        mock_send.assert_called_once()
        assert mock_update_notification.call_count == 2
        assert isinstance(result, Notification)
        assert result.status_code == Notification.NotificationStatus.FAILURE

    @patch("notify_delivery.resources.email_smtp.EmailSMTP.send")
    @patch("notify_delivery.resources.email_smtp.NotificationRequest.model_validate_json")
    @patch("notify_delivery.resources.email_smtp.Notification.create_notification")
    @patch("notify_delivery.resources.email_smtp.Notification.update_notification")
    def test_process_message_with_error(
        self,
        mock_update_notification,
        mock_create_notification,
        mock_model_validate_json,
        mock_send,
    ):
        """Test process_message with error during notification delivery."""
        notification_request = NotificationRequest(
            content=[
                ContentRequest(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="abc@gmail.com",
        )
        mock_model_validate_json.return_value = notification_request
        mock_create_notification.return_value = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="abc@gmail.com",
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )
        mock_send.side_effect = Exception("Test Error")
        with pytest.raises(Exception):
            result = process_message(
                {"notificationRequest": "test_notification_request", "notificationProvider": "smtp"}
            )
            mock_model_validate_json.assert_called_once_with("test_notification_request")
            mock_create_notification.assert_called_once()
            mock_send.assert_called_once()
            mock_update_notification.assert_called_once()
            assert isinstance(result, Notification)
            assert result.status_code == Notification.NotificationStatus.FAILURE
