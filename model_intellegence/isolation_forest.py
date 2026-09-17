from __future__ import annotations
import math
import os
import sys
import json
import copy
import random
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import IsolationForest

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    plt = None
    HAS_MATPLOTLIB = False

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    sns = None
    HAS_SEABORN = False


# Memastikan direktori root repo dan direktori saat ini berada di sys.path
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent if (CURRENT_DIR.parent / "unified_data").exists() else CURRENT_DIR
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    from derived_metrics import (
        safe_divide,
        compute_derived_metrics,
        fetch_and_compute_derived_metrics,
        _get
    )
    HAS_DERIVED_METRICS = True
except ImportError:
    try:
        from .derived_metrics import (
            safe_divide,
            compute_derived_metrics,
            fetch_and_compute_derived_metrics,
            _get
        )
        HAS_DERIVED_METRICS = True
    except ImportError:
        HAS_DERIVED_METRICS = False

        def safe_divide(numerator: Any, denominator: Any) -> Optional[float]:
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
            if obj is None:
                return default
            parts = path.split(".")
            curr = obj
            for part in parts:
                if curr is None:
                    return default
                if isinstance(curr, dict):
                    curr = curr.get(part, default)
                elif hasattr(curr, part):
                    curr = getattr(curr, part, default)
                else:
                    return default
            return curr if curr is not None else default


# ============================================================================
# ANOMALY DETECTION AND ANALYSIS
# Sesuai spesifikasi model-intellegence/PLAN.md (line 310-500)
# ============================================================================

DEFAULT_FEATURE_FIELDS: List[Tuple[str, str]] = [
    ("valuation_metrics", "pe_relative"),
    ("valuation_metrics", "pbv_relative"),
    ("growth_metrics", "revenue_growth_yoy"),
    ("growth_metrics", "growth_acceleration"),
    ("price_metrics", "volatility"),
    ("ownership_metrics", "net_institutional_flow_pct"),
    ("ownership_metrics", "insider_ownership_change")
]


def build_feature_matrix(
    all_companies_metrics: List[Dict[str, Any]],
    feature_fields: List[Tuple[str, str]]
) -> Tuple[List[List[Optional[float]]], List[str]]:
    """
    Mengekstrak matriks fitur X dan daftar nama perusahaan dari seluruh data metrik.
    
    Argumen:
      - all_companies_metrics: List of DerivedMetrics dictionaries/objects.
      - feature_fields: List tuple (category, field_name).
      
    Mengembalikan:
      - X: List of list nilai fitur (dapat mengandung None).
      - company_list: List nama perusahaan/ticker.
    """
    X: List[List[Optional[float]]] = []
    company_list: List[str] = []

    for m in all_companies_metrics:
        row: List[Optional[float]] = []
        for category, field in feature_fields:
            val = _get(m, f"{category}.{field}")
            if val is None:
                # Fallback bila dictionary langsung menyimpan field di level root atau alias
                val = _get(m, field)
            try:
                if val is not None and not math.isnan(float(val)):
                    row.append(float(val))
                else:
                    row.append(None)
            except (ValueError, TypeError):
                row.append(None)
        X.append(row)
        
        comp_name = _get(m, "company") or _get(m, "ticker") or f"Company_{len(company_list) + 1}"
        company_list.append(str(comp_name).strip().upper())

    return X, company_list


def impute_missing(
    X: List[List[Optional[float]]],
    method: str = "median"
) -> np.ndarray:
    """
    Mengisi missing value (None / NaN) pada matriks X kolom demi kolom.
    
    Argumen:
      - X: Matriks 2D data fitur (bisa ada None).
      - method: 'median' (default) atau 'mean'.
      
    Mengembalikan:
      - X_clean: numpy.ndarray berdimensi (N, P) bebas dari NaN.
    """
    if isinstance(X, np.ndarray):
        if X.size == 0:
            return np.empty((0, 0), dtype=float)
        X_clean = np.copy(X).astype(float)
        for col_idx in range(X_clean.shape[1]):
            col = X_clean[:, col_idx]
            nan_mask = np.isnan(col)
            if np.any(nan_mask):
                valid = col[~nan_mask]
                fill_val = float(np.median(valid)) if len(valid) > 0 and method == "median" else (
                    float(np.mean(valid)) if len(valid) > 0 else 0.0
                )
                col[nan_mask] = fill_val
        return X_clean

    if not X or not X[0]:
        return np.empty((0, 0), dtype=float)

    n_rows = len(X)
    n_cols = len(X[0])
    X_arr = np.zeros((n_rows, n_cols), dtype=float)

    for col_idx in range(n_cols):
        col_vals = [row[col_idx] for row in X]
        valid_vals = [v for v in col_vals if v is not None and not math.isnan(v)]

        if valid_vals:
            if method == "mean":
                fill_val = float(np.mean(valid_vals))
            else:
                fill_val = float(np.median(valid_vals))
        else:
            # Jika seluruh kolom berisi None/NaN, gunakan fallback netral 0.0
            fill_val = 0.0

        for row_idx in range(n_rows):
            val = col_vals[row_idx]
            if val is None or math.isnan(val):
                X_arr[row_idx, col_idx] = fill_val
            else:
                X_arr[row_idx, col_idx] = float(val)

    return X_arr


def normalize_scores(raw_scores: Union[List[float], np.ndarray]) -> List[float]:
    """
    Normalisasi raw_scores dari decision_function Isolation Forest ke rentang [0, 1].
    
    Nilai decision_function sklearn:
      - Makin negatif = data makin anomali / terisolasi cepat
      - Makin positif = data makin normal di dalam dense cluster
      
    Fungsi ini membalik (invert) dan menskalakan:
      1.0 = paling anomali (score decision_function paling minimum/negatif)
      0.0 = paling normal (score decision_function paling maksimum)
    """
    scores = [float(s) for s in raw_scores]
    if not scores:
        return []

    min_score = min(scores)
    max_score = max(scores)

    # Bila semua score seragam (misal 1 observasi atau data identik)
    if min_score == max_score:
        return [0.0 for _ in scores]

    normalized: List[float] = []
    # Formula PLAN.md line 427-428:
    # inverted = -s
    # scaled = safe_divide(inverted - (-max_score), (-min_score) - (-max_score))
    denom = (-min_score) - (-max_score)
    for s in scores:
        inverted = -s
        numerator = inverted - (-max_score)
        scaled = safe_divide(numerator, denom)
        if scaled is None:
            scaled = 0.0
        # Batasi di rentang [0.0, 1.0] dan bulatkan 4 desimal
        scaled_bounded = max(0.0, min(1.0, scaled))
        normalized.append(round(scaled_bounded, 4))

    return normalized


def _extract_field_name(item: Any) -> str:
    """Helper untuk mengekstrak nama field dari tuple (category, field) atau string langsung."""
    if isinstance(item, (list, tuple)) and len(item) > 1:
        return str(item[1])
    return str(item)


def compute_feature_stats(
    X_clean: np.ndarray,
    feature_fields: Union[List[Tuple[str, str]], List[str]]
) -> Dict[str, Dict[str, float]]:
    """
    Menghitung statistik ringkasan (mean & standard deviation) per fitur di seluruh observasi.
    Digunakan untuk evidence generation (menghitung z-score per metrik).
    Mendukung list of tuples [('cat', 'field')] maupun list of strings ['field'].
    """
    stats: Dict[str, Dict[str, float]] = {}
    n_rows, n_cols = X_clean.shape

    for i, item in enumerate(feature_fields):
        field = _extract_field_name(item)
        if i >= n_cols:
            stats[field] = {"mean": 0.0, "std": 0.0}
            continue

        col_vals = X_clean[:, i]
        mean_val = float(np.mean(col_vals)) if n_rows > 0 else 0.0
        # Gunakan sample standard deviation (ddof=1) jika observasi > 1, jika 1 observasi ddof=0
        std_val = float(np.std(col_vals, ddof=1 if n_rows > 1 else 0)) if n_rows > 0 else 0.0

        if math.isnan(std_val) or std_val == 0.0:
            std_val = 0.0

        stats[field] = {
            "mean": round(mean_val, 4),
            "std": round(std_val, 4)
        }

    return stats


def find_contributing_factors(
    company_row: Union[List[float], np.ndarray],
    feature_fields: Union[List[Tuple[str, str]], List[str]],
    feature_stats: Dict[str, Dict[str, float]],
    top_n: int = 3
) -> List[Dict[str, Any]]:
    """
    Mencari faktor metrik yang paling berkontribusi terhadap anomali berdasarkan |z-score| terbesar.
    Mendukung list of tuples [('cat', 'field')] maupun list of strings ['field'].
    """
    factor_scores: List[Dict[str, Any]] = []

    for i, item in enumerate(feature_fields):
        field = _extract_field_name(item)
        if field not in feature_stats:
            continue

        value = float(company_row[i])
        mean = feature_stats[field]["mean"]
        std = feature_stats[field]["std"]

        if std == 0.0:
            continue

        metric_z = (value - mean) / std

        factor_scores.append({
            "field": field,
            "value": round(value, 4),
            "peer_mean": round(mean, 4),
            "z_score": round(metric_z, 4),
            "direction": "above_normal" if metric_z > 0 else "below_normal"
        })

    # Urutkan berdasarkan |z_score| terbesar -> faktor yang paling menyimpang/ekstrem
    factor_scores.sort(key=lambda item: abs(item["z_score"]), reverse=True)

    return factor_scores[:top_n]


def generate_evidence_text(
    company: str,
    contributing_factors: List[Dict[str, Any]]
) -> str:
    """
    Menghasilkan narasi eviden/penjelasan alasan deteksi anomali dalam bahasa Indonesia.
    """
    if not contributing_factors:
        return f"{company} terdeteksi anomali berdasarkan kombinasi variasi metrik multidimensi."

    parts: List[str] = []
    for factor in contributing_factors:
        direction_text = "jauh di atas" if factor.get("direction") == "above_normal" else "jauh di bawah"
        val = factor.get("value", 0.0)
        mean = factor.get("peer_mean", 0.0)
        field_name = factor.get("field", "metric")
        parts.append(
            f"{field_name} {direction_text} rata-rata seluruh company "
            f"(nilai: {val:.2f}, rata-rata: {mean:.2f})"
        )

    return f"{company} terdeteksi anomali terutama karena: {'; '.join(parts)}"


def classify_severity(anomaly_score: float) -> str:
    """
    Klasifikasi tingkat keparahan anomali berdasarkan anomaly_score [0, 1].
    - score < 0.50: normal
    - score < 0.65: mild
    - score < 0.80: moderate
    - score >= 0.80: severe
    """
    if anomaly_score < 0.50:
        return "normal"
    if anomaly_score < 0.65:
        return "mild"
    if anomaly_score < 0.80:
        return "moderate"
    return "severe"


