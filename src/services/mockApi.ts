import type {
  ResponseWrapper,
  Company,
  IntelligenceSnapshot,
  MarketOverview,
  ScreenerFilter
} from '../types/api';
import {
  MOCK_COMPANIES,
  MOCK_INTELLIGENCE,
  MOCK_MARKET_OVERVIEW
} from './mockData';

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const apiService = {
  async getCompany(symbol: string): Promise<ResponseWrapper<Company>> {
    await delay(300);
    const company = MOCK_COMPANIES[symbol.toUpperCase()];
    if (!company) {
      return {
        status: "error",
        message: `Company with symbol ${symbol} not found`
      };
    }
    return {
      status: "success",
      data: company
    };
  },

  async getIntelligence(symbol: string): Promise<ResponseWrapper<IntelligenceSnapshot>> {
    await delay(400);
    const intel = MOCK_INTELLIGENCE[symbol.toUpperCase()];
    if (!intel) {
      // Fallback for demo: return default BBCA intel with updated symbol
      const fallback = { ...MOCK_INTELLIGENCE.BBCA, symbol: symbol.toUpperCase() };
      return {
        status: "success",
        data: fallback
      };
    }
    return {
      status: "success",
      data: intel
    };
  },

  async getMarketOverview(): Promise<ResponseWrapper<MarketOverview>> {
    await delay(500);
    return {
      status: "success",
      data: MOCK_MARKET_OVERVIEW
    };
  },

  async runScreener(filter: ScreenerFilter): Promise<ResponseWrapper<IntelligenceSnapshot[]>> {
    await delay(600);
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
      results = results.filter((item) => item.risk_score <= (filter.max_risk || 100));
    }

    if (filter.must_have_divergence) {
      results = results.filter((item) => item.divergence_detected);
    }

    return {
      status: "success",
      data: results
    };
  }
};
