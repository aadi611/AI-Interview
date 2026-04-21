"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Brain, Shield, Users, ClipboardList, Video, BarChart3,
  Home, LogOut, Trash2, Download, ArrowUpCircle, ArrowDownCircle, Loader2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/stores/authStore";
import { api } from "@/lib/api";
import { toast } from "@/hooks/useToast";
import { domainLabel } from "@/lib/utils";

type Tab = "stats" | "users" | "sessions" | "recordings";

export default function AdminPage() {
  const { user, logout, hydrate } = useAuthStore();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("stats");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    hydrate().then(() => {
      const u = useAuthStore.getState().user;
      if (!u) {
        router.push("/auth/login");
      } else if (!u.is_admin) {
        router.push("/dashboard");
      } else {
        setReady(true);
      }
    });
  }, []);

  if (!ready) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-6 h-6 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/40 bg-background/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-primary" />
            <span className="font-bold text-lg">Admin Console</span>
            <Badge variant="outline" className="ml-2">{user?.email}</Badge>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/">
              <Button variant="ghost" size="sm" className="gap-1.5">
                <Home className="w-4 h-4" /> Home
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button variant="ghost" size="sm" className="gap-1.5">
                <Brain className="w-4 h-4" /> Dashboard
              </Button>
            </Link>
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => { logout(); router.push("/"); }}
            >
              <LogOut className="w-4 h-4" /> Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-border">
          {([
            ["stats", "Overview", BarChart3],
            ["users", "Users", Users],
            ["sessions", "Sessions", ClipboardList],
            ["recordings", "Recordings", Video],
          ] as const).map(([key, label, Icon]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 -mb-[1px] transition ${
                tab === key
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <Icon className="w-4 h-4" /> {label}
            </button>
          ))}
        </div>

        {tab === "stats" && <StatsTab />}
        {tab === "users" && <UsersTab />}
        {tab === "sessions" && <SessionsTab />}
        {tab === "recordings" && <RecordingsTab />}
      </main>
    </div>
  );
}

