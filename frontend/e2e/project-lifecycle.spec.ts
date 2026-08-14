import { expect, test, type Page } from "@playwright/test"

async function signUp(page: Page, email: string) {
  await page.goto("/register")
  await page.getByLabel("Full name").fill("Owner User")
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password").fill("password12")
  await page.getByRole("button", { name: "Create account" }).click()
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password").fill("password12")
  await page.getByRole("button", { name: "Sign in" }).click()
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
}

test("create a project and add a member by email", async ({ page, browser }) => {
  const ownerEmail = `owner.${Date.now()}@example.com`
  const memberEmail = `member.${Date.now()}@example.com`

  const memberPage = await browser.newPage()
  await signUp(memberPage, memberEmail)
  await memberPage.close()

  await signUp(page, ownerEmail)
  await page.getByRole("link", { name: "Projects" }).click()
  await page.getByRole("button", { name: "New project" }).click()
  await page.getByLabel("Name").fill("Launch plan")
  await page.getByLabel("Description").fill("First project")
  await page.getByRole("button", { name: "Create" }).click()
  await expect(page.getByText("Launch plan")).toBeVisible()

  await page.getByRole("link", { name: "Launch plan" }).click()
  await page.getByRole("button", { name: "Add member" }).click()
  await page.getByLabel("Email").fill(memberEmail)
  await page.getByRole("button", { name: "Add member" }).click()
  await expect(page.getByText(memberEmail)).toBeVisible()
})
