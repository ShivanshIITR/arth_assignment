import { expect, test } from "@playwright/test"

function uniqueEmail() {
  return `user.${Date.now()}@example.com`
}

test("register then sign in", async ({ page }) => {
  const email = uniqueEmail()
  await page.goto("/register")
  await page.getByLabel("Full name").fill("E2E User")
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password").fill("password12")
  await page.getByRole("button", { name: "Create account" }).click()
  await expect(page.getByText("Account created")).toBeVisible()

  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password").fill("password12")
  await page.getByRole("button", { name: "Sign in" }).click()
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
})
