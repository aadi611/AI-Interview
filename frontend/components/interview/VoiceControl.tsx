"use client";
import { Mic, Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface VoiceControlProps {
  isListening: boolean;
  isSpeaking: boolean;
  voiceActive: boolean;
  onToggle: () => void;
  className?: string;
}

export function VoiceControl({
  isListening,
  isSpeaking,
  voiceActive,
  onToggle,
  className,
}: VoiceControlProps) {
  const status = isSpeaking
    ? "AI is speaking..."
    : isListening
    ? "Listening — speak naturally"
    : voiceActive
    ? "Paused"
    : "Tap to start voice mode";

  return (
    <div className={cn("flex flex-col items-center gap-4", className)}>
      <button
        onClick={onToggle}
        className={cn(
          "w-20 h-20 rounded-full border-4 transition-all duration-200 flex items-center justify-center",
          isSpeaking
            ? "bg-blue-500/20 border-blue-500 scale-110 shadow-lg shadow-blue-500/30"
            : isListening
            ? "bg-red-500/20 border-red-500 scale-110 shadow-lg shadow-red-500/30 animate-pulse"
            : "bg-primary/10 border-primary hover:bg-primary/20 hover:scale-105"
        )}
      >
        {isSpeaking ? (
          <Volume2 className="w-8 h-8 text-blue-500" />
        ) : isListening ? (
          <div className="flex items-end gap-[2px] h-8 text-red-500">
            {Array.from({ length: 5 }).map((_, i) => (
              <span
                key={i}
                className="w-1.5 bg-current rounded-full animate-pulse"
                style={{ animationDelay: `${i * 0.1}s`, height: `${40 + (i % 3) * 20}%` }}
              />
            ))}
          </div>
        ) : (
          <Mic className="w-8 h-8 text-primary" />
        )}
      </button>
      <p className="text-xs text-muted-foreground text-center max-w-[12rem]">
        {status}
      </p>
      {voiceActive && (
        <p className="text-[10px] text-muted-foreground/60 text-center">
          Tap again to stop
        </p>
      )}
    </div>
  );
}
