"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line,
} from "recharts";
import { Layers, ChevronRight, ExternalLink } from "lucide-react";
import { fetchThemes, fetchTheme, ThemeDetail } from "@/lib/api";

const SOURCE_COLORS: Record<string, string> = {
  app_store: "#3b82f6", play_store: "#22c55e", reddit: "#f97316",
  spotify_community: "#8b5cf6", twitter_x: "#06b6d4",
};

const SENTIMENT_COLORS: Record<string, string> = {
  very_negative: "#ef4444", negative: "#f97316", neutral: "#6b7280",
  positive: "#22c55e", very_positive: "#1DB954",
};

const SEGMENT_COLORS: Record<string, string> = {
  active_explorer_stuck: "#ec4899", background_listener: "#6b7280",
  mood_regulator: "#8b5cf6", identity_listener: "#f59e0b",
  socially_led_discoverer: "#06b6d4", new_user: "#22c55e", unclear: "#374151",
};

const SEGMENT_LABELS: Record<string, string> = {
  active_explorer_stuck: "Explorer (Stuck)", background_listener: "Background",
  mood_regulator: "Mood Regulator", identity_listener: "Identity",
  socially_led_discoverer: "Social", new_user: "New User", unclear: "Unclear",
};

const SOURCE_LABELS: Record<string, string> = {
  app_store: "App Store", play_store: "Play Store", reddit: "Reddit",
  spotify_community: "Community", twitter_x: "Twitter/X",
};

const DEMO_THEMES = [
  { id: "1", cluster_id: 0, theme_name: "Algorithm Never Evolves", theme_description: "Users feel recommendations stagnate despite changing listening behavior", review_count: 423, cross_source_count: 5, confidence_level: "high", trend_direction: "growing", representative_quote: "My Discover Weekly has been recommending the same type of songs for months now" },
  { id: "2", cluster_id: 1, theme_name: "Genre Echo Chamber", theme_description: "Users trapped in narrow genre bubbles", review_count: 312, cross_source_count: 4, confidence_level: "high", trend_direction: "growing", representative_quote: "I'm stuck in an indie rock bubble" },
  { id: "3", cluster_id: 2, theme_name: "Lost Trust in Recommendations", theme_description: "Repeated bad suggestions eroded confidence", review_count: 267, cross_source_count: 4, confidence_level: "high", trend_direction: "stable", representative_quote: "I've given Discover Weekly so many chances" },
  { id: "4", cluster_id: 3, theme_name: "Mood Context Blindness", theme_description: "Algorithm ignores emotional context", review_count: 198, cross_source_count: 3, confidence_level: "medium", trend_direction: "stable", representative_quote: "I'm trying to study and Spotify recommends dance tracks" },
  { id: "5", cluster_id: 4, theme_name: "Overwhelming Choice Paralysis", theme_description: "Too many options lead to decision fatigue", review_count: 156, cross_source_count: 3, confidence_level: "medium", trend_direction: "declining", representative_quote: "50 different playlists and I can't choose" },
];

const DEMO_DETAIL: ThemeDetail = {
  id: "1", theme_name: "Algorithm Never Evolves", theme_description: "Users feel recommendations stagnate despite changing listening behavior and exploring new genres",
  representative_quote: "My Discover Weekly has been recommending the same type of songs for months now",
  review_count: 423, cross_source_count: 5, confidence_level: "high", trend_direction: "growing",
  source_breakdown: { app_store: 95, play_store: 87, reddit: 132, spotify_community: 56, twitter_x: 53 },
  segment_breakdown: { active_explorer_stuck: 287, mood_regulator: 68, background_listener: 38, identity_listener: 18, unclear: 12 },
  sentiment_breakdown: { very_negative: 142, negative: 178, neutral: 52, positive: 35, very_positive: 16 },
  monthly_trend: { "2025-07": 28, "2025-08": 32, "2025-09": 35, "2025-10": 41, "2025-11": 38, "2025-12": 45, "2026-01": 52, "2026-02": 48, "2026-03": 55, "2026-04": 49 },
  top_quotes: [
    { quote: "My Discover Weekly has been recommending the same type of songs for months now", full_body: "Full review text...", source: "app_store", date: "2026-03-15", rating: 2, sentiment: "negative", segment: "active_explorer_stuck" },
    { quote: "The algorithm never evolves. I started listening to jazz 3 months ago", full_body: "Full review...", source: "reddit", date: "2026-04-02", rating: null, sentiment: "very_negative", segment: "active_explorer_stuck" },
    { quote: "Haven't found a single new artist through Spotify in over 6 months", full_body: "Full review...", source: "play_store", date: "2026-05-10", rating: 1, sentiment: "very_negative", segment: "active_explorer_stuck" },
  ],
};

