"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Users, ChevronRight } from "lucide-react";
import { fetchSegments, fetchSegment, SegmentDetail } from "@/lib/api";

const SEGMENT_META: Record<string, { label: string; color: string; description: string }> = {
  active_explorer_stuck: { label: "Active Explorer (Stuck)", color: "#ec4899", description: "Wants to discover new music but keeps defaulting to familiar content" },
  background_listener: { label: "Background Listener", color: "#6b7280", description: "Uses music as functional background — discovery isn't important" },
  mood_regulator: { label: "Mood Regulator", color: "#8b5cf6", description: "Uses music to achieve a specific emotional state — new music feels risky" },
  identity_listener: { label: "Identity Listener", color: "#f59e0b", description: "Music reflects identity and nostalgia — discovery isn't relevant" },
  socially_led_discoverer: { label: "Social Discoverer", color: "#06b6d4", description: "Discovers music through friends and social media, not the algorithm" },
  new_user: { label: "New User", color: "#22c55e", description: "Recently joined Spotify, still building their library" },
  unclear: { label: "Unclear", color: "#374151", description: "Segment cannot be determined from the review text" },
};

const SENTIMENT_COLORS: Record<string, string> = {
  very_negative: "#ef4444", negative: "#f97316", neutral: "#6b7280",
  positive: "#22c55e", very_positive: "#1DB954",
};

const DEMO_SEGMENTS = [
  { segment: "active_explorer_stuck", review_count: 823, top_complaint: "algorithm_staleness" },
  { segment: "mood_regulator", review_count: 342, top_complaint: "mood_mismatch" },
  { segment: "background_listener", review_count: 298, top_complaint: "no_complaint" },
  { segment: "identity_listener", review_count: 234, top_complaint: "genre_bubble" },
  { segment: "socially_led_discoverer", review_count: 187, top_complaint: "social_disconnect" },
  { segment: "new_user", review_count: 134, top_complaint: "choice_overload" },
];

const DEMO_DETAIL: SegmentDetail = {
  segment: "active_explorer_stuck", total_reviews: 823,
  top_complaints: [{ category: "algorithm_staleness", count: 312 }, { category: "genre_bubble", count: 198 }, { category: "trust_erosion", count: 145 }],
  top_unmet_needs: [{ need: "Recommendations that evolve with my taste", count: 287 }, { need: "Break out of genre bubble", count: 198 }, { need: "Better feedback mechanism", count: 134 }],
  sentiment_distribution: { very_negative: 198, negative: 312, neutral: 98, positive: 145, very_positive: 70 },
  cross_source_presence: { app_store: 185, play_store: 178, reddit: 245, spotify_community: 112, twitter_x: 103 },
  jtbd_statements: [
    "When I want to explore new music, I want fresh recommendations that match my evolving taste, so that I can discover artists I'd never find on my own",
    "When I'm tired of my usual playlist, I want to easily break out of my genre bubble, so that I can experience new styles",
    "When I dislike a recommendation, I want the algorithm to learn immediately, so that I don't waste time on bad suggestions",
  ],
  representative_quotes: [
    { quote: "My Discover Weekly has been recommending the same type of songs for months", source: "app_store", date: "2026-03-15", rating: 2, sentiment: "negative" },
    { quote: "I actively try to listen to new genres but Spotify keeps pulling me back", source: "reddit", date: "2026-04-02", rating: null, sentiment: "very_negative" },
    { quote: "Haven't found a single new artist through Spotify in over 6 months", source: "play_store", date: "2026-05-10", rating: 1, sentiment: "very_negative" },
  ],
};

