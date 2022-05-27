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
"""The Unit Test for the content model."""
import pytest
from pydantic import ValidationError

from notify_api.models.content import Content, ContentRequest
from tests.factories.attachment import AttachmentFactory
from tests.factories.content import ContentFactory
from tests.factories.notification import NotificationFactory


def test_content_validation():
    """Assert the test content model vaildation."""
    for bad_data in list(ContentFactory.RequestBadData):
        with pytest.raises(ValidationError) as exc_info:
            ContentRequest(**bad_data)

        assert exc_info.value.errors()

def test_create_content(session):
    """Assert the test can create notification contents."""
    notification = NotificationFactory.create_model(session, notification_info=NotificationFactory.Models.PENDING_1)

    request_content: ContentRequest = ContentRequest(**ContentFactory.RequestData.CONTENT_REQUEST_1)

    result = Content.create_content(request_content, notification_id=notification.id)

    assert result.json['subject'] == ContentFactory.RequestData.CONTENT_REQUEST_1['subject']
    assert result.subject == ContentFactory.RequestData.CONTENT_REQUEST_1['subject']


def test_create_content_with_attachment(session):
    """Assert the test can create notification contents with attachment."""
    notification = NotificationFactory.create_model(session, notification_info=NotificationFactory.Models.PENDING_1)

    request_content: ContentRequest = ContentRequest(**ContentFactory.RequestData.CONTENT_REQUEST_2)

    result = Content.create_content(request_content, notification_id=notification.id)

    assert result.json['subject'] == ContentFactory.RequestData.CONTENT_REQUEST_2['subject']
    assert result.subject == ContentFactory.RequestData.CONTENT_REQUEST_2['subject']
    assert result.attachments[0].file_name == AttachmentFactory.RequestData.FILE_REQUEST_1['fileName']


def test_create_content_with_attachment_url(session):
    """Assert the test can create notification contents with attachment url."""
    notification = NotificationFactory.create_model(session, notification_info=NotificationFactory.Models.PENDING_1)

    request_content: ContentRequest = ContentRequest(**ContentFactory.RequestData.CONTENT_REQUEST_3)

    result = Content.create_content(request_content, notification_id=notification.id)

    assert result.json['subject'] == ContentFactory.RequestData.CONTENT_REQUEST_3['subject']
    assert result.subject == ContentFactory.RequestData.CONTENT_REQUEST_3['subject']
    assert result.attachments[0].file_name == AttachmentFactory.RequestData.FILE_REQUEST_1['fileName']
    assert result.attachments[1].file_name == AttachmentFactory.RequestData.FILE_REQUEST_2['fileName']


def test_update_content(session):
    """Assert the test can update content."""
    notification = NotificationFactory.create_model(session, notification_info=NotificationFactory.Models.PENDING_1)

    content = ContentFactory.create_model(session, notification.id, content_info=ContentFactory.Models.CONTENT_1)

    content.body = ''
    result = Content.update_content(content)

    assert result.body == ''
