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

"""The Unit Test for the Notification Model."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from notify_api.models.notification import Notification, NotificationRequest
from tests.factories.notification import NotificationFactory


def test_notification_validation():
    """Assert the test notification model vaildation."""
    for bad_data in list(NotificationFactory.RequestBadData):
        with pytest.raises(ValidationError) as exc_info:
            NotificationRequest(**bad_data)

        assert exc_info.value.errors()

def test_find_notification_by_id(session):
    """Assert the test can retrieve notification by id."""
    notification = NotificationFactory.create_model(session)

    result = Notification.find_notification_by_id(notification.id)

    assert result.recipients == NotificationFactory.Models.PENDING_1['recipients']

    result = Notification.find_notification_by_id(None)

    assert result is None

def test_find_notification_by_status(session):
    """Assert the test can retrieve notifications by status."""
    notification = NotificationFactory.create_model(session)

    result = Notification.find_notifications_by_status(notification.status_code)

    assert result[0].recipients == NotificationFactory.Models.PENDING_1['recipients']

    result = Notification.find_notifications_by_status(None)

    assert result is None

def test_create_notification(session):  # pylint: disable=unused-argument
    """Assert the test can create notification."""
    result = Notification.create_notification(NotificationRequest(**NotificationFactory.RequestData.REQUEST_1))
    assert result.recipients == NotificationFactory.RequestData.REQUEST_1['recipients']

def test_update_notification(session):
    """Assert the test can update notification."""
    notification = NotificationFactory.create_model(session)

    notification.sent_date = datetime.now()
    notification.status_code = Notification.NotificationStatus.FAILURE
    result = Notification.update_notification(notification)
    assert result == notification
    assert result.recipients == NotificationFactory.Models.PENDING_1['recipients']
    assert result.status_code == Notification.NotificationStatus.FAILURE
