"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Brain, Plus, Clock, CheckCircle, XCircle, PlayCircle,
  TrendingUp, Target, LogOut, ChevronRight, Home, Shield
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useAuthStore } from "@/stores/authStore";
import { api } from "@/lib/api";
import { scoreToGrade, domainLabel, formatDuration } from "@/lib/utils";

const statusConfig = {
  pending: { icon: Clock, color: "text-yellow-400", label: "Pending" },
  in_progress: { icon: PlayCircle, color: "text-blue-400", label: "In Progress" },
  completed: { icon: CheckCircle, color: "text-green-400", label: "Completed" },
  cancelled: { icon: XCircle, color: "text-red-400", label: "Cancelled" },
} as const;

export default function DashboardPage() {
  const { user, logout, hydrate } = useAuthStore();
  const router = useRouter();
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    hydrate().then(() => {
      if (!useAuthStore.getState().user) router.push("/auth/login");
    });
    api.sessions.list().then(setSessions).catch(console.error).finally(() => setLoading(false));
  }, []);

  const completed = sessions.filter((s) => s.status === "completed");
  const avgScore = completed.length
    ? Math.round(completed.reduce((acc, s) => acc + (s.evaluation?.score || 0), 0) / completed.length)
    : 0;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/40 bg-background/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-primary" />
            <span className="font-bold text-lg">InterviewAI</span>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/">
              <Button variant="ghost" size="sm" className="gap-1.5">
                <Home className="w-4 h-4" />
                Home
              </Button>
            </Link>
            {user?.is_admin && (
              <Link href="/admin">
                <Button variant="ghost" size="sm" className="gap-1.5">
                  <Shield className="w-4 h-4" />
                  Admin
                </Button>
              </Link>
            )}
            <span className="text-sm text-muted-foreground hidden sm:inline ml-1">
              {user?.name}
            </span>
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => {
                logout();
                router.push("/");
              }}
            >
              <LogOut className="w-4 h-4" />
              Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        {/* Welcome */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold mb-1">Welcome back, {user?.name?.split(" ")[0]} 👋</h1>
          <p className="text-muted-foreground">Ready to practice? Start a new interview below.</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          {[
            { label: "Total Sessions", value: sessions.length, icon: Target },
            { label: "Completed", value: completed.length, icon: CheckCircle },
            { label: "Avg Score", value: avgScore ? `${avgScore}/100` : "—", icon: TrendingUp },
            { label: "Domains Tried", value: new Set(sessions.map((s) => s.domain)).size, icon: Brain },
          ].map((stat) => (
            <Card key={stat.label} className="bg-card/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                  <stat.icon className="w-5 h-5 text-primary" />
                </div>
                <div className="text-2xl font-bold">{stat.value}</div>
                <div className="text-xs text-muted-foreground mt-1">{stat.label}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Start New Interview */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Recent Interviews</h2>
          <Button asChild>
            <Link href="/interview/setup">
              <Plus className="w-4 h-4" /> New Interview
            </Link>
          </Button>
        </div>

        {/* Sessions List */}
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-24 rounded-xl bg-muted/40 animate-pulse" />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <Card className="text-center py-16">
            <CardContent>
              <Brain className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="font-semibold mb-2">No interviews yet</h3>
              <p className="text-sm text-muted-foreground mb-6">Start your first practice interview to see results here.</p>
              <Button asChild>
                <Link href="/interview/setup"><Plus className="w-4 h-4" /> Start Interview</Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {sessions.map((session, i) => {
              const status = statusConfig[session.status as keyof typeof statusConfig];
              const score = session.evaluation?.score;
              const grade = score ? scoreToGrade(score) : null;
              return (
                <motion.div
                  key={session.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className="hover:bg-card/80 transition-colors cursor-pointer" onClick={() => router.push(`/results/${session.id}`)}>
                    <CardContent className="py-4 px-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                            <Brain className="w-5 h-5 text-primary" />
                          </div>
                          <div>
                            <div className="font-medium">{domainLabel(session.domain)}</div>
                            <div className="text-sm text-muted-foreground flex items-center gap-2 mt-0.5">
                              <Badge variant="outline" className="text-xs py-0">{session.difficulty}</Badge>
                              <status.icon className={`w-3.5 h-3.5 ${status.color}`} />
                              <span className={`text-xs ${status.color}`}>{status.label}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-6">
                          {score && (
                            <div className="text-right">
                              <div className={`font-bold text-lg ${grade?.color}`}>{score}</div>
                              <div className="text-xs text-muted-foreground">{grade?.label}</div>
                            </div>
                          )}
                          <ChevronRight className="w-4 h-4 text-muted-foreground" />
                        </div>
                      </div>
                      {score && (
                        <div className="mt-3 ml-14">
                          <Progress value={score} className="h-1.5" />
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
