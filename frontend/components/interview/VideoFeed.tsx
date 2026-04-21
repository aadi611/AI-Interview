"use client";
import { useRef, useEffect } from "react";
import { Camera, CameraOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface VideoFeedProps {
  stream: MediaStream | null;
  className?: string;
  muted?: boolean;
  label?: string;
}

export function VideoFeed({ stream, className, muted = true, label }: VideoFeedProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  return (
    <div className={cn("relative rounded-xl overflow-hidden bg-zinc-900 border border-border", className)}>
      {stream ? (
        <video
          ref={videoRef}
          autoPlay
          muted={muted}
          playsInline
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="flex flex-col items-center justify-center h-full gap-2 text-muted-foreground">
          <CameraOff className="w-8 h-8" />
          <span className="text-sm">Camera off</span>
        </div>
      )}
      {label && (
        <div className="absolute bottom-2 left-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
          {label}
        </div>
      )}
      {stream && (
        <div className="absolute top-2 right-2 flex items-center gap-1 bg-black/60 text-white text-xs px-2 py-1 rounded">
          <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          LIVE
        </div>
      )}
    </div>
  );
}
