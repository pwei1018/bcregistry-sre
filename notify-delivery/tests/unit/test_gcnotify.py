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
import base64
from http import HTTPStatus
from unittest.mock import patch

import pytest
from notify_api.models.notification import Notification, NotificationSendResponses
from notify_api.models.notification_history import NotificationHistory
from simple_cloudevent import SimpleCloudEvent, to_queue_message

from notify_delivery.resources.gc_notify import process_message
from notify_delivery.services.providers.gc_notify import GCNotify
from tests.factories.notification import ContentFactory, NotificationFactory

CLOUD_EVENT = SimpleCloudEvent(
    id="fake-id",
    source="fake-for-tests",
    subject="fake-subject",
    type="fake-type",
    data={
        "notificationId": "29590",
    },
)

#
# This needs to mimic the envelope created by GCP PubSb when call a resource
#
CLOUD_EVENT_ENVELOPE = {
    "subscription": "projects/PUBSUB_PROJECT_ID/subscriptions/SUBSCRIPTION_ID",
    "message": {
        "data": base64.b64encode(to_queue_message(CLOUD_EVENT)).decode("UTF-8"),
        "messageId": "10",
        "attributes": {},
    },
    "id": 1,
}


def test_invalid_endpoints(client):
    """Return a 4xx when endpoint is invalid"""
    rv = client.post("/")
    assert rv.status_code == HTTPStatus.NOT_FOUND

    rv = client.post("")
    assert rv.status_code == HTTPStatus.NOT_FOUND

    rv = client.post("/smtp")
    assert rv.status_code == HTTPStatus.NOT_FOUND

    rv = client.post("/gcno")
    assert rv.status_code == HTTPStatus.NOT_FOUND

    rv = client.post("/gcnotify/test")
    assert rv.status_code == HTTPStatus.NOT_FOUND


def test_no_message(client):
    """Return a 4xx when an no JSON present."""
    rv = client.post("/gcnotify")
    assert rv.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    "test_name,queue_envelope,expected",
    [("invalid", {}, HTTPStatus.OK), ("valid", CLOUD_EVENT_ENVELOPE, HTTPStatus.OK)],
)
def test_worker_gcnotify(client, test_name, queue_envelope, expected):
    """Test cloud event"""
    rv = client.post("/gcnotify", json=CLOUD_EVENT_ENVELOPE)
    assert rv.status_code == expected


def test_process_message(session):
    """Test process_message function."""
    notification: Notification = NotificationFactory.create_model(
        session, NotificationFactory.RequestProviderData.REQUEST_PROVIDER_4["data"]
    )

    ContentFactory.create_model(
        session, notification.id, NotificationFactory.RequestProviderData.REQUEST_PROVIDER_1["data"]["content"]
    )

    notification.status_code = Notification.NotificationStatus.QUEUED
    notification.provider_code = Notification.NotificationProvider.GC_NOTIFY
    notification.update_notification()

    data: dict = {"notificationId": notification.id}

    responses = NotificationSendResponses(recipients=[NotificationFactory.SendResponseData.SEND_RESPONSE])
    with (patch.object(GCNotify, "send", return_value=responses),):
        history: NotificationHistory = process_message(data)

        assert history is not None
        assert history.recipients == NotificationFactory.RequestProviderData.REQUEST_PROVIDER_4["data"]["recipients"]


def test_process_message_no_response(session):
    """Test process_message function with no response from provider."""
    notification: Notification = NotificationFactory.create_model(
        session, NotificationFactory.RequestProviderData.REQUEST_PROVIDER_4["data"]
    )

    ContentFactory.create_model(
        session, notification.id, NotificationFactory.RequestProviderData.REQUEST_PROVIDER_1["data"]["content"]
    )

    notification.status_code = Notification.NotificationStatus.QUEUED
    notification.provider_code = Notification.NotificationProvider.GC_NOTIFY
    notification.update_notification()

    data: dict = {"notificationId": notification.id}

    with (patch.object(GCNotify, "send", return_value=None),):
        result: Notification = process_message(data)
        assert result is not None
        assert result.status_code == Notification.NotificationStatus.FAILURE


def test_process_message_id_not_exist_exception(session):
    """Test process_message function that notification not exist."""
    notification_id = 3333
    data: dict = {"notificationId": notification_id}

    with pytest.raises(Exception) as exception:
        process_message(data)

    assert exception.value.args[0] == f"Unknown notification for notificationId {notification_id}"

    notification_id = ""
    data: dict = {"notificationId": notification_id}

    with pytest.raises(Exception) as exception:
        process_message(data)

    assert exception.value.args[0] == f"Unknown notification for notificationId {notification_id}"


def test_process_message_status_code_exception(session):
    """Test process_message function that notify status is not QUEUED."""
    notification: Notification = NotificationFactory.create_model(
        session, NotificationFactory.RequestProviderData.REQUEST_PROVIDER_4["data"]
    )

    ContentFactory.create_model(
        session, notification.id, NotificationFactory.RequestProviderData.REQUEST_PROVIDER_1["data"]["content"]
    )

    notification.status_code = Notification.NotificationStatus.PENDING
    notification.provider_code = Notification.NotificationProvider.GC_NOTIFY
    notification.update_notification()

    data: dict = {"notificationId": notification.id}

    with pytest.raises(Exception) as exception:
        process_message(data)

    assert exception.value.args[0] == f"Notification status is not {notification.status_code}"
