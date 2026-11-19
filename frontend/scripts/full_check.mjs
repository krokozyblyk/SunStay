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

async function visit(page, role, path, marker) {
  try {
    await page.goto(base + path, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(700);
    const text = await page.locator("body").innerText();
    results.push(`${role} ${path}: ${marker ? text.includes(marker) : "ok"}`);
  } catch (e) {
    errors.push(`[${role}] visit ${path}: ${e.message}`);
  }
}

{
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  page.on("pageerror", (e) => errors.push(`[public] ${e}`));
  await page.goto(base, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(700);
  const imgs = await page.locator('img[src*="images/"]').evaluateAll((els) => els.filter((e) => e.naturalWidth > 0).length);
  results.push(`public images loaded: ${imgs}`);
  await page.goto(`${base}/search?checkin=2026-12-20&checkout=2026-12-22&guests=2`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(700);
  results.push(`public search variants: ${await page.locator("text=Классика").count()}`);
  await context.close();
}

{
  const { context, page } = await makePage("Администратор БД");
  for (const [path, marker] of [
    ["/app", "Операционный обзор"], ["/app/admin/users", "Пользователи"], ["/app/admin/directories", "Справочники"],
    ["/app/admin/audit", "Журнал аудита"], ["/app/admin/reviews", "Отзывы"], ["/app/admin/backups", "Резервное"],
    ["/app/admin/sessions", "Сессии"], ["/app/admin/settings", "Настройки"], ["/app/employees", "Сотрудники"],
  ]) await visit(page, "admin", path, marker);
  await page.goto(`${base}/app/admin/backups`, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Проверить копию" }).click();
  await page.waitForTimeout(1200);
  results.push("admin backup verify clicked");
  await page.getByRole("button", { name: "Тест восстановления" }).click();
  await page.waitForTimeout(2500);
  results.push("admin backup restore clicked");
  await context.close();
}

{
  const { context, page } = await makePage("Менеджер");
  for (const [path, marker] of [
    ["/app", "Операционный обзор"], ["/app/room-grid", "Шахматка"], ["/app/bookings", "Реестр"],
    ["/app/folios", "Folio"], ["/app/reports", "Отчёты"], ["/app/housekeeping", "Хаускипинг"],
    ["/app/waitlist", "Лист ожидания"], ["/app/floor-plan", "План этажа"],
  ]) await visit(page, "manager", path, marker);
  await context.close();
}

{
  const { context, page } = await makePage("Гость");
  for (const [path, marker] of [
    ["/me", "Добрый день"], ["/me/bookings", "Мои бронирования"], ["/me/invoices", "Счета"],
    ["/me/services", "Дополнительные услуги"], ["/me/profile", "Профиль"], ["/me/loyalty", "Бонусные баллы"],
  ]) await visit(page, "guest", path, marker);
  await context.close();
}

console.log(results.join("\n"));
console.log("ERRORS", JSON.stringify(errors, null, 2));
await browser.close();
