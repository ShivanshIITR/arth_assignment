import { expect, test, type Page } from "@playwright/test"

import { registerAndSignIn, uniqueEmail } from "./helpers"

async function signUp(page: Page, email: string) {
  await registerAndSignIn(page, "Owner User", email)
}

test("create a project and add a member by email", async ({ page, browser }) => {
  const ownerEmail = uniqueEmail("owner")
  const memberEmail = uniqueEmail("member")

  const memberPage = await browser.newPage()
  await signUp(memberPage, memberEmail)
  await memberPage.close()

  await signUp(page, ownerEmail)
  await page.getByRole("link", { name: "Projects", exact: true }).click()
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
