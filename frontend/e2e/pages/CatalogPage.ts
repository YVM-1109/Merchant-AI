import { Page, Locator, expect } from '@playwright/test'

export class CatalogPage {
  readonly page: Page

  constructor(page: Page) {
    this.page = page
  }

  async goto() {
    await this.page.goto('/dashboard/catalog')
    await this.page.waitForLoadState('networkidle')
  }

  get searchInput(): Locator {
    return this.page.locator('input[placeholder="Search products..."]')
  }

  get merchantFilter(): Locator {
    return this.page.locator('select')
  }

  get productCards(): Locator {
    // Product cards contain an h3 with product name
    return this.page.locator('h3.font-semibold')
  }

  get addProductButton(): Locator {
    return this.page.locator('text=Add Product')
  }

  async search(query: string) {
    await this.searchInput.fill(query)
    await this.page.waitForTimeout(500)
    await this.page.waitForLoadState('networkidle')
  }

  async filterByMerchant(merchantId: string) {
    // Wait for merchants to load so options are populated
    await this.merchantFilter.waitFor({ state: 'visible' })
    await this.merchantFilter.selectOption(merchantId)
    await this.page.waitForLoadState('networkidle')
  }

  async getProductCount(): Promise<number> {
    return this.productCards.count()
  }
}
