import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Loader2, Instagram, Check } from "lucide-react";

import { queryKeys, useActiveWorkspace } from "@/lib/api/hooks";
import { authApi, instagramApi } from "@/lib/api/resources";
import { ApiError } from "@/lib/api/client";

export const Route = createFileRoute("/auth/instagram/callback")({
  component: InstagramCallbackPage,
});

type DetectedAccount = {
  ig_user_id: string;
  ig_username: string;
};

function InstagramCallbackPage() {
  const navigate = useNavigate({ from: "/auth/instagram/callback" });
  const queryClient = useQueryClient();
  const { activeWorkspace } = useActiveWorkspace();
  const [error, setError] = useState<string | null>(null);
  
  // Selection states for Option A (Workspace Selector)
  const [selectionMode, setSelectionMode] = useState(false);
  const [detectedAccounts, setDetectedAccounts] = useState<DetectedAccount[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState("");
  const [isCompleting, setIsCompleting] = useState(false);

  const [authCode, setAuthCode] = useState("");
  const [authState, setAuthState] = useState("");
  const [authIntent, setAuthIntent] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");
    const intent = localStorage.getItem("vibedm.instagram_intent") || "onboarding";

    if (!code || !state) {
      setError("Instagram callback is missing code or state.");
      return;
    }

    setAuthCode(code);
    setAuthState(state);
    setAuthIntent(intent);

    triggerOAuthCompletion(code, state, intent);
  }, [navigate, queryClient]);

  const triggerOAuthCompletion = (code: string, state: string, intent: string, selectedIgUserId?: string) => {
    const complete =
      intent === "add_workspace"
        ? (body: { code: string; state: string; ig_user_id?: string }) => {
            if (!activeWorkspace?.id && intent === "add_workspace") {
              setError("Select a workspace before continuing.");
              return Promise.reject(new Error("Select a workspace before continuing."));
            }
            return instagramApi.connectWorkspace(body, activeWorkspace?.id);
          }
        : instagramApi.completeOauth;

    setIsCompleting(true);
    setError(null);

    complete({ code, state, ig_user_id: selectedIgUserId })
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
        setIsCompleting(false);
        // Intercept requires_selection error to switch to selection mode
        if (callbackError instanceof ApiError && callbackError.code === "requires_selection") {
          const accounts = (callbackError.details as any)?.accounts || [];
          setDetectedAccounts(accounts);
          if (accounts.length > 0) {
            setSelectedAccountId(accounts[0].ig_user_id);
          }
          setSelectionMode(true);
        } else {
          setError(
            callbackError instanceof Error ? callbackError.message : "Instagram connection failed",
          );
        }
      });
  };

  const handleLinkSelection = () => {
    if (!selectedAccountId) return;
    triggerOAuthCompletion(authCode, authState, authIntent, selectedAccountId);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="max-w-md w-full rounded-2xl border border-border bg-card p-8 text-center shadow-[var(--shadow-card)]">
        {!selectionMode ? (
          <>
            <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto mb-4 animate-pulse">
              <Instagram className="w-6 h-6 animate-spin" />
            </div>
            <h1 className="text-xl font-semibold">Connecting Instagram</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              {error ?? "Please wait while we establish a secure connection."}
            </p>
            {error && (
              <button
                onClick={() => navigate({ to: "/settings" })}
                className="mt-6 h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition"
              >
                Back to settings
              </button>
            )}
          </>
        ) : (
          <div className="text-left">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center mb-4">
              <svg className="w-6 h-6 fill-current" viewBox="0 0 24 24">
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
              </svg>
            </div>
            <h1 className="text-xl font-bold text-foreground">Select Instagram Profile</h1>
            <p className="mt-1.5 text-xs text-muted-foreground">
              We found multiple Instagram profiles linked to your Facebook account. Please choose which one to connect:
            </p>

            {error && <p className="text-xs text-destructive mt-3">{error}</p>}

            <div className="mt-5 space-y-2.5 max-h-56 overflow-y-auto pr-1">
              {detectedAccounts.map((account) => {
                const isSelected = selectedAccountId === account.ig_user_id;
                return (
                  <button
                    key={account.ig_user_id}
                    onClick={() => setSelectedAccountId(account.ig_user_id)}
                    type="button"
                    className={`w-full flex items-center justify-between p-3.5 rounded-xl border text-left transition select-none ${
                      isSelected
                        ? "border-primary bg-primary/5 shadow-sm"
                        : "border-border bg-card hover:bg-accent"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${
                        isSelected ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                      }`}>
                        {account.ig_username[0]?.toUpperCase()}
                      </div>
                      <div>
                        <span className="block text-sm font-semibold text-foreground">@{account.ig_username}</span>
                        <span className="block text-[10px] text-muted-foreground mt-0.5">ID: {account.ig_user_id}</span>
                      </div>
                    </div>
                    {isSelected && (
                      <div className="w-5 h-5 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                        <Check className="w-3.5 h-3.5" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={() => navigate({ to: "/settings" })}
                disabled={isCompleting}
                className="flex-1 h-11 px-4 rounded-lg border border-border text-foreground hover:bg-accent text-sm font-semibold transition disabled:opacity-60"
              >
                Cancel
              </button>
              <button
                onClick={handleLinkSelection}
                disabled={isCompleting || !selectedAccountId}
                className="flex-1 h-11 px-4 rounded-lg bg-primary text-primary-foreground hover:bg-primary-dark text-sm font-semibold transition flex items-center justify-center gap-1.5 disabled:opacity-60"
              >
                {isCompleting && <Loader2 className="w-4 h-4 animate-spin" />}
                {isCompleting ? "Linking..." : "Link Profile"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
