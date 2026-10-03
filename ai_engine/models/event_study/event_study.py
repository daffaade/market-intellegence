"""
event_study.py — Market Model Event Study (CAR / t-stat / p-value)
ai_engine/models/event_study/event_study.py

Menghitung Cumulative Abnormal Return (CAR) untuk setiap event korporasi
menggunakan OLS market model. Output JSON siap dikonsumsi backend Go.
Fungsi entry point: run_event_study(ticker, event_id=None).

Data policy:
  - Harga saham: via UnifiedDataLoader.get_historical_data() (getter resmi)
  - JKSE benchmark: via yfinance (^JKSE bukan emiten IDX — tidak di Sectors API)
  - events.csv: data manual (kalender event korporasi tidak di Sectors API)
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from scipy import stats
import yaml

# ── Path setup (ikuti konvensi repo: dua level ke atas menuju ai_engine/) ─────
CURRENT_DIR   = Path(__file__).resolve().parent    # models/event_study/
AI_ENGINE_DIR = CURRENT_DIR.parent.parent          # ai_engine/
REPO_ROOT     = AI_ENGINE_DIR.parent               # project root
for _p in [str(CURRENT_DIR), str(AI_ENGINE_DIR), str(REPO_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

CONFIG_PATH = AI_ENGINE_DIR / "config" / "event_study.yaml"
DATA_DIR    = AI_ENGINE_DIR / "data"
EVENTS_CSV  = DATA_DIR / "events.csv"


# ── Config helpers ────────────────────────────────────────────────────────────
def _load_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _cfg_int(cfg: Dict, *keys: str, default: int) -> int:
    cur: Any = cfg
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
    try:
        return int(cur)
    except (TypeError, ValueError):
        return default


def _cfg_float(cfg: Dict, *keys: str, default: float) -> float:
    cur: Any = cfg
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
    try:
        return float(cur)
    except (TypeError, ValueError):
        return default


# ── Data fetching ─────────────────────────────────────────────────────────────
def _get_data_loader():
    try:
        from ai_engine.core.data_loader import UnifiedDataLoader
        return UnifiedDataLoader()
    except ImportError:
        try:
            from core.data_loader import UnifiedDataLoader
            return UnifiedDataLoader()
        except ImportError:
            return None


def _fetch_price_series(ticker: str, data_loader=None) -> pd.Series:
    """Ambil harga penutupan harian. Prioritas: getter → yfinance fallback."""
    clean = ticker.upper().replace(".JK", "").strip()

    if data_loader and hasattr(data_loader, "get_historical_data"):
        try:
            df = data_loader.get_historical_data(clean, period="5y")
            if df is not None and not df.empty:
                df = df.copy()
                df.columns = [str(c).lower() for c in df.columns]
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"], errors="coerce")
                    df = df.set_index("date")
                else:
                    df.index = pd.to_datetime(df.index, errors="coerce")
                df = df.sort_index()
                if "close" in df.columns:
                    s = pd.to_numeric(df["close"], errors="coerce").dropna()
                    if len(s) > 10:
                        return s
        except Exception:
            pass

    try:
        import yfinance as yf
        raw = yf.download(f"{clean}.JK", period="5y", progress=False, auto_adjust=True)
        if not raw.empty:
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = [c[0].lower() for c in raw.columns]
            else:
                raw.columns = [c.lower() for c in raw.columns]
            raw.index = pd.to_datetime(raw.index)
            close = pd.to_numeric(raw["close"], errors="coerce").dropna()
            if len(close) > 10:
                return close
    except Exception:
        pass

    return pd.Series(dtype=float)


def _fetch_jkse_series() -> pd.Series:
    """Ambil JKSE index via yfinance (^JKSE bukan emiten IDX — tidak ada di Sectors API)."""
    try:
        import yfinance as yf
        raw = yf.download("^JKSE", period="5y", progress=False, auto_adjust=True)
        if not raw.empty:
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = [c[0].lower() for c in raw.columns]
            else:
                raw.columns = [c.lower() for c in raw.columns]
            raw.index = pd.to_datetime(raw.index)
            return pd.to_numeric(raw["close"], errors="coerce").dropna()
    except Exception:
        pass
    return pd.Series(dtype=float)


def _load_events(ticker: str) -> List[Dict[str, Any]]:
    try:
        from ai_engine.core.data_events import DataEventsGetter
        df = DataEventsGetter.get_corporate_events(ticker)
        if df.empty:
            return []
        
        events = df.to_dict(orient="records")
        for ev in events:
            # Transfer attributes for data quality
            ev["_data_quality"] = df.attrs.get("data_quality", "real")
            ev["_data_source"] = df.attrs.get("data_source", "real")
        return events
    except ImportError:
        return []


# ── Market model ──────────────────────────────────────────────────────────────
def _compute_event(
    event: Dict[str, str],
    ticker_ret: pd.Series,
    market_ret: pd.Series,
    cfg: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Hitung CAR, t-stat, p-value untuk satu event.
    Tidak ada look-ahead: kalkulasi hanya memakai data ≤ t + event_window_end.
    """
    ticker_name    = event.get("ticker", "").upper()
    event_date_str = event.get("date", "")
    event_type     = event.get("event_type", "")
    event_id       = f"{event_date_str}_{event_type}"

    try:
        event_date = pd.Timestamp(event_date_str)
    except Exception:
        return _build_error_result(event, "Format tanggal tidak valid", "missing")

    est_start   = _cfg_int(cfg,   "estimation_window", "start",          default=-250)
    est_end     = _cfg_int(cfg,   "estimation_window", "end",            default=-30)
    evt_start   = _cfg_int(cfg,   "event_window",      "start",          default=-5)
    evt_end     = _cfg_int(cfg,   "event_window",      "end",            default=5)
    min_obs     = _cfg_int(cfg,   "estimation_window", "min_obs",         default=80)
    min_partial = _cfg_int(cfg,   "fallback",          "min_obs_partial", default=30)
    sig_level   = _cfg_float(cfg, "significance_level",                   default=0.05)
    car_scale   = _cfg_float(cfg, "score", "car_high_threshold",          default=0.10)
    sig_boost   = _cfg_float(cfg, "score", "significance_boost",          default=1.20)

    common = ticker_ret.index.intersection(market_ret.index).sort_values()
    if len(common) < 20:
        return _build_error_result(event, "Data harga tidak cukup (< 20 hari trading)", "missing")

    tr        = ticker_ret.loc[common]
    mr        = market_ret.loc[common]
    all_dates = tr.index
    pos       = min(all_dates.searchsorted(event_date, side="left"), len(all_dates) - 1)

    est_s  = max(0, pos + est_start)
    est_e  = max(0, pos + est_end)
    if est_s >= est_e:
        return _build_error_result(event, "Estimation window terlalu sempit", "missing")

    est_tr = tr.iloc[est_s:est_e].values
    est_mr = mr.iloc[est_s:est_e].values

    data_quality = "ok"
    if len(est_tr) < min_partial:
        return _build_error_result(event, f"Histori terlalu pendek (n={len(est_tr)} < {min_partial})", "missing")
    if len(est_tr) < min_obs:
        data_quality = "partial"

    if len(est_tr) < 5:
        return _build_error_result(event, "Terlalu sedikit observasi untuk OLS", "missing")

    slope, intercept, _, _, _ = stats.linregress(est_mr, est_tr)
    residuals = est_tr - (intercept + slope * est_mr)
    resid_std = float(np.std(residuals, ddof=2)) if len(residuals) > 2 else 1e-8
    if resid_std < 1e-10:
        resid_std = 1e-8

    evt_s = max(0, pos + evt_start)
    evt_e = min(len(tr), pos + evt_end + 1)
    if evt_s >= evt_e:
        return _build_error_result(event, "Tidak ada data di event window", "missing")

    ar  = tr.iloc[evt_s:evt_e].values - (intercept + slope * mr.iloc[evt_s:evt_e].values)
    car = float(np.sum(ar))

    se_car  = resid_std * math.sqrt(len(ar))
    t_stat  = car / se_car if se_car > 0 else 0.0
    df_r    = max(1, len(est_tr) - 2)
    p_value = float(2 * stats.t.sf(abs(t_stat), df=df_r))
    sig     = p_value < sig_level

    raw_score = min(100.0, abs(car) / car_scale * 100.0)
    if sig:
        raw_score = min(100.0, raw_score * sig_boost)
    score = int(round(raw_score))

    th_high = _cfg_int(cfg, "score", "level_thresholds", "high",   default=70)
    th_med  = _cfg_int(cfg, "score", "level_thresholds", "medium", default=40)
    level   = "High" if score >= th_high else ("Medium" if score >= th_med else "Low")

    direction_str = f"+{car*100:.2f}%" if car >= 0 else f"{car*100:.2f}%"
    sig_str       = "signifikan pada 5%" if sig else "tidak signifikan pada 5%"

    return {
        "ticker":              ticker_name,
        "event_id":            event_id,
        "event_type":          event_type,
        "description":         event.get("description", ""),
        "event_date":          event_date_str,
        "car":                 round(car, 6),
        "t_stat":              round(t_stat, 4),
        "p_value":             round(p_value, 4),
        "significant_at_5pct": sig,
        "alpha":               round(float(intercept), 6),
        "beta":                round(float(slope), 4),
        "n_estimation":        len(est_tr),
        "level":               level,
        "score":               score,
        "evidence": [
            f"CAR[-5,+5] = {direction_str}, t-stat={t_stat:.2f}, p={p_value:.3f} ({sig_str})",
            f"Model pasar: alpha={intercept:.5f}, beta={slope:.4f}, n_estimasi={len(est_tr)}",
            f"Event: {event.get('description', event_type)} pada {event_date_str}",
        ],
        "data_quality": data_quality,
        "data_source":  "real",
    }


