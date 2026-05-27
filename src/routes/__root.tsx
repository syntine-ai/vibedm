import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  HeadContent,
  Link,
  Outlet,
  Scripts,
  createRootRouteWithContext,
  useNavigate,
  useRouter,
  useRouterState,
} from "@tanstack/react-router";
import { useEffect } from "react";

import appCss from "../styles.css?url";
import { AppSidebar } from "@/components/AppSidebar";
import { useAuthMeQuery, useSessionQuery } from "@/lib/api/hooks";
import { supabase } from "@/integrations/supabase/client";

const AUTH_ROUTES = ["/login", "/signup", "/forgot-password", "/auth/instagram/callback"];

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">Page not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The page you're looking for doesn't exist.
        </p>
        <div className="mt-6">
          <Link
            to="/dashboard"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Go to dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight">Something went wrong</h1>
        <p className="mt-2 text-sm text-muted-foreground">{error.message}</p>
        <button
          onClick={() => {
            router.invalidate();
            reset();
          }}
          className="mt-6 inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          Try again
        </button>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "DMFlow — Instagram DM Automation" },
      {
        name: "description",
        content: "Automate Instagram DMs triggered by comments, replies, and mentions.",
      },
      { property: "og:title", content: "DMFlow — Instagram DM Automation" },
      { name: "twitter:title", content: "DMFlow — Instagram DM Automation" },
      {
        property: "og:description",
        content: "Automate Instagram DMs triggered by comments, replies, and mentions.",
      },
      {
        name: "twitter:description",
        content: "Automate Instagram DMs triggered by comments, replies, and mentions.",
      },
      {
        property: "og:image",
        content:
          "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/d06a00aa-6992-4f85-9769-15982fe16605/id-preview-0e5c6911--b074ac34-e5e0-4137-beaf-70caf0891b83.lovable.app-1779731369660.png",
      },
      {
        name: "twitter:image",
        content:
          "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/d06a00aa-6992-4f85-9769-15982fe16605/id-preview-0e5c6911--b074ac34-e5e0-4137-beaf-70caf0891b83.lovable.app-1779731369660.png",
      },
      { name: "twitter:card", content: "summary_large_image" },
      { property: "og:type", content: "website" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
      },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <QueryClientProvider client={queryClient}>
      <AppFrame />
    </QueryClientProvider>
  );
}

function AppFrame() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const isAuth = AUTH_ROUTES.some((p) => pathname.startsWith(p));

  if (isAuth) {
    return <Outlet />;
  }

  return <ProtectedAppFrame />;
}

function ProtectedAppFrame() {
  const navigate = useNavigate();
  const sessionQuery = useSessionQuery();
  const meQuery = useAuthMeQuery(Boolean(sessionQuery.data));

  useEffect(() => {
    if (sessionQuery.isSuccess && !sessionQuery.data) {
      navigate({ to: "/login", replace: true });
    }
  }, [navigate, sessionQuery.data, sessionQuery.isSuccess]);

  if (sessionQuery.isLoading || (sessionQuery.data && meQuery.isLoading)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-sm text-muted-foreground">
        Loading workspace...
      </div>
    );
  }

  if (meQuery.isError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="max-w-md w-full text-center p-8 bg-card rounded-2xl shadow-lg border border-destructive/20">
          <div className="w-12 h-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center mx-auto mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-foreground mb-2">Backend Connection Failed</h2>
          <p className="text-sm text-muted-foreground mb-6">
            We couldn't connect to the backend server. Please ensure the backend server is running (usually at <code className="bg-muted px-1.5 py-0.5 rounded text-xs">localhost:8000</code>).
          </p>
          <div className="flex flex-col gap-2">
            <button
              onClick={() => meQuery.refetch()}
              className="w-full h-11 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition text-sm"
            >
              Retry Connection
            </button>
            <button
              onClick={async () => {
                await supabase.auth.signOut();
                window.location.href = "/login";
              }}
              className="w-full h-11 rounded-lg border border-border bg-card font-medium text-sm hover:bg-muted transition text-foreground"
            >
              Return to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!sessionQuery.data) {
    return null;
  }

  return (
    <div className="flex min-h-screen bg-background">
      <AppSidebar />
      <main className="flex-1 min-w-0">
        <div className="px-10 py-8 max-w-[1400px] mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
