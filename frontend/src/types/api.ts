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
  /** Price/volume and foreign-flow based accumulation signal. */
  smart_money?: {
    state: 'Accumulation' | 'Distribution' | 'Neutral' | string;
    score: number;
    confidence: string;
    evidence: string[] | null;
  };
  catalysts?: {
    catalyst_score: number;
    net_direction: string;
    events: Array<{ date: string; type: string; direction: string; strength: number; evidence: string[] }> | null;
  };
  /** Set by the backend when the AI engine was unreachable and this is heuristic placeholder data. */
  is_fallback?: boolean;
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

// ─── Company fundamentals (Sectors company report) ─────────────
export interface GrowthData {
  year: string;
  revenue: number; // billions IDR
  net_profit: number; // billions IDR
  margin: number; // percentage
}

export interface DividendHistory {
  year: string;
  dividend_per_share: number;
  yield_percent: number;
  /** null when it cannot be derived reliably (e.g. DPS not split-adjusted). */
  payout_ratio: number | null;
}

export interface Shareholder {
  name: string;
  share_percentage: number;
  category: "INSTITUTIONAL" | "MANAGEMENT" | "RETAIL" | "GOVERNMENT" | "TREASURY";
}

export interface KeyExecutive {
  name: string;
  position: string;
  share_amount: number | null;
  share_percentage: number | null;
}

/** Net change in shares held by an institution over the reporting period. */
export interface SmartMoneyTransaction {
  institution: string;
  action: "ACCUMULATE" | "DISTRIBUTE";
  shares_change: number;
}

export interface InstitutionalFlowPoint {
  date: string;
  net_shares: number;
}

export interface CompanyFundamentals {
  symbol: string;
  growth_data: GrowthData[];
  dividends: DividendHistory[];
  shareholders: Shareholder[];
  executives: KeyExecutive[];
  smart_money: SmartMoneyTransaction[];
  smart_money_as_of?: string;
  institutional_flow: InstitutionalFlowPoint[];
  /** Daily net foreign flow in IDR for the last ~90 days (Sectors). */
  foreign_flow?: Array<{ date: string; net_idr: number; foreign_share: number | null }>;
  source: string;
  fetched_at: string;
}

// ─── Live market series (yfinance via the engine) ──────────────
export interface PricePerformance {
  symbols: string[];
  /** Weekly closes (dividend-adjusted); null when a symbol did not trade that week. */
  points: Array<{ date: string } & Record<string, number | string | null>>;
  as_of: string | null;
  source: string;
}

export interface MacroSnapshotItem {
  key: string;
  name: string;
  unit: string;
  value: number;
  date: string;
  change_1m_pct: number | null;
  change_1y_pct: number | null;
  sparkline: number[];
}

/** Corporate action with an event study: abnormal return vs IHSG over [-1, +5]. */
export interface CorporateEvent {
  date: string;
  type: "DIVIDEND" | "SPLIT";
  car_pct: number | null;
  t_stat: number | null;
  p_value: number | null;
  significant: boolean;
  amount?: number;
  yield_pct?: number;
  ratio?: number;
}

export interface MacroSensitivity {
  key: string;
  label: string;
  beta: number;
  correlation: number;
  p_value: number;
  significant: boolean;
  n_weeks: number;
  move_1m_pct: number | null;
  implied_move_1m_pct: number | null;
  interpretation: string;
}

export interface PortfolioRiskReport {
  status: string;
  period: string;
  metrics: {
    portfolio_volatility: number;
    individual_volatility: Record<string, number>;
    correlation_matrix: Record<string, Record<string, number>>;
    risk_contribution: Record<string, number>;
    concentration_risk: number;
    historical_var: number;
    maximum_drawdown: number;
  };
  metadata?: Record<string, unknown>;
  disclaimer?: string;
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

export interface DataSourceStatus {
  key: string;
  label: string;
  provider: string;
  used_for: string;
  items: number | null;
  newest: string | null;
  oldest: string | null;
  ttl_hours: number;
}

// ─── Sector intelligence ───────────────────────────────────────
export interface SectorConstituent {
  symbol: string;
  rs_20d: number | null;
  rs_60d: number | null;
  above_ma50: boolean;
  return_20d: number | null;
}

export interface SectorRow {
  sector: string;
  label: string;
  n_constituents: number;
  sentiment: 'Bullish' | 'Bearish' | 'Neutral';
  rs_20d: number | null;
  rs_60d: number | null;
  breadth_ma50: number | null;
  rank: number;
  rank_prev: number;
  rotation: 'Menguat' | 'Melemah' | 'Stabil';
  constituents: SectorConstituent[];
  index_weekly: Array<{ date: string; value: number | null }>;
}

export interface SectorOverview {
  as_of: string;
  method: string;
  sectors: SectorRow[];
  source: string;
}

// ─── Consumer behavior ─────────────────────────────────────────
export interface CorrelationStat {
  r: number;
  p_value: number;
  significant: boolean;
  n_weeks: number;
}

export interface ConsumerBehaviorResult {
  keyword: string;
  industry: string;
  sector: string | null;
  sector_label: string | null;
  error?: string;
  available_sectors?: Array<{ key: string; label: string }>;
  search_trend?: {
    recent_4w: number;
    yoy_pct: number | null;
    vs_prev_12w_pct: number | null;
    percentile_5y: number;
    weekly: Array<{ date: string; value: number }>;
  } | null;
  correlation?: { same_period: CorrelationStat | null; search_leads_4w: CorrelationStat | null } | null;
  sector_return_60d_pct?: number | null;
  companies?: Array<{ symbol: string; revenue_growth_ttm: number | null; return_20d_pct: number }>;
  impact_signal?: { impact_score: number; impact_direction: 'Positive' | 'Negative' | 'Neutral'; confidence_level: string };
  evidence?: string[];
  data_quality_flags?: string[];
  method?: string;
  disclaimer: string;
}
