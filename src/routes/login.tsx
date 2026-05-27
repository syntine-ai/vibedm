import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Heart } from "lucide-react";
import { useState } from "react";

import { ConnectInstagramDialog } from "@/components/ConnectInstagramDialog";
import { FormField } from "@/components/FormField";
import { GoogleIcon } from "@/components/Icons";
import { queryKeys } from "@/lib/api/hooks";
import { authApi, getActiveWorkspace } from "@/lib/api/resources";
import { supabase } from "@/integrations/supabase/client";

export const Route = createFileRoute("/login")({
  component: LoginPage,
});

function LoginPage() {
  const [show, setShow] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const queryClient = useQueryClient();
  const navigate = useNavigate({ from: "/login" });

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (signInError) throw signInError;
      await authApi.sync(signInData.session?.access_token ?? null);
      const me = await authApi.me();
      queryClient.setQueryData(queryKeys.authMe, me);
      if (getActiveWorkspace(me.workspaces) || me.workspaces.length > 0) {
        navigate({ to: "/dashboard" });
      } else {
        setConnectDialogOpen(true);
      }
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError(null);
    const { error: oauthError } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/dashboard` },
    });
    if (oauthError) setError(oauthError.message);
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: "linear-gradient(135deg, #eef2ff, #f4f5fa)" }}
    >
      <div className="w-full max-w-md bg-card rounded-2xl shadow-[var(--shadow-modal)] p-8">
        <div className="flex items-center gap-2 justify-center mb-8">
          <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center text-primary-foreground">
            <Heart className="size-4 fill-current" />
          </div>
          <span className="font-bold text-lg">Vibe DM</span>
        </div>
        <h1 className="text-2xl font-bold text-center mb-1">Welcome back</h1>
        <p className="text-sm text-muted-foreground text-center mb-6">Log in to your account</p>

        <form className="space-y-4" onSubmit={handleLogin}>
          <FormField label="Email">
            <input
              type="email"
              className="input"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </FormField>
          <FormField
            label="Password"
            trailing={
              <button
                type="button"
                onClick={() => setShow((value) => !value)}
                className="text-xs text-primary"
              >
                {show ? "Hide" : "Show"}
              </button>
            }
          >
            <input
              type={show ? "text" : "password"}
              className="input"
              placeholder="••••••••"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </FormField>
          {error && <p className="text-xs text-destructive">{error}</p>}
          <div className="text-right">
            <Link to="/login" className="text-xs text-primary font-medium">
              Forgot password?
            </Link>
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="w-full h-12 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary-dark transition disabled:opacity-60"
          >
            {submitting ? "Logging in..." : "Login"}
          </button>
        </form>

        <div className="flex items-center gap-3 my-6">
          <div className="flex-1 h-px bg-border" />
          <span className="text-xs text-muted-foreground">or</span>
          <div className="flex-1 h-px bg-border" />
        </div>

        <button
          type="button"
          onClick={handleGoogleLogin}
          className="w-full h-12 rounded-lg border border-border bg-card font-medium text-sm flex items-center justify-center gap-2 hover:bg-muted transition"
        >
          <GoogleIcon />
          Continue with Google
        </button>

        <p className="text-center text-sm text-muted-foreground mt-6">
          Don't have an account?{" "}
          <Link to="/signup" className="text-primary font-semibold">
            Sign Up
          </Link>
        </p>
      </div>

      <ConnectInstagramDialog
        open={connectDialogOpen}
        onOpenChange={setConnectDialogOpen}
        intent="onboarding"
      />

      <style>{`.input { width: 100%; height: 44px; padding: 0 14px; border: 1px solid var(--border); border-radius: 10px; font-size: 14px; outline: none; background: var(--surface); }
.input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(61,58,238,0.12); }`}</style>
    </div>
  );
}
