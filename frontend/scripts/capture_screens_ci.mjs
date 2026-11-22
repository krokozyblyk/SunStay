import { chromium } from "playwright";
import { mkdirSync } from "fs";

const base = "https://krokozyblyk.github.io/SunStay";
const out = "screenshots";
mkdirSync(out, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: "ru-RU" });
const page = await context.newPage();
page.setDefaultTimeout(120000);

async function shot(path, name) {
  try {
    await page.goto(base + path, { waitUntil: "domcontentloaded", timeout: 120000 });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${out}/${name}.png` });
    console.log("OK", name);
  } catch (e) { console.log("FAIL", name, e.message.slice(0, 120)); }
}
async function loginAs(label, paths) {
  try {
    await page.goto(`${base}/login`, { waitUntil: "domcontentloaded", timeout: 120000 });
    await page.getByRole("button", { name: new RegExp(label) }).first().click();
    await page.waitForURL((u) => u.pathname.startsWith("/app") || u.pathname.startsWith("/me"), { timeout: 120000 });
    await page.waitForTimeout(1000);
    console.log("LOGIN", label);
    for (const [path, name] of paths) await shot(path, name);
  } catch (e) { console.log("LOGIN FAIL", label, e.message.slice(0, 120)); }
}

await shot("/", "landing");
await shot("/login", "login");
await shot("/hotel", "hotel");
await shot("/search?checkin=2026-12-20&checkout=2026-12-22&guests=2", "search");
await loginAs("Гость", [["/me", "guest-dashboard"], ["/me/bookings", "guest-bookings"]]);
await loginAs("Менеджер", [["/app", "manager-dashboard"], ["/app/room-grid", "room-grid"], ["/app/bookings", "bookings-registry"], ["/app/folios", "folio-payments"], ["/app/reports", "reports"], ["/app/housekeeping", "housekeeping"]]);
await loginAs("Администратор БД", [["/app/admin/users", "admin-users"], ["/app/admin/audit", "admin-audit"], ["/app/admin/backups", "admin-backups"]]);
await browser.close();
