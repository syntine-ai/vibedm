import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Heart } from "lucide-react";
import { useState } from "react";

import { ConnectInstagramDialog } from "@/components/ConnectInstagramDialog";

export const Route = createFileRoute("/signup")({
  component: SignupPage,
});

function SignupPage() {
  const navigate = useNavigate({ from: "/signup" });
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);
  
  const handleSignup = (e: React.FormEvent) => {
    e.preventDefault();
    setConnectDialogOpen(true);
  };

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
        <h1 className="text-2xl font-bold text-center mb-1">Create your account</h1>
        <p className="text-sm text-muted-foreground text-center mb-6">Start automating in minutes</p>

        <form className="space-y-4" onSubmit={handleSignup}>
          <div className="grid grid-cols-2 gap-3">
            <L label="First name">
              <input className="input" placeholder="Alex" />
            </L>
            <L label="Last name">
              <input className="input" placeholder="Morgan" />
            </L>
          </div>
          <L label="Email"><input type="email" className="input" placeholder="you@example.com" /></L>
          <L label="Phone number"><input type="tel" className="input" placeholder="+1 555 0100" /></L>
          <L label="Password"><input type="password" className="input" placeholder="••••••••" /></L>
          <L label="Confirm password"><input type="password" className="input" placeholder="••••••••" /></L>

          <button className="w-full h-12 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary-dark transition">
            Create Account
          </button>
        </form>

        <p className="text-center text-sm text-muted-foreground mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-primary font-semibold">
            Login
          </Link>
        </p>
      </div>

      <ConnectInstagramDialog
        open={connectDialogOpen}
        onOpenChange={setConnectDialogOpen}
        onConnected={() => {
          setConnectDialogOpen(false);
          navigate({ to: "/dashboard" });
        }}
      />

      <style>{`.input { width: 100%; height: 44px; padding: 0 14px; border: 1px solid var(--border); border-radius: 10px; font-size: 14px; outline: none; background: var(--surface); }
.input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(61,58,238,0.12); }`}</style>
    </div>
  );
}

function L({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-medium mb-1.5 block">{label}</span>
      {children}
    </label>
  );
}
