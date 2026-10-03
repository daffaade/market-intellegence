import numpy as np
import pandas as pd
from typing import Dict, Any, List

TRADING_DAYS_PER_YEAR = 252

class PortfolioRisk:
    def __init__(self, data_fetcher=None):
        """
        Initialize the Portfolio Risk model.
        :param data_fetcher: A callable that accepts (ticker, period) and returns a pandas Series of closing prices.
                             This acts as a dependency injection for the UnifiedData loader.
        """
        self.data_fetcher = data_fetcher
        
    def calculate_risk(
        self, 
        portfolio: List[Dict[str, Any]], 
        period: str = "1y", 
        confidence_level: float = 0.95, 
        var_horizon: int = 1
    ) -> Dict[str, Any]:
        """
        Calculates portfolio risk metrics based on historical data.
        
        :param portfolio: List of dictionaries containing 'ticker' and 'weight'.
                          Example: [{"ticker": "BBCA", "weight": 0.4}, {"ticker": "BBRI", "weight": 0.6}]
        :param period: Time period for historical data (e.g., "1y", "6mo").
        :param confidence_level: Confidence level for VaR calculation (e.g., 0.95 for 95%).
        :param var_horizon: Value at Risk horizon in days.
        :return: A dictionary containing the Portfolio Risk Result.
        """
        
        # 2. VALIDATE PORTFOLIO INPUT
        if not portfolio:
            return {"status": "ERROR", "message": "Portfolio cannot be empty."}
            
        total_weight = 0.0
        for asset in portfolio:
            if "ticker" not in asset or "weight" not in asset:
                return {"status": "ERROR", "message": "Each asset must have 'ticker' and 'weight'."}
            weight = asset["weight"]
            if weight <= 0:
                return {"status": "ERROR", "message": f"Weight for {asset['ticker']} must be > 0."}
            total_weight += weight
            
        epsilon = 0.0001
        if abs(total_weight - 1.0) > epsilon:
            return {"status": "ERROR", "message": f"Total portfolio weight must equal 1.0. Got {total_weight}"}
            
        # 3. REQUEST HISTORICAL DATA
        if not self.data_fetcher:
             return {"status": "ERROR", "message": "Data fetcher is not provided."}

        price_data = {}
        for asset in portfolio:
            ticker = asset["ticker"]
            prices = self.data_fetcher(ticker, period)
            
            if prices is None or prices.empty:
                return {"status": "INSUFFICIENT_DATA", "message": f"Insufficient data for {ticker}."}
            
            price_data[ticker] = prices

        # Combine all price series into a single DataFrame aligned by date
        df_prices = pd.DataFrame(price_data)
        
        # 4. VALIDATE HISTORICAL DATA
        # Apply forward-fill for missing price data to maintain time-series alignment
        df_prices.ffill(inplace=True)
        # Drop rows that still have NaNs (e.g., at the very beginning of the series)
        df_prices.dropna(inplace=True)
        
        if df_prices.empty or len(df_prices) < 2:
            return {"status": "INSUFFICIENT_DATA", "message": "Insufficient data after alignment and cleanup."}
            
        # 5. CALCULATE DAILY RETURNS
        df_returns = df_prices.pct_change().dropna()
        
        # Extract ordered tickers and weights to ensure matrix operations are correctly aligned
        tickers = [asset["ticker"] for asset in portfolio]
        weights = np.array([asset["weight"] for asset in portfolio])
        
        # 6. CALCULATE INDIVIDUAL VOLATILITY
        volatility = df_returns[tickers].std()
        annualized_volatility = volatility * np.sqrt(TRADING_DAYS_PER_YEAR)
        
        # 7. CALCULATE CORRELATION MATRIX
        correlation_matrix = df_returns[tickers].corr()
        
        # 8. CALCULATE COVARIANCE MATRIX
        covariance_matrix = df_returns[tickers].cov()
        annualized_covariance_matrix = covariance_matrix * TRADING_DAYS_PER_YEAR
        
        # 9. CALCULATE PORTFOLIO RETURN
        portfolio_returns_daily = df_returns[tickers].dot(weights)
        
        # 10. CALCULATE PORTFOLIO VOLATILITY
        portfolio_variance = weights.T @ annualized_covariance_matrix @ weights
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # 11. CALCULATE RISK CONTRIBUTION
        marginal_contribution = covariance_matrix @ weights
        component_contribution = weights * marginal_contribution
        total_contribution = component_contribution.sum()
        risk_contribution = component_contribution / total_contribution
        
        # 12. CALCULATE CONCENTRATION RISK (Herfindahl-Hirschman Index / HHI)
        concentration_risk = np.sum(weights ** 2)
        
        # 13. CALCULATE HISTORICAL VaR
        var_threshold = np.percentile(portfolio_returns_daily, (1 - confidence_level) * 100)
        historical_var_daily = -var_threshold
        
        if historical_var_daily < 0:
            historical_var_daily = 0
            
        historical_var = historical_var_daily * np.sqrt(var_horizon)
        
        # 14. CALCULATE MAXIMUM DRAWDOWN
        cumulative_returns = (1 + portfolio_returns_daily).cumprod()
        running_peak = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_peak) / running_peak
        maximum_drawdown = drawdown.min()
        
        # 15. BUILD PORTFOLIO RISK RESULT
        result = {
            "feature": "portfolio_risk",
            "status": "SUCCESS",
            "portfolio": portfolio,
            "period": period,
            "metrics": {
                "portfolio_volatility": float(portfolio_volatility),
                "individual_volatility": annualized_volatility.to_dict(),
                "correlation_matrix": correlation_matrix.to_dict(),
                "covariance_matrix": covariance_matrix.to_dict(),
                "risk_contribution": risk_contribution.to_dict(),
                "concentration_risk": float(concentration_risk),
                "historical_var": float(historical_var),
                "maximum_drawdown": float(maximum_drawdown)
            },
            "metadata": {
                "historical_data_source": "yfinance",
                "data_provider": "UnifiedData",
                "var_method": "historical",
                "confidence_level": confidence_level,
                "var_horizon": var_horizon,
                "trading_days_assumed": TRADING_DAYS_PER_YEAR
            }
        }
        
        return result
