import { chromium } from "@playwright/test";
import path from "path";
import fs from "fs";

const BASE = "http://localhost:3000";
const OUT = path.join(__dirname, "../screenshots");
const STORAGE = path.join(__dirname, ".auth/user.json");

const PAGES = [
  { name: "01-login", url: "/login", auth: false },
  { name: "02-dashboard", url: "/dashboard", auth: true },
  { name: "03-proposals", url: "/proposals", auth: true },
  { name: "04-proposals-new", url: "/proposals/new", auth: true },
  { name: "05-bids", url: "/bids", auth: true },
  { name: "06-analytics", url: "/analytics", auth: true },
  { name: "07-kb-search", url: "/kb/search", auth: true },
  { name: "08-kb-content", url: "/kb/content", auth: true },
  { name: "09-kb-clients", url: "/kb/clients", auth: true },
  { name: "10-kb-competitors", url: "/kb/competitors", auth: true },
  { name: "11-kb-lessons", url: "/kb/lessons", auth: true },
  { name: "12-archive", url: "/archive", auth: true },
  { name: "13-admin", url: "/admin", auth: true },
  { name: "14-admin-users", url: "/admin/users", auth: true },
  { name: "15-pricing", url: "/pricing", auth: true },
  { name: "16-bids-settings", url: "/bids/settings", auth: true },
];

async function main() {
  if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

  const browser = await chromium.launch();

  // non-auth context
  const publicCtx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    colorScheme: "dark",
  });

  // auth context
  const authCtx = fs.existsSync(STORAGE)
    ? await browser.newContext({
        viewport: { width: 1440, height: 900 },
        colorScheme: "dark",
        storageState: STORAGE,
      })
    : null;

  for (const p of PAGES) {
    const ctx = p.auth && authCtx ? authCtx : publicCtx;
    const page = await ctx.newPage();
    try {
      await page.goto(`${BASE}${p.url}`, {
        waitUntil: "networkidle",
        timeout: 20000,
      });
    } catch {
      try {
        await page.goto(`${BASE}${p.url}`, {
          waitUntil: "load",
          timeout: 10000,
        });
      } catch {
        /* best effort */
      }
    }
    await page.waitForTimeout(1500);
    await page.screenshot({
      path: path.join(OUT, `${p.name}.png`),
      fullPage: false,
    });
    console.log(`  captured: ${p.name}`);
    await page.close();
  }

  await browser.close();
  console.log(`\nDone! ${PAGES.length} screenshots in ${OUT}`);
}

main().catch(console.error);
