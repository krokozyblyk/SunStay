import { chromium } from "playwright";
import path from "node:path";
import { pathToFileURL } from "node:url";

const htmlPath = path.resolve("../docs/diagrams/diagrams.html");
const outDir = path.resolve("../docs/diagrams");

const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage({ viewport: { width: 1450, height: 1600 }, deviceScaleFactor: 1.5 });
await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "networkidle" });
await page.waitForSelector(".mermaid svg", { timeout: 30000 });
await page.waitForTimeout(1500);

for (const id of ["architecture", "usecase", "erd", "uimap", "testpyramid"]) {
  const locator = page.locator(`#${id}`);
  await locator.screenshot({ path: path.join(outDir, `${id}.png`) });
  console.log("captured", id);
}

await browser.close();

