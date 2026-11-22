import { chromium } from "playwright";
import { mkdirSync } from "fs";

const base = "https://krokozyblyk.github.io/SunStay";
const out = "../docs/screenshots";
mkdirSync(out, { recursive: true });

const browser = await chromium.launch({ channel: "msedge", headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: "ru-RU" });
const page = await context.newPage();
page.setDefaultTimeout(90000);

async function shot(path, name) {
  try {
    await page.goto(base + path, { waitUntil: "domcontentloaded", timeout: 90000 });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${out}/${name}.png`, fullPage: false });
    console.log("OK", name);
  } catch (e) {
    console.log("FAIL", name, e.message.slice(0, 100));
  }
}
async function loginAs(label) {
  await page.goto(`${base}/login`, { waitUntil: "domcontentloaded", timeout: 90000 });
  await page.getByRole("button", { name: new RegExp(label) }).first().click();
  await page.waitForURL((u) => u.pathname.startsWith("/app") || u.pathname.startsWith("/me"), { timeout: 90000 });
  await page.waitForTimeout(1200);
  console.log("LOGIN", label);
}
async function shotApp(path, name) {
  try {
    await page.goto(base + path, { waitUntil: "domcontentloaded", timeout: 90000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${out}/${name}.png`, fullPage: false });
    console.log("OK", name);
  } catch (e) {
    console.log("FAIL", name, e.message.slice(0, 100));
  }
}

await shot("/", "landing");
await shot("/login", "login");
await shot("/hotel", "hotel");
await shot("/search?checkin=2026-12-20&checkout=2026-12-22&guests=2", "search");

for (const [label, paths] of [
  ["Менеджер", [["/app", "manager-dashboard"], ["/app/room-grid", "room-grid"], ["/app/bookings", "bookings-registry"], ["/app/folios", "folio-payments"], ["/app/reports", "reports"], ["/app/housekeeping", "housekeeping"]]],
]) {
  try {
    await loginAs(label);
    for (const [path, name] of paths) await shotApp(path, name);
  } catch (e) { console.log("LOGIN FAIL", label, e.message.slice(0, 100)); }
}
try {
  await loginAs("Гость");
  for (const [path, name] of [["/me", "guest-dashboard"], ["/me/bookings", "guest-bookings"]]) await shotApp(path, name);
} catch (e) { console.log("LOGIN FAIL guest", e.message.slice(0, 100)); }
try {
  await loginAs("Администратор БД");
  for (const [path, name] of [["/app/admin/users", "admin-users"], ["/app/admin/audit", "admin-audit"], ["/app/admin/backups", "admin-backups"]]) await shotApp(path, name);
} catch (e) { console.log("LOGIN FAIL admin", e.message.slice(0, 100)); }

await browser.close();
