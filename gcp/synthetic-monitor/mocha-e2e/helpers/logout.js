const { expect } = require("chai");
require("dotenv").config();

/**
 * Logs out the user from the application.
 *
 * @param {object} page - The Puppeteer page object.
 * @param {string} host - The URL of the host to navigate to.
 * @param {number} wait - The wait time in milliseconds.
 * @returns {Promise<void>} - A promise that resolves when the logout process is complete.
 * @throws {Error} - Throws an error if no elements with role='menuitem' are found.
 */
const logout = async (page, host, wait) => {
  await page.goto(host, { waitUntil: "networkidle0" });
  console.log("Navigated to host");

  // Click Login button
  await page.waitForSelector('[data-test="user-name"]', { visible: true });
  await page.click('[data-test="user-name"]');

  console.log("Clicked User button");

  // Select BC Services Card option
  const elements = await page.$$('div[role="menuitem"]');
  if (elements.length > 0) {
    await elements[1].click();
    console.log("Successfully clicked the Log out menuitem");
  } else {
    throw new Error("No elements with role='menuitem' found to click");
  }

  console.log("Logged out");

  // Wait for the start page
  console.log("Reached start page");

};

module.exports = logout;
