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
"""API endpoints for validate email address."""
from http import HTTPStatus

from flask import Blueprint
from flask_pydantic import validate

from notify_api.services import notify
from notify_api.utils.auth import jwt
from notify_api.utils.enums import Role

bp = Blueprint("RESEND", __name__, url_prefix="/resend")


@bp.route("", methods=["POST"])
@jwt.requires_auth
@jwt.has_one_of_roles([Role.SYSTEM.value, Role.PUBLIC_USER.value, Role.STAFF.value])
@validate()
def resend(t):
    """Resend notification endpoint."""
    notify.queue_republish()

    return "", HTTPStatus.OK
