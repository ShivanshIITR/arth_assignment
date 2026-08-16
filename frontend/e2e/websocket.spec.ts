import { expect, test } from "@playwright/test"

import { createProject, createTask, registerAndSignIn, uniqueEmail } from "./helpers"

test("task board updates live for a second viewer", async ({ page }) => {
  const email = uniqueEmail("live")
  await registerAndSignIn(page, "Live Owner", email)
  await createProject(page, "Live project")
  await createTask(page, "Move me")

  await expect(page.getByText("Live")).toBeVisible()

  const secondPage = await page.context().newPage()
  await secondPage.goto(page.url())
  await expect(secondPage.getByRole("link", { name: "Move me" })).toBeVisible()
  await expect(secondPage.getByText("Live")).toBeVisible()

  await page.getByLabel("Change task status").click()
  await page.getByRole("option", { name: "In progress" }).click()
  await expect(page.getByLabel("Change task status")).toContainText("In progress")
  await expect(secondPage.getByLabel("Change task status")).toContainText(
    "In progress",
  )
})
