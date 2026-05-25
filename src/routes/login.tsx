import { createFileRoute, Link } from "@tanstack/react-router";
import { Heart } from "lucide-react";
import { useState } from "react";

export const Route = createFileRoute("/login")({
  component: LoginPage,
});

function LoginPage() {
  const [show, setShow] = useState(false);
  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: "linear-gradient(135deg, #eef2ff, #f4f5fa)" }}
    >
      <div className="w-full max-w-md bg-card rounded-2xl shadow-[var(--shadow-modal)] p-8">
        <div className="flex items-center gap-2 justify-center mb-8">
          <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center text-primary-foreground">
            <Heart className="w-4 h-4 fill-current" />
          </div>
          <span className="font-bold text-lg">DMFlow</span>
        </div>
        <h1 className="text-2xl font-bold text-center mb-1">Welcome back</h1>
        <p className="text-sm text-muted-foreground text-center mb-6">Log in to your account</p>

        <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
          <Field label="Email">
            <input type="email" className="input" placeholder="you@example.com" />
          </Field>
          <Field
            label="Password"
            trailing={
              <button type="button" onClick={() => setShow((v) => !v)} className="text-xs text-primary">
                {show ? "Hide" : "Show"}
              </button>
            }
          >
            <input type={show ? "text" : "password"} className="input" placeholder="••••••••" />
          </Field>
          <div className="text-right">
            <Link to="/login" className="text-xs text-primary font-medium">
              Forgot password?
            </Link>
          </div>
          <button className="w-full h-12 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary-dark transition">
            Login
          </button>
        </form>

        <div className="flex items-center gap-3 my-6">
          <div className="flex-1 h-px bg-border" />
          <span className="text-xs text-muted-foreground">or</span>
          <div className="flex-1 h-px bg-border" />
        </div>

        <button className="w-full h-12 rounded-lg border border-border bg-card font-medium text-sm flex items-center justify-center gap-2 hover:bg-muted transition">
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
      <style>{`.input { width: 100%; height: 44px; padding: 0 14px; border: 1px solid var(--border); border-radius: 10px; font-size: 14px; outline: none; background: var(--surface); }
.input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(61,58,238,0.12); }`}</style>
    </div>
  );
}

function Field({ label, children, trailing }: { label: string; children: React.ReactNode; trailing?: React.ReactNode }) {
  return (
    <label className="block">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-medium text-foreground">{label}</span>
        {trailing}
      </div>
      {children}
    </label>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48">
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.1 29.2 35 24 35c-6.1 0-11-4.9-11-11s4.9-11 11-11c2.8 0 5.4 1.1 7.4 2.8l5.7-5.7C33.5 6.6 28.9 5 24 5 13.5 5 5 13.5 5 24s8.5 19 19 19 19-8.5 19-19c0-1.2-.1-2.4-.4-3.5z" />
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.6 16.1 19 13 24 13c2.8 0 5.4 1.1 7.4 2.8l5.7-5.7C33.5 6.6 28.9 5 24 5 16.5 5 10 9.3 6.3 14.7z" />
      <path fill="#4CAF50" d="M24 43c4.8 0 9.2-1.6 12.6-4.4l-5.8-4.9C28.9 35 26.6 36 24 36c-5.2 0-9.6-3.4-11.2-8l-6.5 5C9.8 38.7 16.4 43 24 43z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4-4 5.3l5.8 4.9C40.9 35.6 43 30.2 43 24c0-1.2-.1-2.4-.4-3.5z" />
    </svg>
  );
}
