import { chromium } from "playwright";
const browser = await chromium.launch({ channel: "msedge", headless: true });
for (const base of ["http://localhost:8080", "https://krokozyblyk.github.io/SunStay"]) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const bad = [];
  page.on("response", (r) => { if (r.url().includes("images/") && r.status() >= 400) bad.push(`${r.status()} ${r.url()}`); });
  await page.goto(base, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2000);
  const imgs = await page.locator('img[src*="images/"]').evaluateAll((els) => els.map((e) => ({ src: e.getAttribute("src"), w: e.naturalWidth })));
  console.log(base, JSON.stringify(imgs), "bad", JSON.stringify(bad));
  await page.goto(`${base}/search?checkin=2026-12-20&checkout=2026-12-22&guests=2`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2000);
  const searchImgs = await page.locator('img[src*="images/"]').evaluateAll((els) => els.map((e) => ({ src: e.getAttribute("src"), w: e.naturalWidth })));
  console.log(base, "search", JSON.stringify(searchImgs), "bad", JSON.stringify(bad));
  await page.close();
}
await browser.close();
