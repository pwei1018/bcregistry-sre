# Copyright © 2024 Province of British Columbia
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
"""Worker resource to handle incoming queue pushes from gcp."""
import sys
from datetime import datetime, timezone
from http import HTTPStatus

from flask import Blueprint, request
from notify_api.models import Notification, NotificationHistory, NotificationRequest, NotificationSendResponses
from notify_api.services.gcp_queue import queue
from notify_api.utils.logging import logger

from notify_delivery.services.gcp_queue.gcp_auth import ensure_authorized_queue_user
from notify_delivery.services.providers import _all_providers  # noqa: E402

bp = Blueprint("smtp", __name__)


@bp.route("/", methods=("POST",))
@ensure_authorized_queue_user
def worker():
    """Worker to handle incoming queue pushes."""
    if not request.data:
        logger.info("No incoming raw msg.")
        return {}, HTTPStatus.OK

    if not (ce := queue.get_simple_cloud_event(request, wrapped=True)):
        # Return a 200, so event is removed from the Queue
        logger.info("No incoming cloud event msg.")
        return {}, HTTPStatus.OK

    try:
        logger.info(f"Event Message Received: {ce}")
        if ce.type == "bc.registry.notify.smtp":
            process_message(ce.data)
        else:
            raise Exception("Invalid queue message type")  # pylint: disable=broad-exception-raised

        logger.info(f"Event Message Proccessd: {ce.id}")
        return {}, HTTPStatus.OK
    except Exception:  # pylint: disable=broad-exception-caught
        logger.error(f"Failed to process queue message: {sys.exc_info()}")
        # Optionally, return an error status code or message
        return {}, HTTPStatus.OK


def process_message(data: dict) -> NotificationHistory | Notification:
    """Delivery message through GC Notify service."""
    history: NotificationHistory = None

    if "notificationRequest" not in data or not data["notificationRequest"]:
        raise Exception("Notification data not found.")  # pylint: disable=broad-exception-raised

    if "notificationProvider" not in data or not data["notificationProvider"]:
        raise Exception("Notification provider not found.")  # pylint: disable=broad-exception-raised

    notification_data = data["notificationRequest"]
    notification_provider = data["notificationProvider"]

    if notification_provider != Notification.NotificationProvider.SMTP:
        raise Exception("Notification provider is incorrect.")  # pylint: disable=broad-exception-raised

    # create notificaiton record in OCP database
    notification_request = NotificationRequest.model_validate_json(notification_data)
    notification: Notification = Notification.create_notification(notification_request)
    notification.status_code = Notification.NotificationStatus.SENT
    notification.provider_code = notification_provider
    notification.sent_date = datetime.now(timezone.utc)
    notification.update_notification()

    responses: NotificationSendResponses = _all_providers[notification.provider_code](notification).send()

    if responses:
        for response in responses.recipients:
            # save to history as per recipient
            history = NotificationHistory.create_history(notification, response.recipient, response.response_id)

        # clean notification record
        notification.delete_notification()
    else:
        notification.status_code = Notification.NotificationStatus.FAILURE
        notification.update_notification()

        return notification

    return history
