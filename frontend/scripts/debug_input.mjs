import { chromium } from "playwright";
const base = process.argv[2] || "http://localhost:8080";
const browser = await chromium.launch({ channel: "msedge", headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: "ru-RU" });
const page = await context.newPage();
await page.goto(`${base}/login`, { waitUntil: "domcontentloaded" });
await page.getByRole("button", { name: /Менеджер/ }).first().click();
await page.waitForURL((url) => url.pathname.startsWith("/app"), { timeout: 20000 });
await page.goto(`${base}/app/bookings?new=1`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(1000);
const adults = page.getByLabel("Взрослые").first();
await adults.click();
for (const ch of "1234") {
  await page.keyboard.type(ch);
  await page.waitForTimeout(150);
  const info = await page.evaluate(() => ({
    active: document.activeElement?.getAttribute("aria-label") || document.activeElement?.getAttribute("placeholder") || document.activeElement?.tagName,
    value: document.activeElement?.value,
  }));
  console.log("typed", ch, JSON.stringify(info), "fieldValue", await adults.inputValue());
}
await browser.close();
