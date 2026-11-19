import { chromium } from "playwright";
const base = process.argv[2] || "http://localhost:8080";
const browser = await chromium.launch({ channel: "msedge", headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: "ru-RU" });
const page = await context.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("response", (r) => { if (r.status() >= 400 && r.url().includes("/api/")) errors.push(`${r.status()} ${r.url()}`); });
await page.goto(`${base}/login`, { waitUntil: "domcontentloaded" });
await page.getByRole("button", { name: /Гость/ }).first().click();
await page.waitForURL((url) => url.pathname.startsWith("/me"), { timeout: 25000 });
await page.goto(`${base}/hotel`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(2500);
const text = await page.locator("body").innerText();
console.log("HAS FORM", text.includes("Оставить отзыв"));
console.log("HAS PUBLISH", await page.getByRole("button", { name: "Опубликовать" }).count());
console.log("HAS LOGIN MSG", text.includes("Войдите как гость"));
console.log("FEATURES", await page.evaluate(async () => {
  try { const r = await fetch("/api/public/config"); return await r.text(); } catch (e) { return String(e); }
}));
console.log("ERRORS", JSON.stringify(errors));
await browser.close();
