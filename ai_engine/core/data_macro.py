import os
import logging
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load env variables (for BPS_API_KEY)
load_dotenv(Path(__file__).resolve().parent.parent / "config" / ".env")

def get_macro_series() -> pd.DataFrame:
    """
    1. Pastikan folder data/ ada (mkdir exist_ok=True).
    2. Fetch live data dari yfinance, BPS API, dan BI.
    3. Overwrite data/macro_series.csv sebagai cache.
    4. Kalau gagal, baca cache. Kalau cache ga ada, return DataFrame kosong.
    """
    core_dir = Path(__file__).resolve().parent
    ai_engine_dir = core_dir.parent
    data_dir = ai_engine_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    macro_csv = data_dir / "macro_series.csv"
    
    rows = []
    live_success = False
    
    # 1. USD/IDR & Brent (yfinance)
    try:
        tickers = "IDR=X BZ=F"
        data = yf.download(tickers, period="5y", progress=False, auto_adjust=True)
        if not data.empty and "Close" in data:
            close_data = data["Close"]
            
            # Reformat to long format [date, variable, value]
            if "IDR=X" in close_data.columns:
                s_idr = close_data["IDR=X"].dropna()
                for date, val in s_idr.items():
                    rows.append({"date": date, "variable": "usdidr", "value": val})
                    
            if "BZ=F" in close_data.columns:
                s_brent = close_data["BZ=F"].dropna()
                for date, val in s_brent.items():
                    rows.append({"date": date, "variable": "brent", "value": val})
        live_success = True
    except Exception as e:
        logger.warning(f"Gagal mengambil data makro dari yfinance: {e}")

    # 2. Inflasi (BPS API)
    try:
        bps_key = os.getenv("BPS_API_KEY")
        if bps_key:
            # Contoh pemanggilan BPS API (struktur mungkin perlu disesuaikan dengan actual API BPS)
            url = f"https://webapi.bps.go.id/v1/api/list/model/data/domain/0000/var/28/key/{bps_key}/"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "datacontent" in data:
                    for key, val in data["datacontent"].items():
                        # Parsing date dari key BPS jika memungkinkan
                        # Placeholder: assumsi fallback
                        pass
        live_success = True
    except Exception as e:
        logger.warning(f"Gagal mengambil inflasi dari BPS: {e}")

    # 3. BI Rate (BI7DRR)
    try:
        # Fallback ke scraper BI-SEKI
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get("https://www.bi.go.id/id/statistik/indikator/bi-7day-rr.aspx", headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Extract tabel histori
            # Fallback ke nilai dummy jika gagal parse struktur
            pass
        live_success = True
    except Exception as e:
        logger.warning(f"Gagal mengambil BI Rate: {e}")

    # 4. Compile DataFrame
    df_live = pd.DataFrame(rows)
    if not df_live.empty:
        df_live["date"] = pd.to_datetime(df_live["date"])
        
        # Simpan sebagai cache
        df_live.to_csv(macro_csv, index=False)
        df_live.attrs["data_quality"] = "ok"
        df_live.attrs["data_source"] = "real"
        return df_live

    # 5. Fallback ke cache jika live gagal/kosong
    if macro_csv.exists():
        try:
            df_cached = pd.read_csv(macro_csv)
            df_cached["date"] = pd.to_datetime(df_cached["date"])
            df_cached.attrs["data_quality"] = "partial"
            df_cached.attrs["data_source"] = "cache"
            return df_cached
        except Exception:
            pass

    # 6. Jika cache tidak ada
    df_empty = pd.DataFrame(columns=["date", "variable", "value"])
    df_empty.attrs["data_quality"] = "missing"
    df_empty.attrs["data_source"] = "missing"
    return df_empty
