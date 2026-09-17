from __future__ import annotations
import math
import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Memastikan modul unified_data dapat diakses dari direktori manapun
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent if (CURRENT_DIR.parent / "unified_data").exists() else CURRENT_DIR
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from unified_data.endpoint_finaldata import get_api_data
    HAS_UNIFIED_DATA = True
except ImportError:
    HAS_UNIFIED_DATA = False


# ============================================================================
# HELPER & ACCESSOR
# ============================================================================

def safe_divide(numerator: Any, denominator: Any) -> Optional[float]:
    """
    Safe Divide Helper (digunakan di semua fungsi perhitungan).
    Mengembalikan None jika penyebut 0, None, atau jika terjadi error tipe.
    """
    if numerator is None or denominator is None:
        return None
    try:
        num = float(numerator)
        den = float(denominator)
        if den == 0.0 or math.isnan(den) or math.isnan(num):
            return None
        return num / den
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _get(obj: Any, path: str, default: Any = None) -> Any:
    """
    Helper fleksibel untuk mengakses nilai dari dictionary atau objek (dot-notation).
    Mendukung format 'valuation.pe' atau 'growth.revenue', serta alias field umum.
    """
    if obj is None:
        return default

    parts = path.split(".")
    curr = obj

    for part in parts:
        if curr is None:
            return default

        # Dictionary access
        if isinstance(curr, dict):
            if part in curr:
                curr = curr[part]
            else:
                # Cek alias umum jika key persis tidak ditemukan
                found = False
                aliases = {
                    "pe": ["pe", "trailing_pe", "forward_pe", "pe_ttm"],
                    "pbv": ["pbv", "price_to_book", "pb_ratio"],
                    "close": ["close", "adj_close", "price", "last_price"],
                    "revenue": ["revenue", "total_revenue", "operating_revenue"],
                    "forecast": ["forecast", "revenue_estimate", "target_mean_price"],
                    "actual": ["actual", "revenue", "total_revenue"],
                    "eps": ["eps", "basic_eps", "diluted_eps", "eps_estimate"],
                    "insider_pct": ["insider_pct", "insiders_percent_held", "insider_percentage"],
                    "per_share": ["per_share", "dividend_rate", "trailing_annual_dividend_rate"],
                    "dividend_growth": ["dividend_growth", "div_growth"],
                    "market_cap": ["market_cap", "market_capitalization"],
                    "total_debt": ["total_debt", "total_liabilities"],
                    "cash": ["cash", "cash_and_cash_equivalents"],
                    "ebitda": ["ebitda", "operating_income"]
                }
                for alias in aliases.get(part, []):
                    if alias in curr:
                        curr = curr[alias]
                        found = True
                        break
                if not found:
                    return default
        else:
            # Object attribute access
            if hasattr(curr, part):
                curr = getattr(curr, part)
            else:
                return default

    return curr if curr is not None else default


def extract_price_series(historical_data: Any) -> List[float]:
    """
    Mengekstrak list harga penutupan urut waktu (kronologis: terlama ke terbaru).
    Mendukung format list of numbers, list of dicts [{'close': ...}], atau dict dari API.
    """
    if not historical_data:
        return []

    # Jika historical_data adalah dictionary (misal respons API price)
    if isinstance(historical_data, dict):
        if "records" in historical_data and isinstance(historical_data["records"], list):
            historical_data = historical_data["records"]
        elif "price_series" in historical_data:
            historical_data = historical_data["price_series"]

    if not isinstance(historical_data, list):
        return []

    prices: List[float] = []
    for item in historical_data:
        if isinstance(item, (int, float)):
            prices.append(float(item))
        elif isinstance(item, dict):
            # Prioritas: 'close' -> 'adj_close' -> 'price'
            c = item.get("close")
            if c is None:
                c = item.get("adj_close")
            if c is None:
                c = item.get("price")
            if c is not None:
                try:
                    prices.append(float(c))
                except (ValueError, TypeError):
                    continue
        else:
            # Objek dengan attribute close
            c = getattr(item, "close", getattr(item, "adj_close", None))
            if c is not None:
                try:
                    prices.append(float(c))
                except (ValueError, TypeError):
                    continue

    return prices


