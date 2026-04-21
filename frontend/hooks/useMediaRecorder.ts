"use client";
import { useRef, useCallback, useState } from "react";
import { useInterviewStore } from "@/stores/interviewStore";
import { api } from "@/lib/api";

export function useMediaRecorder(sessionId: string) {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const { setRecording } = useInterviewStore();

  const startRecording = useCallback(async (videoRef: React.RefObject<HTMLVideoElement>) => {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    streamRef.current = stream;

    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      videoRef.current.muted = true;
    }

    const recorder = new MediaRecorder(stream, { mimeType: "video/webm;codecs=vp9,opus" });
    mediaRecorderRef.current = recorder;
    chunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.start(1000); // collect data every second
    setRecording(true);
  }, [setRecording]);

  const stopRecording = useCallback(async (): Promise<string | null> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder) { resolve(null); return; }

      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "video/webm" });
        const url = URL.createObjectURL(blob);
        setVideoUrl(url);

        try {
          const { url: remoteUrl } = await api.recordings.upload(sessionId, blob);
          resolve(remoteUrl);
        } catch {
          resolve(url);
        }

        streamRef.current?.getTracks().forEach((t) => t.stop());
        setRecording(false);
      };

      recorder.stop();
    });
  }, [sessionId, setRecording]);

  return { startRecording, stopRecording, videoUrl, streamRef };
}
