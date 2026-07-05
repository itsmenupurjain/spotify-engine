"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import {
  TrendingUp, TrendingDown, Minus, Database, Globe, Clock,
  ChevronDown, ChevronUp, AlertTriangle, Sparkles, Layers,
} from "lucide-react";
import { fetchSummary, DashboardSummary } from "@/lib/api";

const SOURCE_COLORS: Record<string, string> = {
  app_store: "#3b82f6",
  play_store: "#22c55e",
  reddit: "#f97316",
  spotify_community: "#8b5cf6",
  twitter_x: "#06b6d4",
};

const SOURCE_LABELS: Record<string, string> = {
  app_store: "App Store",
  play_store: "Play Store",
  reddit: "Reddit",
  spotify_community: "Community",
  twitter_x: "Twitter/X",
};

const SEGMENT_COLORS: Record<string, string> = {
  active_explorer_stuck: "#ec4899",
  background_listener: "#6b7280",
  mood_regulator: "#8b5cf6",
  identity_listener: "#f59e0b",
  socially_led_discoverer: "#06b6d4",
  new_user: "#22c55e",
  unclear: "#374151",
};

const SEGMENT_LABELS: Record<string, string> = {
  active_explorer_stuck: "Active Explorer (Stuck)",
  background_listener: "Background Listener",
  mood_regulator: "Mood Regulator",
  identity_listener: "Identity Listener",
  socially_led_discoverer: "Social Discoverer",
  new_user: "New User",
  unclear: "Unclear",
};

const SENTIMENT_COLORS: Record<string, string> = {
  very_negative: "#ef4444",
  negative: "#f97316",
  neutral: "#6b7280",
  positive: "#22c55e",
  very_positive: "#1DB954",
};

function TrendIcon({ direction }: { direction: string }) {
  if (direction === "growing") return <TrendingUp size={14} className="trend-growing" />;
  if (direction === "declining") return <TrendingDown size={14} className="trend-declining" />;
  return <Minus size={14} className="trend-stable" />;
}

// Demo data for when the API isn't connected
const DEMO_DATA: DashboardSummary = {
  total_raw_reviews: 2847,
  total_classified_reviews: 2134,
  sources_active: 5,
  source_counts: { app_store: 612, play_store: 587, reddit: 723, spotify_community: 398, twitter_x: 527 },
  last_updated: new Date().toISOString(),
  top_themes: [
    { id: "1", name: "Algorithm Never Evolves", description: "Users feel recommendations stagnate despite changing listening behavior", review_count: 423, cross_source_count: 5, confidence_level: "high", trend_direction: "growing", representative_quote: "My Discover Weekly has been recommending the same type of songs for months now" },
    { id: "2", name: "Genre Echo Chamber", description: "Users trapped in narrow genre bubbles, unable to discover across styles", review_count: 312, cross_source_count: 4, confidence_level: "high", trend_direction: "growing", representative_quote: "I'm stuck in an indie rock bubble. I listen to other genres too but Spotify only recommends variations of the same thing" },
    { id: "3", name: "Lost Trust in Recommendations", description: "Repeated bad suggestions have eroded confidence in the algorithm", review_count: 267, cross_source_count: 4, confidence_level: "high", trend_direction: "stable", representative_quote: "I've given Discover Weekly so many chances and it keeps disappointing. Trust is gone." },
    { id: "4", name: "Mood Context Blindness", description: "Algorithm ignores situational and emotional context for music selection", review_count: 198, cross_source_count: 3, confidence_level: "medium", trend_direction: "stable", representative_quote: "I'm trying to study and Spotify recommends high-energy dance tracks" },
    { id: "5", name: "Overwhelming Choice Paralysis", description: "Too many playlists and options lead to decision fatigue", review_count: 156, cross_source_count: 3, confidence_level: "medium", trend_direction: "declining", representative_quote: "I open the app wanting to find something new and I'm hit with 50 different playlists" },
    { id: "6", name: "Dead Social Discovery", description: "Users miss social features for discovering music through friends", review_count: 89, cross_source_count: 3, confidence_level: "medium", trend_direction: "growing", representative_quote: "I discover most of my music from friends and TikTok, not from Spotify" },
  ],
  top_unmet_needs: [
    { need: "Music recommendations that actually evolve with my changing taste", count: 387 },
    { need: "A way to break out of my genre bubble without random noise", count: 256 },
    { need: "Context-aware recommendations based on time and mood", count: 198 },
    { need: "Better feedback mechanism to tell the algorithm what I like", count: 167 },
    { need: "Social discovery features that actually work", count: 89 },
  ],
  segment_distribution: {
    active_explorer_stuck: 823,
    mood_regulator: 342,
    background_listener: 298,
    identity_listener: 234,
    socially_led_discoverer: 187,
    new_user: 134,
    unclear: 116,
  },
  sentiment_by_source: {
    app_store: { very_negative: 120, negative: 210, neutral: 82, positive: 130, very_positive: 70 },
    play_store: { very_negative: 98, negative: 195, neutral: 94, positive: 125, very_positive: 75 },
    reddit: { very_negative: 145, negative: 280, neutral: 98, positive: 120, very_positive: 80 },
    spotify_community: { very_negative: 85, negative: 160, neutral: 53, positive: 60, very_positive: 40 },
    twitter_x: { very_negative: 110, negative: 190, neutral: 77, positive: 95, very_positive: 55 },
  },
};

