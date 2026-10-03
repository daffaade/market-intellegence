import logging
from typing import Dict, Any
from .consumer_data import get_consumer_data
from .company_analysis import CompanyAnalyzer
from .industry_impact import IndustryImpactCalculator
from .evidence import EvidenceFormatter

logger = logging.getLogger(__name__)

class ConsumerBehaviorModel:
    def __init__(self, sector_map_path: str = None):
        self.company_analyzer = CompanyAnalyzer(sector_map_path)
        self.impact_calculator = IndustryImpactCalculator()
        self.evidence_formatter = EvidenceFormatter()
        
    def analyze(self, keyword: str, industry: str) -> Dict[str, Any]:
        """
        Main orchestration function for Consumer Behavior analysis.
        """
        logger.info(f"Starting Consumer Behavior Analysis for Keyword: {keyword}, Industry: {industry}")
        
        # 1. Fetch Consumer Data (PyTrends & BPS)
        consumer_data = get_consumer_data(keyword)
        
        # 2. Get Top 3-5 Companies for the industry
        top_companies = self.company_analyzer.get_top_companies(industry, limit=5)
        if not top_companies:
            logger.warning(f"No companies found for industry: {industry}")
            
        # 3. Analyze Companies
        company_metrics = self.company_analyzer.analyze_companies(top_companies)
        
        # 4. Calculate Industry Impact Score
        impact_signal = self.impact_calculator.calculate_impact(consumer_data, company_metrics)
        
        # 5. Format Evidence
        evidence = self.evidence_formatter.format_evidence(keyword, consumer_data, company_metrics)
        
        # 6. Construct Final Result
        result = {
            "keyword": keyword,
            "industry": industry,
            "impact_signal": impact_signal,
            "evidence": evidence,
            "disclaimer": "Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."
        }
        
        return result
