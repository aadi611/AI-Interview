import { create } from "zustand";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface Evaluation {
  score: number;
  strengths: string[];
  weaknesses: string[];
  improvements: string[];
  overall_feedback: string;
}

interface InterviewState {
  sessionId: string | null;
  domain: string | null;
  difficulty: string | null;
  messages: Message[];
  evaluation: Evaluation | null;
  isTyping: boolean;
  isRecording: boolean;
  isVoiceActive: boolean;
  transcript: string;
  elapsed: number;

  setSession: (id: string, domain: string, difficulty: string) => void;
  addMessage: (msg: Omit<Message, "id" | "timestamp">) => void;
  setTyping: (v: boolean) => void;
  setEvaluation: (e: Evaluation) => void;
  setRecording: (v: boolean) => void;
  setVoiceActive: (v: boolean) => void;
  setTranscript: (t: string) => void;
  incrementElapsed: () => void;
  reset: () => void;
}

export const useInterviewStore = create<InterviewState>((set) => ({
  sessionId: null,
  domain: null,
  difficulty: null,
  messages: [],
  evaluation: null,
  isTyping: false,
  isRecording: false,
  isVoiceActive: false,
  transcript: "",
  elapsed: 0,

  setSession: (id, domain, difficulty) => set({ sessionId: id, domain, difficulty }),
  addMessage: (msg) =>
    set((s) => ({
      messages: [
        ...s.messages,
        { ...msg, id: crypto.randomUUID(), timestamp: new Date() },
      ],
    })),
  setTyping: (isTyping) => set({ isTyping }),
  setEvaluation: (evaluation) => set({ evaluation }),
  setRecording: (isRecording) => set({ isRecording }),
  setVoiceActive: (isVoiceActive) => set({ isVoiceActive }),
  setTranscript: (transcript) => set({ transcript }),
  incrementElapsed: () => set((s) => ({ elapsed: s.elapsed + 1 })),
  reset: () =>
    set({
      sessionId: null,
      messages: [],
      evaluation: null,
      isTyping: false,
      isRecording: false,
      isVoiceActive: false,
      transcript: "",
      elapsed: 0,
    }),
}));
