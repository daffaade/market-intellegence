import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add root directory to sys.path for clean multi-package imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Pipeline imports
from data_sectors.caching import SectorsPipeline
from y_finance_data.cachingyfinance import YFinancePipeline
from unified_data.cachingunified import UnifiedDataCache, UnifiedCacheTier


class DiscrepancyDetector:
    """
    Detects significant differences between overlapping data points
    from Sectors API and yFinance API.
    """
    DISCREPANCY_THRESHOLD_PCT = 10.0  # 10% discrepancy threshold

    @classmethod
    def check_discrepancy(cls, field: str, val_sectors: Any, val_yf: Any) -> Optional[dict]:
        """Compares numeric fields and returns discrepancy record if diff > threshold."""
        if val_sectors is None or val_yf is None:
            return None

        if isinstance(val_sectors, (int, float)) and isinstance(val_yf, (int, float)):
            if val_sectors == 0 and val_yf == 0:
                return None
            base = abs(val_sectors) if val_sectors != 0 else abs(val_yf)
            diff = abs(val_sectors - val_yf)
            diff_pct = (diff / base) * 100.0

            if diff_pct > cls.DISCREPANCY_THRESHOLD_PCT:
                return {
                    "field": field,
                    "sectors_value": val_sectors,
                    "yfinance_value": val_yf,
                    "diff_pct": round(diff_pct, 2),
                    "flag": "SIGNIFICANT_DISCREPANCY",
                    "note": f"Difference of {diff_pct:.1f}% between Sectors and yFinance for {field}"
                }
        return None


