import { test, expect } from '@playwright/test'
import { MerchantsPage } from '../pages/MerchantsPage'

test.describe('Merchants', () => {
  let merchants: MerchantsPage

  test.beforeEach(async ({ page }) => {
    merchants = new MerchantsPage(page)
    await merchants.goto()
  })

  test('should display merchant cards with entries', async ({ page }) => {
    await expect(page).toHaveURL('/dashboard/merchants')

    const count = await merchants.getMerchantCount()
    expect(count).toBeGreaterThan(0)
  })

  test('should show Razorpay dashboard link', async ({ page }) => {
    await expect(merchants.razorpayLinkButton).toBeVisible()
  })

  test('should have add merchant button', async ({ page }) => {
    await expect(merchants.addMerchantButton).toBeVisible()
  })
})
