import { chromium } from "@playwright/test";
import path from "path";
import fs from "fs";

const BASE = "http://localhost:3000";
const OUT = path.join(__dirname, "../screenshots");

const PAGES = [
  { name: "01-login", url: "/login" },
  { name: "02-dashboard", url: "/dashboard" },
  { name: "03-proposals", url: "/proposals" },
  { name: "04-proposals-new", url: "/proposals/new" },
  { name: "05-bids", url: "/bids" },
  { name: "06-analytics", url: "/analytics" },
  { name: "07-kb-search", url: "/kb/search" },
  { name: "08-kb-content", url: "/kb/content" },
  { name: "09-archive", url: "/archive" },
  { name: "10-admin", url: "/admin" },
];

async function main() {
  if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    colorScheme: "dark",
  });

  for (const p of PAGES) {
    const page = await ctx.newPage();
    try {
      await page.goto(`${BASE}${p.url}`, { waitUntil: "networkidle", timeout: 15000 });
    } catch {
      await page.goto(`${BASE}${p.url}`, { waitUntil: "load", timeout: 10000 }).catch(() => {});
    }
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT, `${p.name}.png`), fullPage: false });
    console.log(`  captured: ${p.name}`);
    await page.close();
  }

  await browser.close();
  console.log(`\nDone! ${PAGES.length} screenshots in ${OUT}`);
}

main().catch(console.error);
