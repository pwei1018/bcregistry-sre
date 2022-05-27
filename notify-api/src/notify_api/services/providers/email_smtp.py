# Copyright © 2022 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This provides send email through SMTP."""
import logging
import re
import smtplib
import unicodedata
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app

from notify_api.errors import BadGatewayException
from notify_api.models import Notification


logger = logging.getLogger(__name__)


class EmailSMTP:  # pylint: disable=too-few-public-methods
    """Send emails via SMTP."""

    def __init__(self, notification: Notification):
        """Construct object."""
        self.mail_server = current_app.config.get('MAIL_SERVER')
        self.mail_port = current_app.config.get('MAIL_PORT')
        self.mail_from_id = current_app.config.get('MAIL_FROM_ID')
        self.mail_debug = current_app.config.get('MAIL_DEBUG')
        self.notification = notification

    def send(self):
        """Send message."""
        try:
            encoding = 'utf-8'
            message = MIMEMultipart()
            message['Subject'] = self.notification.content[0].subject
            message['From'] = self.mail_from_id
            message['To'] = self.notification.recipients
            message.attach(MIMEText(self.notification.content[0].body, 'html', encoding))

            if self.notification.content[0].attachments:
                for attachment in self.notification.content[0].attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.file_bytes)
                    encode_base64(part)

                    spaces = re.compile(r'[\s]+', re.UNICODE)
                    filename = unicodedata.normalize('NFKD', attachment.file_name)
                    filename = filename.encode('ascii', 'ignore').decode('ascii')
                    filename = spaces.sub(' ', filename).strip()

                    try:
                        filename and filename.encode('ascii')
                    except UnicodeEncodeError:
                        filename = ('UTF8', '', filename)

                    part.add_header('Content-Disposition', 'attachment; filename=' + filename)

                    message.attach(part)

            server = smtplib.SMTP(host=self.mail_server, port=self.mail_port)
            server.set_debuglevel(self.mail_debug)
            server.sendmail(message['From'], [message['To']], message.as_string())
            server.quit()

        except Exception as err:  # pylint: disable=broad-except # noqa F841;
            logger.error('Email SMTP Error: %s', err)
            raise BadGatewayException(error=f'Email SMTP Error {err}') from err
        return True
