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
  const oauthMutation = useStartInstagramOauth(intent);
  const submit = () => {
    onConnected?.();
    oauthMutation.mutate();
  };
  const connecting = isConnecting || oauthMutation.isPending;
  const error =
    errorMessage ||
    (oauthMutation.error instanceof Error ? oauthMutation.error.message : undefined);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md rounded-2xl border-border/60 p-0 overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-4 text-left">
          <div className="w-11 h-11 rounded-xl bg-accent text-primary flex items-center justify-center mb-3">
            <Instagram className="w-6 h-6" />
          </div>
          <DialogTitle>Connect Instagram</DialogTitle>
          <DialogDescription>
            Connect your Instagram Business account to get started.
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 pb-2">
          {error && <p className="text-xs text-destructive mt-2">{error}</p>}

          <p className="text-xs text-muted-foreground mt-3">
            A popup will open for Instagram login. After you approve access, Vibedm will
            automatically link your Instagram Business account.
          </p>
        </div>

        <DialogFooter className="px-6 py-5 border-t border-border bg-surface sm:justify-end">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={connecting}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={connecting}>
            {connecting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Instagram className="w-4 h-4" />
            )}
            {connecting ? "Connecting..." : "Continue with Instagram"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
