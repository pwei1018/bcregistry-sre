/**
 * This file contains Mocha tests for synthetic monitoring of BC Registry services.
 * 
 * The tests in this file use the `chai` assertion library and `node-fetch` to send HTTP requests
 * and verify the responses. The URLs for the tests are provided via environment variables.
 * 
 * Dependencies:
 * - chai: https://www.npmjs.com/package/chai
 * - node-fetch: https://www.npmjs.com/package/node-fetch
 * 
 * Example usage:
 * - To add tests for other GCP products or services, add the necessary dependencies to the package.json file
 *   and require them in this file.
 * - For example, to interact with Google Cloud Secret Manager, add `@google-cloud/secret-manager` to package.json
 *   and require it in this file.
 * 
 * @fileoverview Mocha tests for synthetic monitoring of BC Registry services.
 * @license Apache-2.0
 */
// Copyright 2023 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// [START monitoring_synthetic_monitoring_mocha_test]

/*
 * This is the file may be interacted with to author mocha tests. To interact
 * with other GCP products or services, users should add dependencies to the
 * package.json file, and require those dependencies here A few examples:
 *  - @google-cloud/secret-manager:
 *        https://www.npmjs.com/package/@google-cloud/secret-manager
 *  - @google-cloud/spanner: https://www.npmjs.com/package/@google-cloud/spanner
 *  - Supertest: https://www.npmjs.com/package/supertest
 */

const {expect} = require('chai');
const fetch = require('node-fetch');

it('pings account.bcregistry', async () => {
  /**
   * URL to send the request to.
   * @type {string}
   */
  const url = process.env.APP_AUTH_WEB_URL; // URL to send the request to
  const externalRes = await fetch(url);
  expect(externalRes.ok).to.be.true;
});

it('pings bcregistry', async () => {
    /**
   * URL to send the request to.
   * @type {string}
   */
  const url = process.env.REGISTRY_HOME_URL; // URL to send the request to
  const externalRes = await fetch(url);
  expect(externalRes.ok).to.be.true;
});

// [END monitoring_synthetic_monitoring_mocha_test]