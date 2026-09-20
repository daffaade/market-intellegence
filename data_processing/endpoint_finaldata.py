import os
import sys
import json
import re
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add directories to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
for _p in [str(CURRENT_DIR), str(CURRENT_DIR / "data_sectors"), str(CURRENT_DIR / "y_finance_data"), str(ROOT_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import yfinance as yf
import pandas as pd
import numpy as np

from data_processing.unified_pipeline import UnifiedPipeline, UnifiedDataMerger


class EndpointStatus:
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


def get_section_data(ticker: str, section: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Helper to fetch a specific section using unified pipeline or get_api_data."""
    clean_ticker = ticker.upper().replace(".JK", "")
    section_clean = section.lower().strip()

    unified_section_keys = {
        "company_data", "valuation_data", "peer_data", "forecast_data",
        "ownership_data", "institutional_data", "insider_data",
        "historical_data", "dividend_data", "financial_data", "market_data"
    }

    if section_clean in unified_section_keys:
        pipeline = get_pipeline()
        unified_res = pipeline.get_unified_dataset(clean_ticker, force_refresh=force_refresh)
        full_data = unified_res.get("data", {})
        sec_content = full_data.get(section_clean)
        return {
            "ticker": clean_ticker,
            "section": section_clean,
            "status": EndpointStatus.SUCCESS if sec_content else EndpointStatus.WARNING,
            "source": unified_res.get("source", "Unified Pipeline"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": sec_content or {}
        }

    return get_api_data(ticker=ticker, data_type=section, force_refresh=force_refresh)


# =====================================================================
# DATA TYPES & SOURCE MAPPING (from rules.md)
# =====================================================================

SUPPORTED_DATA_TYPES = [
    "price",
    "valuation",
    "peers",
    "forecast",
    "dividend",
    "dividend_growth",
    "executives",
    "executive_shareholdings",
    "major_shareholders",
    "shareholder_composition",
    "institutional_transactions",
    "financials",
    "balance_sheet",
    "cash_flow",
    "company",
    "sector",
    "industry",
    "all"
]

DATA_SOURCE_MAPPING = {
    "price": "yFinance",
    "valuation": "Sectors",
    "peers": "Sectors",
    "forecast": "Sectors",
    "dividend": "yFinance",
    "dividend_growth": "Sectors / yFinance",
    "executives": "Sectors / yFinance",
    "executive_shareholdings": "Sectors",
    "major_shareholders": "Sectors",
    "shareholder_composition": "Sectors",
    "institutional_transactions": "Sectors / yFinance",
    "financials": "yFinance",
    "balance_sheet": "yFinance",
    "cash_flow": "yFinance",
    "company": "yFinance",
    "sector": "yFinance / Sectors",
    "industry": "yFinance / Sectors",
    "all": "Unified Multi-Source Pipeline"
}


# =====================================================================
# PERIOD HELPER & SANITIZER
# =====================================================================

def parse_period(period_str: Optional[str]) -> Tuple[str, str]:
    """
    Parses input period (e.g. 'current', '1y', '5y', '10y', '1m', '3m', '6m', '4w', '12w').
    Returns tuple of (canonical_period, yfinance_history_period).
    """
    if not period_str or not isinstance(period_str, str):
        return "current", "1d"

    p_clean = period_str.strip().lower()

    if p_clean in ("current", "latest", "now", "today"):
        return "current", "5d"

    # Match {number}y
    match_y = re.match(r"^(\d+)y$", p_clean)
    if match_y:
        yrs = int(match_y.group(1))
        if yrs <= 1:
            return f"{yrs}y", "1y"
        elif yrs <= 2:
            return f"{yrs}y", "2y"
        elif yrs <= 5:
            return f"{yrs}y", "5y"
        elif yrs <= 10:
            return f"{yrs}y", "10y"
        else:
            return f"{yrs}y", "max"

    # Match {number}m
    match_m = re.match(r"^(\d+)m$", p_clean)
    if match_m:
        months = int(match_m.group(1))
        if months <= 1:
            return f"{months}m", "1mo"
        elif months <= 3:
            return f"{months}m", "3mo"
        elif months <= 6:
            return f"{months}m", "6mo"
        elif months <= 12:
            return f"{months}m", "1y"
        else:
            return f"{months}m", f"{months}mo"

    # Match {number}w
    match_w = re.match(r"^(\d+)w$", p_clean)
    if match_w:
        weeks = int(match_w.group(1))
        days = weeks * 7
        return f"{weeks}w", f"{days}d"

    return p_clean, "1mo"


def clean_val(val: Any) -> Any:
    """Sanitizes pandas / numpy types into native Python JSON serializable types."""
    if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
        return None
    if isinstance(val, (np.integer, np.int64, np.int32)):
        return int(val)
    if isinstance(val, (np.floating, np.float64, np.float32)):
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return None
        if f.is_integer():
            return int(f)
        return round(f, 4)
    if isinstance(val, (pd.Timestamp, datetime)):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, np.bool_):
        return bool(val)
    # Convert Unix timestamp integers (e.g. exDividendDate from yFinance) to date strings
    if isinstance(val, int) and val > 1_000_000_000:
        try:
            return datetime.fromtimestamp(val, tz=timezone.utc).strftime("%Y-%m-%d")
        except (OSError, OverflowError, ValueError):
            pass
    return val


def dataframe_to_clean_dict(df: Optional[pd.DataFrame], max_cols: int = 10) -> Optional[dict]:
    """Converts a pandas DataFrame (e.g. financials, balance sheet) to clean dict."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return None

    result = {}
    sub_df = df.iloc[:, :max_cols] if df.shape[1] > max_cols else df

    for col in sub_df.columns:
        col_name = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
        result[col_name] = {}
        for row_idx, val in sub_df[col].items():
            field_name = str(row_idx).lower().replace(" ", "_").replace("-", "_")
            result[col_name][field_name] = clean_val(val)

    return result


# =====================================================================
# EXTRACTORS FOR LONG-TERM / PERIOD-AWARE DATA
# =====================================================================

def fetch_period_price(symbol: str, yf_period: str, period_label: str) -> Dict[str, Any]:
    """Fetches historical price list or current quote according to period."""
    clean_sym = symbol.upper().replace(".JK", "")
    yf_sym = f"{clean_sym}.JK"
    ticker = yf.Ticker(yf_sym)

    if period_label == "current":
        hist = ticker.history(period="5d")
        if not hist.empty:
            latest = hist.iloc[-1]
            dt = hist.index[-1].strftime("%Y-%m-%d") if hasattr(hist.index[-1], "strftime") else str(hist.index[-1])
            return {
                "symbol": clean_sym,
                "date": dt,
                "open": clean_val(latest.get("Open")),
                "high": clean_val(latest.get("High")),
                "low": clean_val(latest.get("Low")),
                "close": clean_val(latest.get("Close")),
                "volume": clean_val(latest.get("Volume")),
                "currency": "IDR"
            }
        return {"symbol": clean_sym, "message": "No price data available"}

    # Historical multi-period series
    hist = ticker.history(period=yf_period)
    if hist.empty:
        return {"symbol": clean_sym, "period": period_label, "records_count": 0, "records": []}

    records = []
    for dt_idx, row in hist.iterrows():
        dt_str = dt_idx.strftime("%Y-%m-%d") if hasattr(dt_idx, "strftime") else str(dt_idx)
        records.append({
            "date": dt_str,
            "open": clean_val(row.get("Open")),
            "high": clean_val(row.get("High")),
            "low": clean_val(row.get("Low")),
            "close": clean_val(row.get("Close")),
            "volume": clean_val(row.get("Volume"))
        })

    return {
        "symbol": clean_sym,
        "period": period_label,
        "total_records": len(records),
        "latest_close": records[-1]["close"] if records else None,
        "records": records
    }


def fetch_period_dividend(symbol: str, period_label: str) -> Dict[str, Any]:
    """Fetches historical dividends according to period."""
    clean_sym = symbol.upper().replace(".JK", "")
    yf_sym = f"{clean_sym}.JK"
    ticker = yf.Ticker(yf_sym)

    info = ticker.info or {}
    divs = getattr(ticker, "dividends", None)

    div_summary = {
        "symbol": clean_sym,
        "dividend_rate": clean_val(info.get("dividendRate")),
        "dividend_yield": clean_val(info.get("dividendYield")),
        "payout_ratio": clean_val(info.get("payoutRatio")),
        "trailing_annual_dividend_rate": clean_val(info.get("trailingAnnualDividendRate")),
        "trailing_annual_dividend_yield": clean_val(info.get("trailingAnnualDividendYield")),
        "five_year_avg_dividend_yield": clean_val(info.get("fiveYearAvgDividendYield")),
        "ex_dividend_date": clean_val(info.get("exDividendDate")),
        "period": period_label
    }

    if isinstance(divs, pd.Series) and not divs.empty:
        # Filter by period years if requested
        if period_label.endswith("y") and period_label[:-1].isdigit():
            cutoff_years = int(period_label[:-1])
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=cutoff_years * 365)
            filtered_divs = divs[divs.index >= cutoff_date] if divs.index.tz else divs[divs.index >= cutoff_date.replace(tzinfo=None)]
        else:
            filtered_divs = divs.tail(20)

        history_list = []
        for dt_idx, amt in filtered_divs.items():
            dt_str = dt_idx.strftime("%Y-%m-%d") if hasattr(dt_idx, "strftime") else str(dt_idx)
            history_list.append({
                "date": dt_str,
                "amount": clean_val(amt)
            })
        div_summary["dividend_history"] = history_list
        div_summary["total_payments"] = len(history_list)

    return div_summary


def fetch_dividend_growth(symbol: str, period_label: str) -> Dict[str, Any]:
    """Fetches dividend growth data by comparing current and previous periods."""
    clean_sym = symbol.upper().replace(".JK", "")
    
    div_data = fetch_period_dividend(clean_sym, period_label)
    history = div_data.get("dividend_history", [])
    dividend_growth = None
    
    if len(history) >= 2:
        history.sort(key=lambda x: x["date"])
        try:
            latest = float(history[-1]["amount"])
            previous = float(history[-2]["amount"])
            if previous and previous > 0:
                dividend_growth = round(((latest - previous) / previous) * 100, 2)
        except (ValueError, TypeError):
            pass
            
    # Try to get it from Sectors API through unified pipeline if period is current
    sectors_growth = None
    if period_label in ("current", "latest", "now", "today"):
        try:
            pipeline = get_pipeline()
            unified_res = pipeline.get_unified_dataset(clean_sym)
            s_div = unified_res.get("data", {}).get("dividend_data", {})
            sectors_growth = s_div.get("dividend_growth")
        except Exception:
            pass

    if period_label in ("current", "latest", "now", "today"):
        final_growth = sectors_growth if sectors_growth is not None else dividend_growth
        source = "Sectors API" if sectors_growth is not None else "yFinance (Calculated)"
    else:
        final_growth = dividend_growth if dividend_growth is not None else sectors_growth
        source = "yFinance (Calculated)" if dividend_growth is not None else "Sectors API"

    if final_growth is None:
        return {}

    return {
        "symbol": clean_sym,
        "dividend_growth": final_growth,
        "period": period_label,
        "source": source
    }


def fetch_financial_statements(symbol: str, statement_type: str, period_label: str) -> Dict[str, Any]:
    """Fetches multi-year financials, balance sheet, or cash flow."""
    clean_sym = symbol.upper().replace(".JK", "")
    yf_sym = f"{clean_sym}.JK"
    ticker = yf.Ticker(yf_sym)

    if statement_type == "financials":
        df = getattr(ticker, "financials", None)
    elif statement_type == "balance_sheet":
        df = getattr(ticker, "balance_sheet", None)
    elif statement_type == "cash_flow":
        df = getattr(ticker, "cashflow", None)
    else:
        df = None

    data_dict = dataframe_to_clean_dict(df)
    return {
        "symbol": clean_sym,
        "statement_type": statement_type,
        "period": period_label,
        "years_available": list(data_dict.keys()) if data_dict else [],
        "statements": data_dict or "Data not available for this ticker"
    }


# Singleton pipeline instance
_pipeline_instance: Optional[UnifiedPipeline] = None

def get_pipeline() -> UnifiedPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = UnifiedPipeline()
    return _pipeline_instance


# =====================================================================
# UNIFIED DATA API — MAIN CONTROLLER
# =====================================================================

def get_api_data(
    ticker: Optional[str] = None,
    data_type: str = "all",
    period: str = "current",
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Main endpoint controller implementing GET /api/{ticker}/{data_type}?period={period}
    from rules.md.
    """
    # 1. Validate API Request
    if not ticker or not isinstance(ticker, str) or not ticker.strip():
        return {
            "status": "ERROR",
            "error_code": "MISSING_TICKER",
            "message": "Stock ticker is required (e.g. 'BBCA', 'TLKM', 'BMRI').",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": None
        }

    clean_ticker = ticker.strip().upper().replace(".JK", "")
    dt_clean = data_type.strip().lower() if data_type else "all"
    norm_period, yf_period = parse_period(period)

    # Normalize alias data types
    alias_map = {
        "peer": "peers",
        "future_forecast": "forecast",
        "cashflow": "cash_flow",
        "balancesheet": "balance_sheet",
        "overview": "all",
        "full": "all"
    }
    dt_clean = alias_map.get(dt_clean, dt_clean)

    if dt_clean not in SUPPORTED_DATA_TYPES:
        return {
            "status": "ERROR",
            "error_code": "INVALID_DATA_TYPE",
            "message": f"Data type '{data_type}' is not supported. Available: {', '.join(SUPPORTED_DATA_TYPES)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": None
        }

    source_desc = DATA_SOURCE_MAPPING.get(dt_clean, "Unified Multi-Source Pipeline")

    try:
        # -------------------------------------------------------------
        # Route 1: Price
        # -------------------------------------------------------------
        if dt_clean == "price":
            price_data = fetch_period_price(clean_ticker, yf_period, norm_period)
            return {
                "ticker": clean_ticker,
                "data_type": "price",
                "period": norm_period,
                "source": "yFinance Data Pipeline",
                "status": "SUCCESS" if price_data.get("close") or price_data.get("records") else "WARNING",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": price_data
            }

        # -------------------------------------------------------------
        # Route 2: Dividend
        # -------------------------------------------------------------
        elif dt_clean == "dividend":
            div_data = fetch_period_dividend(clean_ticker, norm_period)
            return {
                "ticker": clean_ticker,
                "data_type": "dividend",
                "period": norm_period,
                "source": "yFinance Data Pipeline (Historical) + Sectors (Breakdown)",
                "status": "SUCCESS",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": div_data
            }

        # -------------------------------------------------------------
        # Route 2b: Dividend Growth
        # -------------------------------------------------------------
        elif dt_clean == "dividend_growth":
            div_growth_data = fetch_dividend_growth(clean_ticker, norm_period)
            return {
                "ticker": clean_ticker,
                "data_type": "dividend_growth",
                "period": norm_period,
                "source": div_growth_data.get("source", "Unknown") if div_growth_data else "Unknown",
                "status": "SUCCESS" if div_growth_data else "WARNING",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": div_growth_data if div_growth_data else {"error": "Dividend growth data not available"}
            }

        # -------------------------------------------------------------
        # Route 3: Financial Statements (financials, balance_sheet, cash_flow)
        # -------------------------------------------------------------
        elif dt_clean in ("financials", "balance_sheet", "cash_flow"):
            stmt_data = fetch_financial_statements(clean_ticker, dt_clean, norm_period)
            return {
                "ticker": clean_ticker,
                "data_type": dt_clean,
                "period": norm_period,
                "source": "yFinance Data Pipeline",
                "status": "SUCCESS" if stmt_data.get("statements") != "Data not available for this ticker" else "WARNING",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": stmt_data
            }

        # -------------------------------------------------------------
        # Route 4: Snapshot and Categorical Sections (via Unified Pipeline)
        # -------------------------------------------------------------
        pipeline = get_pipeline()
        unified_res = pipeline.get_unified_dataset(clean_ticker, force_refresh=force_refresh)
        full_data = unified_res.get("data", {})

        section_map = {
            "valuation": "valuation_data",
            "peers": "peer_data",
            "forecast": "forecast_data",
            "executives": "insider_data",
            "executive_shareholdings": "insider_data",
            "major_shareholders": "ownership_data",
            "shareholder_composition": "ownership_data",
            "institutional_transactions": "institutional_data",
            "company": "company_data",
            "sector": "company_data",
            "industry": "company_data"
        }

        # Specific sub-attributes for sector/industry/company
        if dt_clean in ("sector", "industry"):
            comp = full_data.get("company_data", {})
            return {
                "ticker": clean_ticker,
                "data_type": dt_clean,
                "period": norm_period,
                "source": source_desc,
                "status": "SUCCESS" if comp.get(dt_clean) else "WARNING",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "symbol": clean_ticker,
                    dt_clean: comp.get(dt_clean),
                    "company_name": comp.get("company_name")
                }
            }

        if dt_clean in section_map:
            sec_key = section_map[dt_clean]
            sec_content = full_data.get(sec_key, {})
            return {
                "ticker": clean_ticker,
                "data_type": dt_clean,
                "period": norm_period,
                "source": source_desc,
                "status": "SUCCESS" if sec_content else "WARNING",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": sec_content
            }

        # -------------------------------------------------------------
        # Route 5: All (Complete Unified Dataset)
        # -------------------------------------------------------------
        if dt_clean == "all":
            # If period is multi-year/multi-month, attach historical records
            if norm_period != "current":
                full_data = dict(full_data)
                full_data["historical_data"] = fetch_period_price(clean_ticker, yf_period, norm_period)
                full_data["dividend_data"] = fetch_period_dividend(clean_ticker, norm_period)
                full_data["financial_statements"] = {
                    "income_statement": fetch_financial_statements(clean_ticker, "financials", norm_period).get("statements"),
                    "balance_sheet": fetch_financial_statements(clean_ticker, "balance_sheet", norm_period).get("statements"),
                    "cash_flow": fetch_financial_statements(clean_ticker, "cash_flow", norm_period).get("statements")
                }

            return {
                "ticker": clean_ticker,
                "data_type": "all",
                "period": norm_period,
                "source": "Unified Multi-Source Pipeline (Sectors + yFinance)",
                "status": "SUCCESS" if full_data else "WARNING",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "discrepancies": unified_res.get("discrepancies", []),
                "data": full_data
            }

        return {
            "status": "WARNING",
            "ticker": clean_ticker,
            "data_type": dt_clean,
            "message": f"Data not compiled for {dt_clean}",
            "data": None
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "ticker": clean_ticker,
            "error_code": "ENDPOINT_EXCEPTION",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": None
        }


def get_final_data(ticker: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
    """Compatibility wrapper for complete unified dataset retrieval."""
    return get_api_data(ticker=ticker, data_type="all", period="current", force_refresh=force_refresh)


# =====================================================================
# LOCAL HTTP REST API SERVER (Matching GET /api/{ticker}/{data_type}?period={period})
# =====================================================================

class UnifiedDataHTTPHandler(BaseHTTPRequestHandler):
    """
    HTTP REST API Handler implementing:
      GET /api/{ticker}/{data_type}?period={period}
      GET /api/{ticker}?period={period}
      GET /health
    """

    def _send_json(self, status_code: int, payload: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.strip("/")
        query_params = urllib.parse.parse_qs(parsed.query)
        period = query_params.get("period", ["current"])[0]
        force_refresh = query_params.get("refresh", ["false"])[0].lower() == "true"

        if path == "health":
            self._send_json(200, {
                "status": "HEALTHY",
                "service": "Unified Market Intelligence API",
                "version": "2.0",
                "supported_data_types": SUPPORTED_DATA_TYPES
            })
            return

        # Route matching: /api/{ticker}/{data_type} or /api/{ticker}
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] == "api":
            ticker = parts[1]
            data_type = parts[2] if len(parts) >= 3 else "all"

            res = get_api_data(ticker=ticker, data_type=data_type, period=period, force_refresh=force_refresh)
            status_code = 200 if res.get("status") != "ERROR" else 400
            self._send_json(status_code, res)
            return

        self._send_json(404, {
            "status": "ERROR",
            "message": f"Invalid endpoint: /{path}",
            "format": "GET /api/{ticker}/{data_type}?period={period}",
            "examples": [
                "/api/BBCA/price?period=10y",
                "/api/BBCA/valuation?period=current",
                "/api/BBCA/dividend?period=5y",
                "/api/BBCA/financials?period=5y",
                "/api/BBCA/all?period=current"
            ]
        })


def run_local_server(port: int = 8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, UnifiedDataHTTPHandler)
    print("=" * 80)
    print(f"🚀 Unified Data API Server running on http://localhost:{port}")
    print("=" * 80)
    print(f"📡 Format   : GET /api/{{ticker}}/{{data_type}}?period={{period}}")
    print(f"📌 Examples :")
    print(f"   • http://localhost:{port}/api/BBCA/price?period=10y")
    print(f"   • http://localhost:{port}/api/BBCA/valuation?period=current")
    print(f"   • http://localhost:{port}/api/BBCA/dividend?period=5y")
    print(f"   • http://localhost:{port}/api/BBCA/financials?period=5y")
    print(f"   • http://localhost:{port}/api/BBCA/all?period=current")
    print(f"   • http://localhost:{port}/health")
    print("=" * 80)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")


# =====================================================================
# CLI RUNNER & TESTER
# =====================================================================

def display_cli_result(res: dict):
    print("=" * 80)
    print(f"📡 UNIFIED DATA API RESULT: {res.get('ticker', 'UNKNOWN')} [{res.get('data_type', '').upper()}]")
    print("=" * 80)
    print(f"• Ticker        : {res.get('ticker')}")
    print(f"• Data Type     : {res.get('data_type')}")
    print(f"• Period        : {res.get('period')}")
    print(f"• Source        : {res.get('source')}")
    print(f"• Status        : {res.get('status')}")
    print(f"• Timestamp     : {res.get('timestamp')}")

    data = res.get("data")
    print("\n📦 DATA CONTENT:")
    print("-" * 80)
    if isinstance(data, dict):
        data_str = json.dumps(data, indent=2, ensure_ascii=False)
        print(data_str[:3000])
        if len(data_str) > 3000:
            print("\n... (truncated preview)")
    else:
        print(data)
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        run_local_server(port)
    else:
        target_ticker = sys.argv[1] if len(sys.argv) > 1 else "BBCA"
        target_type = sys.argv[2] if len(sys.argv) > 2 else "all"
        target_period = sys.argv[3] if len(sys.argv) > 3 else "current"

        result = get_api_data(ticker=target_ticker, data_type=target_type, period=target_period)
        display_cli_result(result)
