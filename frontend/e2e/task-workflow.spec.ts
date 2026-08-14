import { expect, test } from "@playwright/test"

test("create a task, assign it, and complete it", async ({ page }) => {
  const email = `tasks.${Date.now()}@example.com`
  await page.goto("/register")
  await page.getByLabel("Full name").fill("Task Owner")
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password").fill("password12")
  await page.getByRole("button", { name: "Create account" }).click()
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password").fill("password12")
  await page.getByRole("button", { name: "Sign in" }).click()

  await page.getByRole("link", { name: "Projects" }).click()
  await page.getByRole("button", { name: "New project" }).click()
  await page.getByLabel("Name").fill("Task project")
  await page.getByRole("button", { name: "Create" }).click()
  await page.getByRole("link", { name: "Task project" }).click()

  await page.getByRole("button", { name: "New task" }).click()
  await page.getByLabel("Title").fill("Write brief")
  await page.getByLabel("Due date").fill("2026-12-01")
  await page.getByRole("button", { name: "Create task" }).click()
  await expect(page.getByRole("link", { name: "Write brief" })).toBeVisible()

  await page.getByRole("link", { name: "Write brief" }).click()
  await page.getByLabel("Assignee").click()
  await page.getByRole("option", { name: "Task Owner" }).click()
  await page.getByRole("button", { name: "Save changes" }).click()

  await page.getByLabel("Change task status").click()
  await page.getByRole("option", { name: "Completed" }).click()
  await expect(page.getByLabel("Change task status")).toContainText("Completed")

  await page.getByRole("link", { name: "Dashboard" }).click()
  await expect(page.getByText("Completed tasks")).toBeVisible()
})
