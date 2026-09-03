import { Page, Locator, expect } from '@playwright/test'

export class MerchantsPage {
  readonly page: Page

  constructor(page: Page) {
    this.page = page
  }

  async goto() {
    await this.page.goto('/dashboard/merchants')
    await this.page.waitForLoadState('networkidle')
  }

  get merchantCards(): Locator {
    return this.page.locator('div.border.rounded-lg.p-4.bg-card')
  }

  get addMerchantButton(): Locator {
    return this.page.locator('text=Add Merchant')
  }

  get razorpayLinkButton(): Locator {
    return this.page.locator('a[title="Open Razorpay Dashboard"]').first()
  }

  async getMerchantCount(): Promise<number> {
    return this.merchantCards.count()
  }

  async openRazorpayForMerchant(merchantId: string) {
    await this.page.locator(`text=${merchantId}`).locator('..').locator('a[href*="dashboard.razorpay.com"]').click()
  }
}
