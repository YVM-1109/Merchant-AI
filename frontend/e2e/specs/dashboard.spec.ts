import { test, expect } from '@playwright/test'
import { DashboardPage } from '../pages/DashboardPage'

test.describe('Dashboard', () => {
  let dashboard: DashboardPage

  test.beforeEach(async ({ page }) => {
    dashboard = new DashboardPage(page)
  })

  test('should display dashboard with key metrics', async ({ page }) => {
    await dashboard.goto()

    await expect(page).toHaveTitle(/Merchant-AI/)
    await expect(dashboard.totalRevenue).toBeVisible()
    await expect(dashboard.avgOrderValue).toBeVisible()
    await expect(dashboard.guardianRate).toBeVisible()
  })

  test('should navigate to ShopBot from dashboard', async ({ page }) => {
    await dashboard.goto()
    await dashboard.openShopBot()

    await expect(page).toHaveURL(/\/demo\/shopbot/)
  })

  test('should navigate to catalog from dashboard', async ({ page }) => {
    await dashboard.goto()
    await dashboard.openCatalog()

    await expect(page).toHaveURL(/\/dashboard\/catalog/)
  })

  test('should show merchant filter dropdown', async ({ page }) => {
    await dashboard.goto()

    await expect(dashboard.merchantFilter).toBeVisible()
  })
})