class UnifiedDataMerger:
    """
    Merges and resolves overlapping data from Sectors API (current/short-term)
    and yFinance API (long-term/additional) into 11 organized schema categories.
    """

    @classmethod
    def merge(
        cls,
        symbol: str,
        sectors_data: Dict[str, Any],
        yf_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[dict], Dict[str, Any]]:
        """
        Builds the 11 organized sections:
        1. company_data
        2. valuation_data
        3. peer_data
        4. forecast_data
        5. ownership_data
        6. institutional_data
        7. insider_data
        8. historical_data
        9. dividend_data
        10. financial_data
        11. market_data

        Returns:
            Tuple of (organized_dataset, discrepancies_list, availability_meta)
        """
        clean_symbol = symbol.replace(".JK", "").upper()
        yf_symbol = f"{clean_symbol}.JK"

        discrepancies = []

        # 1. Extract sub-categories from both sources
        s_val = sectors_data.get("valuation", {})
        y_val = yf_data.get("valuation", {})

        s_peer = sectors_data.get("peer", {})
        y_peer = yf_data.get("peer", {})

        s_fc = sectors_data.get("future_forecast", {})
        y_fc = yf_data.get("future_forecast", {})

        s_inst = sectors_data.get("institutional_transactions", {})
        y_inst = yf_data.get("institutional_transactions", {})

        s_exec_sh = sectors_data.get("executive_shareholdings", {})
        y_exec_sh = yf_data.get("executive_shareholdings", {})

        s_maj_sh = sectors_data.get("major_shareholders", {})
        y_maj_sh = yf_data.get("major_shareholders", {})

        s_sh_comp = sectors_data.get("shareholder_composition", {})
        y_sh_comp = yf_data.get("shareholder_composition", {})

        s_div = sectors_data.get("dividend", {})
        y_div = yf_data.get("dividend", {})

        s_exec = sectors_data.get("executives", {})
        y_exec = yf_data.get("executives", {})

        s_price = sectors_data.get("historical_price", {})
        y_price = yf_data.get("historical_price", {})

        # Check Discrepancies on key metrics
        disc_price = DiscrepancyDetector.check_discrepancy("close_price", s_price.get("close"), y_price.get("close"))
        if disc_price:
            discrepancies.append(disc_price)

        disc_fpe = DiscrepancyDetector.check_discrepancy("forward_pe", s_val.get("forward_pe"), y_val.get("forward_pe"))
        if disc_fpe:
            discrepancies.append(disc_fpe)

        disc_mcap = DiscrepancyDetector.check_discrepancy("market_cap", s_peer.get("market_cap"), y_peer.get("market_cap"))
        if disc_mcap:
            discrepancies.append(disc_mcap)

        # -------------------------------------------------------------
        # Section 1: COMPANY DATA
        # -------------------------------------------------------------
        company_data = {
            "symbol": clean_symbol,
            "yfinance_symbol": yf_symbol,
            "company_name": s_peer.get("company_name") or y_peer.get("company_name"),
            "sector": y_peer.get("sector") or "General",
            "industry": y_peer.get("industry") or "General",
            "currency": y_peer.get("currency", "IDR"),
            "summary": y_peer.get("summary"),
            "source_primary": "Sectors API",
            "source_supporting": "yFinance API"
        }

        # -------------------------------------------------------------
        # Section 2: VALUATION DATA
        # -------------------------------------------------------------
        valuation_data = {
            # Prioritize Sectors API for primary Indonesian forward PE & intrinsic value
            "forward_pe": s_val.get("forward_pe") if s_val.get("forward_pe") is not None else y_val.get("forward_pe"),
            "trailing_pe": y_val.get("trailing_pe") or s_peer.get("pe_ttm"),
            "intrinsic_value": s_val.get("intrinsic_value") if s_val.get("intrinsic_value") is not None else y_val.get("intrinsic_value"),
            "price_to_book": y_val.get("price_to_book"),
            "enterprise_to_revenue": y_val.get("enterprise_to_revenue"),
            "enterprise_to_ebitda": y_val.get("enterprise_to_ebitda"),
            "peg_ratio": y_val.get("peg_ratio"),
            "enterprise_value": y_val.get("enterprise_value"),
            "sample_historical_valuation": s_val.get("sample_historical_valuation"),
            "fifty_two_week_high": y_val.get("fifty_two_week_high"),
            "fifty_two_week_low": y_val.get("fifty_two_week_low"),
            "source_resolution": "Sectors API prioritized for forward_pe & intrinsic_value; yFinance cover-additional metrics"
        }

        # -------------------------------------------------------------
        # Section 3: PEER DATA
        # -------------------------------------------------------------
        peer_data = {
            "peer_company_name": s_peer.get("company_name") or y_peer.get("company_name"),
            "market_cap": s_peer.get("market_cap") if s_peer.get("market_cap") is not None else y_peer.get("market_cap"),
            "pe_ttm": s_peer.get("pe_ttm") if s_peer.get("pe_ttm") is not None else y_peer.get("pe_ttm"),
            "total_assets": s_peer.get("total_assets"),
            "total_liabilities": s_peer.get("total_liabilities"),
            "total_equity": s_peer.get("total_equity"),
            "total_revenue": s_peer.get("total_revenue"),
            "net_income": s_peer.get("net_income"),
            "sector": y_peer.get("sector"),
            "industry": y_peer.get("industry")
        }

        # -------------------------------------------------------------
        # Section 4: FORECAST DATA
        # -------------------------------------------------------------
        forecast_data = {
            # Sectors forecast
            "estimate_year": s_fc.get("estimate_year") or y_fc.get("estimate_year"),
            "eps_estimate": s_fc.get("eps_estimate") if s_fc.get("eps_estimate") is not None else y_fc.get("eps_estimate"),
            "revenue_estimate": s_fc.get("revenue_estimate") if s_fc.get("revenue_estimate") is not None else y_fc.get("revenue_estimate"),
            # yFinance analyst target metrics
            "target_mean_price": y_fc.get("target_mean_price"),
            "target_high_price": y_fc.get("target_high_price"),
            "target_low_price": y_fc.get("target_low_price"),
            "target_median_price": y_fc.get("target_median_price"),
            "eps_growth": y_fc.get("eps_growth"),
            "revenue_growth": y_fc.get("revenue_growth"),
            "recommendation_key": y_fc.get("recommendation_key")
        }

        # -------------------------------------------------------------
        # Section 5: OWNERSHIP DATA
        # -------------------------------------------------------------
        ownership_data = {
            # Sectors major shareholders & whales
            "major_shareholder_name": s_maj_sh.get("name") or y_maj_sh.get("name"),
            "major_shareholder_percentage": s_maj_sh.get("share_percentage") if s_maj_sh.get("share_percentage") is not None else y_maj_sh.get("share_percentage"),
            "major_shareholder_shares": s_maj_sh.get("share_amount") or y_maj_sh.get("share_amount"),
            "major_shareholder_value": s_maj_sh.get("share_value") or y_maj_sh.get("share_value"),
            "whale_investor": s_sh_comp.get("sample_whale_investor"),
            "conglomerate_group": s_sh_comp.get("sample_conglomerate_group"),
            "insiders_percent_held": y_sh_comp.get("insiders_percent_held"),
            "institutions_percent_held": y_sh_comp.get("institutions_percent_held"),
            "breakdown": y_maj_sh.get("breakdown", {})
        }

        # -------------------------------------------------------------
        # Section 6: INSTITUTIONAL DATA
        # -------------------------------------------------------------
        institutional_data = {
            # Sectors top buyers/sellers & flow
            "transaction_date": s_inst.get("date") or y_inst.get("date"),
            "sample_buyer": s_inst.get("sample_buyer"),
            "sample_seller": s_inst.get("sample_seller"),
            # yFinance institutional / fund holdings
            "top_holder_name": y_inst.get("holder"),
            "top_holder_shares": y_inst.get("shares"),
            "top_holder_value": y_inst.get("value"),
            "top_holder_pct_held": y_inst.get("pct_held"),
            "top_holder_pct_change": y_inst.get("pct_change")
        }

        # -------------------------------------------------------------
        # Section 7: INSIDER DATA
        # -------------------------------------------------------------
        insider_data = {
            # Executive shareholdings (Sectors prioritized)
            "executive_name": s_exec_sh.get("name") or y_exec_sh.get("name") or s_exec.get("name") or y_exec.get("name"),
            "position": s_exec_sh.get("position") or y_exec_sh.get("position") or s_exec.get("position") or y_exec.get("position"),
            "share_percentage": s_exec_sh.get("share_percentage") if s_exec_sh.get("share_percentage") is not None else y_exec_sh.get("share_percentage"),
            "share_amount": s_exec_sh.get("share_amount") or y_exec_sh.get("share_amount"),
            "age": y_exec.get("age") or y_exec_sh.get("age"),
            "exercised_value": y_exec.get("exercised_value") or y_exec_sh.get("exercised_value"),
            "unexercised_value": y_exec.get("unexercised_value") or y_exec_sh.get("unexercised_value")
        }

        # -------------------------------------------------------------
        # Section 8: HISTORICAL DATA
        # -------------------------------------------------------------
        historical_data = {
            "date": s_price.get("date") or y_price.get("date"),
            "open": s_price.get("open") if s_price.get("open") is not None else y_price.get("open"),
            "high": s_price.get("high") if s_price.get("high") is not None else y_price.get("high"),
            "low": s_price.get("low") if s_price.get("low") is not None else y_price.get("low"),
            "close": s_price.get("close") if s_price.get("close") is not None else y_price.get("close"),
            "volume": s_price.get("volume") if s_price.get("volume") is not None else y_price.get("volume"),
            "dividends": y_price.get("dividends", 0.0),
            "stock_splits": y_price.get("stock_splits", 0.0),
            "source": "Sectors API (Primary) + yFinance (Extended)"
        }

        # -------------------------------------------------------------
        # Section 9: DIVIDEND DATA
        # -------------------------------------------------------------
        s_div_inner = s_div.get("data", {}) if isinstance(s_div.get("data"), dict) else {}
        dividend_data = {
            "year": s_div.get("year"),
            "total_dividend": s_div_inner.get("total_dividend") or y_div.get("dividend_rate"),
            "breakdown": s_div_inner.get("breakdown", []),
            "dividend_yield": y_div.get("dividend_yield"),
            "payout_ratio": y_div.get("payout_ratio"),
            "trailing_annual_dividend_rate": y_div.get("trailing_annual_dividend_rate"),
            "trailing_annual_dividend_yield": y_div.get("trailing_annual_dividend_yield"),
            "five_year_avg_dividend_yield": y_div.get("five_year_avg_dividend_yield"),
            "ex_dividend_date": y_div.get("ex_dividend_date"),
            "recent_dividends": y_div.get("recent_dividends", [])
        }

        # -------------------------------------------------------------
        # Section 10: FINANCIAL DATA
        # -------------------------------------------------------------
        financial_data = {
            "total_assets": s_peer.get("total_assets"),
            "total_liabilities": s_peer.get("total_liabilities"),
            "total_equity": s_peer.get("total_equity"),
            "total_revenue": s_peer.get("total_revenue") or s_fc.get("revenue_estimate"),
            "net_income": s_peer.get("net_income"),
            "eps_estimate": s_fc.get("eps_estimate") or y_fc.get("eps_estimate"),
            "revenue_estimate": s_fc.get("revenue_estimate") or y_fc.get("revenue_estimate")
        }

        # -------------------------------------------------------------
        # Section 11: MARKET DATA
        # -------------------------------------------------------------
        market_data = {
            "symbol": clean_symbol,
            "latest_price": s_price.get("close") if s_price.get("close") is not None else y_price.get("close"),
            "open": s_price.get("open") if s_price.get("open") is not None else y_price.get("open"),
            "high": s_price.get("high") if s_price.get("high") is not None else y_price.get("high"),
            "low": s_price.get("low") if s_price.get("low") is not None else y_price.get("low"),
            "close": s_price.get("close") if s_price.get("close") is not None else y_price.get("close"),
            "volume": s_price.get("volume") if s_price.get("volume") is not None else y_price.get("volume"),
            "market_cap": s_peer.get("market_cap") if s_peer.get("market_cap") is not None else y_peer.get("market_cap"),
            "currency": y_peer.get("currency", "IDR"),
            "fifty_two_week_high": y_val.get("fifty_two_week_high"),
            "fifty_two_week_low": y_val.get("fifty_two_week_low"),
            "as_of_date": s_price.get("date") or y_price.get("date")
        }

        organized_dataset = {
            "company_data": company_data,
            "valuation_data": valuation_data,
            "peer_data": peer_data,
            "forecast_data": forecast_data,
            "ownership_data": ownership_data,
            "institutional_data": institutional_data,
            "insider_data": insider_data,
            "historical_data": historical_data,
            "dividend_data": dividend_data,
            "financial_data": financial_data,
            "market_data": market_data
        }

        # Check overall data availability
        missing_sections = [
            sec for sec, data in organized_dataset.items()
            if not any(v is not None for v in data.values() if isinstance(data, dict))
        ]

        availability_meta = {
            "status": "WARNING" if missing_sections else "OKAY",
            "available_sections_count": len(organized_dataset) - len(missing_sections),
            "total_sections": len(organized_dataset),
            "missing_sections": missing_sections,
            "discrepancies_count": len(discrepancies)
        }

        return organized_dataset, discrepancies, availability_meta


