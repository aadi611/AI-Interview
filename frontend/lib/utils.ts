import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function scoreToGrade(score: number): { label: string; color: string } {
  if (score >= 85) return { label: "Excellent", color: "text-green-500" };
  if (score >= 70) return { label: "Good", color: "text-blue-500" };
  if (score >= 55) return { label: "Average", color: "text-yellow-500" };
  return { label: "Needs Work", color: "text-red-500" };
}

export function domainLabel(domain: string): string {
  const labels: Record<string, string> = {
    dsa: "DSA",
    system_design: "System Design",
    hr: "HR",
    behavioral: "Behavioral",
    frontend: "Frontend",
    backend: "Backend",
    ml: "Machine Learning",
  };
  return labels[domain] || domain;
}
