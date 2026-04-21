import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Brain, Mic, Video, ChartBar, Code, Users, ArrowRight,
  Zap, Shield
} from "lucide-react";

const features = [
  { icon: Brain, title: "AI-Powered Questions", desc: "Adaptive questions that adjust to your performance in real time." },
  { icon: Mic, title: "Voice Mode", desc: "Practice speaking under pressure with live speech-to-text transcription." },
  { icon: Video, title: "Video Recording", desc: "Review your body language and presentation alongside AI feedback." },
  { icon: ChartBar, title: "Detailed Analytics", desc: "Score breakdown across technical depth, clarity, and confidence." },
  { icon: Code, title: "Multi-Domain", desc: "DSA, System Design, HR, Behavioral, Frontend, Backend, ML and more." },
  { icon: Shield, title: "Real Evaluation", desc: "Honest scoring with strengths, gaps, and actionable improvements." },
];

const domains = [
  { name: "Data Structures & Algorithms", color: "bg-blue-500/20 text-blue-400" },
  { name: "System Design", color: "bg-purple-500/20 text-purple-400" },
  { name: "Behavioral", color: "bg-green-500/20 text-green-400" },
  { name: "HR Interview", color: "bg-yellow-500/20 text-yellow-400" },
  { name: "Frontend", color: "bg-pink-500/20 text-pink-400" },
  { name: "Backend", color: "bg-orange-500/20 text-orange-400" },
  { name: "Machine Learning", color: "bg-cyan-500/20 text-cyan-400" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-7 h-7 text-primary" />
            <span className="text-xl font-bold">InterviewAI</span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
            <a href="#features" className="hover:text-foreground transition-colors">Features</a>
            <a href="#domains" className="hover:text-foreground transition-colors">Domains</a>
            <a href="#how-it-works" className="hover:text-foreground transition-colors">How It Works</a>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" asChild>
              <Link href="/auth/login">Sign In</Link>
            </Button>
            <Button asChild>
              <Link href="/auth/register">Get Started <ArrowRight className="w-4 h-4" /></Link>
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-12 px-6">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <Badge variant="outline" className="gap-1.5 py-1 px-3">
            <Zap className="w-3.5 h-3.5 text-yellow-400" />
            Powered by Claude AI
          </Badge>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight">
            Ace Your Next
            <span className="text-primary"> Technical</span>
            <br />Interview
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Practice with an AI interviewer that adapts to your skill level, records your sessions,
            and gives you honest, actionable feedback across every domain.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
            <Button size="lg" className="h-12 px-8 text-base" asChild>
              <Link href="/auth/register">
                Start Practicing Free <ArrowRight className="w-5 h-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" className="h-12 px-8 text-base" asChild>
              <Link href="/auth/login">View Demo</Link>
            </Button>
          </div>
        </div>

        {/* Mock interview preview */}
        <div className="max-w-4xl mx-auto mt-16 rounded-2xl border border-border/60 bg-card/50 backdrop-blur overflow-hidden shadow-2xl">
          <div className="flex items-center gap-1.5 px-4 py-3 bg-muted/30 border-b border-border/40">
            <span className="w-3 h-3 rounded-full bg-red-500/70" />
            <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
            <span className="w-3 h-3 rounded-full bg-green-500/70" />
            <span className="ml-3 text-xs text-muted-foreground">Interview Room — DSA Medium</span>
          </div>
          <div className="p-6 space-y-4 min-h-[200px]">
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                <Brain className="w-4 h-4 text-primary" />
              </div>
              <div className="bg-secondary rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm max-w-lg">
                Explain the difference between BFS and DFS. When would you use each approach, and what are their time/space complexities?
              </div>
            </div>
            <div className="flex gap-3 flex-row-reverse">
              <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                <Users className="w-4 h-4" />
              </div>
              <div className="bg-primary rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm text-primary-foreground max-w-lg">
                BFS uses a queue and explores level by level, while DFS uses a stack and goes deep first. BFS is O(V+E) time and O(W) space where W is max width, DFS is O(V+E) time and O(H) space...
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground pl-11">
              <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
              AI is evaluating your answer...
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="pt-16 pb-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Everything You Need to Succeed</h2>
            <p className="text-muted-foreground text-lg max-w-xl mx-auto">
              A complete interview prep platform built for serious candidates.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <div key={f.title} className="rounded-xl border border-border p-6 bg-card/50 hover:bg-card transition-colors">
                <f.icon className="w-8 h-8 text-primary mb-4" />
                <h3 className="font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Domains */}
      <section id="domains" className="py-24 px-6 bg-muted/10">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-4">Interview in Any Domain</h2>
          <p className="text-muted-foreground text-lg mb-12">
            From DSA to system design to behavioral — we've got you covered.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            {domains.map((d) => (
              <span key={d.name} className={`px-4 py-2 rounded-full text-sm font-medium ${d.color}`}>
                {d.name}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section id="how-it-works" className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">How It Works</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: "01", title: "Choose Your Domain", desc: "Select the interview type and difficulty level that matches your target role." },
              { step: "02", title: "Start Interviewing", desc: "Chat or use voice mode. The AI adapts questions based on your answers." },
              { step: "03", title: "Get Detailed Feedback", desc: "Receive scores, identify gaps, and watch your recorded session." },
            ].map((item) => (
              <div key={item.step} className="text-center space-y-3">
                <div className="text-5xl font-black text-primary/20">{item.step}</div>
                <h3 className="font-semibold text-lg">{item.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 bg-primary/5 border-t border-border/40">
        <div className="max-w-2xl mx-auto text-center space-y-6">
          <h2 className="text-4xl font-bold">Ready to Ace Your Interview?</h2>
          <p className="text-muted-foreground text-lg">
            Join thousands of developers who prep smarter with InterviewAI.
          </p>
          <Button size="lg" className="h-12 px-10 text-base" asChild>
            <Link href="/auth/register">Start for Free <ArrowRight className="w-5 h-5" /></Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 py-8 px-6 text-center text-sm text-muted-foreground">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Brain className="w-4 h-4 text-primary" />
          <span className="font-medium text-foreground">InterviewAI</span>
        </div>
        <p>Built with Claude AI · LangGraph · FastAPI · Next.js</p>
      </footer>
    </div>
  );
}
