import { user } from "@/lib/mock-data";

export function ProBanner() {
  if (user.plan === "pro") return null;
  return (
    <div
      className="rounded-2xl px-6 py-4 mb-6 flex items-center justify-between gap-4 text-white"
      style={{
        background:
          "linear-gradient(135deg, var(--banner-from), var(--banner-to))",
      }}
    >
      <div>
        <div className="text-[18px] font-bold leading-tight">
          Unlock <span className="font-extrabold text-white/90">Pro Power!</span>
        </div>
        <div className="text-[13px] text-white/80 mt-0.5">
          Get unlimited automations, contacts &amp; advanced analytics.
        </div>
      </div>
      <button className="shrink-0 bg-white text-primary font-semibold text-[13px] px-5 py-2.5 rounded-full hover:bg-white/90 transition">
        Upgrade to Pro
      </button>
    </div>
  );
}
