import { chromium } from "playwright";
import path from "node:path";
import fs from "node:fs";

const base = process.env.BASE_URL ?? "http://localhost:5173";
const outDir = path.resolve("../docs/screenshots");
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ channel: "msedge", headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1024 }, locale: "ru-RU" });
const page = await context.newPage();
const errors = [];
page.on("console", (message) => {
  if (message.type() === "error") errors.push(message.text());
});
page.on("pageerror", (error) => errors.push(String(error)));
page.on("response", (response) => {
  if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
});

async function shot(name) {
  await page.screenshot({ path: path.join(outDir, `${name}.png`), fullPage: false });
  console.log("screenshot", name);
}

await page.goto(base, { waitUntil: "networkidle" });
await shot("landing");

await page.goto(`${base}/login`, { waitUntil: "networkidle" });
await shot("login");
await page.getByRole("button", { name: /Менеджер/ }).first().click();
await page.waitForURL("**/app", { timeout: 15000 });
await page.waitForTimeout(1500);
await shot("manager-dashboard");
console.log("manager dashboard text:", (await page.locator("body").innerText()).slice(0, 500));

await page.goto(`${base}/app/bookings`, { waitUntil: "networkidle" });
await page.waitForTimeout(1000);
await shot("bookings-registry");

await page.goto(`${base}/app/room-grid`, { waitUntil: "networkidle" });
await page.waitForTimeout(1000);
await shot("room-grid");

await page.goto(`${base}/app/folios`, { waitUntil: "networkidle" });
await page.waitForTimeout(1000);
await shot("folio-payments");

await page.goto(`${base}/app/reports`, { waitUntil: "networkidle" });
await page.waitForTimeout(1800);
await shot("reports");

await page.goto(`${base}/app/housekeeping`, { waitUntil: "networkidle" });
await page.waitForTimeout(1000);
await shot("housekeeping");

await page.goto(`${base}/app/waitlist`, { waitUntil: "networkidle" });
await page.waitForTimeout(1000);
await shot("waitlist");

await page.getByTitle("Переключить тему").first().click();
await page.waitForTimeout(500);
await shot("manager-dashboard-dark");

const adminContext = await browser.newContext({ viewport: { width: 1440, height: 1024 }, locale: "ru-RU" });
const adminPage = await adminContext.newPage();
adminPage.on("console", (message) => { if (message.type() === "error") errors.push(`[admin] ${message.text()}`); });
adminPage.on("pageerror", (error) => errors.push(`[admin] ${String(error)}`));
adminPage.on("response", (response) => { if (response.status() >= 400) errors.push(`[admin] ${response.status()} ${response.url()}`); });
await adminPage.goto(`${base}/login`, { waitUntil: "networkidle" });
await adminPage.getByRole("button", { name: /Администратор БД/ }).first().click();
await adminPage.waitForURL("**/app", { timeout: 15000 });
await adminPage.waitForTimeout(1200);
await adminPage.screenshot({ path: path.join(outDir, "admin-dashboard.png") });
await adminPage.goto(`${base}/app/admin/users`, { waitUntil: "networkidle" });
await adminPage.waitForTimeout(1200);
await adminPage.screenshot({ path: path.join(outDir, "admin-users.png") });
await adminPage.goto(`${base}/app/admin/directories`, { waitUntil: "networkidle" });
await adminPage.waitForTimeout(1200);
await adminPage.screenshot({ path: path.join(outDir, "admin-directories.png") });
await adminPage.goto(`${base}/app/admin/audit`, { waitUntil: "networkidle" });
await adminPage.waitForTimeout(1200);
await adminPage.screenshot({ path: path.join(outDir, "admin-audit.png") });
await adminPage.getByRole("button", { name: "Пользователи и вход" }).click();
await adminPage.waitForTimeout(1000);
await adminPage.screenshot({ path: path.join(outDir, "admin-audit-login.png") });
await adminPage.getByRole("button", { name: "Системные события" }).click();
await adminPage.waitForTimeout(1000);
await adminPage.screenshot({ path: path.join(outDir, "admin-audit-system.png") });
await adminPage.goto(`${base}/app/admin/backups`, { waitUntil: "networkidle" });
await adminPage.waitForTimeout(1200);
await adminPage.screenshot({ path: path.join(outDir, "admin-backups.png") });
await adminPage.goto(`${base}/app/admin/reviews`, { waitUntil: "networkidle" });
await adminPage.waitForTimeout(1200);
await adminPage.screenshot({ path: path.join(outDir, "admin-reviews.png") });

const guestContext = await browser.newContext({ viewport: { width: 1440, height: 1024 }, locale: "ru-RU" });
const guestPage = await guestContext.newPage();
guestPage.on("console", (message) => { if (message.type() === "error") errors.push(`[guest] ${message.text()}`); });
guestPage.on("pageerror", (error) => errors.push(`[guest] ${String(error)}`));
guestPage.on("response", (response) => { if (response.status() >= 400) errors.push(`[guest] ${response.status()} ${response.url()}`); });
await guestPage.goto(`${base}/login`, { waitUntil: "networkidle" });
await guestPage.getByRole("button", { name: /Гость/ }).first().click();
await guestPage.waitForURL("**/me", { timeout: 15000 });
await guestPage.waitForTimeout(1200);
await guestPage.screenshot({ path: path.join(outDir, "guest-dashboard.png") });
await guestPage.goto(`${base}/me/bookings`, { waitUntil: "networkidle" });
await guestPage.waitForTimeout(1000);
await guestPage.screenshot({ path: path.join(outDir, "guest-bookings.png") });
await guestPage.goto(`${base}/me/invoices`, { waitUntil: "networkidle" });
await guestPage.waitForTimeout(1000);
await guestPage.screenshot({ path: path.join(outDir, "guest-invoices.png") });

console.log("ERRORS:", JSON.stringify(errors, null, 2));
await browser.close();
