import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Setup sys.path
_SUB_DIR = Path(__file__).resolve().parent
_PKG_DIR = _SUB_DIR.parent
_ROOT_DIR = _PKG_DIR.parent
for _p in [str(_ROOT_DIR), str(_PKG_DIR), str(_SUB_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from data_processing.y_finance_data.cachingyfinance import YFinancePipeline, YFinanceDataCache, CacheTier
from data_processing.y_finance_data.datamineryfinance import ValidationStatus


class DataStatus:
    OKAY = "OKAY"
    WARNING = "WARNING"
    ERROR = "ERROR"


REQUIRED_CATEGORIES = [
    "valuation",
    "peer",
    "future_forecast",
    "institutional_transactions",
    "executive_shareholdings",
    "major_shareholders",
    "shareholder_composition",
    "dividend",
    "executives",
    "historical_price"
]

OPTIONAL_CATEGORIES = {
    "shareholder_composition",
    "executive_shareholdings"
}

CATEGORY_DISPLAY_NAMES = {
    "valuation": "Valuation",
    "peer": "Peer",
    "future_forecast": "Future Forecast",
    "institutional_transactions": "Institutional Trans.",
    "executive_shareholdings": "Executive Shareholding",
    "major_shareholders": "Major Shareholders",
    "shareholder_composition": "Shareholder Composition",
    "dividend": "Dividend",
    "executives": "Executives",
    "historical_price": "Historical Price"
}


class YFinanceDataProvider:
    """
    Final data retrieval provider for Intelligence Engine and analytics
    using Yahoo Finance data via yfinance.
    
    Provides:
    - get_price(ticker)
    - get_variable(ticker, variable)
    - get_all_data(ticker, print_table=True)
    - Structured table formatting with status (OKAY, WARNING, ERROR)
    """

    def __init__(self, pipeline: Optional[YFinancePipeline] = None):
        self.pipeline = pipeline or YFinancePipeline()
        self.cache = self.pipeline.cache

    def _format_summary_value(self, category: str, content: Any) -> str:
        """Helper to create human-readable single-line summary for table display."""
        if not content:
            return "data (Not Available)"

        if category == "valuation":
            fpe = content.get("forward_pe")
            iv = content.get("intrinsic_value")
            parts = []
            if fpe is not None:
                parts.append(f"Fwd P/E: {fpe}")
            if iv is not None:
                parts.append(f"Intrinsic/Target: Rp {iv:,.0f}" if isinstance(iv, (int, float)) else f"Intrinsic: {iv}")
            return " | ".join(parts) if parts else str(content)

        elif category == "peer":
            name = content.get("company_name", "")
            sector = content.get("sector", "")
            mcap = content.get("market_cap")
            mcap_str = f"Rp {mcap/1e12:,.1f}T" if isinstance(mcap, (int, float)) else str(mcap)
            return f"{name} ({sector}, MCap: {mcap_str})" if name else str(content)

        elif category == "future_forecast":
            mean_p = content.get("target_mean_price")
            eps = content.get("eps_estimate")
            yr = content.get("estimate_year")
            parts = []
            if mean_p:
                parts.append(f"Target: Rp {mean_p:,.0f}" if isinstance(mean_p, (int, float)) else f"Target: {mean_p}")
            if eps:
                parts.append(f"EPS Est: {eps}")
            if yr:
                parts.append(f"Year: {yr}")
            return " | ".join(parts) if parts else str(content)

        elif category == "institutional_transactions":
            dt = content.get("date", "")
            holder = content.get("holder", "")
            chg = content.get("pct_change")
            chg_str = f"{chg*100:.1f}%" if isinstance(chg, (int, float)) else ""
            parts = [f"Date: {dt}"] if dt else []
            if holder:
                parts.append(f"Holder: {holder}")
            if chg_str:
                parts.append(f"Change: {chg_str}")
            return " | ".join(parts) if parts else str(content)

        elif category == "executive_shareholdings":
            name = content.get("name", "")
            pos = content.get("position", "")
            return f"{name} ({pos})" if name else str(content)

        elif category == "major_shareholders":
            name = content.get("name", "Major Stakeholders")
            pct = content.get("share_percentage")
            pct_str = f"{pct*100:.2f}%" if isinstance(pct, (int, float)) else ""
            return f"{name} ({pct_str})" if pct_str else str(name)

        elif category == "shareholder_composition":
            insider = content.get("insiders_percent_held")
            inst = content.get("institutions_percent_held")
            parts = []
            if insider is not None:
                parts.append(f"Insiders: {insider*100:.2f}%")
            if inst is not None:
                parts.append(f"Institutions: {inst*100:.2f}%")
            return " | ".join(parts) if parts else "Composition available"

        elif category == "dividend":
            rate = content.get("dividend_rate")
            dy = content.get("dividend_yield")
            dy_str = f"{dy*100:.2f}%" if isinstance(dy, (int, float)) else str(dy)
            parts = []
            if rate is not None:
                parts.append(f"Rate: Rp {rate}")
            if dy is not None:
                parts.append(f"Yield: {dy_str}")
            return " | ".join(parts) if parts else str(content)

        elif category == "executives":
            name = content.get("name", "")
            pos = content.get("position", "")
            return f"{name} - {pos}" if name else str(content)

        elif category == "historical_price":
            dt = content.get("date", "")
            close_p = content.get("close")
            vol = content.get("volume")
            vol_str = f"{vol:,.0f}" if isinstance(vol, (int, float)) else str(vol)
            close_str = f"Rp {close_p:,.0f}" if isinstance(close_p, (int, float)) else str(close_p)
            return f"Date: {dt} | Close: {close_str} | Vol: {vol_str}"

        return str(content)[:60]

    def get_price(self, ticker: str) -> Dict[str, Any]:
        """
        Retrieves current / latest historical stock price.
        """
        clean_ticker = self.pipeline.miner.format_symbol(ticker)
        
        # Check cache first
        cached_price = self.cache.get(clean_ticker, "historical_price")
        if cached_price and isinstance(cached_price, dict) and cached_price.get("close") is not None:
            return {
                "status": DataStatus.OKAY,
                "ticker": clean_ticker,
                "price": cached_price.get("close"),
                "date": cached_price.get("date"),
                "source": "CACHE_HIT",
                "data": cached_price
            }

        # Run pipeline to fetch & cache
        res = self.pipeline.get_dataset(clean_ticker)
        dataset = res.get("data", {})
        price_data = dataset.get("historical_price")

        if price_data and isinstance(price_data, dict) and price_data.get("close") is not None:
            return {
                "status": DataStatus.OKAY,
                "ticker": clean_ticker,
                "price": price_data.get("close"),
                "date": price_data.get("date"),
                "source": res.get("source", "YFINANCE_API"),
                "data": price_data
            }

        return {
            "status": DataStatus.ERROR,
            "ticker": clean_ticker,
            "price": None,
            "message": f"Historical/current price not available for {clean_ticker}",
            "source": res.get("source")
        }

    def get_variable(self, ticker: str, variable: str) -> Dict[str, Any]:
        """
        Retrieves a single data category for a given ticker.
        """
        clean_ticker = self.pipeline.miner.format_symbol(ticker)
        var_clean = variable.lower().strip().replace(" ", "_")

        # Check cache first
        cached_var = self.cache.get(clean_ticker, var_clean)
        if cached_var is not None:
            return {
                "status": DataStatus.OKAY,
                "ticker": clean_ticker,
                "category": var_clean,
                "source": "CACHE_HIT",
                "data": cached_var
            }

        # Pipeline fetch
        res = self.pipeline.get_dataset(clean_ticker)
        dataset = res.get("data", {})
        var_data = dataset.get(var_clean)

        if var_data is not None:
            return {
                "status": DataStatus.OKAY,
                "ticker": clean_ticker,
                "category": var_clean,
                "source": res.get("source"),
                "data": var_data
            }

        status = DataStatus.WARNING if var_clean in OPTIONAL_CATEGORIES else DataStatus.ERROR
        return {
            "status": status,
            "ticker": clean_ticker,
            "category": var_clean,
            "source": res.get("source"),
            "data": None,
            "message": f"Category '{var_clean}' is not available for {clean_ticker}"
        }

    def get_all_data(self, ticker: str, print_table: bool = True) -> Dict[str, Any]:
        """
        Retrieves all categories and optionally prints a clean status overview table.
        """
        clean_ticker = self.pipeline.miner.format_symbol(ticker)
        res = self.pipeline.get_dataset(clean_ticker)
        dataset = res.get("data", {})
        source = res.get("source", "UNKNOWN")

        rows = []
        for cat in REQUIRED_CATEGORIES:
            content = dataset.get(cat)
            disp_name = CATEGORY_DISPLAY_NAMES.get(cat, cat.replace("_", " ").title())

            if content:
                status = DataStatus.OKAY
                summary_val = self._format_summary_value(cat, content)
            elif cat in OPTIONAL_CATEGORIES:
                status = DataStatus.WARNING
                summary_val = "data (Not Available)"
            else:
                status = DataStatus.ERROR
                summary_val = "data (Not Available)"

            rows.append({
                "category": cat,
                "display_name": disp_name,
                "status": status,
                "content": content,
                "summary": summary_val
            })

        if print_table:
            self.display_summary_table(clean_ticker, rows, source)

        return {
            "ticker": clean_ticker,
            "source": source,
            "timestamp": res.get("timestamp"),
            "categories": rows,
            "raw_dataset": dataset
        }

    def get_historical_data(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        Retrieves historical OHLCV data as a pandas DataFrame.
        """
        try:
            import yfinance as yf
            clean_sym = ticker.strip().upper()
            if not clean_sym.startswith("^") and not clean_sym.endswith(".JK"):
                sym = f"{clean_sym}.JK"
            else:
                sym = clean_sym
            df = yf.download(sym, period=period, progress=False, auto_adjust=False)
            return df
        except Exception:
            return None

    def display_summary_table(self, ticker: str, rows: List[dict], source: str):
        """Displays data in formatted table with OKAY / WARNING / ERROR tags."""
        col1_w = 26
        col2_w = 12
        col3_w = 48

        print("=" * (col1_w + col2_w + col3_w + 7))
        print(f"📊 YFINANCE DATA RETRIEVAL REPORT: {ticker.upper()} (Source: {source})")
        print("=" * (col1_w + col2_w + col3_w + 7))
        
        header = f"| {'Data Category':<{col1_w}} | {'Status':<{col2_w}} | {'Summary Value / Sample':<{col3_w}} |"
        sep = f"|{'-' * (col1_w + 2)}|{'-' * (col2_w + 2)}|{'-' * (col3_w + 2)}|"
        
        print(header)
        print(sep)

        for row in rows:
            st = row["status"]
            if st == DataStatus.OKAY:
                st_str = "OKAY"
            elif st == DataStatus.WARNING:
                st_str = "WARNING"
            else:
                st_str = "ERROR"

            name = row["display_name"][:col1_w]
            summ = row["summary"][:col3_w]
            print(f"| {name:<{col1_w}} | {st_str:<{col2_w}} | {summ:<{col3_w}} |")

        print("=" * (col1_w + col2_w + col3_w + 7))


if __name__ == "__main__":
    target_ticker = sys.argv[1] if len(sys.argv) > 1 else "BBCA.JK"
    provider = YFinanceDataProvider()

    print(f"\n🚀 Running YFinance Data Provider for {target_ticker}...\n")
    provider.get_all_data(target_ticker, print_table=True)