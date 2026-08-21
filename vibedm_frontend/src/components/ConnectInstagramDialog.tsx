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
  // Set up OAuth start mutation for legacy direct flow
  const legacyMutation = useStartInstagramOauth(intent, "legacy");

  const submitLegacy = () => {
    onConnected?.();
    legacyMutation.mutate();
  };

  const connecting = isConnecting || legacyMutation.isPending;
  
  const error =
    errorMessage ||
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
            Link your Instagram professional account using standard Instagram login.
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 pb-6 space-y-4">
          {error && <p className="text-xs text-destructive">{error}</p>}

          <div className="p-4 rounded-xl border border-border bg-card">
            <p className="text-sm text-foreground font-medium mb-1">Instagram Direct Connection</p>
            <p className="text-xs text-muted-foreground">
              This will open a secure window to log in directly with your Instagram credentials. Please ensure your account is set up as a Creator or Business account.
            </p>
          </div>

          <Button
            type="button"
            onClick={submitLegacy}
            disabled={connecting}
            className="w-full h-11 bg-primary text-primary-foreground font-semibold rounded-lg hover:bg-primary/90 transition flex items-center justify-center gap-2"
          >
            {connecting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <Instagram className="w-4 h-4" />
                Continue with Instagram
              </>
            )}
          </Button>
        </div>

        <DialogFooter className="px-6 py-4 border-t border-border bg-surface sm:justify-end">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={connecting}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
