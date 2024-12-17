const { expect } = require("chai");

/**
 * Logs into the application via IDIR.
 *
 * @param {object} page - The Puppeteer page object.
 * @param {string} host - The URL of the host to navigate to.
 * @param {number} wait - The wait time in milliseconds.
 * @throws Will throw an error if any step of the login process fails.
 * @returns {Promise<void>} - A promise that resolves when the login process is complete.
 */
const loginViaIDIR = async (page, host, wait) => {
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
      await elements[2].click();
      console.log("Successfully clicked the IDIR menuitem");
    } else {
      throw new Error("No elements with role='menuitem' found to click");
    }

    console.log("Selected IDIR option");

    // Wait for the IDIR login page
    console.log("Reached IDIR login page");

    // Handle IDIR button
    await page.waitForSelector(
      "#idirLogo",
      { visible: true }
    );

    // Enter credentials
    await page.waitForSelector("#user", { visible: true });
    await page.type("#user", process.env.USERNAMEIDIR, { delay: 100 });
    await page.waitForSelector("#password", { visible: true });
    await page.type("#password", process.env.PWDIDIR, { delay: 100 });
    console.log("Entered credentials");

    // Submit the form
    await page.waitForSelector('input[name="btnSubmit"]', { visible: true });
    await page.click('input[name="btnSubmit"]');
    console.log("Submitted credentials");

    // Assert successful login
    const loggedInUrl = process.env.APP_AUTH_WEB_URL + "staff/dashboard/active";

    await page
      .waitForNavigation({
        waitUntil: "load",
        url: loggedInUrl, // Wait specifically for the second URL
      })
      .then(() => {
        console.log("Login successful");
      });

    console.log(page.url());

  } catch (err) {
    console.error("Error during login:", err);
    throw err; // Rethrow the error to fail the test
  }
};

module.exports = loginViaIDIR;