def get_previous_period(historical_data: Any, offset: int = 1) -> Any:
    """
    Mendapatkan data periode sebelumnya berdasarkan offset.
    offset=1: periode sebelumnya (QoQ / 1 periode lalu)
    offset=4: 4 periode sebelumnya (YoY kuartalan)
    
    Mendukung list kronologis (terbaru di indeks terakhir) maupun terbalik (terbaru di indeks 0).
    """
    if not historical_data or not isinstance(historical_data, list):
        return None

    if len(historical_data) < offset:
        return None

    # Asumsi umum time-series: elemen terakhir [-1] adalah periode paling mutakhir
    # offset=1 mengambil elemen [-1], atau [-offset] jika list memuat histori sebelumnya
    try:
        return historical_data[-offset]
    except IndexError:
        return None


def compute_daily_returns(price_series: List[float]) -> List[float]:
    """Menghitung return harian dari seri harga: (P_t - P_{t-1}) / P_{t-1}."""
    if not price_series or len(price_series) < 2:
        return []
    returns: List[float] = []
    for i in range(1, len(price_series)):
        prev = price_series[i - 1]
        curr = price_series[i]
        ret = safe_divide(curr - prev, prev)
        if ret is not None:
            returns.append(ret)
    return returns


def std_dev(series: List[float], window: int = 30) -> Optional[float]:
    """Menghitung standar deviasi sampel dari n data terakhir."""
    if not series:
        return None
    sub = series[-window:] if len(series) >= window else series
    n = len(sub)
    if n < 2:
        return None
    mean = sum(sub) / n
    variance = sum((x - mean) ** 2 for x in sub) / (n - 1)
    return math.sqrt(variance)


def moving_average(price_series: List[float], window: int) -> Optional[float]:
    """Menghitung Simple Moving Average (SMA) n data terakhir."""
    if not price_series or len(price_series) < window or window <= 0:
        return None
    sub = price_series[-window:]
    return sum(sub) / len(sub)


def compute_return(price_series: List[float], periods_back: int) -> Optional[float]:
    """
    Menghitung persentase return harga n periode ke belakang.
    Formula: ((new_price - old_price) / old_price) * 100
    """
    if not price_series or len(price_series) <= periods_back:
        return None
    old_price = price_series[-periods_back]
    new_price = price_series[-1]
    ret = safe_divide(new_price - old_price, old_price)
    return round(ret * 100, 4) if ret is not None else None


def compute_growth_qoq_for(period_data: Any, historical_data: Any) -> Optional[float]:
    """
    Helper untuk menghitung QoQ growth untuk periode sebelumnya (digunakan dalam akselerasi).
    """
    if not period_data or not historical_data or not isinstance(historical_data, list):
        return None

    try:
        # Temukan posisi period_data dalam historical_data
        idx = -1
        for i, item in enumerate(historical_data):
            if item is period_data or item == period_data:
                idx = i
                break

        if idx > 0:
            prior_period = historical_data[idx - 1]
            curr_rev = _get(period_data, "growth.revenue")
            prior_rev = _get(prior_period, "growth.revenue")
            growth = safe_divide(curr_rev - prior_rev, prior_rev)
            return growth * 100 if growth is not None else None
    except Exception:
        pass

    return None


# ============================================================================
# 1. VALUATION METRICS
# ============================================================================

