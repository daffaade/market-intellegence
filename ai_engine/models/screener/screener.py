from typing import List, Dict, Any, Optional
import concurrent.futures
from pydantic import BaseModel
from ai_engine.core.data_loader import UnifiedDataLoader
from ai_engine.core.derived_metrics import fetch_and_compute_derived_metrics

from ai_engine.models.forecast.forecast_model import ForecastModel
from ai_engine.models.anomaly.isolation_forest import AnomalyModel
from ai_engine.models.peers.peer_analysis import PeerAnalysisModel
from ai_engine.models.smart_money.smart_money_model import SmartMoneyModel
from ai_engine.models.catalyst.catalyst_detector import CatalystDetector

class ScreenerRule(BaseModel):
    field: str
    operator: str  # gt, gte, lt, lte, eq, neq, between, in
    value: Any

class ScreenerRequest(BaseModel):
    universe: List[str]
    logic: str = "AND"
    rules: List[ScreenerRule]
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    limit: int = 10

class IntelligenceScreener:
    """
    Intelligent Screener that combines Fundamental data and AI Signals (Forecast, Anomaly, Smart Money, etc)
    and evaluates them concurrently across a defined universe.
    """
    def __init__(self, data_loader: UnifiedDataLoader):
        self.data_loader = data_loader

    def _get_flattened_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Gathers fundamental and AI metrics for a single ticker and flattens them into a dictionary.
        """
        metrics = {}
        
        # 1. Fundamental Metrics (pe_ratio, pbv_ratio, etc)
        derived = fetch_and_compute_derived_metrics(symbol)
        for key, value in derived.items():
            if isinstance(value, dict):
                metrics.update(value)
            else:
                metrics[key] = value

        # 2. Basic / Market Metrics
        unified = self.data_loader.get_unified_dataset(symbol)
        if "data" in unified:
            m_data = unified["data"].get("market_data", {})
            v_data = unified["data"].get("valuation_data", {})
            metrics.update(m_data)
            metrics.update(v_data)
            # Add alias for standard pe_ratio compatibility if trailing_pe exists
            if "trailing_pe" in v_data:
                metrics["pe_ratio"] = v_data["trailing_pe"]

        # 3. AI Signals
        # Opportunity & Risk
        try:
            forecast_model = ForecastModel(self.data_loader)
            f_res = forecast_model.analyze(symbol)
            if f_res.get("status") == "success":
                metrics["opportunity_score"] = f_res.get("opportunity_signal", {}).get("score", 0)
                metrics["risk_score"] = f_res.get("risk_signal", {}).get("score", 0)
        except Exception:
            pass

        # Anomaly
        try:
            anomaly_model = AnomalyModel(self.data_loader)
            a_res = anomaly_model.analyze(symbol)
            metrics["is_anomaly"] = a_res.get("is_anomaly", False)
            metrics["anomaly_score"] = a_res.get("anomaly_score", 0.0)
        except Exception:
            pass

        # Fundamental Divergence
        try:
            peer_model = PeerAnalysisModel(self.data_loader)
            p_res = peer_model.analyze(symbol)
            metrics["divergence_score"] = p_res.get("divergence_score", 0.0)
        except Exception:
            pass

        # Smart Money
        try:
            sm_model = SmartMoneyModel(self.data_loader)
            sm_res = sm_model.analyze(symbol)
            metrics["smart_money_score"] = sm_res.get("score") if sm_res.get("score") is not None else sm_res.get("smart_money_score", 0.0)
            metrics["smart_money_state"] = sm_res.get("state", "Neutral")
        except Exception:
            pass
            
        # Catalyst
        try:
            cat_model = CatalystDetector(self.data_loader)
            cat_res = cat_model.analyze(symbol)
            metrics["catalyst_score"] = cat_res.get("catalyst_score", 0.0)
        except Exception:
            pass

        return metrics

    def _evaluate_rule(self, field_value: Any, rule: ScreenerRule) -> bool:
        if field_value is None:
            return False
            
        op = rule.operator.lower()
        try:
            if op == "gt":
                return float(field_value) > float(rule.value)
            elif op == "gte":
                return float(field_value) >= float(rule.value)
            elif op == "lt":
                return float(field_value) < float(rule.value)
            elif op == "lte":
                return float(field_value) <= float(rule.value)
            elif op == "eq":
                return field_value == rule.value
            elif op == "neq":
                return field_value != rule.value
            elif op == "between":
                return float(rule.value[0]) <= float(field_value) <= float(rule.value[1])
            elif op == "in":
                return field_value in rule.value
        except (ValueError, TypeError):
            return False
        return False

    def screen(self, request: ScreenerRequest) -> Dict[str, Any]:
        results = []
        
        # Parallel Execution to scan universe efficiently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {executor.submit(self._get_flattened_metrics, sym): sym for sym in request.universe}
            
            for future in concurrent.futures.as_completed(future_to_symbol):
                sym = future_to_symbol[future]
                try:
                    metrics = future.result()
                    
                    passed_rules = []
                    failed_rules = []
                    missing_data = []
                    
                    for rule in request.rules:
                        val = metrics.get(rule.field)
                        if val is None:
                            missing_data.append(rule.field)
                            continue
                            
                        is_pass = self._evaluate_rule(val, rule)
                        if is_pass:
                            passed_rules.append(rule.field)
                        else:
                            failed_rules.append(rule.field)
                    
                    if len(missing_data) > 0 and request.logic.upper() == "AND":
                        status = "INSUFFICIENT_DATA"
                    else:
                        if request.logic.upper() == "AND":
                            status = "MATCH" if len(failed_rules) == 0 else "NO_MATCH"
                        else: # OR
                            status = "MATCH" if len(passed_rules) > 0 else "NO_MATCH"
                            
                    results.append({
                        "ticker": sym,
                        "status": status,
                        "metrics": {r.field: metrics.get(r.field) for r in request.rules} if status == "MATCH" else {},
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
        if request.sort_by:
            matched.sort(
                key=lambda x: float(x["metrics"].get(request.sort_by, 0) or 0), 
                reverse=(request.sort_order.lower() == "desc")
            )
            
        # Limiting
        matched = matched[:request.limit]
        
        return {
            "status": "SUCCESS",
            "summary": {
                "total_scanned": len(request.universe),
                "total_matched": len(matched),
                "total_no_match": len([r for r in results if r["status"] == "NO_MATCH"]),
                "total_insufficient_data": len([r for r in results if r["status"] == "INSUFFICIENT_DATA"])
            },
            "results": matched
        }
