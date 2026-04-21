"use client";
import { cn } from "@/lib/utils";
import { Bot } from "lucide-react";

interface AIIndicatorProps {
  isTyping: boolean;
  isSpeaking?: boolean;
  className?: string;
}

export function AIIndicator({ isTyping, isSpeaking, className }: AIIndicatorProps) {
  if (!isTyping && !isSpeaking) return null;

  return (
    <div className={cn("flex items-center gap-2 text-sm text-muted-foreground", className)}>
      <Bot className="w-4 h-4 text-primary animate-pulse" />
      {isSpeaking ? (
        <div className="audio-wave flex items-end gap-[2px] h-4 text-primary">
          {Array.from({ length: 5 }).map((_, i) => (
            <span key={i} style={{ animationDelay: `${i * 0.1}s`, height: "100%" }} />
          ))}
        </div>
      ) : (
        <span>AI is thinking...</span>
      )}
    </div>
  );
}
