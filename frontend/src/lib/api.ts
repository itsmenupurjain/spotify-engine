/**
 * API Client — typed wrapper around all backend endpoints.
 */

import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// --- Types ---

export interface ThemeSummary {
  id: string;
  name: string;
  description: string;
  review_count: number;
  cross_source_count: number;
  confidence_level: string;
  trend_direction: string;
  representative_quote: string;
}

export interface UnmetNeed {
  need: string;
  count: number;
}

export interface DashboardSummary {
  total_raw_reviews: number;
  total_classified_reviews: number;
  sources_active: number;
  source_counts: Record<string, number>;
  last_updated: string | null;
  top_themes: ThemeSummary[];
  top_unmet_needs: UnmetNeed[];
  segment_distribution: Record<string, number>;
  sentiment_by_source: Record<string, Record<string, number>>;
}

export interface QueryResult {
  answer: string;
  evidence: { text: string; source: string; date?: string }[];
  confidence: string;
  confidence_reason: string;
  follow_up_questions: string[];
  result_count: number;
  query_time_ms: number;
  raw_results?: any[];
}

export interface ThemeDetail {
  id: string;
  theme_name: string;
  theme_description: string;
  representative_quote: string;
  review_count: number;
  cross_source_count: number;
  confidence_level: string;
  trend_direction: string;
  source_breakdown: Record<string, number>;
  segment_breakdown: Record<string, number>;
  sentiment_breakdown: Record<string, number>;
  monthly_trend: Record<string, number>;
  top_quotes: {
    quote: string;
    full_body: string;
    source: string;
    date: string | null;
    rating: number | null;
    sentiment: string;
    segment: string;
  }[];
}

export interface SegmentDetail {
  segment: string;
  total_reviews: number;
  top_complaints: { category: string; count: number }[];
  top_unmet_needs: { need: string; count: number }[];
  sentiment_distribution: Record<string, number>;
  cross_source_presence: Record<string, number>;
  jtbd_statements: string[];
  representative_quotes: {
    quote: string;
    source: string;
    date: string | null;
    rating: number | null;
    sentiment: string;
  }[];
}

export interface Opportunity {
  theme_id: string;
  theme_name: string;
  frequency: number;
  severity: number;
  cross_source_score: number;
  dominant_segment: string;
  confidence_level: string;
  trend_direction: string;
  representative_quote: string;
}

export interface Quote {
  id: string;
  key_frustration_phrase: string;
  full_body: string;
  source: string;
  published_at: string | null;
  rating: number | null;
  sentiment: string;
  segment: string;
  unmet_need: string;
  primary_complaint_category: string;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  checks: Record<string, { status: string; message?: string }>;
}

// --- API Functions ---

export async function fetchSummary(): Promise<DashboardSummary> {
  const { data } = await api.get("/synthesis/summary");
  return data;
}

export async function queryNL(query: string): Promise<QueryResult> {
  const { data } = await api.post("/query", { query });
  return data;
}

export async function fetchThemes() {
  const { data } = await api.get("/themes");
  return data;
}

export async function fetchTheme(themeId: string): Promise<ThemeDetail> {
  const { data } = await api.get(`/themes/${themeId}`);
  return data;
}

export async function fetchSegments() {
  const { data } = await api.get("/segments");
  return data;
}

export async function fetchSegment(segmentId: string): Promise<SegmentDetail> {
  const { data } = await api.get(`/segments/${segmentId}`);
  return data;
}

export async function fetchOpportunities(): Promise<{ opportunities: Opportunity[]; total: number }> {
  const { data } = await api.get("/opportunities");
  return data;
}

export async function fetchQuotes(params: Record<string, any> = {}) {
  const { data } = await api.get("/quotes", { params });
  return data;
}

export async function fetchHealth(): Promise<HealthStatus> {
  const { data } = await api.get("/health");
  return data;
}

export async function fetchCollections() {
  const { data } = await api.get("/collections");
  return data;
}

export async function createCollection(name: string, description?: string) {
  const { data } = await api.post("/collections", { name, description });
  return data;
}

export async function addToCollection(collectionId: string, reviewIds: string[], note?: string) {
  const { data } = await api.put(`/collections/${collectionId}`, { review_ids: reviewIds, note });
  return data;
}

export default api;
