import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from unified_data.endpoint_finaldata import get_final_data, get_section_data, EndpointStatus
from unified_data.unified_pipeline import UnifiedPipeline


UNIFIED_SECTIONS = [
    ("company_data", "Company Profile"),
    ("valuation_data", "Valuation Metrics"),
    ("peer_data", "Peer & Industry Comparison"),
    ("forecast_data", "Forecast & Analyst Targets"),
    ("ownership_data", "Ownership & Whales"),
    ("institutional_data", "Institutional Flow & Holders"),
    ("insider_data", "Executive & Insider Holdings"),
    ("historical_data", "Historical Market OHLCV"),
    ("dividend_data", "Dividend Metrics & History"),
    ("financial_data", "Financial Statements"),
    ("market_data", "Current Market Data")
]


class UnifiedDataProvider:
    """
    Unified Data Provider delivering compiled multi-source intelligence
    for Machine Learning, Analytics, and Intelligence Engines.
    """

    def __init__(self, pipeline: Optional[UnifiedPipeline] = None):
        self.pipeline = pipeline or UnifiedPipeline()

    def get_price(self, ticker: str) -> Dict[str, Any]:
        """Returns unified market price and OHLC summary."""
        res = get_section_data(ticker, "market_data")
        if res.get("status") == EndpointStatus.SUCCESS:
            data = res.get("data", {})
            return {
                "status": "OKAY",
                "ticker": ticker.upper().replace(".JK", ""),
                "price": data.get("latest_price") or data.get("close"),
                "date": data.get("as_of_date"),
                "market_cap": data.get("market_cap"),
                "volume": data.get("volume"),
                "data": data
            }
        return {"status": "ERROR", "ticker": ticker, "price": None, "message": res.get("message")}

    def get_section(self, ticker: str, section: str) -> Dict[str, Any]:
        """Returns a single organized section."""
        return get_section_data(ticker, section)

    def get_all_data(self, ticker: str, print_table: bool = True) -> Dict[str, Any]:
        """Compiles the full unified dataset and optionally prints a clean overview table."""
        payload = get_final_data(ticker)
        data = payload.get("data", {})
        clean_ticker = ticker.upper().replace(".JK", "")

        if print_table:
            self.display_summary_table(clean_ticker, payload)

        return payload

    def _format_section_summary(self, sec_key: str, content: Any) -> str:
        """Helper to create human-readable summary for console table."""
        if not content or not isinstance(content, dict):
            return "(Not Available)"

        if sec_key == "company_data":
            name = content.get("company_name", "")
            sector = content.get("sector", "")
            return f"{name} ({sector})"

        elif sec_key == "valuation_data":
            fpe = content.get("forward_pe")
            iv = content.get("intrinsic_value")
            parts = []
            if fpe:
                parts.append(f"Fwd P/E: {fpe}")
            if iv:
                parts.append(f"Intrinsic: Rp {iv:,.0f}" if isinstance(iv, (int, float)) else f"Intrinsic: {iv}")
            return " | ".join(parts) or "Valuation metrics compiled"

        elif sec_key == "peer_data":
            name = content.get("peer_company_name", "")
            mcap = content.get("market_cap")
            mcap_str = f"Rp {mcap/1e12:,.1f}T" if isinstance(mcap, (int, float)) else ""
            return f"{name} (MCap: {mcap_str})" if mcap_str else name

        elif sec_key == "forecast_data":
            target = content.get("target_mean_price")
            eps = content.get("eps_estimate")
            parts = []
            if target:
                parts.append(f"Target: Rp {target:,.0f}" if isinstance(target, (int, float)) else f"Target: {target}")
            if eps:
                parts.append(f"EPS: {eps}")
            return " | ".join(parts) or "Forecast data compiled"

        elif sec_key == "ownership_data":
            name = content.get("major_shareholder_name", "")
            pct = content.get("major_shareholder_percentage")
            pct_str = f"{pct*100:.1f}%" if isinstance(pct, (int, float)) else ""
            return f"{name} ({pct_str})" if pct_str else name

        elif sec_key == "institutional_data":
            holder = content.get("top_holder_name") or content.get("sample_buyer", {}).get("name")
            return f"Top Holder: {holder}" if holder else "Institutional transactions compiled"

        elif sec_key == "insider_data":
            name = content.get("executive_name", "")
            pos = content.get("position", "")
            return f"{name} ({pos})" if name else "Insider holdings compiled"

        elif sec_key == "historical_data":
            dt = content.get("date", "")
            close_p = content.get("close")
            close_str = f"Rp {close_p:,.0f}" if isinstance(close_p, (int, float)) else str(close_p)
            return f"Date: {dt} | Close: {close_str}"

        elif sec_key == "dividend_data":
            rate = content.get("total_dividend")
            dy = content.get("dividend_yield")
            dy_str = f"{dy*100:.2f}%" if isinstance(dy, (int, float)) else ""
            return f"Rate: Rp {rate} | Yield: {dy_str}" if dy_str else f"Rate: Rp {rate}"

        elif sec_key == "financial_data":
            rev = content.get("total_revenue")
            rev_str = f"Rp {rev/1e12:,.1f}T" if isinstance(rev, (int, float)) else str(rev)
            return f"Revenue: {rev_str}" if rev else "Financial data compiled"

        elif sec_key == "market_data":
            price = content.get("latest_price") or content.get("close")
            vol = content.get("volume")
            p_str = f"Rp {price:,.0f}" if isinstance(price, (int, float)) else str(price)
            v_str = f"{vol:,.0f}" if isinstance(vol, (int, float)) else str(vol)
            return f"Price: {p_str} | Vol: {v_str}"

        return str(content)[:50]

    def display_summary_table(self, ticker: str, payload: dict):
        """Prints a clean tabular report for the Intelligence Engine."""
        col1_w = 30
        col2_w = 12
        col3_w = 48

        total_w = col1_w + col2_w + col3_w + 10
        print("=" * total_w)
        print(f"🏛️  UNIFIED MARKET INTELLIGENCE REPORT: {ticker.upper()}")
        print(f"    Source: {payload.get('source')} | Status: {payload.get('status')}")
        print("=" * total_w)

        header = f"| {'Section Name':<{col1_w}} | {'Status':<{col2_w}} | {'Summary Value / Sample':<{col3_w}} |"
        sep = f"|{'-' * (col1_w + 2)}|{'-' * (col2_w + 2)}|{'-' * (col3_w + 2)}|"

        print(header)
        print(sep)

        data = payload.get("data", {})
        for sec_key, disp_name in UNIFIED_SECTIONS:
            sec_content = data.get(sec_key)
            status = "READY" if sec_content and any(v is not None for v in sec_content.values() if isinstance(sec_content, dict)) else "WARNING"
            summary_str = self._format_section_summary(sec_key, sec_content)

            print(f"| {disp_name:<{col1_w}} | {status:<{col2_w}} | {summary_str[:col3_w]:<{col3_w}} |")

        print("=" * total_w)
        if payload.get("discrepancies"):
            print(f"⚠️  {len(payload['discrepancies'])} Data Discrepancy Flag(s) Detected Between Sectors and yFinance.")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "BBCA"
    provider = UnifiedDataProvider()
    provider.get_all_data(target, print_table=True)
