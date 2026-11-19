import { chromium } from "playwright";

const base = process.argv[2] || "http://localhost:8080";
const browser = await chromium.launch({ channel: "msedge", headless: true });
const errors = [];

async function makePage(role) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: "ru-RU" });
  const page = await context.newPage();
  page.on("pageerror", (e) => errors.push(`[${role}] ${e.message}`));
  page.on("response", (r) => { if (r.status() >= 500) errors.push(`[${role}] ${r.status()} ${r.url()}`); });
  await page.goto(`${base}/login`, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: new RegExp(role) }).first().click();
  await page.waitForURL((url) => url.pathname.startsWith("/app") || url.pathname.startsWith("/me"), { timeout: 25000 });
  return { context, page };
}
const ok = (name, value, detail = "") => console.log(`${value ? "PASS" : "FAIL"} ${name} ${detail}`);

// Public: unique photos + rating + amenities
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  await page.goto(`${base}/hotel`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1800);
  const text = await page.locator("body").innerText();
  ok("rating summary", /\d\.\d/.test(text) && text.includes("отзывов"));
  ok("rating bars", (await page.locator(".bg-amber").count()) >= 5);
  await page.goto(`${base}/search?checkin=2026-12-20&checkout=2026-12-22&guests=2`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1800);
  const imgs = await page.locator('img[src*="images/"]').evaluateAll((els) => els.map((e) => e.getAttribute("src")));
  const unique = new Set(imgs);
  ok(`unique photos (${unique.size}/${imgs.length})`, imgs.length > 0 && unique.size === imgs.length, JSON.stringify([...unique].slice(0, 5)));
  // amenity filter
  const before = await page.locator("text=Выбрать").count();
  await page.getByLabel("Wi-Fi").check();
  await page.waitForTimeout(400);
  const after = await page.locator("text=Выбрать").count();
  ok(`amenity filter keeps results (${before} -> ${after})`, after > 0);
  await context.close();
}

// Guest: review form in booking
{
  const { context, page } = await makePage("Гость");
  await page.goto(`${base}/me/bookings/1`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1200);
  const text = await page.locator("body").innerText();
  ok("booking review form", text.includes("Отзыв об отеле"));
  await context.close();
}

// Manager: status legend colors
{
  const { context, page } = await makePage("Менеджер");
  await page.goto(`${base}/app`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1200);
  const colored = await page.evaluate(() => {
    const el = [...document.querySelectorAll("span")].find((e) => e.textContent?.includes("Свободен"));
    return el ? getComputedStyle(el).color : null;
  });
  ok(`status legend colored (${colored})`, Boolean(colored) && colored !== "rgb(167, 176, 168)" && colored !== "rgb(110, 116, 109)");
  await context.close();
}

console.log("ERRORS", JSON.stringify(errors));
await browser.close();
