import { describe, expect, it, vi } from "vitest";

import { ApiError, createApiClient } from "./client";

function jsonResponse(body: unknown, init?: ResponseInit) {
  return new Response(JSON.stringify(body), {
    status: init?.status ?? 200,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
  });
}

describe("createApiClient", () => {
  it("attaches bearer token and workspace header for workspace scoped JSON requests", async () => {
    const fetchImpl = vi.fn(async () => jsonResponse({ ok: true }));
    const client = createApiClient({
      baseUrl: "http://api.test",
      getAccessToken: async () => "token-123",
      getActiveWorkspaceId: () => "workspace-123",
      fetchImpl,
    });

    await client.request("/api/v1/automations", {
      method: "POST",
      workspaceScoped: true,
      body: { name: "Welcome" },
    });

    const [url, init] = fetchImpl.mock.calls[0];
    const headers = init?.headers as Headers;

    expect(url).toBe("http://api.test/api/v1/automations");
    expect(init).toMatchObject({
      method: "POST",
      body: JSON.stringify({ name: "Welcome" }),
    });
    expect(headers.get("Authorization")).toBe("Bearer token-123");
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.get("X-Workspace-Id")).toBe("workspace-123");
  });

  it("parses backend error envelopes into ApiError", async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse(
        {
          error: {
            code: "automation_incomplete",
            message: "Automation is incomplete",
            details: { missing: ["steps"] },
          },
        },
        { status: 422 },
      ),
    );
    const client = createApiClient({
      baseUrl: "http://api.test",
      getAccessToken: async () => "token-123",
      getActiveWorkspaceId: () => "workspace-123",
      fetchImpl,
    });

    await expect(
      client.request("/api/v1/automations/automation-123/activate", {
        method: "POST",
        workspaceScoped: true,
      }),
    ).rejects.toMatchObject<ApiError>({
      status: 422,
      code: "automation_incomplete",
      message: "Automation is incomplete",
      details: { missing: ["steps"] },
    });
  });
});