export default function SegmentsPage() {
  const [segments, setSegments] = useState(DEMO_SEGMENTS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<SegmentDetail | null>(null);

  useEffect(() => {
    fetchSegments().then(d => setSegments(d.segments || DEMO_SEGMENTS)).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedId) {
      fetchSegment(selectedId).then(setDetail).catch(() => setDetail(DEMO_DETAIL));
    }
  }, [selectedId]);

  const d = detail || DEMO_DETAIL;
  const displaySegment = selectedId || d.segment;
  const meta = SEGMENT_META[displaySegment] || { label: displaySegment, color: "#6b7280", description: "" };
  const sentimentData = Object.entries(d.sentiment_distribution).map(([k, v]) => ({ name: k.replace("_", " "), value: v, fill: SENTIMENT_COLORS[k] || "#6b7280" }));
  const sourceData = Object.entries(d.cross_source_presence).map(([k, v]) => ({ name: k.replace("_", " "), value: v }));

  return (
    <div className="max-w-[1400px] mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold flex items-center gap-2 mb-2">
          <Users size={24} className="text-[var(--color-accent-green)]" />
          Segment Breakdown
        </h1>
        <p className="text-sm text-[var(--color-text-secondary)]">
          Understand how different user segments express the discovery problem
        </p>
      </div>

      <div className="flex gap-6">
        {/* Segment List */}
        <div className="w-[300px] shrink-0 space-y-2">
          {segments.map(s => {
            const sm = SEGMENT_META[s.segment] || { label: s.segment, color: "#6b7280" };
            return (
              <button
                key={s.segment}
                onClick={() => setSelectedId(s.segment)}
                className={`w-full text-left p-4 rounded-xl border transition-all ${
                  selectedId === s.segment
                    ? "border-[var(--color-accent-green)] bg-[var(--color-bg-card-hover)]"
                    : "border-[var(--color-border)] bg-[var(--color-bg-card)] hover:border-[var(--color-border-hover)]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ background: sm.color }} />
                    <span className="font-semibold text-sm">{sm.label}</span>
                  </div>
                  <ChevronRight size={14} className="text-[var(--color-text-muted)]" />
                </div>
                <span className="text-xs text-[var(--color-text-muted)] ml-5">{s.review_count} reviews</span>
              </button>
            );
          })}
        </div>

        {/* Detail Panel */}
        <div className="flex-1 space-y-6">
          <div className="glass-card p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-4 h-4 rounded-full" style={{ background: meta.color }} />
              <h2 className="text-xl font-bold">{meta.label}</h2>
            </div>
            <p className="text-sm text-[var(--color-text-secondary)] mb-3">{meta.description}</p>
            <span className="badge badge-green">{d.total_reviews} reviews</span>
          </div>

          {/* Top Complaints + Unmet Needs */}
          <div className="dashboard-grid dashboard-grid-2">
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold mb-3">Top Complaints</h3>
              {d.top_complaints.map((c, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-[var(--color-border)] last:border-0">
                  <span className="text-sm">{c.category.replace(/_/g, " ")}</span>
                  <span className="badge badge-orange text-xs">{c.count}</span>
                </div>
              ))}
            </div>

            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold mb-3">Top Unmet Needs</h3>
              {d.top_unmet_needs.map((n, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-[var(--color-border)] last:border-0">
                  <span className="text-sm">{n.need}</span>
                  <span className="badge badge-purple text-xs">{n.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Sentiment + Source */}
          <div className="dashboard-grid dashboard-grid-2">
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold mb-3">Sentiment Distribution</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={sentimentData}>
                  <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #2a2a3e", borderRadius: "8px", color: "#f0f0f5" }} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {sentimentData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold mb-3">Cross-Source Presence</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={sourceData} layout="vertical">
                  <XAxis type="number" tick={{ fill: "#9ca3af", fontSize: 11 }} />
                  <YAxis dataKey="name" type="category" width={90} tick={{ fill: "#9ca3af", fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #2a2a3e", borderRadius: "8px", color: "#f0f0f5" }} />
                  <Bar dataKey="value" fill="#1DB954" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* JTBD Statements */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold mb-3">Jobs-to-be-Done Statements</h3>
            <div className="space-y-3">
              {d.jtbd_statements.map((j, i) => (
                <div key={i} className="p-4 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl">
                  <p className="text-sm italic text-[var(--color-text-secondary)]">&ldquo;{j}&rdquo;</p>
                </div>
              ))}
            </div>
          </div>

          {/* Quotes */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold mb-3">Representative Quotes</h3>
            <div className="space-y-3">
              {d.representative_quotes.map((q, i) => (
                <div key={i} className="quote-card">
                  <p className="text-sm italic mb-2">&ldquo;{q.quote}&rdquo;</p>
                  <div className="flex items-center gap-2">
                    <span className={`badge source-${q.source} text-[10px]`}>{q.source.replace("_", " ")}</span>
                    {q.rating && <span className="text-[11px] text-[var(--color-text-muted)]">★ {q.rating}/5</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
