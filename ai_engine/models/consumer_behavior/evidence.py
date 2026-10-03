from typing import Dict, Any, List

class EvidenceFormatter:
    @staticmethod
    def format_evidence(keyword: str, consumer_data: Dict[str, Any], company_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats all data points into the structured evidence list required by the AI Summary.
        """
        evidence = []
        
        # Add Search Trend Evidence
        search_trend = consumer_data.get("search_trend", {})
        if "error" not in search_trend:
            evidence.append({
                "source": "PyTrends",
                "metric": "Search Interest",
                "value": f"Latest: {search_trend.get('latest_interest', 0):.2f}, Mean: {search_trend.get('mean_interest', 0):.2f}",
                "description": f"Google search trend for '{keyword}' is {search_trend.get('trend_direction', 'UNKNOWN')}."
            })
            
        # Add Macro Evidence
        macro = consumer_data.get("macro_indicators", {})
        if "error" not in macro and macro.get("data"):
            evidence.append({
                "source": "BPS Web API",
                "metric": "Macro Indicator",
                "value": f"Subject ID: {macro.get('subject')}",
                "description": f"Found correlated macro data from BPS for keyword '{keyword}'."
            })
            
        # Add Company Evidence
        if company_analysis:
            tickers = list(company_analysis.keys())
            evidence.append({
                "source": "Market Data",
                "metric": "Top Companies Impacted",
                "value": ", ".join(tickers),
                "description": f"Analyzed {len(tickers)} market cap leaders in the relevant industry."
            })
            
        return evidence
