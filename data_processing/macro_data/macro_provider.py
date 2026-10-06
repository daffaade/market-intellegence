from typing import Dict, Any
from data_processing.macro_data.get_trends import PyTrendsFetcher
from data_processing.macro_data.get_bps import BPSFetcher

class MacroDataProvider:
    def __init__(self):
        self.pytrends_fetcher = PyTrendsFetcher()
        self.bps_fetcher = BPSFetcher()
        
    def get_consumer_data(self, keyword: str, timeframe: str = 'today 12-m') -> Dict[str, Any]:
        """
        Fetches macro economic indicators and search trends for a given keyword/industry.
        """
        trend_data = self.pytrends_fetcher.fetch_trend(keyword, timeframe)
        bps_data = self.bps_fetcher.fetch_data(keyword)
        
        return {
            "keyword": keyword,
            "search_trend": trend_data,
            "macro_indicators": bps_data
        }
