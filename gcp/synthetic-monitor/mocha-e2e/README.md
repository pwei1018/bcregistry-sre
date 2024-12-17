# Tests

We have 3 sample tests, they are:

- `10-test.spec.js` : A simple test that checks if the BC Registries and Online Services home page is available.
- `20-test.spec.js` : A simple test that checks if the BC Registries and Online Services account authentication page is available. And does some basic navifgation to 'Names".'
- `30-test.spec.js` : A simple test that checks if the BC Registries and Online Services names page is available for an IDIR user and does some basic navigation.

We also created 3 helper functions to help with the tests:

- Login with a BCSC account
- Login with an IDIR account
- Logout

These helper functions can be used to quickstart future expansions on these tests.