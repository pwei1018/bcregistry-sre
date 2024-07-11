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
"""Common setup and fixtures for the pytest suite used by this service."""
import pytest

from notify_delivery import create_app


@pytest.fixture(autouse=True)
def app():
    """Return a session-wide application configured in TEST mode."""
    _app = create_app("unitTesting")

    with _app.app_context():
        yield _app


@pytest.fixture(scope="function")
def client(app, request):  # pylint: disable=redefined-outer-name
    """Return a session-wide Flask test client."""
    request.cls.client = app.test_client()


@pytest.fixture(autouse=True)
def app_smtp():
    """Return a session-wide application configured in TEST mode."""
    _app = create_app("unitTestingSMTP")

    with _app.app_context():
        yield _app


@pytest.fixture(scope="function")
def client_smtp(app_smtp, request):  # pylint: disable=redefined-outer-name
    """Return a session-wide Flask test client."""
    request.cls.client = app_smtp.test_client()
