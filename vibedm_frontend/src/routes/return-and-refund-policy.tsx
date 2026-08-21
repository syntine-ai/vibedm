import { createFileRoute } from "@tanstack/react-router";
import { Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

export const Route = createFileRoute("/return-and-refund-policy")({
  head: () => ({ meta: [{ title: "Return and Refund Policy - Vibe DM" }] }),
  component: ReturnAndRefundPolicy,
});

function ReturnAndRefundPolicy() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="px-10 py-12 max-w-4xl mx-auto">
        <div className="mb-8">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors mb-6"
          >
            <ArrowLeft className="size-4" /> Back to Home
          </Link>
          <h1 className="text-4xl font-extrabold tracking-tight">Return and Refund Policy</h1>
          <p className="text-muted-foreground mt-2">Effective Date: May 27, 2026</p>
        </div>

        <div className="prose prose-sm sm:prose-base dark:prose-invert max-w-none space-y-6 text-foreground/90">
          <p>
            At Vibe DM (<strong><a href="https://vibedm.syntine.com">https://vibedm.syntine.com</a></strong>), we value
            your satisfaction and strive to provide the best experience possible. Below are the terms
            for refunds and cancellations for our Free, Monthly, and Annual plans.
          </p>

          <h3 className="text-2xl font-bold mt-8 mb-4">1. Free Plan</h3>
          <ul className="list-disc pl-6 space-y-2">
            <li>
              The Free plan does not require payment and can be canceled or discontinued at any time
              without any obligation.
            </li>
            <li>Users on the Free plan can upgrade to a paid plan at any time.</li>
          </ul>

          <h3 className="text-2xl font-bold mt-8 mb-4">2. Monthly Plan</h3>
          <ul className="list-disc pl-6 space-y-2">
            <li>You can cancel your Monthly Plan subscription before 3 days of your payment date.</li>
            <li>
              <strong>Refund Policy:</strong> No refunds are provided for the current billing cycle.
              Once canceled, your subscription will not renew for the next billing cycle.
            </li>
            <li>
              Your access to premium features will remain active until the end of the current billing
              cycle.
            </li>
          </ul>

          <h3 className="text-2xl font-bold mt-8 mb-4">3. Annual Plan</h3>
          <ul className="list-disc pl-6 space-y-2">
            <li>You may cancel your Annual Plan subscription at any time.</li>
            <li>
              <strong>Refund Policy:</strong> No refunds are provided for the current billing cycle.
              Once canceled, your subscription will not renew for the next billing cycle.
            </li>
            <li>
              Your access to premium features will remain active until the end of the current billing
              cycle.
            </li>
          </ul>

          <h3 className="text-2xl font-bold mt-8 mb-4">4. How to Cancel Your Subscription</h3>
          <p>
            To cancel your subscription, contact the founder at <strong>WA: [Your WhatsApp Number]</strong> or email <strong>support@vibedm.syntine.com</strong>.
          </p>
          <p>
            Once canceled, you will receive an email confirmation. For assistance, contact our
            support team at <strong>support@vibedm.syntine.com</strong>.
          </p>

          <h3 className="text-2xl font-bold mt-8 mb-4">5. Abuse of Refunds</h3>
          <p>
            We reserve the right to deny refunds to users who repeatedly subscribe and cancel to
            abuse the policy. Such accounts may also be subject to suspension.
          </p>

          <h3 className="text-2xl font-bold mt-8 mb-4">6. Changes to This Policy</h3>
          <p>
            We may update this policy from time to time. Any changes will be posted on this page,
            and significant updates will be communicated via email.
          </p>
          <p>
            If you have any questions or concerns, feel free to reach out to our support team at <strong>hello@syntine.com</strong>.
          </p>
          <p className="mt-8 font-semibold">Thank you for using Vibe DM!</p>
        </div>
      </div>
    </div>
  );
}
