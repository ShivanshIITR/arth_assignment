import { expect, type Page } from "@playwright/test"

export const PASSWORD = "password12"

export function uniqueEmail(prefix: string) {
  return `${prefix}.${Date.now()}@example.com`
}

export async function registerAndSignIn(
  page: Page,
  fullName: string,
  email: string,
) {
  await page.goto("/register")
  await page.getByLabel("Full name").fill(fullName)
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password").fill(PASSWORD)
  await page.getByRole("button", { name: "Create account" }).click()
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password").fill(PASSWORD)
  await page.getByRole("button", { name: "Sign in" }).click()
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
}

export async function createProject(page: Page, name: string) {
  await page.getByRole("link", { name: "Projects" }).click()
  await page.getByRole("button", { name: "New project" }).click()
  await page.getByLabel("Name").fill(name)
  await page.getByRole("button", { name: "Create" }).click()
  await page.getByRole("link", { name }).click()
}

export async function createTask(page: Page, title: string) {
  await page.getByRole("button", { name: "New task" }).click()
  await page.getByLabel("Title").fill(title)
  await page.getByRole("button", { name: "Create task" }).click()
  await expect(page.getByRole("link", { name: title })).toBeVisible()
}
