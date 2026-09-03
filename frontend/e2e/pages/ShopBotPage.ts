import { Page, Locator, expect } from '@playwright/test'

export class ShopBotPage {
  readonly page: Page

  constructor(page: Page) {
    this.page = page
  }

  async goto() {
    await this.page.goto('/demo/shopbot')
    await this.page.waitForLoadState('networkidle')
  }

  get inputBox(): Locator {
    return this.page.locator('input[placeholder="Type your request..."]')
  }

  get sendButton(): Locator {
    // Button with Send icon - blue background
    return this.page.locator('button.bg-primary')
  }

  async sendMessage(text: string) {
    await this.inputBox.fill(text)
    await this.sendButton.click()
  }

  async waitForBotResponse() {
    // Wait for the loading state to clear
    await this.page.waitForLoadState('networkidle')
    await this.page.waitForTimeout(2000)
  }

  async getBotMessages(): Promise<string[]> {
    return this.page.locator('div.bg-card.border.mr-auto').allInnerTexts()
  }
}
