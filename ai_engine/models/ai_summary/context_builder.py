from typing import Dict, Any, List
import logging
from ai_engine.core.data_loader import UnifiedDataLoader

# Import models
from ai_engine.models.forecast.forecast_model import ForecastModel
from ai_engine.models.anomaly.isolation_forest import AnomalyModel
from ai_engine.models.peers.peer_analysis import PeerAnalysisModel
from ai_engine.models.smart_money.smart_money_model import SmartMoneyModel
from ai_engine.models.catalyst.catalyst_detector import CatalystDetector

logger = logging.getLogger(__name__)

def build_context_and_evidence(ticker: str, include_models: List[str], data_loader: UnifiedDataLoader) -> Dict[str, Any]:
    """
    Executes selected models, gathers their results, and extracts numerical facts into an evidence_list.
    Returns a context dictionary.
    """
    analysis_results = {}
    evidence_list = []
    
    # 1. Forecast Model
    if not include_models or "forecast" in include_models:
        try:
            model = ForecastModel(data_loader)
            res = model.analyze(ticker)
            if res.get("status") == "success":
                analysis_results["forecast"] = res
                
                # Extract evidence
                opp = res.get("opportunity_signal", {})
                risk = res.get("risk_signal", {})
                if "score" in opp:
                    evidence_list.append({"source_model": "forecast", "metric": "opportunity_score", "value": opp["score"], "source": "RandomForest"})
                if "score" in risk:
                    evidence_list.append({"source_model": "forecast", "metric": "risk_score", "value": risk["score"], "source": "RandomForest"})
            else:
                analysis_results["forecast"] = {"status": "UNAVAILABLE"}
        except Exception as e:
            logger.warning(f"ForecastModel failed for {ticker}: {e}")
            analysis_results["forecast"] = {"status": "UNAVAILABLE"}

    # 2. Anomaly Model
    if not include_models or "anomaly" in include_models:
        try:
            model = AnomalyModel(data_loader)
            res = model.analyze(ticker)
            analysis_results["anomaly"] = res
            
            # Extract evidence
            if "is_anomaly" in res:
                evidence_list.append({"source_model": "anomaly", "metric": "is_anomaly", "value": res["is_anomaly"], "source": "IsolationForest"})
            if "anomaly_score" in res:
                evidence_list.append({"source_model": "anomaly", "metric": "anomaly_score", "value": res["anomaly_score"], "source": "IsolationForest"})
        except Exception as e:
            logger.warning(f"AnomalyModel failed for {ticker}: {e}")
            analysis_results["anomaly"] = {"status": "UNAVAILABLE"}

    # 3. Divergence / Peers
    if not include_models or "divergence" in include_models:
        try:
            model = PeerAnalysisModel(data_loader)
            res = model.analyze(ticker)
            analysis_results["divergence"] = res
            
            # Extract evidence
            if "divergence_score" in res:
                evidence_list.append({"source_model": "divergence", "metric": "divergence_score", "value": res["divergence_score"], "source": "PeerComparison"})
        except Exception as e:
            logger.warning(f"PeerAnalysisModel failed for {ticker}: {e}")
            analysis_results["divergence"] = {"status": "UNAVAILABLE"}

    # 4. Smart Money
    if not include_models or "smart_money" in include_models:
        try:
            model = SmartMoneyModel(data_loader)
            res = model.analyze(ticker)
            analysis_results["smart_money"] = res
            
            # Extract evidence
            if "smart_money_score" in res:
                evidence_list.append({"source_model": "smart_money", "metric": "smart_money_score", "value": res["smart_money_score"], "source": "VolumeAnalysis"})
        except Exception as e:
            logger.warning(f"SmartMoneyModel failed for {ticker}: {e}")
            analysis_results["smart_money"] = {"status": "UNAVAILABLE"}

    # 5. Catalyst
    if not include_models or "catalyst" in include_models:
        try:
            model = CatalystDetector(data_loader)
            res = model.analyze(ticker)
            analysis_results["catalyst"] = res
            
            # Extract evidence
            if "catalyst_score" in res:
                evidence_list.append({"source_model": "catalyst", "metric": "catalyst_score", "value": res["catalyst_score"], "source": "News/Events"})
        except Exception as e:
            logger.warning(f"CatalystDetector failed for {ticker}: {e}")
            analysis_results["catalyst"] = {"status": "UNAVAILABLE"}

    context = {
        "ticker": ticker,
        "analysis_results": analysis_results,
        "evidence": evidence_list
    }
    
    return context, evidence_list
