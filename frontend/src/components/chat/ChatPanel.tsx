import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { streamChat } from "../../api/client";
import type { Message, Source } from "../../types";

interface Props {
  messages: Message[];
  sources: Source[];
  lastRoute?: string;
  loading: boolean;
  onSend: (prompt: string) => Promise<void>;
  onMessagesUpdate: (messages: Message[], sources: Source[], route: string) => void;
  placeholder?: string;
}

export default function ChatPanel({
  messages,
  sources,
  lastRoute,
  loading,
  onSend,
  onMessagesUpdate,
  placeholder = "Ask about rules…",
}: Props) {
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, streaming]);

  const submit = async () => {
    const prompt = input.trim();
    if (!prompt || loading || streaming) return;
    setInput("");
    setStreaming(true);
    const optimistic = [...messages, { role: "user" as const, content: prompt }];
    onMessagesUpdate(optimistic, sources, lastRoute || "");
    streamChat(
      prompt,
      (data) => {
        onMessagesUpdate(data.messages, data.sources, data.route);
        setStreaming(false);
      },
      () => {
        onSend(prompt).finally(() => setStreaming(false));
      }
    );
  };

  return (
    <div className="panel flex flex-col h-full min-h-0">
      <div className="px-4 py-2.5 border-b border-border flex items-center justify-between gap-2">
        <span className="section-title">Chat</span>
        {lastRoute && (
          <span className="badge bg-elevated text-muted border border-border">{lastRoute}</span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
        {messages.length === 0 && (
          <p className="text-muted text-sm">
            Start with a rules question, /roll d20, or a journey shortcut.
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex gap-2.5 ${m.role === "user" ? "flex-row-reverse" : ""}`}
          >
            <div
              className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${
                m.role === "user"
                  ? "bg-accent/20 text-accent"
                  : "bg-moss-muted text-moss"
              }`}
            >
              {m.role === "user" ? "Y" : "A"}
            </div>
            <div
              className={`rounded-xl px-3 py-2 max-w-[85%] ${
                m.role === "user"
                  ? "bg-accent-muted/60 border border-accent/20"
                  : "bg-elevated border border-border"
              }`}
            >
              <div className="prose-chat">
                <ReactMarkdown>{m.content}</ReactMarkdown>
              </div>
            </div>
          </div>
        ))}
        {(loading || streaming) && (
          <div className="text-sm text-muted animate-pulse pl-9">Thinking…</div>
        )}
        <div ref={bottomRef} />
      </div>

      {sources.length > 0 && (
        <details className="border-t border-border px-4 py-2 text-xs">
          <summary className="cursor-pointer text-muted hover:text-gray-200">
            Sources ({sources.length})
          </summary>
          <ul className="mt-2 space-y-1 max-h-32 overflow-y-auto">
            {sources.map((s, i) => (
              <li key={i} className="text-muted">
                {s.source_label || s.source_file} p.{s.page}
                {s.score != null ? ` (${s.score.toFixed?.(2) ?? s.score})` : ""}
              </li>
            ))}
          </ul>
        </details>
      )}

      <div className="p-3 border-t border-border flex gap-2 bg-panel sticky bottom-0">
        <input
          className="input flex-1"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && submit()}
          placeholder={placeholder}
          disabled={loading || streaming}
        />
        <button
          type="button"
          className="btn btn-primary flex items-center gap-1.5 px-4"
          onClick={submit}
          disabled={loading || streaming}
        >
          <Send className="w-4 h-4" />
          <span className="hidden sm:inline">Send</span>
        </button>
      </div>
    </div>
  );
}
