const puppeteer = require("puppeteer");
const loginViaBCSC = require("./helpers/loginbcsc.js");
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
    browser = await puppeteer.launch({ headless: 'new', timeout: 0 }); // Use an environment variable to toggle headless
    page = await browser.newPage();
    // setting viewport is essential for the tests to run consistently
    await page.setViewport({ width: 1920, height: 1080});
  });

  after(async () => {
    await browser.close();
  });

  it("should log in via BCSC flow", async () => {
    await loginViaBCSC(page, host, wait);
  });

  it("Click on the action button", async () => {
    expect(page.url()).to.equal(
      process.env.REGISTRY_HOME_URL + "dashboard/"
    );
    await page.waitForSelector("button.action-btn", { visible: true });
    await page.click("button.action-btn");
    console.log("Clicked on the action button");
    console.log(page.url());

    // Wait for the heading to appear on the new page
    let heading;
    await page.waitForSelector("h1.view-header__title", { visible: true });
    heading = await page.$eval(
      "h1.view-header__title",
      (heading) => heading.innerText
    );
    expect(heading).to.contain("My Business Registry");

    // Wait for the get started button to be active
    await page.waitForSelector("#get-started-button", { visible: true });
    await page.click("#get-started-button");

    expect(page.url()).to.contain(process.env.NAMES_HOME_URL);
    console.log(page.url());

    await page.waitForSelector("#app-title", { visible: true });
    heading = await page.$eval("#app-title", (heading) => heading.innerText);
    expect(heading).to.contain("Name Request");
  });

  it("Navigate back", async () => {
    // Wait for the heading to appear on the new page
    let heading;
    await page.waitForSelector("#app-title", { visible: true });
    heading = await page.$eval("#app-title", (heading) => heading.innerText);
    expect(heading).to.contain("Name Request");

    await page.waitForSelector("a.v-breadcrumbs__item", { visible: true });
    await page.click("a.v-breadcrumbs__item", { force: true });
    console.log("Navigated back");
  });

  it("Logout", async () => {
    await logout(page, host, wait);
  });
});