def _build_error_result(event: Dict[str, str], reason: str, data_quality: str) -> Dict[str, Any]:
    d, et = event.get("date", ""), event.get("event_type", "")
    return {
        "ticker": event.get("ticker", "").upper(),
        "event_id": f"{d}_{et}", "event_type": et,
        "description": event.get("description", ""), "event_date": d,
        "car": None, "t_stat": None, "p_value": None,
        "significant_at_5pct": None, "alpha": None, "beta": None,
        "n_estimation": 0, "level": "Low", "score": 0,
        "evidence": [f"Data tidak tersedia: {reason}"],
        "data_quality": data_quality, "data_source": "real",
    }


# ── Entry point ───────────────────────────────────────────────────────────────
def run_event_study(
    ticker: str,
    event_id: Optional[str] = None,
    _data_loader=None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Hitung CAR + t-stat + p-value untuk satu atau semua event korporasi ticker.

    Args:
        ticker:       Kode emiten IDX (mis. "BBCA", "GOTO")
        event_id:     "YYYY-MM-DD_event_type". None → semua event ticker.
        _data_loader: Opsional, untuk injeksi saat testing.
    """
    cfg    = _load_config()
    clean  = ticker.upper().replace(".JK", "").strip()
    events = _load_events(clean)

    if not events:
        missing: Dict[str, Any] = {
            "ticker": clean, "event_id": event_id, "event_type": None,
            "description": "", "event_date": None, "car": None, "t_stat": None,
            "p_value": None, "significant_at_5pct": None, "alpha": None, "beta": None,
            "n_estimation": 0, "level": "Low", "score": 0,
            "evidence": ["Tidak ada event ditemukan untuk ticker ini di events.csv"],
            "data_quality": "missing", "data_source": "seed",
        }
        return missing if event_id else [missing]

    if event_id:
        events = [e for e in events if f"{e['date']}_{e['event_type']}" == event_id]
        if not events:
            return _build_error_result(
                {"ticker": clean, "date": "", "event_type": ""},
                f"event_id '{event_id}' tidak ditemukan", "missing",
            )

    dl         = _data_loader or _get_data_loader()
    price_s    = _fetch_price_series(clean, dl)
    jkse_s     = _fetch_jkse_series()

    if price_s.empty or jkse_s.empty:
        results = [_build_error_result(e, "Gagal mengambil data harga historis", "missing") for e in events]
        return results[0] if event_id else results

    ticker_ret = price_s.pct_change().dropna()
    market_ret = jkse_s.pct_change().dropna()
    results    = [_compute_event(e, ticker_ret, market_ret, cfg) for e in events]
    return results[0] if (event_id and results) else results


def aggregate_car_by_event_type(
    tickers: Optional[List[str]] = None,
    _data_loader=None,
) -> Dict[str, Any]:
    """Agregasi rata-rata CAR per event_type lintas semua ticker prototype."""
    if tickers is None:
        tickers = ["BBCA", "AMRT", "TLKM", "ASII", "GOTO"]
    from collections import defaultdict
    cars_by_type: Dict[str, List[float]] = defaultdict(list)
    for tk in tickers:
        res = run_event_study(tk, _data_loader=_data_loader)
        for r in ([res] if isinstance(res, dict) else res):
            if r.get("car") is not None:
                cars_by_type[r["event_type"]].append(r["car"])
    return {
        "aggregated_by_event_type": {
            et: {
                "n_events": len(cl), "mean_car": round(float(np.mean(cl)), 6),
                "median_car": round(float(np.median(cl)), 6), "std_car": round(float(np.std(cl)), 6),
            }
            for et, cl in cars_by_type.items()
        },
        "tickers_included": tickers,
        "note": "Agregasi CAR per event_type lintas ticker prototype. Termasuk hasil tidak signifikan.",
    }
