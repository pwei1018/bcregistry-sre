# Copyright © 2023 Province of British Columbia
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
"""Tests to assure the safe list end-point."""

import json

from notify_api.models.safe_list import SafeList
from notify_api.utils.enums import Role
from tests.factories.jwt import create_header


def test_safe_list(session, client, jwt):  # pylint: disable=unused-argument
    """Assert that the safe list returns."""
    headers = create_header(jwt, [Role.STAFF.value], **{"Accept-Version": "v2"})
    safelist = SafeList()
    safelist.add_email("hello@gogo.com")
    safelist.add_email("hello@gogo2.com")
    response = client.get("/api/v2/safe_list/", headers=headers)
    assert response.status_code == 200
    assert response.json
    assert len(response.json) == 2
    assert response.json[0]["email"] == "hello@gogo.com"
    response = client.delete(f'/api/v2/safe_list/{"hello@gogo.com"}', headers=headers)
    assert response.status_code == 200
    assert response.json
    assert len(response.json) == 1
    assert response.json[0]["email"] == "hello@gogo2.com"
    request_json = json.dumps({"email": ["hello@gogo.com"]})
    response = client.post("/api/v2/safe_list", json=request_json, headers=headers)
    assert response.status_code == 200
    assert response.json
    assert len(response.json) == 2
    assert response.json[0]["email"] == "hello@gogo2.com"