import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, Info, Play, Save, Zap } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api/client";
import {
  useActiveWorkspace,
  useAutomationQuery,
  useAutomationStatusMutation,
  useCreateAutomationMutation,
  useTestTriggerMutation,
  useUpdateAutomationMutation,
} from "@/lib/api/hooks";
import type { AutomationStep, TriggerType } from "@/lib/api/types";

export const Route = createFileRoute("/automations/$id/edit")({
  head: () => ({ meta: [{ title: "Edit automation - DMFlow" }] }),
  component: EditorPage,
});

type UiTrigger = "comment-post" | "dm" | "live" | "story-reply" | "story-mention";

const triggerMap: Record<UiTrigger, TriggerType> = {
  "comment-post": "comment_post",
  dm: "dm",
  live: "live_comment",
  "story-reply": "story_reply",
  "story-mention": "story_mention",
};

const uiTriggerMap: Partial<Record<TriggerType, UiTrigger>> = {
  comment_post: "comment-post",
  dm: "dm",
  live_comment: "live",
  story_reply: "story-reply",
  story_mention: "story-mention",
};

const triggers: { id: UiTrigger; label: string; soon?: boolean }[] = [
  { id: "comment-post", label: "User comments on your post or reel" },
  { id: "dm", label: "User DMs to you" },
  { id: "live", label: "User comments on your LIVE" },
  { id: "story-reply", label: "User replies to your stories" },
  { id: "story-mention", label: "User mentions you in story", soon: true },
];