def compute_valuation_metrics(data: Any) -> Dict[str, Optional[float]]:
    """
    Menghitung metrik valuasi:
    - pe_relative: P/E emiten dibagi rata-rata P/E sektor/peer
    - pbv_relative: P/BV emiten dibagi rata-rata P/BV sektor/peer
    - valuation_percentile: persentase peer yang memiliki PE lebih tinggi dari emiten ini
    - ev_ebitda: (Market Cap + Total Debt - Cash) / EBITDA
    """
    peers = _get(data, "peers") or _get(data, "peer_data") or []
    if isinstance(peers, dict):
        peers = [peers]

    company_pe = _get(data, "valuation.pe")
    company_pbv = _get(data, "valuation.pbv")

    # Ambil list PE dan PBV dari peer
    pe_list = []
    pbv_list = []
    for p in peers:
        p_pe = _get(p, "pe")
        p_pbv = _get(p, "pbv")
        if p_pe is not None:
            pe_list.append(float(p_pe))
        if p_pbv is not None:
            pbv_list.append(float(p_pbv))

    pe_sector_avg = sum(pe_list) / len(pe_list) if pe_list else None
    pbv_sector_avg = sum(pbv_list) / len(pbv_list) if pbv_list else None

    pe_relative = safe_divide(company_pe, pe_sector_avg)
    pbv_relative = safe_divide(company_pbv, pbv_sector_avg)

    # Percentile: berapa persen peer yang PE-nya lebih tinggi dari company ini
    if peers and company_pe is not None and pe_list:
        higher_pe_count = sum(1 for p_pe in pe_list if p_pe > float(company_pe))
        val_pct = safe_divide(higher_pe_count, len(pe_list))
        valuation_percentile = round(val_pct * 100, 2) if val_pct is not None else None
    else:
        valuation_percentile = None

    # EV / EBITDA calculation
    market_cap = _get(data, "valuation.market_cap")
    total_debt = _get(data, "valuation.total_debt", 0.0) or 0.0
    cash = _get(data, "valuation.cash", 0.0) or 0.0
    ebitda = _get(data, "valuation.ebitda")

    if market_cap is not None and ebitda is not None and float(ebitda) != 0:
        ev = float(market_cap) + float(total_debt) - float(cash)
        ev_ebitda = safe_divide(ev, ebitda)
    else:
        # Fallback jika EV/EBITDA sudah dihitung langsung oleh sumber valuasi
        ev_ebitda = _get(data, "valuation.ev_ebitda") or _get(data, "valuation.enterprise_to_ebitda")

    return {
        "pe_relative": round(pe_relative, 4) if pe_relative is not None else None,
        "pbv_relative": round(pbv_relative, 4) if pbv_relative is not None else None,
        "valuation_percentile": valuation_percentile,
        "ev_ebitda": round(ev_ebitda, 4) if ev_ebitda is not None else None
    }


# ============================================================================
# 2. GROWTH METRICS
# ============================================================================

def compute_growth_metrics(data: Any, historical_data: Any) -> Dict[str, Optional[float]]:
    """
    Menghitung metrik pertumbuhan:
    - revenue_growth_qoq: Pertumbuhan pendapatan kuartalan (%)
    - revenue_growth_yoy: Pertumbuhan pendapatan tahunan (%)
    - growth_acceleration: Akselerasi pertumbuhan QoQ vs periode lalu (% poin)
    - forecast_gap: Deviasi kinerja aktual terhadap forecast/konsensus (%)
    """
    prev_period = get_previous_period(historical_data, offset=1)
    prev_year = get_previous_period(historical_data, offset=4)

    curr_rev = _get(data, "growth.revenue")
    prev_rev = _get(prev_period, "growth.revenue") if prev_period else None
    prev_year_rev = _get(prev_year, "growth.revenue") if prev_year else None

    # QoQ Growth
    growth_qoq = None
    if curr_rev is not None and prev_rev is not None:
        g_qoq = safe_divide(float(curr_rev) - float(prev_rev), float(prev_rev))
        if g_qoq is not None:
            growth_qoq = round(g_qoq * 100, 2)

    # YoY Growth
    growth_yoy = None
    if curr_rev is not None and prev_year_rev is not None:
        g_yoy = safe_divide(float(curr_rev) - float(prev_year_rev), float(prev_year_rev))
        if g_yoy is not None:
            growth_yoy = round(g_yoy * 100, 2)
    elif curr_rev is not None and prev_rev is not None and prev_year is None:
        # Fallback jika data historis adalah tahunan (offset 1 = 1 year)
        pass

    # Growth Acceleration = growth_qoq - prev_growth_qoq
    prev_growth_qoq = compute_growth_qoq_for(prev_period, historical_data)
    acceleration = None
    if growth_qoq is not None and prev_growth_qoq is not None:
        acceleration = round(growth_qoq - prev_growth_qoq, 2)

    # Forecast Gap = (actual - forecast) / forecast * 100
    actual = _get(data, "growth.actual", curr_rev)
    forecast = _get(data, "growth.forecast")
    forecast_gap = None
    if actual is not None and forecast is not None:
        fg = safe_divide(float(actual) - float(forecast), float(forecast))
        if fg is not None:
            forecast_gap = round(fg * 100, 2)

    return {
        "revenue_growth_qoq": growth_qoq,
        "revenue_growth_yoy": growth_yoy,
        "growth_acceleration": acceleration,
        "forecast_gap": forecast_gap
    }


