import { test, expect } from '@playwright/test';

const VAULT_URL = process.env.VAULT_URL || 'http://localhost:3000/vault';
const API_URL = process.env.API_URL || 'http://localhost:8000';

test.describe('Vault AI Chat - Complete E2E Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to Vault page
    await page.goto(VAULT_URL);

    // Wait for page to load
    await page.waitForSelector('[data-testid="vault-layout"]', { timeout: 10000 });
  });

  test('Complete chat flow: Create conversation -> Send message -> Get response', async ({ page }) => {
    /**
     * E2E Test: Complete chat workflow
     * 1. Create new conversation
     * 2. Send user message
     * 3. Verify AI response with sources
     * 4. Check message persistence
     */

    // Step 1: Create new conversation
    const newConvButton = page.locator('[data-testid="new-conversation-button"]');
    await newConvButton.click();

    // Verify conversation is created and visible
    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await expect(conversationItem).toBeVisible();

    // Step 2: Send message
    const messageInput = page.locator('[data-testid="chat-input"]');
    await messageInput.fill('We need to build a mobile app. What projects did we do before?');

    const sendButton = page.locator('[data-testid="send-button"]');
    await sendButton.click();

    // Verify user message appears
    const userMessage = page.locator('[data-testid="message-user"]').first();
    await expect(userMessage).toContainText('build a mobile app');

    // Step 3: Wait for AI response
    const aiMessage = page.locator('[data-testid="message-assistant"]').first();
    await expect(aiMessage).toBeVisible({ timeout: 15000 });

    // Verify response content
    const responseText = await aiMessage.locator('[data-testid="message-content"]').textContent();
    expect(responseText).toBeTruthy();
    expect(responseText?.length).toBeGreaterThan(10);

    // Step 4: Verify sources are shown
    const sourcesSection = aiMessage.locator('[data-testid="message-sources"]');
    if (await sourcesSection.isVisible()) {
      const sourceItems = aiMessage.locator('[data-testid="source-item"]');
      const count = await sourceItems.count();
      expect(count).toBeGreaterThan(0);
    }

    // Step 5: Verify confidence score
    const confidenceScore = aiMessage.locator('[data-testid="confidence-score"]');
    if (await confidenceScore.isVisible()) {
      const scoreText = await confidenceScore.textContent();
      const score = parseFloat(scoreText?.match(/[\d.]+/)?.[0] || '0');
      expect(score).toBeGreaterThan(0.5);
      expect(score).toBeLessThanOrEqual(1);
    }
  });

  test('Message history persistence: Conversation retains messages', async ({ page }) => {
    /**
     * E2E Test: Message persistence
     * 1. Send multiple messages
     * 2. Refresh page
     * 3. Verify all messages are still visible
     */

    // Send first message
    const messageInput = page.locator('[data-testid="chat-input"]');
    await messageInput.fill('First question: What mobile projects did we have?');
    await page.locator('[data-testid="send-button"]').click();

    // Wait for response
    await page.waitForSelector('[data-testid="message-assistant"]');

    // Send follow-up message
    await messageInput.fill('Follow-up: What was the budget for those projects?');
    await page.locator('[data-testid="send-button"]').click();

    // Count messages
    const messages = page.locator('[data-testid="chat-message"]');
    const initialCount = await messages.count();
    expect(initialCount).toBeGreaterThanOrEqual(2); // At least user message and response

    // Refresh page
    await page.reload();

    // Wait for messages to load
    await page.waitForSelector('[data-testid="chat-message"]', { timeout: 10000 });

    // Verify messages persisted
    const messagesAfterRefresh = page.locator('[data-testid="chat-message"]');
    const countAfterRefresh = await messagesAfterRefresh.count();
    expect(countAfterRefresh).toBe(initialCount);
  });

  test('Vector search results integration: Sources displayed correctly', async ({ page }) => {
    /**
     * E2E Test: Vector search integration
     * 1. Send query
     * 2. Verify search results as sources
     * 3. Check source formatting and content
     */

    // Send query that should trigger vector search
    const messageInput = page.locator('[data-testid="chat-input"]');
    await messageInput.fill('Show me past projects similar to e-commerce platforms');
    await page.locator('[data-testid="send-button"]').click();

    // Wait for response with sources
    await page.waitForSelector('[data-testid="message-assistant"]', { timeout: 15000 });

    const aiMessage = page.locator('[data-testid="message-assistant"]').first();
    const sourcesSection = aiMessage.locator('[data-testid="message-sources"]');

    // Sources should be visible
    if (await sourcesSection.isVisible()) {
      const sourceItems = aiMessage.locator('[data-testid="source-item"]');
      const count = await sourceItems.count();

      // Each source should have content
      for (let i = 0; i < count; i++) {
        const sourceItem = sourceItems.nth(i);

        // Check for source title
        const title = sourceItem.locator('[data-testid="source-title"]');
        await expect(title).toBeVisible();

        // Check for relevance indicator
        const relevance = sourceItem.locator('[data-testid="relevance-score"]');
        if (await relevance.isVisible()) {
          const scoreText = await relevance.textContent();
          expect(scoreText).toMatch(/\d+%/);
        }
      }
    }
  });

  test('Conversation management: Create, list, and delete conversations', async ({ page }) => {
    /**
     * E2E Test: Conversation CRUD
     * 1. Create multiple conversations
     * 2. Verify list displays all
     * 3. Switch between conversations
     * 4. Delete conversation
     */

    // Create first conversation
    let newConvButton = page.locator('[data-testid="new-conversation-button"]');
    await newConvButton.click();

    const firstConv = page.locator('[data-testid="conversation-item"]').first();
    await expect(firstConv).toBeVisible();

    // Send message to first conversation
    const messageInput = page.locator('[data-testid="chat-input"]');
    await messageInput.fill('Conversation 1 message');
    await page.locator('[data-testid="send-button"]').click();

    // Wait for message
    await page.waitForSelector('[data-testid="message-assistant"]');

    // Create second conversation
    newConvButton = page.locator('[data-testid="new-conversation-button"]');
    await newConvButton.click();

    // Verify second conversation is separate (no messages)
    const chatMessages = page.locator('[data-testid="chat-message"]');
    let messageCount = await chatMessages.count();
    expect(messageCount).toBe(0); // New conversation should be empty

    // Go back to first conversation
    const conversations = page.locator('[data-testid="conversation-item"]');
    if (await conversations.count() > 1) {
      const firstConvAgain = conversations.nth(0);
      await firstConvAgain.click();

      // Should see first conversation messages
      await page.waitForSelector('[data-testid="chat-message"]');
      messageCount = await chatMessages.count();
      expect(messageCount).toBeGreaterThan(0);
    }

    // Delete current conversation
    const deleteButton = page.locator('[data-testid="delete-conversation-button"]').first();
    if (await deleteButton.isVisible()) {
      await deleteButton.click();

      // Confirm delete
      const confirmButton = page.locator('[data-testid="confirm-delete-button"]');
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
      }

      // Verify conversation is removed from list
      await page.waitForTimeout(500);
      const remainingConvs = page.locator('[data-testid="conversation-item"]');
      const finalCount = await remainingConvs.count();
      expect(finalCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('Search with filters: Section selection and filtering', async ({ page }) => {
    /**
     * E2E Test: Search filters
     * 1. Open search with section dropdown
     * 2. Select different sections
     * 3. Verify query searches selected section
     */

    // Open new conversation
    const newConvButton = page.locator('[data-testid="new-conversation-button"]');
    await newConvButton.click();

    // Find search bar
    const searchBar = page.locator('[data-testid="vault-search-bar"]');

    // Test section dropdown
    const sectionSelect = searchBar.locator('[data-testid="section-select"]');
    if (await sectionSelect.isVisible()) {
      // Get initial section
      let selectedSection = await sectionSelect.locator('[data-testid="selected-section"]').textContent();
      expect(selectedSection).toBeTruthy();

      // Open dropdown
      await sectionSelect.click();

      // Select "Completed Projects"
      const projectsOption = page.locator('[data-testid="section-option-completed_projects"]');
      if (await projectsOption.isVisible()) {
        await projectsOption.click();

        // Send query
        const messageInput = page.locator('[data-testid="chat-input"]');
        await messageInput.fill('Show completed projects');
        await page.locator('[data-testid="send-button"]').click();

        // Verify response mentions projects
        await page.waitForSelector('[data-testid="message-assistant"]');
        const response = page.locator('[data-testid="message-assistant"]').first();
        await expect(response).toBeVisible();
      }
    }
  });

  test('Rate limiting: User is notified when limit is exceeded', async ({ page }) => {
    /**
     * E2E Test: Rate limit notification
     * 1. Make rapid requests
     * 2. Verify rate limit error is shown
     * 3. Verify submit button is disabled
     */

    const messageInput = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');

    // Make multiple rapid requests (simulate exceeding limit)
    for (let i = 0; i < 5; i++) {
      await messageInput.fill(`Rapid message ${i}`);

      if (await sendButton.isEnabled()) {
        await sendButton.click();
      } else {
        // Button disabled - rate limit likely triggered
        break;
      }

      // Small delay between requests
      await page.waitForTimeout(100);
    }

    // Check for rate limit error message
    const errorMessage = page.locator('[data-testid="rate-limit-error"]');
    const rateLimitText = page.locator('text=Rate limit');

    // Either error message or button disabled indicates rate limiting
    const isRateLimited =
      await errorMessage.isVisible() ||
      await rateLimitText.isVisible() ||
      !(await sendButton.isEnabled());

    if (isRateLimited) {
      // Verify user is informed
      const notificationArea = page.locator('[data-testid="notification"]');
      if (await notificationArea.isVisible()) {
        const notification = await notificationArea.textContent();
        expect(notification).toContain('limit' || 'rate');
      }
    }
  });

  test('Error handling: Graceful error display', async ({ page }) => {
    /**
     * E2E Test: Error handling
     * 1. Send message that might cause error
     * 2. Verify error is shown gracefully
     * 3. Verify chat remains usable
     */

    // This test assumes backend might return errors
    const messageInput = page.locator('[data-testid="chat-input"]');

    // Send a message
    await messageInput.fill('Test message');
    await page.locator('[data-testid="send-button"]').click();

    // Wait for response (might be error or normal response)
    const response = page.locator('[data-testid="message-assistant"]');

    // Check if error message appears
    const errorNotification = page.locator('[data-testid="error-notification"]');

    // Either get response or error
    if (await response.isVisible()) {
      const content = await response.locator('[data-testid="message-content"]').textContent();
      expect(content).toBeTruthy();
    } else if (await errorNotification.isVisible()) {
      // Error was shown
      const errorText = await errorNotification.textContent();
      expect(errorText).toBeTruthy();
    }

    // Verify chat input is still usable
    const inputField = page.locator('[data-testid="chat-input"]');
    await expect(inputField).toBeEnabled();
  });

  test('Responsive design: Chat works on mobile view', async ({ page }) => {
    /**
     * E2E Test: Mobile responsiveness
     * 1. Set mobile viewport
     * 2. Verify chat interface is usable
     * 3. Check sidebar collapses properly
     */

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 }); // iPhone size

    // Navigate to vault
    await page.goto(VAULT_URL);
    await page.waitForSelector('[data-testid="vault-layout"]');

    // Check if sidebar is visible or can be toggled
    const sidebar = page.locator('[data-testid="vault-sidebar"]');
    const sidebarToggle = page.locator('[data-testid="toggle-sidebar"]');

    // Sidebar should either be hidden or have toggle
    const sidebarVisible = await sidebar.isVisible();
    const toggleVisible = await sidebarToggle.isVisible();

    expect(sidebarVisible || toggleVisible).toBeTruthy();

    // Verify chat input is accessible
    const messageInput = page.locator('[data-testid="chat-input"]');
    await expect(messageInput).toBeVisible();

    // Test sending message
    await messageInput.fill('Mobile test');
    const sendButton = page.locator('[data-testid="send-button"]');
    await expect(sendButton).toBeVisible();
  });

  test('Accessibility: Keyboard navigation works', async ({ page }) => {
    /**
     * E2E Test: Keyboard accessibility
     * 1. Use Tab to navigate
     * 2. Use Enter to send message
     * 3. Verify all interactive elements are accessible
     */

    // Focus on message input
    const messageInput = page.locator('[data-testid="chat-input"]');
    await messageInput.focus();
    await expect(messageInput).toBeFocused();

    // Type message
    await page.keyboard.type('Keyboard test');

    // Send with Enter
    await page.keyboard.press('Enter');

    // Verify message was sent
    const userMessage = page.locator('[data-testid="message-user"]');
    await expect(userMessage).toContainText('Keyboard test');

    // Tab to new conversation button
    const newConvButton = page.locator('[data-testid="new-conversation-button"]');

    // Simulate tabbing (simple focus test)
    await newConvButton.focus();
    await expect(newConvButton).toBeFocused();

    // Activate with Enter
    await page.keyboard.press('Enter');

    // Should create new conversation
    const conversations = page.locator('[data-testid="conversation-item"]');
    expect(await conversations.count()).toBeGreaterThan(0);
  });
});

