"use client";
import { useEffect, useRef, useCallback } from "react";
import { useInterviewStore } from "@/stores/interviewStore";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

type WSMessage =
  | { type: "message"; content: string; role: "assistant"; audio?: string; format?: string }
  | { type: "typing"; active: boolean }
  | { type: "evaluation"; data: any }
  | { type: "transcript"; text: string }
  | { type: "audio"; data: string; format: string }
  | { type: "error"; message: string }
  | { type: "processing"; active: boolean };

interface UseWebSocketOptions {
  sessionId: string;
  enabled?: boolean;
  onEvaluation?: (data: any) => void;
  /** Called when an assistant turn carries audio. The handler is responsible for
   * playing the audio AND revealing the text (via revealText) at the right moment. */
  onAssistantAudio?: (audio: string, revealText: () => void) => void;
  onTranscript?: (text: string) => void;
}

export function useWebSocket({
  sessionId,
  enabled = true,
  onEvaluation,
  onAssistantAudio,
  onTranscript,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const { addMessage, setTyping, setEvaluation, setTranscript } = useInterviewStore();

  // Stable refs so callbacks never invalidate the connect memoization
  const onEvaluationRef = useRef(onEvaluation);
  const onAssistantAudioRef = useRef(onAssistantAudio);
  const onTranscriptRef = useRef(onTranscript);
  useEffect(() => {
    onEvaluationRef.current = onEvaluation;
    onAssistantAudioRef.current = onAssistantAudio;
    onTranscriptRef.current = onTranscript;
  });

  const connect = useCallback(() => {
    if (!sessionId || !enabled) return null;

    const token = localStorage.getItem("access_token") || "";
    const ws = new WebSocket(`${WS_BASE}/ws/interview/${sessionId}?token=${token}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);

      switch (msg.type) {
        case "message": {
          const content = msg.content;
          const role = msg.role;
          if (msg.audio && onAssistantAudioRef.current) {
            // Defer text reveal until audio actually starts playing
            let revealed = false;
            const reveal = () => {
              if (revealed) return;
              revealed = true;
              addMessage({ role, content });
            };
            onAssistantAudioRef.current(msg.audio, reveal);
          } else {
            addMessage({ role, content });
          }
          break;
        }
        case "typing":
          setTyping(msg.active);
          break;
        case "evaluation":
          setEvaluation(msg.data);
          onEvaluationRef.current?.(msg.data);
          break;
        case "transcript":
          if (msg.text?.trim()) addMessage({ role: "user", content: msg.text });
          setTranscript("");
          onTranscriptRef.current?.(msg.text);
          break;
        case "audio":
          // Legacy path — audio without bundled text. Play without text sync.
          onAssistantAudioRef.current?.(msg.data, () => {});
          break;
        case "error":
          console.error("WS error:", msg.message);
          break;
      }
    };

    ws.onerror = () => console.error("WebSocket connection error");
    ws.onclose = () => (wsRef.current = null);

    return ws;
  }, [sessionId, enabled, addMessage, setTyping, setEvaluation, setTranscript]);
  // Callbacks intentionally excluded — accessed via refs above

  useEffect(() => {
    const ws = connect();
    return () => ws?.close();
  }, [connect]);

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "message", content }));
    }
  }, []);

  const sendBinary = useCallback((data: ArrayBuffer | Blob) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  const sendControl = useCallback((type: string, extra: object = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, ...extra }));
    }
  }, []);

  return { sendMessage, sendBinary, sendControl, wsRef };
}
