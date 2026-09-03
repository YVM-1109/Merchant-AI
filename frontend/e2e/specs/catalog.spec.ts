import { test, expect } from '@playwright/test'
import { CatalogPage } from '../pages/CatalogPage'

test.describe('Catalog', () => {
  let catalog: CatalogPage

  test.beforeEach(async ({ page }) => {
    catalog = new CatalogPage(page)
    await catalog.goto()
  })

  test('should load catalog page with products', async ({ page }) => {
    await expect(page).toHaveURL('/dashboard/catalog')

    const count = await catalog.getProductCount()
    expect(count).toBeGreaterThan(0)
  })

  test('should search products', async ({ page }) => {
    await catalog.search('USB')

    await page.waitForLoadState('networkidle')
    const count = await catalog.getProductCount()
    expect(count).toBeGreaterThan(0)
  })

  test('should filter by merchant', async ({ page }) => {
    await catalog.filterByMerchant('merch_1d07bd956960')

    await page.waitForLoadState('networkidle')
    const count = await catalog.getProductCount()
    expect(count).toBeGreaterThan(0)
  })

  test('should display search input', async ({ page }) => {
    await expect(catalog.searchInput).toBeVisible()
    await expect(catalog.searchInput).toHaveValue('')
  })
})
