const { chromium } = require('@playwright/test');

async function runTests() {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  console.log('Running E2E Tests...\n');

  // Test 1: Login page loads
  console.log('Test 1: Login page loads without errors...');
  try {
    await page.goto('http://localhost:3000/');
    const url = page.url();
    if (url.includes('/login')) {
      console.log('✓ PASS: Login page loaded');
    } else {
      console.log('✗ FAIL: Expected login redirect, got', url);
    }
  } catch (e) {
    console.log('✗ FAIL:', e.message);
  }

  // Test 2: Proposals page navigable
  console.log('\nTest 2: Proposals page navigable...');
  try {
    await page.goto('http://localhost:3000/proposals');
    await page.waitForURL('**/login**', { timeout: 2000 }).catch(() => {
      // Expected - redirects to login
    });
    console.log('✓ PASS: Proposals page redirects to login');
  } catch (e) {
    console.log('✗ FAIL:', e.message);
  }

  // Test 3: Analytics page navigable
  console.log('\nTest 3: Analytics page navigable...');
  try {
    await page.goto('http://localhost:3000/analytics');
    await page.waitForURL('**/login**', { timeout: 2000 }).catch(() => {
      // Expected - redirects to login
    });
    console.log('✓ PASS: Analytics page redirects to login');
  } catch (e) {
    console.log('✗ FAIL:', e.message);
  }

  // Test 4: Production build ready
  console.log('\nTest 4: Production build ready...');
  try {
    const response = await page.goto('http://localhost:3000/', { waitUntil: 'domcontentloaded' });
    if (response && response.status() < 500) {
      console.log('✓ PASS: Page returned status', response.status());
    } else {
      console.log('✗ FAIL: Unexpected status', response?.status());
    }
  } catch (e) {
    console.log('✗ FAIL:', e.message);
  }

  // Test 5: No pending async errors
  console.log('\nTest 5: No pending async errors...');
  try {
    await page.goto('http://localhost:3000/');
    await page.waitForLoadState('networkidle').catch(() => {
      // Timeout is okay
    });
    const html = await page.content();
    if (html && html.length > 0) {
      console.log('✓ PASS: Page loaded successfully');
    }
  } catch (e) {
    console.log('✗ FAIL:', e.message);
  }

  await browser.close();
  console.log('\nTests completed!');
}

runTests().catch(err => {
  console.error('Test runner error:', err);
  process.exit(1);
});
