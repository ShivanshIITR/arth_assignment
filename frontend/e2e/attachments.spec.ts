import { expect, test } from "@playwright/test"

import { createProject, createTask, registerAndSignIn, uniqueEmail } from "./helpers"

test("upload, download, and delete a task attachment", async ({ page }) => {
  const email = uniqueEmail("files")
  await registerAndSignIn(page, "File Owner", email)
  await createProject(page, "Files project")
  await createTask(page, "Attach spec")
  await page.getByRole("link", { name: "Attach spec" }).click()

  await expect(page.getByRole("heading", { name: "Attachments" })).toBeVisible()
  await expect(page.getByText("No attachments yet")).toBeVisible()

  await page.getByLabel("Upload file").setInputFiles({
    name: "notes.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("hello from e2e"),
  })
  await expect(page.getByRole("button", { name: "notes.txt" })).toBeVisible()

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "notes.txt" }).click(),
  ])
  expect(download.suggestedFilename()).toBe("notes.txt")

  await page.getByRole("button", { name: "Delete" }).click()
  await expect(page.getByText("No attachments yet")).toBeVisible()
})
