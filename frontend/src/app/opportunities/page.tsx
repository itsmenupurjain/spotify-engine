"use client";

import { useEffect, useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Target, ArrowRight } from "lucide-react";
import Link from "next/link";
import { fetchOpportunities, Opportunity } from "@/lib/api";

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

const DEMO_OPPORTUNITIES: Opportunity[] = [
  { theme_id: "1", theme_name: "Algorithm Never Evolves", frequency: 423, severity: 0.72, cross_source_score: 5, dominant_segment: "active_explorer_stuck", confidence_level: "high", trend_direction: "growing", representative_quote: "My Discover Weekly has been recommending the same type of songs for months now" },
  { theme_id: "2", theme_name: "Genre Echo Chamber", frequency: 312, severity: 0.65, cross_source_score: 4, dominant_segment: "active_explorer_stuck", confidence_level: "high", trend_direction: "growing", representative_quote: "I'm stuck in an indie rock bubble" },
  { theme_id: "3", theme_name: "Lost Trust in Recs", frequency: 267, severity: 0.78, cross_source_score: 4, dominant_segment: "active_explorer_stuck", confidence_level: "high", trend_direction: "stable", representative_quote: "Trust is gone" },
  { theme_id: "4", theme_name: "Mood Context Blindness", frequency: 198, severity: 0.55, cross_source_score: 3, dominant_segment: "mood_regulator", confidence_level: "medium", trend_direction: "stable", representative_quote: "Studying and Spotify recommends dance tracks" },
  { theme_id: "5", theme_name: "Choice Paralysis", frequency: 156, severity: 0.45, cross_source_score: 3, dominant_segment: "new_user", confidence_level: "medium", trend_direction: "declining", representative_quote: "50 playlists and I can't choose" },
  { theme_id: "6", theme_name: "Dead Social Discovery", frequency: 89, severity: 0.52, cross_source_score: 3, dominant_segment: "socially_led_discoverer", confidence_level: "medium", trend_direction: "growing", representative_quote: "I find music on TikTok, not Spotify" },
  { theme_id: "7", theme_name: "UI Hides Discovery", frequency: 134, severity: 0.48, cross_source_score: 2, dominant_segment: "new_user", confidence_level: "low", trend_direction: "stable", representative_quote: "Where did the Discover tab go?" },
  { theme_id: "8", theme_name: "Context Collapse", frequency: 112, severity: 0.61, cross_source_score: 2, dominant_segment: "mood_regulator", confidence_level: "low", trend_direction: "stable", representative_quote: "Baby shark ruined my recommendations" },
];

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-4 shadow-xl max-w-[280px]">
      <h4 className="font-semibold text-sm mb-1">{d.theme_name}</h4>
      <div className="space-y-1 text-xs text-[var(--color-text-secondary)]">
        <p>Frequency: <span className="text-[var(--color-text-primary)] font-medium">{d.frequency} reviews</span></p>
        <p>Severity: <span className="text-[var(--color-text-primary)] font-medium">{(d.severity * 100).toFixed(0)}%</span></p>
        <p>Sources: <span className="text-[var(--color-text-primary)] font-medium">{d.cross_source_score}</span></p>
        <p>Segment: <span className="text-[var(--color-text-primary)] font-medium">{SEGMENT_LABELS[d.dominant_segment]}</span></p>
      </div>
      <p className="text-[11px] italic text-[var(--color-text-muted)] mt-2 border-t border-[var(--color-border)] pt-2">
        &ldquo;{d.representative_quote}&rdquo;
      </p>
    </div>
  );
}

export default function OpportunitiesPage() {
  const [data, setData] = useState<Opportunity[]>(DEMO_OPPORTUNITIES);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  useEffect(() => {
    fetchOpportunities().then(d => setData(d.opportunities || DEMO_OPPORTUNITIES)).catch(() => {});
  }, []);

  // Sort by priority (frequency * severity)
  const sorted = [...data].sort((a, b) => b.frequency * b.severity - a.frequency * a.severity);

  return (
    <div className="max-w-[1400px] mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold flex items-center gap-2 mb-2">
          <Target size={24} className="text-[var(--color-accent-green)]" />
          Opportunity Map
        </h1>
        <p className="text-sm text-[var(--color-text-secondary)]">
          Prioritize which discovery problems to solve based on frequency, severity, and cross-source consistency
        </p>
      </div>

      {/* Bubble Chart */}
      <div className="glass-card p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-6 text-xs text-[var(--color-text-muted)]">
            <span>X: Frequency (review count)</span>
            <span>Y: Severity (avg negative sentiment)</span>
            <span>Size: Cross-source consistency</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={450}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <XAxis type="number" dataKey="frequency" name="Frequency" tick={{ fill: "#9ca3af", fontSize: 11 }} label={{ value: "Frequency →", position: "insideBottomRight", fill: "#6b7280", fontSize: 12 }} />
            <YAxis type="number" dataKey="severity" name="Severity" domain={[0, 1]} tick={{ fill: "#9ca3af", fontSize: 11 }} label={{ value: "Severity →", angle: -90, position: "insideLeft", fill: "#6b7280", fontSize: 12 }} />
            <ZAxis type="number" dataKey="cross_source_score" range={[200, 800]} name="Sources" />
            <Tooltip content={<CustomTooltip />} />
            <Scatter data={data}>
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={SEGMENT_COLORS[entry.dominant_segment] || "#6b7280"}
                  fillOpacity={hoveredId === entry.theme_id ? 1 : 0.7}
                  stroke={hoveredId === entry.theme_id ? "#fff" : "transparent"}
                  strokeWidth={2}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>

        {/* Legend */}
        <div className="flex flex-wrap gap-4 mt-4 justify-center">
          {Object.entries(SEGMENT_LABELS).filter(([k]) => k !== "unclear").map(([key, label]) => (
            <div key={key} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ background: SEGMENT_COLORS[key] }} />
              <span className="text-xs text-[var(--color-text-muted)]">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Priority List */}
      <div className="glass-card p-6">
        <h3 className="text-sm font-semibold mb-4">Priority Ranking</h3>
        <div className="space-y-3">
          {sorted.map((opp, i) => (
            <div
              key={opp.theme_id}
              className="flex items-center gap-4 p-4 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl hover:border-[var(--color-border-hover)] transition-all"
              onMouseEnter={() => setHoveredId(opp.theme_id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <span className="text-lg font-bold text-[var(--color-accent-green)] min-w-[28px]">{i + 1}</span>
              <div className="flex-1">
                <span className="font-semibold text-sm">{opp.theme_name}</span>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5 italic">&ldquo;{opp.representative_quote}&rdquo;</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="badge badge-green text-xs">{opp.frequency} reviews</span>
                <span className="badge badge-orange text-xs">{(opp.severity * 100).toFixed(0)}% severe</span>
                <span className="badge badge-purple text-xs">{opp.cross_source_score} sources</span>
                <Link href={`/themes?id=${opp.theme_id}`}>
                  <ArrowRight size={16} className="text-[var(--color-text-muted)] hover:text-[var(--color-accent-green)]" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
