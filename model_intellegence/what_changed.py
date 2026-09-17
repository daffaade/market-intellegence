from __future__ import annotations
import math
import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Memastikan direktori root repo dan direktori saat ini berada di sys.path
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent if (CURRENT_DIR.parent / "unified_data").exists() else CURRENT_DIR
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    # 1. Absolute import ketika direktori model-intellegence ada di sys.path
    from derived_metrics import (
        safe_divide,
        compute_derived_metrics,
        fetch_and_compute_derived_metrics,
        _get
    )
    HAS_DERIVED_METRICS = True
except ImportError:
    try:
        # 2. Relative import jika diakses sebagai package (misal dari __init__.py)
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


# ============================================================================
# WHAT CHANGED ANALYSIS
# Sesuai spesifikasi model-intellegence/PLAN.md (line 184-224)
# ============================================================================

METRIC_CATEGORIES = [
    "valuation_metrics",
    "growth_metrics",
    "price_metrics",
    "ownership_metrics",
    "dividend_metrics"
]

DEFAULT_THRESHOLD_PCT = 10.0  # Sesuai PLAN.md: set thresholds = 10%


def compute_what_changed(
    metrics_now: Dict[str, Any],
    metrics_prev: Dict[str, Any],
    thresholds: Optional[Union[Dict[str, float], float]] = None,
    default_threshold: float = DEFAULT_THRESHOLD_PCT,
    sort_by: str = "magnitude"
) -> Dict[str, Any]:
    """
    Menganalisis perubahan signifikan antara dua snapshot metrik derived.
    
    Argumen:
      - metrics_now: Dictionary hasil derived metrics periode saat ini (mutakhir).
      - metrics_prev: Dictionary hasil derived metrics periode pembanding sebelumnya.
      - thresholds: Ambang batas persentase perubahan minimum untuk dianggap signifikan.
                    Bisa berupa float tunggal (misal 10.0) atau dict per field {'field_name': 15.0}.
      - default_threshold: Ambang batas default jika tidak ditentukan spesifik (default 10.0%).
      - sort_by: 'magnitude' (default, descending abs(delta_pct)) atau 'delta_pct' (descending delta_pct).
      
    Mengembalikan:
      Dictionary dengan daftar perubahan terdeteksi beserta besaran dan arah perubahannya.
    """
    if not isinstance(metrics_now, dict) or not isinstance(metrics_prev, dict):
        return {
            "status": "ERROR",
            "error": "metrics_now dan metrics_prev harus berupa dictionary."
        }

    changes: List[Dict[str, Any]] = []

    for category in METRIC_CATEGORIES:
        cat_now = metrics_now.get(category)
        cat_prev = metrics_prev.get(category)

        if not isinstance(cat_now, dict) or not isinstance(cat_prev, dict):
            continue

        for field, value_now in cat_now.items():
            value_prev = cat_prev.get(field)

            # Skip jika data tidak lengkap
            if value_now is None or value_prev is None:
                continue

            try:
                v_now = float(value_now)
                v_prev = float(value_prev)
            except (ValueError, TypeError):
                continue

            delta = v_now - v_prev

            # Hitung persentase perubahan terhadap nilai absolut periode sebelumnya
            if abs(v_prev) > 1e-9:
                d_pct = safe_divide(delta, abs(v_prev))
                delta_pct = (d_pct * 100.0) if d_pct is not None else None
            else:
                # Jika nilai sebelumnya 0
                if abs(delta) < 1e-9:
                    delta_pct = 0.0
                else:
                    # Nilai berubah dari 0 ke angka bukan nol (dianggap perubahan signifikan 100%)
                    delta_pct = 100.0 if delta > 0 else -100.0

            if delta_pct is None:
                continue

            # Tentukan threshold signifikansi
            if isinstance(thresholds, (int, float)):
                threshold = float(thresholds)
            elif isinstance(thresholds, dict) and field in thresholds:
                threshold = float(thresholds[field])
            else:
                threshold = default_threshold

            # Hanya catat jika besaran perubahan melebihi threshold
            if abs(delta_pct) >= threshold:
                changes.append({
                    "category": category,
                    "field": field,
                    "value_before": round(v_prev, 4),
                    "value_after": round(v_now, 4),
                    "delta": round(delta, 4),
                    "delta_pct": round(delta_pct, 2),
                    "direction": "increase" if delta > 0 else "decrease"
                })

    # Urutkan berdasarkan besarnya perubahan
    if sort_by == "delta_pct":
        changes.sort(key=lambda x: x["delta_pct"], reverse=True)
    else:
        # Default: Magnitude perubahan (nilai absolut persentase perubahan)
        changes.sort(key=lambda x: abs(x["delta_pct"]), reverse=True)

    company_name = metrics_now.get("company") or metrics_now.get("symbol") or metrics_now.get("ticker", "UNKNOWN")
    period_now = metrics_now.get("period", "current")
    period_prev = metrics_prev.get("period", "previous")

    return {
        "status": "SUCCESS",
        "company": company_name,
        "period": period_now,
        "compared_to": period_prev,
        "changes": changes,
        "total_changes_detected": len(changes)
    }