# ============================================================================
# 3. PRICE & MOMENTUM METRICS
# ============================================================================

def compute_price_metrics(data: Any, historical_data: Any) -> Dict[str, Optional[float]]:
    """
    Menghitung metrik harga dan momentum:
    - return_1m: Return 1 bulan (~21 hari bursa)
    - return_3m: Return 3 bulan (~63 hari bursa)
    - return_1y: Return 1 tahun (~252 hari bursa)
    - volatility: Volatilitas harian di-annualisasi (sqrt(252))
    - price_vs_ma20: Posisi harga terhadap Moving Average 20 hari (%)
    - price_vs_ma50: Posisi harga terhadap Moving Average 50 hari (%)
    """
    price_series = extract_price_series(historical_data)
    current_price = _get(data, "price.close")

    # Pastikan current_price berada di ujung akhir price_series jika belum ada
    if current_price is not None:
        current_price = float(current_price)
        if not price_series or abs(price_series[-1] - current_price) > 1e-4:
            price_series = list(price_series) + [current_price]
    elif price_series:
        current_price = price_series[-1]

    return_1m = compute_return(price_series, periods_back=21)
    return_3m = compute_return(price_series, periods_back=63)
    return_1y = compute_return(price_series, periods_back=252)

    daily_returns = compute_daily_returns(price_series)
    vol_30 = std_dev(daily_returns, window=30)
    volatility = round(vol_30 * math.sqrt(252) * 100, 2) if vol_30 is not None else None

    ma20 = moving_average(price_series, window=20)
    ma50 = moving_average(price_series, window=50)

    price_vs_ma20 = None
    if current_price is not None and ma20 is not None:
        p20 = safe_divide(current_price - ma20, ma20)
        if p20 is not None:
            price_vs_ma20 = round(p20 * 100, 2)

    price_vs_ma50 = None
    if current_price is not None and ma50 is not None:
        p50 = safe_divide(current_price - ma50, ma50)
        if p50 is not None:
            price_vs_ma50 = round(p50 * 100, 2)

    return {
        "return_1m": return_1m,
        "return_3m": return_3m,
        "return_1y": return_1y,
        "volatility": volatility,
        "price_vs_ma20": price_vs_ma20,
        "price_vs_ma50": price_vs_ma50
    }


# ============================================================================
# 4. OWNERSHIP METRICS
# ============================================================================

def compute_ownership_metrics(data: Any, historical_data: Any) -> Dict[str, Optional[float]]:
    """
    Menghitung metrik kepemilikan dan aliran dana:
    - net_institutional_flow_pct: Net akumulasi institusi terhadap market cap (%)
    - insider_ownership_change: Perubahan persentase kepemilikan orang dalam (%)
    - concentration_top5: Akumulasi porsi kepemilikan 5 pemegang saham terbesar (%)
    - hhi: Indeks konsentrasi Herfindahl-Hirschman
    """
    # Net Institutional Flow %
    buy_val = _get(data, "institutional.total_buy_value")
    sell_val = _get(data, "institutional.total_sell_value")
    market_cap = _get(data, "valuation.market_cap")

    if buy_val is not None and sell_val is not None:
        net_flow = float(buy_val) - float(sell_val)
    else:
        net_flow = _get(data, "institutional.net_flow")

    net_flow_pct = None
    if net_flow is not None and market_cap is not None:
        flow_pct = safe_divide(net_flow, market_cap)
        if flow_pct is not None:
            net_flow_pct = round(flow_pct * 100, 4)

    # Insider Ownership Change
    curr_insider = _get(data, "ownership.insider_pct")
    prev_period = get_previous_period(historical_data, offset=1)
    prev_insider = _get(prev_period, "ownership.insider_pct") if prev_period else None

    insider_change = None
    if curr_insider is not None and prev_insider is not None:
        insider_change = round(float(curr_insider) - float(prev_insider), 4)

    # Shareholder Concentration & HHI
    raw_shareholders = _get(data, "ownership.shareholders") or []
    shareholder_pcts: List[float] = []

    for sh in raw_shareholders:
        pct = _get(sh, "pct") or _get(sh, "share_percentage") or _get(sh, "percentage")
        if pct is not None:
            try:
                val = float(pct)
                # Normalisasi jika porsi dinyatakan dalam skala 0.0 - 1.0 ke 0 - 100%
                if 0.0 < val <= 1.0:
                    val = val * 100.0
                shareholder_pcts.append(val)
            except (ValueError, TypeError):
                continue

    if shareholder_pcts:
        sorted_pcts = sorted(shareholder_pcts, reverse=True)
        concentration_top5 = round(sum(sorted_pcts[:5]), 2)
        hhi = round(sum(p ** 2 for p in sorted_pcts), 2)
    else:
        concentration_top5 = None
        hhi = None

    return {
        "net_institutional_flow_pct": net_flow_pct,
        "insider_ownership_change": insider_change,
        "concentration_top5": concentration_top5,
        "hhi": hhi
    }


