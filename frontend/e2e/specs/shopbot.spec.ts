import { test, expect } from '@playwright/test'
import { ShopBotPage } from '../pages/ShopBotPage'

test.describe('ShopBot Demo', () => {
  let shopBot: ShopBotPage

  test.beforeEach(async ({ page }) => {
    shopBot = new ShopBotPage(page)
    await shopBot.goto()
  })

  test('should load ShopBot page with initial message', async ({ page }) => {
    await expect(page).toHaveURL('/demo/shopbot')
    await expect(page.locator('text=ShopBot ready')).toBeVisible()
  })

  test('should process product purchase request', async ({ page }) => {
    await shopBot.sendMessage('I want to buy a wireless mouse for under ₹1000')
    await shopBot.waitForBotResponse()

    // Bot should respond (either success, no_products, or denied)
    const botMessages = await page.locator('div.bg-card.border.mr-auto').allInnerTexts()
    expect(botMessages.length).toBeGreaterThan(0)
    // At least one bot message should have content
    expect(botMessages.some(msg => msg.length > 0)).toBe(true)
  })

  test('should handle empty message gracefully', async ({ page }) => {
    // Empty message should not trigger anything
    await shopBot.inputBox.fill('')
    await shopBot.page.waitForTimeout(500)

    // Page should still be on the same route
    await expect(page).toHaveURL('/demo/shopbot')
  })
})
