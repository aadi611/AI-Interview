"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Clock, Mic, MicOff, Video, VideoOff, StopCircle, Settings, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ChatPanel } from "@/components/interview/ChatPanel";
import { VideoFeed } from "@/components/interview/VideoFeed";
import { VoiceControl } from "@/components/interview/VoiceControl";
import { AIIndicator } from "@/components/interview/AIIndicator";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useMediaRecorder } from "@/hooks/useMediaRecorder";
import { useVoice } from "@/hooks/useVoice";
import { useInterviewStore } from "@/stores/interviewStore";
import { api } from "@/lib/api";
import { formatDuration, domainLabel } from "@/lib/utils";
import { cn } from "@/lib/utils";

export default function InterviewRoomPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();
  const [session, setSession] = useState<any>(null);
  const [cameraOn, setCameraOn] = useState(true);
  const [ended, setEnded] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const timerRef = useRef<NodeJS.Timeout>();

  const {
    messages, isTyping, evaluation, elapsed,
    setSession: storeSetSession, addMessage, incrementElapsed
  } = useInterviewStore();

  // Load session
  useEffect(() => {
    api.sessions.get(sessionId).then((s) => {
      setSession(s);
      storeSetSession(s.id, s.domain, s.difficulty);
    }).catch(() => router.push("/dashboard"));
  }, [sessionId]);

  // Timer
  useEffect(() => {
    timerRef.current = setInterval(incrementElapsed, 1000);
    return () => clearInterval(timerRef.current);
  }, []);

  // Video recording
  const { startRecording, stopRecording, streamRef } = useMediaRecorder(sessionId);

  useEffect(() => {
    if (session && cameraOn) {
      startRecording(videoRef as any);
    }
  }, [session]);

  const { start: startVoice, stopCurrentRecorder, stopAudio, stopAll: stopAllVoice, playAudio, isListening, isSpeaking } = useVoice();
  const [voiceActive, setVoiceActive] = useState(false);
  const voiceActiveRef = useRef(false);
  useEffect(() => { voiceActiveRef.current = voiceActive; }, [voiceActive]);

  // Forward-declare refs so beginListening/handleAudio can reference each other
  const beginListeningRef = useRef<() => Promise<void>>();
  const sendBinaryRef = useRef<(d: ArrayBuffer) => void>(() => {});
  const sendControlRef = useRef<(t: string, e?: object) => void>(() => {});

  const handleAssistantAudio = useCallback((base64: string, revealText: () => void) => {
    playAudio(
      base64,
      () => {
        // Auto-resume listening after AI finishes speaking
        if (voiceActiveRef.current) beginListeningRef.current?.();
      },
      // Reveal the assistant's text bubble the moment audio actually starts
      revealText,
    );
  }, [playAudio]);

  // WebSocket — one unified endpoint handles both voice + chat
  const { sendMessage, sendBinary, sendControl } = useWebSocket({
    sessionId,
    enabled: !!session,
    onEvaluation: () => {
      stopRecording().then(() => {
        setTimeout(() => router.push(`/results/${sessionId}`), 2000);
      });
    },
    onAssistantAudio: handleAssistantAudio,
  });

  useEffect(() => {
    sendBinaryRef.current = sendBinary;
    sendControlRef.current = sendControl;
  });

  const beginListening = useCallback(async () => {
    sendControlRef.current("start_voice");
    await startVoice({
      onChunk: (chunk) => sendBinaryRef.current(chunk),
      onSilence: () => {
        // User paused — finalize this turn, server will transcribe + respond
        sendControlRef.current("end_voice");
        stopCurrentRecorder();
      },
      onBargeIn: () => {
        // User spoke while AI was talking — interrupt AI and hand mic back
        stopAudio();
        sendControlRef.current("interrupt");
        if (voiceActiveRef.current) beginListeningRef.current?.();
      },
    });
  }, [startVoice, stopCurrentRecorder, stopAudio]);
  beginListeningRef.current = beginListening;

  const toggleVoice = useCallback(() => {
    if (voiceActive) {
      setVoiceActive(false);
      sendControlRef.current("end_voice");
      stopAllVoice();
    } else {
      setVoiceActive(true);
      beginListening();
    }
  }, [voiceActive, beginListening, stopAllVoice]);

  const handleSend = (content: string) => {
    addMessage({ role: "user", content });
    sendMessage(content);
  };

  const handleEnd = async () => {
    setEnded(true);
    clearInterval(timerRef.current);
    await stopRecording();
    sendControl("end");
    setTimeout(() => router.push(`/results/${sessionId}`), 500);
  };

  if (!session) return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Brain className="w-5 h-5 animate-pulse text-primary" />
        Loading interview room...
      </div>
    </div>
  );

  const stream = streamRef.current;

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      {/* Top Bar */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-border/40 bg-background/80 backdrop-blur flex-shrink-0">
        <div className="flex items-center gap-3">
          <Brain className="w-5 h-5 text-primary" />
          <span className="font-semibold">{domainLabel(session.domain)}</span>
          <Badge variant="outline">{session.difficulty}</Badge>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <Clock className="w-4 h-4" />
            <span className="font-mono">{formatDuration(elapsed)}</span>
          </div>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleEnd}
            disabled={ended}
            className="gap-1.5"
          >
            <StopCircle className="w-4 h-4" />
            End Interview
          </Button>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Video + Controls */}
        <div className="w-80 border-r border-border/40 flex flex-col p-4 gap-4 flex-shrink-0">
          {/* Candidate video */}
          <VideoFeed
            stream={cameraOn ? stream : null}
            className="aspect-video"
            label="You"
          />

          {/* AI avatar placeholder */}
          <div className="aspect-video rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 border border-border flex flex-col items-center justify-center gap-2">
            <Brain className={cn("w-10 h-10 text-primary", isTyping && "animate-pulse")} />
            <span className="text-xs text-muted-foreground font-medium">AI Interviewer</span>
            {isTyping && (
              <div className="flex gap-1">
                {Array.from({ length: 3 }).map((_, i) => (
                  <span
                    key={i}
                    className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Camera toggle */}
          <div className="flex gap-2">
            <Button
              variant={cameraOn ? "outline" : "secondary"}
              size="sm"
              className="flex-1"
              onClick={() => setCameraOn(!cameraOn)}
            >
              {cameraOn ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
              {cameraOn ? "Camera On" : "Camera Off"}
            </Button>
          </div>

          {/* Voice controls — always visible */}
          <div className="flex-1 flex items-center justify-center">
            <VoiceControl
              isListening={isListening}
              isSpeaking={isSpeaking}
              voiceActive={voiceActive}
              onToggle={toggleVoice}
            />
          </div>
        </div>

        {/* Right: Chat — text input always available as a fallback */}
        <div className="flex-1 flex flex-col">
          <ChatPanel onSend={handleSend} />
        </div>
      </div>

      {/* Evaluation overlay */}
      <AnimatePresence>
        {evaluation && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 bg-background/95 flex items-center justify-center"
          >
            <div className="text-center space-y-4">
              <div className="text-6xl font-black text-primary">{evaluation.score}</div>
              <div className="text-2xl font-bold">Interview Complete!</div>
              <p className="text-muted-foreground">Redirecting to your results...</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
