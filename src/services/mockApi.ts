import type {
  ResponseWrapper,
  Company,
  IntelligenceSnapshot,
  MarketOverview,
  ScreenerFilter,
  HealthStatus,
  PeerComparisonItem
} from '../types/api';
import {
  MOCK_COMPANIES,
  MOCK_INTELLIGENCE,
  MOCK_MARKET_OVERVIEW
} from './mockData';

// Storage key for data source preference
const DUMMY_STORAGE_KEY = 'marketidex_use_dummy_data';

// Determine initial state: defaults to false (Backend Live) since backend is ready, or loads user preference
let useDummyData = localStorage.getItem(DUMMY_STORAGE_KEY) === 'true';

export const isDummyMode = (): boolean => useDummyData;

export const setDummyMode = (enabled: boolean): void => {
  useDummyData = enabled;
  localStorage.setItem(DUMMY_STORAGE_KEY, String(enabled));
  window.dispatchEvent(new CustomEvent('marketidex_datasource_changed', { detail: { useDummy: enabled } }));
};

// API Configuration (defaults to Go backend port 8080 or custom env)
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080').replace(/\/+$/, '');

export const getApiBaseUrl = (): string => API_BASE_URL;

/**
 * Where the most recent data came from. 'fallback' means backend mode is on but
 * the backend failed and mock data was served instead — the UI surfaces this so
 * simulated numbers are never mistaken for live ones.
 */
export type DataOrigin = 'dummy' | 'backend' | 'fallback';
export const DATA_ORIGIN_EVENT = 'marketidex_data_origin';

const markOrigin = (origin: DataOrigin): void => {
  window.dispatchEvent(new CustomEvent<DataOrigin>(DATA_ORIGIN_EVENT, { detail: origin }));
};

function screenLocally(filter: ScreenerFilter): IntelligenceSnapshot[] {
  let results = Object.values(MOCK_INTELLIGENCE);

  if (filter.sector) {
    results = results.filter((item) => {
      const company = MOCK_COMPANIES[item.symbol];
      return company && company.sector.toLowerCase() === filter.sector?.toLowerCase();
    });
  }
  if (filter.min_opportunity !== undefined) {
    results = results.filter((item) => item.opportunity_score >= (filter.min_opportunity || 0));
  }
  if (filter.max_risk !== undefined) {
    results = results.filter((item) => item.risk_score <= (filter.max_risk ?? 100));
  }
  if (filter.must_have_divergence) {
    results = results.filter((item) => item.divergence_detected || item.is_anomaly);
  }
  return results;
}

/**
 * Universal HTTP helper with timeout.
 */
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<ResponseWrapper<T>> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 4000);

  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      const errJson = await res.json().catch(() => null);
      return errJson || { status: 'error', message: `HTTP ${res.status}: ${res.statusText}` };
    }

    const json = await res.json();
    return json;
  } catch (err: any) {
    clearTimeout(timeoutId);
    return {
      status: 'error',
      message: err.name === 'AbortError' 
        ? 'Request timeout ke backend (melebihi 4 detik)' 
        : `Gagal terhubung ke backend (${API_BASE_URL}): Pastikan server Go sedang berjalan.`
    };
  }
}

/**
 * Normalizes backend intelligence payload so frontend components render seamlessly
 * (e.g. converting 'Bullish' to 'BULLISH', guaranteeing array fields)
 */
function normalizeIntelligence(raw: any): IntelligenceSnapshot {
  if (!raw) return raw;
  return {
    ...raw,
    direction: String(raw.direction || 'NEUTRAL').toUpperCase() as any,
    confidence: String(raw.confidence || 'MEDIUM').toUpperCase() as any,
    risk_level: String(raw.risk_level || 'LOW').toUpperCase() as any,
    positive_factors: Array.isArray(raw.positive_factors) ? raw.positive_factors : [],
    negative_factors: Array.isArray(raw.negative_factors) ? raw.negative_factors : [],
    supporting_factors: Array.isArray(raw.supporting_factors) ? raw.supporting_factors : [],
    evidence: Array.isArray(raw.evidence) ? raw.evidence : [],
    what_changed: Array.isArray(raw.what_changed) ? raw.what_changed : [],
    peer_comparison: Array.isArray(raw.peer_comparison) ? raw.peer_comparison : [],
    ai_research_summary: raw.ai_research_summary || '',
    disclaimer: raw.disclaimer || 'Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual).'
  };
}

