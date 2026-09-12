
import yfinance as yf
import pandas as pd
import os
from datetime import datetime

# ==== KONFIGURASI ====
TICKERS = {
    "BBCA": "BBCA.JK",
    "AMRT": "AMRT.JK",
    "TLKM": "TLKM.JK",
    "ASII": "ASII.JK",
    "GOTO": "GOTO.JK",
}

OUTPUT_DIR = "data_saham"          # folder output CSV
PERIOD = "max"                     # ambil data historis semaksimal mungkin
INTERVAL = "1d"                    # data harian

os.makedirs(OUTPUT_DIR, exist_ok=True)


def scrape_ticker(nama: str, kode_yf: str) -> pd.DataFrame:
    """Ambil data historis 1 saham dari yfinance dan rapikan formatnya."""
    print(f"Mengambil data {nama} ({kode_yf}) ...")

    ticker = yf.Ticker(kode_yf)
    df = ticker.history(period=PERIOD, interval=INTERVAL, auto_adjust=False)

    if df.empty:
        print(f"  -> WARNING: tidak ada data untuk {nama}")
        return df

    df = df.reset_index()
    df["Ticker"] = nama

    # rapikan nama kolom & urutan
    df = df.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
        "Dividends": "dividends",
        "Stock Splits": "stock_splits",
    })

    kolom_urut = ["date", "Ticker", "open", "high", "low", "close",
                  "adj_close", "volume", "dividends", "stock_splits"]
    kolom_urut = [k for k in kolom_urut if k in df.columns]
    df = df[kolom_urut]

    # tanggal tanpa timezone biar rapi di csv
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

    print(f"  -> {len(df)} baris, dari {df['date'].min().date()} sampai {df['date'].max().date()}")
    return df


def main():
    semua_data = []

    for nama, kode_yf in TICKERS.items():
        df = scrape_ticker(nama, kode_yf)
        if df.empty:
            continue

        # simpan per saham
        path_csv = os.path.join(OUTPUT_DIR, f"{nama}.csv")
        df.to_csv(path_csv, index=False)
        print(f"  -> disimpan ke {path_csv}\n")

        semua_data.append(df)

    # gabungkan semua saham jadi 1 file (long format, enak buat ML)
    if semua_data:
        df_gabungan = pd.concat(semua_data, ignore_index=True)
        df_gabungan = df_gabungan.sort_values(["Ticker", "date"])
        path_gabungan = os.path.join(OUTPUT_DIR, "all_stocks_combined.csv")
        df_gabungan.to_csv(path_gabungan, index=False)
        print(f"Data gabungan disimpan ke {path_gabungan}")
        print(f"Total baris: {len(df_gabungan)}")
    else:
        print("Tidak ada data yang berhasil di-scrape.")


if __name__ == "__main__":
    print(f"Mulai scraping - {datetime.now()}\n")
    main()
    print(f"\nSelesai - {datetime.now()}")