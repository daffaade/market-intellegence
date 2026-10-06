import sys
import os
import json
import pandas as pd
from pathlib import Path

# Add project root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = CURRENT_DIR.parent
ROOT_DIR = AI_ENGINE_DIR.parent
for p in [str(ROOT_DIR), str(AI_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ai_engine.models.portofolio_risk.portofolio_risk import PortfolioRisk
from ai_engine.core.data_loader import UnifiedDataLoader
from ai_engine.providers.gemini_provider import GeminiProvider

def test_portfolio_risk_with_summary():
    print("Initializing components...")
    data_loader = UnifiedDataLoader()
    
    # Use UnifiedDataLoader's get_historical_data, extracting 'Close' price
    def fetch_prices(ticker: str, period: str):
        df = data_loader.get_historical_data(ticker, period)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                s = df['Close'].iloc[:, 0]
            else:
                s = df['Close']
            
            if isinstance(s, pd.DataFrame):
                s = s.squeeze()
            
            # Convert timezone-aware index to naive if necessary, or just return
            return s
        return None

    model = PortfolioRisk(data_fetcher=fetch_prices)
    
    portfolio = [
        {"ticker": "BBCA", "weight": 0.4},
        {"ticker": "BMRI", "weight": 0.3},
        {"ticker": "TLKM", "weight": 0.3}
    ]
    
    print(f"Calculating risk for portfolio: {portfolio}")
    result = model.calculate_risk(portfolio=portfolio, period="1y")
    
    if result.get("status") != "SUCCESS":
        print("Calculation failed:", result.get("message", "Unknown error"))
        return
        
    print("Portfolio Risk calculated successfully. Generating AI Summary...")
    
    # Generate Summary
    provider = GeminiProvider()
    
    instruction = """
    Anda adalah AI Market Intelligence yang bertugas merangkum hasil metrik risiko portofolio saham.
    Anda akan menerima JSON hasil perhitungan risiko dari 'portfolio_risk'.
    
    ATURAN KETAT (NON-ADVISORY COMPLIANCE - WAJIB DIPATUHI):
    1. JANGAN memberikan rekomendasi BELI, JUAL, TAHAN, atau saran investasi lainnya.
    2. JANGAN memanipulasi, menghitung ulang, atau mengarang angka. Gunakan angka asli dari konteks.
    3. HANYA merangkum metrik yang ada dalam konteks, seperti volatilitas (portfolio_volatility), Historical VaR, dan Maximum Drawdown.
    4. Selalu masukkan disclaimer hukum resmi di akhir rangkuman.
    
    Disclaimer wajib: "Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."
    """
    
    schema = {
        "type": "object",
        "properties": {
            "risk_summary": {
                "type": "string",
                "description": "Rangkuman deskriptif objektif tentang tingkat risiko berdasarkan metrik."
            },
            "key_metrics_explained": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Penjelasan dari metrik penting seperti Volatility, VaR, Max Drawdown dan porsi risikonya (risk contribution)."
            },
            "disclaimer": {
                "type": "string",
                "description": "Teks disclaimer legal wajib."
            }
        },
        "required": ["risk_summary", "key_metrics_explained", "disclaimer"]
    }
    
    try:
        summary_result = provider.generate_summary(
            context=result, 
            instruction=instruction, 
            output_schema=schema
        )
        print("\n" + "="*50)
        print("=== AI SUMMARY RESULT ===")
        print("="*50)
        print(json.dumps(summary_result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Failed to generate summary: {e}")
        
    print("\n" + "="*50)
    print("=== RAW PORTFOLIO RISK DATA ===")
    print("="*50)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_portfolio_risk_with_summary()
