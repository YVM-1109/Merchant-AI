import { test, expect } from '@playwright/test'

test.describe('ShopBot Widget', () => {
  test('ShopBot widget renders and toggles correctly', async ({ page }) => {
    await page.goto('/store')
    await expect(page.getByRole('button', { name: /ShopBot/i })).toBeVisible()
    await page.getByRole('button', { name: /ShopBot/i }).click()
    await expect(page.locator('[role="dialog"]')).toBeVisible()
    await page.locator('.shopbot-close-btn').click()
    await expect(page.locator('[role="dialog"]')).not.toBeVisible()
  })
})
