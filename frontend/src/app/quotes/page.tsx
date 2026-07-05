"use client";

import { useEffect, useState, useCallback } from "react";
import { Quote as QuoteIcon, Copy, Bookmark, Check, Filter, X, Plus, FolderOpen } from "lucide-react";
import { fetchQuotes, fetchCollections, createCollection, addToCollection, Quote } from "@/lib/api";

const SOURCE_LABELS: Record<string, string> = {
  app_store: "App Store", play_store: "Play Store", reddit: "Reddit",
  spotify_community: "Community", twitter_x: "Twitter/X",
};

const SENTIMENT_LABELS: Record<string, string> = {
  very_negative: "Very Negative", negative: "Negative", neutral: "Neutral",
  positive: "Positive", very_positive: "Very Positive",
};

const SEGMENT_LABELS: Record<string, string> = {
  active_explorer_stuck: "Explorer (Stuck)", background_listener: "Background",
  mood_regulator: "Mood Regulator", identity_listener: "Identity",
  socially_led_discoverer: "Social Discoverer", new_user: "New User", unclear: "Unclear",
};

const CATEGORY_LABELS: Record<string, string> = {
  algorithm_staleness: "Algorithm Staleness", choice_overload: "Choice Overload",
  trust_erosion: "Trust Erosion", mood_mismatch: "Mood Mismatch",
  interface_friction: "Interface Friction", lack_of_context: "Lack of Context",
  genre_bubble: "Genre Bubble", social_disconnect: "Social Disconnect",
};

const DEMO_QUOTES: Quote[] = [
  { id: "1", key_frustration_phrase: "My Discover Weekly has been recommending the same type of songs for months now. I've been listening to completely different genres but Spotify doesn't seem to care.", full_body: "Full review text...", source: "app_store", published_at: "2026-03-15T00:00:00Z", rating: 2, sentiment: "negative", segment: "active_explorer_stuck", unmet_need: "Recommendations that evolve with my taste", primary_complaint_category: "algorithm_staleness" },
  { id: "2", key_frustration_phrase: "I'm stuck in an indie rock bubble. I listen to other genres too but Spotify only recommends variations of the same thing.", full_body: "Full review text...", source: "reddit", published_at: "2026-04-02T00:00:00Z", rating: null, sentiment: "very_negative", segment: "active_explorer_stuck", unmet_need: "Break out of genre bubble", primary_complaint_category: "genre_bubble" },
  { id: "3", key_frustration_phrase: "I've given Discover Weekly so many chances and it keeps disappointing. I've completely stopped checking it. Trust is gone.", full_body: "Full review text...", source: "play_store", published_at: "2026-05-10T00:00:00Z", rating: 1, sentiment: "very_negative", segment: "active_explorer_stuck", unmet_need: "Algorithm that learns from feedback", primary_complaint_category: "trust_erosion" },
  { id: "4", key_frustration_phrase: "I'm trying to study and Spotify recommends high-energy dance tracks. Read the room, algorithm.", full_body: "Full review text...", source: "twitter_x", published_at: "2026-04-18T00:00:00Z", rating: null, sentiment: "negative", segment: "mood_regulator", unmet_need: "Context-aware recommendations", primary_complaint_category: "mood_mismatch" },
  { id: "5", key_frustration_phrase: "There are SO many playlists on Spotify I don't even know where to start. Daily Mix 1 through 6, Discover Weekly, Release Radar... it's overwhelming.", full_body: "Full review text...", source: "spotify_community", published_at: "2026-03-28T00:00:00Z", rating: null, sentiment: "negative", segment: "new_user", unmet_need: "One perfect playlist instead of many", primary_complaint_category: "choice_overload" },
  { id: "6", key_frustration_phrase: "I discover most of my music from friends and TikTok, not from Spotify. The social features on Spotify are basically dead.", full_body: "Full review text...", source: "reddit", published_at: "2026-05-22T00:00:00Z", rating: null, sentiment: "negative", segment: "socially_led_discoverer", unmet_need: "Social discovery features that work", primary_complaint_category: "social_disconnect" },
];