# ============================================================================
# 5. DIVIDEND METRICS
# ============================================================================

def compute_dividend_metrics(
    data: Any,
    historical_data: Any = None,
    period: str = "current"
) -> Dict[str, Optional[float]]:
    """
    Menghitung metrik dividen:
    - dividend_yield: Dividen per lembar dibagi harga saham (%)
    - payout_ratio: Dividen per lembar dibagi laba per saham / EPS (%)
    - dividend_growth: Pertumbuhan dividen per lembar dibanding periode sebelumnya (%)
      Prioritas sumber:
      1. Nilai langsung dari input data (data.dividend.dividend_growth atau data.dividend_growth)
      2. Mengambil dari endpoint_finaldata (jika modul tersedia dan ada ticker/company riil)
      3. Kalkulasi manual dari historical_data (data.dividend.per_share vs prev_period.dividend.per_share)
    """
    div_per_share = _get(data, "dividend.per_share")
    current_price = _get(data, "price.close")
    eps = _get(data, "growth.eps")

    # Dividend Yield
    div_yield = None
    if div_per_share is not None and current_price is not None:
        dy = safe_divide(div_per_share, current_price)
        if dy is not None:
            div_yield = round(dy * 100, 2)
    else:
        # Fallback jika yield langsung diberikan di input
        raw_dy = _get(data, "dividend.dividend_yield")
        if raw_dy is not None:
            div_yield = round(float(raw_dy), 2)

    # Payout Ratio
    payout_ratio = None
    if div_per_share is not None and eps is not None and float(eps) != 0:
        pr = safe_divide(div_per_share, eps)
        if pr is not None:
            payout_ratio = round(pr * 100, 2)
    else:
        # Fallback jika payout ratio langsung disediakan
        raw_pr = _get(data, "dividend.payout_ratio")
        if raw_pr is not None:
            val = float(raw_pr)
            payout_ratio = round(val * 100 if val <= 1.0 else val, 2)

    # Dividend Growth
    # 1. Cek apakah sudah disediakan langsung di data (misal dari pre-fetch endpoint_finaldata)
    raw_dg = _get(data, "dividend.dividend_growth")
    if raw_dg is None:
        raw_dg = _get(data, "dividend_growth")

    div_growth = None
    if raw_dg is not None:
        try:
            div_growth = round(float(raw_dg), 2)
        except (ValueError, TypeError):
            div_growth = None

    # 2. Coba ambil dari endpoint_finaldata jika modul tersedia dan ada ticker/company riil
    if div_growth is None and HAS_UNIFIED_DATA:
        sym = _get(data, "company") or _get(data, "symbol") or _get(data, "ticker")
        if sym and isinstance(sym, str) and not sym.upper().startswith("TEST"):
            try:
                p_label = _get(data, "period", period) or period
                res = get_api_data(sym, data_type="dividend_growth", period=p_label)
                if res.get("status") == "SUCCESS":
                    val = res.get("data", {}).get("dividend_growth")
                    if val is not None:
                        div_growth = round(float(val), 2)
            except Exception:
                pass

    # 3. Fallback kalkulasi manual dari historical_data
    if div_growth is None:
        prev_period = get_previous_period(historical_data, offset=1)
        prev_div = _get(prev_period, "dividend.per_share") if prev_period else None

        if div_per_share is not None and prev_div is not None and float(prev_div) != 0:
            dg = safe_divide(float(div_per_share) - float(prev_div), float(prev_div))
            if dg is not None:
                div_growth = round(dg * 100, 2)

    return {
        "dividend_yield": div_yield,
        "payout_ratio": payout_ratio,
        "dividend_growth": div_growth
    }


