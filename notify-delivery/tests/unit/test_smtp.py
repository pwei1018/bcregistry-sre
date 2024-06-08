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
import json
from http import HTTPStatus
from unittest.mock import patch

import pytest
from notify_api.models.notification import Notification, NotificationSendResponses
from notify_api.models.notification_history import NotificationHistory
from simple_cloudevent import SimpleCloudEvent, to_queue_message

from notify_delivery.resources.email_smtp import process_message
from notify_delivery.services.providers.email_smtp import EmailSMTP
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


CLOUD_EVENT_ENVELOPE = {
    "subscription": "projects/PUBSUB_PROJECT_ID/subscriptions/SUBSCRIPTION_ID",
    "message": {
        "data": base64.b64encode(to_queue_message(CLOUD_EVENT)).decode("UTF-8"),
        "messageId": "10",
        "attributes": {},
    },
    "id": 1,
}


def test_invalid_endpoints(client_smtp):
    """Return a 4xx when endpoint is invalid."""
    rv = client_smtp.post("/")
    assert rv.status_code == HTTPStatus.NOT_FOUND

    rv = client_smtp.post("")
    assert rv.status_code == HTTPStatus.NOT_FOUND

    rv = client_smtp.post("/smt")
    assert rv.status_code == HTTPStatus.NOT_FOUND

    rv = client_smtp.post("/smtp/test")
    assert rv.status_code == HTTPStatus.NOT_FOUND

    rv = client_smtp.post("/gcnotify")
    assert rv.status_code == HTTPStatus.NOT_FOUND


def test_without_jwt(client_smtp, mocker):
    """Return a 4xx when jwt."""
    rv = client_smtp.post("/smtp")
    assert rv.status_code == HTTPStatus.UNAUTHORIZED


def test_no_message(client_smtp, mocker):
    """Return a 4xx when an no JSON present."""
    mocker.patch("notify_delivery.services.gcp_queue.gcp_auth.verify_jwt", return_value="")
    rv = client_smtp.post("/smtp")

    assert rv.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    "test_name,queue_envelope,expected",
    [("invalid", {}, HTTPStatus.OK), ("valid", CLOUD_EVENT_ENVELOPE, HTTPStatus.OK)],
)
def test_worker_smtp(client_smtp, test_name, queue_envelope, expected, mocker):
    """Test cloud event"""
    mocker.patch("notify_delivery.services.gcp_queue.gcp_auth.verify_jwt", return_value="")
    rv = client_smtp.post("/smtp", json=CLOUD_EVENT_ENVELOPE)
    assert rv.status_code == expected


def test_process_message(session):
    """Test process_message function."""
    data: dict = NotificationFactory.RequestProviderData.REQUEST_PROVIDER_5

    responses = NotificationSendResponses(recipients=[NotificationFactory.SendResponseData.SEND_RESPONSE])
    with (patch.object(EmailSMTP, "send", return_value=responses),):
        history: NotificationHistory = process_message(data)

        assert history is not None
        assert history.recipients == json.loads(data["notificationRequest"])["recipients"]


def test_process_message_no_response(session):
    """Test process_message function with no response from provider."""
    data: dict = NotificationFactory.RequestProviderData.REQUEST_PROVIDER_5

    with (patch.object(EmailSMTP, "send", return_value=None),):
        result: Notification = process_message(data)
        assert result is not None
        assert result.status_code == Notification.NotificationStatus.FAILURE


def test_process_message_no_request_data(session):
    """Test process_message function that notification data not exist."""
    data: dict = NotificationFactory.RequestProviderData.REQUEST_PROVIDER_6

    with pytest.raises(Exception) as exception:
        process_message(data)

    assert exception.value.args[0] == "Notification data not found."

    data: dict = NotificationFactory.RequestProviderData.REQUEST_PROVIDER_6_1

    with pytest.raises(Exception) as exception:
        process_message(data)

    assert exception.value.args[0] == "Notification data not found."


def test_process_message_no_provider(session):
    """Test process_message function that provider not exist."""
    data: dict = NotificationFactory.RequestProviderData.REQUEST_PROVIDER_7

    with pytest.raises(Exception) as exception:
        process_message(data)

    assert exception.value.args[0] == "Notification provider not found."

    data: dict = NotificationFactory.RequestProviderData.REQUEST_PROVIDER_7_1

    with pytest.raises(Exception) as exception:
        process_message(data)

    assert exception.value.args[0] == "Notification provider not found."


def test_process_message_wrong_provider(session):
    """Test process_message function that provider is incorrect."""
    data: dict = NotificationFactory.RequestProviderData.REQUEST_PROVIDER_8

    with pytest.raises(Exception) as exception:
        process_message(data)

    assert exception.value.args[0] == "Notification provider is incorrect."
