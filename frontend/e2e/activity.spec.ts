import { expect, test } from "@playwright/test"

import { createProject, createTask, registerAndSignIn, uniqueEmail } from "./helpers"

test("project activity records creates and task changes", async ({ page }) => {
  const email = uniqueEmail("activity")
  await registerAndSignIn(page, "Activity Owner", email)
  await createProject(page, "Activity project")

  await expect(page.getByRole("heading", { name: "Activity" })).toBeVisible()
  await expect(page.getByText("Activity Owner created the project")).toBeVisible()
  await expect(page.getByRole("heading", { name: "Audit log" })).toBeVisible()
  await expect(page.getByText("Activity Owner created the project").nth(1)).toBeVisible()

  await createTask(page, "Draft timeline")
  await expect(page.getByText("Activity Owner created a task")).toBeVisible()
})
