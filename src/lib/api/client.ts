import createOpenApiClient from "openapi-fetch";

import { supabase } from "@/integrations/supabase/client";

import type { paths } from "./openapi";

type RequestMethod = "GET" | "POST" | "PATCH" | "DELETE";

type ApiClientOptions = {
  baseUrl?: string;
  getAccessToken?: () => Promise<string | null>;
  getActiveWorkspaceId?: () => string | null;
  fetchImpl?: typeof fetch;
};

type RequestOptions = {
  method?: RequestMethod;
  query?: Record<string, string | number | boolean | null | undefined>;
  body?: unknown;
  workspaceScoped?: boolean;
  workspaceId?: string | null;
  headers?: HeadersInit;
};

type BackendErrorEnvelope = {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
};

export class ApiError extends Error {
  status: number;
  code: string;
  details: unknown;

  constructor({
    status,
    code,
    message,
    details,
  }: {
    status: number;
    code: string;
    message: string;
    details?: unknown;
  }) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details ?? {};
  }
}

export class MissingWorkspaceError extends ApiError {
  constructor() {
    super({
      status: 400,
      code: "workspace_required",
      message: "Select a workspace before continuing.",
      details: {},
    });
    this.name = "MissingWorkspaceError";
  }
}

export function getApiBaseUrl() {
  const env = import.meta.env.VITE_API_BASE_URL as string | undefined;
  return (env || "http://localhost:8000").replace(/\/$/, "");
}

export async function getSupabaseAccessToken() {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

export function createApiClient({
  baseUrl = getApiBaseUrl(),
  getAccessToken = getSupabaseAccessToken,
  getActiveWorkspaceId = () => null,
  fetchImpl = fetch,
}: ApiClientOptions = {}) {
  async function request<T = unknown>(path: string, options: RequestOptions = {}): Promise<T> {
    const method = options.method ?? "GET";
    const token = await getAccessToken();
    const workspaceId = options.workspaceId ?? getActiveWorkspaceId();
    const headers = new Headers(options.headers);

    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    if (options.workspaceScoped) {
      if (!workspaceId) {
        throw new MissingWorkspaceError();
      }
      headers.set("X-Workspace-Id", workspaceId);
    }

    const url = buildUrl(baseUrl, path, options.query);
    const body = serializeBody(options.body, headers);
    const response = await fetchImpl(url, { method, headers, body });
    return parseResponse<T>(response);
  }

  return { request };
}

export const openApiClient = createOpenApiClient<paths>({ baseUrl: getApiBaseUrl() });

function buildUrl(baseUrl: string, path: string, query?: RequestOptions["query"]) {
  const url = new URL(`${baseUrl}${path}`);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== null && value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

function serializeBody(body: unknown, headers: Headers): BodyInit | undefined {
  if (body === undefined || body === null) {
    return undefined;
  }
  if (body instanceof FormData) {
    return body;
  }
  headers.set("Content-Type", "application/json");
  return JSON.stringify(body);
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    throw toApiError(response.status, payload);
  }

  return payload as T;
}

function toApiError(status: number, payload: unknown) {
  const envelope = payload as BackendErrorEnvelope;
  const error = envelope?.error;
  return new ApiError({
    status,
    code: error?.code ?? "http_error",
    message: error?.message ?? "Request failed",
    details: error?.details ?? {},
  });
}
