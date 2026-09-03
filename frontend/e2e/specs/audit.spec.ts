import { test, expect } from '@playwright/test'
import { AuditPage } from '../pages/AuditPage'

test.describe('Audit Trail', () => {
  let audit: AuditPage

  test.beforeEach(async ({ page }) => {
    audit = new AuditPage(page)
  })

  test('should display summary cards', async ({ page }) => {
    await audit.goto()

    await expect(audit.totalActionsCard).toBeVisible()
    await expect(audit.approvedCard).toBeVisible()
    await expect(audit.deniedCard).toBeVisible()
    await expect(audit.guardianRateCard).toBeVisible()
  })

  test('should show audit trail page', async ({ page }) => {
    await audit.goto()
    await expect(page).toHaveURL('/dashboard/audit')
  })
})
