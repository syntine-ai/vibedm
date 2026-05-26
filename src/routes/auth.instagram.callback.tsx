import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";

import { queryKeys } from "@/lib/api/hooks";
import { authApi, instagramApi } from "@/lib/api/resources";

export const Route = createFileRoute("/auth/instagram/callback")({
  component: InstagramCallbackPage,
});

function InstagramCallbackPage() {
  const navigate = useNavigate({ from: "/auth/instagram/callback" });
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");
    const intent = localStorage.getItem("vibedm.instagram_intent");

    if (!code || !state) {
      setError("Instagram callback is missing code or state.");
      return;
    }

    const complete =
      intent === "add_workspace" ? instagramApi.connectWorkspace : instagramApi.completeOauth;

    complete({ code, state })
      .then(async (response) => {
        localStorage.removeItem("vibedm.instagram_intent");
        const me = await authApi.me();
        queryClient.setQueryData(queryKeys.authMe, me);
        await queryClient.invalidateQueries({ queryKey: queryKeys.workspaces });
        
        const targetUrl = response.redirect_to || "/dashboard";

        if (window.opener && !window.opener.closed) {
          try {
            // Redirect the main/parent tab to the dashboard
            window.opener.location.href = targetUrl;
          } catch (e) {
            console.error("Failed to redirect parent window:", e);
          }
          // Close the popup window automatically
          window.close();
        } else {
          // Fallback if not opened in a popup
          navigate({ to: targetUrl, replace: true });
        }
      })
      .catch((callbackError) => {
        setError(
          callbackError instanceof Error ? callbackError.message : "Instagram connection failed",
        );
      });
  }, [navigate, queryClient]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="max-w-md rounded-2xl border border-border bg-card p-8 text-center shadow-[var(--shadow-card)]">
        <h1 className="text-xl font-semibold">Connecting Instagram</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {error ?? "Please wait while we create your workspace."}
        </p>
        {error && (
          <button
            onClick={() => navigate({ to: "/settings" })}
            className="mt-6 h-10 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold"
          >
            Back to settings
          </button>
        )}
      </div>
    </div>
  );
}
