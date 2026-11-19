import { chromium } from "playwright";
const base = "https://krokozyblyk.github.io/SunStay";
const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("response", (r) => { if (r.url().includes("images/") && r.status() >= 400) errors.push(`${r.status()} ${r.url()}`); });
for (const path of ["/", "/hotel", "/rooms/9?room_number=111&room_type=%D0%A1%D1%82%D0%B0%D0%BD%D0%B4%D0%B0%D1%80%D1%82&variant=%D0%9A%D0%BB%D0%B0%D1%81%D1%81%D0%B8%D0%BA%D0%B0&price=4000&rate_id=5&guests=2&image=images%2Fvariants%2Fstandard-classic.jpg", "/search?checkin=2026-12-20&checkout=2026-12-22&guests=2"]) {
  await page.goto(base + path, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2500);
  const text = await page.locator("body").innerText();
  const imgs = await page.locator('img[src*="images/"]').evaluateAll((els) => els.filter((e) => e.naturalWidth > 0).length);
  console.log(path, "text:", text.slice(0, 90).replace(/\n/g, " "), "| imgs:", imgs);
}
console.log("ERRORS", JSON.stringify(errors));
await browser.close();
