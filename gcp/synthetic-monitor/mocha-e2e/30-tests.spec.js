const puppeteer = require("puppeteer");
const loginViaIDIR = require("./helpers/loginidir.js");
const logout = require("./helpers/logout.js");
const { expect } = require("chai");
require("dotenv").config();

describe("Login Proxy Tests", function () {
  let browser;
  let page;
  const host = process.env.APP_AUTH_WEB_URL;
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  this.timeout(60000); // Global timeout for all tests

  before(async () => {
    browser = await puppeteer.launch({ headless: 'new', timeout: 0}); // Use an environment variable to toggle headless
    //browser = await puppeteer.launch({ headless: false, timeout: 0 }); // Use an environment variable to toggle headless
    page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080});
  });

  after(async () => {
    await browser.close();
  });

  it("should log in via IDIR flow", async () => {
    await loginViaIDIR(page, host, wait);
    wait(10000);
  });

  it("Click on the action button", async () => {
    await page.waitForSelector("button.srch-card__link", { visible: true });
    await page.click("button.srch-card__link");
    console.log("Clicked on the Staff Dashboard button");
    console.log(page.url());
  });

  it("Logout", async () => {
    await logout(page, host, wait);
  });
});
