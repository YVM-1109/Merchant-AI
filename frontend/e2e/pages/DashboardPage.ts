import { Page, Locator, expect } from '@playwright/test'

export class DashboardPage {
  readonly page: Page

  constructor(page: Page) {
    this.page = page
  }

  async goto() {
    await this.page.goto('/dashboard')
    await this.page.waitForLoadState('networkidle')
  }

  get totalRevenue(): Locator {
    return this.page.locator('text=Total Revenue')
  }

  get avgOrderValue(): Locator {
    return this.page.locator('text=Avg Order Value')
  }

  get guardianRate(): Locator {
    return this.page.locator('text=Guardian Interception')
  }

  get shopBotButton(): Locator {
    return this.page.locator('text=ShopBot Demo')
  }

  get catalogButton(): Locator {
    return this.page.locator('a[href="/dashboard/catalog"]')
  }

  get merchantFilter(): Locator {
    return this.page.locator('select')
  }

  async openShopBot() {
    await this.shopBotButton.click()
    await this.page.waitForURL(/\/demo\/shopbot/)
  }

  async openCatalog() {
    await this.catalogButton.click()
    await this.page.waitForURL(/\/dashboard\/catalog/)
  }
}
