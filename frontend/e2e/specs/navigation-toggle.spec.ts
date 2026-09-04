import { test, expect } from '@playwright/test'

test.describe('Navigation Toggle', () => {
  test('Navigation toggle appears on both portals', async ({ page }) => {
    await page.goto('/store')
    await expect(page.locator('.nav-toggle')).toBeVisible()
    await page.goto('/merchant')
    await expect(page.locator('.nav-toggle')).toBeVisible()
  })

  test('Navigation toggle links work', async ({ page }) => {
    await page.goto('/store')
    await page.locator('.nav-toggle a:has-text("Merchant View")').click()
    await expect(page).toHaveURL('/merchant')
    await page.locator('.nav-toggle a:has-text("Customer View")').click()
    await expect(page).toHaveURL('/store')
  })
})
