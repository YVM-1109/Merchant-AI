import { Page, Locator, expect } from '@playwright/test'

export class AuditPage {
  readonly page: Page

  constructor(page: Page) {
    this.page = page
  }

  async goto(merchantId: string = 'merch_1d07bd956960') {
    await this.page.goto(`/dashboard/audit`)
    await this.page.waitForLoadState('networkidle')
  }

  get totalActionsCard(): Locator {
    return this.page.locator('text=Total Actions')
  }

  get approvedCard(): Locator {
    return this.page.locator('text=Approved')
  }

  get deniedCard(): Locator {
    return this.page.locator('text=Denied')
  }

  get guardianRateCard(): Locator {
    return this.page.locator('text=Guardian Rate')
  }

  get auditTable(): Locator {
    return this.page.locator('table')
  }

  get auditRows(): Locator {
    return this.auditTable.locator('tbody tr')
  }

  async getAuditCount(): Promise<number> {
    return this.auditRows.count()
  }
}
