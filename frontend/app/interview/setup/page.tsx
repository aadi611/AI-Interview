"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Brain, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/useToast";

const difficulties = [
  { value: "easy", label: "Easy", desc: "Warm up with fundamental concepts", color: "border-green-500" },
  { value: "medium", label: "Medium", desc: "Intermediate — suitable for most roles", color: "border-yellow-500" },
  { value: "hard", label: "Hard", desc: "Senior/Staff level depth", color: "border-red-500" },
] as const;

export default function SetupPage() {
  const router = useRouter();
  const [domains, setDomains] = useState<any[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<string>("medium");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.sessions.domains().then(setDomains).catch(console.error);
  }, []);

  const handleStart = async () => {
    if (!selectedDomain) { toast({ variant: "destructive", title: "Select a domain" }); return; }
    setLoading(true);
    try {
      const session = await api.sessions.create({ domain: selectedDomain, difficulty, mode: "hybrid" });
      router.push(`/interview/${session.id}`);
    } catch (err: any) {
      toast({ variant: "destructive", title: "Failed to create session", description: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-2 mb-10">
          <Brain className="w-6 h-6 text-primary" />
          <span className="font-bold text-lg">New Interview</span>
        </div>

        {/* Domain Selection */}
        <section className="mb-10">
          <h2 className="text-xl font-semibold mb-4">Choose Domain</h2>
          <div className="grid sm:grid-cols-2 gap-3">
            {domains.map((d) => (
              <motion.div key={d.name} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
                <Card
                  className={cn(
                    "cursor-pointer border-2 transition-all",
                    selectedDomain === d.name
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-primary/50"
                  )}
                  onClick={() => setSelectedDomain(d.name)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-medium">{d.display_name}</div>
                        <div className="text-sm text-muted-foreground mt-0.5">{d.description}</div>
                      </div>
                      {selectedDomain === d.name && (
                        <span className="w-5 h-5 rounded-full bg-primary flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="w-2 h-2 bg-white rounded-full" />
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Difficulty */}
        <section className="mb-10">
          <h2 className="text-xl font-semibold mb-4">Difficulty Level</h2>
          <div className="grid grid-cols-3 gap-3">
            {difficulties.map((d) => (
              <Card
                key={d.value}
                className={cn(
                  "cursor-pointer border-2 transition-all",
                  difficulty === d.value ? `${d.color} bg-primary/5` : "border-border hover:border-primary/40"
                )}
                onClick={() => setDifficulty(d.value)}
              >
                <CardContent className="p-4 text-center">
                  <div className="font-semibold">{d.label}</div>
                  <div className="text-xs text-muted-foreground mt-1">{d.desc}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <Button
          onClick={handleStart}
          disabled={!selectedDomain || loading}
          size="lg"
          className="w-full h-12 text-base"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (
            <>Start Interview <ArrowRight className="w-5 h-5" /></>
          )}
        </Button>
      </div>
    </div>
  );
}
