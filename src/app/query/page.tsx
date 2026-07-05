"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Clock, ChevronDown, ExternalLink } from "lucide-react";
import { queryNL, QueryResult } from "@/lib/api";

const EXAMPLE_QUERIES = [
  "Why do users stop using Discover Weekly?",
  "Top complaints from users who want to discover but keep repeating",
  "What do Reddit users say that App Store reviewers don't?",
  "Give me 5 quotes about algorithm staleness",
  "Which unmet need appears most across all sources?",
  "What is the JTBD of active explorer stuck users?",
];

export default function QueryPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<{ query: string; result: QueryResult }[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const handleSubmit = async (q?: string) => {
    const queryText = q || query;
    if (!queryText.trim()) return;

    setLoading(true);
    setQuery("");

    try {
      const result = await queryNL(queryText);
      setHistory((prev) => [{ query: queryText, result }, ...prev]);
    } catch (err) {
      setHistory((prev) => [
        {
          query: queryText,
          result: {
            answer: "Failed to process query. Please check that the backend is running.",
            evidence: [],
            confidence: "Low",
            confidence_reason: "API connection error",
            follow_up_questions: [],
            result_count: 0,
            query_time_ms: 0,
          },
        },
        ...prev,
      ]);
    } finally {
      setLoading(false);
    }
  };

  const confidenceColor = (c: string) => {
    if (c === "High") return "badge-green";
    if (c === "Medium") return "badge-orange";
    return "badge-red";
  };

  return (
    <div className="max-w-[900px] mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold flex items-center gap-2 mb-2">
          <Sparkles size={24} className="text-[var(--color-accent-green)]" />
          Ask a Question
        </h1>
        <p className="text-sm text-[var(--color-text-secondary)]">
          Query your review intelligence in natural language. The AI analyzes thousands of user feedback entries to answer your question.
        </p>
      </div>

      {/* Example Queries */}
      <div className="mb-6 flex flex-wrap gap-2">
        {EXAMPLE_QUERIES.map((eq) => (
          <button
            key={eq}
            onClick={() => handleSubmit(eq)}
            className="btn-secondary text-xs"
            disabled={loading}
          >
            {eq}
          </button>
        ))}
      </div>

      {/* Query Input */}
      <div className="relative mb-8">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder="Ask anything about user feedback..."
          className="chat-input pr-12"
          disabled={loading}
        />
        <button
          onClick={() => handleSubmit()}
          disabled={loading || !query.trim()}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-[var(--color-accent-green)] text-white disabled:opacity-30 hover:bg-[var(--color-accent-green-dim)] transition-all"
        >
          <Send size={16} />
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="glass-card p-8 mb-6 text-center animate-pulse-glow">
          <div className="flex items-center justify-center gap-3">
            <div className="w-5 h-5 border-2 border-[var(--color-accent-green)] border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-[var(--color-text-secondary)]">
              Analyzing feedback data...
            </span>
          </div>
        </div>
      )}

      {/* Results */}
      <div ref={resultsRef} className="space-y-6">
        {history.map((item, idx) => (
          <div key={idx} className="glass-card p-6 animate-fade-in">
            {/* Query */}
            <div className="flex items-center gap-2 mb-4 text-sm text-[var(--color-text-muted)]">
              <Clock size={14} />
              <span className="font-medium">{item.query}</span>
            </div>

            {/* Answer */}
            <div className="mb-4">
              <p className="text-[15px] leading-relaxed">{item.result.answer}</p>
            </div>

            {/* Evidence */}
            {item.result.evidence.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2 text-[var(--color-text-secondary)]">
                  Supporting Evidence
                </h3>
                <div className="space-y-2">
                  {item.result.evidence.map((e, i) => (
                    <div key={i} className="quote-card">
                      <p className="text-sm">{e.text}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`badge source-${e.source} text-[10px]`}>
                          {e.source.replace("_", " ")}
                        </span>
                        {e.date && (
                          <span className="text-[11px] text-[var(--color-text-muted)]">{e.date}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Confidence + Meta */}
            <div className="flex items-center gap-3 mb-4">
              <span className={`badge ${confidenceColor(item.result.confidence)}`}>
                {item.result.confidence} Confidence
              </span>
              <span className="text-xs text-[var(--color-text-muted)]">
                {item.result.result_count} results · {item.result.query_time_ms}ms
              </span>
            </div>

            {/* Follow-up Questions */}
            {item.result.follow_up_questions.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2 text-[var(--color-text-secondary)]">
                  Suggested Follow-ups
                </h3>
                <div className="flex flex-wrap gap-2">
                  {item.result.follow_up_questions.map((fq, i) => (
                    <button
                      key={i}
                      onClick={() => handleSubmit(fq)}
                      className="btn-secondary text-xs"
                      disabled={loading}
                    >
                      {fq}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Empty State */}
      {!loading && history.length === 0 && (
        <div className="text-center py-16">
          <Sparkles size={48} className="text-[var(--color-accent-green)] mx-auto mb-4 opacity-30" />
          <h3 className="text-lg font-semibold text-[var(--color-text-secondary)] mb-2">
            Ask anything about your users
          </h3>
          <p className="text-sm text-[var(--color-text-muted)] max-w-md mx-auto">
            Type a question above or click an example query. The AI will search through
            thousands of user reviews to give you evidence-backed answers.
          </p>
        </div>
      )}
    </div>
  );
}
