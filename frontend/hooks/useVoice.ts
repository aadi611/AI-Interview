"use client";
import { useRef, useCallback, useState, useEffect } from "react";
import { useInterviewStore } from "@/stores/interviewStore";

interface StartOpts {
  onChunk: (data: ArrayBuffer) => void;
  onSilence: () => void;           // user paused ~silenceMs while recording
  onBargeIn?: () => void;          // user spoke while AI was playing TTS
  silenceMs?: number;
}

export function useVoice() {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Callback refs so a single long-lived SpeechRecognition instance
  // can always see the latest handlers without being recreated.
  const onSilenceRef = useRef<() => void>(() => {});
  const onBargeInRef = useRef<() => void>(() => {});
  const silenceMsRef = useRef(900);
  const isSpeakingRef = useRef(false);

  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState("");
  const { setVoiceActive, setTranscript } = useInterviewStore();

  useEffect(() => { isSpeakingRef.current = isSpeaking; }, [isSpeaking]);

  const clearSilenceTimer = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  };

  const armSilenceTimer = () => {
    clearSilenceTimer();
    silenceTimerRef.current = setTimeout(() => {
      onSilenceRef.current();
    }, silenceMsRef.current);
  };

  const ensureRecognition = useCallback(() => {
    if (recognitionRef.current) return;
    const SR: any =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    const recog = new SR();
    recog.continuous = true;
    recog.interimResults = true;
    recog.lang = "en-US";
    recog.onresult = (event: any) => {
      let interim = "";
      let final = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const chunk = event.results[i];
        if (chunk.isFinal) final += chunk[0].transcript;
        else interim += chunk[0].transcript;
      }
      const live = (final + " " + interim).trim();
      if (!live) return;

      if (isSpeakingRef.current) {
        // User barged in while AI was talking
        onBargeInRef.current();
        return;
      }

      if (mediaRecorderRef.current?.state === "recording") {
        setInterimTranscript(live);
        setTranscript(live);
        armSilenceTimer();
      }
    };
    recog.onerror = () => {};
    recog.onend = () => {
      // Restart as long as the session is still alive (stream present)
      if (streamRef.current) {
        try { recog.start(); } catch {}
      }
    };
    try { recog.start(); } catch {}
    recognitionRef.current = recog;
  }, [setTranscript]);

  const start = useCallback(
    async ({ onChunk, onSilence, onBargeIn, silenceMs = 900 }: StartOpts) => {
      onSilenceRef.current = onSilence;
      onBargeInRef.current = onBargeIn || (() => {});
      silenceMsRef.current = silenceMs;

      if (!streamRef.current) {
        streamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
      }
      const stream = streamRef.current;

      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = async (e) => {
        if (e.data.size > 0) {
          const buf = await e.data.arrayBuffer();
          onChunk(buf);
        }
      };
      recorder.start(250);

      ensureRecognition();
      // Don't arm silence timer yet — wait for first speech result.
      // Otherwise user pausing to think (>silenceMs) before speaking ends the turn.
      setIsListening(true);
      setVoiceActive(true);
    },
    [ensureRecognition, setVoiceActive]
  );

  const stopCurrentRecorder = useCallback(() => {
    clearSilenceTimer();
    const r = mediaRecorderRef.current;
    if (r && r.state !== "inactive") {
      try { r.stop(); } catch {}
    }
    mediaRecorderRef.current = null;
    setInterimTranscript("");
  }, []);

  const stopAudio = useCallback(() => {
    const a = audioRef.current;
    if (a) {
      try { a.pause(); } catch {}
      audioRef.current = null;
    }
    setIsSpeaking(false);
  }, []);

  const stopAll = useCallback(() => {
    stopCurrentRecorder();
    stopAudio();
    try { recognitionRef.current?.stop(); } catch {}
    recognitionRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setIsListening(false);
    setVoiceActive(false);
    setTranscript("");
  }, [setTranscript, setVoiceActive, stopCurrentRecorder, stopAudio]);

  const playAudio = useCallback(
    async (base64: string, onEnded?: () => void, onStart?: () => void) => {
      try {
        // Replace any currently playing audio
        if (audioRef.current) {
          try { audioRef.current.pause(); } catch {}
        }
        const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
        const blob = new Blob([bytes], { type: "audio/mp3" });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audioRef.current = audio;
        setIsSpeaking(true);
        let started = false;
        const fireStart = () => {
          if (started) return;
          started = true;
          onStart?.();
        };
        const cleanup = () => {
          URL.revokeObjectURL(url);
          if (audioRef.current === audio) {
            audioRef.current = null;
            setIsSpeaking(false);
          }
          // If we never got a "playing" event (e.g. autoplay blocked), still reveal text.
          fireStart();
          onEnded?.();
        };
        audio.onplaying = fireStart;
        audio.onended = cleanup;
        audio.onerror = cleanup;
        audio.onpause = () => {
          if (!audio.ended) cleanup();
        };
        await audio.play();
      } catch (e) {
        console.error("Audio play failed:", e);
        setIsSpeaking(false);
        onStart?.();
        onEnded?.();
      }
    },
    []
  );

  useEffect(() => {
    return () => { stopAll(); };
  }, [stopAll]);

  return {
    start,
    stopCurrentRecorder,
    stopAudio,
    stopAll,
    playAudio,
    isListening,
    isSpeaking,
    interimTranscript,
  };
}
