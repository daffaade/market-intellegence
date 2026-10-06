import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class IndustryImpactCalculator:
    @staticmethod
    def calculate_impact(consumer_data: Dict[str, Any], company_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates the quantitative impact score (0-100), direction, and confidence.
        """
        score = 50.0 # Base score neutral
        confidence = "Medium"
        direction = "Neutral"
        
        # 1. Evaluate Search Trends
        search_trend = consumer_data.get("search_trend", {})
        if "error" not in search_trend and "trend_data" in search_trend:
            mean_interest = search_trend.get("mean_interest", 0)
            latest_interest = search_trend.get("latest_interest", 0)
            
            if mean_interest > 0:
                trend_ratio = latest_interest / mean_interest
                if trend_ratio > 1.2:
                    score += 15
                elif trend_ratio > 1.05:
                    score += 5
                elif trend_ratio < 0.8:
                    score -= 15
                elif trend_ratio < 0.95:
                    score -= 5
                    
        # 2. Evaluate Macro Indicators (BPS logic)
        macro = consumer_data.get("macro_indicators", {})
        if "error" not in macro and macro.get("data"):
            # Assume presence of relevant BPS data slightly increases confidence
            confidence = "High"
            # Optional: parse specific BPS values if needed.
            
        # 3. Evaluate Company Growth (from top companies)
        positive_growth_count = 0
        total_companies = len(company_analysis)
        
        if total_companies > 0:
            for ticker, metrics in company_analysis.items():
                if metrics.get("growth_estimate", 0) > 0:
                    positive_growth_count += 1
            
            growth_ratio = positive_growth_count / total_companies
            if growth_ratio >= 0.6:
                score += 10
            elif growth_ratio <= 0.4:
                score -= 10
                
        # Clamp score between 0 and 100
        score = max(0.0, min(100.0, score))
        
        # Determine Direction
        if score >= 65:
            direction = "Positive"
        elif score <= 35:
            direction = "Negative"
        else:
            direction = "Neutral"
            
        return {
            "impact_score": round(score, 2),
            "impact_direction": direction,
            "confidence_level": confidence
        }
