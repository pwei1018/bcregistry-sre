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
from notify_api.models import Content, Notification, NotificationSendResponse, NotificationSendResponses
from simple_cloudevent import SimpleCloudEvent

from notify_delivery.resources.gc_notify import process_message


@pytest.mark.usefixtures("client")
class TestGCNotify(unittest.TestCase):
    """Test GC Notify worker."""

    # pylint: disable=no-member

    def test_invalid_endpoints(self):
        """Return a 4xx when endpoint is invalid"""
        rv = self.client.post("/")
        assert rv.status_code == HTTPStatus.NOT_FOUND

        rv = self.client.post("")
        assert rv.status_code == HTTPStatus.NOT_FOUND

        rv = self.client.post("/smtp")
        assert rv.status_code == HTTPStatus.NOT_FOUND

        rv = self.client.post("/gcno")
        assert rv.status_code == HTTPStatus.NOT_FOUND

        rv = self.client.post("/gcnotify/test")
        assert rv.status_code == HTTPStatus.NOT_FOUND

    @patch("notify_delivery.resources.gc_notify.process_message")
    def test_worker_no_data(self, mock_process_message):
        """Test worker with no data."""
        response = self.client.post("/gcnotify", data=None)
        assert response.status_code == HTTPStatus.OK
        mock_process_message.assert_not_called()

    @patch("notify_delivery.resources.gc_notify.queue.get_simple_cloud_event")
    def test_worker_no_cloud_event(self, mock_get_simple_cloud_event):
        """Test worker with no cloud event."""
        mock_get_simple_cloud_event.return_value = None
        response = self.client.post("/gcnotify", data="{}")
        assert response.status_code == HTTPStatus.OK
        mock_get_simple_cloud_event.assert_called_once()

    @patch("notify_delivery.resources.gc_notify.queue.get_simple_cloud_event")
    @patch("notify_delivery.resources.gc_notify.process_message")
    def test_worker_valid_event(self, mock_process_message, mock_get_simple_cloud_event):
        """Test worker with valid cloud event."""
        mock_get_simple_cloud_event.return_value = SimpleCloudEvent(
            type="bc.registry.notify.gc_notify",
            data={"notificationId": "test_notification_id"},
        )
        response = self.client.post("/gcnotify", data="{}")
        assert response.status_code == HTTPStatus.OK
        mock_process_message.assert_called_once_with({"notificationId": "test_notification_id"})

    @patch("notify_delivery.resources.gc_notify.queue.get_simple_cloud_event")
    @patch("notify_delivery.resources.gc_notify.process_message")
    def test_worker_invalid_event_type(self, mock_process_message, mock_get_simple_cloud_event):
        """Test worker with invalid cloud event type."""
        mock_get_simple_cloud_event.return_value = SimpleCloudEvent(
            type="invalid.event.type",
            data={"notificationId": "test_notification_id"},
        )
        response = self.client.post("/gcnotify", data="{}")
        assert response.status_code == HTTPStatus.OK
        mock_process_message.assert_not_called()

    @patch("notify_delivery.resources.gc_notify.Notification.find_notification_by_id")
    def test_process_message_unknown_notification(self, mock_find_notification_by_id):
        """Test process_message with unknown notification."""
        mock_find_notification_by_id.return_value = None
        with pytest.raises(Exception) as e:
            process_message({"notificationId": "test_notification_id"})
        assert str(e.value) == "Unknown notification for notificationId test_notification_id"

    @patch("notify_delivery.resources.gc_notify.Notification.find_notification_by_id")
    def test_process_message_invalid_notification_status(self, mock_find_notification_by_id):
        """Test process_message with invalid notification status."""
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
            status_code=Notification.NotificationStatus.SENT,
        )
        mock_find_notification_by_id.return_value = notification
        with pytest.raises(Exception) as e:
            process_message({"notificationId": "test_notification_id"})
        assert str(e.value) == "Notification status is not sent"

    @patch("notify_delivery.services.providers.gc_notify.GCNotify.send")
    @patch("notify_delivery.resources.gc_notify.Notification.find_notification_by_id")
    @patch("notify_delivery.resources.gc_notify.NotificationHistory.create_history")
    @patch("notify_delivery.resources.gc_notify.Notification.update_notification")
    @patch("notify_delivery.resources.gc_notify.Notification.delete_notification")
    def test_process_message_success(
        self,
        mock_delete_notification,
        mock_update_notification,
        mock_create_history,
        mock_find_notification_by_id,
        mock_send,
    ):
        """Test process_message with successful notification delivery."""
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code="test_provider",
        )
        mock_find_notification_by_id.return_value = notification
        mock_send.return_value = NotificationSendResponses(
            recipients=[NotificationSendResponse(recipient="test@example.com", response_id="some_id")]
        )
        process_message({"notificationId": "test_notification_id"})
        mock_find_notification_by_id.assert_called_once_with("test_notification_id")
        mock_send.assert_called_once()
        mock_update_notification.assert_called_once()
        mock_create_history.assert_called_once_with(notification, "test@example.com", "some_id")
        mock_delete_notification.assert_called_once()

    @patch("notify_delivery.services.providers.gc_notify.GCNotify.send")
    @patch("notify_delivery.resources.gc_notify.Notification.find_notification_by_id")
    @patch("notify_delivery.resources.gc_notify.Notification.update_notification")
    def test_process_message_failure(self, mock_update_notification, mock_find_notification_by_id, mock_send):
        """Test process_message with failed notification delivery."""
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                )
            ],
            recipients="test@example.com",
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code="GC_NOTIFY",
        )
        mock_find_notification_by_id.return_value = notification
        mock_send.return_value = None
        result = process_message({"notificationId": "test_notification_id"})
        mock_find_notification_by_id.assert_called_once_with("test_notification_id")
        mock_send.assert_called_once()
        mock_update_notification.assert_called_once()
        assert isinstance(result, Notification)
        assert result.status_code == Notification.NotificationStatus.FAILURE
