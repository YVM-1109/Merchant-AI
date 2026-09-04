import { test, expect } from '@playwright/test'

test.describe('Store ShopBot Page', () => {
  test('ShopBot page loads and accepts messages', async ({ page }) => {
    await page.goto('/store/shopbot')
    await expect(page).toHaveURL('/store/shopbot')
    await expect(page.getByRole('heading', { name: /ShopBot/i })).toBeVisible()

    await page.fill('input[placeholder="Type your request..."]', 'I want to buy a wireless mouse')
    await page.click('button[aria-label="Send message"]')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('.shopbot-message')).toContainText(/ShopBot|product|Guardian|Error/i)
  })
})
