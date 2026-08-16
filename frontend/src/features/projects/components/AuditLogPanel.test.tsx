import { screen } from "@testing-library/react"
import { http, HttpResponse } from "msw"
import { describe, expect, it } from "vitest"

import { formatAuditSentence } from "@/features/audit/format"
import { AuditLogPanel } from "@/features/projects/components/AuditLogPanel"
import { projectFixture, userFixture } from "@/test/fixtures"
import { renderWithProviders } from "@/test/render"
import { server } from "@/test/setup"
import type { AuditLog } from "@/types/audit"

const entry: AuditLog = {
  id: "1",
  actor_id: userFixture.id,
  actor: userFixture,
  event_type: "PROJECT_CREATED",
  project_id: projectFixture.id,
  resource_type: "project",
  resource_id: projectFixture.id,
  metadata: null,
  ip_address: "127.0.0.1",
  created_at: "2026-01-02T00:00:00Z",
}

describe("formatAuditSentence", () => {
  it("describes project and auth events", () => {
    expect(formatAuditSentence(entry)).toBe("Owner User created the project")
    expect(formatAuditSentence({ ...entry, event_type: "LOGIN" })).toBe(
      "Owner User signed in",
    )
  })
})

describe("AuditLogPanel", () => {
  it("renders audit events for the project owner", async () => {
    renderWithProviders(<AuditLogPanel projectId={projectFixture.id} />)
    expect(await screen.findByText("Owner User created the project")).toBeInTheDocument()
  })

  it("is not responsible for hiding itself — the page gates visibility", async () => {
    server.use(
      http.get("*/api/v1/projects/:projectId/audit-logs", () =>
        HttpResponse.json({ error: { code: "FORBIDDEN", message: "No" } }, { status: 403 }),
      ),
    )
    renderWithProviders(<AuditLogPanel projectId={projectFixture.id} />)
    expect(await screen.findByText("Could not load audit log")).toBeInTheDocument()
  })
})