class UnifiedPipeline:
    """
    Unified Data Layer Pipeline coordinating:
    - Sectors Data Pipeline (Current & Short-Term Data)
    - yFinance Data Pipeline (Long-Term & Additional Data)
    - Discrepancy Detection & Data Resolution
    - 11-Section Unified Organization
    - Multi-tier Disk and Memory Caching
    """

    def __init__(self):
        self.sectors_pipeline = SectorsPipeline()
        self.yfinance_pipeline = YFinancePipeline()
        self.cache = UnifiedDataCache()

    def get_unified_dataset(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        clean_symbol = symbol.replace(".JK", "").upper()
        yf_symbol = f"{clean_symbol}.JK"

        # Check unified cache first
        if not force_refresh:
            cached_unified = self.cache.get(clean_symbol)
            if cached_unified:
                return {
                    "source": "UNIFIED_CACHE_HIT",
                    "symbol": clean_symbol,
                    "status": "READY",
                    "data": cached_unified,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

        # 1. Fetch from Sectors Data Pipeline (Current & Short-Term)
        try:
            sectors_res = self.sectors_pipeline.get_dataset(clean_symbol, force_refresh=force_refresh)
            sectors_data = sectors_res.get("data", {})
        except Exception as e:
            sectors_data = {}

        # 2. Fetch from yFinance Data Pipeline (Long-Term & Additional)
        try:
            yf_res = self.yfinance_pipeline.get_dataset(yf_symbol, force_refresh=force_refresh)
            yf_data = yf_res.get("data", {})
        except Exception as e:
            yf_data = {}

        # 3. Merge, Resolve Overlaps, and Detect Discrepancies
        organized_data, discrepancies, avail_meta = UnifiedDataMerger.merge(
            symbol=clean_symbol,
            sectors_data=sectors_data,
            yf_data=yf_data
        )

        # 4. Save to Unified Cache
        self.cache.set(clean_symbol, organized_data, discrepancies=discrepancies)

        # 5. Build Final Payload for Intelligence Engine
        return {
            "source": "UNIFIED_MULTI_SOURCE_PIPELINE",
            "symbol": clean_symbol,
            "status": "READY" if avail_meta["status"] == "OKAY" else "DATA_WARNING",
            "availability": avail_meta,
            "discrepancies": discrepancies,
            "data": organized_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
