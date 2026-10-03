import os
import logging
import pandas as pd
import yfinance as yf
from pathlib import Path

logger = logging.getLogger(__name__)

def get_corporate_events(ticker: str) -> pd.DataFrame:
    """
    1. Pastikan folder data/ ada.
    2. Fetch LIVE tk.actions dari yfinance (ticker + '.JK') -> dividen & stock split.
    3. Simpan/overwrite hasil fetch ke data/events.csv.
    4. Kalau gagal, baca cache. Kalau tidak ada, return DataFrame kosong.
    """
    # 1. Pastikan folder data/ ada
    core_dir = Path(__file__).resolve().parent
    ai_engine_dir = core_dir.parent
    data_dir = ai_engine_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    events_csv = data_dir / "events.csv"
    clean_ticker = ticker.upper().replace(".JK", "").strip()
    
    live_success = False
    df_live = pd.DataFrame()
    
    try:
        tk = yf.Ticker(f"{clean_ticker}.JK")
        actions = tk.actions
        
        if actions is not None and not actions.empty:
            events_list = []
            for date, row in actions.iterrows():
                d = row.get("Dividends", 0)
                s = row.get("Stock Splits", 0)
                date_str = date.strftime("%Y-%m-%d")
                
                if d > 0:
                    events_list.append({
                        "ticker": clean_ticker,
                        "date": date_str,
                        "event_type": "dividend",
                        "description": f"Cash Dividend IDR {d:.2f}"
                    })
                if s > 0:
                    events_list.append({
                        "ticker": clean_ticker,
                        "date": date_str,
                        "event_type": "split",
                        "description": f"Stock Split {s}"
                    })
                    
            df_live = pd.DataFrame(events_list)
            
            # 3. Simpan/overwrite ke events.csv
            # Kita append atau overwrite? Karena ini per ticker, 
            # jika overwrite seluruh file, data ticker lain hilang. 
            # Kita baca dulu yang ada, lalu update untuk ticker ini.
            if events_csv.exists():
                df_existing = pd.read_csv(events_csv)
                # Hapus data lama untuk ticker ini
                df_existing = df_existing[df_existing["ticker"] != clean_ticker]
                df_to_save = pd.concat([df_existing, df_live], ignore_index=True)
            else:
                df_to_save = df_live
                
            df_to_save.to_csv(events_csv, index=False)
            live_success = True
            
            # Tambahkan metadata untuk pemanggil
            df_live.attrs["data_quality"] = "ok"
            df_live.attrs["data_source"] = "real"
            
        else:
            # Berhasil konek tapi kosong
            live_success = True
            df_live = pd.DataFrame(columns=["ticker", "date", "event_type", "description"])
            df_live.attrs["data_quality"] = "ok"
            df_live.attrs["data_source"] = "real"
            
    except Exception as e:
        logger.warning(f"Gagal mengambil corporate events via yfinance untuk {clean_ticker}: {e}")
        live_success = False

    # 4. Kalau live fetch gagal
    if not live_success:
        if events_csv.exists():
            try:
                df_existing = pd.read_csv(events_csv)
                df_cached = df_existing[df_existing["ticker"] == clean_ticker].copy()
                df_cached.attrs["data_quality"] = "partial"
                df_cached.attrs["data_source"] = "cache"
                return df_cached
            except Exception:
                pass
        
        # Jika file tidak ada atau gagal dibaca
        df_empty = pd.DataFrame(columns=["ticker", "date", "event_type", "description"])
        df_empty.attrs["data_quality"] = "missing"
        df_empty.attrs["data_source"] = "missing"
        return df_empty
        
    return df_live
