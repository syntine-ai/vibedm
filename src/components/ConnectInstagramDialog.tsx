import { Instagram, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useStartInstagramOauth } from "@/lib/api/hooks";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

type ConnectInstagramDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConnected?: () => void;
  intent?: "onboarding" | "add_workspace";
  isConnecting?: boolean;
  errorMessage?: string;
};

export function ConnectInstagramDialog({
  open,
  onOpenChange,
  onConnected,
  intent = "onboarding",
  isConnecting = false,
  errorMessage,
}: ConnectInstagramDialogProps) {
  // Set up OAuth start mutations for both legacy and professional config flows
  const facebookMutation = useStartInstagramOauth(intent, "facebook");
  const legacyMutation = useStartInstagramOauth(intent, "legacy");

  const submitFacebook = () => {
    onConnected?.();
    facebookMutation.mutate();
  };

  const submitLegacy = () => {
    onConnected?.();
    legacyMutation.mutate();
  };

  const connecting = isConnecting || facebookMutation.isPending || legacyMutation.isPending;
  
  const error =
    errorMessage ||
    (facebookMutation.error instanceof Error ? facebookMutation.error.message : undefined) ||
    (legacyMutation.error instanceof Error ? legacyMutation.error.message : undefined);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md rounded-2xl border-border/60 p-0 overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-4 text-left">
          <div className="w-11 h-11 rounded-xl bg-accent text-primary flex items-center justify-center mb-3">
            <Instagram className="w-6 h-6" />
          </div>
          <DialogTitle>Connect Instagram</DialogTitle>
          <DialogDescription>
            Choose how you would like to link your Instagram professional account.
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 pb-4 space-y-3.5">
          {error && <p className="text-xs text-destructive mt-2">{error}</p>}

          <div className="grid gap-3">
            {/* Facebook Business (Recommended Option Card) */}
            <button
              type="button"
              onClick={submitFacebook}
              disabled={connecting}
              className="flex items-start gap-4 p-4 rounded-xl border border-border bg-card text-left hover:bg-accent hover:border-primary transition group disabled:opacity-60"
            >
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center shrink-0 transition group-hover:scale-105">
                {connecting && facebookMutation.isPending ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                  </svg>
                )}
              </div>
              <div>
                <h5 className="font-semibold text-sm text-foreground group-hover:text-primary transition">
                  Facebook Business (Recommended)
                </h5>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Link via your Facebook Page to unlock robust, error-free DM automations and comment triggers.
                </p>
              </div>
            </button>

            {/* Instagram Direct (Legacy Option Card) */}
            <button
              type="button"
              onClick={submitLegacy}
              disabled={connecting}
              className="flex items-start gap-4 p-4 rounded-xl border border-border bg-card text-left hover:bg-accent hover:border-pink-500 transition group disabled:opacity-60"
            >
              <div className="w-10 h-10 rounded-lg bg-pink-500/10 text-pink-500 flex items-center justify-center shrink-0 transition group-hover:scale-105">
                {connecting && legacyMutation.isPending ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Instagram className="w-5 h-5" />
                )}
              </div>
              <div>
                <h5 className="font-semibold text-sm text-foreground group-hover:text-pink-500 transition">
                  Instagram Direct (Basic)
                </h5>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Simple direct login using your Instagram password. Optimized for solo creators.
                </p>
              </div>
            </button>
          </div>
        </div>

        <DialogFooter className="px-6 py-5 border-t border-border bg-surface sm:justify-end">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={connecting}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
