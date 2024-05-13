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
"""Resource package for the pay-queue service."""
from flask import Flask

from notify_api.resources.ops.ops import bp as ops_bp

from notify_delivery.resources.email_smtp import bp as smtp_endpoint
from notify_delivery.resources.gc_notify import bp as gcnotify_endpoint


def register_endpoints(app: Flask):
    """Register endpoints with the flask application."""
    # Allow base route to match with, and without a trailing slash
    app.url_map.strict_slashes = False

    if app.config.get("DEPLOYMENT_PLATFORM") == "OCP":
        app.register_blueprint(smtp_endpoint, url_prefix="/smtp")
    else:
        app.register_blueprint(gcnotify_endpoint, url_prefix="/gcnotify")

    app.register_blueprint(ops_bp, url_prefix="/ops")
