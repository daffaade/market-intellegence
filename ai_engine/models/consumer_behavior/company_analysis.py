import yaml
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CompanyAnalyzer:
    def __init__(self, sector_map_path: str = None):
        if not sector_map_path:
            # Default path relative to ai_engine execution
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.sector_map_path = os.path.join(base_dir, "config", "sector_map.yaml")
        else:
            self.sector_map_path = sector_map_path
            
    def _load_sector_map(self) -> Dict[str, Any]:
        try:
            if not os.path.exists(self.sector_map_path):
                logger.warning(f"Sector map not found at {self.sector_map_path}")
                return {}
            with open(self.sector_map_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load sector_map.yaml: {e}")
            return {}
            
    def get_top_companies(self, industry: str, limit: int = 5) -> List[str]:
        """
        Retrieves top market cap leaders for a given industry from sector_map.yaml.
        """
        sector_map = self._load_sector_map()
        
        # Map common indonesian industry names to yaml keys
        ind_lower = industry.lower()
        target_sector = ""
        if "makanan" in ind_lower or "minuman" in ind_lower or "consumer" in ind_lower or "ritel" in ind_lower:
            target_sector = "ConsumerNonCyclical"
        elif "bank" in ind_lower or "keuangan" in ind_lower or "financial" in ind_lower:
            target_sector = "Financials"
        elif "teknologi" in ind_lower or "tech" in ind_lower:
            target_sector = "Technology"
        elif "infrastruktur" in ind_lower or "telekomunikasi" in ind_lower:
            target_sector = "Infrastructure"
        elif "tambang" in ind_lower or "energi" in ind_lower or "batu" in ind_lower:
            target_sector = "Energy"
            
        companies = []
        if sector_map and "universe" in sector_map:
            universe = sector_map["universe"]
            # Exact match if possible, otherwise mapped match
            if target_sector in universe:
                companies.extend(universe[target_sector])
            else:
                # search for direct key
                for k, v in universe.items():
                    if k.lower() == ind_lower:
                        companies.extend(v)
                        
        if not companies:
            # Fallback mock for primary universe
            fallback = {
                "ConsumerNonCyclical": ["ICBP", "INDF", "AMRT", "UNVR", "MYOR"],
                "Financials": ["BBCA", "BBRI", "BMRI", "BBNI"]
            }
            companies = fallback.get(target_sector, [])
            
        return companies[:limit]

    def analyze_companies(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Gathers basic fundamentals/forecasts for the selected top companies.
        Integrates with UnifiedData conceptually. Here we provide a structured mock
        to adhere to the rule of separating logic from data pipeline testing.
        """
        analysis_result = {}
        for ticker in tickers:
            # In a real scenario, this would call UnifiedDataLoader.get_company_info(ticker)
            # We mock the structure to satisfy the model algorithms
            analysis_result[ticker] = {
                "growth_estimate": 0.05 if ticker in ["AMRT", "ICBP", "TLKM"] else -0.02, 
                "pe_ratio": 15.0 if ticker != "GOTO" else -5.0,
                "recent_momentum": "Positive" if ticker in ["AMRT", "ASII"] else "Neutral"
            }
        return analysis_result