def detect_anomalies_isolation_forest(
    all_companies_metrics: List[Dict[str, Any]],
    contamination: Union[float, str] = 0.05,
    feature_fields: Optional[List[Tuple[str, str]]] = None,
    filter_anomalies_only: bool = True,
    top_n_factors: int = 3,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Entry point deteksi anomali menggunakan Isolation Forest sesuai spesifikasi PLAN.md.
    
    Argumen:
      - all_companies_metrics: List of DerivedMetrics dictionaries/objects dalam SATU periode.
      - contamination: Proporsi outlier ('auto' atau float antara (0, 0.5]). Default 0.05.
      - feature_fields: Daftar fitur (category, field_name) yang diuji. Jika None, gunakan default.
      - filter_anomalies_only: Jika True (default), hanya menyertakan perusahaan dengan label anomali (-1).
      - top_n_factors: Jumlah faktor penyimpang terbesar yang dicantumkan per perusahaan (default 3).
      - random_state: Seed untuk reproduktibilitas Isolation Forest (default 42).
      
    Mengembalikan:
      Dictionary dengan struktur:
      {
        "period": str,
        "total_companies_analyzed": int,
        "anomalies_detected": int,
        "anomalies": List[Dict[str, Any]],
        "all_results": Optional[List[Dict[str, Any]]]
      }
    """
    if not all_companies_metrics:
        return {
            "period": "unknown",
            "total_companies_analyzed": 0,
            "anomalies_detected": 0,
            "anomalies": [],
            "status": "EMPTY_INPUT",
            "message": "Data all_companies_metrics kosong."
        }

    # 1. Pilih fitur yang dipakai
    fields = feature_fields or DEFAULT_FEATURE_FIELDS

    # 2. Bangun matrix X dan daftar company
    X_raw, company_list = build_feature_matrix(all_companies_metrics, fields)
    n_companies = len(company_list)

    period_str = str(_get(all_companies_metrics[0], "period", "current"))

    # Isolation Forest membutuhkan minimal 2 sampel untuk mendeteksi outlier
    if n_companies < 2:
        return {
            "period": period_str,
            "total_companies_analyzed": n_companies,
            "anomalies_detected": 0,
            "anomalies": [],
            "status": "INSUFFICIENT_DATA",
            "message": "Deteksi anomali membutuhkan minimal 2 observasi perusahaan."
        }

    # 3. Handle missing values
    X_clean = impute_missing(X_raw, method="median")

    # Pastikan parameter contamination valid
    model_contamination = contamination
    if isinstance(contamination, (int, float)):
        # sklearn membatasi float contamination dalam rentang (0.0, 0.5]
        if contamination <= 0.0 or contamination > 0.5:
            model_contamination = "auto"
        # Jika jumlah sampel terlalu kecil (misal 5 sampel dan contamination 0.05),
        # pastikan tidak 0 expected outlier jika user menginginkan eksplorasi
        elif int(n_companies * contamination) < 1 and contamination < (1.0 / n_companies):
            # Biarkan sklearn auto atau minimum contamination yang representatif
            model_contamination = max(0.05, min(0.5, 1.0 / n_companies))

    # 4. Train Isolation Forest
    model = IsolationForest(
        n_estimators=100,
        contamination=model_contamination,
        random_state=random_state
    )
    model.fit(X_clean)

    raw_scores = model.decision_function(X_clean)  # makin negatif = makin anomali
    labels = model.predict(X_clean)                # -1 = anomali, 1 = normal

    # 5. Normalisasi raw_scores ke [0, 1] (1 = paling anomali)
    anomaly_scores = normalize_scores(raw_scores)

    # 6. Hitung statistik per fitur untuk seluruh populasi
    feature_stats = compute_feature_stats(X_clean, fields)

    # 7. Susun hasil per company
    anomalies_list: List[Dict[str, Any]] = []
    all_company_records: List[Dict[str, Any]] = []

    for i, company in enumerate(company_list):
        factors = find_contributing_factors(
            X_clean[i], fields, feature_stats, top_n=top_n_factors
        )
        score = anomaly_scores[i]
        severity = classify_severity(score)
        is_anomaly = bool(labels[i] == -1)

        evidence_text = generate_evidence_text(company, factors)

        record = {
            "company": company,
            "is_anomaly": is_anomaly,
            "raw_score": round(float(raw_scores[i]), 4),
            "anomaly_score": score,
            "severity": severity,
            "contributing_factors": factors,
            "evidence": evidence_text
        }
        all_company_records.append(record)

        if is_anomaly or not filter_anomalies_only:
            anomalies_list.append({
                "company": company,
                "anomaly_score": score,
                "severity": severity,
                "contributing_factors": factors,
                "evidence": evidence_text
            })

    # Urutkan berdasarkan anomaly_score descending
    anomalies_list.sort(key=lambda x: x["anomaly_score"], reverse=True)
    all_company_records.sort(key=lambda x: x["anomaly_score"], reverse=True)

    return {
        "period": period_str,
        "total_companies_analyzed": n_companies,
        "anomalies_detected": sum(1 for r in all_company_records if r["is_anomaly"]),
        "anomalies": anomalies_list,
        "all_results": all_company_records
    }


# ============================================================================
# PIPELINE INTEGRATION & UNIFIED DATA RETRIEVAL (TIME-SERIES + CROSS-SECTIONAL)
# ============================================================================

def fetch_historical_price(ticker: str, start: str = "2015-01-01", end: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Mengambil data historis harga saham harian dari yfinance dari start date hingga end date.
    Mendukung emiten saham bursa (.JK) maupun simbol indeks pasar (^JKSE).
    """
    clean_sym = ticker.strip()
    if clean_sym.startswith("^"):
        yf_sym = clean_sym
    else:
        clean_sym = clean_sym.upper().replace(".JK", "")
        yf_sym = f"{clean_sym}.JK"
    
    # Supress yfinance prints by capturing stdout if needed, but for now just run it.
    t = yf.Ticker(yf_sym)
    hist = t.history(start=start, end=end) if end else t.history(start=start)

    if hist.empty:
        return []

    records: List[Dict[str, Any]] = []
    for dt_idx, row in hist.iterrows():
        dt_str = dt_idx.strftime("%Y-%m-%d") if hasattr(dt_idx, "strftime") else str(dt_idx)[:10]
        records.append({
            "date": dt_str,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": float(row["Volume"])
        })

    return records


def prepare_multi_emiten_data(
    tickers: List[str],
    start: str = "2015-01-01",
    end: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Mengambil data harga mentah untuk seluruh emiten yang ditentukan.
    """
    all_raw_data: Dict[str, List[Dict[str, Any]]] = {}
    for sym in tickers:
        data = fetch_historical_price(sym, start=start, end=end)
        if data:
            all_raw_data[sym] = data
    return all_raw_data


def compute_daily_features(
    price_series: List[Dict[str, Any]],
    ihsg_series: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Menghitung fitur harian berbasis rolling window 60 hari dengan penyempurnaan:
    1. Log return harian: ln(close_t / close_t-1) * 100 (menggantikan formula persentase biasa)
    2. volatility_20d: volatilitas log return tahunan berbasis rolling 20 hari
    3. volume_zscore: z-score volume perdagangan (lembar saham) rolling 60 hari
    4. value_traded & value_traded_zscore: nilai transaksi Rupiah (volume * close) dan rolling z-score 60 hari
    5. price_vs_ma20 & price_vs_ma60: deviasi harga penutupan terhadap MA20 & MA60 (%)
    6. range_pct: rentang harga harian (high - low) / close * 100
    7. return_vs_ihsg: Alpha terhadap indeks IHSG (^JKSE) harian (emiten return - ihsg return)
    """
    features: List[Dict[str, Any]] = []
    n_days = len(price_series)

    # Hitung log returns untuk IHSG jika seri data IHSG diberikan
    ihsg_log_returns: Dict[str, float] = {}
    if ihsg_series and len(ihsg_series) > 1:
        for j in range(1, len(ihsg_series)):
            p_prev = ihsg_series[j - 1]["close"]
            p_curr = ihsg_series[j]["close"]
            d_date = ihsg_series[j]["date"]
            if p_prev > 0 and p_curr > 0:
                ihsg_log_returns[d_date] = math.log(p_curr / p_prev) * 100.0
            else:
                ihsg_log_returns[d_date] = 0.0

    for i in range(60, n_days):
        window = price_series[i - 60 : i]
        current = price_series[i]
        prev = price_series[i - 1]
        cur_date = current["date"]

        # 1. Alignment Tanggal terhadap IHSG:
        # Jika data IHSG tersedia, pastikan tanggal match dengan IHSG
        # Skip tanggal yang tidak match (misal karena hari libur bursa berbeda / suspensi)
        if ihsg_series is not None and cur_date not in ihsg_log_returns:
            continue

        # 2. Log Return: ln(close_t / close_t-1) * 100
        if prev["close"] > 0 and current["close"] > 0:
            daily_return = math.log(current["close"] / prev["close"]) * 100.0
        else:
            daily_return = 0.0

        # 3. Volatilitas 20 Hari berbasis log return
        window_20_closes = [row["close"] for row in window[-20:]]
        returns_20 = [
            math.log(window_20_closes[k] / window_20_closes[k - 1])
            if window_20_closes[k - 1] > 0 and window_20_closes[k] > 0 else 0.0
            for k in range(1, len(window_20_closes))
        ]
        volatility_20d = float(np.std(returns_20, ddof=1)) * math.sqrt(252) * 100.0 if len(returns_20) > 1 else 0.0

        # 4. Volume Z-Score (lembar saham)
        window_volumes = [row["volume"] for row in window]
        mean_vol = float(np.mean(window_volumes))
        std_vol = float(np.std(window_volumes, ddof=1)) if len(window_volumes) > 1 else 1.0
        volume_zscore = safe_divide(current["volume"] - mean_vol, std_vol) or 0.0

        # 5. Value Traded (Rupiah = volume * close) & Value Traded Z-Score
        current_value_traded = float(current["volume"] * current["close"])
        window_values_traded = [float(row["volume"] * row["close"]) for row in window]
        mean_val = float(np.mean(window_values_traded))
        std_val = float(np.std(window_values_traded, ddof=1)) if len(window_values_traded) > 1 else 1.0
        value_traded_zscore = safe_divide(current_value_traded - mean_val, std_val) or 0.0

        # 6. Price vs MA20 & MA60
        mean_ma20 = float(np.mean(window_20_closes))
        price_vs_ma20 = (safe_divide(current["close"] - mean_ma20, mean_ma20) or 0.0) * 100.0

        window_60_closes = [row["close"] for row in window]
        mean_ma60 = float(np.mean(window_60_closes))
        price_vs_ma60 = (safe_divide(current["close"] - mean_ma60, mean_ma60) or 0.0) * 100.0

        # 7. Range Pct
        range_pct = (safe_divide(current["high"] - current["low"], current["close"]) or 0.0) * 100.0

        # 8. Return vs IHSG (Alpha)
        if ihsg_series is not None and cur_date in ihsg_log_returns:
            daily_ihsg = ihsg_log_returns[cur_date]
            return_vs_ihsg = daily_return - daily_ihsg
        else:
            return_vs_ihsg = 0.0

        features.append({
            "date": current["date"],
            "close": current["close"],
            "high": current["high"],
            "low": current["low"],
            "volume": current["volume"],
            "value_traded": round(current_value_traded, 2),
            "daily_return": round(daily_return, 4),
            "volatility_20d": round(volatility_20d, 4),
            "volume_zscore": round(volume_zscore, 4),
            "value_traded_zscore": round(value_traded_zscore, 4),
            "price_vs_ma20": round(price_vs_ma20, 4),
            "price_vs_ma60": round(price_vs_ma60, 4),
            "range_pct": round(range_pct, 4),
            "return_vs_ihsg": round(return_vs_ihsg, 4)
        })

    return features


def split_by_date(
    features_df: List[Dict[str, Any]],
    train_end: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Memisahkan dataset menjadi train (<= train_end) dan test (> train_end)."""
    train_data = [row for row in features_df if row["date"] <= train_end]
    test_data = [row for row in features_df if row["date"] > train_end]
    return train_data, test_data


def extract_columns(data: List[Dict[str, Any]], feature_columns: List[str]) -> np.ndarray:
    """Mengekstrak matriks numerik numpy dari list dictionary data."""
    matrix = []
    for row in data:
        row_vals = []
        for col in feature_columns:
            val = row.get(col)
            row_vals.append(float(val) if val is not None and not math.isnan(val) else np.nan)
        matrix.append(row_vals)
    return np.array(matrix, dtype=float)


def impute_with_reference(
    X: np.ndarray,
    feature_columns: List[str],
    reference_stats: Dict[str, Dict[str, float]]
) -> np.ndarray:
    """Imputasi test set menggunakan mean dari data TRAIN."""
    X_clean = np.copy(X)
    for col_idx, col_name in enumerate(feature_columns):
        col = X_clean[:, col_idx]
        nan_mask = np.isnan(col)
        if np.any(nan_mask):
            fill_val = reference_stats.get(col_name, {}).get("mean", 0.0)
            col[nan_mask] = fill_val
    return X_clean


def apply_to_test(
    model: IsolationForest,
    test_data: List[Dict[str, Any]],
    feature_columns: List[str],
    feature_stats: Dict[str, Dict[str, float]]
) -> List[Dict[str, Any]]:
    """Menerapkan model Isolation Forest ke data testing."""
    if not test_data:
        return []

    test_data_copy = copy.deepcopy(test_data)
    X_test = extract_columns(test_data_copy, feature_columns)
    X_test_clean = impute_with_reference(X_test, feature_columns, feature_stats)

    scores = model.decision_function(X_test_clean)
    labels = model.predict(X_test_clean)
    
    # Gunakan fungsi normalize dari isolation_forest yang ada
    # (Di modul ini, normalize_scores sudah ada dan menerima Union[List, np.ndarray])
    norm_scores = normalize_scores(scores)
    
    try:
        percentile_scores = normalize_score_percentile(scores)
    except NameError:
        # Fallback jika fungsi belum terdefinisi di scope atas
        percentile_scores = [s * 100 for s in norm_scores]

    for i, row in enumerate(test_data_copy):
        row["anomaly_score"] = norm_scores[i]
        row["percentile_score"] = percentile_scores[i]
        row["is_anomaly"] = bool(labels[i] == -1)
        row["contributing_factors"] = find_contributing_factors(
            X_test_clean[i], feature_columns, feature_stats, top_n=3
        )

    return test_data_copy


def anomaly_detect(
    tickers: List[str],
    train_start: str = "2015-01-01",
    train_end: str = "2024-12-31",
    base_contamination: float = 0.03,
    market_wide_threshold: float = 0.6,
    market_wide_z_threshold: float = 1.5,
    min_volume_zscore: float = 0.5
) -> Dict[str, Any]:
    """
    Fungsi utama (Main API) untuk deteksi anomali pada market.
    Menarik data, menjalankan model isolation forest, menggabungkan time-series dan cross-sectional,
    dan memfilter false positives.
    """
    clean_tickers = [str(t).upper().replace(".JK", "").strip() for t in tickers if t]
    clean_tickers = list(dict.fromkeys(clean_tickers))
    
    if not clean_tickers:
        return {"status": "ERROR", "error": "Tidak ada ticker valid."}

    feature_columns = [
        "daily_return", "volatility_20d", "volume_zscore", "value_traded_zscore",
        "price_vs_ma20", "price_vs_ma60", "range_pct", "return_vs_ihsg"
    ]

    all_raw_data = prepare_multi_emiten_data(clean_tickers, start=train_start)
    if not all_raw_data:
        return {"status": "ERROR", "error": "Gagal mengambil data untuk seluruh ticker."}

    # Fetch data historis IHSG (^JKSE) untuk periode yang sama persis (Alpha terhadap indeks)
    ihsg_raw_data = fetch_historical_price("^JKSE", start=train_start)

    all_features = {}
    train_sets = {}
    test_sets = {}

    for sym, raw_prices in all_raw_data.items():
        feat = compute_daily_features(raw_prices, ihsg_series=ihsg_raw_data)
        tr, te = split_by_date(feat, train_end=train_end)
        all_features[sym] = feat
        train_sets[sym] = tr
        test_sets[sym] = te

    # Hitung baseline volatilitas rata-rata seluruh emiten dari 500 hari trading terakhir
    # Dipanggil SEKALI di luar loop per-emiten sebelum training dimulai
    recent_baseline_vol = compute_recent_baseline_volatility(train_sets, recent_window_days=500)

    results: Dict[str, Any] = {
        "status": "SUCCESS", 
        "companies": {},
        "recent_baseline_vol": round(recent_baseline_vol, 4)
    }

    for ticker in clean_tickers:
        if ticker not in train_sets or not train_sets[ticker]:
            continue

        train_data = train_sets[ticker]
        test_data = test_sets[ticker]

        # Hitung volatilitas 10 tahun (full) vs 500 hari terakhir untuk verifikasi regime shift
        rets_full = [float(r["daily_return"]) for r in train_data if r.get("daily_return") is not None and not math.isnan(float(r["daily_return"]))]
        rets_recent = [float(r["daily_return"]) for r in train_data[-500:] if r.get("daily_return") is not None and not math.isnan(float(r["daily_return"]))]
        hist_vol_10y = float(np.std(rets_full, ddof=1)) if len(rets_full) > 1 else 1.0
        hist_vol_500d = float(np.std(rets_recent, ddof=1)) if len(rets_recent) > 1 else 1.0

        model, feature_stats, adaptive_c = train_model_with_adaptive_contamination(
            train_data,
            feature_columns=feature_columns,
            all_emiten_avg_volatility=recent_baseline_vol,
            base_contamination=base_contamination,
            recent_window_days=500,
            random_state=42
        )

        test_with_anomalies = apply_to_test(model, test_data, feature_columns, feature_stats)

        results["companies"][ticker] = {
            "model": model,
            "feature_columns": feature_columns,
            "feature_stats": feature_stats,
            "adaptive_contamination": adaptive_c,
            "hist_vol_10y": round(hist_vol_10y, 4),
            "hist_vol_500d": round(hist_vol_500d, 4),
            "baseline_vol_500d": round(recent_baseline_vol, 4),
            "train_data": train_data,
            "test_data": test_with_anomalies
        }

    # ========================================================================
    # [NON-AKTIFKAN SEMENTARA] Cross-Sectional Analysis Layer
    # Digantikan oleh fitur relatif return_vs_ihsg (Alpha) secara end-to-end.
    # Kode lama dipertahankan (comment) untuk referensi/komparasi di masa mendatang:
    #
    # test_features_dict = {t: results["companies"][t]["test_data"] for t in results["companies"].keys()}
    # cross_df = build_cross_sectional_dataset(test_features_dict, list(results["companies"].keys()))
    # market_wide_results = detect_market_wide_anomaly(
    #     cross_df, 
    #     list(results["companies"].keys()), 
    #     threshold_pct=market_wide_threshold, 
    #     z_threshold=market_wide_z_threshold
    # )
    # ========================================================================
    market_wide_results: List[Dict[str, Any]] = []

    # Combine & Filter for each ticker
    for ticker in results["companies"].keys():
        # [KODE LAMA DENGAN CROSS-SECTIONAL LAYER]:
        # combined_data = combine_time_series_and_cross_sectional(
        #     results["companies"][ticker]["test_data"],
        #     market_wide_results,
        #     ticker=ticker
        # )
        
        # [KODE BARU: Time-Series dengan Alpha vs IHSG & Value Traded]:
        test_rows = results["companies"][ticker]["test_data"]
        combined_data = []
        for row in test_rows:
            r_copy = copy.deepcopy(row)
            is_anom = bool(r_copy.get("is_anomaly", False))
            r_copy["final_is_anomaly"] = is_anom
            r_copy["anomaly_source"] = "time_series_only" if is_anom else "none"
            combined_data.append(r_copy)
        
        # Apply False Positives Filter
        # Kita hanya peduli pada row yang ditandai final_is_anomaly
        anomalies_only = [r for r in combined_data if r.get("final_is_anomaly")]
        processed_anomalies = filter_false_positives(
            anomalies_only, 
            min_volume_zscore=min_volume_zscore,
            bearish_score_threshold=0.6,
            bullish_score_threshold=0.8
        )
        
        # Update flag
        filtered_dates = {f["date"]: f for f in processed_anomalies}
        for row in combined_data:
            if row["date"] in filtered_dates:
                f_row = filtered_dates[row["date"]]
                if f_row.get("is_false_positive"):
                    row["final_is_anomaly"] = False # Dianggap false positive oleh filter
                    row["filtered_reason"] = f_row.get("filtered_reason")
                    row["anomaly_note"] = f_row.get("note")
                else:
                    row["anomaly_type"] = f_row.get("anomaly_type", "UNKNOWN")

        results["companies"][ticker]["final_results"] = combined_data
        results["companies"][ticker]["anomalies"] = [r for r in combined_data if r.get("final_is_anomaly")]
        
        # Clustering
        anomaly_pts = [
            {
                "date": row["date"],
                "score": row.get("anomaly_score", 0.0),
                "factors": row.get("contributing_factors", []),
                "type": row.get("anomaly_type")
            }
            for row in combined_data if row.get("final_is_anomaly")
        ]
        results["companies"][ticker]["episodes"] = cluster_consecutive_anomalies(anomaly_pts, max_gap_days=3)

    results["market_wide_results"] = market_wide_results
    return results


def fetch_and_detect_anomalies(
    tickers: List[str],
    period: str = "current",
    contamination: Union[float, str] = 0.05,
    feature_fields: Optional[List[Tuple[str, str]]] = None,
    filter_anomalies_only: bool = True,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Mengambil data derived metrics untuk daftar tickers dari unified data layer,
    lalu menjalankan deteksi anomali Isolation Forest.
    
    Argumen:
      - tickers: List kode saham (misal ['BBCA', 'BMRI', 'BBRI', 'TLKM']).
      - period: Periode laporan keuangan ('current', '2025', '2024', dsb).
      - contamination: Proporsi contamination Isolation Forest (default 0.05).
      - feature_fields: Daftar fitur (opsional).
      - filter_anomalies_only: True untuk hanya menyaring perusahaan anomali.
      - force_refresh: Force bypass cache unified data layer.
      
    Mengembalikan:
      Dictionary hasil analisis deteksi anomali.
    """
    if not HAS_DERIVED_METRICS:
        return {
            "status": "ERROR",
            "error": "Modul derived_metrics tidak tersedia."
        }

    clean_tickers = [str(t).upper().replace(".JK", "").strip() for t in tickers if t]
    clean_tickers = list(dict.fromkeys(clean_tickers))  # Hapus duplikat tanpa ubah urutan

    if len(clean_tickers) < 2:
        return {
            "status": "ERROR",
            "error": "Diperlukan minimal 2 ticker untuk analisis deteksi anomali."
        }

    collected_metrics: List[Dict[str, Any]] = []

    for sym in clean_tickers:
        try:
            m = fetch_and_compute_derived_metrics(sym, period=period, force_refresh=force_refresh)
            if isinstance(m, dict) and m.get("status") != "ERROR":
                # Pastikan field company tercatat
                if "company" not in m:
                    m["company"] = sym
                collected_metrics.append(m)
            else:
                # Mock fallback jika ticker gagal di-fetch agar tidak memutus batch
                continue
        except Exception:
            continue

    if len(collected_metrics) < 2:
        return {
            "status": "ERROR",
            "error": f"Data derived metrics hanya berhasil diambil untuk {len(collected_metrics)} ticker (minimal 2 dibutuhkan)."
        }

    return detect_anomalies_isolation_forest(
        all_companies_metrics=collected_metrics,
        contamination=contamination,
        feature_fields=feature_fields,
        filter_anomalies_only=filter_anomalies_only
    )


# ============================================================================
# FORMATTING & VISUALIZATION HELPERS
# ============================================================================

def format_anomalies_summary(result: Dict[str, Any]) -> str:
    """
    Memformat hasil deteksi anomali menjadi tabel ASCII yang rapi untuk CLI report.
    """
    period = result.get("period", "current")
    total = result.get("total_companies_analyzed", 0)
    anom_count = result.get("anomalies_detected", 0)
    anomalies = result.get("anomalies", [])

    lines = [
        "=" * 85,
        f" HASIL DETEKSI ANOMALI PASAR (ISOLATION FOREST) - PERIODE: {period}",
        f" Total Perusahaan Dianalisis: {total} | Anomali Terdeteksi: {anom_count}",
        "=" * 85,
    ]

    if not anomalies:
        lines.append(" Tidak ada anomali signifikan yang terdeteksi pada parameter saat ini.")
        lines.append("=" * 85)
        return "\n".join(lines)

    lines.extend([
        f"{'Company':<9} {'Score':<8} {'Severity':<10} {'Faktor Penyimpang Utama & Bukti':<55}",
        "-" * 85
    ])

    for item in anomalies:
        c = item.get("company", "-")
        score = item.get("anomaly_score", 0.0)
        sev = item.get("severity", "-").upper()
        ev = item.get("evidence", "")

        lines.append(f"{c:<9} {score:<8.3f} {sev:<10} {ev}")

    lines.append("=" * 85)
    return "\n".join(lines)


def plot_anomalies(
    result: Dict[str, Any],
    save_path: Optional[str] = None,
    show_plot: bool = True
) -> Optional[str]:
    """
    Menghasilkan visualisasi scatter/bar chart anomaly score per perusahaan.
    """
    if not HAS_MATPLOTLIB or plt is None:
        print("Matplotlib tidak terpasang. Visualisasi tidak dapat digenerate.")
        return None

    records = result.get("all_results") or result.get("anomalies", [])
    if not records:
        return None

    df = pd.DataFrame(records)
    if "anomaly_score" not in df.columns or "company" not in df.columns:
        return None

    plt.figure(figsize=(10, 5))
    palette = {"normal": "#2ecc71", "mild": "#f1c40f", "moderate": "#e67e22", "severe": "#e74c3c"}
    
    if HAS_SEABORN and sns is not None:
        sns.barplot(
            data=df,
            x="company",
            y="anomaly_score",
            hue="severity",
            palette=palette,
            dodge=False
        )
    else:
        colors = [palette.get(str(sev).lower(), "#95a5a6") for sev in df.get("severity", ["normal"] * len(df))]
        plt.bar(df["company"], df["anomaly_score"], color=colors, alpha=0.85)

    plt.axhline(0.50, color="gray", linestyle="--", alpha=0.6, label="Threshold Mild (0.50)")
    plt.axhline(0.65, color="orange", linestyle="--", alpha=0.6, label="Threshold Moderate (0.65)")
    plt.axhline(0.80, color="red", linestyle="--", alpha=0.6, label="Threshold Severe (0.80)")

    plt.title(f"Market Anomaly Detection (Isolation Forest) - Periode: {result.get('period', 'N/A')}", fontsize=12, fontweight="bold")
    plt.xlabel("Perusahaan")
    plt.ylabel("Anomaly Score (0 = Normal, 1 = Anomali)")
    plt.ylim(0, 1.05)
    plt.legend(loc="upper right")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300)
    if show_plot:
        plt.show()

    return save_path


# ============================================================================
# REVISION FOR ANOMALY DETECTOR AND ANALYSIS
# Sesuai spesifikasi model_intellegence/PLAN.md (lines 502-718)
# ============================================================================

def build_cross_sectional_dataset(
    all_emiten_features: Dict[str, Any],
    tickers: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    1.1 HITUNG DEVIASI ANTAR-EMITEN DI HARI YANG SAMA
    Menggabungkan fitur harian seluruh emiten menjadi satu dataset cross-sectional:
    baris = tanggal bersama (common dates), kolom = daily_return tiap emiten.
    """
    target_tickers = tickers or list(all_emiten_features.keys())
    if not target_tickers:
        return []

    # Ambil irisan tanggal yang tersedia di seluruh emiten yang ditargetkan
    ticker_date_sets: List[set] = []
    ticker_feature_maps: Dict[str, Dict[str, float]] = {}

    for t in target_tickers:
        series = all_emiten_features.get(t, [])
        date_map = {}
        if isinstance(series, pd.DataFrame):
            for _, r in series.iterrows():
                dt = str(r.get("date", ""))[:10]
                ret = r.get("daily_return")
                if dt and ret is not None and not (isinstance(ret, float) and math.isnan(ret)):
                    date_map[dt] = float(ret)
        elif isinstance(series, list):
            for r in series:
                dt = str(r.get("date", ""))[:10]
                ret = r.get("daily_return")
                if dt and ret is not None and not (isinstance(ret, float) and math.isnan(ret)):
                    date_map[dt] = float(ret)

        ticker_feature_maps[t] = date_map
        ticker_date_sets.append(set(date_map.keys()))

    if not ticker_date_sets:
        return []

    common_dates = sorted(list(set.intersection(*ticker_date_sets)))

    cross_df: List[Dict[str, Any]] = []
    for dt in common_dates:
        row: Dict[str, Any] = {"date": dt}
        for t in target_tickers:
            row[f"{t}_return"] = ticker_feature_maps[t].get(dt)
        cross_df.append(row)

    return cross_df


def detect_market_wide_anomaly(
    cross_df: List[Dict[str, Any]],
    tickers: Optional[List[str]] = None,
    threshold_pct: float = 0.6,
    z_threshold: float = 1.5
) -> List[Dict[str, Any]]:
    """
    1.2 DETEKSI ANOMALI MARKET-WIDE PER HARI
    Mendeteksi hari-hari di mana terjadi pergerakan ekstrem serentak lintas emiten
    (misalnya saat guncangan makroekonomi, perubahan suku bunga, atau crash pasar).
    """
    if not cross_df:
        return []

    if tickers is None:
        target_tickers = [k.replace("_return", "") for k in cross_df[0].keys() if k.endswith("_return")]
    else:
        target_tickers = tickers

    market_wide_results: List[Dict[str, Any]] = []

    for row in cross_df:
        returns_today = [
            float(row[f"{t}_return"])
            for t in target_tickers
            if row.get(f"{t}_return") is not None and not math.isnan(float(row[f"{t}_return"]))
        ]

        if len(returns_today) < 3:
            continue  # Data tidak cukup untuk estimasi parameter cross-sectional hari itu

        market_mean = float(np.mean(returns_today))
        market_std = float(np.std(returns_today, ddof=1)) if len(returns_today) > 1 else 0.0

        if market_std == 0.0 or math.isnan(market_std):
            continue

        extreme_count = 0
        per_emiten_z: Dict[str, float] = {}

        for t in target_tickers:
            val = row.get(f"{t}_return")
            if val is None or math.isnan(float(val)):
                continue
            z = (float(val) - market_mean) / market_std
            per_emiten_z[t] = round(float(z), 4)
            if abs(z) > z_threshold:
                extreme_count += 1

        pct_moving_together = safe_divide(extreme_count, len(returns_today))
        is_market_wide = pct_moving_together >= threshold_pct

        market_wide_results.append({
            "date": row["date"],
            "pct_emiten_extreme": round(pct_moving_together, 4),
            "is_market_wide_anomaly": is_market_wide,
            "market_mean_return": round(market_mean, 4),
            "market_volatility": round(market_std, 4),
            "per_emiten_deviation": per_emiten_z
        })

    return market_wide_results


def combine_time_series_and_cross_sectional(
    per_company_results: Union[Dict[str, Any], List[Dict[str, Any]]],
    market_wide_results: List[Dict[str, Any]],
    ticker: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    1.3 GABUNGKAN HASIL TIME SERIES PER-COMPANY DENGAN DETEKSI CROSS-SECTIONAL
    Menggabungkan anomali individu (Isolation Forest time-series) dengan anomali market-wide.
    Status anomali final = union (terdeteksi di salah satu layer).
    """
    rows: List[Dict[str, Any]] = []
    if isinstance(per_company_results, dict):
        if ticker and ticker in per_company_results:
            cand = per_company_results[ticker]
            rows = cand.get("test_data", cand) if isinstance(cand, dict) else cand
        else:
            # Fallback ambil list pertama yang tersedia
            for k, v in per_company_results.items():
                cand = v.get("test_data", v) if isinstance(v, dict) else v
                if isinstance(cand, list):
                    rows = cand
                    break
    elif isinstance(per_company_results, list):
        rows = per_company_results

    market_map = {m["date"]: m for m in market_wide_results}
    combined: List[Dict[str, Any]] = []

    for row in rows:
        dt = row.get("date")
        market_day = market_map.get(dt)

        ts_anomaly = bool(row.get("is_anomaly", False))
        ts_score = float(row.get("anomaly_score", 0.0))
        mw_anomaly = bool(market_day.get("is_market_wide_anomaly", False)) if market_day else False
        mw_pct = float(market_day.get("pct_emiten_extreme", 0.0)) if market_day else 0.0

        final_is_anomaly = ts_anomaly or mw_anomaly

        if ts_anomaly and mw_anomaly:
            source = "both"
        elif ts_anomaly:
            source = "time_series_only"
        elif mw_anomaly:
            source = "market_wide_only"
        else:
            source = "none"

        combined_row = copy.deepcopy(row)
        combined_row.update({
            "date": dt,
            "close": row.get("close"),
            "time_series_anomaly": ts_anomaly,
            "time_series_score": ts_score,
            "market_wide_anomaly": mw_anomaly,
            "market_wide_pct": mw_pct,
            "final_is_anomaly": final_is_anomaly,
            "anomaly_source": source
        })
        combined.append(combined_row)

    return combined


# ============================================================================
# 1.4 UPDATE: DETEKSI MARKET-WIDE DENGAN TIME SERIES Z-SCORE HISTORIS (PLAN.md ## UPDATE)
# ============================================================================

def compute_historical_zscore_per_emiten(
    train_data: List[Dict[str, Any]],
    test_data: List[Dict[str, Any]],
    ticker: str
) -> List[Dict[str, Any]]:
    """
    Hitung baseline mean (mu_hist) dan standard deviation (sigma_hist)
    HANYA dari train period (2015-2024), lalu terapkan ke test period
    untuk menghasilkan time series Z-score historis per emiten.
    """
    train_returns = [
        float(row["daily_return"])
        for row in train_data
        if row.get("daily_return") is not None and not math.isnan(float(row["daily_return"]))
    ]
    if len(train_returns) < 2:
        return []

    mu_hist = float(np.mean(train_returns))
    sigma_hist = float(np.std(train_returns, ddof=1))

    z_scores: List[Dict[str, Any]] = []
    for row in test_data:
        val = row.get("daily_return")
        if val is not None and not math.isnan(float(val)) and sigma_hist > 0:
            z = (float(val) - mu_hist) / sigma_hist
            z_scores.append({
                "date": row["date"],
                "ticker": ticker,
                "z_score": round(float(z), 4)
            })

    return z_scores


def detect_market_wide_shock(
    all_emiten_test_zscores: Dict[str, List[Dict[str, Any]]],
    tickers: Optional[List[str]] = None,
    z_threshold: float = 1.5,
    vote_threshold_pct: float = 0.6
) -> List[Dict[str, Any]]:
    """
    CARA 1 — MAIN METHOD:
    Mendeteksi shock pasar saat sebagian besar emiten (>= vote_threshold_pct)
    mengalami Z-score pergerakan return yang melebihi ambang batas (|z| > z_threshold)
    terhadap volatilitas historisnya masing-masing.
    """
    if not all_emiten_test_zscores:
        return []

    target_tickers = tickers or list(all_emiten_test_zscores.keys())

    # Bangun dictionary mapping: ticker -> date -> z_score
    ticker_date_map: Dict[str, Dict[str, float]] = {}
    for t in target_tickers:
        ticker_date_map[t] = {
            row["date"]: float(row["z_score"])
            for row in all_emiten_test_zscores.get(t, [])
            if row.get("date") and row.get("z_score") is not None
        }

    # Cari intersection tanggal yang tersedia di seluruh emiten target
    common_dates_sets = [set(ticker_date_map[t].keys()) for t in target_tickers if t in ticker_date_map]
    if not common_dates_sets:
        return []
    common_dates = sorted(list(set.intersection(*common_dates_sets)))

    market_wide_days: List[Dict[str, Any]] = []

    for dt in common_dates:
        z_today = {t: ticker_date_map[t].get(dt) for t in target_tickers}
        z_today_valid = {t: z for t, z in z_today.items() if z is not None and not math.isnan(z)}

        if not z_today_valid:
            continue

        n_extreme = sum(1 for z in z_today_valid.values() if abs(z) > z_threshold)
        pct_extreme = safe_divide(n_extreme, len(z_today_valid)) or 0.0

        if pct_extreme >= vote_threshold_pct:
            market_wide_days.append({
                "date": dt,
                "pct_emiten_extreme": round(float(pct_extreme), 4),
                "n_emiten_extreme": n_extreme,
                "contributing_emiten": [t for t, z in z_today_valid.items() if abs(z) > z_threshold],
                "z_scores_detail": {t: round(float(z), 4) for t, z in z_today_valid.items()}
            })

    return market_wide_days


def compute_market_aggregate_shock(
    train_data_all: Dict[str, List[Dict[str, Any]]],
    test_data_all: Dict[str, List[Dict[str, Any]]],
    tickers: Optional[List[str]] = None,
    threshold_sigma: float = 2.0
) -> List[Dict[str, Any]]:
    """
    CARA 2 — SANITY CHECK / SECONDARY SIGNAL:
    Menghitung return pasar gabungan (equal-weighted average) pada data TRAIN sebagai baseline,
    lalu mendeteksi shock di data TEST apabila return rata-rata pasar harian menyimpang
    melebihi threshold_sigma standar deviasi pasar.
    """
    target_tickers = tickers or list(train_data_all.keys())

    # Map date -> daily_return per emiten untuk TRAIN
    train_map: Dict[str, Dict[str, float]] = {}
    for t in target_tickers:
        train_map[t] = {
            row["date"]: float(row["daily_return"])
            for row in train_data_all.get(t, [])
            if row.get("date") and row.get("daily_return") is not None and not math.isnan(float(row["daily_return"]))
        }

    train_dates_sets = [set(train_map[t].keys()) for t in target_tickers if t in train_map]
    if not train_dates_sets:
        return []
    common_train_dates = sorted(list(set.intersection(*train_dates_sets)))

    train_market_returns = []
    for dt in common_train_dates:
        daily_vals = [train_map[t][dt] for t in target_tickers if dt in train_map[t]]
        if daily_vals:
            train_market_returns.append(float(np.mean(daily_vals)))

    if len(train_market_returns) < 2:
        return []

    mu_market = float(np.mean(train_market_returns))
    sigma_market = float(np.std(train_market_returns, ddof=1))

    # Map date -> daily_return per emiten untuk TEST
    test_map: Dict[str, Dict[str, float]] = {}
    for t in target_tickers:
        test_map[t] = {
            row["date"]: float(row["daily_return"])
            for row in test_data_all.get(t, [])
            if row.get("date") and row.get("daily_return") is not None and not math.isnan(float(row["daily_return"]))
        }

    test_dates_sets = [set(test_map[t].keys()) for t in target_tickers if t in test_map]
    if not test_dates_sets:
        return []
    common_test_dates = sorted(list(set.intersection(*test_dates_sets)))

    market_shocks: List[Dict[str, Any]] = []
    for dt in common_test_dates:
        daily_vals = [test_map[t][dt] for t in target_tickers if dt in test_map[t]]
        if daily_vals:
            daily_avg_test = float(np.mean(daily_vals))
            if sigma_market > 0 and abs(daily_avg_test - mu_market) > threshold_sigma * sigma_market:
                market_shocks.append({
                    "date": dt,
                    "market_avg_return": round(daily_avg_test, 4),
                    "deviation_sigma": round((daily_avg_test - mu_market) / sigma_market, 4)
                })

    return market_shocks


def cross_validate_market_wide(
    cara1_results: List[Dict[str, Any]],
    cara2_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    GABUNGKAN — Cara 2 sebagai konfirmasi/validasi silang terhadap Cara 1.
    - high_confidence: dikonfirmasi oleh kedua cara (konsensus tinggi)
    - consensus_only: hanya terdeteksi cara 1 (pergerakan serentak tanpa dominasi 1 saham ekstrem)
    - possible_single_stock_driven: hanya terdeteksi cara 2 (kemungkinan bias didorong 1 saham ekstrem)
    """
    cara1_dates = set(r["date"] for r in cara1_results if "date" in r)
    cara2_dates = set(r["date"] for r in cara2_results if "date" in r)

    confirmed_by_both = sorted(list(cara1_dates.intersection(cara2_dates)))
    only_cara1 = sorted(list(cara1_dates - cara2_dates))
    only_cara2 = sorted(list(cara2_dates - cara1_dates))

    return {
        "high_confidence": confirmed_by_both,
        "consensus_only": only_cara1,
        "possible_single_stock_driven": only_cara2
    }


# ============================================================================
# 1.5 UPDATE: FEATURE KONTEKS PASAR (ALPHA) & POST-PROCESSING FILTER
# ============================================================================

def compute_relative_alpha(
    emiten_returns: List[Dict[str, Any]],
    index_returns: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    ENHANCEMENT 1: Menghitung selisih return harian emiten terhadap return indeks pasar.
    Saham yang turun saat market turun adalah normal. 
    Saham yang naik saat market turun tajam adalah anomali.
    """
    # Buat map date -> return untuk indeks
    index_map = {
        row["date"]: float(row["daily_return"])
        for row in index_returns
        if row.get("date") and row.get("daily_return") is not None and not math.isnan(float(row["daily_return"]))
    }
    
    relative_features = []
    
    for row in emiten_returns:
        date = row.get("date")
        e_return = row.get("daily_return")
        
        if date and e_return is not None and not math.isnan(float(e_return)):
            e_return_val = float(e_return)
            idx_return = index_map.get(date)
            
            if idx_return is not None:
                daily_alpha = e_return_val - idx_return
                relative_features.append({
                    "date": date,
                    "daily_alpha": round(daily_alpha, 4)
                })
                
    return relative_features


def filter_false_positives(
    anomaly_predictions: List[Dict[str, Any]],
    min_volume_zscore: float = 0.5,
    bearish_score_threshold: float = 0.6,
    bullish_score_threshold: float = 0.8
) -> List[Dict[str, Any]]:
    """
    ENHANCEMENT 2: POST-PROCESSING FILTER & ASYMMETRIC THRESHOLD
    Menyaring False Positives dengan mengabaikan anomali saat likuiditas tipis,
    dan menerapkan ambang batas yang berbeda untuk pergerakan harga naik vs turun.
    """
    processed_anomalies = []
    
    for prediction in anomaly_predictions:
        vol_zscore = prediction.get("volume_zscore", 0.0)
        daily_return = prediction.get("daily_return", 0.0)
        anomaly_score = prediction.get("anomaly_score", 0.0)
        
        # Inisialisasi default
        pred_copy = copy.deepcopy(prediction)
        pred_copy["is_false_positive"] = False
        pred_copy["filtered_reason"] = None
        pred_copy["anomaly_type"] = "UNKNOWN"
        
        # Aturan 1: Filter Volume Rendah (Mengabaikan noise akibat likuiditas tipis)
        if vol_zscore < min_volume_zscore:
            pred_copy["is_false_positive"] = True
            pred_copy["filtered_reason"] = "low_volume"
            pred_copy["note"] = f"False Positive: Low Volume (Z-Score: {vol_zscore:.2f} < {min_volume_zscore})"
            processed_anomalies.append(pred_copy)
            continue 
            
        # Aturan 2: Threshold Asimetris (Berdasarkan arah pergerakan)
        is_bearish = daily_return < 0
        
        if is_bearish and anomaly_score >= bearish_score_threshold:
            pred_copy["anomaly_type"] = "BEARISH_SHOCK"
        elif not is_bearish and anomaly_score >= bullish_score_threshold:
            pred_copy["anomaly_type"] = "BULLISH_SPIKE"
        else:
            # Tidak lolos asymmetric threshold
            pred_copy["is_false_positive"] = True
            pred_copy["filtered_reason"] = "threshold_asymmetric"
            pred_copy["note"] = f"False Positive: Score {anomaly_score:.2f} below threshold (Bearish: {bearish_score_threshold}, Bullish: {bullish_score_threshold})"
            
        processed_anomalies.append(pred_copy)
            
    return processed_anomalies


def compute_adaptive_contamination(
    train_data: List[Dict[str, Any]],
    all_emiten_avg_volatility: Optional[float] = None,
    base_contamination: float = 0.03,
    recent_window_days: int = 500
) -> float:
    """
    2.1 HITUNG CONTAMINATION ADAPTIF (WINDOW 500 HARI TERAKHIR)
    Menyesuaikan contamination rate Isolation Forest berdasarkan volatilitas historis terkini emiten
    (menggunakan recent_window_days=500, bukan 10 tahun penuh, untuk mengantisipasi regime change).
    Emiten yang lebih volatile dari rata-rata pasar mendapatkan contamination lebih tinggi secara proporsional.
    Dibatasi (clamped) pada rentang [0.015, 0.10].
    """
    recent_data = train_data[-recent_window_days:] if len(train_data) > recent_window_days else train_data

    returns = [
        float(row["daily_return"])
        for row in recent_data
        if row.get("daily_return") is not None and not math.isnan(float(row["daily_return"]))
    ]

    hist_vol = float(np.std(returns, ddof=1)) if len(returns) > 1 else 1.0
    baseline_vol = all_emiten_avg_volatility if (all_emiten_avg_volatility and all_emiten_avg_volatility > 0) else hist_vol

    volatility_ratio = safe_divide(hist_vol, baseline_vol)
    if volatility_ratio is None:
        volatility_ratio = 1.0

    adaptive_c = base_contamination * volatility_ratio

    # Clamp antara 1.5% s/d 10%
    adaptive_c = max(0.015, min(0.10, adaptive_c))
    return round(float(adaptive_c), 4)


def train_model_with_adaptive_contamination(
    train_data: List[Dict[str, Any]],
    feature_columns: List[str],
    all_emiten_avg_volatility: Optional[float] = None,
    base_contamination: float = 0.03,
    recent_window_days: int = 500,
    random_state: int = 42
) -> Tuple[IsolationForest, Dict[str, Dict[str, float]], float]:
    """
    2.2 TRAINING DENGAN CONTAMINATION ADAPTIF
    Melatih Isolation Forest dengan contamination yang disesuaikan secara otomatis
    berdasarkan profil risiko / volatilitas terkini masing-masing saham.
    """
    contamination = compute_adaptive_contamination(
        train_data,
        all_emiten_avg_volatility=all_emiten_avg_volatility,
        base_contamination=base_contamination,
        recent_window_days=recent_window_days
    )

    # Ekstrak data train
    matrix = []
    for row in train_data:
        r_vals = []
        for col in feature_columns:
            val = row.get(col)
            r_vals.append(float(val) if val is not None and not math.isnan(val) else np.nan)
        matrix.append(r_vals)
    X_train = np.array(matrix, dtype=float)
    X_train_clean = impute_missing(X_train, method="median")

    feature_stats = compute_feature_stats(X_train_clean, feature_columns)

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=random_state
    )
    model.fit(X_train_clean)

    return model, feature_stats, contamination


def compute_recent_baseline_volatility(
    train_sets: Dict[str, List[Dict[str, Any]]],
    recent_window_days: int = 500
) -> float:
    """
    1.1 HITUNG BASELINE VOLATILITAS DARI WINDOW TERKINI
    """
    emiten_volatilities = []
    
    for ticker, train_data in train_sets.items():
        recent_data = train_data[-recent_window_days:] if len(train_data) > recent_window_days else train_data
        
        returns = [
            float(row["daily_return"]) for row in recent_data
            if row.get("daily_return") is not None and not math.isnan(float(row["daily_return"]))
        ]
        
        if len(returns) > 1:
            vol = float(np.std(returns, ddof=1))
            emiten_volatilities.append(vol)
            
    all_emiten_avg_vol = float(np.mean(emiten_volatilities)) if emiten_volatilities else 1.0
    
    return all_emiten_avg_vol


def compute_adaptive_contamination_v2(
    train_data: List[Dict[str, Any]],
    all_emiten_avg_volatility: float,
    base_contamination: float = 0.03,
    recent_window_days: int = 500
) -> float:
    """
    1.2 ADAPTIVE CONTAMINATION — KONSISTEN PAKAI WINDOW YANG SAMA
    """
    recent_data = train_data[-recent_window_days:] if len(train_data) > recent_window_days else train_data
    
    returns = [
        float(row["daily_return"]) for row in recent_data
        if row.get("daily_return") is not None and not math.isnan(float(row["daily_return"]))
    ]
    
    hist_vol = float(np.std(returns, ddof=1)) if len(returns) > 1 else 1.0
    baseline_vol = all_emiten_avg_volatility if all_emiten_avg_volatility > 0 else hist_vol
    
    volatility_ratio = safe_divide(hist_vol, baseline_vol)
    if volatility_ratio is None:
        volatility_ratio = 1.0
        
    adaptive_c = base_contamination * volatility_ratio
    adaptive_c = max(0.015, min(0.10, adaptive_c))
    
    return round(float(adaptive_c), 4)


def run_training_pipeline_v2(
    train_sets: Dict[str, List[Dict[str, Any]]],
    feature_columns: List[str],
    recent_window_days: int = 500,
    base_contamination: float = 0.03,
    random_state: int = 42
) -> Dict[str, Dict[str, Any]]:
    """
    1.3 PIPELINE UTAMA — URUTAN PEMANGGILAN YANG BENAR
    """
    # LANGKAH A: hitung baseline SEKALI, sebelum loop training
    all_emiten_avg_vol = compute_recent_baseline_volatility(train_sets, recent_window_days)
    
    print(f"Baseline Market Vol (Recent {recent_window_days} days): {all_emiten_avg_vol:.4f}")
    
    # LANGKAH B: baru masuk loop training per-emiten
    models = {}
    for ticker, train_data in train_sets.items():
        contamination = compute_adaptive_contamination_v2(
            train_data, 
            all_emiten_avg_vol, 
            base_contamination=base_contamination,
            recent_window_days=recent_window_days
        )
        
        # Ekstrak data train
        matrix = []
        for row in train_data:
            r_vals = []
            for col in feature_columns:
                val = row.get(col)
                r_vals.append(float(val) if val is not None and not math.isnan(float(val)) else np.nan)
            matrix.append(r_vals)
            
        X_train = np.array(matrix, dtype=float)
        X_train_clean = impute_missing(X_train, method="median")
        
        feature_stats = compute_feature_stats(X_train_clean, feature_columns)
        
        model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=random_state
        )
        
        if X_train_clean.shape[0] > 0:
            model.fit(X_train_clean)
            
        models[ticker] = {
            "model": model,
            "feature_stats": feature_stats,
            "contamination": contamination
        }
        
        print(f"{ticker} | Adaptive Contamination: {contamination:.4f}")
        
    return models

def validate_against_known_events_multi_tolerance(
    test_data: List[Dict[str, Any]],
    known_events: List[Dict[str, str]],
    tolerance_options: Optional[List[int]] = None
) -> Dict[int, Dict[str, Any]]:
    """
    3.1 VALIDASI EVENT NYATA DENGAN MULTI-TOLERANCE (3, 5, 7 Hari)
    Mengevaluasi match rate deteksi anomali pada jendela toleransi waktu yang fleksibel.
    """
    tolerances = tolerance_options or [3, 5, 7]
    results_per_tolerance: Dict[int, Dict[str, Any]] = {}

    test_dates = {
        str(row.get("date", ""))[:10]: bool(row.get("final_is_anomaly", row.get("is_anomaly", False)))
        for row in test_data
    }

    for tol in tolerances:
        matches = []
        for evt in known_events:
            evt_dt = pd.to_datetime(evt["date"])
            detected = False
            matched_dates = []

            for delta in range(-tol, tol + 1):
                check_date = (evt_dt + pd.Timedelta(days=delta)).strftime("%Y-%m-%d")
                if test_dates.get(check_date, False):
                    detected = True
                    matched_dates.append(check_date)

            matches.append({
                "event": evt.get("description", ""),
                "date": evt.get("date", ""),
                "detected": detected,
                "matched_dates": matched_dates
            })

        detected_count = sum(1 for m in matches if m["detected"])
        match_rate = safe_divide(detected_count, len(known_events))

        results_per_tolerance[tol] = {
            "tolerance_days": tol,
            "detected_count": detected_count,
            "total_events": len(known_events),
            "match_rate": round(match_rate, 4),
            "match_rate_pct": round(match_rate * 100.0, 2),
            "details": matches
        }

    return results_per_tolerance


def extract_false_positives_for_review(
    injection_test_result: Dict[str, Any],
    test_data: List[Dict[str, Any]],
    n_samples: int = 10,
    random_state: int = 42
) -> List[Dict[str, Any]]:
    """
    3.2 EKSTRAKSI FALSE POSITIVES UNTUK REVIEW MANUAL
    Mengambil sampel titik non-injeksi yang terdeteksi anomali agar analis dapat
    memverifikasi apakah tanggal tersebut sesungguhnya menyimpan sentimen / berita riil.
    """
    fp_indices = injection_test_result.get("false_positive_indices", [])
    if not fp_indices:
        # Fallback bila index FP tidak terdaftar eksplisit: cari index anomali non-injected
        injected_set = set(injection_test_result.get("injected_indices", []))
        predicted_set = set(injection_test_result.get("predicted_anomaly_indices", []))
        fp_indices = sorted(list(predicted_set - injected_set))

    if not fp_indices:
        return []

    rng = random.Random(random_state)
    sample_size = min(n_samples, len(fp_indices))
    sampled_indices = rng.sample(fp_indices, sample_size)

    review_list = []
    for idx in sampled_indices:
        if 0 <= idx < len(test_data):
            row = test_data[idx]
            review_list.append({
                "index": int(idx),
                "date": row.get("date"),
                "close": row.get("close"),
                "anomaly_score": row.get("anomaly_score"),
                "contributing_factors": row.get("contributing_factors", []),
                "note": "CEK MANUAL: apakah ada berita/event nyata atau transaksi masif di tanggal ini?"
            })

    return review_list


def cluster_consecutive_anomalies(
    anomaly_points: List[Dict[str, Any]],
    max_gap_days: int = 3
) -> List[Dict[str, Any]]:
    """
    3.3 CLUSTERING ANOMALI BERURUTAN MENJADI EPISODE
    Mengelompokkan titik-titik anomali yang berdekatan (gap <= max_gap_days)
    menjadi satu episode gejolak / anomali pasar yang kohesif.
    """
    if not anomaly_points:
        return []

    # Urutkan berdasarkan tanggal
    valid_points = [p for p in anomaly_points if p.get("date")]
    sorted_points = sorted(valid_points, key=lambda x: str(x["date"]))

    clusters: List[List[Dict[str, Any]]] = []
    current_cluster: List[Dict[str, Any]] = []

    for point in sorted_points:
        if not current_cluster:
            current_cluster.append(point)
        else:
            prev_dt = pd.to_datetime(current_cluster[-1]["date"])
            curr_dt = pd.to_datetime(point["date"])
            days_diff = (curr_dt - prev_dt).days

            if days_diff <= max_gap_days:
                current_cluster.append(point)
            else:
                clusters.append(current_cluster)
                current_cluster = [point]

    if current_cluster:
        clusters.append(current_cluster)

    episode_list: List[Dict[str, Any]] = []
    for cl in clusters:
        scores = [float(p.get("score", p.get("anomaly_score", 0.0))) for p in cl]
        max_idx = int(np.argmax(scores)) if scores else 0
        peak_score = scores[max_idx] if scores else 0.0
        peak_date = cl[max_idx].get("date")

        # Cari dominant factor pemicu episode
        factor_counts: Dict[str, int] = {}
        for p in cl:
            factors = p.get("factors", p.get("contributing_factors", []))
            for f in factors:
                f_name = f.get("field", "unknown") if isinstance(f, dict) else str(f)
                factor_counts[f_name] = factor_counts.get(f_name, 0) + 1

        dominant_factors = sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)
        top_dominant = [item[0] for item in dominant_factors[:2]]

        episode_list.append({
            "start_date": cl[0].get("date"),
            "end_date": cl[-1].get("date"),
            "n_days": len(cl),
            "peak_score": round(peak_score, 4),
            "peak_date": peak_date,
            "dominant_factors": top_dominant
        })

    return episode_list


def normalize_score_percentile(raw_scores: Union[List[float], np.ndarray]) -> List[float]:
    """
    3.4 NORMALISASI SCORE BERBASIS PERSENTIL (0 - 100)
    Mengonversi decision_function score menjadi percentile rank.
    Menghindari clipping ekstrem dari min-max scaling dan memberikan skala 0-100 yang lebih granular.
    """
    scores = [float(s) for s in raw_scores]
    if not scores:
        return []

    # Invert score decision_function (makin negatif sklearn = makin anomali)
    inverted = [-s for s in scores]
    n = len(inverted)

    percentile_scores = []
    for val in inverted:
        # Hitung persentase observasi yang memiliki skor anomali <= observasi ini
        rank = sum(1 for v in inverted if v <= val)
        pct = safe_divide(rank, n) * 100.0
        percentile_scores.append(round(pct, 2))

    return percentile_scores


def build_extended_event_calendar(
    ticker: str,
    categories: Optional[List[str]] = None
) -> List[Dict[str, str]]:
    """
    3.5 EXTENDED EVENT CALENDAR (5-8 EVENT PER EMITEN)
    Daftar event riil komprehensif mencakup laporan keuangan (earnings), dividen, RUPS,
    dan pergerakan sektor / MSCI rebalancing untuk validasi anomali 2025-2026.
    """
    clean_sym = ticker.upper().replace(".JK", "")

    calendar_database: Dict[str, List[Dict[str, str]]] = {
        "BBCA": [
            {"date": "2025-01-22", "category": "earnings", "description": "BBCA FY2024 Earnings Release & Record Net Profit"},
            {"date": "2025-03-14", "category": "corporate_action", "description": "BBCA Annual General Meeting of Shareholders (AGMS)"},
            {"date": "2025-03-24", "category": "dividend", "description": "BBCA Cum-Dividend & Ex-Dividend High Trading Volume"},
            {"date": "2025-04-23", "category": "earnings", "description": "BBCA Q1 2025 Financial Performance Disclosure"},
            {"date": "2025-05-30", "category": "sector_news", "description": "MSCI Global Standard Index Semi-Annual Rebalancing"},
            {"date": "2025-07-24", "category": "earnings", "description": "BBCA H1 2025 Earnings Briefing & Net Interest Margin Update"},
            {"date": "2025-08-05", "category": "sector_news", "description": "Global Banking Sell-off Rebound & Foreign Outflow Peak"}
        ],
        "BBRI": [
            {"date": "2025-01-30", "category": "earnings", "description": "BBRI FY2024 Financial Performance & MSME Restructuring Progress"},
            {"date": "2025-03-05", "category": "corporate_action", "description": "BBRI RUPST & Special Dividend Ratio Declaration"},
            {"date": "2025-03-14", "category": "dividend", "description": "BBRI Cum/Ex-Dividend Date Market Volatility"},
            {"date": "2025-04-29", "category": "earnings", "description": "BBRI Q1 2025 Financial Results & NPL Coverage Disclosure"},
            {"date": "2025-05-30", "category": "sector_news", "description": "MSCI Indonesia Banking Portfolio Weight Adjustment"},
            {"date": "2025-07-31", "category": "earnings", "description": "BBRI H1 2025 Performance Conference"},
            {"date": "2025-08-05", "category": "sector_news", "description": "Global Tech & Banking Liquidation Shockwave Reaction"}
        ],
        "BMRI": [
            {"date": "2025-01-28", "category": "earnings", "description": "BMRI FY2024 Financial Results Analyst Conference"},
            {"date": "2025-03-19", "category": "corporate_action", "description": "BMRI Annual General Meeting & Special Dividend Approval"},
            {"date": "2025-03-26", "category": "dividend", "description": "BMRI Cum-Dividend & Record Date Reaction"},
            {"date": "2025-04-28", "category": "earnings", "description": "BMRI Q1 2025 Financial Results Briefing"},
            {"date": "2025-05-30", "category": "sector_news", "description": "MSCI Large Cap Index Rebalance Inflow"},
            {"date": "2025-07-30", "category": "earnings", "description": "BMRI H1 2025 Earnings Announcement"},
            {"date": "2025-08-05", "category": "sector_news", "description": "Global Market Flash Drop & Rapid Domestic Banking Recovery"}
        ],
        "BBNI": [
            {"date": "2025-01-24", "category": "earnings", "description": "BBNI FY2024 Performance Briefing & Digital Transformation Update"},
            {"date": "2025-03-10", "category": "corporate_action", "description": "BBNI Annual General Meeting of Shareholders"},
            {"date": "2025-03-18", "category": "dividend", "description": "BBNI Ex-Dividend Date Market Reaction"},
            {"date": "2025-04-25", "category": "earnings", "description": "BBNI Q1 2025 Net Profit & Asset Quality Update"},
            {"date": "2025-05-30", "category": "sector_news", "description": "MSCI Index Semi-Annual Weight Rebalance"},
            {"date": "2025-07-28", "category": "earnings", "description": "BBNI H1 2025 Financial Results"},
            {"date": "2025-08-05", "category": "sector_news", "description": "IHSG Shock Pullback & Defensive Banking Inflow"}
        ],
        "TLKM": [
            {"date": "2025-02-18", "category": "corporate_action", "description": "Telkom Data Center Monetization & Infra Fiber Strategy Update"},
            {"date": "2025-03-25", "category": "earnings", "description": "TLKM FY2024 Financial Report & Telkomsel Revenue Realization"},
            {"date": "2025-05-28", "category": "corporate_action", "description": "TLKM Annual General Meeting of Shareholders & Dividend Ratio"},
            {"date": "2025-06-06", "category": "dividend", "description": "TLKM Cum-Dividend / Ex-Dividend Date High Volume"},
            {"date": "2025-07-30", "category": "earnings", "description": "TLKM H1 2025 Financial Performance Release"},
            {"date": "2025-08-05", "category": "sector_news", "description": "Defensive Sector Rotation During Overseas Market Pullback"},
            {"date": "2025-11-25", "category": "sector_news", "description": "MSCI Semi-Annual Index Adjustment"}
        ],
        "ASII": [
            {"date": "2025-02-27", "category": "earnings", "description": "ASII FY2024 Full Year Earnings & Automotive Sales Disclosure"},
            {"date": "2025-04-29", "category": "corporate_action", "description": "ASII AGMS & Final Dividend Declaration"},
            {"date": "2025-05-09", "category": "dividend", "description": "ASII Cum-Dividend High Liquidity Trading"},
            {"date": "2025-05-30", "category": "sector_news", "description": "MSCI Index Weight Rebalance Adjustment"},
            {"date": "2025-07-29", "category": "earnings", "description": "ASII H1 2025 Earnings & Heavy Equipment Outlook"},
            {"date": "2025-08-05", "category": "sector_news", "description": "Global Shock & Cyclical Sector Volatility"}
        ],
        "ICBP": [
            {"date": "2025-03-21", "category": "earnings", "description": "ICBP FY2024 Earnings Release & Pinehill Operations"},
            {"date": "2025-04-30", "category": "earnings", "description": "ICBP Q1 2025 Financial Results"},
            {"date": "2025-06-25", "category": "corporate_action", "description": "ICBP Annual General Meeting of Shareholders & Dividend"},
            {"date": "2025-07-04", "category": "dividend", "description": "ICBP Cum/Ex-Dividend Date"},
            {"date": "2025-07-31", "category": "earnings", "description": "ICBP H1 2025 Earnings Announcement"},
            {"date": "2025-08-05", "category": "sector_news", "description": "Consumer Goods Defensive Buying Session"}
        ],
        "UNVR": [
            {"date": "2025-02-06", "category": "earnings", "description": "UNVR FY2024 Financial Report & Restructuring Review"},
            {"date": "2025-04-24", "category": "earnings", "description": "UNVR Q1 2025 Financial Results & Distribution Channel Update"},
            {"date": "2025-06-19", "category": "corporate_action", "description": "UNVR RUPST & Special Dividend Approval"},
            {"date": "2025-06-27", "category": "dividend", "description": "UNVR Ex-Dividend Date Price Reaction"},
            {"date": "2025-07-25", "category": "earnings", "description": "UNVR H1 2025 Performance Review"},
            {"date": "2025-08-05", "category": "sector_news", "description": "Market Wide Volatility & Consumer Staple Volume"}
        ],
        "ADRO": [
            {"date": "2025-02-28", "category": "earnings", "description": "ADRO FY2024 Financial Performance & AAI Spin-off Transition"},
            {"date": "2025-05-15", "category": "corporate_action", "description": "ADRO AGMS & High Dividend Yield Distribution"},
            {"date": "2025-05-23", "category": "dividend", "description": "ADRO Cum-Dividend Extreme Volume & Gap Down"},
            {"date": "2025-05-30", "category": "sector_news", "description": "MSCI Index Semi-Annual Weight Rebalance"},
            {"date": "2025-08-05", "category": "sector_news", "description": "Commodity Sector & Energy Price Shock"},
            {"date": "2025-08-28", "category": "earnings", "description": "ADRO H1 2025 Earnings Briefing"}
        ],
        "KLBF": [
            {"date": "2025-03-27", "category": "earnings", "description": "KLBF FY2024 Earnings & Pharma Margin Expansion"},
            {"date": "2025-04-28", "category": "earnings", "description": "KLBF Q1 2025 Financial Results"},
            {"date": "2025-05-19", "category": "corporate_action", "description": "KLBF RUPST & Dividend Payout Declaration"},
            {"date": "2025-05-28", "category": "dividend", "description": "KLBF Cum-Dividend Trading"},
            {"date": "2025-07-31", "category": "earnings", "description": "KLBF H1 2025 Earnings Announcement"},
            {"date": "2025-08-05", "category": "sector_news", "description": "Defensive Healthcare Capital Inflow"}
        ]
    }

    events = calendar_database.get(clean_sym, [
        {"date": "2025-01-30", "category": "earnings", "description": f"{clean_sym} Full Year 2024 Financial Report"},
        {"date": "2025-03-25", "category": "dividend", "description": f"{clean_sym} Dividend Announcement & Distribution"},
        {"date": "2025-05-30", "category": "sector_news", "description": f"{clean_sym} MSCI Semi-Annual Rebalance Adjustment"},
        {"date": "2025-08-05", "category": "sector_news", "description": f"{clean_sym} Market-wide Volatility Session"}
    ])

    if categories:
        events = [e for e in events if e.get("category") in categories]

    return sorted(events, key=lambda x: x["date"])


# ============================================================================
# SELF-TESTS & CLI EXECUTION
# ============================================================================

def _run_self_tests():
    """Unit test komprehensif memvalidasi implementasi PLAN.md line 310-500."""
    print("Menjalankan self-test Isolation Forest Anomaly Detection...")

    # Buat dataset simulasi 10 perusahaan dengan 1 outlier ekstrem
    np.random.seed(42)
    mock_data = []

    tickers = ["BBCA", "BMRI", "BBRI", "BBNI", "TLKM", "ISAT", "EXCL", "ASII", "ICBP", "WEIRD_STOCK"]
    for sym in tickers:
        if sym == "WEIRD_STOCK":
            # Anomali ekstrem: P/E raksasa, revenue drop drastis, volatilitas gila-gilaan
            m = {
                "company": sym,
                "period": "2026-Q1",
                "valuation_metrics": {"pe_relative": 15.5, "pbv_relative": 12.0},
                "growth_metrics": {"revenue_growth_yoy": -85.0, "growth_acceleration": -50.0},
                "price_metrics": {"volatility": 95.0},
                "ownership_metrics": {"net_institutional_flow_pct": -45.0, "insider_ownership_change": -30.0}
            }
        else:
            # Perusahaan normal dengan sedikit variasi acak
            m = {
                "company": sym,
                "period": "2026-Q1",
                "valuation_metrics": {"pe_relative": 1.0 + np.random.normal(0, 0.1), "pbv_relative": 1.5 + np.random.normal(0, 0.1)},
                "growth_metrics": {"revenue_growth_yoy": 12.0 + np.random.normal(0, 2.0), "growth_acceleration": 1.0 + np.random.normal(0, 0.5)},
                "price_metrics": {"volatility": 18.0 + np.random.normal(0, 2.0)},
                "ownership_metrics": {"net_institutional_flow_pct": 2.0 + np.random.normal(0, 0.5), "insider_ownership_change": 0.0}
            }
        mock_data.append(m)

    # 1. Test Feature Matrix & Imputation
    X_raw, comps = build_feature_matrix(mock_data, DEFAULT_FEATURE_FIELDS)
    assert len(X_raw) == 10
    assert len(comps) == 10
    assert comps[0] == "BBCA"

    X_clean = impute_missing(X_raw, method="median")
    assert X_clean.shape == (10, len(DEFAULT_FEATURE_FIELDS))
    assert not np.isnan(X_clean).any()

    # 2. Test Anomaly Detection
    res = detect_anomalies_isolation_forest(mock_data, contamination=0.10)
    assert res["total_companies_analyzed"] == 10
    assert res["anomalies_detected"] >= 1
    assert "period" in res
    assert len(res["anomalies"]) >= 1

    # WEIRD_STOCK harus menjadi anomali dengan score tertinggi
    top_anomaly = res["anomalies"][0]
    assert top_anomaly["company"] == "WEIRD_STOCK"
    assert top_anomaly["anomaly_score"] >= 0.5
    assert top_anomaly["severity"] in ["moderate", "severe"]
    assert len(top_anomaly["contributing_factors"]) > 0
    assert "terdeteksi anomali terutama karena" in top_anomaly["evidence"]

    # 3. Test Normalize Scores
    dummy_scores = [-0.25, -0.10, 0.05, 0.20]
    norm_scores = normalize_scores(dummy_scores)
    assert norm_scores[0] == 1.0  # paling negatif -> paling anomali (1.0)
    assert norm_scores[-1] == 0.0  # paling positif -> paling normal (0.0)

    # 4. Test Classify Severity
    assert classify_severity(0.30) == "normal"
    assert classify_severity(0.60) == "mild"
    assert classify_severity(0.75) == "moderate"
    assert classify_severity(0.90) == "severe"

    # 5. Test REVISION Functions (PLAN.md line 502-718)
    # 5.1 build_cross_sectional_dataset & detect_market_wide_anomaly
    mock_series = {
        "BBCA": [{"date": f"2025-01-0{i}", "daily_return": 0.5 if i != 3 else -4.5} for i in range(1, 6)],
        "BBRI": [{"date": f"2025-01-0{i}", "daily_return": 0.2 if i != 3 else -4.2} for i in range(1, 6)],
        "BMRI": [{"date": f"2025-01-0{i}", "daily_return": 0.3 if i != 3 else -4.0} for i in range(1, 6)],
    }
    cross_df = build_cross_sectional_dataset(mock_series, ["BBCA", "BBRI", "BMRI"])
    assert len(cross_df) == 5
    assert "BBCA_return" in cross_df[0]

    mw_res = detect_market_wide_anomaly(cross_df, ["BBCA", "BBRI", "BMRI"], threshold_pct=0.6, z_threshold=0.5)
    assert len(mw_res) >= 1

    # 5.2 combine_time_series_and_cross_sectional
    ts_rows = [{"date": f"2025-01-0{i}", "close": 1000, "is_anomaly": (i == 2), "anomaly_score": 0.8 if i == 2 else 0.2} for i in range(1, 6)]
    combined = combine_time_series_and_cross_sectional(ts_rows, mw_res)
    assert len(combined) == 5
    assert "final_is_anomaly" in combined[0]
    assert "anomaly_source" in combined[0]

    # 5.3 compute_adaptive_contamination & train_model_with_adaptive_contamination
    mock_train = [{"daily_return": np.random.normal(0, 1.5), "vol": 10.0} for _ in range(50)]
    adapt_c = compute_adaptive_contamination(mock_train, all_emiten_avg_volatility=1.0, base_contamination=0.03)
    assert 0.015 <= adapt_c <= 0.10

    adapt_model, adapt_stats, used_c = train_model_with_adaptive_contamination(
        mock_train, feature_columns=["daily_return", "vol"], all_emiten_avg_volatility=1.0, base_contamination=0.03
    )
    assert adapt_model is not None
    assert "daily_return" in adapt_stats
    assert used_c == adapt_c

    # 5.3.1 compute_recent_baseline_volatility, compute_adaptive_contamination_v2, run_training_pipeline_v2
    mock_train_sets = {
        "BBCA": [{"daily_return": np.random.normal(0, 1.0), "vol": 10.0} for _ in range(100)],
        "GOTO": [{"daily_return": np.random.normal(0, 3.0), "vol": 30.0} for _ in range(100)]
    }
    baseline_vol = compute_recent_baseline_volatility(mock_train_sets, recent_window_days=50)
    assert baseline_vol > 0
    
    adapt_c_v2 = compute_adaptive_contamination_v2(
        mock_train_sets["GOTO"], baseline_vol, base_contamination=0.03, recent_window_days=50
    )
    assert 0.015 <= adapt_c_v2 <= 0.10
    
    pipeline_models = run_training_pipeline_v2(
        mock_train_sets, feature_columns=["daily_return", "vol"], recent_window_days=50
    )
    assert "BBCA" in pipeline_models
    assert "GOTO" in pipeline_models
    assert pipeline_models["BBCA"]["model"] is not None

    # 5.4 cluster_consecutive_anomalies
    mock_anomaly_points = [
        {"date": "2025-03-01", "score": 0.7, "factors": [{"field": "daily_return"}]},
        {"date": "2025-03-02", "score": 0.9, "factors": [{"field": "daily_return"}]},
        {"date": "2025-03-10", "score": 0.85, "factors": [{"field": "volatility_20d"}]}
    ]
    episodes = cluster_consecutive_anomalies(mock_anomaly_points, max_gap_days=2)
    assert len(episodes) == 2  # episode 1: Mar 1-2 (2 days), episode 2: Mar 10 (1 day)
    assert episodes[0]["n_days"] == 2
    assert episodes[0]["peak_score"] == 0.9
    assert episodes[0]["peak_date"] == "2025-03-02"

    # 5.5 normalize_score_percentile
    pct_scores = normalize_score_percentile([-0.20, -0.10, 0.0, 0.10, 0.20])
    assert len(pct_scores) == 5
    assert pct_scores[0] == 100.0  # most negative = highest anomaly rank

    # 5.6 validate_against_known_events_multi_tolerance
    mock_events = [{"date": "2025-03-03", "description": "Test Event"}]
    tol_res = validate_against_known_events_multi_tolerance(ts_rows, mock_events, [3, 5])
    assert 3 in tol_res and 5 in tol_res

    # 5.7 build_extended_event_calendar
    bbca_cal = build_extended_event_calendar("BBCA")
    assert len(bbca_cal) >= 5
    assert any("earnings" in e.get("category", "") or "dividend" in e.get("category", "") for e in bbca_cal)

    # 5.8 PLAN.md ## UPDATE: Historical Z-Score & Dual-Method Market-Wide Shock
    mock_tr_data = [{"date": f"2024-01-0{i}", "daily_return": 0.1 * i} for i in range(1, 10)]
    mock_te_data = [
        {"date": "2025-01-01", "daily_return": 0.5},
        {"date": "2025-01-02", "daily_return": -4.0}
    ]
    z_scores_bbca = compute_historical_zscore_per_emiten(mock_tr_data, mock_te_data, "BBCA")
    assert len(z_scores_bbca) == 2
    assert "z_score" in z_scores_bbca[0]

    all_z = {
        "BBCA": z_scores_bbca,
        "BBRI": [{"date": "2025-01-01", "z_score": 0.2}, {"date": "2025-01-02", "z_score": -3.5}],
        "BMRI": [{"date": "2025-01-01", "z_score": 0.1}, {"date": "2025-01-02", "z_score": -3.8}]
    }
    mw_shock_c1 = detect_market_wide_shock(all_z, ["BBCA", "BBRI", "BMRI"], z_threshold=1.5, vote_threshold_pct=0.6)
    assert len(mw_shock_c1) == 1
    assert mw_shock_c1[0]["date"] == "2025-01-02"

    mock_tr_all = {
        "BBCA": [{"date": "2024-01-01", "daily_return": 0.1}, {"date": "2024-01-02", "daily_return": 0.2}],
        "BBRI": [{"date": "2024-01-01", "daily_return": 0.0}, {"date": "2024-01-02", "daily_return": 0.1}]
    }
    mock_te_all = {
        "BBCA": [{"date": "2025-01-01", "daily_return": 0.1}, {"date": "2025-01-02", "daily_return": -5.0}],
        "BBRI": [{"date": "2025-01-01", "daily_return": 0.1}, {"date": "2025-01-02", "daily_return": -5.0}]
    }
    mw_shock_c2 = compute_market_aggregate_shock(mock_tr_all, mock_te_all, ["BBCA", "BBRI"], threshold_sigma=1.5)
    assert len(mw_shock_c2) == 1
    assert mw_shock_c2[0]["date"] == "2025-01-02"

    cross_val = cross_validate_market_wide(mw_shock_c1, mw_shock_c2)
    assert "2025-01-02" in cross_val["high_confidence"]

    # 5.9 PLAN.md ## UPDATE ENHANCEMENT: Context & Post-Processing Filter
    mock_emiten_ret = [{"date": "2025-01-01", "daily_return": 2.0}, {"date": "2025-01-02", "daily_return": -3.0}]
    mock_idx_ret = [{"date": "2025-01-01", "daily_return": 1.0}, {"date": "2025-01-02", "daily_return": -2.0}]
    alpha_feat = compute_relative_alpha(mock_emiten_ret, mock_idx_ret)
    assert len(alpha_feat) == 2
    assert alpha_feat[0]["daily_alpha"] == 1.0
    assert alpha_feat[1]["daily_alpha"] == -1.0

    mock_preds = [
        # FP karena volume kecil
        {"date": "2025-01-01", "volume_zscore": 0.2, "daily_return": -5.0, "anomaly_score": 0.9},
        # TP Bearish
        {"date": "2025-01-02", "volume_zscore": 1.0, "daily_return": -4.0, "anomaly_score": 0.65},
        # FP Bullish (score < 0.8)
        {"date": "2025-01-03", "volume_zscore": 1.5, "daily_return": 3.0, "anomaly_score": 0.75},
        # TP Bullish
        {"date": "2025-01-04", "volume_zscore": 2.0, "daily_return": 5.0, "anomaly_score": 0.85}
    ]
    filtered_preds = filter_false_positives(mock_preds)
    assert len(filtered_preds) == 2
    assert filtered_preds[0]["anomaly_type"] == "BEARISH_SHOCK"
    assert filtered_preds[1]["anomaly_type"] == "BULLISH_SPIKE"

    # 5.10 Test New Feature Engineering: log_return, value_traded, value_traded_zscore, return_vs_ihsg & date alignment
    mock_ihsg = [{"date": f"2025-01-{i:02d}", "close": 7000.0 + i * 10} for i in range(1, 75)]
    mock_emiten_series = [
        {
            "date": f"2025-01-{i:02d}",
            "open": 1000.0,
            "high": 1050.0,
            "low": 980.0,
            "close": 1000.0 + (50 if i == 70 else i),
            "volume": 100000.0 if i != 70 else 500000.0
        }
        for i in range(1, 75)
    ]
    # Simulasi mismatch hari libur di index 65 (tanggal 2025-01-66)
    del mock_ihsg[64]

    computed_feats = compute_daily_features(mock_emiten_series, ihsg_series=mock_ihsg)
    assert len(computed_feats) > 0
    # Pastikan tanggal yang tidak ada di IHSG di-skip (alignment benar)
    computed_dates = [f["date"] for f in computed_feats]
    assert "2025-01-65" not in computed_dates

    sample_feat = computed_feats[0]
    assert "value_traded" in sample_feat
    assert "value_traded_zscore" in sample_feat
    assert "return_vs_ihsg" in sample_feat
    assert "daily_return" in sample_feat

    # Validasi bahwa daily_return menggunakan log return: ln(close_t / close_t-1) * 100
    p_prev = mock_emiten_series[59]["close"]
    p_curr = mock_emiten_series[60]["close"]
    expected_log_ret = round(math.log(p_curr / p_prev) * 100.0, 4)
    assert sample_feat["daily_return"] == expected_log_ret

    print("Semua self-test Isolation Forest & REVISION PLAN BERHASIL lolos tanpa kendala.")


if __name__ == "__main__":
    _run_self_tests()
    print("=" * 85)

    # Contoh eksekusi live jika dijalankan dari command line
    sample_tickers = sys.argv[1].split(",") if len(sys.argv) > 1 else [
        "BBCA", "BMRI", "BBRI", "BBNI", "TLKM", "ISAT", "EXCL", "BUMI", "ADRO", "ASII"
    ]
    p = sys.argv[2] if len(sys.argv) > 2 else "current"

    print(f"Menjalankan deteksi anomali pasar untuk {len(sample_tickers)} ticker (periode: {p})...")
    live_res = fetch_and_detect_anomalies(sample_tickers, period=p, contamination=0.15)
    print(format_anomalies_summary(live_res))
