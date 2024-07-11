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
"""This provides the service for email notify calls."""
import uuid
import warnings
from datetime import datetime, timezone

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from flask import current_app
from simple_cloudevent import SimpleCloudEvent

from notify_api.models import Notification, NotificationHistory, NotificationRequest, SafeList
from notify_api.services.gcp_queue import GcpQueue, queue
from notify_api.utils.logging import logger

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)


class NotifyService:
    """Provides services to manages notification."""

    def __init__(self):
        """Return a Notification service instance."""

    @classmethod
    def get_provider(cls, notify_type: str, content_body: str) -> str:
        """Get the notify service provider."""
        if notify_type == Notification.NotificationType.TEXT:
            # Send TEXT through GC Notify
            return Notification.NotificationProvider.GC_NOTIFY

        # Send email through GC Notify if email body is not html
        if not bool(BeautifulSoup(content_body, "html.parser").find()):
            return Notification.NotificationProvider.GC_NOTIFY

        return Notification.NotificationProvider.SMTP

    def queue_publish(self, notification_request: NotificationRequest) -> Notification:
        """Send the notification."""
        notification: Notification = Notification.create_notification(notification_request)

        provider: str = self.get_provider(notification_request.notify_type, notification_request.content.body)

        notification_status: str = Notification.NotificationStatus.QUEUED
        is_safe_to_send = True

        # Email must set in safe list of Dev and Test environment
        if current_app.config.get("DEVELOPMENT"):
            recipients = [
                r.strip()
                for r in notification_request.recipients.split(",")
                if SafeList.is_in_safe_list(r.lower().strip())
            ]
            unsafe_recipients = [r for r in notification_request.recipients.split(",") if r.strip() not in recipients]
            if unsafe_recipients:
                logger.info(f"{unsafe_recipients} are not in the safe list")
            if not recipients:
                is_safe_to_send = False
            else:
                notification_request.recipients = ",".join(recipients)

        if is_safe_to_send:
            deliery_topic = current_app.config.get("NOTIFY_DELIVERY_GCNOTIFY_TOPIC")
            data = {
                "notificationId": notification.id,
            }

            if provider == Notification.NotificationProvider.SMTP:
                deliery_topic = current_app.config.get("NOTIFY_DELIVERY_SMTP_TOPIC")
                data = {
                    "notificationId": notification.id,
                    "notificationProvider": provider,
                    "notificationRequest": notification_request.model_dump_json(),
                }

            cloud_event = SimpleCloudEvent(
                id=str(uuid.uuid4()),
                source="notify-api",
                subject=None,
                time=datetime.now(tz=timezone.utc).isoformat(),
                type=f"bc.registry.notify.{provider}",
                data=data,
            )

            publish_future = queue.publish(deliery_topic, GcpQueue.to_queue_message(cloud_event))
            logger.info(publish_future)

        notification.status_code = notification_status
        notification.provider_code = provider
        notification.sent_date = datetime.now(timezone.utc)
        notification.update_notification()

        if not is_safe_to_send or provider == Notification.NotificationProvider.SMTP:
            # recipint is not in the safe list (dev or test);
            # SMTP service handle by OpenShift;
            if provider == Notification.NotificationProvider.SMTP:
                notification.status_code = Notification.NotificationStatus.FORWARDED
            notification_history: NotificationHistory = NotificationHistory.create_history(notification)
            notification.delete_notification()
            return notification_history

        return notification

    def queue_republish(self):
        """Republish notifications to queue."""
        notifications = Notification.find_resend_notifications()

        for notification in notifications:

            deliery_topic = current_app.config.get("NOTIFY_DELIVERY_GCNOTIFY_TOPIC")
            data = {
                "notificationId": notification.id,
            }

            cloud_event = SimpleCloudEvent(
                id=str(uuid.uuid4()),
                source="notify-api",
                subject=None,
                time=datetime.now(tz=timezone.utc).isoformat(),
                type=f"bc.registry.notify.{notification.provider_code}",
                data=data,
            )

            publish_future = queue.publish(deliery_topic, GcpQueue.to_queue_message(cloud_event))
            logger.info(publish_future)

            notification.status_code = Notification.NotificationStatus.QUEUED
            notification.update_notification()
