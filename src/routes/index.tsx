import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useSessionQuery } from "@/lib/api/hooks";
import { Button } from "@/components/ui/button";
import { ArrowRight, MessageSquare, Zap, Shield, Heart } from "lucide-react";
import logo from "@/logo.png";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [{ title: "Vibe DM - Smart Instagram Automation" }] }),
  component: IndexComponent,
});

function IndexComponent() {
  const { data: session, isLoading } = useSessionQuery();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background flex flex-col font-sans selection:bg-primary/30">
      {/* Navbar */}
      <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 flex h-16 items-center justify-between">
          <div className="flex items-center gap-2.5">
            <img src={logo} alt="Vibe DM Logo" className="size-8 object-contain" />
            <span className="font-bold text-xl tracking-tight">Vibe DM</span>
          </div>
          <nav className="flex items-center gap-4">
            {!isLoading && (
              <>
                {session ? (
                  <Button onClick={() => navigate({ to: "/dashboard" })} variant="default">
                    Go to Dashboard
                  </Button>
                ) : (
                  <>
                    <Button onClick={() => navigate({ to: "/login" })} variant="ghost">
                      Log in
                    </Button>
                    <Button onClick={() => navigate({ to: "/signup" })} variant="default">
                      Sign up
                    </Button>
                  </>
                )}
              </>
            )}
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col">
        <section className="relative w-full py-24 md:py-32 lg:py-48 overflow-hidden">
          {/* Background Gradient */}
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/20 via-background to-background"></div>
          
          <div className="container mx-auto px-4 md:px-6 text-center space-y-8">
            <div className="inline-block rounded-full bg-muted px-3 py-1 text-sm text-muted-foreground ring-1 ring-inset ring-border/50 mb-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
              Welcome to the future of Instagram DMs ✨
            </div>
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold tracking-tighter text-foreground max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-6 duration-700 delay-100">
              Automate your <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-500">Instagram DMs</span> like magic.
            </h1>
            <p className="mx-auto max-w-2xl text-lg md:text-xl text-muted-foreground animate-in fade-in slide-in-from-bottom-6 duration-700 delay-200">
              Vibe DM helps you connect with your audience instantly. Set up automated replies, manage conversations, and grow your business on autopilot.
            </p>
            <div className="flex flex-col sm:flex-row justify-center items-center gap-4 pt-4 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-300">
              <Button size="lg" className="h-12 px-8 text-base group" onClick={() => navigate({ to: session ? "/dashboard" : "/signup" })}>
                {session ? "Enter Dashboard" : "Get Started for Free"}
                <ArrowRight className="ml-2 size-4 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button size="lg" variant="outline" className="h-12 px-8 text-base bg-background/50 backdrop-blur-sm">
                Learn More
              </Button>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-24 bg-muted/30 border-y border-border/50">
          <div className="container mx-auto px-4 md:px-6">
            <div className="grid md:grid-cols-3 gap-8 md:gap-12 max-w-5xl mx-auto">
              <div className="flex flex-col items-center text-center space-y-4 p-6 rounded-2xl bg-background border border-border/50 shadow-sm hover:shadow-md transition-shadow">
                <div className="p-3 rounded-full bg-primary/10 text-primary">
                  <Zap className="size-6" />
                </div>
                <h3 className="text-xl font-bold">Lightning Fast</h3>
                <p className="text-muted-foreground">Respond to your followers instantly, 24/7. Never miss a potential lead again.</p>
              </div>
              <div className="flex flex-col items-center text-center space-y-4 p-6 rounded-2xl bg-background border border-border/50 shadow-sm hover:shadow-md transition-shadow">
                <div className="p-3 rounded-full bg-primary/10 text-primary">
                  <MessageSquare className="size-6" />
                </div>
                <h3 className="text-xl font-bold">Smart Replies</h3>
                <p className="text-muted-foreground">Set up intelligent flows that understand context and guide users through your funnel.</p>
              </div>
              <div className="flex flex-col items-center text-center space-y-4 p-6 rounded-2xl bg-background border border-border/50 shadow-sm hover:shadow-md transition-shadow">
                <div className="p-3 rounded-full bg-primary/10 text-primary">
                  <Shield className="size-6" />
                </div>
                <h3 className="text-xl font-bold">Safe & Secure</h3>
                <p className="text-muted-foreground">Official Instagram API integration guarantees your account stays safe and compliant.</p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer with Legal Links */}
      <footer className="w-full py-12 bg-background border-t border-border/40">
        <div className="container mx-auto px-4 md:px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2.5 text-muted-foreground">
              <img src={logo} alt="Vibe DM Logo" className="size-7 object-contain" />
              <span className="font-semibold text-foreground">Vibe DM</span>
              <span className="text-sm">© {new Date().getFullYear()} Syntine Labs. All rights reserved.</span>
            </div>
            
            <nav className="flex flex-wrap justify-center gap-x-8 gap-y-4 text-sm font-medium text-muted-foreground">
              <Link to="/terms" className="hover:text-foreground transition-colors">
                Terms and Conditions
              </Link>
              <Link to="/privacy" className="hover:text-foreground transition-colors">
                Privacy Policy
              </Link>
              <Link to="/return-and-refund-policy" className="hover:text-foreground transition-colors">
                Return & Refund Policy
              </Link>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}
