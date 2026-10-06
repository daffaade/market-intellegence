import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yaml

from ai_engine.core.data_loader import UnifiedDataLoader

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"

def _load_macro_series() -> pd.DataFrame:
    try:
        from ai_engine.core.data_macro import get_macro_series
        return get_macro_series()
    except ImportError:
        return pd.DataFrame()

def _detect_forecast_revisions(
    forecast_series: pd.Series, 
    threshold_pp: float = 2.0
) -> List[Dict[str, Any]]:
    revisions = []
    if forecast_series.empty or len(forecast_series) < 2:
        return revisions
        
    diffs = forecast_series.diff()
    for date, diff in diffs.items():
        if pd.isna(diff):
            continue
        if abs(diff) >= threshold_pp:
            direction = "up" if diff > 0 else "down"
            revisions.append({
                "date": date,
                "direction": direction,
                "magnitude_pp": round(diff, 2)
            })
    return revisions

def _detect_macro_shocks(
    macro_df: pd.DataFrame, 
    thresholds: Dict[str, float]
) -> List[Dict[str, Any]]:
    shocks = []
    if macro_df.empty:
        return shocks
        
    # macro_df has columns [date, variable, value]
    for var in macro_df["variable"].unique():
        var_lower = var.lower()
        if var_lower not in thresholds:
            continue
            
        thresh = thresholds[var_lower]
        sub = macro_df[macro_df["variable"] == var].copy().sort_values("date")
        
        if var_lower == "bi_rate":
            # absolute diff for bps
            sub["diff"] = sub["value"].diff()
            mask = sub["diff"].abs() >= thresh
        else:
            # pct change
            sub["diff"] = sub["value"].pct_change()
            mask = sub["diff"].abs() >= thresh
            
        shock_dates = sub[mask]
        for _, row in shock_dates.iterrows():
            val = row["diff"]
            change_str = f"{val:+.2f}" if var_lower == "bi_rate" else f"{val*100:+.1f}%"
            shocks.append({
                "date": row["date"],
                "variable": var,
                "change": change_str
            })
            
    return shocks

def _sanitize_evidence(evidence: List[str]) -> List[str]:
    BLOCKLIST = ["menyebabkan", "causes", "akibat", "berakibat", "impacted", "mengakibatkan", "dampak", "memicu", "trigger", "karena"]
    sanitized = []
    for line in evidence:
        lower_line = line.lower()
        if any(w in lower_line for w in BLOCKLIST):
            sanitized.append(line + " (Catatan: Hubungan bersifat korelasional, bukan kausal)")
        else:
            sanitized.append(line)
    return sanitized

def run_macro_impact(ticker: str) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {}
    try:
        cfg_path = CONFIG_DIR / "macro_impact.yaml"
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Gagal load config macro_impact: {e}")
        
    rev_thresh = cfg.get("forecast_revision_threshold_pp", 2.0)
    window_days = cfg.get("co_occurrence_window_days", 30)
    macro_thresh = cfg.get("shock_thresholds", {
        "usdidr": 0.03,    
        "brent": 0.10,     
        "bi_rate": 0.25,   
        "inflation": 0.005 
    })
    
    price_df = UnifiedDataLoader.get_historical_data(ticker)
    macro_df = _load_macro_series()
    
    data_quality = "ok"
    if macro_df.empty or price_df.empty:
        data_quality = "missing"
    elif len(price_df) < 250:
        data_quality = "partial"
        
    if not price_df.empty:
        # P2 strict rule: proxy is return_20d * 1.5, same as forecast_model
        price_df["return_20d"] = price_df["close"].pct_change(20) * 100
        forecast_proxy = price_df["return_20d"].dropna() * 1.5
    else:
        forecast_proxy = pd.Series(dtype=float)
        
    revisions = _detect_forecast_revisions(forecast_proxy, threshold_pp=rev_thresh)
    shocks = _detect_macro_shocks(macro_df, macro_thresh)
    
    co_occurrences = []
    for rev in revisions:
        rev_date = pd.to_datetime(rev["date"])
        window_start = rev_date - pd.Timedelta(days=window_days)
        
        valid_shocks = [s for s in shocks if window_start <= pd.to_datetime(s["date"]) <= rev_date]
        
        if valid_shocks:
            best_shock = sorted(valid_shocks, key=lambda x: pd.to_datetime(x["date"]), reverse=True)[0]
            diff_days = (rev_date - pd.to_datetime(best_shock["date"])).days
            
            co_occurrences.append({
                "date": rev_date.strftime("%Y-%m-%d"),
                "direction": rev["direction"],
                "magnitude_pp": rev["magnitude_pp"],
                "co_occurring_macro_event": {
                    "variable": best_shock["variable"].upper(),
                    "change": best_shock["change"],
                    "date": best_shock["date"].strftime("%Y-%m-%d")
                },
                "within_window_days": diff_days
            })
            
    n_revisions = len(revisions)
    n_co = len(co_occurrences)
    co_rate = (n_co / n_revisions) if n_revisions > 0 else 0.0
    
    if not macro_df.empty and len(macro_df["date"].unique()) > 1:
        dates = pd.to_datetime(macro_df["date"])
        total_days = (dates.max() - dates.min()).days
        if total_days > 0:
            base_rate = min(1.0, (len(shocks) / total_days) * window_days)
        else:
            base_rate = 0.2
    else:
        base_rate = 0.2
        
    if n_revisions == 0:
        score = 0
        level = "Low"
    else:
        raw_score = 50 + ((co_rate - base_rate) * 100)
        score = max(0, min(100, int(raw_score)))
        
        if score >= 70:
            level = "High"
        elif score >= 40:
            level = "Medium"
        else:
            level = "Low"
            
    evidence = []
    if co_occurrences:
        latest = co_occurrences[-1]
        ev = (f"Forecast proxy {ticker} direvisi {latest['direction']} ({latest['magnitude_pp']}pp) "
              f"pada {latest['date']}, bertepatan dengan shock {latest['co_occurring_macro_event']['variable']} "
              f"sebesar {latest['co_occurring_macro_event']['change']} {latest['within_window_days']} hari sebelumnya (korelasional, bukan kausal).")
        evidence.append(ev)
        
    evidence.append(
        f"Dari {n_revisions} revisi forecast historis, {co_rate*100:.1f}% bertepatan dengan macro shock, "
        f"vs base rate {base_rate*100:.1f}%."
    )
    evidence = _sanitize_evidence(evidence)

    return {
        "ticker": ticker,
        "as_of": datetime.now().strftime("%Y-%m-%d"),
        "forecast_revisions": co_occurrences,
        "co_occurrence_rate": round(co_rate, 3),
        "base_rate": round(base_rate, 3),
        "level": level,
        "score": score if not macro_df.empty else None,
        "evidence": evidence,
        "data_quality": data_quality if data_quality != "ok" else "proxy",
        "data_source": "real" if not macro_df.empty else "missing"
    }
