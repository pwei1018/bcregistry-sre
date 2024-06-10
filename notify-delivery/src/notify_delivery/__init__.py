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
"""The Reconciliations queue service.

The service worker for applying payments, receipts and account balance to payment system.
"""
from __future__ import annotations

import os

from flask import Flask
from flask_migrate import Migrate, upgrade
from notify_api.models import db
from notify_api.utils.logging import logger, setup_logging

from notify_delivery.config import config
from notify_delivery.metadata import APP_RUNNING_ENVIRONMENT
from notify_delivery.resources import register_endpoints
from notify_delivery.services.gcp_queue import queue

setup_logging(os.path.join(os.path.abspath(os.path.dirname(__file__)), "logging.yaml"))  # important to do this first


def create_app(service_environment=APP_RUNNING_ENVIRONMENT, **kwargs):
    """Return a configured Flask App using the Factory method."""
    app = Flask(__name__)
    app.config.from_object(config[service_environment])

    db.init_app(app)

    # Have to setup another database in OpenShift platform
    if app.config.get("DEPLOYMENT_PLATFORM") == "OCP":
        Migrate(app, db)
        logger.info("Running migration upgrade.")

        with app.app_context():
            upgrade(directory="migrations", revision="head", sql=False, tag=None)

        # Alembic has it's own logging config, we'll need to restore our logging here.
        setup_logging(os.path.join(os.path.abspath(os.path.dirname(__file__)), "logging.yaml"))
        logger.info("Finished migration upgrade.")

    queue.init_app(app)

    register_endpoints(app)

    return app
