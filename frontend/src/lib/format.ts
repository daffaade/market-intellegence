import type { IntelligenceSnapshot, SignalMatrixPoint } from '../types/api';

export type Direction = IntelligenceSnapshot['direction'];

export const formatMarketCap = (cap: number): string => {
  if (cap >= 1e12) return `Rp ${(cap / 1e12).toLocaleString('id-ID', { maximumFractionDigits: 1 })} T`;
  return `Rp ${(cap / 1e9).toLocaleString('id-ID', { maximumFractionDigits: 0 })} M`;
};

export const formatScore = (n: number): string =>
  Number.isInteger(n) ? String(n) : n.toFixed(1);

export const formatDateTime = (value: string): string => {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString('id-ID', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const directionLabel: Record<Direction, string> = {
  BULLISH: 'Bullish',
  BEARISH: 'Bearish',
  NEUTRAL: 'Netral'
};

export const confidenceLabel: Record<IntelligenceSnapshot['confidence'], string> = {
  HIGH: 'Tinggi',
  MEDIUM: 'Sedang',
  LOW: 'Rendah'
};

export const riskLevelLabel: Record<IntelligenceSnapshot['risk_level'], string> = {
  LOW: 'Rendah',
  MODERATE: 'Sedang',
  HIGH: 'Tinggi',
  CRITICAL: 'Kritis'
};

/** Verbal band for an opportunity score, so the label always matches the number. */
export const opportunityBand = (score: number): string => {
  if (score >= 80) return 'Kuat';
  if (score >= 65) return 'Cukup kuat';
  if (score >= 50) return 'Moderat';
  return 'Lemah';
};

// Quadrant thresholds for the opportunity-vs-risk matrix.
export const OPP_THRESHOLD = 60;
export const RISK_THRESHOLD = 50;

export const quadrantOf = (opp: number, risk: number): SignalMatrixPoint['quadrant'] => {
  if (opp >= OPP_THRESHOLD) return risk < RISK_THRESHOLD ? 'PRIME_VALUE' : 'HIGH_GROWTH';
  return risk < RISK_THRESHOLD ? 'CONSERVATIVE' : 'WARNING_ZONE';
};

export const quadrantLabel: Record<SignalMatrixPoint['quadrant'], string> = {
  PRIME_VALUE: 'Peluang tinggi, risiko rendah',
  HIGH_GROWTH: 'Peluang tinggi, risiko tinggi',
  CONSERVATIVE: 'Peluang rendah, risiko rendah',
  WARNING_ZONE: 'Peluang rendah, risiko tinggi'
};

export const quadrantShort: Record<SignalMatrixPoint['quadrant'], string> = {
  PRIME_VALUE: 'Prime',
  HIGH_GROWTH: 'Spekulatif',
  CONSERVATIVE: 'Defensif',
  WARNING_ZONE: 'Waspada'
};