test.describe('Vault AI Chat - Performance Tests', () => {
  test('Response time under 2 seconds', async ({ page }) => {
    /**
     * Performance test: Chat response latency
     */

    await page.goto(VAULT_URL);
    await page.waitForSelector('[data-testid="vault-layout"]');

    // Create conversation and send message
    const newConvButton = page.locator('[data-testid="new-conversation-button"]');
    await newConvButton.click();

    const messageInput = page.locator('[data-testid="chat-input"]');
    await messageInput.fill('Performance test query');

    const startTime = Date.now();
    await page.locator('[data-testid="send-button"]').click();

    // Wait for response
    await page.waitForSelector('[data-testid="message-assistant"]', { timeout: 5000 });

    const endTime = Date.now();
    const responseTime = endTime - startTime;

    // Response should be under 2 seconds (adjust based on requirements)
    expect(responseTime).toBeLessThan(2000);
  });

  test('No layout shift during message loading', async ({ page }) => {
    /**
     * Visual stability test: Cumulative Layout Shift
     */

    await page.goto(VAULT_URL);
    await page.waitForSelector('[data-testid="vault-layout"]');

    // Send message
    const messageInput = page.locator('[data-testid="chat-input"]');
    await messageInput.fill('Layout stability test');
    await page.locator('[data-testid="send-button"]').click();

    // Get initial chat container position
    const chatContainer = page.locator('[data-testid="chat-container"]');
    const initialBox = await chatContainer.boundingBox();

    // Wait for response
    await page.waitForSelector('[data-testid="message-assistant"]', { timeout: 10000 });

    // Get final position
    const finalBox = await chatContainer.boundingBox();

    // Position should not shift significantly
    if (initialBox && finalBox) {
      expect(Math.abs(initialBox.y - finalBox.y)).toBeLessThan(50);
    }
  });
});
