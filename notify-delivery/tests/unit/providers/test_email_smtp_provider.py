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
"""The Test Suites to ensure that the smtp provider is operating correctly."""
import smtplib
import unittest
from unittest.mock import patch

from notify_api.models import Attachment, Content, Notification, NotificationSendResponses

from notify_delivery.services.providers.email_smtp import EmailSMTP


class TestEmailSMTP(unittest.TestCase):  # pylint: disable=unsubscriptable-object
    """
    Unit tests for the EmailSMTP provider.
    """

    @patch("smtplib.SMTP")
    def test_send_email(self, mock_client):
        """
        Test sending an email notification.
        """
        # Mock the SMTP server response
        mock_client.return_value.sendmail.return_value = None
        mock_client.return_value.connect.return_value = None
        mock_client.return_value.quit.return_value = None

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

        # Initialize the EmailSMTP service
        email_smtp = EmailSMTP(notification)

        # Call the send method
        response = email_smtp.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 1
        assert response.recipients[0].recipient == "test@example.com"
        assert response.recipients[0].response_id is None

    @patch("smtplib.SMTP")
    def test_send_email_with_attachments(self, mock_client):
        """
        Test sending an email notification with attachments.
        """
        # Mock the SMTP server response
        mock_client.return_value.sendmail.return_value = None
        mock_client.return_value.connect.return_value = None
        mock_client.return_value.quit.return_value = None

        # Create a test notification with attachments
        notification = Notification(
            content=[
                Content(
                    subject="Test Subject",
                    body="Test Body",
                    attachments=[Attachment(file_name="test.txt", file_bytes=b"This is a test file.")],
                )
            ],
            recipients="test@example.com",
        )

        # Initialize the EmailSMTP service
        email_smtp = EmailSMTP(notification)

        # Call the send method
        response = email_smtp.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 1
        assert response.recipients[0].recipient == "test@example.com"
        assert response.recipients[0].response_id is None

    @patch("smtplib.SMTP")
    def test_send_email_with_multiple_recipients(self, mock_client):
        """
        Test sending an email notification to multiple recipients.
        """
        # Mock the SMTP server response
        mock_client.return_value.sendmail.return_value = None
        mock_client.return_value.connect.return_value = None
        mock_client.return_value.quit.return_value = None

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

        # Initialize the EmailSMTP service
        email_smtp = EmailSMTP(notification)

        # Call the send method
        response = email_smtp.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 2
        assert response.recipients[0].recipient == "test1@example.com"
        assert response.recipients[0].response_id is None
        assert response.recipients[1].recipient == "test2@example.com"
        assert response.recipients[1].response_id is None

    @patch("smtplib.SMTP")
    def test_send_email_with_error(self, mock_client):
        """
        Test handling errors during email sending.
        """
        # Mock the SMTP server to raise an exception
        mock_client.return_value.sendmail.side_effect = smtplib.SMTPException("Test Error")
        mock_client.return_value.connect.return_value = None
        mock_client.return_value.quit.return_value = None

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

        # Initialize the EmailSMTP service
        email_smtp = EmailSMTP(notification)

        # Call the send method
        response = email_smtp.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0

    @patch("smtplib.SMTP")
    def test_send_email_with_connection_error(self, mock_client):
        """
        Test handling connection errors during email sending.
        """
        # Mock the SMTP server to raise an exception
        mock_client.return_value.connect.side_effect = smtplib.SMTPException("Connection Error")
        mock_client.return_value.quit.return_value = None

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

        # Initialize the EmailSMTP service
        email_smtp = EmailSMTP(notification)

        # Call the send method
        response = email_smtp.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0

    @patch("smtplib.SMTP")
    def test_send_email_with_quit_error(self, mock_client):
        """
        Test handling quit errors during email sending.
        """
        # Mock the SMTP server to raise an exception
        mock_client.return_value.connect.return_value = None
        mock_client.return_value.quit.side_effect = smtplib.SMTPException("Quit Error")

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

        # Initialize the EmailSMTP service
        email_smtp = EmailSMTP(notification)

        # Call the send method
        response = email_smtp.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 1

    @patch("smtplib.SMTP")
    def test_send_email_with_unknown_error(self, mock_client):
        """
        Test handling unknown errors during email sending.
        """
        # Mock the SMTP server to raise an exception
        mock_client.return_value.sendmail.side_effect = Exception("Unknown Error")
        mock_client.return_value.connect.return_value = None
        mock_client.return_value.quit.return_value = None

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

        # Initialize the EmailSMTP service
        email_smtp = EmailSMTP(notification)

        # Call the send method
        response = email_smtp.send()

        # Assert the response
        assert isinstance(response, NotificationSendResponses)
        assert len(response.recipients) == 0
