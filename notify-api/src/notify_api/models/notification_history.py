# Copyright © 2019 Province of British Columbia
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
"""Notification data model."""
from datetime import datetime

from .notification import Notification
from .db import db  # noqa: I001


class NotificationHistory(db.Model):
    """Immutable Notification History record. Represents Notification History."""

    __tablename__ = 'notification_history'

    id = db.Column(db.Integer, primary_key=True)
    recipients = db.Column(db.String(2000), nullable=False)
    request_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=True)
    request_by = db.Column(db.String(100), nullable=True)
    sent_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=True)
    subject = db.Column(db.String(2000), nullable=False)
    type_code = db.Column(db.String(15), nullable=False)
    status_code = db.Column(db.String(15), nullable=False)
    provider_code = db.Column(db.String(15), nullable=False)
    gc_notify_response_id = db.Column(db.String, nullable=True)
    gc_notify_status = db.Column(db.String, nullable=True)

    @property
    def json(self) -> dict:
        """Return a dict of this object, with keys in JSON format."""
        history_json = {
            'id': self.id,
            'recipients': self.recipients,
            'requestDate': self.request_date.isoformat(),
            'requestBy': self.request_by,
            'sentDate': self.request_date.isoformat(),
            'subject': self.subject,
            'notifyType': self.type_code,
            'notifyStatus': self.status_code,
            'notifyProvider': self.provider_code,
            'gc_notify_response_id': self.gc_notify_response_id,
            'gc_notify_status': self.gc_notify_status,
        }

        return history_json

    @classmethod
    def create_history(cls, notification: Notification, recipient: str = None, response_id: str = None):
        """Create notification."""
        db_history = NotificationHistory(recipients=recipient if recipient else notification.recipients,
                                         request_date=notification.request_date,
                                         request_by=notification.request_by,
                                         sent_date=notification.sent_date,
                                         subject=notification.content[0].subject,
                                         type_code=notification.type_code.upper(),
                                         status_code=notification.status_code.upper(),
                                         provider_code=notification.provider_code.upper(),
                                         gc_notify_response_id=response_id)
        db.session.add(db_history)
        db.session.commit()
        db.session.refresh(db_history)

        return db_history

    @classmethod
    def find_by_response_id(cls, response_id: str = None):
        """Return a Notification by the gc notify response id."""
        notification_history = None
        if response_id:
            notification_history = cls.query.filter_by(gc_notify_response_id=response_id).one_or_none()

        return notification_history

    def update(self):
        """Update notification."""
        db.session.add(self)
        db.session.flush()
        db.session.commit()

        return self
