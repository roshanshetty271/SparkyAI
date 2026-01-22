/**
 * End-to-End Tests for Chat Functionality
 * 
 * Tests the complete user flow from landing page to chat interaction.
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

test.describe('Chat Widget E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the main page
    await page.goto(BASE_URL);
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should display chat widget on homepage', async ({ page }) => {
    // Check if chat widget is visible
    const chatWidget = page.locator('[data-testid="chat-widget"]');
    await expect(chatWidget).toBeVisible();
  });

  test('should open chat interface when widget is clicked', async ({ page }) => {
    // Click on chat widget
    const chatWidget = page.locator('[data-testid="chat-widget"]');
    await chatWidget.click();
    
    // Verify chat interface opens
    const chatInterface = page.locator('[data-testid="chat-interface"]');
    await expect(chatInterface).toBeVisible();
    
    // Verify input field is visible
    const inputField = page.locator('[data-testid="chat-input"]');
    await expect(inputField).toBeVisible();
  });

  test('should send a message and receive a response', async ({ page }) => {
    // Open chat
    await page.locator('[data-testid="chat-widget"]').click();
    
    // Type a message
    const inputField = page.locator('[data-testid="chat-input"]');
    await inputField.fill('Tell me about your React experience');
    
    // Send message
    const sendButton = page.locator('[data-testid="send-button"]');
    await sendButton.click();
    
    // Wait for response (with timeout)
    const messageList = page.locator('[data-testid="message-list"]');
    await expect(messageList.locator('.user-message').last()).toContainText('React experience');
    
    // Wait for AI response
    await expect(messageList.locator('.ai-message').last()).toBeVisible({ timeout: 10000 });
    
    // Verify response is not empty
    const aiMessage = await messageList.locator('.ai-message').last().textContent();
    expect(aiMessage?.length).toBeGreaterThan(0);
  });

  test('should handle multiple messages in conversation', async ({ page }) => {
    // Open chat
    await page.locator('[data-testid="chat-widget"]').click();
    
    const inputField = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    const messageList = page.locator('[data-testid="message-list"]');
    
    // First message
    await inputField.fill('Hello');
    await sendButton.click();
    await expect(messageList.locator('.ai-message').first()).toBeVisible({ timeout: 10000 });
    
    // Second message
    await inputField.fill('What projects have you built?');
    await sendButton.click();
    await expect(messageList.locator('.ai-message').nth(1)).toBeVisible({ timeout: 10000 });
    
    // Verify we have 2 user messages and 2 AI responses
    const userMessages = messageList.locator('.user-message');
    const aiMessages = messageList.locator('.ai-message');
    
    await expect(userMessages).toHaveCount(2);
    await expect(aiMessages).toHaveCount(2);
  });

  test('should display typing indicator while waiting for response', async ({ page }) => {
    // Open chat
    await page.locator('[data-testid="chat-widget"]').click();
    
    // Send message
    const inputField = page.locator('[data-testid="chat-input"]');
    await inputField.fill('Tell me about yourself');
    await page.locator('[data-testid="send-button"]').click();
    
    // Check for typing indicator
    const typingIndicator = page.locator('[data-testid="typing-indicator"]');
    await expect(typingIndicator).toBeVisible({ timeout: 2000 });
    
    // Wait for response to complete
    await expect(typingIndicator).toHidden({ timeout: 15000 });
  });

  test('should clear input field after sending message', async ({ page }) => {
    // Open chat
    await page.locator('[data-testid="chat-widget"]').click();
    
    const inputField = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // Type and send
    await inputField.fill('Test message');
    await sendButton.click();
    
    // Verify input is cleared
    await expect(inputField).toHaveValue('');
  });

  test('should disable send button while processing', async ({ page }) => {
    // Open chat
    await page.locator('[data-testid="chat-widget"]').click();
    
    const inputField = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // Send message
    await inputField.fill('Test message');
    await sendButton.click();
    
    // Verify send button is disabled while processing
    await expect(sendButton).toBeDisabled();
    
    // Wait for response
    await expect(page.locator('.ai-message').last()).toBeVisible({ timeout: 15000 });
    
    // Verify send button is enabled again
    await expect(sendButton).toBeEnabled();
  });

  test('should handle error gracefully', async ({ page }) => {
    // Intercept API calls and simulate error
    await page.route(`${API_URL}/chat`, route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' }),
      });
    });
    
    // Open chat
    await page.locator('[data-testid="chat-widget"]').click();
    
    // Send message
    const inputField = page.locator('[data-testid="chat-input"]');
    await inputField.fill('Test error handling');
    await page.locator('[data-testid="send-button"]').click();
    
    // Check for error message
    const errorMessage = page.locator('[data-testid="error-message"]');
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
  });

  test('should validate input length', async ({ page }) => {
    // Open chat
    await page.locator('[data-testid="chat-widget"]').click();
    
    const inputField = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // Try to send empty message
    await inputField.fill('');
    await expect(sendButton).toBeDisabled();
    
    // Try to send very long message
    const longMessage = 'a'.repeat(600);
    await inputField.fill(longMessage);
    
    // Should either be disabled or show warning
    const isDisabled = await sendButton.isDisabled();
    const hasWarning = await page.locator('[data-testid="input-warning"]').isVisible();
    
    expect(isDisabled || hasWarning).toBeTruthy();
  });

  test('should persist conversation when minimizing and reopening', async ({ page }) => {
    // Open chat
    await page.locator('[data-testid="chat-widget"]').click();
    
    // Send a message
    const inputField = page.locator('[data-testid="chat-input"]');
    await inputField.fill('Remember this message');
    await page.locator('[data-testid="send-button"]').click();
    
    // Wait for response
    await expect(page.locator('.ai-message').last()).toBeVisible({ timeout: 10000 });
    
    // Close chat
    const closeButton = page.locator('[data-testid="close-chat"]');
    await closeButton.click();
    
    // Reopen chat
    await page.locator('[data-testid="chat-widget"]').click();
    
    // Verify previous message is still there
    const messageList = page.locator('[data-testid="message-list"]');
    await expect(messageList.locator('.user-message')).toContainText('Remember this message');
  });
});

test.describe('Visualization E2E Tests', () => {
  test('should navigate to How It Works page', async ({ page }) => {
    await page.goto(BASE_URL);
    
    // Click on "How It Works" link
    const howItWorksLink = page.locator('a[href="/how-it-works"]');
    await howItWorksLink.click();
    
    // Verify navigation
    await expect(page).toHaveURL(`${BASE_URL}/how-it-works`);
  });

  test('should display agent graph visualization', async ({ page }) => {
    await page.goto(`${BASE_URL}/how-it-works`);
    
    // Wait for visualization to load
    const agentGraph = page.locator('[data-testid="agent-graph"]');
    await expect(agentGraph).toBeVisible({ timeout: 5000 });
    
    // Check for D3 SVG elements
    const svg = agentGraph.locator('svg');
    await expect(svg).toBeVisible();
    
    // Verify nodes are rendered
    const nodes = svg.locator('circle, rect');
    const nodeCount = await nodes.count();
    expect(nodeCount).toBeGreaterThan(0);
  });

  test('should display embedding explorer', async ({ page }) => {
    await page.goto(`${BASE_URL}/how-it-works`);
    
    // Wait for embedding explorer to load
    const embeddingExplorer = page.locator('[data-testid="embedding-explorer"]');
    await expect(embeddingExplorer).toBeVisible({ timeout: 5000 });
    
    // Check for visualization elements
    const svg = embeddingExplorer.locator('svg');
    await expect(svg).toBeVisible();
    
    // Verify points are rendered
    const points = svg.locator('circle');
    const pointCount = await points.count();
    expect(pointCount).toBeGreaterThan(0);
  });

  test('should update visualizations when chat is active', async ({ page }) => {
    await page.goto(`${BASE_URL}/how-it-works`);
    
    // Open chat
    await page.locator('[data-testid="chat-widget"]').click();
    
    // Send a message
    const inputField = page.locator('[data-testid="chat-input"]');
    await inputField.fill('What are your skills?');
    await page.locator('[data-testid="send-button"]').click();
    
    // Wait a moment for WebSocket events
    await page.waitForTimeout(1000);
    
    // Check if agent graph updates (active node changes)
    const agentGraph = page.locator('[data-testid="agent-graph"]');
    const activeNodes = agentGraph.locator('.node-active');
    
    // Should have at least one active node during processing
    const hasActiveNodes = await activeNodes.count() > 0;
    expect(hasActiveNodes).toBeTruthy();
  });
});

test.describe('Accessibility Tests', () => {
  test('should be keyboard navigable', async ({ page }) => {
    await page.goto(BASE_URL);
    
    // Tab to chat widget
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Open with Enter
    await page.keyboard.press('Enter');
    
    // Verify chat opened
    const chatInterface = page.locator('[data-testid="chat-interface"]');
    await expect(chatInterface).toBeVisible();
    
    // Tab to input field
    await page.keyboard.press('Tab');
    
    // Type message
    await page.keyboard.type('Accessibility test');
    
    // Tab to send button and press Enter
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    
    // Verify message was sent
    await expect(page.locator('.user-message').last()).toContainText('Accessibility test');
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto(BASE_URL);
    
    // Open chat
    await page.locator('[data-testid="chat-widget"]').click();
    
    // Check for ARIA labels on key elements
    const inputField = page.locator('[data-testid="chat-input"]');
    const ariaLabel = await inputField.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();
    
    const sendButton = page.locator('[data-testid="send-button"]');
    const buttonLabel = await sendButton.getAttribute('aria-label');
    expect(buttonLabel).toBeTruthy();
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto(BASE_URL);
    
    // This would typically use axe-core or similar
    // For now, we just verify text is readable
    const mainText = page.locator('body');
    await expect(mainText).toBeVisible();
    
    // Check computed styles (basic check)
    const styles = await page.evaluate(() => {
      const element = document.querySelector('body');
      const computed = window.getComputedStyle(element!);
      return {
        color: computed.color,
        backgroundColor: computed.backgroundColor,
      };
    });
    
    expect(styles.color).toBeTruthy();
    expect(styles.backgroundColor).toBeTruthy();
  });
});

test.describe('Performance Tests', () => {
  test('should load page within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Page should load in less than 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should handle WebSocket connection efficiently', async ({ page }) => {
    await page.goto(`${BASE_URL}/how-it-works`);
    
    // Monitor WebSocket connections
    const wsConnections: any[] = [];
    
    page.on('websocket', ws => {
      wsConnections.push(ws);
    });
    
    // Open chat (should establish WebSocket)
    await page.locator('[data-testid="chat-widget"]').click();
    
    // Wait a moment for connection
    await page.waitForTimeout(1000);
    
    // Should have established WebSocket connection
    expect(wsConnections.length).toBeGreaterThan(0);
  });
});
