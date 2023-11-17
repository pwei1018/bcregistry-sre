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
"""Callback data model."""
from __future__ import annotations

from pydantic import BaseModel

from .db import db  # noqa: I001


class CallbackRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Callback model for resquest."""

    id: str = None
    reference: str = None
    to: str = None
    status: str = None
    status_description: str = None
    provider_response: str = None
    created_at: str = None
    updated_at: str = None
    completed_at: str = None
    sent_at: str = None
    notification_type: str = None


class Callback(db.Model):
    """Immutable Callback record."""

    __tablename__ = "gc_notify_callback"

    id = db.Column(db.Integer, primary_key=True)
    notify_id = db.Column(db.String)
    reference = db.Column(db.String)
    to = db.Column(db.String)
    status = db.Column(db.String)
    status_description = db.Column(db.String)
    provider_response = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    notification_type = db.Column(db.String)

    @property
    def json(self) -> dict:
        """Return a dict of this object, with keys in JSON format."""
        callback_json = {
            "notify_id": self.id,
            "to": self.to,
            "status": self.status,
            "status_description": self.status_description,
            "provider_response": self.provider_response,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "sent_at": self.sent_at,
            "notification_type": self.notification_type,
        }

        return callback_json

    @classmethod
    def save(cls, callback: CallbackRequest):
        """Add email to list."""
        db_callback = Callback(
            notify_id=callback.id,
            reference=callback.reference,
            to=callback.to,
            status=callback.status,
            status_description=callback.status_description,
            provider_response=callback.provider_response,
            created_at=callback.created_at,
            updated_at=callback.updated_at,
            completed_at=callback.completed_at,
            sent_at=callback.sent_at,
            notification_type=callback.notification_type,
        )

        try:
            db.session.add(db_callback)
            db.session.commit()
            db.session.refresh(db_callback)
        except Exception:  # NOQA # pylint: disable=broad-except
            db.session.rollback()
