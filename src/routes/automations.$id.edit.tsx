import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import {
  ArrowLeft,
  Info,
  Play,
  Save,
  Zap,
  ChevronUp,
  ChevronDown,
  Trash2,
  Copy,
  Plus,
  HelpCircle,
  Check,
  Crown,
  Edit,
  X,
  Sparkles,
  Image as ImageIcon,
  MessageSquare,
  UserPlus,
  FileText,
  Tag,
  UploadCloud,
  Loader2
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { FormField } from "@/components/FormField";
import { supabase } from "@/integrations/supabase/client";
import {
  useActiveWorkspace,
  useAutomationQuery,
  useAutomationStatusMutation,
  useCreateAutomationMutation,
  useInstagramMediaQuery,
  useTestTriggerMutation,
  useUpdateAutomationMutation,
  useBillingQueries
} from "@/lib/api/hooks";
import type { AutomationStep, TriggerType } from "@/lib/api/types";

export const Route = createFileRoute("/automations/$id/edit")({
  head: () => ({ meta: [{ title: "Edit automation - Vibe DM" }] }),
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

interface ResponseButton {
  text: string;
  action_type: "open_url" | "trigger_message";
  url?: string;
}

interface StepConfig {
  type: "card" | "text" | "image" | "ask_follow" | "lead_form";
  message?: string;
  title?: string;
  subtitle?: string;
  image_url?: string;
  buttons?: ResponseButton[];
  field_type?: "email" | "phone";
}

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

  // Billing and Premium checks
  const billing = useBillingQueries(activeWorkspace?.id);
  const isPro = billing.subscription.data?.plan_id !== "free" && billing.subscription.data?.plan_id !== undefined;

  // State values
  const [name, setName] = useState("Untitled automation");
  const [trigger, setTrigger] = useState<UiTrigger | null>(null);
  const [postId, setPostId] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Keywords tag states
  const [showKeywordsModal, setShowKeywordsModal] = useState(false);
  const [anyKeyword, setAnyKeyword] = useState(false);
  const [keywordsList, setKeywordsList] = useState<string[]>([]);
  const [tempKeywordInput, setTempKeywordInput] = useState("");

  // Rich response states
  const [openingMessageEnabled, setOpeningMessageEnabled] = useState(false);
  const [openingMessage, setOpeningMessage] = useState({
    text: "Hey there!\n\nI'm so happy you're here, thank you so much for your interest 😊\n\nClick below and I'll send you the link in just a sec ✨",
    buttonText: "Send me the link"
  });
  const [editingOpeningMessage, setEditingOpeningMessage] = useState(false);

  const [followUpEnabled, setFollowUpEnabled] = useState(false);
  const [followUpDelay, setFollowUpDelay] = useState(10); // in minutes
  const [followUpMessage, setFollowUpMessage] = useState("Hey there! Just checking in to see if you had any questions or if you got the link successfully 😊");

  const [steps, setSteps] = useState<AutomationStep[]>([]);
  
  // Modals state
  const [showAddResponseModal, setShowAddResponseModal] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [upgradeFeatureName, setUpgradeFeatureName] = useState("");

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
    setPostId(typeof config.post_id === "string" ? config.post_id : "");

    // Load Keywords
    const list = Array.isArray(config.keywords) ? config.keywords : [];
    setKeywordsList(list);
    setAnyKeyword(!!config.any_keyword || (list.length === 0 && config.any_keyword !== false));

    // Load rich states
    setOpeningMessageEnabled(!!config.opening_message_enabled);
    const openMsg = config.opening_message as any;
    if (openMsg) {
      setOpeningMessage({
        text: openMsg.text || "",
        buttonText: openMsg.buttonText || "Send me the link"
      });
    }
    setFollowUpEnabled(!!config.follow_up_enabled);
    setFollowUpDelay(typeof config.follow_up_delay === "number" ? config.follow_up_delay : 10);
    setFollowUpMessage(typeof config.follow_up_message === "string" ? config.follow_up_message : "Hey there! Just checking in to see if you had any questions or if you got the link successfully 😊");

    setSteps(automation.steps || []);
  }, [automationQuery.data]);

  const triggerUpgradeModal = (feature: string) => {
    setUpgradeFeatureName(feature);
    setShowUpgradeModal(true);
  };

  const save = async () => {
    if (!activeWorkspace?.id || id === "new") return;
    setError(null);
    try {
      await updateMutation.mutateAsync({
        name,
        trigger_type: trigger ? triggerMap[trigger] : null,
        trigger_config: trigger ? buildTriggerConfig(
          trigger,
          anyKeyword ? [] : keywordsList,
          postId,
          openingMessageEnabled,
          openingMessage,
          followUpEnabled,
          followUpDelay,
          anyKeyword,
          followUpMessage
        ) : {},
        steps: steps.map((s, idx) => ({
          ...s,
          order: idx + 1
        })),
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

  // Helper visibility for Opening Message toggle
  const showOpeningMessageOption = trigger === "comment-post" || trigger === "live";

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

  // Steps manipulators
  const addStep = (type: StepConfig["type"]) => {
    // If opening message is off, we can only have one step of Text, Card or Image
    if (!openingMessageEnabled) {
      if (type === "ask_follow" || type === "lead_form") {
        return; // UI already prevents this, but safety check
      }
      // Replace existing step if any
      const newStep: AutomationStep = {
        order: 1,
        action_type: "send_dm",
        config: buildDefaultStepConfig(type) as any
      };
      setSteps([newStep]);
    } else {
      const nextOrder = steps.length + 1;
      let actionType: AutomationStep["action_type"] = "send_dm";
      if (type === "ask_follow") actionType = "tag_contact";
      else if (type === "lead_form") actionType = "ask_for_email";

      const newStep: AutomationStep = {
        order: nextOrder,
        action_type: actionType,
        config: buildDefaultStepConfig(type) as any
      };
      setSteps([...steps, newStep]);
    }
    setShowAddResponseModal(false);
  };

  const deleteStep = (index: number) => {
    const updated = steps.filter((_, idx) => idx !== index);
    setSteps(updated.map((s, idx) => ({ ...s, order: idx + 1 })));
  };

  const duplicateStep = (index: number) => {
    if (!openingMessageEnabled) return; // not allowed when opening message is off
    const sourceStep = steps[index];
    const newStep = {
      ...sourceStep,
      id: undefined, // ensure new UUID is generated on back-end
      order: steps.length + 1,
      config: JSON.parse(JSON.stringify(sourceStep.config)) // deep copy
    };
    setSteps([...steps, newStep]);
  };

  const moveStep = (index: number, direction: "up" | "down") => {
    if (direction === "up" && index === 0) return;
    if (direction === "down" && index === steps.length - 1) return;

    const newIndex = direction === "up" ? index - 1 : index + 1;
    const reordered = [...steps];
    const temp = reordered[index];
    reordered[index] = reordered[newIndex];
    reordered[newIndex] = temp;

    setSteps(reordered.map((s, idx) => ({ ...s, order: idx + 1 })));
  };

  const updateStepConfig = (index: number, configUpdates: Partial<StepConfig>) => {
    const reordered = [...steps];
    reordered[index] = {
      ...reordered[index],
      config: {
        ...reordered[index].config,
        ...configUpdates
      }
    };
    
    // Automatically keep compatibility field "message" synced for the backend DMs
    const config = reordered[index].config as any;
    if (config) {
      const stepType = config.type;
      if (stepType === "card") {
        config.message = `${config.title || ""}\n${config.subtitle || ""}`.trim() || "Card message";
      } else if (stepType === "image") {
        config.message = `Image URL: ${config.image_url || ""}`.trim() || "Image message";
      } else if (stepType === "lead_form") {
        const fieldType = config.field_type || "email";
        reordered[index].action_type = fieldType === "email" ? "ask_for_email" : "ask_for_phone";
      } else if (stepType === "ask_follow") {
        reordered[index].action_type = "tag_contact";
      }
    }

    setSteps(reordered);
  };

  // Keywords management inside the modal
  const addKeyword = (word: string) => {
    const trimmed = word.trim();
    if (!trimmed) return;
    // Check if case-insensitive duplicate exists
    const duplicate = keywordsList.some(k => k.toLowerCase() === trimmed.toLowerCase());
    if (!duplicate) {
      setKeywordsList([...keywordsList, trimmed]);
    }
    setTempKeywordInput("");
  };

  const deleteKeyword = (index: number) => {
    setKeywordsList(keywordsList.filter((_, idx) => idx !== index));
  };

  return (
    <>
      <div className="flex items-center justify-between mb-6 -mt-2">
        <div className="flex items-center gap-3 min-w-0">
          <Link
            to="/automations"
            className="w-9 h-9 rounded-md hover:bg-muted flex items-center justify-center shrink-0"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="text-[18px] font-bold bg-transparent outline-none focus:bg-muted px-2 py-1 rounded min-w-0"
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => testMutation.mutate()}
            disabled={testMutation.isPending}
            className="inline-flex items-center gap-1.5 h-10 px-3 rounded-lg border border-border bg-card text-sm font-medium hover:bg-muted"
          >
            <Play className="w-3.5 h-3.5" /> {testMutation.isPending ? "Testing..." : "Re-Trigger"}
          </button>
          <button
            type="button"
            onClick={toggleActive}
            disabled={!trigger || statusMutation.isPending}
            className={`relative w-11 h-6 rounded-full transition ${
              automationQuery.data?.status === "active" ? "bg-success" : "bg-muted"
            } ${!trigger ? "opacity-40 cursor-not-allowed" : ""}`}
          >
            <span
              className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition animate-all"
              style={{ left: automationQuery.data?.status === "active" ? "22px" : "2px" }}
            />
          </button>
          <button
            type="button"
            onClick={save}
            disabled={updateMutation.isPending}
            className="inline-flex items-center gap-2 h-10 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition"
          >
            <Save className="size-4" /> {updateMutation.isPending ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive font-medium">
          {error}
        </div>
      )}
      {testMutation.data && (
        <div className="mb-4 rounded-lg bg-accent px-4 py-3 text-sm text-primary font-medium flex items-center gap-2">
          <Sparkles className="size-4" /> Test trigger queued successfully: {testMutation.data.status}
        </div>
      )}

      <div className="max-w-[760px] mx-auto space-y-6">
        {/* SELECT A TRIGGER */}
        <Section title="Select a Trigger" subtitle="When to run automation">
          <div className="space-y-2">
            {triggers.map((item) => (
              <button
                type="button"
                key={item.id}
                disabled={item.soon}
                onClick={() => setTrigger(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-lg border text-left text-sm transition-all duration-200 ${
                  trigger === item.id
                    ? "border-primary bg-primary/5 ring-1 ring-primary/20"
                    : "border-border bg-card hover:bg-muted"
                } ${item.soon ? "opacity-60 cursor-not-allowed" : "cursor-pointer"}`}
              >
                <Zap className={`size-4 shrink-0 transition-colors ${trigger === item.id ? "text-primary" : "text-muted-foreground"}`} />
                <span className="flex-1 font-medium">{item.label}</span>
                {item.soon && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-accent text-primary">
                    Coming Soon
                  </span>
                )}
              </button>
            ))}
          </div>
        </Section>

        {/* TRIGGER CONFIG */}
        {trigger && (
          <Section title="Trigger Config" subtitle="Keywords and source configuration">
            {trigger === "comment-post" && (
              <FormField label="Select Post or Reel">
                <InstagramMediaSelector
                  workspaceId={activeWorkspace.id}
                  selectedId={postId}
                  onChange={setPostId}
                />
              </FormField>
            )}
            {trigger === "story-reply" && (
              <FormField label="Story ID">
                <input
                  className="ipt"
                  value={postId}
                  onChange={(event) => setPostId(event.target.value)}
                  placeholder="Instagram story ID"
                />
              </FormField>
            )}
            
            {/* Configure Keywords Trigger Button & Sleek Inline Previews */}
            <FormField label="Keywords">
              <div className="space-y-3">
                <button
                  type="button"
                  onClick={() => setShowKeywordsModal(true)}
                  className="inline-flex items-center gap-2 h-10 px-4 rounded-xl border border-border bg-card text-xs font-semibold hover:bg-muted transition cursor-pointer text-foreground shadow-sm"
                >
                  <Tag className="size-3.5 text-muted-foreground" /> Configure Keywords
                </button>
                
                <div className="flex flex-wrap gap-1.5 min-h-[36px] items-center p-2.5 rounded-xl bg-muted/30 border border-border/60">
                  {anyKeyword ? (
                    <span className="text-[11px] font-extrabold px-3 py-1 rounded-lg bg-indigo-50 border border-indigo-100 text-primary flex items-center gap-1.5 select-none">
                      <Sparkles className="size-3" /> Triggers on any comment
                    </span>
                  ) : keywordsList.length > 0 ? (
                    keywordsList.map((kw, idx) => (
                      <span
                        key={idx}
                        className="text-[11px] font-bold px-2.5 py-1 rounded-lg bg-white border border-border text-foreground shadow-sm animate-in fade-in zoom-in-95"
                      >
                        {kw}
                      </span>
                    ))
                  ) : (
                    <span className="text-[11px] font-medium text-muted-foreground italic pl-1 select-none">
                      No keywords configured yet
                    </span>
                  )}
                </div>
              </div>
            </FormField>
          </Section>
        )}

        {/* RESPONSE FLOW SECTION */}
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <div>
              <h2 className="text-base font-bold text-foreground">Response Flow</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                The action sequence this automation will execute
              </p>
            </div>
          </div>

          {/* 1. Opening Message Toggle & Custom Card */}
          {showOpeningMessageOption && (
            <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-5 space-y-4 transition-all duration-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-foreground">Opening Message</span>
                  <div className="relative group">
                    <Info className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                    <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block w-56 bg-black text-white text-[11px] p-2 rounded-lg shadow-lg z-10 leading-tight">
                      First greeting message sent to users immediately after they comment. Required to capture followers or email leads.
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    const nextVal = !openingMessageEnabled;
                    setOpeningMessageEnabled(nextVal);
                    if (!nextVal) {
                      // Adjust steps if opening message disabled
                      if (steps.length > 1) {
                        setSteps([steps[0]]);
                      }
                    }
                  }}
                  className={`relative w-11 h-6 rounded-full transition-all duration-200 ${
                    openingMessageEnabled ? "bg-primary" : "bg-muted"
                  }`}
                >
                  <span
                    className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all duration-200"
                    style={{ left: openingMessageEnabled ? "22px" : "2px" }}
                  />
                </button>
              </div>

              {/* Interactive Opening Message Card */}
              {openingMessageEnabled && (
                <div className="rounded-xl border border-border bg-muted/40 p-4 space-y-4 relative transition-all duration-300 animate-in fade-in slide-in-from-top-2">
                  {!editingOpeningMessage ? (
                    <div className="flex flex-col items-center">
                      <div className="w-full max-w-[340px] bg-white rounded-2xl border border-border/80 p-4 shadow-sm space-y-4 text-center relative">
                        <button
                          type="button"
                          onClick={() => setEditingOpeningMessage(true)}
                          className="absolute top-3 right-3 text-xs font-semibold text-muted-foreground hover:text-primary flex items-center gap-1 cursor-pointer bg-muted/30 px-2.5 py-1 rounded-md border border-border/60 transition"
                        >
                          Edit <Edit className="size-3" />
                        </button>
                        <div className="text-[13px] text-foreground leading-relaxed text-left whitespace-pre-line pt-2 pr-12">
                          {openingMessage.text || "Hello there!"}
                        </div>
                        {openingMessage.buttonText && (
                          <div className="w-full py-2.5 px-4 rounded-xl border border-primary/20 text-primary font-semibold text-[13px] bg-primary/5 select-none text-center">
                            {openingMessage.buttonText}
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3 bg-white p-4 rounded-xl border border-border/60">
                      <FormField label="Greeting Text">
                        <textarea
                          rows={4}
                          className="ipt min-h-[90px] py-2.5"
                          value={openingMessage.text}
                          onChange={(e) => setOpeningMessage({ ...openingMessage, text: e.target.value })}
                          placeholder="Hey there! Thanks for reaching out..."
                        />
                      </FormField>
                      <FormField label="Button Label">
                        <input
                          type="text"
                          className="ipt"
                          value={openingMessage.buttonText}
                          onChange={(e) => setOpeningMessage({ ...openingMessage, buttonText: e.target.value })}
                          placeholder="Send me the link"
                        />
                      </FormField>
                      <div className="flex justify-end gap-2 pt-1">
                        <button
                          type="button"
                          onClick={() => setEditingOpeningMessage(false)}
                          className="px-3 py-1.5 rounded-lg border border-border text-xs font-semibold hover:bg-muted cursor-pointer"
                        >
                          Done
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Sequential Step Cards */}
          {steps.map((step, idx) => {
            const stepConfig = (step.config || {}) as any;
            return (
              <div
                key={step.id || idx}
                className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-5 space-y-4 relative transition-all duration-300 animate-in fade-in"
              >
                {/* Header */}
                <div className="flex items-center justify-between pb-2 border-b border-border/50">
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-full bg-black text-white text-[13px] font-bold flex items-center justify-center">
                      {idx + 1}
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[14px] font-bold text-foreground">
                        {stepConfig.type === "card" && "Card Message"}
                        {stepConfig.type === "text" && "Text Message"}
                        {stepConfig.type === "image" && "Image Response"}
                        {stepConfig.type === "ask_follow" && "Ask For Follow"}
                        {stepConfig.type === "lead_form" && "Lead Forms"}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1">
                    {openingMessageEnabled && (
                      <>
                        <button
                          type="button"
                          onClick={() => moveStep(idx, "up")}
                          disabled={idx === 0}
                          className="w-8 h-8 rounded-lg flex items-center justify-center border border-border hover:bg-muted text-muted-foreground disabled:opacity-40 transition cursor-pointer"
                        >
                          <ChevronUp className="size-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => moveStep(idx, "down")}
                          disabled={idx === steps.length - 1}
                          className="w-8 h-8 rounded-lg flex items-center justify-center border border-border hover:bg-muted text-muted-foreground disabled:opacity-40 transition cursor-pointer"
                        >
                          <ChevronDown className="size-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => duplicateStep(idx)}
                          className="w-8 h-8 rounded-lg flex items-center justify-center border border-border hover:bg-muted text-muted-foreground transition cursor-pointer"
                          title="Duplicate Step"
                        >
                          <Copy className="size-3.5" />
                        </button>
                      </>
                    )}
                    <button
                      type="button"
                      onClick={() => deleteStep(idx)}
                      className="w-8 h-8 rounded-lg flex items-center justify-center border border-border hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition cursor-pointer"
                      title="Delete Step"
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </div>
                </div>

                {/* Step Editor Content */}
                <div className="space-y-4">
                  {stepConfig.type === "text" && (
                    <TextResponseEditor
                      config={stepConfig}
                      onChange={(updates) => updateStepConfig(idx, updates)}
                    />
                  )}
                  {stepConfig.type === "card" && (
                    <CardResponseEditor
                      config={stepConfig}
                      onChange={(updates) => updateStepConfig(idx, updates)}
                      workspaceId={activeWorkspace.id}
                    />
                  )}
                  {stepConfig.type === "image" && (
                    <ImageResponseEditor
                      config={stepConfig}
                      onChange={(updates) => updateStepConfig(idx, updates)}
                      workspaceId={activeWorkspace.id}
                    />
                  )}
                  {stepConfig.type === "ask_follow" && (
                    <AskFollowResponseEditor
                      config={stepConfig}
                      onChange={(updates) => updateStepConfig(idx, updates)}
                    />
                  )}
                  {stepConfig.type === "lead_form" && (
                    <LeadFormResponseEditor
                      config={stepConfig}
                      onChange={(updates) => updateStepConfig(idx, updates)}
                    />
                  )}
                </div>
              </div>
            );
          })}

          {/* Add Response Button Trigger */}
          {(!openingMessageEnabled && steps.length > 0) ? null : (
            <button
              type="button"
              onClick={() => setShowAddResponseModal(true)}
              className="w-full py-3.5 rounded-xl border border-primary bg-primary text-white font-bold hover:bg-primary-dark transition-all duration-200 shadow-sm flex items-center justify-center gap-2 cursor-pointer text-[14px]"
            >
              <Plus className="size-4" /> Add Response
            </button>
          )}

          {/* 3. Follow-up Message (PRO) Box */}
          <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-5 space-y-4 transition-all duration-200">
            <div className="flex items-start justify-between">
              <div className="space-y-1 pr-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-foreground">Follow-up Message</span>
                  <span className="text-[10px] font-extrabold uppercase bg-amber-100 border border-amber-200 text-amber-600 px-2 py-0.5 rounded flex items-center gap-0.5 select-none leading-none pt-1">
                    PRO <Crown className="size-2.5 fill-amber-500 stroke-none" />
                  </span>
                </div>
                <div className="text-xs text-muted-foreground leading-normal">
                  Send after automation completes (delay: 1 min to 23 hr 30 min)
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  if (!showOpeningMessageOption || !openingMessageEnabled) return;
                  if (!isPro) {
                    triggerUpgradeModal("Follow-up sequences");
                    return;
                  }
                  setFollowUpEnabled(!followUpEnabled);
                }}
                disabled={!showOpeningMessageOption || !openingMessageEnabled}
                className={`relative w-11 h-6 rounded-full transition-all duration-200 shrink-0 ${
                  followUpEnabled ? "bg-primary" : "bg-muted"
                } ${(!showOpeningMessageOption || !openingMessageEnabled) ? "opacity-40 cursor-not-allowed" : "cursor-pointer"}`}
              >
                <span
                  className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all duration-200"
                  style={{ left: followUpEnabled ? "22px" : "2px" }}
                />
              </button>
            </div>

            {/* Delay Slider and Subtext */}
            {followUpEnabled && showOpeningMessageOption && openingMessageEnabled && (
              <div className="rounded-xl border border-border bg-muted/40 p-4 space-y-4 animate-in fade-in slide-in-from-top-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-muted-foreground">Adjust Delay Time</span>
                  <span className="text-xs font-bold text-primary bg-primary/10 px-2.5 py-1 rounded-md border border-primary/20">
                    {formatDelay(followUpDelay)}
                  </span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="1410"
                  step="5"
                  value={followUpDelay}
                  onChange={(e) => setFollowUpDelay(parseInt(e.target.value))}
                  className="w-full h-1.5 bg-border rounded-lg appearance-none cursor-pointer accent-primary outline-none"
                />
                <div className="flex items-center justify-between text-[10px] text-muted-foreground px-0.5 pb-2 border-b border-border/40">
                  <span>1 min</span>
                  <span>6 hours</span>
                  <span>12 hours</span>
                  <span>18 hours</span>
                  <span>23 hours 30 min</span>
                </div>
                
                {/* Custom Follow-up Message Text Input */}
                <FormField label="Follow-up Message Text">
                  <textarea
                    rows={3}
                    className="ipt min-h-[80px] py-2 bg-white"
                    value={followUpMessage}
                    onChange={(e) => setFollowUpMessage(e.target.value)}
                    placeholder="Enter follow-up message text..."
                  />
                </FormField>
              </div>
            )}

            {/* Ineligibility notice */}
            {(!showOpeningMessageOption || !openingMessageEnabled) && (
              <div className="text-[11px] text-amber-600 font-medium bg-amber-500/5 border border-amber-500/10 p-2.5 rounded-lg">
                Available only for Post/Live triggers with Opening Message enabled.
              </div>
            )}
          </div>

          <div className="mt-4 border-t border-border pt-4 flex items-start gap-3 text-xs text-muted-foreground">
            <Info className="w-3.5 h-3.5 mt-0.5 shrink-0" />
            Activation requires a trigger, valid trigger config, and at least one response step.
          </div>
        </div>
      </div>

      {/* 4. Upgrade Popup Modal */}
      {showUpgradeModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in">
          <div className="w-full max-w-[420px] bg-white rounded-2xl border border-border/80 p-6 shadow-2xl relative space-y-5 text-center animate-in zoom-in-95 duration-200">
            <button
              type="button"
              onClick={() => setShowUpgradeModal(false)}
              className="absolute top-4 right-4 text-muted-foreground hover:text-foreground cursor-pointer"
            >
              <X className="size-4" />
            </button>
            <div className="w-14 h-14 bg-amber-100 text-amber-600 rounded-2xl flex items-center justify-center mx-auto shadow-sm">
              <Crown className="size-7 fill-amber-500 stroke-none" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-extrabold text-foreground">Unlock Pro Sequences</h3>
              <p className="text-xs text-muted-foreground leading-relaxed max-w-sm mx-auto">
                {upgradeFeatureName ? `"${upgradeFeatureName}" is` : "Premium actions are"} exclusive to Pro workspaces. Scale your Instagram conversion sequences instantly.
              </p>
            </div>
            <div className="bg-muted/40 border border-border/60 rounded-xl p-3.5 text-left space-y-2 text-[11px] text-muted-foreground">
              <div className="flex items-center gap-2"><Check className="size-3.5 text-success shrink-0" /> Follow-up messages & sequential flows</div>
              <div className="flex items-center gap-2"><Check className="size-3.5 text-success shrink-0" /> Ask For Follow & automated verification</div>
              <div className="flex items-center gap-2"><Check className="size-3.5 text-success shrink-0" /> Lead generation forms (Email & Phone capture)</div>
            </div>
            <div className="flex flex-col gap-2 pt-1">
              <Link
                to="/settings"
                onClick={() => setShowUpgradeModal(false)}
                className="w-full py-2.5 px-4 rounded-xl bg-primary text-primary-foreground font-bold hover:bg-primary-dark transition text-[13px] text-center"
              >
                View Plans & Upgrade
              </Link>
              <button
                type="button"
                onClick={() => setShowUpgradeModal(false)}
                className="w-full py-2.5 px-4 rounded-xl border border-border text-foreground hover:bg-muted font-bold transition text-[13px] cursor-pointer"
              >
                Maybe Later
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 5. Add Response Modal */}
      {showAddResponseModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in">
          <div className="w-full max-w-[440px] bg-white rounded-2xl border border-border/80 shadow-2xl relative animate-in zoom-in-95 duration-200 flex flex-col max-h-[85vh]">
            {/* Header */}
            <div className="p-4 border-b border-border/60 flex items-center justify-between shrink-0">
              <h3 className="font-extrabold text-[15px] text-foreground">Add Response</h3>
              <button
                type="button"
                onClick={() => setShowAddResponseModal(false)}
                className="w-7 h-7 rounded-lg border border-border flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted cursor-pointer transition"
              >
                <X className="size-4" />
              </button>
            </div>

            {/* Yellow warning alert box */}
            {!openingMessageEnabled && (
              <div className="mx-4 mt-4 p-3 rounded-lg border border-amber-500/20 bg-amber-500/5 text-amber-700 text-xs font-semibold flex items-start gap-2 animate-in fade-in">
                <Info className="size-4 shrink-0 text-amber-600 mt-0.5" />
                <span>Opening message is turned off, only one of Text, Card or Image is allowed</span>
              </div>
            )}

            {/* List options */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
              {/* ASK FOR FOLLOW */}
              <button
                type="button"
                disabled={!openingMessageEnabled}
                onClick={() => {
                  if (!isPro) {
                    triggerUpgradeModal("Ask For Follow");
                    return;
                  }
                  addStep("ask_follow");
                }}
                className={`w-full flex items-center gap-3.5 p-3 rounded-xl border text-left transition ${
                  openingMessageEnabled
                    ? "border-border hover:border-primary/50 hover:bg-accent/40 cursor-pointer"
                    : "border-border/60 bg-muted/30 opacity-60 cursor-not-allowed"
                }`}
              >
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${openingMessageEnabled ? "bg-indigo-100 text-primary" : "bg-muted text-muted-foreground"}`}>
                  <UserPlus className="size-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className={`text-[13px] font-bold ${openingMessageEnabled ? "text-foreground" : "text-muted-foreground"}`}>Ask For Follow</span>
                    <span className="text-[9px] font-extrabold uppercase bg-amber-100 text-amber-600 border border-amber-200 px-1.5 py-0.5 rounded">PRO</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground leading-normal mt-0.5 font-medium">Request users to follow your account</p>
                  {!openingMessageEnabled && (
                    <p className="text-[10px] text-destructive font-bold mt-1">Requires Opening Message</p>
                  )}
                </div>
              </button>

              {/* CARD MESSAGE */}
              <button
                type="button"
                onClick={() => addStep("card")}
                className="w-full flex items-center gap-3.5 p-3 rounded-xl border border-border hover:border-primary/50 hover:bg-accent/40 cursor-pointer text-left transition"
              >
                <div className="w-9 h-9 rounded-lg bg-indigo-100 text-primary flex items-center justify-center shrink-0">
                  <ImageIcon className="size-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-[13px] font-bold text-foreground">Card Message</span>
                  <p className="text-[11px] text-muted-foreground leading-normal mt-0.5 font-medium">Send a rich card with Image, Texts and Button</p>
                </div>
              </button>

              {/* TEXT MESSAGE */}
              <button
                type="button"
                onClick={() => addStep("text")}
                className="w-full flex items-center gap-3.5 p-3 rounded-xl border border-border hover:border-primary/50 hover:bg-accent/40 cursor-pointer text-left transition"
              >
                <div className="w-9 h-9 rounded-lg bg-indigo-100 text-primary flex items-center justify-center shrink-0">
                  <MessageSquare className="size-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-[13px] font-bold text-foreground">Text Message</span>
                  <p className="text-[11px] text-muted-foreground leading-normal mt-0.5 font-medium">Send a simple Text or Button Response</p>
                </div>
              </button>

              {/* IMAGE MESSAGE */}
              <button
                type="button"
                onClick={() => addStep("image")}
                className="w-full flex items-center gap-3.5 p-3 rounded-xl border border-border hover:border-primary/50 hover:bg-accent/40 cursor-pointer text-left transition"
              >
                <div className="w-9 h-9 rounded-lg bg-indigo-100 text-primary flex items-center justify-center shrink-0">
                  <Sparkles className="size-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-[13px] font-bold text-foreground">Image Message</span>
                  <p className="text-[11px] text-muted-foreground leading-normal mt-0.5 font-medium">Send an uploaded image response</p>
                </div>
              </button>

              {/* LEAD FORMS */}
              <button
                type="button"
                disabled={!openingMessageEnabled}
                onClick={() => {
                  if (!isPro) {
                    triggerUpgradeModal("Lead Forms");
                    return;
                  }
                  addStep("lead_form");
                }}
                className={`w-full flex items-center gap-3.5 p-3 rounded-xl border text-left transition ${
                  openingMessageEnabled
                    ? "border-border hover:border-primary/50 hover:bg-accent/40 cursor-pointer"
                    : "border-border/60 bg-muted/30 opacity-60 cursor-not-allowed"
                }`}
              >
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${openingMessageEnabled ? "bg-indigo-100 text-primary" : "bg-muted text-muted-foreground"}`}>
                  <FileText className="size-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className={`text-[13px] font-bold ${openingMessageEnabled ? "text-foreground" : "text-muted-foreground"}`}>Lead Forms</span>
                    <span className="text-[9px] font-extrabold uppercase bg-amber-100 text-amber-600 border border-amber-200 px-1.5 py-0.5 rounded">PRO</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground leading-normal mt-0.5 font-medium">Request users to input text</p>
                  {!openingMessageEnabled && (
                    <p className="text-[10px] text-destructive font-bold mt-1 font-semibold">Requires Opening Message</p>
                  )}
                </div>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 6. Setup Keywords Modal */}
      {showKeywordsModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in">
          <div className="w-full max-w-[420px] bg-white rounded-2xl border border-border/80 p-6 shadow-2xl relative space-y-4 animate-in zoom-in-95 duration-200">
            {/* Close trigger */}
            <button
              type="button"
              onClick={() => setShowKeywordsModal(false)}
              className="absolute top-4 right-4 text-muted-foreground hover:text-foreground cursor-pointer transition"
            >
              <X className="size-4" />
            </button>
            
            <div className="space-y-1 pr-8">
              <h3 className="text-[16px] font-extrabold text-foreground tracking-tight">Setup Keywords</h3>
              <p className="text-[11px] text-muted-foreground leading-relaxed leading-normal">
                Keywords are not case-sensitive, e.g., "Link" and "link" are recognized as the same.
              </p>
            </div>

            {/* Keyword tag addition */}
            <div className="space-y-3 pt-2">
              <div className="relative">
                <input
                  type="text"
                  disabled={anyKeyword}
                  className={`ipt pr-14 ${anyKeyword ? "opacity-50 cursor-not-allowed bg-muted/40" : ""}`}
                  placeholder={anyKeyword ? "Disabled (matches any comment)" : "Type & Hit ↵ Enter to add Keyword"}
                  value={tempKeywordInput}
                  onChange={(e) => setTempKeywordInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addKeyword(tempKeywordInput);
                    }
                  }}
                />
                {!anyKeyword && (
                  <button
                    type="button"
                    onClick={() => addKeyword(tempKeywordInput)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 h-8 px-2.5 rounded-lg bg-primary text-white text-[11px] font-extrabold hover:bg-primary-dark transition cursor-pointer"
                  >
                    Add
                  </button>
                )}
              </div>

              {/* Tags layout */}
              {!anyKeyword && (
                <div className="flex flex-wrap gap-1.5 max-h-[140px] overflow-y-auto p-1 border border-border/55 rounded-xl bg-muted/15 min-h-[44px] items-center">
                  {keywordsList.map((kw, idx) => (
                    <span
                      key={idx}
                      className="text-[11px] font-bold px-2.5 py-1 rounded-lg bg-white border border-border text-foreground flex items-center gap-1.5 shadow-sm animate-in fade-in"
                    >
                      {kw}
                      <button
                        type="button"
                        onClick={() => deleteKeyword(idx)}
                        className="text-muted-foreground hover:text-destructive cursor-pointer transition p-0.5 hover:bg-muted rounded-full"
                      >
                        <X className="size-3" />
                      </button>
                    </span>
                  ))}
                  {keywordsList.length === 0 && (
                    <span className="text-[10px] text-muted-foreground italic pl-2 py-1 select-none">
                      Type a word and press enter above to define matching filters
                    </span>
                  )}
                </div>
              )}

              {/* Any Keyword Toggle Switch */}
              <div className="flex items-center justify-between py-2 border-t border-border/40 mt-1">
                <span className="text-[13px] font-semibold text-foreground select-none">Any keyword</span>
                <button
                  type="button"
                  onClick={() => setAnyKeyword(!anyKeyword)}
                  className={`relative w-11 h-6 rounded-full transition-all duration-200 cursor-pointer ${
                    anyKeyword ? "bg-primary" : "bg-muted"
                  }`}
                >
                  <span
                    className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all duration-200"
                    style={{ left: anyKeyword ? "22px" : "2px" }}
                  />
                </button>
              </div>
            </div>

            {/* Confirm buttons */}
            <div className="pt-2 shrink-0">
              <button
                type="button"
                onClick={() => {
                  setShowKeywordsModal(false);
                  save();
                }}
                className="w-full py-3.5 rounded-xl bg-primary text-white font-extrabold hover:bg-primary-dark transition shadow-sm text-center text-[13px] cursor-pointer"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}

      <InputStyles />
    </>
  );
}

// FORMAT DELAY TIME
function formatDelay(mins: number): string {
  if (mins < 60) {
    return `${mins} min${mins === 1 ? "" : "s"}`;
  }
  const hours = Math.floor(mins / 60);
  const remainingMins = mins % 60;
  return `${hours} hr${hours === 1 ? "" : "s"}${remainingMins > 0 ? ` ${remainingMins} min` : ""}`;
}

// MOCK BUILD DEFAULT CONFIGS
function buildDefaultStepConfig(type: StepConfig["type"]): StepConfig {
  if (type === "card") {
    return {
      type: "card",
      title: "",
      subtitle: "",
      image_url: "",
      buttons: []
    };
  }
  if (type === "text") {
    return {
      type: "text",
      message: "",
      buttons: []
    };
  }
  if (type === "image") {
    return {
      type: "image",
      image_url: ""
    };
  }
  if (type === "ask_follow") {
    return {
      type: "ask_follow"
    };
  }
  return {
    type: "lead_form",
    field_type: "email"
  };
}

// BUILD TRIGGER CONFIG
function buildTriggerConfig(
  trigger: UiTrigger,
  keywords: string[],
  postId: string,
  openingMessageEnabled: boolean,
  openingMessage: { text: string; buttonText: string },
  followUpEnabled: boolean,
  followUpDelay: number,
  anyKeyword: boolean,
  followUpMessage: string
) {
  const baseConfig: any = {
    keywords: keywords,
    match: "any",
    any_keyword: anyKeyword,
    opening_message_enabled: openingMessageEnabled,
    opening_message: openingMessage,
    follow_up_enabled: followUpEnabled,
    follow_up_delay: followUpDelay,
    follow_up_message: followUpMessage,
  };

  if (trigger === "comment-post") {
    baseConfig.post_id = postId.trim();
  } else if (trigger === "story-reply") {
    baseConfig.story_ids = postId.trim() ? [postId.trim()] : [];
  }

  return baseConfig;
}

// EDITOR SUBCOMPONENTS

// 1. TEXT MESSAGE RESPONSE EDITOR
function TextResponseEditor({
  config,
  onChange
}: {
  config: StepConfig;
  onChange: (updates: Partial<StepConfig>) => void;
}) {
  return (
    <div className="space-y-4">
      <FormField label="Message Text">
        <textarea
          rows={3}
          className="ipt min-h-[90px] py-2.5"
          value={config.message || ""}
          onChange={(e) => onChange({ message: e.target.value })}
          placeholder="Enter message text here..."
        />
      </FormField>
      <ResponseButtonsEditor
        buttons={config.buttons || []}
        onChange={(updatedButtons) => onChange({ buttons: updatedButtons })}
      />
    </div>
  );
}

// PREMIUM IMAGE UPLOADER COMPONENT WITH DRAG & DROP AND SUPABASE STORAGE
interface PremiumImageUploaderProps {
  imageUrl: string | undefined;
  onChange: (url: string) => void;
  workspaceId: string;
  aspectRatioClass?: string;
  label: string;
}

function PremiumImageUploader({
  imageUrl,
  onChange,
  workspaceId,
  aspectRatioClass = "aspect-video",
  label
}: PremiumImageUploaderProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [urlInputValue, setUrlInputValue] = useState(imageUrl || "");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file: File) => {
    if (!file) return;

    // Validate size (1.5MB)
    if (file.size > 1.5 * 1024 * 1024) {
      setError("Image size exceeds the 1.5MB limit. Please compress your image.");
      return;
    }

    // Validate type
    if (!file.type.startsWith("image/")) {
      setError("Only image files are allowed.");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const fileExt = file.name.split('.').pop() || "png";
      const fileName = `${Date.now()}-${Math.random().toString(36).substring(2, 7)}.${fileExt}`;
      const filePath = `${workspaceId}/${fileName}`;

      // Upload file
      const { data, error: uploadError } = await supabase.storage
        .from('automation_images')
        .upload(filePath, file, {
          cacheControl: '3600',
          upsert: false
        });

      if (uploadError) {
        console.error("Supabase Storage Upload Error details:", uploadError);
        throw new Error(uploadError.message || "Failed to upload image.");
      }

      // Resolve Public URL
      const { data: { publicUrl } } = supabase.storage
        .from('automation_images')
        .getPublicUrl(filePath);

      onChange(publicUrl);
    } catch (err: any) {
      setError(
        err.message || 
        "Failed to upload. Please ensure 'automation_images' public storage bucket exists."
      );
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleUpload(e.target.files[0]);
    }
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-2">
      <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider block select-none">
        {label}
      </span>

      {error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-3.5 text-xs text-destructive font-medium flex items-start gap-2 animate-in fade-in">
          <Info className="size-4 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-bold">Upload Error:</span> {error}
          </div>
          <button 
            type="button"
            onClick={() => setError(null)} 
            className="text-destructive/60 hover:text-destructive shrink-0 cursor-pointer font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      {!imageUrl ? (
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          className={`rounded-2xl border-2 border-dashed text-center p-8 relative transition-all duration-200 ${
            dragActive 
              ? "border-primary bg-primary/5 scale-[0.99] ring-2 ring-primary/20" 
              : "border-border bg-muted/15 hover:bg-muted/20 hover:border-border-dark"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
            disabled={uploading}
          />

          {uploading ? (
            <div className="space-y-3.5 py-2 animate-pulse">
              <div className="w-11 h-11 bg-primary/10 rounded-full flex items-center justify-center mx-auto text-primary animate-spin">
                <Loader2 className="size-5" />
              </div>
              <div className="space-y-1">
                <div className="text-xs font-bold text-foreground">Uploading image...</div>
                <div className="text-[10px] text-muted-foreground">Uploading to Supabase Storage...</div>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className={`w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto text-primary transition duration-200 ${dragActive ? "scale-110" : ""}`}>
                <UploadCloud className="size-6" />
              </div>
              
              <div className="space-y-1">
                <div className="text-xs font-bold text-foreground">
                  Drag & drop your image here, or{" "}
                  <button
                    type="button"
                    onClick={triggerFileSelect}
                    className="text-primary hover:underline cursor-pointer font-bold bg-transparent border-none p-0 inline-block"
                  >
                    browse files
                  </button>
                </div>
                <div className="text-[10px] text-muted-foreground">
                  Supports JPG, PNG, GIF up to 1.5MB
                </div>
              </div>

              <div className="pt-1.5 flex flex-col items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => {
                    setShowUrlInput(!showUrlInput);
                    if (!showUrlInput) setUrlInputValue("");
                  }}
                  className="text-[10px] text-muted-foreground hover:text-foreground font-semibold underline bg-transparent border-none cursor-pointer"
                >
                  {showUrlInput ? "Cancel URL upload" : "Or use direct image URL"}
                </button>

                {showUrlInput && (
                  <div className="w-full max-w-sm mt-2 p-2 bg-white rounded-xl border border-border/80 shadow-sm flex gap-1.5 animate-in fade-in zoom-in-95">
                    <input
                      type="url"
                      className="ipt text-xs h-9 px-3 flex-1"
                      placeholder="Paste image URL here..."
                      value={urlInputValue}
                      onChange={(e) => setUrlInputValue(e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => {
                        if (urlInputValue.trim()) {
                          onChange(urlInputValue.trim());
                          setShowUrlInput(false);
                        }
                      }}
                      className="h-9 px-3 rounded-lg bg-primary text-white text-xs font-bold hover:bg-primary-dark transition cursor-pointer"
                    >
                      Apply
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className={`relative rounded-2xl overflow-hidden border border-border bg-black max-w-sm group shadow-sm ${aspectRatioClass}`}>
          <img
            src={imageUrl}
            alt="Uploaded Media"
            className="w-full h-full object-cover group-hover:scale-105 transition-all duration-300"
            onError={() => {
              setError("Failed to load image. The URL might be broken.");
              onChange("");
            }}
          />
          
          {/* Overlay controls */}
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition duration-200 flex items-center justify-center gap-3">
            <button
              type="button"
              onClick={triggerFileSelect}
              className="px-3.5 py-1.5 rounded-lg bg-white/90 hover:bg-white text-black text-xs font-bold shadow-md hover:scale-105 transition cursor-pointer"
            >
              Replace Image
            </button>
            <button
              type="button"
              onClick={() => {
                onChange("");
                setUrlInputValue("");
              }}
              className="w-8 h-8 rounded-lg bg-destructive/95 hover:bg-destructive text-white flex items-center justify-center shadow-md hover:scale-105 transition cursor-pointer"
              title="Delete Image"
            >
              <Trash2 className="size-4" />
            </button>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
            disabled={uploading}
          />
        </div>
      )}
    </div>
  );
}

// 2. CARD RESPONSE EDITOR
function CardResponseEditor({
  config,
  onChange,
  workspaceId
}: {
  config: StepConfig;
  onChange: (updates: Partial<StepConfig>) => void;
  workspaceId: string;
}) {
  return (
    <div className="space-y-4">
      <PremiumImageUploader
        imageUrl={config.image_url}
        onChange={(url) => onChange({ image_url: url })}
        workspaceId={workspaceId}
        aspectRatioClass="aspect-[1.91/1]"
        label="Card Image"
      />

      {/* Title */}
      <FormField label="Title">
        <div className="relative">
          <input
            type="text"
            maxLength={80}
            className="ipt pr-12"
            value={config.title || ""}
            onChange={(e) => onChange({ title: e.target.value })}
            placeholder="Enter title"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-bold text-muted-foreground select-none">
            {(config.title || "").length}/80
          </span>
        </div>
      </FormField>

      {/* Subtitle */}
      <FormField label="Subtitle">
        <div className="relative">
          <input
            type="text"
            maxLength={80}
            className="ipt pr-12"
            value={config.subtitle || ""}
            onChange={(e) => onChange({ subtitle: e.target.value })}
            placeholder="Enter subtitle"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-bold text-muted-foreground select-none">
            {(config.subtitle || "").length}/80
          </span>
        </div>
      </FormField>

      {/* Interactive buttons */}
      <ResponseButtonsEditor
        buttons={config.buttons || []}
        onChange={(updatedButtons) => onChange({ buttons: updatedButtons })}
      />
    </div>
  );
}

// 3. IMAGE MESSAGE EDITOR
function ImageResponseEditor({
  config,
  onChange,
  workspaceId
}: {
  config: StepConfig;
  onChange: (updates: Partial<StepConfig>) => void;
  workspaceId: string;
}) {
  return (
    <div className="space-y-4">
      <PremiumImageUploader
        imageUrl={config.image_url}
        onChange={(url) => onChange({ image_url: url })}
        workspaceId={workspaceId}
        aspectRatioClass="aspect-video"
        label="Upload Image"
      />
    </div>
  );
}

// 4. LEAD FORM EDITOR
function LeadFormResponseEditor({
  config,
  onChange
}: {
  config: StepConfig;
  onChange: (updates: Partial<StepConfig>) => void;
}) {
  const currentFieldType = config.field_type || "email";
  
  // Default values
  const defaultPrompt = currentFieldType === "email"
    ? "Please reply with your email address to continue..."
    : "Please reply with your phone number to continue...";
    
  const currentPrompt = config.message || defaultPrompt;

  const handleFieldTypeChange = (newType: "email" | "phone") => {
    const currentDefault = currentFieldType === "email"
      ? "Please reply with your email address to continue..."
      : "Please reply with your phone number to continue...";
      
    const nextDefault = newType === "email"
      ? "Please reply with your email address to continue..."
      : "Please reply with your phone number to continue...";

    const updates: Partial<StepConfig> = { field_type: newType };
    // Only switch prompt automatically if they haven't customized it yet
    if (!config.message || config.message === currentDefault) {
      updates.message = nextDefault;
    }
    onChange(updates);
  };

  return (
    <div className="space-y-4">
      <FormField label="Form Input Field">
        <select
          className="ipt"
          value={currentFieldType}
          onChange={(e) => handleFieldTypeChange(e.target.value as any)}
        >
          <option value="email">Email capture form</option>
          <option value="phone">Phone number capture form</option>
        </select>
      </FormField>

      <FormField label="Custom Prompt Text">
        <textarea
          rows={3}
          className="ipt min-h-[80px] py-2.5 bg-white"
          value={currentPrompt}
          onChange={(e) => onChange({ message: e.target.value })}
          placeholder={defaultPrompt}
        />
        <span className="text-[10px] text-muted-foreground mt-1 block">
          Custom prompt sent to users. They will reply directly to this message to submit their lead info.
        </span>
      </FormField>
    </div>
  );
}

// 5. ASK FOR FOLLOW EDITOR
function AskFollowResponseEditor({
  config,
  onChange
}: {
  config: StepConfig;
  onChange: (updates: Partial<StepConfig>) => void;
}) {
  const defaultPrompt = "To get access to the download link, please make sure you're following our account! Click follow, then reply with 'Done' to continue! 😊";
  const currentPrompt = config.message || defaultPrompt;

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-primary/5 p-4 border border-primary/10 text-center space-y-1.5 max-w-md mx-auto">
        <div className="w-9 h-9 rounded-full bg-primary/15 text-primary mx-auto flex items-center justify-center">
          <UserPlus className="size-4.5" />
        </div>
        <div className="text-[13px] font-bold text-foreground">Ask For Follow Prompt</div>
        <div className="text-[11px] text-muted-foreground leading-normal font-medium">
          Sends an automated follow invitation prompt. The flow pauses here until the contact replies or follows.
        </div>
      </div>

      <FormField label="Custom Prompt Text">
        <textarea
          rows={3}
          className="ipt min-h-[80px] py-2.5 bg-white"
          value={currentPrompt}
          onChange={(e) => onChange({ message: e.target.value })}
          placeholder={defaultPrompt}
        />
        <span className="text-[10px] text-muted-foreground mt-1 block">
          Custom prompt text sent to your DMs to request a follow.
        </span>
      </FormField>
    </div>
  );
}

// BUTTONS LIST AND EDITOR SUBCOMPONENT
function ResponseButtonsEditor({
  buttons,
  onChange
}: {
  buttons: ResponseButton[];
  onChange: (updated: ResponseButton[]) => void;
}) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [buttonText, setButtonText] = useState("");
  const [actionType, setActionType] = useState<ResponseButton["action_type"]>("open_url");
  const [buttonUrl, setButtonUrl] = useState("");

  const startAddButton = () => {
    if (buttons.length >= 3) return;
    setButtonText("");
    setActionType("open_url");
    setButtonUrl("");
    setEditingIndex(-1); // special index for adding
  };

  const startEditButton = (index: number) => {
    const btn = buttons[index];
    setButtonText(btn.text);
    setActionType(btn.action_type);
    setButtonUrl(btn.url || "");
    setEditingIndex(index);
  };

  const saveButton = () => {
    if (!buttonText.trim()) return;

    const newBtn: ResponseButton = {
      text: buttonText.trim(),
      action_type: actionType,
      ...(actionType === "open_url" ? { url: buttonUrl.trim() } : {})
    };

    if (editingIndex === -1) {
      onChange([...buttons, newBtn]);
    } else if (editingIndex !== null) {
      const updated = [...buttons];
      updated[editingIndex] = newBtn;
      onChange(updated);
    }
    setEditingIndex(null);
  };

  const deleteButton = (index: number) => {
    const updated = buttons.filter((_, idx) => idx !== index);
    onChange(updated);
    if (editingIndex === index) {
      setEditingIndex(null);
    }
  };

  return (
    <div className="space-y-3.5">
      <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider block select-none">Interactive Buttons</span>

      <div className="space-y-2">
        {buttons.map((btn, index) => (
          <div
            key={index}
            className="flex items-center justify-between rounded-xl border border-border bg-white p-3 shadow-sm hover:border-primary/40 transition group animate-in fade-in"
          >
            <div className="flex-1 min-w-0">
              <span className="text-xs font-bold text-foreground truncate block">{btn.text}</span>
              <span className="text-[10px] text-muted-foreground flex items-center gap-1.5 mt-0.5 font-medium">
                {btn.action_type === "open_url" ? (
                  <>Open URL: <span className="text-primary truncate max-w-[200px]">{btn.url || "none"}</span></>
                ) : (
                  "Trigger Sequence Step"
                )}
              </span>
            </div>
            
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition duration-150">
              <button
                type="button"
                onClick={() => startEditButton(index)}
                className="w-7 h-7 rounded-lg border border-border text-[11px] text-muted-foreground hover:text-primary flex items-center justify-center cursor-pointer transition hover:bg-muted"
              >
                <Edit className="size-3" />
              </button>
              <button
                type="button"
                onClick={() => deleteButton(index)}
                className="w-7 h-7 rounded-lg border border-border text-[11px] text-muted-foreground hover:text-destructive flex items-center justify-center cursor-pointer transition hover:bg-muted"
              >
                <X className="size-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {editingIndex !== null ? (
        <div className="rounded-xl border border-border/80 bg-white p-4 shadow-sm space-y-3 animate-in zoom-in-95 duration-150">
          <FormField label="Button Label">
            <input
              type="text"
              maxLength={20}
              className="ipt"
              placeholder="e.g. Visit Shop"
              value={buttonText}
              onChange={(e) => setButtonText(e.target.value)}
            />
          </FormField>
          
          <FormField label="Button Action">
            <select
              className="ipt"
              value={actionType}
              onChange={(e) => setActionType(e.target.value as any)}
            >
              <option value="open_url">Open URL link</option>
              <option value="trigger_message">Trigger automation sequence step</option>
            </select>
          </FormField>

          {actionType === "open_url" && (
            <FormField label="Link URL">
              <input
                type="url"
                className="ipt"
                placeholder="https://shop.y/item"
                value={buttonUrl}
                onChange={(e) => setButtonUrl(e.target.value)}
              />
            </FormField>
          )}

          <div className="flex justify-end gap-2 pt-2 border-t border-border/45 mt-2 shrink-0">
            <button
              type="button"
              onClick={() => setEditingIndex(null)}
              className="px-3.5 py-1.5 rounded-lg border border-border text-xs font-semibold hover:bg-muted cursor-pointer transition"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={saveButton}
              className="px-3.5 py-1.5 rounded-lg bg-primary text-white text-xs font-semibold hover:bg-primary-dark cursor-pointer transition"
            >
              Save Button
            </button>
          </div>
        </div>
      ) : (
        buttons.length < 3 && (
          <button
            type="button"
            onClick={startAddButton}
            className="w-full py-3 rounded-xl border border-dashed border-border bg-white text-xs font-bold text-muted-foreground hover:text-foreground hover:bg-accent/40 cursor-pointer transition flex items-center justify-center gap-1.5"
          >
            <Plus className="size-3.5" /> Add Button
          </button>
        )
      )}
    </div>
  );
}

// EDITOR SHELL
function EditorShell({ message }: { message: string }) {
  return (
    <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-10 text-center text-sm text-muted-foreground">
      {message}
    </div>
  );
}

// EDITOR SECTION
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

export function InputStyles() {
  return (
    <style>{`.ipt { width:100%; min-height:44px; padding:0 14px; border:1px solid var(--border); border-radius:10px; font-size:14px; outline:none; background:var(--surface); }
.ipt:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(61,58,238,0.12); }`}</style>
  );
}

function InstagramMediaSelector({
  workspaceId,
  selectedId,
  onChange,
}: {
  workspaceId: string;
  selectedId: string;
  onChange: (id: string) => void;
}) {
  const [after, setAfter] = useState<string | undefined>(undefined);
  const [accumulatedMedia, setAccumulatedMedia] = useState<any[]>([]);
  const [filter, setFilter] = useState<"ALL" | "REEL" | "POST">("ALL");
  const { data, isLoading, error } = useInstagramMediaQuery(workspaceId, { limit: 12, after });

  useEffect(() => {
    if (data?.data) {
      setAccumulatedMedia((prev) => {
        const combined = [...prev, ...data.data];
        const unique = combined.filter(
          (item, idx, self) => self.findIndex((x) => x.id === item.id) === idx
        );
        return unique;
      });
    }
  }, [data]);

  const loadMore = () => {
    const nextCursor = data?.paging?.cursors?.after;
    if (nextCursor) {
      setAfter(nextCursor);
    }
  };

  const filteredMedia = accumulatedMedia.filter((media) => {
    if (filter === "ALL") return true;
    if (filter === "REEL") return media.media_type === "VIDEO";
    if (filter === "POST") return media.media_type === "IMAGE" || media.media_type === "CAROUSEL_ALBUM";
    return true;
  });

  if (isLoading && accumulatedMedia.length === 0) {
    return <div className="text-center py-6 text-sm text-muted-foreground animate-pulse">Loading posts & reels...</div>;
  }

  if (error) {
    return <div className="text-center py-6 text-sm text-destructive">Failed to load posts. Make sure your Instagram connection is active.</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3 border-b border-border/40 pb-3">
        <button
          type="button"
          onClick={() => onChange("")}
          className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition cursor-pointer ${
            selectedId === ""
              ? "border-primary bg-primary text-primary-foreground"
              : "border-border bg-card hover:bg-muted text-muted-foreground"
          }`}
        >
          ✨ Apply to all posts/reels
        </button>

        <div className="flex items-center gap-1 bg-muted p-1 rounded-lg border border-border/40 shrink-0">
          {(["ALL", "REEL", "POST"] as const).map((type) => (
            <button
              type="button"
              key={type}
              onClick={() => setFilter(type)}
              className={`px-3 py-1.5 rounded-md text-[11px] font-bold uppercase tracking-wider transition cursor-pointer select-none ${
                filter === type
                  ? "bg-card text-foreground shadow-sm font-extrabold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {type === "ALL" ? "All" : type === "REEL" ? "Reels" : "Posts"}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {filteredMedia.map((media) => {
          const isSelected = selectedId === media.id;
          const isVideo = media.media_type === "VIDEO";
          const isCarousel = media.media_type === "CAROUSEL_ALBUM";
          
          return (
            <button
              type="button"
              key={media.id}
              onClick={() => onChange(media.id)}
              className={`relative overflow-hidden rounded-xl border aspect-[4/5] text-left transition select-none flex flex-col group cursor-pointer ${
                isSelected
                  ? "border-primary ring-2 ring-primary/20 bg-accent/40"
                  : "border-border bg-card hover:border-primary/50"
              }`}
            >
              <div className="relative flex-1 bg-black overflow-hidden">
                <img
                  src={media.thumbnail_url || media.media_url}
                  alt={media.caption || "Instagram media"}
                  className="w-full h-full object-cover transition duration-300 group-hover:scale-105"
                  loading="lazy"
                />
                
                <span className="absolute top-2 left-2 text-[9px] font-bold uppercase px-2 py-0.5 rounded-md bg-black/60 text-white backdrop-blur-[2px]">
                  {isVideo ? "Reel" : isCarousel ? "Carousel" : "Post"}
                </span>

                {isSelected && (
                  <div className="absolute inset-0 bg-primary/10 border-4 border-primary rounded-xl flex items-center justify-center">
                    <span className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm shadow">✓</span>
                  </div>
                )}
              </div>

              <div className="p-2.5 h-[56px] shrink-0 border-t border-border bg-card">
                <p className="text-[11px] leading-tight text-foreground line-clamp-2">
                  {media.caption || "(No caption)"}
                </p>
              </div>
            </button>
          );
        })}

        {filteredMedia.length === 0 && (
          <div className="col-span-full py-12 text-center text-sm text-muted-foreground">
            No {filter === "REEL" ? "reels" : filter === "POST" ? "posts" : "items"} loaded. Click "Show More" below to fetch more.
          </div>
        )}
      </div>

      {data?.paging?.cursors?.after && (
        <div className="text-center pt-2">
          <button
            type="button"
            onClick={loadMore}
            className="h-9 px-4 rounded-lg border border-border text-xs font-semibold hover:bg-muted transition cursor-pointer"
          >
            Show More
          </button>
        </div>
      )}
    </div>
  );
}
