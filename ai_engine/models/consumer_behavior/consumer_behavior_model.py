"""
Consumer behavior: Google search interest for a keyword (Indonesia) set against
the stocks of a sector.

- Search trend: 5 years of weekly Google Trends interest. The latest 4 complete
  weeks are compared with the same 4 weeks a year earlier (seasonality-safe) and
  with the 12 weeks before them.
- Sector basket: equal-weight weekly return of the sector's constituents
  (config/sector_map.yaml), with the correlation between 4-week changes in search
  interest and the basket's 4-week return, both same-period and with search
  leading by 4 weeks. Correlational only.
- Companies: TTM revenue growth from the cached Sectors report (no new fetch)
  and 20-session return.

Replaces an implementation whose company metrics were hard-coded in the code and
whose search-trend fallback returned a flat line of 50s presented as data.
"""
from __future__ import annotations

import json
import logging
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

from ai_engine.models.sector.sector_intelligence import load_sector_map

logger = logging.getLogger(__name__)

TRENDS_CACHE = Path(__file__).resolve().parent.parent.parent / "data" / "trends"
TRENDS_TTL = 24 * 3600
LEAD_WEEKS = 4
DISCLAIMER = ("Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan "
              "anjuran investasi personal (Bukan rekomendasi Beli/Jual).")

# Free-text industry words mapped to sector_map keys.
INDUSTRY_ALIASES = {
    "makanan": "Consumer Non-Cyclicals", "minuman": "Consumer Non-Cyclicals", "ritel": "Consumer Non-Cyclicals",
    "konsumen primer": "Consumer Non-Cyclicals", "consumer": "Consumer Non-Cyclicals",
    "otomotif": "Industrials", "fashion": "Consumer Cyclicals", "elektronik": "Consumer Cyclicals",
    "media": "Consumer Cyclicals", "bank": "Financials", "keuangan": "Financials",
    "teknologi": "Technology", "tech": "Technology", "telekomunikasi": "Infrastructures",
    "tambang": "Basic Materials", "batu bara": "Energy", "energi": "Energy", "minyak": "Energy",
    "kesehatan": "Healthcare", "farmasi": "Healthcare", "properti": "Properties & Real Estate",
    "transportasi": "Transportation & Logistic", "logistik": "Transportation & Logistic",
}


def resolve_sector(industry: str, sectors: Dict[str, Any]) -> Optional[str]:
    q = industry.strip().lower()
    for key, spec in sectors.items():
        if q in (key.lower(), str(spec.get("label", "")).lower()):
            return key
    for word, key in INDUSTRY_ALIASES.items():
        if word in q:
            return key
    return None


def _id(text: str) -> str:
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def fetch_search_trend(keyword: str) -> Optional[pd.Series]:
    """Weekly Google Trends interest (0-100) for Indonesia, complete weeks only, cached a day."""
    TRENDS_CACHE.mkdir(parents=True, exist_ok=True)
    path = TRENDS_CACHE / (keyword.replace("/", "_").replace(" ", "_") + ".json")
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - cached["fetched_at"] < TRENDS_TTL:
            return pd.Series(cached["values"], index=pd.to_datetime(cached["dates"]), dtype=float)
    except (OSError, ValueError, KeyError):
        pass
    try:
        from pytrends.request import TrendReq
        tr = TrendReq(hl="id-ID", tz=420, timeout=(10, 25))
        tr.build_payload([keyword], timeframe="today 5-y", geo="ID")
        df = tr.interest_over_time()
    except Exception as e:
        logger.warning("Google Trends unavailable for %r: %s", keyword, e)
        return None
    if df is None or df.empty or keyword not in df:
        return None
    if "isPartial" in df:
        df = df[~df["isPartial"].astype(bool)]
    s = df[keyword].astype(float)
    path.write_text(json.dumps({"fetched_at": time.time(), "dates": [d.strftime("%Y-%m-%d") for d in s.index],
                                "values": s.tolist()}), encoding="utf-8")
    return s