function EditorPage() {
  const { id } = Route.useParams();
  const navigate = useNavigate({ from: "/automations/$id/edit" });
  const { activeWorkspace } = useActiveWorkspace();
  const createMutation = useCreateAutomationMutation(activeWorkspace?.id);
  const createdDraft = useRef(false);
  const automationQuery = useAutomationQuery(activeWorkspace?.id, id);
  const updateMutation = useUpdateAutomationMutation(activeWorkspace?.id, id);
  const statusMutation = useAutomationStatusMutation(activeWorkspace?.id, id);
  const testMutation = useTestTriggerMutation(activeWorkspace?.id, id);
  const [name, setName] = useState("Untitled automation");
  const [trigger, setTrigger] = useState<UiTrigger | null>(null);
  const [keywords, setKeywords] = useState("");
  const [postId, setPostId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id === "new" && activeWorkspace?.id && !createdDraft.current) {
      createdDraft.current = true;
      createMutation.mutateAsync({ name: "Untitled automation" }).then((automation) => {
        navigate({ to: "/automations/$id/edit", params: { id: automation.id }, replace: true });
      });
    }
  }, [activeWorkspace?.id, createMutation, id, navigate]);

  useEffect(() => {
    const automation = automationQuery.data;
    if (!automation) return;
    setName(automation.name);
    setTrigger(automation.trigger_type ? (uiTriggerMap[automation.trigger_type] ?? null) : null);
    const config = automation.trigger_config ?? {};
    setKeywords(Array.isArray(config.keywords) ? config.keywords.join(", ") : "");
    setPostId(typeof config.post_id === "string" ? config.post_id : "");
    const firstStep = automation.steps?.[0];
    setMessage(typeof firstStep?.config?.message === "string" ? firstStep.config.message : "");
  }, [automationQuery.data]);

  const save = async () => {
    if (!activeWorkspace?.id || id === "new") return;
    setError(null);
    try {
      await updateMutation.mutateAsync({
        name,
        trigger_type: trigger ? triggerMap[trigger] : null,
        trigger_config: trigger ? buildTriggerConfig(trigger, keywords, postId) : {},
        steps: buildSteps(message),
      });
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Save failed");
    }
  };

  const toggleActive = async () => {
    setError(null);
    try {
      await save();
      const next = automationQuery.data?.status === "active" ? "inactive" : "active";
      await statusMutation.mutateAsync(next);
    } catch (statusError) {
      if (statusError instanceof ApiError && statusError.code === "automation_incomplete") {
        const missing = Array.isArray((statusError.details as { missing?: unknown[] }).missing)
          ? (statusError.details as { missing: string[] }).missing.join(", ")
          : "required fields";
        setError(`Automation is incomplete: ${missing}`);
      } else {
        setError(statusError instanceof Error ? statusError.message : "Status update failed");
      }
    }
  };

  if (id === "new" || createMutation.isPending) {
    return <EditorShell message="Creating draft automation..." />;
  }

  if (!activeWorkspace) {
    return (
      <EditorShell message="Connect Instagram and select a workspace before editing automations." />
    );
  }

  if (automationQuery.isLoading) {
    return <EditorShell message="Loading automation..." />;
  }

  return (
    <>
      <div className="flex items-center justify-between mb-6 -mt-2">
        <div className="flex items-center gap-3 min-w-0">
          <Link
            to="/automations"
            className="w-9 h-9 rounded-md hover:bg-muted flex items-center justify-center shrink-0"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="text-[18px] font-bold bg-transparent outline-none focus:bg-muted px-2 py-1 rounded min-w-0"
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => testMutation.mutate()}
            disabled={testMutation.isPending}
            className="inline-flex items-center gap-1.5 h-10 px-3 rounded-lg border border-border bg-card text-sm font-medium hover:bg-muted"
          >
            <Play className="w-3.5 h-3.5" /> {testMutation.isPending ? "Testing..." : "Re-Trigger"}
          </button>
          <button
            onClick={toggleActive}
            disabled={!trigger || statusMutation.isPending}
            className={`relative w-11 h-6 rounded-full transition ${
              automationQuery.data?.status === "active" ? "bg-success" : "bg-muted"
            } ${!trigger ? "opacity-40 cursor-not-allowed" : ""}`}
          >
            <span
              className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition"
              style={{ left: automationQuery.data?.status === "active" ? "22px" : "2px" }}
            />
          </button>
          <button
            onClick={save}
            disabled={updateMutation.isPending}
            className="inline-flex items-center gap-2 h-10 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition"
          >
            <Save className="w-4 h-4" /> {updateMutation.isPending ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}
      {testMutation.data && (
        <div className="mb-4 rounded-lg bg-accent px-4 py-3 text-sm text-primary">
          Test trigger queued: {testMutation.data.status}
        </div>
      )}

      <div className="max-w-[760px] mx-auto space-y-6">
        <Section title="Select a Trigger" subtitle="When to run automation">
          <div className="space-y-2">
            {triggers.map((item) => (
              <button
                key={item.id}
                disabled={item.soon}
                onClick={() => setTrigger(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg border text-left text-sm transition ${
                  trigger === item.id
                    ? "border-primary bg-accent"
                    : "border-border bg-card hover:bg-muted"
                } ${item.soon ? "opacity-60 cursor-not-allowed" : ""}`}
              >
                <Zap className="w-4 h-4 text-primary shrink-0" />
                <span className="flex-1">{item.label}</span>
                {item.soon && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-accent text-primary">
                    Coming Soon
                  </span>
                )}
              </button>
            ))}
          </div>
        </Section>

        {trigger && (
          <Section title="Trigger Config" subtitle="Keywords and source configuration">
            {(trigger === "comment-post" || trigger === "story-reply") && (
              <Field label={trigger === "comment-post" ? "Post or Reel ID" : "Story ID"}>
                <input
                  className="ipt"
                  value={postId}
                  onChange={(event) => setPostId(event.target.value)}
                  placeholder="Instagram media ID"
                />
              </Field>
            )}
            <Field label="Keywords">
              <input
                className="ipt"
                value={keywords}
                onChange={(event) => setKeywords(event.target.value)}
                placeholder="price, buy, giveaway"
              />
            </Field>
          </Section>
        )}

        <Section title="Response Flow" subtitle="The first action step this automation will run">
          <Field label="DM Message">
            <textarea
              className="ipt min-h-[120px] py-3"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Hey! Thanks for reaching out."
            />
          </Field>
          <div className="mt-4 border-t border-border pt-4 flex items-start gap-3 text-xs text-muted-foreground">
            <Info className="w-3.5 h-3.5 mt-0.5" />
            Activation requires a trigger, valid trigger config, and at least one response step.
          </div>
        </Section>
      </div>
      <InputStyles />
    </>
  );
}

function buildTriggerConfig(trigger: UiTrigger, keywords: string, postId: string) {
  const parsedKeywords = keywords
    .split(",")
    .map((keyword) => keyword.trim())
    .filter(Boolean);

  if (trigger === "comment-post") {
    return { post_id: postId.trim(), keywords: parsedKeywords, match: "any" };
  }
  if (trigger === "story-reply") {
    return {
      story_ids: postId.trim() ? [postId.trim()] : [],
      keywords: parsedKeywords,
      match: "any",
    };
  }
  return { keywords: parsedKeywords, match: "any" };
}

function buildSteps(message: string): AutomationStep[] {
  if (!message.trim()) return [];
  return [{ order: 1, action_type: "send_dm", config: { message: message.trim() } }];
}

function EditorShell({ message }: { message: string }) {
  return (
    <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-10 text-center text-sm text-muted-foreground">
      {message}
    </div>
  );
}

function Section({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6">
      <div className="mb-5">
        <div className="text-base font-bold">{title}</div>
        {subtitle && <div className="text-xs text-muted-foreground mt-0.5">{subtitle}</div>}
      </div>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-medium mb-1.5 block">{label}</span>
      {children}
    </label>
  );
}

function InputStyles() {
  return (
    <style>{`.ipt { width:100%; min-height:44px; padding:0 14px; border:1px solid var(--border); border-radius:10px; font-size:14px; outline:none; background:var(--surface); }
.ipt:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(61,58,238,0.12); }`}</style>
  );
}
