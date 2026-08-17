import { expect, test } from "@playwright/test"

import { createProject, createTask, registerAndSignIn, uniqueEmail } from "./helpers"

test("create a task, assign it, and complete it", async ({ page }) => {
  const email = uniqueEmail("tasks")
  await registerAndSignIn(page, "Task Owner", email)
  await createProject(page, "Task project")
  await createTask(page, "Write brief")

  await page.getByRole("link", { name: "Write brief" }).click()
  await page.getByRole("combobox").filter({ hasText: "Unassigned" }).click()
  await page.getByRole("option", { name: "Task Owner" }).click()
  await page.getByLabel("Due date").fill("2026-12-01")
  await page.getByRole("button", { name: "Save changes" }).click()

  await page.getByLabel("Change task status").click()
  await page.getByRole("option", { name: "Completed" }).click()
  await expect(page.getByLabel("Change task status")).toContainText("Completed")

  await page.getByRole("link", { name: "Dashboard", exact: true }).click()
  await expect(page.getByText("Completed tasks")).toBeVisible()
})