def _basket_weekly(symbols: List[str]) -> Optional[pd.DataFrame]:
    import yfinance as yf
    raw = yf.download(" ".join(f"{s}.JK" for s in symbols), period="2y", progress=False, auto_adjust=True)
    close = raw["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame(f"{symbols[0]}.JK")
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close.rename(columns=lambda c: c.replace(".JK", ""))


def _revenue_growth(symbol: str) -> Optional[float]:
    try:
        from data_processing.data_sectors.fundamentals import load_report
        cached = load_report(symbol, max_age=30 * 24 * 3600)
    except Exception:
        return None
    if not cached:
        return None
    v = (cached["report"].get("financials") or {}).get("yoy_ttm_revenue_growth")
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _corr(x: pd.Series, y: pd.Series) -> Optional[Dict[str, Any]]:
    both = pd.concat([x, y], axis=1).dropna()
    if len(both) < 30:
        return None
    r, p = stats.pearsonr(both.iloc[:, 0], both.iloc[:, 1])
    return {"r": round(float(r), 3), "p_value": round(float(p), 4), "significant": bool(p < 0.05), "n_weeks": int(len(both))}


class ConsumerBehaviorModel:
    def __init__(self, data_loader=None, sector_map_path: str = None):
        self.data_loader = data_loader

    def analyze(self, keyword: str, industry: str) -> Dict[str, Any]:
        keyword = keyword.strip().lower()
        cfg = load_sector_map()
        sectors = cfg.get("sectors", {})
        sector = resolve_sector(industry, sectors)
        flags: List[str] = []
        result: Dict[str, Any] = {
            "keyword": keyword, "industry": industry, "sector": sector,
            "sector_label": sectors.get(sector, {}).get("label") if sector else None,
            "as_of": datetime.now().strftime("%Y-%m-%d"), "disclaimer": DISCLAIMER,
        }
        if not sector:
            result.update(error=f"Industri '{industry}' tidak dikenali",
                          available_sectors=[{"key": k, "label": v.get("label", k)} for k, v in sectors.items()])
            return result

        # 1. Search trend
        trend = fetch_search_trend(keyword)
        trend_info = None
        if trend is None or len(trend) < 60 or trend.sum() == 0:
            flags.append("search_trend_unavailable")
        else:
            recent = float(trend.iloc[-4:].mean())
            year_ago = float(trend.iloc[-56:-52].mean()) if len(trend) >= 56 else None
            prior = float(trend.iloc[-16:-4].mean())
            yoy = recent / year_ago - 1 if year_ago else None
            mom = recent / prior - 1 if prior else None
            pct = float((trend < recent).mean() * 100)
            trend_info = {
                "recent_4w": round(recent, 1),
                "yoy_pct": round(yoy * 100, 1) if yoy is not None else None,
                "vs_prev_12w_pct": round(mom * 100, 1) if mom is not None else None,
                "percentile_5y": round(pct, 0),
                "weekly": [{"date": d.strftime("%Y-%m-%d"), "value": float(v)} for d, v in trend.iloc[-104:].items()],
            }

        # 2. Sector basket and companies
        symbols = sectors[sector].get("symbols", [])
        companies, basket_corr, basket_rs = [], {}, None
        try:
            closes = _basket_weekly(symbols)
            daily_ret = closes.pct_change()
            for sym in symbols:
                if sym not in closes or closes[sym].dropna().size < 30:
                    continue
                s = closes[sym].dropna()
                companies.append({
                    "symbol": sym,
                    "revenue_growth_ttm": (lambda g: round(g * 100, 1) if g is not None else None)(_revenue_growth(sym)),
                    "return_20d_pct": round(float(s.iloc[-1] / s.iloc[-21] - 1) * 100, 1),
                })
            basket = (1 + daily_ret.mean(axis=1).fillna(0)).cumprod()
            basket_w = basket.resample("W-SUN").last()  # Google Trends weeks start on Sunday
            if len(basket) > 61:
                basket_rs = float(basket.iloc[-1] / basket.iloc[-61] - 1)
            if trend is not None and len(trend) >= 60:
                t = trend.copy()
                t.index = t.index + pd.Timedelta(days=6)  # label each week by its last day
                t = t.resample("W-SUN").last()
                search_chg = t.pct_change(LEAD_WEEKS).replace([np.inf, -np.inf], np.nan)
                basket_chg = basket_w.pct_change(LEAD_WEEKS)
                basket_corr = {
                    "same_period": _corr(search_chg, basket_chg),
                    "search_leads_4w": _corr(search_chg, basket_chg.shift(-LEAD_WEEKS)),
                }
        except Exception as e:
            logger.warning("sector basket failed for %s: %s", sector, e)
            flags.append("price_data_unavailable")

        growths = [c["revenue_growth_ttm"] for c in companies if c["revenue_growth_ttm"] is not None]
        med_growth = float(np.median(growths)) / 100 if growths else None

        # 3. Score: each available input moves it away from 50; missing inputs don't.
        score, parts = 50.0, 0
        if trend_info and trend_info["yoy_pct"] is not None:
            score += 20 * float(np.clip(trend_info["yoy_pct"] / 30, -1, 1)); parts += 1
        if med_growth is not None:
            score += 15 * float(np.clip(med_growth / 0.20, -1, 1)); parts += 1
        if basket_rs is not None:
            score += 15 * float(np.clip(basket_rs / 0.15, -1, 1)); parts += 1
        score = round(float(np.clip(score, 0, 100)), 1)
        direction = "Positive" if score >= 60 else ("Negative" if score <= 40 else "Neutral")
        lead = (basket_corr or {}).get("search_leads_4w")
        confidence = "High" if parts == 3 and lead and lead["significant"] else ("Medium" if parts >= 2 else "Low")

        evidence = []
        if trend_info:
            if trend_info["yoy_pct"] is not None:
                yoy_text = _id(format(trend_info["yoy_pct"], "+.1f"))
                evidence.append(f"Minat pencarian '{keyword}' 4 minggu terakhir {yoy_text}% dibanding periode yang sama tahun lalu")
            evidence.append(f"Berada di persentil {int(trend_info['percentile_5y'])} dari 5 tahun terakhir")
        if growths:
            evidence.append(f"Median pertumbuhan pendapatan TTM {len(growths)} emiten sektor: {_id(format(med_growth * 100, '+.1f'))}%")
        if basket_rs is not None:
            evidence.append(f"Saham sektor 60 sesi terakhir: {_id(format(basket_rs * 100, '+.1f'))}%")
        if lead:
            evidence.append(
                f"Korelasi perubahan pencarian dengan return sektor 4 minggu berikutnya: {_id(format(lead['r'], '.2f'))}"
                + ("" if lead["significant"] else " (tidak signifikan)")
            )

        result.update(
            search_trend=trend_info,
            correlation=basket_corr or None,
            sector_return_60d_pct=round(basket_rs * 100, 1) if basket_rs is not None else None,
            companies=companies,
            impact_signal={"impact_score": score, "impact_direction": direction, "confidence_level": confidence},
            evidence=evidence,
            data_quality_flags=flags,
            method="Google Trends (Indonesia) vs saham sektor; korelasional, bukan kausal",
        )
        return result
