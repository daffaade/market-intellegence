"""
Opportunity / risk scoring from named, explainable factors.

Every factor has a real input (price history, the Sectors company report, or
yfinance fundamentals as a fallback), a stated reference it is compared with,
and a 0..1 score. Factors whose input is missing are left out and the weights
are renormalised over the ones that remain, so a stock with partial data (e.g.
one requested on demand that Sectors does not cover) still gets an honest
score, with lower confidence.

This replaces the earlier scoring, which compared price-derived "proxies"
(20-day return labelled growth, inverted 60-day return labelled valuation,
volume z-score labelled institutional flow) against hard-coded peer medians.
"""
from __future__ import annotations

import math
import threading
import time
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# ── Weights ───────────────────────────────────────────────────────────────────
OPP_WEIGHTS = {
    "relative_momentum": 0.20,
    "trend": 0.10,
    "valuation": 0.25,
    "earnings_growth": 0.20,
    "foreign_flow": 0.10,       # daily net foreign flow (Sectors)
    "institutional_flow": 0.05,  # monthly institutional holdings change (Sectors report)
    "forecast": 0.10,  # scaled further by the model's measured skill
}

# Sectors index/foreign-flow windows are capped at 90 calendar days (~62 sessions).
MOMENTUM_SESSIONS = 60
FLOW_SESSIONS = 20
RISK_WEIGHTS = {
    "volatility": 0.25,
    "drawdown": 0.20,
    "liquidity": 0.15,
    "valuation_stretch": 0.15,
    "leverage": 0.10,
    "downtrend": 0.10,
    "anomaly": 0.05,
}

BULLISH_AT = 58.0
BEARISH_AT = 42.0


def _mm(x: float, lo: float, hi: float) -> float:
    """Linear map of x from [lo, hi] to [0, 1], clipped."""
    if hi == lo:
        return 0.5
    return float(np.clip((x - lo) / (hi - lo), 0.0, 1.0))


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or math.isinf(f) else f


def _id_number(text: str) -> str:
    """'1,234.5' -> '1.234,5' (Indonesian separators)."""
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def _pct(x: float, nd: int = 1) -> str:
    return _id_number(f"{x * 100:+,.{nd}f}") + "%"


def _fmt(x: float, nd: int = 1) -> str:
    return _id_number(f"{x:,.{nd}f}")


# ── Inputs ────────────────────────────────────────────────────────────────────
_ihsg_cache: Dict[str, Any] = {}
_ihsg_lock = threading.Lock()


