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

from notify_api.models.safe_list import SafeList
from notify_api.utils.enums import Role
from tests.factories.jwt import create_header


def test_safe_list(session, client, jwt):  # pylint: disable=unused-argument
    """Assert that the safe list returns."""
    safelist = SafeList()
    headers = create_header(jwt, [Role.STAFF.value], **{"Accept-Version": "v2"})
    safelist.add_email("hello@gogo.com")
    safelist.add_email("hello@gogo2.com")
    response = client.get("/api/v2/safe_list/", headers=headers)
    assert response.status_code == 200
    assert response.json
    assert len(response.json) == 2
    # Test delete endpoint
    delete_response = client.delete(f"/api/v2/safe_list/{'hello@gogo.com'}", headers=headers)
    assert delete_response.status_code == 200
    response = client.get("/api/v2/safe_list/", headers=headers)
    assert response.status_code == 200
    assert response.json
    assert len(response.json) == 1
    assert safelist.is_in_safe_list("hello@gogo2.com")
    # Test add post endpoint
    add_request_data = {"email": ["hello@gogo.com"]}
    add_response = client.post("/api/v2/safe_list/", json=add_request_data, headers=headers)
    assert add_response.status_code == 200
    response = client.get("/api/v2/safe_list/", headers=headers)
    assert response.status_code == 200
    assert response.json
    assert len(response.json) == 2
    assert safelist.is_in_safe_list("hello@gogo2.com")
    assert safelist.is_in_safe_list("hello@gogo.com")