# ============================================================================
# UNIFIED DATA & DERIVED METRICS PIPELINE INTEGRATION
# ============================================================================

def fetch_and_analyze_what_changed(
    ticker: str,
    period_now: str = "current",
    period_prev: str = "5y",
    thresholds: Optional[Union[Dict[str, float], float]] = None,
    default_threshold: float = DEFAULT_THRESHOLD_PCT,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Mengambil data derived metrics secara otomatis untuk 2 periode berbeda dari
    Unified Data Layer dan menganalisis apa yang berubah secara signifikan.
    """
    if not HAS_DERIVED_METRICS:
        return {
            "status": "ERROR",
            "error": "Modul derived_metrics tidak tersedia."
        }

    clean_ticker = ticker.upper().replace(".JK", "").strip()

    # Ambil derived metrics untuk periode saat ini
    metrics_now = fetch_and_compute_derived_metrics(
        clean_ticker,
        period=period_now,
        force_refresh=force_refresh
    )
    if metrics_now.get("status") != "SUCCESS":
        return {
            "status": "ERROR",
            "error": f"Gagal mengambil derived metrics periode '{period_now}' untuk {clean_ticker}."
        }

    # Ambil derived metrics untuk periode pembanding
    metrics_prev = fetch_and_compute_derived_metrics(
        clean_ticker,
        period=period_prev,
        force_refresh=force_refresh
    )
    if metrics_prev.get("status") != "SUCCESS":
        return {
            "status": "ERROR",
            "error": f"Gagal mengambil derived metrics periode '{period_prev}' untuk {clean_ticker}."
        }

    # Analisis perubahan
    result = compute_what_changed(
        metrics_now=metrics_now,
        metrics_prev=metrics_prev,
        thresholds=thresholds,
        default_threshold=default_threshold
    )

    return result


def format_what_changed_summary(analysis_result: Dict[str, Any]) -> str:
    """
    Menghasilkan ringkasan naratif ramah baca dari hasil analisis what_changed.
    """
    if analysis_result.get("status") != "SUCCESS":
        return f"Error: {analysis_result.get('error', 'Analisis tidak berhasil.')}"

    company = analysis_result.get("company", "Emiten")
    p_now = analysis_result.get("period", "saat ini")
    p_prev = analysis_result.get("compared_to", "sebelumnya")
    changes = analysis_result.get("changes", [])
    total = analysis_result.get("total_changes_detected", 0)

    if total == 0:
        return f"Tidak terdeteksi perubahan signifikan (>= threshold) pada {company} antara periode {p_now} dan {p_prev}."

    lines = [
        f"Analisis Perubahan Signifikan untuk {company} ({p_now} vs {p_prev}):",
        f"Total perubahan terdeteksi: {total} metrik\n"
    ]

    for i, c in enumerate(changes, 1):
        field_name = c["field"]
        cat = c["category"]
        before = c["value_before"]
        after = c["value_after"]
        delta_pct = c["delta_pct"]
        sign = "+" if delta_pct > 0 else ""
        direction = "Meningkat" if c["direction"] == "increase" else "Menurun"

        lines.append(
            f"{i}. [{cat}] {field_name}: {direction} {sign}{delta_pct}% "
            f"({before} -> {after})"
        )

    return "\n".join(lines)


# ============================================================================
# SELF-TESTS & CLI EXECUTION
# ============================================================================

def _run_self_tests():
    """Unit test verifikasi implementasi PLAN.md line 184-224."""
    print("Menjalankan self-test compute_what_changed...")

    mock_metrics_prev = {
        "company": "BBCA",
        "period": "2025-Q1",
        "valuation_metrics": {
            "pe_relative": 1.0,
            "pbv_relative": 2.0,
            "ev_ebitda": 10.0
        },
        "growth_metrics": {
            "revenue_growth_qoq": 5.0,
            "revenue_growth_yoy": 15.0,
            "forecast_gap": 0.0
        },
        "price_metrics": {
            "volatility": 20.0,
            "price_vs_ma20": 2.0
        },
        "ownership_metrics": {
            "concentration_top5": 50.0
        },
        "dividend_metrics": {
            "dividend_yield": 4.0,
            "dividend_growth": 10.0
        }
    }

    mock_metrics_now = {
        "company": "BBCA",
        "period": "2026-Q1",
        "valuation_metrics": {
            "pe_relative": 1.05,       # +5% (<10%, harus diskip pada default threshold)
            "pbv_relative": 2.5,        # +25% (>=10%, catat)
            "ev_ebitda": 8.0            # -20% (>=10%, catat)
        },
        "growth_metrics": {
            "revenue_growth_qoq": 7.5,  # +50% (>=10%, catat)
            "revenue_growth_yoy": 15.5, # +3.33% (<10%, diskip)
            "forecast_gap": None        # None (diskip)
        },
        "price_metrics": {
            "volatility": 28.0,         # +40% (>=10%, catat)
            "price_vs_ma20": 2.1        # +5% (<10%, diskip)
        },
        "ownership_metrics": {
            "concentration_top5": 50.0  # 0% delta (<10%, diskip)
        },
        "dividend_metrics": {
            "dividend_yield": 4.8,      # +20% (>=10%, catat)
            "dividend_growth": 15.0     # +50% (>=10%, catat)
        }
    }

    res = compute_what_changed(mock_metrics_now, mock_metrics_prev, default_threshold=10.0)
    assert res["status"] == "SUCCESS"
    assert res["company"] == "BBCA"
    assert res["period"] == "2026-Q1"
    assert res["compared_to"] == "2025-Q1"

    # Perubahan terdeteksi:
    # 1. pbv_relative (+25%)
    # 2. ev_ebitda (-20%)
    # 3. revenue_growth_qoq (+50%)
    # 4. volatility (+40%)
    # 5. dividend_yield (+20%)
    # 6. dividend_growth (+50%)
    # Total = 6 perubahan
    assert res["total_changes_detected"] == 6, f"Expected 6 changes, got {res['total_changes_detected']}"

    # Pastikan sorted by magnitude descending
    top_change = res["changes"][0]
    assert abs(top_change["delta_pct"]) == 50.0

    # Cek direction
    ev_change = next(c for c in res["changes"] if c["field"] == "ev_ebitda")
    assert ev_change["direction"] == "decrease"
    assert ev_change["delta"] == -2.0
    assert ev_change["delta_pct"] == -20.0

    # Test custom threshold per field
    custom_thresholds = {"revenue_growth_qoq": 60.0}  # QoQ (+50%) harus lolos jika default, tapi gugur jika threshold 60%
    res_custom = compute_what_changed(mock_metrics_now, mock_metrics_prev, thresholds=custom_thresholds)
    fields_detected = [c["field"] for c in res_custom["changes"]]
    assert "revenue_growth_qoq" not in fields_detected
    assert res_custom["total_changes_detected"] == 5

    print("Semua self-test what_changed BERHASIL lolos tanpa kendala.")


if __name__ == "__main__":
    _run_self_tests()
    print("=" * 60)

    target_ticker = sys.argv[1] if len(sys.argv) > 1 else "BBCA"
    p_now = sys.argv[2] if len(sys.argv) > 2 else "current"
    p_prev = sys.argv[3] if len(sys.argv) > 3 else "5y"

    print(f"Menganalisis 'What Changed' untuk ticker: {target_ticker} ({p_now} vs {p_prev})...")
    analysis = fetch_and_analyze_what_changed(target_ticker, period_now=p_now, period_prev=p_prev)
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    print("-" * 60)
    print(format_what_changed_summary(analysis))
