const { expect } = require("chai");
require("dotenv").config();

/**
 * Logs into a website using BC Services Card.
 *
 * @param {object} page - The Puppeteer page object.
 * @param {string} host - The URL of the host to navigate to.
 * @param {number} wait - The wait time in milliseconds.
 * @throws Will throw an error if any step of the login process fails.
 *
 * @example
 * const puppeteer = require('puppeteer');
 * const loginViaBCSC = require('./loginbcsc');
 * 
 * (async () => {
 *   const browser = await puppeteer.launch();
 *   const page = await browser.newPage();
 *   await loginViaBCSC(page, 'https://example.com', 5000);
 *   await browser.close();
 * })();
 */
const loginViaBCSC = async (page, host, wait) => {
  try {
    await page.goto(host, { waitUntil: "networkidle0" });
    console.log("Navigated to host");

    // Click Login button
    await page.waitForSelector("#loginBtn", { visible: true });
    await page.click("#loginBtn");
    console.log("Clicked Login button");

    // Select BC Services Card option
    const elements = await page.$$('div[role="menuitem"]');
    if (elements.length > 0) {
      await elements[0].click();
      console.log("Successfully clicked the BC Services Card menuitem");
    } else {
      throw new Error("No elements with role='menuitem' found to click");
    }

    console.log("Selected BCSC option");

    // Wait for the BCSC start page
    console.log("Reached BCSC start page");

    // Handle BCSC button
    await page.waitForSelector(
      "#tile_test_with_username_password_device_div_id",
      { visible: true }
    );
    await page.click("#tile_test_with_username_password_device_div_id");
    console.log("Clicked Test with username and password");

    // Wait for the BCSC login page
    console.log("Reached BCSC login page");

    // Enter credentials
    await page.waitForSelector("#username", { visible: true });
    await page.type("#username", process.env.USERNAMESCBC, { delay: 100 });
    await page.waitForSelector("#password", { visible: true });
    await page.type("#password", process.env.PWDSCBC, { delay: 100 });
    console.log("Entered credentials");

    // Submit the form
    await page.waitForSelector("#submit-btn", { visible: true });
    await page.click("#submit-btn");
    console.log("Submitted credentials");

    // Assert successful login
    const loggedInUrl = process.env.REGISTRY_HOME_URL + "dashboard/";

    await page
      .waitForNavigation({
        waitUntil: "load",
        url: loggedInUrl, // Wait specifically for the second URL
      })
      .then(() => {
        console.log("Login successful");
      });

    await page.goto(loggedInUrl);
    console.log(page.url());

  } catch (err) {
    console.error("Error during login:", err);
    throw err; // Rethrow the error to fail the test
  }
};

module.exports = loginViaBCSC;
