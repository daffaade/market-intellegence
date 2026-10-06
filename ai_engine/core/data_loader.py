import sys
import json
from typing import Any, Dict, List, Optional

# Ensure modules from parent directory can be loaded
from pathlib import Path
CURRENT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = CURRENT_DIR.parent
ROOT_DIR = AI_ENGINE_DIR.parent
DATA_PROC_DIR = ROOT_DIR / "data_processing"
for _p in [str(ROOT_DIR), str(DATA_PROC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from data_processing.data_sectors.getdata import SectorsDataProvider
from data_processing.y_finance_data.getyfinance import YFinanceDataProvider
from data_processing.getunified import UnifiedDataProvider
try:
    from data_processing.macro_data.macro_provider import MacroDataProvider
except ImportError:
    MacroDataProvider = None


class UnifiedDataLoader:
    """
    Unified Data Access Layer to bridge Sectors Pipeline and YFinance Pipeline.
    Responsible for source routing, merging, and standardizing output format
    without re-doing any validation/normalization/caching.
    """
    def __init__(self):
        self.sectors_provider = SectorsDataProvider() if SectorsDataProvider else None
        self.yfinance_provider = YFinanceDataProvider() if YFinanceDataProvider else None
        self.unified_provider = UnifiedDataProvider()
        self.macro_provider = MacroDataProvider() if MacroDataProvider else None

    def _route_source(self, data_type: str, period: str) -> str:
        """
        Determines which source pipeline to use based on data_type and period.
        """
        # Long-term history (e.g. 5y, 10y) usually goes to yfinance
        if period in ["5y", "10y", "max"] and data_type in ["price", "financials", "dividend"]:
            return "yfinance"
        
        # Current / short-term data usually goes to sectors (which provides IDX specific context)
        # However, fallback to yfinance if not available or explicit
        return "sectors"

    def _resolve_overlap(self, val_sectors: Any, val_yfinance: Any, data_type: str) -> Dict[str, Any]:
        """
        Resolves overlap and flags discrepancies.
        """
        # Simplistic discrepancy check (can be improved)
        discrepancy = False
        
        # Return structured data
        if val_sectors is not None and val_sectors.get("status") == "OKAY":
            return {
                "value": val_sectors.get("data"),
                "source": "sectors",
                "supporting_source": "yfinance" if val_yfinance and val_yfinance.get("status") == "OKAY" else None,
                "discrepancy": discrepancy
            }
        elif val_yfinance is not None and val_yfinance.get("status") == "OKAY":
            return {
                "value": val_yfinance.get("data"),
                "source": "yfinance",
                "supporting_source": None,
                "discrepancy": False
            }
        return {
            "value": None,
            "source": None,
            "discrepancy": False
        }

    def _fetch_from_provider(self, provider, ticker: str, data_type: str) -> Dict[str, Any]:
        if not provider:
            return {"status": "ERROR", "data": None}
        if data_type == "price":
            return provider.get_price(ticker)
        else:
            return provider.get_variable(ticker, data_type)

    def _get_unified(self, ticker: str, data_type: str, period: str) -> Dict[str, Any]:
        """Core router to fetch and unify data based on period rules."""
        primary_source = self._route_source(data_type, period)
        
        if primary_source == "sectors":
            res_primary = self._fetch_from_provider(self.sectors_provider, ticker, data_type)
            res_secondary = self._fetch_from_provider(self.yfinance_provider, ticker, data_type)
            resolved = self._resolve_overlap(res_primary, res_secondary, data_type)
            if resolved.get("source") is None:
                resolved["source"] = "sectors"
            elif res_primary and res_primary.get("status") != "OKAY" and res_secondary and res_secondary.get("status") == "OKAY":
                resolved["source"] = "sectors"
                resolved["fallback_to"] = "yfinance"
            return resolved
        else:
            # yfinance prioritized
            res_primary = self._fetch_from_provider(self.yfinance_provider, ticker, data_type)
            res_secondary = self._fetch_from_provider(self.sectors_provider, ticker, data_type)
            # Reversing order for overlap resolution
            resolved = self._resolve_overlap(res_secondary, res_primary, data_type)
            # If sectors was primary in resolve_overlap, we actually want yfinance to be the main source returned
            if res_primary.get("status") == "OKAY":
                return {
                    "value": res_primary.get("data"),
                    "source": "yfinance",
                    "supporting_source": "sectors" if res_secondary.get("status") == "OKAY" else None,
                    "discrepancy": False
                }
            return resolved

    # =========================================================================
    # Required Getter Methods
    # =========================================================================

    def get_price(self, ticker: str, period: str = "current") -> Dict[str, Any]:
        return self._get_unified(ticker, "price", period)

    def get_valuation(self, ticker: str, period: str = "current") -> Dict[str, Any]:
        return self._get_unified(ticker, "valuation", period)

    def get_peers(self, ticker: str, period: str = "current") -> Dict[str, Any]:
        return self._get_unified(ticker, "peer", period)

    def get_forecast(self, ticker: str, period: str = "current") -> Dict[str, Any]:
        return self._get_unified(ticker, "future_forecast", period)

    def get_dividend(self, ticker: str, period: str = "10y") -> Dict[str, Any]:
        return self._get_unified(ticker, "dividend", period)

    def get_executives(self, ticker: str, period: str = "current") -> Dict[str, Any]:
        return self._get_unified(ticker, "executives", period)

    def get_executive_shareholdings(self, ticker: str, period: str = "current") -> Dict[str, Any]:
        return self._get_unified(ticker, "executive_shareholdings", period)

    def get_major_shareholders(self, ticker: str, period: str = "current") -> Dict[str, Any]:
        return self._get_unified(ticker, "major_shareholders", period)

    def get_shareholder_composition(self, ticker: str, period: str = "current") -> Dict[str, Any]:
        return self._get_unified(ticker, "shareholder_composition", period)

    def get_institutional_transactions(self, ticker: str, period: str = "1y") -> Dict[str, Any]:
        return self._get_unified(ticker, "institutional_transactions", period)

    def get_financials(self, ticker: str, period: str = "10y") -> Dict[str, Any]:
        return self._get_unified(ticker, "financials", period)

    def get_balance_sheet(self, ticker: str, period: str = "10y") -> Dict[str, Any]:
        return self._get_unified(ticker, "balance_sheet", period)

    def get_cash_flow(self, ticker: str, period: str = "10y") -> Dict[str, Any]:
        return self._get_unified(ticker, "cash_flow", period)

    def get_company(self, ticker: str, period: str = "current") -> Dict[str, Any]:
        return self._get_unified(ticker, "company_info", period)

    def get_sector(self, ticker: str, period: str = "current") -> Dict[str, Any]:
        return self._get_unified(ticker, "sector", period)

    def get_industry(self, ticker: str, period: str = "current") -> Dict[str, Any]:
        return self._get_unified(ticker, "industry", period)

    def get_all(self, ticker: str, period: str = "current") -> Dict[str, Dict[str, Any]]:
        """
        Convenience method to fetch a standard set of variables.
        """
        return {
            "price": self.get_price(ticker, period),
            "valuation": self.get_valuation(ticker, period),
            "peers": self.get_peers(ticker, period),
            "forecast": self.get_forecast(ticker, period)
        }

    def get_unified_dataset(self, ticker: str) -> Dict[str, Any]:
        """
        Retrieves the complete 11-section unified dataset compiled by data_processing.
        """
        if self.unified_provider:
            return self.unified_provider.get_all_data(ticker, print_table=False)
        return {}

    def get_section(self, ticker: str, section: str) -> Dict[str, Any]:
        """
        Retrieves a single organized section from data_processing.
        """
        if self.unified_provider:
            return self.unified_provider.get_section(ticker, section)
        return {}

    def get_historical_data(self, ticker: str, period: str = "1y"):
        """
        Retrieves historical OHLCV data as a pandas DataFrame via yfinance_provider.
        """
        if self.yfinance_provider and hasattr(self.yfinance_provider, "get_historical_data"):
            return self.yfinance_provider.get_historical_data(ticker, period=period)
        try:
            import yfinance as yf
            clean_sym = ticker.strip().upper()
            if not clean_sym.startswith("^") and not clean_sym.endswith(".JK"):
                sym = f"{clean_sym}.JK"
            else:
                sym = clean_sym
            return yf.download(sym, period=period, progress=False, auto_adjust=False)
        except Exception:
            return None

    def get_consumer_data(self, keyword: str, timeframe: str = 'today 12-m') -> Dict[str, Any]:
        """
        Retrieves macro economic indicators and search trends.
        """
        if self.macro_provider:
            return self.macro_provider.get_consumer_data(keyword, timeframe)
        return {}
