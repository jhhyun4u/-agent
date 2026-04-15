import { test, expect } from '@playwright/test';

test.describe('Knowledge Base Search', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to knowledge base page
    await page.goto('/knowledge');

    // Wait for search component to load
    await page.waitForSelector('input[placeholder*="조직 지식 검색"]');
  });

  test('should display knowledge search interface', async ({ page }) => {
    // Check for search input
    const searchInput = page.locator('input[placeholder*="조직 지식 검색"]');
    await expect(searchInput).toBeVisible();

    // Check for search button
    const searchButton = page.locator('button', { has: page.locator('svg') }).first();
    await expect(searchButton).toBeVisible();

    // Check for type filters
    const typeLabels = ['역량', '발주기관', '시장가격', '교훈'];
    for (const label of typeLabels) {
      await expect(page.locator('button', { hasText: label })).toBeVisible();
    }

    // Check for freshness slider
    const freshnessSlider = page.locator('input[type="range"]');
    await expect(freshnessSlider).toBeVisible();
  });

  test('should perform basic search', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="조직 지식 검색"]');
    const searchButton = page.locator('button[class*="bg-blue-600"]').first();

    // Type search query
    await searchInput.fill('IoT 플랫폼');

    // Wait for the API call to complete
    const [response] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/knowledge/search') && resp.status() === 200),
      searchButton.click(),
    ]);

    // Verify response is successful
    expect(response.ok()).toBeTruthy();

    // Check for results section
    const resultsCount = page.locator('text=/\\d+개 결과/');
    await expect(resultsCount).toBeVisible({ timeout: 5000 });
  });

  test('should filter search by knowledge type', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="조직 지식 검색"]');
    const typeButton = page.locator('button', { hasText: '역량' });
    const searchButton = page.locator('button[class*="bg-blue-600"]').first();

    // Click type filter to select it
    await typeButton.click();
    await expect(typeButton).toHaveClass(/bg-blue-600/);

    // Perform search
    await searchInput.fill('개발 경험');

    const [response] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/knowledge/search') && resp.status() === 200),
      searchButton.click(),
    ]);

    expect(response.ok()).toBeTruthy();

    // Verify API was called with correct filter
    const requestBody = await response.request().postDataJSON();
    expect(requestBody.filters.knowledge_types).toContain('capability');
  });

  test('should adjust freshness filter', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="조직 지식 검색"]');
    const freshnessSlider = page.locator('input[type="range"]');
    const searchButton = page.locator('button[class*="bg-blue-600"]').first();

    // Set freshness to 70
    await freshnessSlider.fill('70');

    // Verify slider value changed
    const sliderValue = await freshnessSlider.inputValue();
    expect(parseInt(sliderValue)).toBeGreaterThanOrEqual(60);

    // Perform search
    await searchInput.fill('시장 정보');

    const [response] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/knowledge/search') && resp.status() === 200),
      searchButton.click(),
    ]);

    // Verify API was called with freshness filter
    const requestBody = await response.request().postDataJSON();
    expect(requestBody.filters.freshness_min).toBeDefined();
  });

  test('should display search results with metadata', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="조직 지식 검색"]');
    const searchButton = page.locator('button[class*="bg-blue-600"]').first();

    await searchInput.fill('클라이언트 정보');
    await searchButton.click();

    // Wait for results to appear
    await page.waitForSelector('[class*="border-gray-200"]', { timeout: 5000 });

    // Get first result (if available)
    const firstResult = page.locator('[class*="border-gray-200"]').first();
    await expect(firstResult).toBeVisible();

    // Check for result metadata
    const sourceDoc = firstResult.locator('text=/^[^$]+/').first();
    await expect(sourceDoc).toBeVisible();

    // Check for confidence score
    const confidenceText = firstResult.locator('text=/확신:/');
    await expect(confidenceText).toBeVisible();

    // Check for freshness score
    const freshnessText = firstResult.locator('text=/신선도:/');
    await expect(freshnessText).toBeVisible();
  });

  test('should handle empty search gracefully', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="조직 지식 검색"]');
    const searchButton = page.locator('button[class*="bg-blue-600"]').first();

    // Leave search empty and click search
    await searchInput.fill('');
    await searchButton.click();

    // Should not make API call for empty query
    // Check that no results message is shown
    const noResultsMsg = page.locator('text=/결과가 없습니다/');

    // Wait a moment to ensure no unintended API calls happen
    await page.waitForTimeout(500);

    // Either no API call is made, or results area remains empty
    const resultsSection = page.locator('div:has-text("개 결과")');
    const resultsVisible = await resultsSection.isVisible({ timeout: 1000 }).catch(() => false);

    expect(!resultsVisible).toBeTruthy();
  });

  test('should support Enter key to search', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="조직 지식 검색"]');

    await searchInput.fill('조직 역량');

    // Press Enter
    const [response] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/knowledge/search') && resp.status() === 200),
      searchInput.press('Enter'),
    ]);

    expect(response.ok()).toBeTruthy();

    // Wait for results
    await page.waitForSelector('[class*="border-gray-200"]', { timeout: 5000 }).catch(() => null);
  });

  test('should display error message on search failure', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="조직 지식 검색"]');
    const searchButton = page.locator('button[class*="bg-blue-600"]').first();

    // Intercept and mock a failed request
    await page.route('**/knowledge/search', route => {
      route.abort('failed');
    });

    await searchInput.fill('테스트');
    await searchButton.click();

    // Wait for error message
    const errorMessage = page.locator('text=/Search failed|검색 실패/');
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
  });

  test('should display loading state during search', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="조직 지식 검색"]');
    const searchButton = page.locator('button[class*="bg-blue-600"]').first();

    // Slow down network to observe loading state
    await page.route('**/knowledge/search', route => {
      setTimeout(() => {
        route.continue();
      }, 1000);
    });

    await searchInput.fill('로딩 테스트');

    // Click search and immediately check for loading state
    const searchPromise = searchButton.click();

    // Wait for loading text to appear
    const loadingText = page.locator('text=/검색 중/');
    await expect(loadingText).toBeVisible({ timeout: 2000 });

    // Wait for search to complete
    await searchPromise;

    // Loading state should disappear
    await expect(loadingText).not.toBeVisible({ timeout: 5000 });
  });

  test('should allow multiple searches in sequence', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="조직 지식 검색"]');
    const searchButton = page.locator('button[class*="bg-blue-600"]').first();

    // First search
    await searchInput.fill('첫번째 검색');
    await searchButton.click();
    await page.waitForTimeout(500);

    // Second search with different query
    await searchInput.fill('두번째 검색');
    await searchButton.click();
    await page.waitForTimeout(500);

    // Third search
    await searchInput.fill('세번째 검색');
    await searchButton.click();
    await page.waitForTimeout(500);

    // All searches should complete without errors
    const errorMessages = page.locator('[class*="bg-red-50"]');
    const errorCount = await errorMessages.count();
    expect(errorCount).toBe(0);
  });

  test('should combine multiple filters correctly', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="조직 지식 검색"]');
    const roleButton = page.locator('button', { hasText: '역량' });
    const intelButton = page.locator('button', { hasText: '발주기관' });
    const freshnessSlider = page.locator('input[type="range"]');
    const searchButton = page.locator('button[class*="bg-blue-600"]').first();

    // Select multiple type filters
    await roleButton.click();
    await intelButton.click();

    // Set freshness filter
    await freshnessSlider.fill('60');

    // Perform search
    await searchInput.fill('종합 검색 테스트');

    const [response] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/knowledge/search') && resp.status() === 200),
      searchButton.click(),
    ]);

    // Verify all filters were sent
    const requestBody = await response.request().postDataJSON();
    expect(requestBody.filters.knowledge_types).toContain('capability');
    expect(requestBody.filters.knowledge_types).toContain('client_intel');
    expect(requestBody.filters.freshness_min).toBeGreaterThan(0);
  });
});
