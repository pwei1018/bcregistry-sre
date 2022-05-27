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
"""The Unit Test for the API."""
from http import HTTPStatus
from unittest.mock import patch

from notify_api.errors import NotifyException
from notify_api.services.notify_service import NotifyService
from notify_api.utils.enums import Role
from tests.factories.content import ContentFactory
from tests.factories.jwt import create_header
from tests.factories.notification import NotificationFactory


def test_invaild_roles(session, app, client, jwt):  # pylint: disable=unused-argument
    """Assert the test the role validation."""
    headers = create_header(jwt, [Role.INVALID.value], **{'Accept-Version':'v1'})
    res = client.get('/api/v1/notify/1', headers=headers)
    assert res.status_code == HTTPStatus.UNAUTHORIZED

    headers = create_header(jwt, [Role.INVALID.value], **{'Accept-Version':'v1'})
    res = client.get('/api/v1/notify/status/1', headers=headers)
    assert res.status_code == HTTPStatus.UNAUTHORIZED

    headers = create_header(jwt, [Role.INVALID.value], **{'Accept-Version':'v1'})
    res = client.post('/api/v1/notify/', headers=headers)
    assert res.status_code == HTTPStatus.UNAUTHORIZED

    # verify public_user can post notification
    headers = create_header(jwt, [Role.PUBLIC_USER.value], **{'Accept-Version':'v1'})
    res = client.post('/api/v1/notify/', headers=headers)
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_find_by_invaild_input(session, app, client, jwt):  # pylint: disable=unused-argument
    """Assert the test can retrieve notification details with status."""
    headers = create_header(jwt, [Role.SYSTEM.value], **{'Accept-Version':'v1'})
    res = client.get('/api/v1/notify/status/pending123', headers=headers)
    assert res.status_code == HTTPStatus.BAD_REQUEST

    res = client.get('/api/v1/notify/status/', headers=headers)
    assert res.status_code == HTTPStatus.BAD_REQUEST

    res = client.get('/api/v1/notify/status', headers=headers)
    assert res.status_code == HTTPStatus.BAD_REQUEST

    res = client.get('/api/v1/notify/', headers=headers)
    assert res.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    res = client.get('/api/v1/notify', headers=headers)
    assert res.status_code == HTTPStatus.METHOD_NOT_ALLOWED

def test_find_by_id(session, app, client, jwt):  # pylint: disable=unused-argument
    """Assert the test can retrieve notification details by id."""
    notification = NotificationFactory.create_model(session, notification_info=NotificationFactory.Models.PENDING_1)
    ContentFactory.create_model(session, notification.id, content_info=ContentFactory.Models.CONTENT_1)

    headers = create_header(jwt, [Role.SYSTEM.value], **{'Accept-Version':'v1'})

    res = client.get(f'/api/v1/notify/{notification.id}', headers=headers)
    assert res.status_code == HTTPStatus.OK
    assert res.json['recipients'] == NotificationFactory.Models.PENDING_1['recipients']
    assert res.json['content']['subject'] == ContentFactory.Models.CONTENT_1['subject']

def test_get_by_id_no_token(session, app, client):  # pylint: disable=unused-argument
    """Assert the test cannot retrieve notification details with no token."""
    notification = NotificationFactory.create_model(session)

    res = client.get(f'/api/v1/notify/{notification}')
    assert res.status_code == HTTPStatus.UNAUTHORIZED

def test_find_by_id_not_found(session, app, client, jwt):  # pylint: disable=unused-argument
    """Assert the test cannot retrieve notification details with id not existing."""
    headers = create_header(jwt, [Role.SYSTEM.value], **{'Accept-Version':'v1'})
    res = client.get(f'/api/v1/notify/{int(1000)}', headers=headers)
    assert res.status_code == HTTPStatus.NOT_FOUND

def test_find_by_status(session, app, client, jwt):  # pylint: disable=unused-argument
    """Assert the test can retrieve notification details with status."""
    notification = NotificationFactory.create_model(session, notification_info=NotificationFactory.Models.PENDING_1)
    ContentFactory.create_model(session, notification.id, content_info=ContentFactory.Models.CONTENT_1)

    headers = create_header(jwt, [Role.SYSTEM.value], **{'Accept-Version':'v1'})
    res = client.get('/api/v1/notify/status/PENDING', headers=headers)
    assert res.status_code == HTTPStatus.OK
    assert len(res.json.get('notifications')) == 1
    assert res.json['notifications'][0]['recipients'] == NotificationFactory.Models.PENDING_1['recipients']
    assert res.json['notifications'][0]['content']['subject'] == ContentFactory.Models.CONTENT_1['subject']

def test_find_by_status_zero(session, app, client, jwt):  # pylint: disable=unused-argument
    """Assert the test can retrieve notification details with status."""
    notification = NotificationFactory.create_model(session, notification_info=NotificationFactory.Models.LESS_1_HOUR)
    ContentFactory.create_model(session, notification.id, content_info=ContentFactory.Models.CONTENT_1)

    headers = create_header(jwt, [Role.SYSTEM.value], **{'Accept-Version':'v1'})
    res = client.get('/api/v1/notify/status/pending', headers=headers)
    assert res.status_code == HTTPStatus.OK
    assert len(res.json.get('notifications')) == 0

def test_send_email(session, app, client, jwt, monkeypatch):  # pylint: disable=unused-argument, too-many-arguments
    """Assert the test can create notification."""
    headers = create_header(jwt, [Role.SYSTEM.value], **{'Accept-Version':'v1'})
    for notification_data in list(NotificationFactory.RequestData):
        notification = NotificationFactory.create_model(session, notification_info=notification_data)
        ContentFactory.create_model(session, notification.id, content_info=notification_data['content'])

        with patch.object(NotifyService, 'notify', return_value=notification):
            res = client.post('/api/v1/notify', json=notification_data, headers=headers)
            assert res.status_code == HTTPStatus.OK
            assert notification_data['recipients'] == res.json['recipients']
            assert notification_data['content']['subject'] ==res.json['content']['subject']

def test_send_email_with_bad_data(session, app, jwt, client):  # pylint: disable=unused-argument
    """Assert the test can not be create notification."""
    headers = create_header(jwt, [Role.SYSTEM.value], **{'Accept-Version':'v1'})
    for notification_data in list(NotificationFactory.RequestBadData):
        res = client.post('/api/v1/notify/', json=notification_data, headers=headers)
        assert res.status_code == HTTPStatus.BAD_REQUEST

def test_send_email_exception(session, app, jwt, client):  # pylint: disable=unused-argument
    """Assert the test can not be create notification."""
    with patch.object(NotifyService, 'notify', side_effect=NotifyException(error='mocked error',status_code=500)):
        headers = create_header(jwt, [Role.SYSTEM.value], **{'Accept-Version':'v1'})
        res = client.post('/api/v1/notify/', json=NotificationFactory.RequestData.REQUEST_1, headers=headers)
        assert res.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
