from __future__ import annotations
import math
import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

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

try:
    from unified_data.endpoint_finaldata import get_api_data
    HAS_UNIFIED_DATA = True
except ImportError:
    HAS_UNIFIED_DATA = False


# ============================================================================
# PEER COMPARISON LOGIC
# Sesuai spesifikasi model-intellegence/PLAN.md (line 225-308)
# ============================================================================

DEFAULT_COMPARED_FIELDS = [
    ("valuation_metrics", "pe_relative", "lower_is_better"),
    ("growth_metrics", "revenue_growth_yoy", "higher_is_better"),
    ("ownership_metrics", "net_institutional_flow_pct", "higher_is_better")
]

DEFAULT_PEERS_MAP = {
    # Perbankan
    "BBCA": ["BMRI", "BBRI", "BBNI"],
    "BMRI": ["BBCA", "BBRI", "BBNI"],
    "BBRI": ["BBCA", "BMRI", "BBNI"],
    "BBNI": ["BBCA", "BMRI", "BBRI"],
    # Telekomunikasi
    "TLKM": ["ISAT", "EXCL"],
    "ISAT": ["TLKM", "EXCL"],
    "EXCL": ["TLKM", "ISAT"],
    # Tambang & Batubara
    "BUMI": ["ADRO", "PTBA", "ITMG"],
    "ADRO": ["PTBA", "ITMG", "BUMI"],
    "PTBA": ["ADRO", "ITMG", "BUMI"],
    # Konsumsi & Retail
    "ICBP": ["INDF", "MYOR", "UNVR"],
    "INDF": ["ICBP", "MYOR"],
    "UNVR": ["ICBP", "MYOR", "KLBF"],
    "ASII": ["AUTO", "IMAS"]
}


def normalize_to_100(avg_rank: float, total_companies: int) -> float:
    """
    Menormalisasi rata-rata rank terbalik ke skala 0 - 100.
    Rank 1 (terbaik) -> 100.0
    Rank N (terburuk) -> 0.0
    """
    if total_companies <= 1:
        return 100.0
    score = ((total_companies - avg_rank) / (total_companies - 1)) * 100.0
    return round(max(0.0, min(100.0, score)), 2)


def generate_analysis_text(
    company: str,
    company_metrics: Dict[str, Any],
    overall_score: float,
    total_companies_in_group: int
) -> str:
    """
    Menghasilkan teks naratif evaluasi keunggulan & kelemahan emiten dalam peer group.
    Sesuai PLAN.md line 288-308.
    """
    strengths: List[str] = []
    weaknesses: List[str] = []

    for field, data in company_metrics.items():
        rank = data.get("rank")
        if rank == 1:
            strengths.append(f"{field} tertinggi/terbaik di grup")
        elif total_companies_in_group > 1 and rank == total_companies_in_group:
            weaknesses.append(f"{field} terendah di grup")

    text = f"{company} mendapat overall score {overall_score}."

    if len(strengths) > 0:
        text += " Unggul di: " + ", ".join(strengths) + "."
    if len(weaknesses) > 0:
        text += " Tertinggal di: " + ", ".join(weaknesses) + "."

    return text