# ============================================================================
# ENTRY POINT
# ============================================================================

def compute_derived_metrics(
    company_data: Any,
    historical_data: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
    Fungsi Entry Point Utama sesuai spesifikasi PLAN.md:
    
    company_data: Objek/dict yang merepresentasikan data fundamental & pasar terkini emiten.
    historical_data: List dari data periode-periode sebelumnya untuk menghitung
                     pertumbuhan, volatilitas, pergerakan moving average, dll.
    """
    if company_data is None:
        return {"status": "ERROR", "error": "invalid company_data"}

    company_name = _get(company_data, "company")
    if company_name is None:
        company_name = _get(company_data, "symbol") or _get(company_data, "ticker")
    if company_name is None:
        return {"status": "ERROR", "error": "invalid company_data: missing company identifier"}

    period = _get(company_data, "period", "current")
    hist = historical_data if historical_data is not None else []

    result = {
        "status": "SUCCESS",
        "company": company_name,
        "period": period,
        "valuation_metrics": compute_valuation_metrics(company_data),
        "growth_metrics": compute_growth_metrics(company_data, hist),
        "price_metrics": compute_price_metrics(company_data, hist),
        "ownership_metrics": compute_ownership_metrics(company_data, hist),
        "dividend_metrics": compute_dividend_metrics(company_data, hist, period=period)
    }

    return result


# ============================================================================
# UNIFIED DATA API INTEGRATION (Sesuai Rules unified_data)
# ============================================================================

def fetch_and_compute_derived_metrics(
    ticker: str,
    period: str = "current",
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Mengambil data riil dari Unified Data Layer (Sectors API + yFinance)
    dan menghitung derived metrics secara terintegrasi.
    """
    if not HAS_UNIFIED_DATA:
        return {
            "status": "ERROR",
            "error": "Modul unified_data.endpoint_finaldata tidak ditemukan di sys.path."
        }

    clean_ticker = ticker.upper().replace(".JK", "").strip()

    # 1. Ambil data harga historis (1 tahun untuk metrik return 1m, 3m, 1y, MA20, MA50)
    p_res = get_api_data(clean_ticker, data_type="price", period="1y", force_refresh=force_refresh)
    price_records = p_res.get("data", {}).get("records", []) if p_res.get("status") == "SUCCESS" else []

    # 2. Ambil data valuasi
    v_res = get_api_data(clean_ticker, data_type="valuation", period=period, force_refresh=force_refresh)
    v_data = v_res.get("data", {}) if v_res.get("status") == "SUCCESS" else {}

    # 3. Ambil data forecast & analis
    fc_res = get_api_data(clean_ticker, data_type="forecast", period=period, force_refresh=force_refresh)
    fc_data = fc_res.get("data", {}) if fc_res.get("status") == "SUCCESS" else {}

    # 4. Ambil data dividen
    div_res = get_api_data(clean_ticker, data_type="dividend", period="5y", force_refresh=force_refresh)
    div_data = div_res.get("data", {}) if div_res.get("status") == "SUCCESS" else {}

    # 4b. Ambil data dividen growth langsung dari endpoint_finaldata (sesuai PLAN.md line 179)
    div_growth_res = get_api_data(clean_ticker, data_type="dividend_growth", period=period, force_refresh=force_refresh)
    div_growth_data = div_growth_res.get("data", {}) if div_growth_res.get("status") == "SUCCESS" else {}
    fetched_div_growth = div_growth_data.get("dividend_growth") if isinstance(div_growth_data, dict) else None

    # 5. Ambil data pemegang saham & kepemilikan
    sh_res = get_api_data(clean_ticker, data_type="major_shareholders", period=period, force_refresh=force_refresh)
    sh_data = sh_res.get("data", {}) if sh_res.get("status") == "SUCCESS" else {}

    # 6. Ambil data peers industri
    peer_res = get_api_data(clean_ticker, data_type="peers", period=period, force_refresh=force_refresh)
    peer_data = peer_res.get("data", {}) if peer_res.get("status") == "SUCCESS" else {}

    # 7. Ambil laporan keuangan tahunan untuk histori pertumbuhan
    fin_res = get_api_data(clean_ticker, data_type="financials", period="5y", force_refresh=force_refresh)
    fin_statements = fin_res.get("data", {}).get("statements", {}) if fin_res.get("status") == "SUCCESS" else {}

    # Susun company_data terkini
    latest_close = price_records[-1].get("close") if price_records else None
    
    # Kumpulkan daftar pemegang saham
    shareholders_list = []
    if sh_data.get("major_shareholder_percentage"):
        shareholders_list.append({
            "name": sh_data.get("major_shareholder_name", "Major Shareholder"),
            "pct": sh_data.get("major_shareholder_percentage") * 100 if sh_data.get("major_shareholder_percentage") <= 1.0 else sh_data.get("major_shareholder_percentage")
        })

    # Susun historical_data tahunan/kuartalan dari laporan keuangan
    historical_periods = []
    if fin_statements:
        for year_str in sorted(fin_statements.keys()):
            stmt = fin_statements[year_str]
            historical_periods.append({
                "period": year_str,
                "growth": {
                    "revenue": stmt.get("total_revenue") or stmt.get("operating_revenue"),
                    "eps": stmt.get("basic_eps") or stmt.get("diluted_eps")
                }
            })

    # Susun objek company_data yang sesuai dengan skema PLAN.md
    company_data = {
        "company": clean_ticker,
        "period": period,
        "price": {
            "close": latest_close
        },
        "valuation": {
            "pe": v_data.get("trailing_pe") or v_data.get("forward_pe"),
            "pbv": v_data.get("price_to_book"),
            "market_cap": peer_data.get("market_cap") if isinstance(peer_data, dict) else None,
            "enterprise_to_ebitda": v_data.get("enterprise_to_ebitda")
        },
        "growth": {
            "revenue": (
                list(fin_statements.values())[0].get("total_revenue")
                if fin_statements else fc_data.get("revenue_estimate")
            ),
            "actual": (
                list(fin_statements.values())[0].get("total_revenue")
                if fin_statements else None
            ),
            "forecast": fc_data.get("revenue_estimate"),
            "eps": fc_data.get("eps_estimate")
        },
        "peers": [peer_data] if isinstance(peer_data, dict) and peer_data else (peer_data if isinstance(peer_data, list) else []),
        "ownership": {
            "insider_pct": sh_data.get("insiders_percent_held"),
            "shareholders": shareholders_list
        },
        "dividend": {
            "per_share": div_data.get("dividend_rate") or div_data.get("trailing_annual_dividend_rate"),
            "dividend_yield": div_data.get("dividend_yield"),
            "payout_ratio": div_data.get("payout_ratio"),
            "dividend_growth": fetched_div_growth
        }
    }

    # Jika ada histori harga, gunakan untuk price metrics; histori finansial untuk growth metrics
    # Gabungkan atau kirim sesuai kebutuhan
    combined_history = historical_periods if historical_periods else price_records

    # Jalankan engine perhitungan derived metrics
    metrics = compute_derived_metrics(company_data, historical_data=price_records)

    # Tambahkan metrik growth spesifik dari histori finansial jika tersedia
    if historical_periods:
        growth_from_fin = compute_growth_metrics(company_data, historical_periods)
        metrics["growth_metrics"].update({
            k: v for k, v in growth_from_fin.items() if v is not None
        })

    return metrics


# ============================================================================
# SELF-TEST & CLI
# ============================================================================

def _run_self_tests():
    """Menjalankan unit test sederhana untuk memverifikasi logika PLAN.md."""
    print("Menjalankan self-test formula derived_metrics.py...")

    # Mock company data
    mock_company = {
        "company": "TEST_CORP",
        "period": "2026-Q2",
        "price": {"close": 1000.0},
        "valuation": {
            "pe": 15.0,
            "pbv": 2.0,
            "market_cap": 100_000_000,
            "total_debt": 20_000_000,
            "cash": 10_000_000,
            "ebitda": 10_000_000
        },
        "peers": [
            {"company": "P1", "pe": 20.0, "pbv": 2.5},
            {"company": "P2", "pe": 10.0, "pbv": 1.5},
            {"company": "P3", "pe": 25.0, "pbv": 3.0}
        ],
        "growth": {
            "revenue": 120_000_000,
            "actual": 120_000_000,
            "forecast": 100_000_000,
            "eps": 50.0
        },
        "ownership": {
            "insider_pct": 25.0,
            "shareholders": [
                {"name": "H1", "pct": 40.0},
                {"name": "H2", "pct": 20.0},
                {"name": "H3", "pct": 10.0}
            ]
        },
        "institutional": {
            "total_buy_value": 5_000_000,
            "total_sell_value": 2_000_000
        },
        "dividend": {
            "per_share": 30.0
        }
    }

    # Mock historical data (price series & historical periods)
    mock_history = [
        {"price": {"close": 900.0}, "growth": {"revenue": 100_000_000}, "dividend": {"per_share": 25.0}, "ownership": {"insider_pct": 20.0}}
    ]

    # Test valuation
    val_m = compute_valuation_metrics(mock_company)
    assert val_m["pe_relative"] is not None
    # Peer avg PE = (20+10+25)/3 = 18.3333 -> 15 / 18.3333 = 0.8182
    assert abs(val_m["pe_relative"] - (15.0 / (55.0 / 3.0))) < 0.01
    # EV = 100M + 20M - 10M = 110M. EV/EBITDA = 110M / 10M = 11.0
    assert abs(val_m["ev_ebitda"] - 11.0) < 0.01

    # Test growth
    growth_m = compute_growth_metrics(mock_company, mock_history)
    # QoQ growth: (120M - 100M)/100M = 20%
    assert abs(growth_m["revenue_growth_qoq"] - 20.0) < 0.01
    # Forecast gap: (120M - 100M)/100M = 20%
    assert abs(growth_m["forecast_gap"] - 20.0) < 0.01

    # Test price metrics
    # Create artificial 300 days price series
    prices = [100.0 + i for i in range(300)]
    price_m = compute_price_metrics({"price": {"close": prices[-1]}}, prices)
    assert price_m["return_1m"] is not None
    assert price_m["volatility"] is not None
    assert price_m["price_vs_ma20"] is not None

    # Test ownership
    own_m = compute_ownership_metrics(mock_company, mock_history)
    # Net flow = 5M - 2M = 3M. Pct of MC = 3M / 100M = 3%
    assert abs(own_m["net_institutional_flow_pct"] - 3.0) < 0.01
    # Top 5 concentration: 40 + 20 + 10 = 70%
    assert abs(own_m["concentration_top5"] - 70.0) < 0.01

    # Test dividend (kalkulasi manual dari histori)
    div_m = compute_dividend_metrics(mock_company, mock_history)
    # Yield = 30 / 1000 = 3%
    assert abs(div_m["dividend_yield"] - 3.0) < 0.01
    # Payout = 30 / 50 = 60%
    assert abs(div_m["payout_ratio"] - 60.0) < 0.01
    # Growth = (30 - 25)/25 = 20%
    assert abs(div_m["dividend_growth"] - 20.0) < 0.01

    # Test dividend growth langsung dari input / endpoint_finaldata
    mock_ep_div = {
        "company": "TEST_EP",
        "price": {"close": 1000.0},
        "growth": {"eps": 50.0},
        "dividend": {
            "per_share": 30.0,
            "dividend_growth": 25.5
        }
    }
    div_m2 = compute_dividend_metrics(mock_ep_div)
    assert div_m2["dividend_growth"] == 25.5

    print("Semua self-test BERHASIL lolos tanpa kendala.")


if __name__ == "__main__":
    _run_self_tests()
    print("=" * 60)

    # Uji coba menggunakan ticker riil dari Unified Data
    target_ticker = sys.argv[1] if len(sys.argv) > 1 else "BBCA"
    target_period = sys.argv[2] if len(sys.argv) > 2 else "current"
    print(f"Menguji penghitungan Derived Metrics untuk ticker: {target_ticker} (period: {target_period})")
    res = fetch_and_compute_derived_metrics(target_ticker, period=target_period)
    print(json.dumps(res, indent=2, ensure_ascii=False))
