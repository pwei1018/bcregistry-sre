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
"""The Unit Test for the attachment model."""
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from notify_api.models.attachment import Attachment, AttachmentRequest
from tests.factories.attachment import AttachmentFactory
from tests.factories.content import ContentFactory
from tests.factories.notification import NotificationFactory


def test_attachment_validation():
    """Assert the test attachment model vaildation."""
    for bad_data in list(AttachmentFactory.RequestBadData):
        with pytest.raises(ValidationError) as exc_info:
            AttachmentRequest(**bad_data)

        assert exc_info.value.errors()

def test_create_attachment(session):
    """Assert the test can create attachment."""
    notification = NotificationFactory.create_model(session, notification_info=NotificationFactory.Models.PENDING_1)
    content =ContentFactory.create_model(session, notification.id, content_info=ContentFactory.Models.CONTENT_1)

    request_attachment: AttachmentRequest = AttachmentRequest(**AttachmentFactory.Models.FILE_1)

    result = Attachment.create_attachment(request_attachment, content_id=content.id)

    assert result.file_name == AttachmentFactory.Models.FILE_1['fileName']
    assert result.json['fileName'] == AttachmentFactory.Models.FILE_1['fileName']

def test_create_attachment_with_url(session):
    """Assert the test can create attachment with url."""
    notification = NotificationFactory.create_model(session, notification_info=NotificationFactory.Models.PENDING_1)
    content =ContentFactory.create_model(session, notification.id, content_info=ContentFactory.Models.CONTENT_1)

    request_attachment: AttachmentRequest = AttachmentRequest(**AttachmentFactory.Models.FILE_2)

    result = Attachment.create_attachment(request_attachment, content_id=content.id)

    assert result.file_name == AttachmentFactory.Models.FILE_2['fileName']
    assert result.json['fileName'] == AttachmentFactory.Models.FILE_2['fileName']

def test_create_attachment_exception(app, session):  # pylint: disable=unused-argument
    """Assert the test can create attachment with Exception."""

    with patch('base64.b64decode', side_effect=Exception('mocked error')):
        with pytest.raises(Exception) as exception:
            notification = NotificationFactory.create_model(session, notification_info=NotificationFactory.Models.PENDING_1)
            content =ContentFactory.create_model(session, notification.id, content_info=ContentFactory.Models.CONTENT_1)
            request_attachment: AttachmentRequest = AttachmentRequest(**AttachmentFactory.Models.FILE_1)
            Attachment.create_attachment(request_attachment, content_id=content.id)

        assert exception.value.error == 'Create attachment record Error mocked error'