def compute_peer_ranking(
    metrics_target: Dict[str, Any],
    metrics_peers_list: List[Dict[str, Any]],
    weights: Optional[Dict[str, float]] = None,
    compared_fields: Optional[List[Tuple[str, str, str]]] = None
) -> Dict[str, Any]:
    """
    Menghitung komparasi peringkat peer group (Ranking & Benchmark vs Peer Avg).
    Sesuai PLAN.md lines 229-285.
    
    Argumen:
      - metrics_target: Derived metrics untuk emiten target.
      - metrics_peers_list: List derived metrics untuk emiten-emiten peer.
      - weights: Bobot opsional per metrik {'field': weight}.
      - compared_fields: List tuple (category, field, direction).
                         direction: 'lower_is_better' atau 'higher_is_better'.
    """
    all_companies = [metrics_target] + list(metrics_peers_list)
    fields_to_compare = compared_fields or DEFAULT_COMPARED_FIELDS

    # 1. Hitung rank & vs_peer_avg per metrik, untuk SEMUA company (bukan cuma target)
    per_metric_results: Dict[str, Dict[str, Any]] = {}

    for category, field, direction in fields_to_compare:
        values: List[Tuple[str, float]] = []
        for m in all_companies:
            comp_name = _get(m, "company") or _get(m, "symbol") or _get(m, "ticker")
            val = _get(m, f"{category}.{field}")
            if val is not None:
                try:
                    values.append((comp_name, float(val)))
                except (ValueError, TypeError):
                    continue

        if not values:
            continue

        avg_value = sum(v for (_, v) in values) / len(values)
        descending = (direction == "higher_is_better")
        sorted_values = sorted(values, key=lambda x: x[1], reverse=descending)

        per_metric_results[field] = {}
        for i, (comp_name, val) in enumerate(sorted_values):
            if abs(avg_value) > 1e-9:
                vs_avg = safe_divide(val - avg_value, abs(avg_value))
                vs_avg_pct = round(vs_avg * 100.0, 2) if vs_avg is not None else 0.0
            else:
                vs_avg_pct = 0.0

            per_metric_results[field][comp_name] = {
                "value": round(val, 4),
                "rank": i + 1,
                "vs_peer_avg_pct": vs_avg_pct
            }

    # 2. Hitung overall_score per company (rata-rata rank terbalik, dinormalisasi 0-100)
    overall_scores: Dict[str, float] = {}
    total_companies_count = len(all_companies)

    for m in all_companies:
        comp_name = _get(m, "company") or _get(m, "symbol") or _get(m, "ticker")
        ranks: List[float] = []
        applied_weights: List[float] = []

        for field in per_metric_results:
            if comp_name in per_metric_results[field]:
                r = float(per_metric_results[field][comp_name]["rank"])
                w = float(weights.get(field, 1.0)) if weights and field in weights else 1.0
                ranks.append(r * w)
                applied_weights.append(w)
            else:
                # Jika data metrik tidak tersedia pada company ini, beri penalti rank terbawah
                r = float(total_companies_count)
                w = float(weights.get(field, 1.0)) if weights and field in weights else 1.0
                ranks.append(r * w)
                applied_weights.append(w)

        if ranks and sum(applied_weights) > 0:
            avg_rank = sum(ranks) / sum(applied_weights)
        else:
            avg_rank = float(total_companies_count)

        overall_scores[comp_name] = normalize_to_100(avg_rank, total_companies=total_companies_count)

    # 3. Susun ranking list + generate analysis text
    target_name = _get(metrics_target, "company") or _get(metrics_target, "symbol") or _get(metrics_target, "ticker")
    ranking_list: List[Dict[str, Any]] = []

    for m in all_companies:
        comp_name = _get(m, "company") or _get(m, "symbol") or _get(m, "ticker")
        company_metrics = {
            field: per_metric_results[field][comp_name]
            for field in per_metric_results
            if comp_name in per_metric_results[field]
        }
        score = overall_scores[comp_name]
        analysis_text = generate_analysis_text(
            comp_name,
            company_metrics,
            score,
            total_companies_in_group=total_companies_count
        )

        ranking_list.append({
            "company": comp_name,
            "is_target": (comp_name == target_name),
            "overall_score": score,
            "metrics": company_metrics,
            "analysis": analysis_text
        })

    # 4. Urutkan berdasarkan overall_score descending
    ranking_list.sort(key=lambda x: x["overall_score"], reverse=True)
    for i, entry in enumerate(ranking_list):
        entry["rank"] = i + 1

    return {
        "period": metrics_target.get("period", "current"),
        "peer_group_size": total_companies_count,
        "metrics_compared": list(per_metric_results.keys()),
        "ranking": ranking_list
    }


# ============================================================================
# UNIFIED DATA PIPELINE INTEGRATION (Follow RULES IN LINE 5)
# ============================================================================