export default function QuotesPage() {
  const [quotes, setQuotes] = useState<Quote[]>(DEMO_QUOTES);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({ source: "", sentiment: "", segment: "", category: "" });
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Collections state
  const [collections, setCollections] = useState<any[]>([]);
  const [showCollections, setShowCollections] = useState(false);
  const [saveTarget, setSaveTarget] = useState<string | null>(null);
  const [newCollName, setNewCollName] = useState("");
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  const loadQuotes = useCallback(async () => {
    try {
      const cleanFilters: Record<string, any> = { page, page_size: 20 };
      if (filters.source) cleanFilters.source = filters.source;
      if (filters.sentiment) cleanFilters.sentiment = filters.sentiment;
      if (filters.segment) cleanFilters.segment = filters.segment;

      const d = await fetchQuotes(cleanFilters);
      setQuotes(d.quotes || DEMO_QUOTES);
      setTotal(d.total || 0);
    } catch {
      setQuotes(DEMO_QUOTES);
      setTotal(DEMO_QUOTES.length);
    }
  }, [filters, page]);

  useEffect(() => { loadQuotes(); }, [loadQuotes]);

  useEffect(() => {
    fetchCollections().then(d => setCollections(d.collections || [])).catch(() => {});
  }, []);

  const handleCopy = (quote: Quote) => {
    const formatted = `"${quote.key_frustration_phrase}"\n— ${SOURCE_LABELS[quote.source] || quote.source}${quote.rating ? ` (★ ${quote.rating}/5)` : ""}, ${quote.published_at ? new Date(quote.published_at).toLocaleDateString() : ""}`;
    navigator.clipboard.writeText(formatted);
    setCopiedId(quote.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSaveToCollection = async (collectionId: string, quoteId: string) => {
    try {
      await addToCollection(collectionId, [quoteId]);
      setSaveSuccess(quoteId);
      setSaveTarget(null);
      setTimeout(() => setSaveSuccess(null), 2000);
      // Refresh collections
      fetchCollections().then(d => setCollections(d.collections || [])).catch(() => {});
    } catch { /* noop */ }
  };

  const handleCreateCollection = async () => {
    if (!newCollName.trim()) return;
    try {
      const coll = await createCollection(newCollName.trim());
      setCollections(prev => [...prev, { ...coll, item_count: 0 }]);
      setNewCollName("");
    } catch { /* noop */ }
  };

  const sentimentBadgeClass = (s: string) => {
    if (s.includes("very_negative")) return "badge-red";
    if (s.includes("negative")) return "badge-orange";
    if (s.includes("positive")) return "badge-green";
    return "badge-gray";
  };

  const hasActiveFilters = filters.source || filters.sentiment || filters.segment || filters.category;
  const totalPages = Math.ceil(total / 20);

  return (
    <div className="max-w-[1100px] mx-auto">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 mb-2">
            <QuoteIcon size={24} className="text-[var(--color-accent-green)]" />
            Quote Library
          </h1>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Browse, filter, and copy verbatim user quotes for decks, interview guides, and stakeholder docs
          </p>
        </div>
        <button
          onClick={() => setShowCollections(!showCollections)}
          className="btn-secondary flex items-center gap-2"
        >
          <FolderOpen size={14} />
          Collections {collections.length > 0 && `(${collections.length})`}
        </button>
      </div>

      <div className="flex gap-6">
        {/* Main Content */}
        <div className="flex-1">
          {/* Filter Toggle */}
          <div className="mb-6">
            <button onClick={() => setShowFilters(!showFilters)} className="btn-secondary flex items-center gap-2">
              <Filter size={14} />
              {showFilters ? "Hide Filters" : "Show Filters"}
              {hasActiveFilters && <span className="w-2 h-2 rounded-full bg-[var(--color-accent-green)]" />}
            </button>

            {showFilters && (
              <div className="mt-4 glass-card p-4 flex flex-wrap gap-3 animate-fade-in">
                <select
                  value={filters.source}
                  onChange={(e) => { setFilters({ ...filters, source: e.target.value }); setPage(1); }}
                  className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text-primary)]"
                >
                  <option value="">All Sources</option>
                  {Object.entries(SOURCE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
                <select
                  value={filters.sentiment}
                  onChange={(e) => { setFilters({ ...filters, sentiment: e.target.value }); setPage(1); }}
                  className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text-primary)]"
                >
                  <option value="">All Sentiments</option>
                  {Object.entries(SENTIMENT_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
                <select
                  value={filters.segment}
                  onChange={(e) => { setFilters({ ...filters, segment: e.target.value }); setPage(1); }}
                  className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text-primary)]"
                >
                  <option value="">All Segments</option>
                  {Object.entries(SEGMENT_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
                <select
                  value={filters.category}
                  onChange={(e) => { setFilters({ ...filters, category: e.target.value }); setPage(1); }}
                  className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text-primary)]"
                >
                  <option value="">All Categories</option>
                  {Object.entries(CATEGORY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
                {hasActiveFilters && (
                  <button onClick={() => { setFilters({ source: "", sentiment: "", segment: "", category: "" }); setPage(1); }} className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-accent-green)] flex items-center gap-1">
                    <X size={12} /> Clear all
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Results count */}
          {total > 0 && (
            <p className="text-xs text-[var(--color-text-muted)] mb-4">{total} quotes found</p>
          )}

          {/* Quotes List */}
          <div className="space-y-4 stagger-children">
            {quotes.map((q) => (
              <div key={q.id} className="quote-card group">
                <p
                  className="text-[15px] leading-relaxed mb-3 cursor-pointer"
                  onClick={() => setExpandedId(expandedId === q.id ? null : q.id)}
                >
                  &ldquo;{q.key_frustration_phrase}&rdquo;
                </p>

                {expandedId === q.id && q.full_body && q.full_body !== q.key_frustration_phrase && (
                  <div className="mb-3 p-3 bg-[var(--color-bg-secondary)] rounded-lg border border-[var(--color-border)] animate-fade-in">
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Full review:</p>
                    <p className="text-sm text-[var(--color-text-secondary)]">{q.full_body}</p>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`badge source-${q.source} text-[10px]`}>
                      {SOURCE_LABELS[q.source] || q.source}
                    </span>
                    <span className={`badge ${sentimentBadgeClass(q.sentiment)} text-[10px]`}>
                      {SENTIMENT_LABELS[q.sentiment] || q.sentiment}
                    </span>
                    {q.segment && (
                      <span className="badge badge-purple text-[10px]">
                        {SEGMENT_LABELS[q.segment] || q.segment}
                      </span>
                    )}
                    {q.rating && (
                      <span className="text-[11px] text-[var(--color-text-muted)]">★ {q.rating}/5</span>
                    )}
                    {q.published_at && (
                      <span className="text-[11px] text-[var(--color-text-muted)]">
                        {new Date(q.published_at).toLocaleDateString()}
                      </span>
                    )}
                    {q.primary_complaint_category && (
                      <span className="badge badge-gray text-[10px]">
                        {q.primary_complaint_category.replace(/_/g, " ")}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleCopy(q)}
                      className="p-2 rounded-lg hover:bg-[var(--color-bg-card-hover)] text-[var(--color-text-muted)] hover:text-[var(--color-accent-green)] transition-all"
                      title="Copy quote"
                    >
                      {copiedId === q.id ? <Check size={14} className="text-[var(--color-accent-green)]" /> : <Copy size={14} />}
                    </button>
                    <button
                      onClick={() => setSaveTarget(saveTarget === q.id ? null : q.id)}
                      className="p-2 rounded-lg hover:bg-[var(--color-bg-card-hover)] text-[var(--color-text-muted)] hover:text-[var(--color-accent-purple)] transition-all"
                      title="Save to collection"
                    >
                      {saveSuccess === q.id ? <Check size={14} className="text-[var(--color-accent-purple)]" /> : <Bookmark size={14} />}
                    </button>
                  </div>
                </div>

                {/* Save to collection dropdown */}
                {saveTarget === q.id && (
                  <div className="mt-3 p-3 bg-[var(--color-bg-secondary)] rounded-lg border border-[var(--color-border)] animate-fade-in">
                    <p className="text-xs text-[var(--color-text-muted)] mb-2">Save to collection:</p>
                    <div className="space-y-1">
                      {collections.map(c => (
                        <button
                          key={c.id}
                          onClick={() => handleSaveToCollection(c.id, q.id)}
                          className="w-full text-left px-3 py-2 text-sm rounded-lg hover:bg-[var(--color-bg-card-hover)] transition-colors"
                        >
                          {c.name} <span className="text-[var(--color-text-muted)]">({c.item_count} items)</span>
                        </button>
                      ))}
                      {collections.length === 0 && (
                        <p className="text-xs text-[var(--color-text-muted)]">No collections yet — create one from the panel</p>
                      )}
                    </div>
                  </div>
                )}

                {q.unmet_need && (
                  <div className="mt-3 pt-3 border-t border-[var(--color-border)]">
                    <span className="text-[11px] text-[var(--color-text-muted)]">Unmet need: </span>
                    <span className="text-xs text-[var(--color-accent-purple)]">{q.unmet_need}</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Empty State */}
          {quotes.length === 0 && (
            <div className="text-center py-16">
              <QuoteIcon size={48} className="text-[var(--color-text-muted)] mx-auto mb-4 opacity-30" />
              <p className="text-sm text-[var(--color-text-muted)]">No quotes match your filters</p>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              <button
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="btn-secondary disabled:opacity-30"
              >
                Previous
              </button>
              <span className="flex items-center px-4 text-sm text-[var(--color-text-secondary)]">
                Page {page} of {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
                className="btn-secondary disabled:opacity-30"
              >
                Next
              </button>
            </div>
          )}
        </div>

        {/* Collections Sidebar */}
        {showCollections && (
          <div className="w-[280px] shrink-0 animate-slide-in">
            <div className="glass-card p-5 sticky top-8">
              <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                <FolderOpen size={16} className="text-[var(--color-accent-purple)]" />
                Saved Collections
              </h3>

              {/* Create new */}
              <div className="flex gap-2 mb-4">
                <input
                  value={newCollName}
                  onChange={(e) => setNewCollName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreateCollection()}
                  placeholder="New collection name..."
                  className="flex-1 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-xs text-[var(--color-text-primary)]"
                />
                <button
                  onClick={handleCreateCollection}
                  disabled={!newCollName.trim()}
                  className="p-2 rounded-lg bg-[var(--color-accent-purple)] text-white hover:opacity-90 transition-opacity disabled:opacity-30"
                >
                  <Plus size={14} />
                </button>
              </div>

              {/* Collections list */}
              <div className="space-y-2">
                {collections.map(c => (
                  <div key={c.id} className="p-3 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg">
                    <p className="text-sm font-medium">{c.name}</p>
                    <p className="text-[11px] text-[var(--color-text-muted)]">
                      {c.item_count} quotes • {c.created_at ? new Date(c.created_at).toLocaleDateString() : ""}
                    </p>
                    {c.description && (
                      <p className="text-[11px] text-[var(--color-text-secondary)] mt-1">{c.description}</p>
                    )}
                  </div>
                ))}
                {collections.length === 0 && (
                  <p className="text-xs text-[var(--color-text-muted)] text-center py-4">
                    Create a collection to save quotes for stakeholder presentations
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
