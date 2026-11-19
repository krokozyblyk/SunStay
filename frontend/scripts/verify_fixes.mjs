import { chromium } from "playwright";

const base = "http://localhost:8080";
const browser = await chromium.launch({ channel: "msedge", headless: true });
const results = [];
const errors = [];

async function makePage(role) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: "ru-RU" });
  const page = await context.newPage();
  page.on("pageerror", (e) => errors.push(`[${role}] pageerror ${e}`));
  page.on("response", (r) => { if (r.status() >= 500) errors.push(`[${role}] ${r.status()} ${r.url()}`); });
  await page.goto(`${base}/login`, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: new RegExp(role) }).first().click();
  await page.waitForURL((url) => url.pathname.startsWith("/app") || url.pathname.startsWith("/me"), { timeout: 20000 });
  await page.waitForTimeout(500);
  return { context, page };
}

function ok(name, value) { results.push(`${value ? "PASS" : "FAIL"} ${name}`); }

// --- Public: room page, hotel page, service images ---
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  page.on("pageerror", (e) => errors.push(`[public] ${e}`));
  await page.goto(`${base}/hotel`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1200);
  ok("hotel page reviews block", (await page.locator("body").innerText()).includes("Отзывы гостей"));
  await page.goto(`${base}/rooms/9`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1200);
  const gallery = await page.locator('img[alt^="Стандарт"]').count();
  ok(`room page gallery (${gallery})`, gallery >= 3);
  ok("room page choose button", await page.getByRole("button", { name: /Выбрать/ }).count() > 0);
  await context.close();
}

// --- Guest: service images load, 2FA hidden until requested ---
{
  const { context, page } = await makePage("Гость");
  await page.goto(`${base}/me/services`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1200);
  const svcImgs = await page.locator('img[src*="services/"]').evaluateAll((els) => els.map((e) => ({ src: e.getAttribute("src"), w: e.naturalWidth })));
  ok(`service images load (${JSON.stringify(svcImgs)})`, svcImgs.length > 0 && svcImgs.every((i) => i.w > 0));
  await context.close();
}

// --- Manager: document number multi-digit, number inputs, auto tariff ---
{
  const { context, page } = await makePage("Менеджер");
  await page.goto(`${base}/app/bookings?new=1`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1200);
  {
    await page.waitForTimeout(300);
    const addGuest = page.getByRole("button", { name: /Гость/ }).last();
    if (await addGuest.count()) { await addGuest.click(); await page.waitForTimeout(300); }
    const doc = page.getByLabel("Документ");
    if (await doc.count()) {
      await doc.first().fill("4510 123456");
      const val = await doc.first().inputValue();
      ok(`document multi-digit (${val})`, val === "4510123456");
    } else ok("document input present", false);
    const adults = page.getByLabel("Взрослые");
    if (await adults.count()) {
      await adults.first().fill("12");
      ok(`number multi-digit (${await adults.first().inputValue()})`, (await adults.first().inputValue()) === "12");
    }
  }
  // dark theme tooltip on dashboard
  await page.goto(`${base}/app`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
  ok("dashboard loads", (await page.locator("body").innerText()).includes("Операционный обзор"));
  await context.close();
}

// --- Staff settings visible to manager ---
{
  const { context, page } = await makePage("Менеджер");
  await page.goto(`${base}/app/settings`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
  ok("staff settings page", (await page.locator("body").innerText()).includes("Двухфакторная"));
  ok("2FA disable hidden for fresh staff", (await page.getByRole("button", { name: "Отключить" }).count()) === 0);
  await context.close();
}

console.log(results.join("\n"));
console.log("ERRORS", JSON.stringify(errors, null, 2));
await browser.close();
