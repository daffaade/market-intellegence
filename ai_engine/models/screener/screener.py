from typing import List, Dict, Any, Optional
import time
import concurrent.futures
from pydantic import BaseModel, Field
from ai_engine.core.data_loader import UnifiedDataLoader
from ai_engine.core.derived_metrics import fetch_and_compute_derived_metrics

from ai_engine.models.forecast.forecast_model import ForecastModel
from ai_engine.models.anomaly.isolation_forest import AnomalyModel
from ai_engine.models.peers.peer_analysis import PeerAnalysisModel
from ai_engine.models.smart_money.smart_money_model import SmartMoneyModel
from ai_engine.models.catalyst.catalyst_detector import CatalystDetector

MANDATORY_DISCLAIMER = (
    "Informasi dan hasil screener merupakan hasil pemrosesan data riset dan bukan "
    "merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."
)

PRIMARY_UNIVERSE = ["BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "AMRT", "GOTO", "ANTM", "BUMI"]

DEFAULT_SECTOR_MAP = {
    "FINANCIALS": ["BBCA", "BBRI", "BMRI", "BBNI"],
    "BANKING": ["BBCA", "BBRI", "BMRI", "BBNI"],
    "TELECOMMUNICATION": ["TLKM"],
    "INFRASTRUCTURE": ["TLKM"],
    "CONSUMER": ["AMRT", "ASII"],
    "TECHNOLOGY": ["GOTO"],
    "MINING": ["ANTM", "BUMI"],
    "BASIC MATERIALS": ["ANTM", "BUMI"]
}

# Cache for flattened metrics to make subsequent screener runs instant (<5ms)
_METRICS_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TIMESTAMP: Dict[str, float] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour TTL

class ScreenerRule(BaseModel):
    field: str
    operator: str  # gt, gte, lt, lte, eq, neq, between, in
    value: Any

class ScreenerRequest(BaseModel):
    universe: Optional[List[str]] = None
    tickers: Optional[List[str]] = None
    preset: Optional[str] = None  # e.g., 'undervalued_growth', 'smart_money_inflow', 'low_risk_compounder'
    logic: str = "AND"
    rules: List[ScreenerRule] = Field(default_factory=list)
    sort_by: Optional[str] = "opportunity_score"
    sort_order: str = "desc"
    limit: int = 15

class IntelligenceScreener:
    """
    Intelligent Screener that combines Fundamental data and AI Signals (Forecast, Anomaly, Smart Money, etc)
    and evaluates them concurrently across a defined universe with explainable Key Findings.
    """
    def __init__(self, data_loader: UnifiedDataLoader):
        self.data_loader = data_loader

    def _get_flattened_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Gathers fundamental and AI metrics for a single ticker and flattens them into a dictionary.
        Leverages an in-memory cache to guarantee ultra-fast response times.
        """
        now = time.time()
        clean_sym = symbol.upper().strip()

        # Check Cache
        if clean_sym in _METRICS_CACHE and (now - _CACHE_TIMESTAMP.get(clean_sym, 0)) < CACHE_TTL_SECONDS:
            return _METRICS_CACHE[clean_sym]

        metrics: Dict[str, Any] = {
            "ticker": clean_sym,
            "opportunity_score": 50.0,
            "opportunity_direction": "Neutral",
            "risk_score": 30.0,
            "risk_level": "Low",
            "is_anomaly": False,
            "anomaly_score": 0.0,
            "divergence_score": 0.0,
            "has_divergence": False,
            "smart_money_score": 50.0,
            "smart_money_state": "Neutral",
            "catalyst_score": 0.0,
            "has_catalyst": False,
            "growth_proxy": 0.0,
            "valuation_proxy": 0.0,
            "valuation_position": "Neutral",
            "growth_position": "Neutral",
            "peer_group": []
        }
        
        # 1. Fundamental Metrics (pe_ratio, pbv_ratio, roe, etc)
        try:
            derived = fetch_and_compute_derived_metrics(clean_sym)
            if isinstance(derived, dict):
                for key, value in derived.items():
                    if isinstance(value, dict):
                        metrics.update(value)
                    else:
                        metrics[key] = value
        except Exception:
            pass

        # 2. Basic / Market Metrics
        try:
            unified = self.data_loader.get_unified_dataset(clean_sym)
            if "data" in unified:
                m_data = unified["data"].get("market_data", {})
                v_data = unified["data"].get("valuation_data", {})
                metrics.update(m_data)
                metrics.update(v_data)
                if "trailing_pe" in v_data:
                    metrics["pe_ratio"] = v_data["trailing_pe"]
        except Exception:
            pass

        # 3. Forecast & Signals
        try:
            forecast_model = ForecastModel(self.data_loader)
            f_res = forecast_model.analyze(clean_sym)
            if f_res.get("status") == "success":
                opp = f_res.get("opportunity_signal", {})
                risk = f_res.get("risk_signal", {})
                metrics["opportunity_score"] = float(opp.get("score", 50.0))
                metrics["opportunity_direction"] = opp.get("direction", "Neutral")
                metrics["risk_score"] = float(risk.get("score", 30.0))
                metrics["risk_level"] = risk.get("level", "Low")
        except Exception:
            pass

        # 4. Anomaly Model (Isolation Forest)
        try:
            anomaly_model = AnomalyModel(self.data_loader)
            a_res = anomaly_model.analyze(clean_sym)
            metrics["is_anomaly"] = bool(a_res.get("is_anomaly", False))
            metrics["anomaly_score"] = float(a_res.get("anomaly_score", 0.0))
        except Exception:
            pass

        # 5. Peer Analysis & Fundamental Divergence
        try:
            peer_model = PeerAnalysisModel(self.data_loader)
            p_res = peer_model.analyze(clean_sym)
            div_score = float(p_res.get("divergence_score", 0.0))
            metrics["divergence_score"] = div_score
            metrics["has_divergence"] = div_score >= 0.70
            metrics["peer_group"] = p_res.get("peer_group", [])
            
            rel_pos = p_res.get("relative_positions", {})
            if "valuation_proxy" in rel_pos:
                v_diff = rel_pos["valuation_proxy"].get("diff", 0)
                # Lower valuation relative to peer means Cheaper / Undervalued
                if v_diff < 0:
                    metrics["valuation_position"] = "Cheaper"
                elif v_diff > 0:
                    metrics["valuation_position"] = "More Expensive"
                else:
                    metrics["valuation_position"] = "In Line"
            if "growth_proxy" in rel_pos:
                g_diff = rel_pos["growth_proxy"].get("diff", 0)
                metrics["growth_position"] = "Outperform" if g_diff > 0 else ("Underperform" if g_diff < 0 else "In Line")
        except Exception:
            pass

        # 6. Smart Money Analysis
        try:
            sm_model = SmartMoneyModel(self.data_loader)
            sm_res = sm_model.analyze(clean_sym)
            metrics["smart_money_score"] = float(sm_res.get("smart_money_score", 50.0))
            metrics["smart_money_state"] = sm_res.get("state", "Neutral")
        except Exception:
            pass
            
        # 7. Catalyst Detector
        try:
            cat_model = CatalystDetector(self.data_loader)
            cat_res = cat_model.analyze(clean_sym)
            cat_score = float(cat_res.get("catalyst_score", 0.0))
            metrics["catalyst_score"] = cat_score
            metrics["has_catalyst"] = cat_score >= 60.0
        except Exception:
            pass

        # Store to cache
        _METRICS_CACHE[clean_sym] = metrics
        _CACHE_TIMESTAMP[clean_sym] = now
        return metrics

    def _evaluate_rule(self, field_value: Any, rule: ScreenerRule) -> bool:
        if field_value is None:
            return False
            
        op = rule.operator.lower().strip()
        try:
            # Boolean check
            if isinstance(rule.value, bool):
                if op in ("eq", "==", "="):
                    return bool(field_value) is rule.value
                elif op in ("neq", "!="):
                    return bool(field_value) is not rule.value

            # Numeric comparison
            if op in ("gt", ">"):
                return float(field_value) > float(rule.value)
            elif op in ("gte", ">="):
                return float(field_value) >= float(rule.value)
            elif op in ("lt", "<"):
                return float(field_value) < float(rule.value)
            elif op in ("lte", "<="):
                return float(field_value) <= float(rule.value)
            elif op in ("eq", "==", "="):
                return str(field_value).strip().lower() == str(rule.value).strip().lower()
            elif op in ("neq", "!="):
                return str(field_value).strip().lower() != str(rule.value).strip().lower()
            elif op == "between":
                return float(rule.value[0]) <= float(field_value) <= float(rule.value[1])
            elif op == "in":
                if isinstance(rule.value, list):
                    clean_list = [str(x).strip().lower() for x in rule.value]
                    return str(field_value).strip().lower() in clean_list
                return str(field_value) in str(rule.value)
        except (ValueError, TypeError):
            return False
        return False

    def _synthesize_key_findings(self, metrics: Dict[str, Any], passed_rules: List[str]) -> List[str]:
        """
        Generates explainable human-readable key findings (Why this stock matched).
        """
        findings = []
        opp = metrics.get("opportunity_score", 0)
        risk = metrics.get("risk_score", 0)
        direction = metrics.get("opportunity_direction", "Neutral")
        
        # Opportunity Finding
        if opp >= 65:
            findings.append(f"Skor Peluang menonjol di level {opp:.1f}/100 ({direction}).")
        
        # Relative Valuation & Growth Finding
        val_pos = metrics.get("valuation_position")
        gro_pos = metrics.get("growth_position")
        if val_pos == "Cheaper" and gro_pos == "Outperform":
            findings.append("Kombinasi Prima: Valuasi lebih murah dan Pertumbuhan mengungguli median industri.")
        elif val_pos == "Cheaper":
            findings.append("Valuasi relatif atraktif (lebih murah dari median peer industri).")
        elif gro_pos == "Outperform":
            findings.append("Pertumbuhan relatif unggul dibandingkan median peer industri.")

        # Smart Money Finding
        sm_state = metrics.get("smart_money_state")
        if sm_state == "Accumulation":
            findings.append("Aktivitas investor institusional terdeteksi dalam fase Akumulasi.")
        elif sm_state == "Distribution":
            findings.append("Waspada: Aktivitas institusional terdeteksi dalam tekanan Distribusi.")

        # Divergence Finding
        if metrics.get("has_divergence"):
            findings.append(f"Divergensi fundamental positif terkonfirmasi (Score: {metrics.get('divergence_score', 0):.2f}).")

        # Anomaly Finding
        if metrics.get("is_anomaly"):
            findings.append(f"Peringatan Anomali: Terdeteksi pola transaksi/harga tidak biasa (Score: {metrics.get('anomaly_score', 0):.1f}).")

        # Risk Finding
        if risk <= 35:
            findings.append("Profil risiko tergolong Rendah/Terkendali.")
        elif risk >= 65:
            findings.append(f"Tingkat risiko terdeteksi Tinggi ({risk:.1f}/100), pantau batas volatilitas.")

        if not findings:
            findings.append("Memenuhi kriteria filter yang ditentukan pengguna.")

        return findings

    def _apply_preset_rules(self, preset_name: str, existing_rules: List[ScreenerRule]) -> List[ScreenerRule]:
        """
        Appends preset smart rules to existing rules.
        """
        preset_clean = preset_name.lower().strip()
        new_rules = list(existing_rules)
        
        if preset_clean == "undervalued_growth":
            new_rules.append(ScreenerRule(field="opportunity_score", operator="gte", value=60))
            new_rules.append(ScreenerRule(field="valuation_position", operator="eq", value="Cheaper"))
        elif preset_clean == "smart_money_inflow":
            new_rules.append(ScreenerRule(field="smart_money_state", operator="eq", value="Accumulation"))
            new_rules.append(ScreenerRule(field="opportunity_score", operator="gte", value=55))
        elif preset_clean == "low_risk_compounder":
            new_rules.append(ScreenerRule(field="risk_score", operator="lte", value=40))
            new_rules.append(ScreenerRule(field="opportunity_score", operator="gte", value=55))
            new_rules.append(ScreenerRule(field="is_anomaly", operator="eq", value=False))
        elif preset_clean == "catalyst_breakout":
            new_rules.append(ScreenerRule(field="catalyst_score", operator="gte", value=60))
            new_rules.append(ScreenerRule(field="opportunity_score", operator="gte", value=60))
        elif preset_clean == "fundamental_divergence":
            new_rules.append(ScreenerRule(field="divergence_score", operator="gte", value=0.70))

        return new_rules

    def _resolve_universe(self, request: ScreenerRequest) -> List[str]:
        """
        Resolves target tickers from universe, sector names, or explicit tickers list.
        Defaults to PRIMARY_UNIVERSE if none provided.
        """
        raw_list = request.universe if request.universe is not None else (request.tickers or [])
        if not raw_list:
            return PRIMARY_UNIVERSE

        resolved = []
        for item in raw_list:
            clean_item = item.strip().upper()
            if clean_item in DEFAULT_SECTOR_MAP:
                resolved.extend(DEFAULT_SECTOR_MAP[clean_item])
            else:
                resolved.append(clean_item)

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for sym in resolved:
            if sym not in seen:
                seen.add(sym)
                deduped.append(sym)
        return deduped if deduped else PRIMARY_UNIVERSE

    def screen(self, request: ScreenerRequest) -> Dict[str, Any]:
        target_universe = self._resolve_universe(request)
        
        # Apply Preset if specified
        active_rules = request.rules
        if request.preset:
            active_rules = self._apply_preset_rules(request.preset, request.rules)

        results = []
        
        # Parallel Execution to scan universe efficiently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {executor.submit(self._get_flattened_metrics, sym): sym for sym in target_universe}
            
            for future in concurrent.futures.as_completed(future_to_symbol):
                sym = future_to_symbol[future]
                try:
                    metrics = future.result()
                    
                    passed_rules = []
                    failed_rules = []
                    missing_data = []
                    
                    for rule in active_rules:
                        val = metrics.get(rule.field)
                        if val is None:
                            missing_data.append(rule.field)
                            continue
                            
                        is_pass = self._evaluate_rule(val, rule)
                        if is_pass:
                            passed_rules.append(rule.field)
                        else:
                            failed_rules.append(rule.field)
                    
                    total_rules = len(active_rules)
                    if total_rules > 0:
                        match_pct = round((len(passed_rules) / total_rules) * 100.0, 1)
                    else:
                        match_pct = 100.0  # If no rules specified, all match

                    if len(missing_data) > 0 and request.logic.upper() == "AND" and total_rules > 0:
                        status = "INSUFFICIENT_DATA"
                    else:
                        if total_rules == 0:
                            status = "MATCH"
                        elif request.logic.upper() == "AND":
                            status = "MATCH" if len(failed_rules) == 0 else "NO_MATCH"
                        else:  # OR
                            status = "MATCH" if len(passed_rules) > 0 else "NO_MATCH"

                    key_findings = self._synthesize_key_findings(metrics, passed_rules)
                    
                    # Extract evidence items for transparency
                    evidence = [
                        {"metric": "opportunity_score", "value": metrics.get("opportunity_score"), "direction": metrics.get("opportunity_direction")},
                        {"metric": "risk_score", "value": metrics.get("risk_score"), "level": metrics.get("risk_level")},
                        {"metric": "valuation_position", "value": metrics.get("valuation_position")},
                        {"metric": "growth_position", "value": metrics.get("growth_position")},
                        {"metric": "smart_money_state", "value": metrics.get("smart_money_state")},
                        {"metric": "is_anomaly", "value": metrics.get("is_anomaly")}
                    ]

                    results.append({
                        "ticker": sym,
                        "status": status,
                        "match_score": match_pct,
                        "opportunity_score": metrics.get("opportunity_score", 50.0),
                        "risk_score": metrics.get("risk_score", 30.0),
                        "direction": metrics.get("opportunity_direction", "Neutral"),
                        "risk_level": metrics.get("risk_level", "Low"),
                        "key_findings": key_findings,
                        "evidence": evidence,
                        "metrics": {r.field: metrics.get(r.field) for r in active_rules} if status == "MATCH" else {},
                        "matched_rules": passed_rules,
                        "failed_rules": failed_rules,
                        "missing_data": missing_data
                    })
                    
                except Exception as exc:
                    results.append({
                        "ticker": sym,
                        "status": "ERROR",
                        "error": str(exc)
                    })
                    
        matched = [r for r in results if r["status"] == "MATCH"]
        
        # Sorting
        sort_key = request.sort_by or "opportunity_score"
        matched.sort(
            key=lambda x: float(x.get(sort_key, 0) or x.get("metrics", {}).get(sort_key, 0) or 0), 
            reverse=(request.sort_order.lower() == "desc")
        )
            
        # Limiting & Assign Rank
        matched = matched[:request.limit]
        for idx, item in enumerate(matched, 1):
            item["rank"] = idx
        
        return {
            "feature": "intelligence_screener",
            "status": "SUCCESS",
            "summary": {
                "total_scanned": len(target_universe),
                "total_matched": len(matched),
                "total_no_match": len([r for r in results if r["status"] == "NO_MATCH"]),
                "total_insufficient_data": len([r for r in results if r["status"] == "INSUFFICIENT_DATA"]),
                "preset_applied": request.preset
            },
            "disclaimer": MANDATORY_DISCLAIMER,
            "results": matched
        }