def fetch_and_compute_peer_ranking(
    target_ticker: str,
    peer_tickers: Optional[List[str]] = None,
    period: str = "current",
    weights: Optional[Dict[str, float]] = None,
    compared_fields: Optional[List[Tuple[str, str, str]]] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Mengambil data derived metrics target dan peers dari Unified Data Layer,
    kemudian menghitung pemeringkatan peer group komprehensif.
    """
    if not HAS_DERIVED_METRICS:
        return {
            "status": "ERROR",
            "error": "Modul derived_metrics tidak tersedia."
        }

    clean_target = target_ticker.upper().replace(".JK", "").strip()

    # Tentukan peers jika tidak diberikan
    peers_to_fetch = peer_tickers
    if not peers_to_fetch:
        peers_to_fetch = DEFAULT_PEERS_MAP.get(clean_target, [])

    if not peers_to_fetch:
        # Fallback query peers data dari Unified Data jika ticker tidak ada di default map
        if HAS_UNIFIED_DATA:
            try:
                p_res = get_api_data(clean_target, data_type="peers", period=period, force_refresh=force_refresh)
                if p_res.get("status") == "SUCCESS":
                    peers_info = p_res.get("data", {})
                    # Cek list peers jika disediakan
                    if isinstance(peers_info, dict) and "peer_list" in peers_info:
                        peers_to_fetch = peers_info["peer_list"]
            except Exception:
                pass

    if not peers_to_fetch:
        return {
            "status": "ERROR",
            "error": f"Daftar peer ticker untuk {clean_target} tidak ditemukan. Silakan cantumkan parameter peer_tickers."
        }

    # Fetch derived metrics target
    target_metrics = fetch_and_compute_derived_metrics(clean_target, period=period, force_refresh=force_refresh)
    if target_metrics.get("status") != "SUCCESS":
        return {
            "status": "ERROR",
            "error": f"Gagal mengambil derived metrics untuk target {clean_target}."
        }

    # Fetch derived metrics untuk setiap peer
    peers_metrics_list = []
    for peer in peers_to_fetch:
        peer_clean = peer.upper().replace(".JK", "").strip()
        if peer_clean == clean_target:
            continue
        try:
            p_metric = fetch_and_compute_derived_metrics(peer_clean, period=period, force_refresh=force_refresh)
            if p_metric.get("status") == "SUCCESS":
                peers_metrics_list.append(p_metric)
        except Exception:
            continue

    if not peers_metrics_list:
        return {
            "status": "ERROR",
            "error": f"Tidak ada data peer yang berhasil diambil untuk kelompok {peers_to_fetch}."
        }

    # Hitung ranking komparasi
    result = compute_peer_ranking(
        metrics_target=target_metrics,
        metrics_peers_list=peers_metrics_list,
        weights=weights,
        compared_fields=compared_fields
    )

    return {
        "status": "SUCCESS",
        "target_company": clean_target,
        **result
    }


def format_peer_ranking_summary(ranking_result: Dict[str, Any]) -> str:
    """
    Format hasil evaluasi ranking peer group ke tabel & teks naratif ringkas.
    """
    if ranking_result.get("status") != "SUCCESS" and "ranking" not in ranking_result:
        return f"Error: {ranking_result.get('error', 'Evaluasi ranking gagal.')}"

    target = ranking_result.get("target_company", "Target")
    period = ranking_result.get("period", "current")
    size = ranking_result.get("peer_group_size", 0)
    compared = ranking_result.get("metrics_compared", [])
    ranking = ranking_result.get("ranking", [])

    lines = [
        f"=== PEER COMPARISON RANKING ({target} | Periode: {period}) ===",
        f"Jumlah Emiten dalam Grup: {size}",
        f"Metrik yang Dibandingkan: {', '.join(compared)}\n",
        f"{'Rank':<5} {'Company':<10} {'Score':<8} {'Is Target':<10} {'Analisis Ringkas'}",
        "-" * 85
    ]

    for item in ranking:
        r = item["rank"]
        c = item["company"]
        s = item["overall_score"]
        is_t = "YES" if item.get("is_target") else "NO"
        analysis = item.get("analysis", "")
        lines.append(f"{r:<5} {c:<10} {s:<8.1f} {is_t:<10} {analysis}")

    return "\n".join(lines)


# ============================================================================
# SELF-TESTS & CLI EXECUTION
# ============================================================================

def _run_self_tests():
    """Unit test verifikasi implementasi PLAN.md line 225-308."""
    print("Menjalankan self-test compute_peer_ranking...")

    # Mock Data Target
    target = {
        "company": "BBCA",
        "period": "2026-Q1",
        "valuation_metrics": {"pe_relative": 1.05},
        "growth_metrics": {"revenue_growth_yoy": 25.0},
        "ownership_metrics": {"net_institutional_flow_pct": 2.5}
    }

    # Mock Data Peers
    peer1 = {
        "company": "BMRI",
        "period": "2026-Q1",
        "valuation_metrics": {"pe_relative": 0.95},  # P/E paling rendah -> Rank 1
        "growth_metrics": {"revenue_growth_yoy": 20.0},
        "ownership_metrics": {"net_institutional_flow_pct": 3.0}  # Net flow paling tinggi -> Rank 1
    }

    peer2 = {
        "company": "BBRI",
        "period": "2026-Q1",
        "valuation_metrics": {"pe_relative": 1.20},  # P/E paling tinggi -> Rank 3
        "growth_metrics": {"revenue_growth_yoy": 30.0},  # YoY paling tinggi -> Rank 1
        "ownership_metrics": {"net_institutional_flow_pct": 1.0}  # Net flow paling rendah -> Rank 3
    }

    res = compute_peer_ranking(target, [peer1, peer2])
    assert res["peer_group_size"] == 3
    assert len(res["ranking"]) == 3
    assert "pe_relative" in res["metrics_compared"]
    assert "revenue_growth_yoy" in res["metrics_compared"]

    # Cek bahwa ranking terurut descending overall_score
    scores = [r["overall_score"] for r in res["ranking"]]
    assert scores == sorted(scores, reverse=True)

    # Cek bahwa rank 1 memiliki overall_score tertinggi
    assert res["ranking"][0]["rank"] == 1
    assert res["ranking"][1]["rank"] == 2
    assert res["ranking"][2]["rank"] == 3

    # Cek analisis text
    for r in res["ranking"]:
        assert "mendapat overall score" in r["analysis"]

    print("Semua self-test compute_peer_ranking BERHASIL lolos tanpa kendala.")


if __name__ == "__main__":
    _run_self_tests()
    print("=" * 60)

    target_sym = sys.argv[1] if len(sys.argv) > 1 else "BBCA"
    p = sys.argv[2] if len(sys.argv) > 2 else "current"

    print(f"Menjalankan Peer Comparison untuk target {target_sym} (period: {p})...")
    res = fetch_and_compute_peer_ranking(target_sym, period=p)
    print(format_peer_ranking_summary(res))
    print("-" * 60)
    print(json.dumps(res, indent=2, ensure_ascii=False))