function normalizeMarketOverview(raw: any): MarketOverview {
  if (!raw) return raw;
  return {
    top_opportunities: (raw.top_opportunities || []).map(normalizeIntelligence),
    top_risks: (raw.top_risks || []).map(normalizeIntelligence),
    detected_anomalies: (raw.detected_anomalies || []).map(normalizeIntelligence),
    sector_summary: raw.sector_summary || []
  };
}

export const apiService = {
  /**
   * 1. GET /api/v1/health
   * Cek Status & Konfigurasi Server (AI Provider, Model, Mock Mode)
   */
  async getHealth(): Promise<ResponseWrapper<HealthStatus>> {
    // Health check can always ping the backend directly to inform the inspector
    const res = await fetchApi<HealthStatus>('/api/v1/health');
    if (res.status === 'success' && res.data) {
      return res;
    }

    if (useDummyData) {
      return {
        status: 'success',
        data: {
          status: 'simulated',
          ai_provider: 'mock-local',
          ai_model: 'gemini-3.5-flash (simulated)',
          mock_mode: true,
          version: 'v1.0.0-dummy-mode'
        }
      };
    }

    return res;
  },

  /**
   * 2. GET /api/v1/companies
   * Ambil seluruh daftar emiten IDX
   */
  async getCompanies(): Promise<ResponseWrapper<Company[]>> {
    if (useDummyData) {
      return {
        status: 'success',
        data: Object.values(MOCK_COMPANIES)
      };
    }

    const res = await fetchApi<Company[]>('/api/v1/companies');
    if (res.status === 'success' && res.data) {
      return res;
    }

    // If backend returns error, return fallback with notification
    return {
      status: 'success',
      data: Object.values(MOCK_COMPANIES)
    };
  },

  /**
   * 3. GET /api/v1/companies/{symbol}
   * Ambil detail profil spesifik 1 emiten
   */
  async getCompany(symbol: string): Promise<ResponseWrapper<Company>> {
    const cleanSym = symbol.toUpperCase().trim();

    if (useDummyData) {
      markOrigin('dummy');
      const company = MOCK_COMPANIES[cleanSym];
      if (!company) {
        return { status: 'error', message: `Company ${cleanSym} not found in dummy data` };
      }
      return { status: 'success', data: company };
    }

    const res = await fetchApi<Company>(`/api/v1/companies/${cleanSym}`);
    if (res.status === 'success' && res.data) {
      markOrigin('backend');
      return res;
    }
    markOrigin('fallback');

    // If backend fails or emiten not yet in backend DB, gracefully fall back to local mock data
    const fallback = MOCK_COMPANIES[cleanSym];
    if (fallback) {
      return { status: 'success', data: fallback };
    }

    return res;
  },

  /**
   * 4. GET /api/v1/companies/{symbol}/intelligence
   * AI Intelligence Snapshot lengkap (skor, bukti, what changed, peers, narasi riset AI)
   */
  async getIntelligence(symbol: string): Promise<ResponseWrapper<IntelligenceSnapshot>> {
    const cleanSym = symbol.toUpperCase().trim();

    if (useDummyData) {
      const intel = MOCK_INTELLIGENCE[cleanSym] || { ...MOCK_INTELLIGENCE.BBCA, symbol: cleanSym };
      return { status: 'success', data: intel };
    }

    const res = await fetchApi<any>(`/api/v1/companies/${cleanSym}/intelligence`);
    if (res.status === 'success' && res.data) {
      return {
        status: 'success',
        data: normalizeIntelligence(res.data)
      };
    }

    // Backend does not have this emiten yet
    markOrigin('fallback');
    const fallback = MOCK_INTELLIGENCE[cleanSym] || { ...MOCK_INTELLIGENCE.BBCA, symbol: cleanSym };
    return { status: 'success', data: fallback };
  },

  /**
   * 5. GET /api/v1/companies/{symbol}/anomalies
   * Fokus deteksi anomali & divergensi emiten
   */
  async getAnomalies(symbol: string): Promise<ResponseWrapper<any>> {
    const cleanSym = symbol.toUpperCase().trim();

    if (useDummyData) {
      const intel = MOCK_INTELLIGENCE[cleanSym] || MOCK_INTELLIGENCE.BBCA;
      return {
        status: 'success',
        data: {
          symbol: cleanSym,
          is_anomaly: intel.is_anomaly,
          anomaly_score: intel.anomaly_score,
          divergence_detected: intel.divergence_detected,
          evidence: intel.evidence,
          factors: [...intel.positive_factors, ...intel.negative_factors]
        }
      };
    }

    const res = await fetchApi<any>(`/api/v1/companies/${cleanSym}/anomalies`);
    if (res.status === 'success' && res.data) {
      return res;
    }

    const intel = MOCK_INTELLIGENCE[cleanSym] || MOCK_INTELLIGENCE.BBCA;
    return {
      status: 'success',
      data: {
        symbol: cleanSym,
        is_anomaly: intel.is_anomaly,
        anomaly_score: intel.anomaly_score,
        divergence_detected: intel.divergence_detected,
        evidence: intel.evidence,
        factors: [...intel.positive_factors, ...intel.negative_factors]
      }
    };
  },

  /**
   * 6. GET /api/v1/companies/{symbol}/peers
   * Komparasi valuasi & metrik vs peer median
   */
  async getPeers(symbol: string): Promise<ResponseWrapper<PeerComparisonItem[]>> {
    const cleanSym = symbol.toUpperCase().trim();

    if (useDummyData) {
      const intel = MOCK_INTELLIGENCE[cleanSym] || MOCK_INTELLIGENCE.BBCA;
      return {
        status: 'success',
        data: intel.peer_comparison || []
      };
    }

    const res = await fetchApi<PeerComparisonItem[]>(`/api/v1/companies/${cleanSym}/peers`);
    if (res.status === 'success' && res.data) {
      return res;
    }

    const intel = MOCK_INTELLIGENCE[cleanSym] || MOCK_INTELLIGENCE.BBCA;
    return {
      status: 'success',
      data: intel.peer_comparison || []
    };
  },

  /**
   * 7. GET /api/v1/market/overview
   * Dashboard ikhtisar pasar (top opportunities, top risks, anomalies, sector summary)
   */
  async getMarketOverview(): Promise<ResponseWrapper<MarketOverview>> {
    if (useDummyData) {
      return {
        status: 'success',
        data: MOCK_MARKET_OVERVIEW
      };
    }

    const res = await fetchApi<any>('/api/v1/market/overview');
    if (res.status === 'success' && res.data) {
      markOrigin('backend');
      return {
        status: 'success',
        data: normalizeMarketOverview(res.data)
      };
    }

    markOrigin('fallback');
    return {
      status: 'success',
      data: MOCK_MARKET_OVERVIEW
    };
  },

  /**
   * 8. POST /api/v1/screener
   * Intelligent Screener dengan kriteria filter
   */
  async runScreener(filter: ScreenerFilter): Promise<ResponseWrapper<IntelligenceSnapshot[]>> {
    if (useDummyData) {
      markOrigin('dummy');
      return { status: 'success', data: screenLocally(filter) };
    }

    const res = await fetchApi<any[]>('/api/v1/screener', {
      method: 'POST',
      body: JSON.stringify(filter)
    });
    if (res.status === 'success' && res.data) {
      return {
        status: 'success',
        data: res.data.map(normalizeIntelligence)
      };
    }

    markOrigin('fallback');
    return { status: 'success', data: screenLocally(filter) };
  }
};