const TOOLTIP_STYLE = { background: "#1a1a2e", border: "1px solid #2a2a3e", borderRadius: "8px", color: "#f0f0f5", fontSize: "13px" };

export default function ThemesPage() {
  const [themes, setThemes] = useState<any[]>(DEMO_THEMES);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ThemeDetail | null>(null);
  const [activeTab, setActiveTab] = useState<"charts" | "quotes" | "reviews">("charts");

  useEffect(() => {
    fetchThemes().then(d => setThemes(d.themes || DEMO_THEMES)).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedId) {
      setActiveTab("charts");
      fetchTheme(selectedId).then(setDetail).catch(() => setDetail(DEMO_DETAIL));
    }
  }, [selectedId]);

  const d = detail || DEMO_DETAIL;
  const sourceData = Object.entries(d.source_breakdown).map(([k, v]) => ({ name: SOURCE_LABELS[k] || k.replace("_", " "), value: v, fill: SOURCE_COLORS[k] || "#6b7280" }));
  const segmentData = Object.entries(d.segment_breakdown).map(([k, v]) => ({ name: SEGMENT_LABELS[k] || k.replace(/_/g, " "), value: v, fill: SEGMENT_COLORS[k] || "#6b7280" }));
  const sentimentData = Object.entries(d.sentiment_breakdown).map(([k, v]) => ({ name: k.replace("_", " "), value: v, color: SENTIMENT_COLORS[k] || "#6b7280" }));
  const trendData = Object.entries(d.monthly_trend).map(([month, count]) => ({ month: month.slice(5), count }));

  const trendBadge = d.trend_direction === "growing" ? "badge-green" : d.trend_direction === "declining" ? "badge-red" : "badge-gray";
  const trendIcon = d.trend_direction === "growing" ? "↑" : d.trend_direction === "declining" ? "↓" : "→";

  return (
    <div className="max-w-[1400px] mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold flex items-center gap-2 mb-2">
          <Layers size={24} className="text-[var(--color-accent-green)]" />
          Theme Explorer
        </h1>
        <p className="text-sm text-[var(--color-text-secondary)]">
          Deep-dive into identified themes from user feedback across all sources
        </p>
      </div>

      <div className="flex gap-6">
        {/* Theme List */}
        <div className="w-[320px] shrink-0 space-y-2">
          {themes.map(t => (
            <button
              key={t.id}
              onClick={() => setSelectedId(t.id)}
              className={`w-full text-left p-4 rounded-xl border transition-all ${
                selectedId === t.id
                  ? "border-[var(--color-accent-green)] bg-[var(--color-bg-card-hover)]"
                  : "border-[var(--color-border)] bg-[var(--color-bg-card)] hover:border-[var(--color-border-hover)]"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm">{t.theme_name}</span>
                <ChevronRight size={14} className="text-[var(--color-text-muted)]" />
              </div>
              <p className="text-[11px] text-[var(--color-text-muted)] mt-1 line-clamp-2">{t.theme_description}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-[var(--color-text-muted)]">{t.review_count} reviews</span>
                <span className="badge badge-green text-[10px]">{t.cross_source_count} sources</span>
                <span className={`badge ${trendBadge} text-[10px]`}>{trendIcon} {t.trend_direction}</span>
              </div>
            </button>
          ))}
        </div>

        {/* Detail Panel */}
        <div className="flex-1 space-y-6">
          {/* Header Card */}
          <div className="glass-card p-6">
            <h2 className="text-xl font-bold mb-2">{d.theme_name}</h2>
            <p className="text-sm text-[var(--color-text-secondary)] mb-4">{d.theme_description}</p>
            <div className="flex gap-3 flex-wrap">
              <span className="badge badge-green">{d.review_count} reviews</span>
              <span className="badge badge-purple">{d.cross_source_count} sources</span>
              <span className="badge badge-blue">{d.confidence_level} confidence</span>
              <span className={`badge ${trendBadge}`}>{trendIcon} {d.trend_direction}</span>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex gap-1 p-1 bg-[var(--color-bg-card)] rounded-lg border border-[var(--color-border)] w-fit">
            {(["charts", "quotes", "reviews"] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  activeTab === tab
                    ? "bg-[var(--color-accent-green)] text-white"
                    : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
                }`}
              >
                {tab === "charts" ? "Analytics" : tab === "quotes" ? "Quotes" : "Reviews"}
              </button>
            ))}
          </div>

          {/* Charts Tab */}
          {activeTab === "charts" && (
            <div className="space-y-6 animate-fade-in">
              {/* Source + Segment Charts */}
              <div className="dashboard-grid dashboard-grid-2">
                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold mb-3">Reviews by Source</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={sourceData}>
                      <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} />
                      <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
                      <Tooltip contentStyle={TOOLTIP_STYLE} />
                      <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                        {sourceData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold mb-3">Reviews by Segment</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={segmentData} layout="vertical">
                      <XAxis type="number" tick={{ fill: "#9ca3af", fontSize: 11 }} />
                      <YAxis dataKey="name" type="category" width={90} tick={{ fill: "#9ca3af", fontSize: 10 }} />
                      <Tooltip contentStyle={TOOLTIP_STYLE} />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {segmentData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Sentiment + Trend */}
              <div className="dashboard-grid dashboard-grid-2">
                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold mb-3">Sentiment Breakdown</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={sentimentData} cx="50%" cy="50%" innerRadius={40} outerRadius={75} paddingAngle={3} dataKey="value">
                        {sentimentData.map((e, i) => <Cell key={i} fill={e.color} />)}
                      </Pie>
                      <Tooltip contentStyle={TOOLTIP_STYLE} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex flex-wrap justify-center gap-3 mt-2">
                    {sentimentData.map((s, i) => (
                      <span key={i} className="flex items-center gap-1 text-[10px] text-[var(--color-text-muted)]">
                        <span className="w-2 h-2 rounded-full" style={{ background: s.color }} />
                        {s.name} ({s.value})
                      </span>
                    ))}
                  </div>
                </div>

                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold mb-3">Monthly Trend</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={trendData}>
                      <XAxis dataKey="month" tick={{ fill: "#9ca3af", fontSize: 11 }} />
                      <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
                      <Tooltip contentStyle={TOOLTIP_STYLE} />
                      <Line type="monotone" dataKey="count" stroke="#1DB954" strokeWidth={2} dot={{ fill: "#1DB954", r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* Quotes Tab */}
          {activeTab === "quotes" && (
            <div className="glass-card p-6 animate-fade-in">
              <h3 className="text-sm font-semibold mb-4">Representative Quotes ({d.top_quotes.length})</h3>
              <div className="space-y-3">
                {d.top_quotes.map((q, i) => (
                  <div key={i} className="quote-card">
                    <p className="text-sm italic mb-2">&ldquo;{q.quote}&rdquo;</p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`badge source-${q.source} text-[10px]`}>{SOURCE_LABELS[q.source] || q.source.replace("_", " ")}</span>
                      <span className={`badge ${q.sentiment?.includes("negative") ? "badge-red" : "badge-gray"} text-[10px]`}>
                        {q.sentiment?.replace("_", " ")}
                      </span>
                      {q.segment && (
                        <span className="badge badge-purple text-[10px]">
                          {SEGMENT_LABELS[q.segment] || q.segment}
                        </span>
                      )}
                      {q.rating && <span className="text-[11px] text-[var(--color-text-muted)]">★ {q.rating}/5</span>}
                      {q.date && <span className="text-[11px] text-[var(--color-text-muted)]">{q.date}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reviews Tab (placeholder table from real data) */}
          {activeTab === "reviews" && (
            <div className="glass-card p-6 animate-fade-in">
              <h3 className="text-sm font-semibold mb-4">Linked Reviews</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)]">
                      <th className="text-left py-3 px-3 text-[var(--color-text-muted)] font-medium text-xs">Source</th>
                      <th className="text-left py-3 px-3 text-[var(--color-text-muted)] font-medium text-xs">Quote</th>
                      <th className="text-left py-3 px-3 text-[var(--color-text-muted)] font-medium text-xs">Sentiment</th>
                      <th className="text-left py-3 px-3 text-[var(--color-text-muted)] font-medium text-xs">Segment</th>
                      <th className="text-left py-3 px-3 text-[var(--color-text-muted)] font-medium text-xs">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.top_quotes.map((q, i) => (
                      <tr key={i} className="border-b border-[var(--color-border)] hover:bg-[var(--color-bg-card-hover)] transition-colors">
                        <td className="py-3 px-3">
                          <span className={`badge source-${q.source} text-[10px]`}>
                            {SOURCE_LABELS[q.source] || q.source}
                          </span>
                        </td>
                        <td className="py-3 px-3 max-w-[400px]">
                          <p className="text-xs truncate">{q.quote}</p>
                        </td>
                        <td className="py-3 px-3">
                          <span className={`badge ${q.sentiment?.includes("negative") ? "badge-red" : "badge-gray"} text-[10px]`}>
                            {q.sentiment?.replace("_", " ")}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <span className="text-xs">{SEGMENT_LABELS[q.segment] || q.segment || "—"}</span>
                        </td>
                        <td className="py-3 px-3">
                          <span className="text-xs text-[var(--color-text-muted)]">{q.date || "—"}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