function StatsTab() {
  const [stats, setStats] = useState<any>(null);
  useEffect(() => { api.admin.stats().then(setStats).catch(console.error); }, []);

  if (!stats) return <Loader2 className="w-5 h-5 animate-spin text-primary" />;

  const cards = [
    { label: "Total Users", value: stats.total_users, icon: Users },
    { label: "Total Sessions", value: stats.total_sessions, icon: ClipboardList },
    { label: "Completed", value: stats.completed_sessions, icon: BarChart3 },
    { label: "In Progress", value: stats.in_progress_sessions, icon: BarChart3 },
  ];

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {cards.map((c) => (
          <Card key={c.label} className="bg-card/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <c.icon className="w-5 h-5 text-primary" />
              </div>
              <div className="text-2xl font-bold">{c.value}</div>
              <div className="text-xs text-muted-foreground">{c.label}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-3 text-muted-foreground">Sessions by Domain</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {Object.entries(stats.by_domain || {}).map(([domain, count]) => (
            <Card key={domain}>
              <CardContent className="pt-4 pb-4 flex items-center justify-between">
                <span className="text-sm">{domainLabel(domain)}</span>
                <span className="font-bold">{count as number}</span>
              </CardContent>
            </Card>
          ))}
          {Object.keys(stats.by_domain || {}).length === 0 && (
            <p className="text-sm text-muted-foreground col-span-3">No sessions yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function UsersTab() {
  const { user } = useAuthStore();
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = () => {
    setLoading(true);
    api.admin.users().then(setUsers).finally(() => setLoading(false));
  };
  useEffect(refresh, []);

  const toggleAdmin = async (u: any) => {
    try {
      if (u.is_admin) await api.admin.demoteUser(u.id);
      else await api.admin.promoteUser(u.id);
      toast({ title: u.is_admin ? "Admin revoked" : "Promoted to admin" });
      refresh();
    } catch (e: any) {
      toast({ variant: "destructive", title: "Failed", description: e.message });
    }
  };

  const removeUser = async (u: any) => {
    if (!confirm(`Delete ${u.email} and all their sessions? This is irreversible.`)) return;
    try {
      await api.admin.deleteUser(u.id);
      toast({ title: "User deleted" });
      refresh();
    } catch (e: any) {
      toast({ variant: "destructive", title: "Failed", description: e.message });
    }
  };

  if (loading) return <Loader2 className="w-5 h-5 animate-spin text-primary" />;

  return (
    <div className="space-y-2">
      {users.map((u) => (
        <Card key={u.id}>
          <CardContent className="py-4 flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium truncate">{u.name}</span>
                {u.is_admin && <Badge className="bg-primary/20 text-primary">admin</Badge>}
              </div>
              <div className="text-sm text-muted-foreground truncate">{u.email}</div>
              <div className="text-xs text-muted-foreground mt-0.5">
                {u.session_count} session{u.session_count === 1 ? "" : "s"} · joined{" "}
                {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
              </div>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <Button
                variant="outline"
                size="sm"
                onClick={() => toggleAdmin(u)}
                disabled={u.id === user?.id}
                title={u.id === user?.id ? "Can't modify your own role" : ""}
              >
                {u.is_admin ? <ArrowDownCircle className="w-4 h-4" /> : <ArrowUpCircle className="w-4 h-4" />}
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => removeUser(u)}
                disabled={u.id === user?.id}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
      {users.length === 0 && <p className="text-sm text-muted-foreground">No users.</p>}
    </div>
  );
}

function SessionsTab() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = () => {
    setLoading(true);
    api.admin.sessions().then(setSessions).finally(() => setLoading(false));
  };
  useEffect(refresh, []);

  const removeSession = async (id: string) => {
    if (!confirm("Delete this session and its recording?")) return;
    try {
      await api.admin.deleteSession(id);
      toast({ title: "Session deleted" });
      refresh();
    } catch (e: any) {
      toast({ variant: "destructive", title: "Failed", description: e.message });
    }
  };

  if (loading) return <Loader2 className="w-5 h-5 animate-spin text-primary" />;

  return (
    <div className="space-y-2">
      {sessions.map((s) => (
        <Card key={s.id}>
          <CardContent className="py-4 flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-medium">{domainLabel(s.domain)}</span>
                <Badge variant="outline" className="text-xs py-0">{s.difficulty}</Badge>
                <Badge variant="outline" className="text-xs py-0">{s.status}</Badge>
                {s.evaluation?.score != null && (
                  <Badge className="bg-primary/20 text-primary">
                    {Math.round(s.evaluation.score)}/100
                  </Badge>
                )}
              </div>
              <div className="text-sm text-muted-foreground truncate">
                {s.user_name} · {s.user_email}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">
                {s.created_at ? new Date(s.created_at).toLocaleString() : "—"}
              </div>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              {s.status === "completed" && (
                <Link href={`/results/${s.id}`}>
                  <Button variant="outline" size="sm">View</Button>
                </Link>
              )}
              <Button variant="destructive" size="sm" onClick={() => removeSession(s.id)}>
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
      {sessions.length === 0 && <p className="text-sm text-muted-foreground">No sessions.</p>}
    </div>
  );
}

function RecordingsTab() {
  const [recs, setRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = () => {
    setLoading(true);
    api.admin.recordings().then(setRecs).finally(() => setLoading(false));
  };
  useEffect(refresh, []);

  const remove = async (filename: string) => {
    if (!confirm(`Delete recording ${filename}?`)) return;
    try {
      await api.admin.deleteRecording(filename);
      toast({ title: "Recording deleted" });
      refresh();
    } catch (e: any) {
      toast({ variant: "destructive", title: "Failed", description: e.message });
    }
  };

  if (loading) return <Loader2 className="w-5 h-5 animate-spin text-primary" />;

  return (
    <div className="space-y-2">
      {recs.map((r) => (
        <Card key={r.id}>
          <CardContent className="py-4 flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="font-medium truncate">{r.filename}</div>
              <div className="text-sm text-muted-foreground truncate">
                {r.user_name} · {r.user_email} · {domainLabel(r.domain)}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">
                {r.created_at ? new Date(r.created_at).toLocaleString() : "—"}
              </div>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <a href={api.admin.recordingUrl(r.filename)} target="_blank" rel="noreferrer">
                <Button variant="outline" size="sm" className="gap-1.5">
                  <Download className="w-4 h-4" /> Download
                </Button>
              </a>
              <Button variant="destructive" size="sm" onClick={() => remove(r.filename)}>
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
      {recs.length === 0 && <p className="text-sm text-muted-foreground">No recordings.</p>}
    </div>
  );
}
