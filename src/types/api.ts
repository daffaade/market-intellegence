export interface ResponseWrapper<T> {
  status: "success" | "error";
  data?: T;
  message?: string;
}

export interface HealthStatus {
  status: string;
  ai_provider?: string;
  ai_model?: string;
  mock_mode?: boolean;
  version?: string;
}

export interface Company {
  symbol: string;
  name: string;
  sector: string;
  sub_sector: string;
  market_cap: number;
  updated_at: string;
}

export interface EvidenceItem {
  metric: string;
  company_value: string;
  peer_median: string;
  position: string;
}

export interface WhatChangedItem {
  metric: string;
  previous: string;
  current: string;
  delta: string;
  impact: "HIGH_BULLISH" | "MODERATE_BULLISH" | "NEUTRAL" | "HIGH_BEARISH" | "MODERATE_BEARISH";
}

export interface PeerComparisonItem {
  metric: string;
  target: string;
  peer_median: string;
  position: "PREMIUM" | "DISCOUNT" | "FAIR";
}

export interface IntelligenceSnapshot {
  id: number;
  symbol: string;
  opportunity_score: number;
  risk_score: number;
  direction: "BULLISH" | "BEARISH" | "NEUTRAL";
  confidence: "HIGH" | "MEDIUM" | "LOW";
  risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  is_anomaly: boolean;
  anomaly_score: number;
  divergence_detected: boolean;
  positive_factors: string[];
  negative_factors: string[];
  supporting_factors: string[];
  evidence: EvidenceItem[];
  what_changed: WhatChangedItem[];
  peer_comparison: PeerComparisonItem[];
  ai_research_summary: string;
  disclaimer: string;
  is_cached: boolean;
  created_at: string;
}

export interface SectorSummary {
  sector: string;
  sentiment: "Bullish" | "Bearish" | "Neutral";
  avg_opportunity: number;
  anomaly_count: number;
}

export interface MarketOverview {
  top_opportunities: IntelligenceSnapshot[];
  top_risks: IntelligenceSnapshot[];
  detected_anomalies: IntelligenceSnapshot[];
  sector_summary: SectorSummary[];
}

export interface ScreenerFilter {
  sector?: string;
  min_opportunity?: number;
  max_risk?: number;
  must_have_divergence?: boolean;
}

// Additional UI & Analytics domain types
export interface GrowthData {
  year: string;
  revenue: number; // in Billions
  net_profit: number; // in Billions
  margin: number; // percentage
}

export interface DividendHistory {
  year: string;
  dividend_per_share: number;
  yield_percent: number;
  payout_ratio: number;
}

export interface Shareholder {
  name: string;
  share_percentage: number;
  category: "INSTITUTIONAL" | "MANAGEMENT" | "RETAIL" | "GOVERNMENT";
}

export interface KeyExecutive {
  name: string;
  position: string;
  tenure: string;
  insider_action: "BOUGHT" | "SOLD" | "HELD";
  transaction_amount?: string;
}

export interface SmartMoneyTransaction {
  date: string;
  institution: string;
  action: "ACCUMULATE" | "DISTRIBUTE";
  volume: string;
  value_idr: string;
}

export interface MacroIndicator {
  name: string;
  value: string;
  trend: "UP" | "DOWN" | "STABLE";
  correlation_with_market: string;
  impact_assessment: string;
}

export interface EventImpact {
  event_name: string;
  date: string;
  category: string;
  price_reaction_pct: number;
  market_sentiment: string;
}

export interface DisasterRisk {
  region: string;
  risk_type: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "SEVERE";
  impacted_operations: string;
  mitigation_status: string;
}

export interface PortfolioPosition {
  symbol: string;
  name: string;
  allocation_pct: number;
  sector: string;
  risk_score: number;
  opportunity_score: number;
}

// ─── Standardized Signal Output ────────────────────────────────
export interface RelatedSignal {
  signal_type: string;
  description: string;
  strength: "STRONG" | "MODERATE" | "WEAK";
}

export interface StandardizedSignalOutput {
  finding: string;
  score: {
    opportunity: number;
    risk: number;
    composite: number;
  };
  explanation: string;
  evidence: EvidenceItem[];
  related_signals: RelatedSignal[];
}

// ─── Sectors API / MCP Data Pipeline ───────────────────────────
export type PipelineStageId =
  | "RETRIEVAL"
  | "VALIDATION"
  | "NORMALIZATION"
  | "TRANSFORMATION"
  | "FEATURE_GENERATION"
  | "INTELLIGENCE_ENGINE";

export interface PipelineStage {
  id: PipelineStageId;
  label: string;
  description: string;
  status: "COMPLETED" | "PROCESSING" | "PENDING";
  data_type: string;
  duration_ms?: number;
}

// ─── Signal Matrix (2D Quadrant) ───────────────────────────────
export interface SignalMatrixPoint {
  symbol: string;
  name: string;
  sector: string;
  opportunity_score: number;
  risk_score: number;
  direction: "BULLISH" | "BEARISH" | "NEUTRAL";
  is_anomaly: boolean;
  quadrant: "PRIME_VALUE" | "HIGH_GROWTH" | "CONSERVATIVE" | "WARNING_ZONE";
}

// ─── Watchlist ─────────────────────────────────────────────────
export interface WatchlistItem {
  symbol: string;
  name: string;
  added_at: string;
}

// ─── Market Growth Timeline (Top 10 Time-Series) ───────────────
export interface MarketGrowthTimelinePoint {
  period: string; // e.g. "Okt 2025", "Nov 2025", etc.
  [symbol: string]: number | string;
}
