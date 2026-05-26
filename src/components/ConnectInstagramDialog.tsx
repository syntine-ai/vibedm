import { Instagram, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
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
  onConnected: () => void;
  isConnecting?: boolean;
  errorMessage?: string;
};

export function ConnectInstagramDialog({
  open,
  onOpenChange,
  onConnected,
  isConnecting = false,
  errorMessage,
}: ConnectInstagramDialogProps) {
  const submit = () => {
    onConnected();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md rounded-2xl border-border/60 p-0 overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-4 text-left">
          <div className="w-11 h-11 rounded-xl bg-accent text-primary flex items-center justify-center mb-3">
            <Instagram className="w-6 h-6" />
          </div>
          <DialogTitle>Connect Instagram</DialogTitle>
          <DialogDescription>
            Log in with Instagram first, then create the workspace for that account.
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 pb-2">
          {errorMessage && <p className="text-xs text-destructive mt-2">{errorMessage}</p>}

          <p className="text-xs text-muted-foreground mt-3">
            This currently simulates a successful Instagram login callback and is ready for OAuth wiring.
          </p>
        </div>

        <DialogFooter className="px-6 py-5 border-t border-border bg-surface sm:justify-end">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isConnecting}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={isConnecting}>
            {isConnecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Instagram className="w-4 h-4" />}
            {isConnecting ? "Logging in..." : "Log in with Instagram"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
