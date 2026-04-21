"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Brain, ArrowLeft, CheckCircle, AlertTriangle, Lightbulb,
  Play, TrendingUp, Star, Target
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { api } from "@/lib/api";
import { scoreToGrade, domainLabel } from "@/lib/utils";
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from "recharts";
import { cn } from "@/lib/utils";

const ScoreRing = ({ score }: { score: number }) => {
  const { label, color } = scoreToGrade(score);
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-36 h-36">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="8" className="text-muted/30" />
        <circle
          cx="50" cy="50" r="45" fill="none" strokeWidth="8"
          stroke="hsl(var(--primary))"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-black">{score}</span>
        <span className={`text-xs font-medium ${color}`}>{label}</span>
      </div>
    </div>
  );
};

export default function ResultsPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.sessions.get(sessionId)
      .then(setSession)
      .catch(() => router.push("/dashboard"))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Brain className="w-8 h-8 text-primary animate-pulse" />
    </div>
  );

  if (!session || session.status !== "completed") return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <h2 className="text-xl font-semibold">Results not available yet</h2>
        <Button onClick={() => router.push("/dashboard")}>Back to Dashboard</Button>
      </div>
    </div>
  );

  const ev = session.evaluation || {};
  const score = ev.score || 0;
  const { label, color } = scoreToGrade(score);

  const radarData = [
    { subject: "Technical", value: ev.technical_score || score },
    { subject: "Communication", value: ev.communication_score || score * 0.9 },
    { subject: "Behavioral", value: ev.behavioral_score || score * 0.85 },
    { subject: "Problem Solving", value: score * 0.95 },
    { subject: "Clarity", value: ev.communication_score || score * 0.88 },
  ];

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Header */}
      <header className="border-b border-border/40 sticky top-0 bg-background/80 backdrop-blur z-40">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push("/dashboard")}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            <span className="font-semibold">Interview Results</span>
          </div>
          <div className="ml-auto flex gap-2">
            <Badge variant="outline">{domainLabel(session.domain)}</Badge>
            <Badge variant="outline">{session.difficulty}</Badge>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10">
        {/* Score Hero */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
          <Card className="bg-gradient-to-br from-primary/5 to-background border-primary/20">
            <CardContent className="p-8">
              <div className="flex flex-col md:flex-row items-center gap-8">
                <ScoreRing score={score} />
                <div className="flex-1 text-center md:text-left">
                  <h1 className="text-3xl font-bold mb-2">
                    {score >= 80 ? "Excellent Performance!" : score >= 65 ? "Good Job!" : score >= 50 ? "Room to Grow" : "Keep Practicing"}
                  </h1>
                  <p className="text-muted-foreground leading-relaxed max-w-lg">
                    {ev.overall_feedback?.split("\n")[0] || "Your interview has been evaluated. See below for detailed feedback."}
                  </p>
                  <div className="flex flex-wrap gap-2 mt-4 justify-center md:justify-start">
                    {ev.hire_recommendation && (
                      <Badge
                        className={cn(
                          "text-sm py-1 px-3",
                          ev.hire_recommendation === "strong_yes" ? "bg-green-500/20 text-green-400" :
                          ev.hire_recommendation === "yes" ? "bg-blue-500/20 text-blue-400" :
                          ev.hire_recommendation === "maybe" ? "bg-yellow-500/20 text-yellow-400" :
                          "bg-red-500/20 text-red-400"
                        )}
                      >
                        {ev.hire_recommendation === "strong_yes" ? "Strong Hire" :
                         ev.hire_recommendation === "yes" ? "Hire" :
                         ev.hire_recommendation === "maybe" ? "Maybe" : "No Hire"}
                      </Badge>
                    )}
                    <Badge variant="outline">{label}</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Radar Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Target className="w-4 h-4 text-primary" /> Performance Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" className="text-xs" />
                  <Radar name="Score" dataKey="value" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.2} />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Score breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-primary" /> Score Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { label: "Technical", value: ev.technical_score || score },
                { label: "Communication", value: ev.communication_score || Math.round(score * 0.9) },
                { label: "Behavioral / Culture", value: ev.behavioral_score || Math.round(score * 0.85) },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-sm mb-1.5">
                    <span className="text-muted-foreground">{item.label}</span>
                    <span className="font-medium">{item.value}/100</span>
                  </div>
                  <Progress value={item.value} className="h-2" />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Strengths / Weaknesses / Improvements */}
        <div className="grid md:grid-cols-3 gap-6 mb-6">
          <Card className="border-green-500/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 text-green-400">
                <CheckCircle className="w-4 h-4" /> Strengths
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {(ev.strengths || []).map((s: string, i: number) => (
                  <li key={i} className="text-sm flex gap-2">
                    <span className="text-green-400 mt-0.5">✓</span> {s}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card className="border-red-500/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 text-red-400">
                <AlertTriangle className="w-4 h-4" /> Areas to Improve
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {(ev.weaknesses || []).map((w: string, i: number) => (
                  <li key={i} className="text-sm flex gap-2">
                    <span className="text-red-400 mt-0.5">!</span> {w}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card className="border-blue-500/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 text-blue-400">
                <Lightbulb className="w-4 h-4" /> Action Items
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {(ev.improvements || []).map((imp: string, i: number) => (
                  <li key={i} className="text-sm flex gap-2">
                    <span className="text-blue-400 mt-0.5">→</span> {imp}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Feedback */}
        {ev.overall_feedback && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Brain className="w-4 h-4 text-primary" /> Detailed Feedback
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                {ev.overall_feedback}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Recording playback */}
        {session.recording_url && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Play className="w-4 h-4 text-primary" /> Session Recording
              </CardTitle>
            </CardHeader>
            <CardContent>
              <video
                src={session.recording_url}
                controls
                className="w-full rounded-lg bg-black"
              />
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <div className="flex gap-3 mt-8 justify-center">
          <Button onClick={() => router.push("/dashboard")} variant="outline">
            Back to Dashboard
          </Button>
          <Button onClick={() => router.push("/interview/setup")}>
            Practice Again
          </Button>
        </div>
      </main>
    </div>
  );
}