export default function IntelligenceHome() {
  const [data, setData] = useState<DashboardSummary>(DEMO_DATA);
  const [expandedTheme, setExpandedTheme] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSummary()
      .then(setData)
      .catch(() => setData(DEMO_DATA))
      .finally(() => setLoading(false));
  }, []);

  // Prepare chart data
  const segmentChartData = Object.entries(data.segment_distribution).map(([key, value]) => ({
    name: SEGMENT_LABELS[key] || key,
    value,
    color: SEGMENT_COLORS[key] || "#6b7280",
  }));

  const sentimentChartData = Object.entries(data.sentiment_by_source).map(([source, sentiments]) => ({
    source: SOURCE_LABELS[source] || source,
    ...sentiments,
  }));

  return (
    <div className="max-w-[1400px] mx-auto">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Sparkles size={24} className="text-[var(--color-accent-green)]" />
          <h1 className="text-2xl font-bold">Intelligence Dashboard</h1>
        </div>
        <p className="text-[var(--color-text-secondary)] text-sm">
          AI-powered analysis of user feedback on Spotify&apos;s music discovery features
        </p>
      </div>

      {/* Stats Bar */}
      <div className="dashboard-grid dashboard-grid-4 mb-8 stagger-children">
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-2">
            <Database size={16} className="text-[var(--color-accent-green)]" />
            <span className="stat-label">Reviews Analyzed</span>
          </div>
          <div className="stat-value">{data.total_classified_reviews.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-2">
            <Globe size={16} className="text-[var(--color-accent-blue)]" />
            <span className="stat-label">Sources Active</span>
          </div>
          <div className="stat-value">{data.sources_active}</div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={16} className="text-[var(--color-accent-orange)]" />
            <span className="stat-label">Themes Identified</span>
          </div>
          <div className="stat-value">{data.top_themes.length}</div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-2">
            <Clock size={16} className="text-[var(--color-accent-purple)]" />
            <span className="stat-label">Last Updated</span>
          </div>
          <div className="text-lg font-semibold text-[var(--color-text-primary)]">
            {data.last_updated ? new Date(data.last_updated).toLocaleDateString() : "—"}
          </div>
        </div>
      </div>

      {/* Top Themes Panel */}
      <div className="glass-card p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Layers size={18} className="text-[var(--color-accent-green)]" />
          Top Themes
        </h2>
        <div className="space-y-3 stagger-children">
          {data.top_themes.map((theme) => {
            const isExpanded = expandedTheme === theme.id;
            const pctOfTotal = data.total_classified_reviews > 0
              ? ((theme.review_count / data.total_classified_reviews) * 100).toFixed(1)
              : "0";

            return (
              <div
                key={theme.id}
                className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-4 cursor-pointer transition-all hover:border-[var(--color-border-hover)]"
                onClick={() => setExpandedTheme(isExpanded ? null : theme.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <TrendIcon direction={theme.trend_direction} />
                    <div>
                      <span className="font-semibold text-[15px]">{theme.name}</span>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-[var(--color-text-muted)]">
                          {theme.review_count} reviews ({pctOfTotal}%)
                        </span>
                        <span className="badge badge-green text-[10px]">
                          {theme.cross_source_count} sources
                        </span>
                        {theme.confidence_level === "high" && (
                          <span className="badge badge-purple text-[10px]">High Confidence</span>
                        )}
                      </div>
                    </div>
                  </div>
                  {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>

                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-[var(--color-border)] animate-fade-in">
                    <p className="text-sm text-[var(--color-text-secondary)] mb-3">
                      {theme.description}
                    </p>
                    <div className="quote-card">
                      <p className="text-sm italic text-[var(--color-text-secondary)]">
                        &ldquo;{theme.representative_quote}&rdquo;
                      </p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Two Column: Unmet Needs + Segment Distribution */}
      <div className="dashboard-grid dashboard-grid-2 mb-8">
        {/* Unmet Needs */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold mb-4">Top Unmet Needs</h2>
          <div className="space-y-3">
            {data.top_unmet_needs.map((need, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="text-lg font-bold text-[var(--color-accent-green)] min-w-[28px]">
                  {i + 1}
                </span>
                <div className="flex-1">
                  <p className="text-sm font-medium">{need.need}</p>
                  <div className="mt-1 flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-[var(--color-bg-primary)] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-[var(--color-accent-green)] to-[var(--color-accent-purple)]"
                        style={{ width: `${Math.min(100, (need.count / (data.top_unmet_needs[0]?.count || 1)) * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-[var(--color-text-muted)] min-w-[40px] text-right">
                      {need.count}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Segment Distribution */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold mb-4">User Segments</h2>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={segmentChartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={3}
                dataKey="value"
              >
                {segmentChartData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "var(--color-bg-card)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "8px",
                  color: "var(--color-text-primary)",
                  fontSize: "13px",
                }}
              />
              <Legend
                wrapperStyle={{ fontSize: "12px", color: "var(--color-text-secondary)" }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Sentiment by Source */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold mb-4">Sentiment Distribution by Source</h2>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={sentimentChartData} layout="vertical">
            <XAxis type="number" tick={{ fill: "#9ca3af", fontSize: 12 }} />
            <YAxis dataKey="source" type="category" width={100} tick={{ fill: "#9ca3af", fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                background: "var(--color-bg-card)",
                border: "1px solid var(--color-border)",
                borderRadius: "8px",
                color: "var(--color-text-primary)",
                fontSize: "13px",
              }}
            />
            <Bar dataKey="very_negative" stackId="sentiment" fill={SENTIMENT_COLORS.very_negative} name="Very Negative" />
            <Bar dataKey="negative" stackId="sentiment" fill={SENTIMENT_COLORS.negative} name="Negative" />
            <Bar dataKey="neutral" stackId="sentiment" fill={SENTIMENT_COLORS.neutral} name="Neutral" />
            <Bar dataKey="positive" stackId="sentiment" fill={SENTIMENT_COLORS.positive} name="Positive" />
            <Bar dataKey="very_positive" stackId="sentiment" fill={SENTIMENT_COLORS.very_positive} name="Very Positive" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
