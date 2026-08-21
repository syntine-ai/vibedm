# Billing behavior — Brief

Goal: Provide per-workspace subscription management with a Free default plan and three paid INR plans (monthly + yearly 20% off).

Plans
- **Free:** ₹0 — basic features (no workspace-count shown).
- **Pro:** ₹99 / month.
- **Business:** ₹299 / month.
- **Enterprise:** ₹399 / month.
- Display: show monthly price by default; when Yearly selected, show yearly total = monthly * 12 * 0.8 and per-month equivalent; show “Save 20%” badge for yearly.

Billing cycle UI
- Monthly / Yearly toggle (default: Monthly). Toggle updates displayed prices immediately.

Per-workspace billing
- Each workspace has its own active plan mapping.
- New workspace defaults to Free and must be upgraded separately.
- Billing UI includes a workspace selector (dropdown) to choose which workspace you’re managing.
- Selecting a workspace shows that workspace’s current plan and allows changing it.

Plan cards
- Title, small badge (e.g., “Popular”), price, short feature bullets (no “X workspaces” lines), primary CTA (Free → “Start free”, Paid → “Subscribe”), secondary quick-select (check icon) to mark as workspace’s plan.
- Visual state for currently active plan for selected workspace.

CTAs / flow
- Free: instantly activate locally (UI feedback).
- Paid: open checkout flow (placeholder until integrated with Stripe/backend). Show chosen billingCycle and final price in checkout.
- After successful checkout (backend/webhook), update workspace plan mapping and invoices.

Invoice history
- Show invoices (per workspace) below plans; “No invoices found” when none.

State & persistence
- Client state shows selection; backend persists workspace -> plan, billing cycle, and customer/subscription info.
- Expose API endpoints: list plans, create checkout session (planId, workspaceId, cycle), webhook for payment status, fetch invoices for workspace.

Pricing calc
- yearlyTotal = monthly * 12 * 0.8; show cents/paise rounded to two decimals; show per-month equivalent when yearly chosen.

Accessibility & responsiveness
- keyboard-focusable toggle and cards, ARIA labels for cycle and workspace selector, cards stack on small screens.

Telemetry & UX
- record events: view billing, select workspace, open checkout, checkout success/fail, plan changed.

Developer notes / current app
- UI is implemented with INR prices and per-workspace mapping; plan descriptions were updated to remove workspace-count bullets. Replace placeholder alerts with real checkout integration and persist mapping server-side.

Next options
- Implement Stripe Checkout wiring and backend endpoints.
- Extract the plan UI into reusable components and add unit tests.
- Improve accessibility & responsive styling and add visual badges showing the current workspace plan.

