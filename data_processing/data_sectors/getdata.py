import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Setup sys.path
_SUB_DIR = Path(__file__).resolve().parent
_PKG_DIR = _SUB_DIR.parent
_ROOT_DIR = _PKG_DIR.parent
for _p in [str(_SUB_DIR), str(_PKG_DIR), str(_ROOT_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Correlated modules
from data_processing.data_sectors.caching import SectorsPipeline, SectorsDataCache, CacheTier
from data_processing.data_sectors.dataminer import ValidationStatus


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

# Core mandatory categories vs optional/market-dependent categories
OPTIONAL_CATEGORIES = {
    "shareholder_composition",     # Whale/conglomerates may not exist for some entities (e.g. SOEs/Danantara)
    "executive_shareholdings"      # May not be reported for all firms
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


class SectorsDataProvider:
    """
    Final data retrieval provider for Intelligence Engine and analytics.
    Implements getdata.md specifications:
    - get_price(ticker)
    - get_variable(ticker, variable)
    - get_all_data(ticker)
    - Structured table formatting with status (OKAY, WARNING, ERROR)
    """

    def __init__(self, pipeline: Optional[SectorsPipeline] = None):
        self.pipeline = pipeline or SectorsPipeline()
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
                parts.append(f"Intrinsic: Rp {iv:,.0f}" if isinstance(iv, (int, float)) else f"Intrinsic: {iv}")
            return " | ".join(parts) if parts else str(content)

        elif category == "peer":
            name = content.get("company_name", "")
            mcap = content.get("market_cap")
            pe = content.get("pe_ttm")
            mcap_str = f"Rp {mcap/1e12:,.1f}T" if isinstance(mcap, (int, float)) else str(mcap)
            return f"{name} (MCap: {mcap_str}, PE: {pe})" if name else str(content)

        elif category == "future_forecast":
            eps = content.get("eps_estimate")
            yr = content.get("estimate_year")
            rev = content.get("revenue_estimate")
            rev_str = f"Rp {rev/1e12:,.1f}T" if isinstance(rev, (int, float)) else str(rev)
            return f"Year: {yr} | EPS Est: {eps} | Rev Est: {rev_str}"

        elif category == "institutional_transactions":
            dt = content.get("date", "")
            buyer = content.get("sample_buyer", {})
            seller = content.get("sample_seller", {})
            b_name = buyer.get("name") if isinstance(buyer, dict) else None
            s_name = seller.get("name") if isinstance(seller, dict) else None
            parts = [f"Date: {dt}"]
            if b_name:
                parts.append(f"Buyer: {b_name}")
            if s_name:
                parts.append(f"Seller: {s_name}")
            return " | ".join(parts)

        elif category == "executive_shareholdings":
            name = content.get("name", "")
            pos = content.get("position", "")
            pct = content.get("share_percentage")
            pct_str = f"{pct*100:.4f}%" if isinstance(pct, (int, float)) else str(pct)
            return f"{name} ({pos}) - Stake: {pct_str}"

        elif category == "major_shareholders":
            name = content.get("name", "")
            pct = content.get("share_percentage")
            pct_str = f"{pct*100:.2f}%" if isinstance(pct, (int, float)) else str(pct)
            return f"{name} - Stake: {pct_str}"

        elif category == "shareholder_composition":
            whale = content.get("sample_whale_investor")
            cong = content.get("sample_conglomerate_group")
            parts = []
            if whale:
                parts.append(f"Whale: {whale}")
            if cong:
                parts.append(f"Group: {cong}")
            return " | ".join(parts) if parts else str(content)

        elif category == "dividend":
            yr = content.get("year", "")
            data_inner = content.get("data", {})
            total = data_inner.get("total_dividend") if isinstance(data_inner, dict) else None
            yield_val = data_inner.get("total_yield") if isinstance(data_inner, dict) else None
            yield_str = f"{yield_val*100:.2f}%" if isinstance(yield_val, (int, float)) else str(yield_val)
            return f"Year: {yr} | Total: Rp {total} | Yield: {yield_str}"

        elif category == "executives":
            name = content.get("name", "")
            pos = content.get("position", "")
            return f"{pos}: {name}" if pos else name

        elif category == "historical_price":
            dt = content.get("date", "")
            close = content.get("close")
            vol = content.get("volume")
            vol_str = f"{vol/1e6:,.1f}M" if isinstance(vol, (int, float)) else str(vol)
            return f"Date: {dt} | Close: {close} | Vol: {vol_str}"

        return json.dumps(content, ensure_ascii=False)

    def get_price(self, ticker: str) -> Dict[str, Any]:
        """
        Retrieves current / latest stock price.
        - Checks cache first
        - If not in cache, processes pipeline and returns price
        """
        clean_ticker = ticker.replace(".JK", "").upper()

        # Check cached price
        cached_price = self.cache.get(clean_ticker, "historical_price")
        if cached_price and isinstance(cached_price, dict) and "close" in cached_price:
            return {
                "ticker": clean_ticker,
                "source": "CACHE_HIT",
                "status": DataStatus.OKAY,
                "price": cached_price.get("close"),
                "date": cached_price.get("date"),
                "data": cached_price
            }

        # Fetch through pipeline
        full_data = self.get_all_data(clean_ticker)
        hp = full_data.get("historical_price")
        
        if hp and isinstance(hp, dict) and "close" in hp:
            return {
                "ticker": clean_ticker,
                "source": full_data.get("source", "PIPELINE"),
                "status": full_data.get("status_per_category", {}).get("historical_price", DataStatus.OKAY),
                "price": hp.get("close"),
                "date": hp.get("date"),
                "data": hp
            }

        return {
            "ticker": clean_ticker,
            "status": DataStatus.ERROR,
            "message": f"Price data not available for {clean_ticker}"
        }

    def get_variable(self, ticker: str, variable: str) -> Dict[str, Any]:
        """
        Retrieves a specific variable or category for a ticker.
        Checks variable availability and returns data with corresponding processing status.
        """
        clean_ticker = ticker.replace(".JK", "").upper()
        clean_var = variable.lower().strip().replace(" ", "_")

        # 1. First check if whole dataset or category exists in cache
        cached_cat = self.cache.get(clean_ticker, clean_var)
        if cached_cat is not None:
            return {
                "ticker": clean_ticker,
                "variable": clean_var,
                "status": DataStatus.OKAY,
                "source": "CACHE_HIT",
                "data": cached_cat
            }

        # 2. If not in cache or searching for sub-field, load full dataset
        full_data = self.get_all_data(clean_ticker)
        status_map = full_data.get("status_per_category", {})

        # Direct category match
        if clean_var in full_data and clean_var in REQUIRED_CATEGORIES:
            val = full_data[clean_var]
            st = status_map.get(clean_var, DataStatus.OKAY)
            return {
                "ticker": clean_ticker,
                "variable": clean_var,
                "status": st,
                "source": full_data.get("source"),
                "data": val
            }

        # Sub-field search across categories
        for cat_name in REQUIRED_CATEGORIES:
            cat_data = full_data.get(cat_name)
            if isinstance(cat_data, dict) and clean_var in cat_data:
                st = status_map.get(cat_name, DataStatus.OKAY)
                return {
                    "ticker": clean_ticker,
                    "variable": clean_var,
                    "parent_category": cat_name,
                    "status": st,
                    "source": full_data.get("source"),
                    "data": cat_data[clean_var]
                }

        return {
            "ticker": clean_ticker,
            "variable": clean_var,
            "status": DataStatus.ERROR,
            "message": f"Variable '{variable}' not found for {clean_ticker}"
        }

    def get_all_data(self, ticker: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Retrieves all 10 required data categories for a ticker.
        Checks availability, validation status, and normalization integrity.
        
        Returns final data structure matching getdata.md:
        - ticker
        - valuation
        - peer
        - future_forecast
        - institutional_transactions
        - executive_shareholdings
        - major_shareholders
        - shareholder_composition
        - dividend
        - executives
        - historical_price
        - processing_status
        """
        clean_ticker = ticker.replace(".JK", "").upper()

        # Execute through pipeline (checks cache first, mines & validates if miss)
        pipeline_res = self.pipeline.get_dataset(clean_ticker, force_refresh=force_refresh)
        raw_dataset = pipeline_res.get("data", {})

        status_per_category = {}
        error_count = 0
        warning_count = 0

        # Construct final structured dictionary
        final_struct: Dict[str, Any] = {
            "ticker": clean_ticker,
            "source": pipeline_res.get("source", "UNKNOWN"),
            "timestamp": pipeline_res.get("timestamp", datetime.now(timezone.utc).isoformat())
        }

        # Validate availability and assign status for each required category
        for cat in REQUIRED_CATEGORIES:
            content = raw_dataset.get(cat)
            final_struct[cat] = content

            if content is None:
                if cat in OPTIONAL_CATEGORIES:
                    status_per_category[cat] = DataStatus.WARNING
                    warning_count += 1
                else:
                    status_per_category[cat] = DataStatus.ERROR
                    error_count += 1
            else:
                # Check validation warnings from pipeline if available
                val_info = pipeline_res.get("validation", {}).get("categories", {}).get(cat, {})
                if val_info.get("status") == "WARNING" or (isinstance(content, dict) and not content):
                    status_per_category[cat] = DataStatus.WARNING
                    warning_count += 1
                else:
                    status_per_category[cat] = DataStatus.OKAY

        # Compute overall processing status according to getdata.md
        if error_count > 0:
            overall_status = DataStatus.ERROR
        elif warning_count > 0:
            overall_status = DataStatus.WARNING
        else:
            overall_status = DataStatus.OKAY

        final_struct["processing_status"] = {
            "overall": overall_status,
            "total_categories": len(REQUIRED_CATEGORIES),
            "okay_count": len([s for s in status_per_category.values() if s == DataStatus.OKAY]),
            "warning_count": warning_count,
            "error_count": error_count,
            "details": status_per_category
        }
        final_struct["status_per_category"] = status_per_category

        return final_struct

    def display_data_table(self, data_struct: Dict[str, Any]):
        """Displays final data as a clean, structured table matching getdata.md."""
        ticker = data_struct.get("ticker", "UNKNOWN")
        source = data_struct.get("source", "UNKNOWN")
        proc_status = data_struct.get("processing_status", {})
        overall = proc_status.get("overall", DataStatus.OKAY)
        status_map = data_struct.get("status_per_category", {})

        icon_map = {
            DataStatus.OKAY: "🟢 OKAY",
            DataStatus.WARNING: "🟡 WARNING",
            DataStatus.ERROR: "🔴 ERROR"
        }

        print("=" * 95)
        print(f"📊 FINAL DATASET FOR INTELLIGENCE ENGINE: {ticker}")
        print(f"📡 Source: {source} | Status: {icon_map.get(overall, overall)}")
        print("=" * 95)
        print(f"{'DATA TYPE':<28} | {'VALUE / SUMMARY':<48} | {'STATUS':<12}")
        print("-" * 95)

        for cat in REQUIRED_CATEGORIES:
            disp_name = CATEGORY_DISPLAY_NAMES.get(cat, cat)
            content = data_struct.get(cat)
            st = status_map.get(cat, DataStatus.OKAY)
            summary_val = self._format_summary_value(cat, content)
            
            # Truncate summary if too long for display
            if len(summary_val) > 46:
                summary_val = summary_val[:43] + "..."

            print(f"{disp_name:<28} | {summary_val:<48} | {icon_map.get(st, st):<12}")

        print("=" * 95)
        print(f"🎯 Ready for Intelligence Engine: {'YES ✅' if overall in [DataStatus.OKAY, DataStatus.WARNING] else 'NO ❌'}")
        print("=" * 95)


# Global helper functions for convenient import & usage
_default_provider = None

def _get_provider() -> SectorsDataProvider:
    global _default_provider
    if _default_provider is None:
        _default_provider = SectorsDataProvider()
    return _default_provider


def get_price(ticker: str) -> Dict[str, Any]:
    """Top-level convenience function to get stock price."""
    return _get_provider().get_price(ticker)


def get_variable(ticker: str, variable: str) -> Dict[str, Any]:
    """Top-level convenience function to get a specific data variable."""
    return _get_provider().get_variable(ticker, variable)


def get_all_data(ticker: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Top-level convenience function to get all required data for a ticker."""
    return _get_provider().get_all_data(ticker, force_refresh=force_refresh)


if __name__ == "__main__":
    target_ticker = sys.argv[1] if len(sys.argv) > 1 else "BBRI"
    
    provider = SectorsDataProvider()
    print(f"\n🚀 Fetching all final data for {target_ticker}...")
    final_data = provider.get_all_data(target_ticker)
    provider.display_data_table(final_data)

    print("\n🔍 Testing get_price():")
    price_res = provider.get_price(target_ticker)
    print(f"   ↳ Result: Ticker={price_res.get('ticker')}, Price={price_res.get('price')}, Status={price_res.get('status')}")

    print("\n🔍 Testing get_variable('valuation'):")
    var_res = provider.get_variable(target_ticker, "valuation")
    print(f"   ↳ Result Status: {var_res.get('status')}, Data Keys: {list(var_res.get('data', {}).keys())}")
