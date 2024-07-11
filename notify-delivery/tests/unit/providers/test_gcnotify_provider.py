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
"""The Test Suites to ensure that the gc notify provider is operating correctly."""
from unittest.mock import patch

from notifications_python_client.errors import HTTPError
from notify_api.models import Attachment, Content, Notification, NotificationSendResponses

from notify_delivery.services.providers.gc_notify import GCNotify


class TestGCNotify:  # pylint: disable=unsubscriptable-object
    """
    Unit tests for the GCNotify provider.
    """

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_email(self, mock_client):
        """
        Test sending an email notification.
        """
        # Mock the mock_client response
        mock_client.return_value.send_email_notification.return_value = {
            "id": "some_id",
            "reference": "some_reference",
        }

        # Create a test notification
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 1
        assert response.recipients[0].recipient == "test@example.com"
        assert response.recipients[0].response_id == "some_id"

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_email_with_attachments(self, mock_client):
        """
        Test sending an email notification with attachments.
        """
        # Mock the mock_client response
        mock_client.return_value.send_email_notification.return_value = {
            "id": "some_id",
            "reference": "some_reference",
        }

        # Create a test notification with attachments
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[
                        Attachment(file_name="test.txt", file_bytes=b"This is a test file.", attach_order="1")
                    ],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 1
        assert response.recipients[0].recipient == "test@example.com"
        assert response.recipients[0].response_id == "some_id"

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_multiple_recipients(self, mock_client):
        """
        Test sending a notification to multiple recipients.
        """
        # Mock the mock_client response
        mock_client.return_value.send_email_notification.return_value = {
            "id": "some_id",
            "reference": "some_reference",
        }

        # Create a test notification with multiple recipients
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test1@example.com,test2@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 2
        assert response.recipients[0].recipient == "test1@example.com"
        assert response.recipients[0].response_id == "some_id"
        assert response.recipients[1].recipient == "test2@example.com"
        assert response.recipients[1].response_id == "some_id"

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_error(self, mock_client):
        """
        Test handling errors during notification sending.
        """
        # Mock the mock_client to raise an exception
        mock_client.return_value.send_email_notification.side_effect = HTTPError(
            response={"status": 400, "body": "Test Error"}
        )

        # Create a test notification
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_invalid_template_id(self, mock_client):
        """
        Test handling errors when an invalid template ID is provided.
        """
        # Mock the mock_client to raise an exception
        mock_client.return_value.send_email_notification.side_effect = HTTPError(
            response={"status": 400, "body": "Invalid template ID"}
        )

        # Create a test notification
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_invalid_email_address(self, mock_client):
        """
        Test handling errors when an invalid email address is provided.
        """
        # Mock the mock_client to raise an exception
        mock_client.return_value.send_email_notification.side_effect = HTTPError(
            response={"status": 400, "body": "Invalid email address"}
        )

        # Create a test notification
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_invalid_personalisation(self, mock_client):
        """
        Test handling errors when invalid personalisation data is provided.
        """
        # Mock the mock_client to raise an exception
        mock_client.return_value.send_email_notification.side_effect = HTTPError(
            response={"status": 400, "body": "Invalid personalisation"}
        )

        # Create a test notification
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_invalid_reply_to_id(self, mock_client):
        """
        Test handling errors when an invalid reply-to ID is provided.
        """
        # Mock the mock_client to raise an exception
        mock_client.return_value.send_email_notification.side_effect = HTTPError(
            response={"status": 400, "body": "Invalid reply-to ID"}
        )

        # Create a test notification
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_invalid_api_key(self, mock_client):
        """
        Test handling errors when an invalid API key is provided.
        """
        # Mock the mock_client to raise an exception
        mock_client.return_value.send_email_notification.side_effect = HTTPError(
            response={"status": 401, "body": "Invalid API key"}
        )

        # Create a test notification
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_invalid_base_url(self, mock_client):
        """
        Test handling errors when an invalid base URL is provided.
        """
        # Mock the mock_client to raise an exception
        mock_client.return_value.send_email_notification.side_effect = HTTPError(
            response={"status": 400, "body": "Invalid base URL"}
        )

        # Create a test notification
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_connection_error(self, mock_client):
        """
        Test handling connection errors during notification sending.
        """
        # Mock the mock_client to raise an exception
        mock_client.return_value.send_email_notification.side_effect = ConnectionError("Connection error")

        # Create a test notification
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_timeout_error(self, mock_client):
        """
        Test handling timeout errors during notification sending.
        """
        # Mock the mock_client to raise an exception
        mock_client.return_value.send_email_notification.side_effect = TimeoutError("Timeout error")

        # Create a test notification
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_unknown_error(self, mock_client):
        """
        Test handling unknown errors during notification sending.
        """
        # Mock the mock_client to raise an exception
        mock_client.return_value.send_email_notification.side_effect = Exception("Unknown error")

        # Create a test notification
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the GCNotify service
        gc_notify = GCNotify(notification)

        # Call the send method
        response = gc_notify.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0
