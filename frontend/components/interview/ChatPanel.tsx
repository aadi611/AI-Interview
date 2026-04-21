"use client";
import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AIIndicator } from "./AIIndicator";
import { useInterviewStore, type Message } from "@/stores/interviewStore";
import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";

interface ChatPanelProps {
  onSend: (content: string) => void;
}

function MessageBubble({ message }: { message: Message }) {
  const isAI = message.role === "assistant";
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("flex gap-3", isAI ? "flex-row" : "flex-row-reverse")}
    >
      <div className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
        isAI ? "bg-primary/20 text-primary" : "bg-secondary"
      )}>
        {isAI ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
      </div>
      <div className={cn(
        "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
        isAI
          ? "bg-secondary text-foreground rounded-tl-sm"
          : "bg-primary text-primary-foreground rounded-tr-sm"
      )}>
        {message.content}
      </div>
    </motion.div>
  );
}

export function ChatPanel({ onSend }: ChatPanelProps) {
  const { messages, isTyping, isVoiceActive, transcript } = useInterviewStore();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping, transcript]);

  const handleSend = () => {
    const content = input.trim();
    if (!content) return;
    onSend(content);
    setInput("");
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
        </AnimatePresence>
        {isTyping && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="pl-11">
            <AIIndicator isTyping={isTyping} />
          </motion.div>
        )}
        {isVoiceActive && transcript && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3 flex-row-reverse"
          >
            <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-secondary">
              <User className="w-4 h-4" />
            </div>
            <div className="max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed bg-primary/60 text-primary-foreground rounded-tr-sm italic">
              {transcript}
              <span className="ml-1 inline-block w-1 h-4 bg-current animate-pulse align-middle" />
            </div>
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder="Type your answer, or use the mic..."
            className="flex-1 bg-secondary/50 border-0 focus-visible:ring-1"
          />
          <Button onClick={handleSend} size="icon" disabled={!input.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