def ihsg_close() -> Optional[pd.Series]:
    """
    IHSG daily closes for relative performance: Sectors index-daily (cached a day
    on disk), falling back to yfinance ^JKSE. Cached in memory for 6 hours.
    """
    with _ihsg_lock:
        hit = _ihsg_cache.get("s")
        if hit and time.time() - hit[0] < 6 * 3600:
            return hit[1]
    try:
        from data_processing.data_sectors.market_series import get_index_daily
        idx = get_index_daily("ihsg")
    except Exception:
        idx = None
    if idx and len(idx["points"]) > MOMENTUM_SESSIONS:
        close = pd.Series(
            [p["price"] for p in idx["points"]],
            index=pd.to_datetime([p["date"] for p in idx["points"]]),
            dtype=float,
        )
        with _ihsg_lock:
            _ihsg_cache["s"] = (time.time(), close)
        return close
    try:
        import yfinance as yf
        raw = yf.download("^JKSE", period="2y", progress=False, auto_adjust=True)
        close = raw["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = close.dropna()
        close.index = pd.to_datetime(close.index).tz_localize(None)
    except Exception:
        return None
    with _ihsg_lock:
        _ihsg_cache["s"] = (time.time(), close)
    return close


def fundamentals_snapshot(symbol: str) -> Dict[str, Any]:
    """
    Valuation, growth, leverage and institutional flow for one stock.
    Prefers the cached Sectors report (no new credit is spent here), falls back
    to yfinance .info with sanity bounds, which is often wrong for IDX tickers.
    """
    sym = symbol.replace(".JK", "").upper()
    out: Dict[str, Any] = {"source": None}

    try:
        from data_processing.data_sectors.fundamentals import load_report
        cached = load_report(sym, max_age=30 * 24 * 3600)
    except Exception:
        cached = None

    if cached:
        rep = cached["report"]
        out["source"] = "sectors"
        hv = (rep.get("valuation") or {}).get("historical_valuation")
        if isinstance(hv, list):
            hv = max((h for h in hv if isinstance(h, dict)), key=lambda h: str(h.get("year")), default=None)
        if isinstance(hv, dict):
            out["pe"], out["pe_peer"] = _num(hv.get("pe")), _num(hv.get("pe_peer_avg"))
            out["pb"], out["pb_peer"] = _num(hv.get("pb")), _num(hv.get("pb_peer_avg"))
        fin = rep.get("financials") or {}
        out["earnings_growth"] = _num(fin.get("yoy_ttm_earnings_growth"))
        out["revenue_growth"] = _num(fin.get("yoy_ttm_revenue_growth"))
        ratios = fin.get("historical_financial_ratio") or []
        if ratios:
            last = max(ratios, key=lambda r: str(r.get("year")))
            out["roe"] = _num((last.get("profitability") or {}).get("roe"))
            out["der"] = _num((last.get("leverage") or {}).get("debt_to_equity_ratio"))
        overview = rep.get("overview") or {}
        out["sector"] = overview.get("sector")
        rows = fin.get("historical_financials") or []
        if rows:
            out["shares_outstanding"] = _num(max(rows, key=lambda r: str(r.get("year"))).get("outstanding_shares"))
        flow = (rep.get("ownership") or {}).get("institutional_transaction_flow") or []
        flow = sorted((f for f in flow if f.get("date")), key=lambda f: f["date"])
        if flow:
            # Reporting periods are irregular (e.g. Apr, Jun, Jul, Aug), so take the
            # periods within 90 days of the latest one rather than the last N rows.
            end = pd.Timestamp(flow[-1]["date"])
            recent = [f for f in flow if pd.Timestamp(f["date"]) > end - pd.Timedelta(days=90)]
            out["inst_net_3m"] = sum(_num(f.get("net_transaction")) or 0 for f in recent)
            out["inst_flow_as_of"] = flow[-1]["date"]
    else:
        try:
            import yfinance as yf
            info = yf.Ticker(f"{sym}.JK").info or {}
        except Exception:
            info = {}
        if info:
            out["source"] = "yfinance"
            pe, pb = _num(info.get("trailingPE")), _num(info.get("priceToBook"))
            out["pe"] = pe if pe is not None and 0 < pe < 200 else None
            out["pb"] = pb if pb is not None and 0 < pb < 50 else None
            eg = _num(info.get("earningsGrowth"))
            out["earnings_growth"] = eg if eg is not None and -1 < eg < 5 else None
            out["roe"] = _num(info.get("returnOnEquity"))
            der = _num(info.get("debtToEquity"))
            out["der"] = der / 100 if der is not None else None  # yfinance reports percent
            out["sector"] = info.get("sector")
    return out


def _bench_return(bench: Optional[pd.Series], start, end) -> Optional[float]:
    """Benchmark return over the same dates as the stock (None if it does not cover them)."""
    if bench is None or bench.empty:
        return None
    b = bench[(bench.index >= start - pd.Timedelta(days=4)) & (bench.index <= end)]
    if len(b) < 2 or b.index[0] > start + pd.Timedelta(days=4):
        return None
    return float(b.iloc[-1]) / float(b.iloc[0]) - 1


# ── Factor engine ─────────────────────────────────────────────────────────────
def _factor(key, side, label, value_text, reference, score, favorable, weight_scale=1.0, note=None):
    return {
        "key": key,
        "side": side,
        "label": label,
        "value": value_text,
        "reference": reference,
        "score": round(float(score), 4),
        "favorable": favorable,  # True = supports the stock, False = weighs on it, None = neutral
        "weight_scale": weight_scale,
        "note": note,
    }


def _is_financial(sector: Optional[str]) -> bool:
    return bool(sector) and any(s in sector.lower() for s in ("financ", "bank"))


def compute_signals(
    symbol: str,
    price_df: pd.DataFrame,
    forecast_h7: Optional[float] = None,
    forecast_skill: Optional[float] = None,
    anomaly: Optional[Dict[str, Any]] = None,
    fundamentals: Optional[Dict[str, Any]] = None,
    benchmark: Optional[pd.Series] = None,
    foreign_flow: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    df = price_df.copy()
    if "date" in df.columns:
        df = df.set_index(pd.to_datetime(df["date"]))
    df.index = pd.to_datetime(df.index).tz_localize(None)
    close = df["close"].astype(float).dropna()
    fund = fundamentals if fundamentals is not None else fundamentals_snapshot(symbol)
    bench = benchmark if benchmark is not None else ihsg_close()
    if foreign_flow is None and fundamentals is None:
        try:
            from data_processing.data_sectors.market_series import get_foreign_flow
            foreign_flow = get_foreign_flow(symbol)
        except Exception:
            foreign_flow = None

    factors: List[Dict[str, Any]] = []
    last = float(close.iloc[-1])

    # ── Opportunity ──
    if len(close) > MOMENTUM_SESSIONS:
        start_day = close.index[-MOMENTUM_SESSIONS - 1]
        ret_3m = last / float(close.iloc[-MOMENTUM_SESSIONS - 1]) - 1
        bench_3m = _bench_return(bench, start_day, close.index[-1])
        rel = ret_3m - (bench_3m or 0.0)
        factors.append(_factor(
            "relative_momentum", "opportunity", f"Kinerja {MOMENTUM_SESSIONS} sesi vs IHSG",
            _pct(ret_3m), f"IHSG {_pct(bench_3m)}" if bench_3m is not None else "IHSG tidak tersedia",
            _mm(rel, -0.20, 0.20), rel > 0.02 if abs(rel) > 0.02 else None,
        ))

    ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
    if ma200:
        gap = last / ma200 - 1
        factors.append(_factor(
            "trend", "opportunity", "Harga vs rata-rata 200 hari",
            _pct(gap), "MA200", _mm(gap, -0.15, 0.15), gap > 0.02 if abs(gap) > 0.02 else None,
        ))

    pe, pe_peer = fund.get("pe"), fund.get("pe_peer")
    pb, pb_peer = fund.get("pb"), fund.get("pb_peer")
    val_ratio = None

    def usable(v, peer, cap):
        # A PER/PBV far from its peers usually means near-zero or one-off earnings
        # (e.g. a company that has just turned profitable), not a real valuation.
        return v and peer and 0 < v <= cap and peer > 0 and v / peer <= 4

    if usable(pe, pe_peer, 80):
        val_ratio, val_label, val_text, ref = pe / pe_peer, "PER vs rata-rata peer", f"{_fmt(pe)}x", f"{_fmt(pe_peer)}x"
    elif usable(pb, pb_peer, 30):
        val_ratio, val_label, val_text, ref = pb / pb_peer, "PBV vs rata-rata peer", f"{_fmt(pb, 2)}x", f"{_fmt(pb_peer, 2)}x"
    if val_ratio is not None:
        discount = 1 - val_ratio  # +0.3 = 30% cheaper than peers
        factors.append(_factor(
            "valuation", "opportunity", val_label, val_text, ref,
            _mm(discount, -0.5, 0.5), discount > 0.1 if abs(discount) > 0.1 else None,
        ))
        stretch = val_ratio - 1
        factors.append(_factor(
            "valuation_stretch", "risk", val_label.replace("vs", "di atas"), val_text, ref,
            _mm(stretch, 0.0, 1.0), False if stretch > 0.25 else (True if stretch < 0 else None),
        ))

    eg = fund.get("earnings_growth")
    if eg is not None:
        factors.append(_factor(
            "earnings_growth", "opportunity", "Pertumbuhan laba (TTM, YoY)",
            _pct(eg), "0%", _mm(eg, -0.20, 0.30), eg > 0.05 if abs(eg) > 0.05 else None,
        ))

    flow_pts = [p for p in ((foreign_flow or {}).get("points") or []) if p.get("net") is not None]
    if len(flow_pts) >= FLOW_SESSIONS and "volume" in df.columns:
        recent = flow_pts[-FLOW_SESSIONS:]
        net = sum(float(p["net"]) for p in recent)
        turnover = float((df["close"] * df["volume"]).iloc[-FLOW_SESSIONS:].sum())
        if turnover > 0:
            share = net / turnover
            factors.append(_factor(
                "foreign_flow", "opportunity", f"Arus bersih asing {FLOW_SESSIONS} sesi",
                f"Rp {_fmt(net / 1e9)} M ({_pct(share)} nilai transaksi)", "0",
                _mm(share, -0.10, 0.10), share > 0.01 if abs(share) > 0.01 else None,
            ))

    inst = fund.get("inst_net_3m")
    shares = fund.get("shares_outstanding")
    if inst is not None and shares:
        share_of = inst / shares
        factors.append(_factor(
            "institutional_flow", "opportunity", "Arus bersih institusi 90 hari",
            _pct(share_of, 2) + " saham beredar", "0%",
            _mm(share_of, -0.02, 0.02), share_of > 0.002 if abs(share_of) > 0.002 else None,
        ))

    if forecast_h7 is not None:
        skill = float(forecast_skill or 0.0)
        h7 = float(np.clip(forecast_h7, -0.10, 0.10))
        factors.append(_factor(
            "forecast", "opportunity", "Proyeksi model H+7",
            _pct(h7, 2), "0%", _mm(h7, -0.05, 0.05),
            (h7 > 0.005 if abs(h7) > 0.005 else None) if skill > 0 else None,
            weight_scale=skill,
            note=None if skill > 0 else "Bobot 0: akurasi arah model pada data uji tidak di atas tebakan acak",
        ))

    # ── Risk ──
    rets = close.pct_change().dropna()
    if len(rets) >= 60:
        vol = float(rets.iloc[-60:].std() * math.sqrt(252))
        factors.append(_factor(
            "volatility", "risk", "Volatilitas tahunan (60 hari)", f"{_fmt(vol * 100)}%", "15–70%",
            _mm(vol, 0.15, 0.70), False if vol > 0.45 else (True if vol < 0.25 else None),
        ))
    if len(close) >= 120:
        window = close.iloc[-252:]
        dd = float((window / window.cummax() - 1).min())
        factors.append(_factor(
            "drawdown", "risk", "Penurunan terdalam 1 tahun", _pct(dd), "10–60%",
            _mm(-dd, 0.10, 0.60), False if dd < -0.35 else (True if dd > -0.15 else None),
        ))
    if "volume" in df.columns and len(df) >= 60:
        value_traded = float((df["close"] * df["volume"]).iloc[-60:].mean())
        if value_traded > 0:
            lv = math.log10(value_traded)
            factors.append(_factor(
                "liquidity", "risk", "Nilai transaksi harian rata-rata",
                f"Rp {_fmt(value_traded / 1e9)} M", "Rp 1–300 M",
                1 - _mm(lv, 9.0, 11.5), False if value_traded < 5e9 else (True if value_traded > 1e11 else None),
            ))
    der = fund.get("der")
    if der is not None and not _is_financial(fund.get("sector")):
        factors.append(_factor(
            "leverage", "risk", "Rasio utang terhadap ekuitas", f"{_fmt(der, 2)}x", "0,5–2,5x",
            _mm(der, 0.5, 2.5), False if der > 1.5 else (True if der < 0.5 else None),
        ))
    if ma200:
        gap = last / ma200 - 1
        factors.append(_factor(
            "downtrend", "risk", "Jarak di bawah MA200", _pct(gap), "MA200",
            _mm(-gap, 0.0, 0.20), False if gap < -0.05 else None,
        ))
    if anomaly and anomaly.get("status") == "success":
        score = float(anomaly.get("anomaly_score") or 0) / 100
        flagged = bool(anomaly.get("is_anomaly"))
        factors.append(_factor(
            "anomaly", "risk", "Anomali pergerakan 5 sesi terakhir",
            "Ya" if flagged else "Tidak", "Isolation Forest",
            1.0 if flagged else score, False if flagged else None,
        ))

    # ── Aggregate ──
    def aggregate(side: str, weights: Dict[str, float]):
        used = [(f, weights[f["key"]] * f["weight_scale"]) for f in factors if f["side"] == side and f["key"] in weights]
        total = sum(w for _, w in used)
        coverage = total / sum(weights.values())
        if total <= 0:
            return 50.0, coverage, {}
        score = sum(f["score"] * w for f, w in used) / total * 100
        return round(float(np.clip(score, 1, 99)), 1), coverage, {f["key"]: round(w / total, 3) for f, w in used if w > 0}

    opp, opp_cov, opp_w = aggregate("opportunity", OPP_WEIGHTS)
    risk, risk_cov, risk_w = aggregate("risk", RISK_WEIGHTS)
    for f in factors:
        f["weight"] = (opp_w if f["side"] == "opportunity" else risk_w).get(f["key"], 0.0)

    coverage = (opp_cov + risk_cov) / 2
    confidence = "High" if coverage >= 0.85 else ("Medium" if coverage >= 0.6 else "Low")
    direction = "Positive" if opp >= BULLISH_AT else ("Negative" if opp <= BEARISH_AT else "Neutral")

    def text(f):
        return f"{f['label']}: {f['value']} (pembanding {f['reference']})"

    positive = [text(f) for f in factors if f["favorable"] is True]
    negative = [text(f) for f in factors if f["favorable"] is False]

    return {
        "opportunity_signal": {
            "score": opp,
            "confidence": confidence,
            "direction": direction,
            "positive_factors": positive,
            "negative_factors": [text(f) for f in factors if f["favorable"] is False and f["side"] == "opportunity"],
            "evidence": [text(f) for f in factors if f["side"] == "opportunity"],
            "components": {f["key"]: f["score"] for f in factors if f["side"] == "opportunity"},
        },
        "risk_signal": {
            "score": risk,
            "level": "High" if risk >= 66 else ("Medium" if risk >= 40 else "Low"),
            "negative_factors": negative,
            "evidence": [text(f) for f in factors if f["side"] == "risk"],
            "components": {f["key"]: f["score"] for f in factors if f["side"] == "risk"},
        },
        "fundamental_divergence": compute_divergence(factors, fund, close, bench),
        "factors": factors,
        "data_coverage": round(coverage, 2),
        "fundamentals_source": fund.get("source"),
    }


def compute_divergence(factors, fund, close: pd.Series, bench: Optional[pd.Series]) -> Dict[str, Any]:
    """
    Fundamental divergence = price and earnings moving in opposite directions:
    earnings growing while the stock lags the market (positive), or earnings
    shrinking while the stock outruns it (negative). Needs real earnings data.
    """
    eg = fund.get("earnings_growth")
    rel = next((f for f in factors if f["key"] == "relative_momentum"), None)
    if eg is None or rel is None:
        return {"detected": False, "confidence": "Low", "type": None, "evaluated": False,
                "reason": "Data pertumbuhan laba tidak tersedia"}
    start = close.index[-MOMENTUM_SESSIONS - 1]
    ret_3m = float(close.iloc[-1]) / float(close.iloc[-MOMENTUM_SESSIONS - 1]) - 1
    rel_ret = ret_3m - (_bench_return(bench, start, close.index[-1]) or 0.0)
    kind = None
    if eg > 0.10 and rel_ret < -0.05:
        kind = "POSITIVE"
    elif eg < -0.10 and rel_ret > 0.05:
        kind = "NEGATIVE"
    strong = abs(eg) > 0.25 and abs(rel_ret) > 0.10
    return {
        "detected": kind is not None,
        "confidence": ("High" if strong else "Medium") if kind else "Low",
        "type": kind,
        "evaluated": True,
        "earnings_growth": round(eg, 4),
        "relative_return": round(rel_ret, 4),
    }
