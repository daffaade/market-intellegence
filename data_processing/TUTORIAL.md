# 📖 Panduan Lengkap Penggunaan `get_api_data` (Unified Data API)

Dokumen ini berisi panduan lengkap penggunaan fungsi `get_api_data` dari modul `unified_data`, penjelasan parameter, daftar lengkap 17 tipe data (`data_type`), opsi periode waktu (`period`), dan contoh kode penggunaannya.

---

## INSTALL LIBRARY
pip install yfinance

## 📌 1. Pengenalan

Fungsi `get_api_data` adalah antarmuka utama (*Unified Data Layer*) yang menggabungkan dua sumber data finansial secara terintegrasi:

* **Sectors API**: Menyediakan data otoritatif pasar Indonesia (*current & short-term*), mencakup valuasi emiten BEI, kepemilikan konglomerat dan *whale investor*, transaksi institusi lokal, serta profil perusahaan.
* **yFinance API**: Menyediakan data jangka panjang (*long-term & cover-additional*), mencakup data historis harga saham multi-tahun, laporan keuangan tahunan, konsensus analis global, dan estimasi pertumbuhan laba.

Fungsi ini otomatis menangani:
* Validasi input dan sanitasi format data.
* Resolusi data yang tumpang tindih (*prioritas data lokal Sectors API, didukung data global yFinance*).
* Deteksi diskrepansi nilai secara otomatis.
* Penyimpanan ke dalam *Multi-Tier Cache* (Memory L1 + Disk L2) untuk inferensi berkecepatan tinggi.

---

## ⚙️ 2. Spesifikasi Fungsi & Parameter

### Signature Fungsi
```python
from unified_data.endpoint_finaldata import get_api_data

response = get_api_data(
    ticker: str,
    data_type: str = "all",
    period: str = "current",
    force_refresh: bool = False
) -> dict
```

### Parameter
* **`ticker`** *(str, Wajib)*:
  * Simbol ticker saham (contoh: `"BBCA"`, `"BBRI"`, `"TLKM"`, `"BMRI"`, `"BUMI"`, `"ANTM"`).
  * Suffix `.JK` akan ditangani otomatis.
* **`data_type`** *(str, Opsional, default: `"all"`)*:
  * Kategori data spesifik yang diminta (tersedia 17 tipe data).
* **`period`** *(str, Opsional, default: `"current"`)*:
  * Rentang waktu data (contoh: `"current"`, `"10y"`, `"5y"`, `"6m"`, `"4w"`).
* **`force_refresh`** *(bool, Opsional, default: `False`)*:
  * Jika `True`, akan melewati cache lokal dan mengambil data langsung dari sumber API.

---

## 🗂️ 3. Daftar Lengkap 17 `data_type` & Field yang Tersedia

Berikut adalah rincian 17 tipe data yang dapat dipanggil:

### 1. `price`
* **Sumber Utama**: yFinance Data Pipeline
* **Deskripsi**: Data pergerakan harga saham dan volume (OHLCV).
* **Field yang Tersedia**:
  * `date`: Tanggal perdagangan (format `YYYY-MM-DD`).
  * `open`: Harga pembukaan.
  * `high`: Harga tertinggi.
  * `low`: Harga terendah.
  * `close`: Harga penutupan.
  * `volume`: Volume perdagangan harian.
  * `currency`: Mata uang transaksi (e.g. `IDR`).
  * *Catatan*: Jika `period` diisi multi-tahun atau multi-minggu (e.g. `10y`, `6m`, `4w`), mengembalikan daftar `records` time-series lengkap.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BBCA", data_type="price", period="10y")
  ```

---

### 2. `valuation`
* **Sumber Utama**: Sectors API *(didukung yFinance)*
* **Deskripsi**: Metrik valuasi fundamental dan rasio keuangan.
* **Field yang Tersedia**:
  * `forward_pe`: Rasio Forward Price to Earnings.
  * `trailing_pe`: Rasio Trailing P/E (TTM).
  * `intrinsic_value`: Nilai intrinsik / target model valuasi.
  * `price_to_book`: Rasio Price to Book Value (P/B).
  * `peg_ratio`: Rasio PEG (Price/Earnings to Growth).
  * `enterprise_value`: Nilai Enterprise Value perusahaan.
  * `enterprise_to_revenue`: Rasio EV terhadap Pendapatan.
  * `enterprise_to_ebitda`: Rasio EV terhadap EBITDA.
  * `sample_historical_valuation`: Rekam valuasi historis tahunan.
  * `fifty_two_week_high` & `fifty_two_week_low`: Rentang harga 52 minggu.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BBCA", data_type="valuation", period="current")
  ```

---

### 3. `peers`
* **Sumber Utama**: Sectors API
* **Deskripsi**: Perbandingan emiten dengan kompetitor sejenis di industrinya.
* **Field yang Tersedia**:
  * `peer_company_name`: Nama perusahaan pembanding.
  * `market_cap`: Kapitalisasi pasar kompetitor.
  * `pe_ttm`: Rasio P/E TTM kompetitor.
  * `total_assets`: Total aset.
  * `total_liabilities`: Total liabilitas.
  * `total_equity`: Total ekuitas.
  * `total_revenue`: Total pendapatan.
  * `net_income`: Laba bersih.
  * `sector` & `industry`: Klasifikasi sektor dan industri.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BBCA", data_type="peers", period="current")
  ```

---

### 4. `forecast`
* **Sumber Utama**: Sectors API & yFinance Consensus
* **Deskripsi**: Proyeksi kinerja keuangan masa depan dan target konsensus analis.
* **Field yang Tersedia**:
  * `target_mean_price`: Target rata-rata harga menurut analis.
  * `target_high_price`: Target harga tertinggi analis.
  * `target_low_price`: Target harga terendah analis.
  * `target_median_price`: Target harga median analis.
  * `eps_estimate`: Estimasi laba per saham (EPS) mendatang.
  * `eps_growth`: Proyeksi pertumbuhan EPS.
  * `revenue_estimate`: Estimasi pendapatan masa depan.
  * `revenue_growth`: Proyeksi pertumbuhan pendapatan.
  * `estimate_year`: Tahun proyeksi.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BBRI", data_type="forecast", period="current")
  ```

---

### 5. `dividend`
* **Sumber Utama**: yFinance *(didukung Sectors API)*
* **Deskripsi**: Profil dividen, rasio pembayaran, dan riwayat pembayaran dividen.
* **Field yang Tersedia**:
  * `dividend_rate`: Nilai dividen per lembar saham.
  * `dividend_yield`: Dividend yield saat ini.
  * `payout_ratio`: Rasio pembayaran dividen terhadap laba.
  * `trailing_annual_dividend_rate`: Tingkat dividen tahunan berjalan.
  * `trailing_annual_dividend_yield`: Yield dividen tahunan berjalan.
  * `five_year_avg_dividend_yield`: Rata-rata yield dividen 5 tahun terakhir.
  * `ex_dividend_date`: Tanggal batas cum/ex dividen terakhir.
  * `dividend_history`: Daftar riwayat tanggal dan nominal dividen kas yang dibayarkan.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BMRI", data_type="dividend", period="5y")
  ```

---

### 6. `executives`
* **Sumber Utama**: Sectors API & yFinance
* **Deskripsi**: Data profil jajaran manajemen, dewan direksi, dan komisaris.
* **Field yang Tersedia**:
  * `name`: Nama pimpinan / eksekutif.
  * `position`: Jabatan (e.g. *President Director, Vice President Director*).
  * `age`: Usia eksekutif.
  * `year_born`: Tahun kelahiran.
  * `total_pay`: Total remunerasi / kompensasi.
  * `exercised_value` & `unexercised_value`: Nilai eksekusi opsi saham.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BBCA", data_type="executives", period="current")
  ```

---

### 7. `executive_shareholdings`
* **Sumber Utama**: Sectors API
* **Deskripsi**: Rincian kepemilikan saham riil oleh masing-masing pimpinan perusahaan.
* **Field yang Tersedia**:
  * `name`: Nama direktur / komisaris.
  * `position`: Jabatan di perusahaan.
  * `share_amount`: Jumlah lembar saham yang dimiliki secara langsung.
  * `share_percentage`: Persentase porsi kepemilikan terhadap total saham beredar.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BBCA", data_type="executive_shareholdings", period="current")
  ```

---

### 8. `major_shareholders`
* **Sumber Utama**: Sectors API
* **Deskripsi**: Informasi entitas atau pihak pengendali saham terbesar (PSP).
* **Field yang Tersedia**:
  * `name`: Nama pemegang saham mayoritas / pengendali.
  * `share_percentage`: Porsi kepemilikan saham mayoritas.
  * `share_amount`: Total lembar saham yang dimiliki.
  * `share_value`: Estimasi valuasi nilai kepemilikan saham.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BUMI", data_type="major_shareholders", period="current")
  ```

---

### 9. `shareholder_composition`
* **Sumber Utama**: Sectors API & yFinance
* **Deskripsi**: Struktur komposisi pemegang saham, keterkaitan konglomerat, dan *whale investor*.
* **Field yang Tersedia**:
  * `whale_investor`: Nama tokoh investor besar/konglomerat yang terafiliasi.
  * `conglomerate_group`: Nama grup konglomerasi pengendali.
  * `insiders_percent_held`: Persentase kepemilikan orang dalam / institusi pengendali.
  * `institutions_percent_held`: Persentase kepemilikan institusi publik.
  * `breakdown`: Rincian komposisi kepemilikan lainnya.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BBCA", data_type="shareholder_composition", period="current")
  ```

---

### 10. `institutional_transactions`
* **Sumber Utama**: Sectors API & yFinance
* **Deskripsi**: Rekam jejak transaksi dan kepemilikan dana institusi / fund manager global.
* **Field yang Tersedia**:
  * `transaction_date`: Tanggal pencatatan transaksi institusi.
  * `sample_buyer`: Institusi pembeli terbesar dan perubahan jumlah lembar saham.
  * `sample_seller`: Institusi penjual terbesar dan perubahan lembar saham.
  * `top_holder_name`: Nama institusi pengelola dana global terbesar.
  * `top_holder_shares`: Jumlah saham yang dikelola institusi.
  * `top_holder_value`: Nilai valuasi kepemilikan institusi.
  * `top_holder_pct_held`: Persentase kepemilikan institusi.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="TLKM", data_type="institutional_transactions", period="6m")
  ```

---

### 11. `financials`
* **Sumber Utama**: yFinance Data Pipeline
* **Deskripsi**: Laporan Laba Rugi (*Income Statement*) multi-tahun.
* **Field yang Tersedia**:
  * `years_available`: Daftar tahun laporan keuangan yang tersedia (e.g. `2025`, `2024`, `2023`).
  * `statements`: Dictionary metrik tahunan berisi `total_revenue`, `operating_revenue`, `gross_profit`, `operating_income`, `net_income`, `ebit`, `ebitda`, `basic_eps`, `diluted_eps`, dll.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="TLKM", data_type="financials", period="5y")
  ```

---

### 12. `balance_sheet`
* **Sumber Utama**: yFinance Data Pipeline
* **Deskripsi**: Laporan Posisi Keuangan (*Balance Sheet*) multi-tahun.
* **Field yang Tersedia**:
  * `years_available`: Daftar tahun neraca yang tersedia.
  * `statements`: Dictionary neraca tahunan berisi `total_assets`, `current_assets`, `cash_and_cash_equivalents`, `total_liabilities`, `current_liabilities`, `total_debt`, `stockholders_equity`, dll.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="TLKM", data_type="balance_sheet", period="5y")
  ```

---

### 13. `cash_flow`
* **Sumber Utama**: yFinance Data Pipeline
* **Deskripsi**: Laporan Arus Kas (*Cash Flow Statement*) multi-tahun.
* **Field yang Tersedia**:
  * `years_available`: Daftar tahun arus kas yang tersedia.
  * `statements`: Dictionary arus kas berisi `operating_cash_flow`, `investing_cash_flow`, `financing_cash_flow`, `capital_expenditure`, `free_cash_flow`, `dividends_paid`, dll.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="TLKM", data_type="cash_flow", period="5y")
  ```

---

### 14. `company`
* **Sumber Utama**: yFinance / Sectors API
* **Deskripsi**: Profil umum dan deskripsi lini bisnis operasional emiten.
* **Field yang Tersedia**:
  * `symbol`: Simbol emiten.
  * `company_name`: Nama resmi perseroan.
  * `sector`: Sektor industri.
  * `industry`: Sub-industri spesifik.
  * `currency`: Mata uang pelaporan.
  * `summary`: Deskripsi profil kegiatan operasional dan model bisnis perusahaan.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BBCA", data_type="company", period="current")
  ```

---

### 15. `sector`
* **Sumber Utama**: yFinance / Sectors API
* **Deskripsi**: Informasi sektor bisnis emiten.
* **Field yang Tersedia**: `symbol`, `sector`, `company_name`.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BBCA", data_type="sector", period="current")
  ```

---

### 16. `industry`
* **Sumber Utama**: yFinance / Sectors API
* **Deskripsi**: Informasi industri emiten.
* **Field yang Tersedia**: `symbol`, `industry`, `company_name`.
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BBCA", data_type="industry", period="current")
  ```

---

### 17. `all`
* **Sumber Utama**: Unified Multi-Source Pipeline
* **Deskripsi**: Pengambilan menyeluruh 11 section data terpadu sekaligus dalam satu respons.
* **Field yang Tersedia**:
  1. `company_data`
  2. `valuation_data`
  3. `peer_data`
  4. `forecast_data`
  5. `ownership_data`
  6. `institutional_data`
  7. `insider_data`
  8. `historical_data`
  9. `dividend_data`
  10. `financial_data`
  11. `market_data`
* **Contoh Panggilan**:
  ```python
  get_api_data(ticker="BBCA", data_type="all", period="current")
  ```

---

## ⏱️ 4. Opsi Format Periode (`period`)

Parameter `period` mengontrol rentang waktu data yang dikembalikan:

* **Snapshot Terkini / Default**:
  * `"current"` atau `"latest"`: Mengambil data titik waktu terkini.
* **Rentang Tahunan (`{n}y`)**:
  * `"1y"`: 1 tahun terakhir.
  * `"5y"`: 5 tahun terakhir.
  * `"10y"`: 10 tahun terakhir.
* **Rentang Bulanan (`{n}m`)**:
  * `"1m"`: 1 bulan terakhir.
  * `"3m"`: 3 bulan terakhir.
  * `"6m"`: 6 bulan terakhir.
  * `"12m"`: 12 bulan terakhir.
* **Rentang Mingguan (`{n}w`)**:
  * `"1w"`: 1 minggu terakhir.
  * `"2w"`: 2 minggu terakhir.
  * `"4w"`: 4 minggu terakhir.
  * `"12w"`: 12 minggu terakhir.

---

## 📋 5. Struktur Respons JSON Standar

Setiap pemanggilan `get_api_data` selalu mengembalikan format JSON standar yang konsisten:

* **`ticker`** *(str)*: Simbol saham yang diminta.
* **`data_type`** *(str)*: Kategori tipe data yang diproses.
* **`period`** *(str)*: Periode data yang digunakan.
* **`source`** *(str)*: Pipeline sumber data (`"Sectors"`, `"yFinance"`, atau `"Unified Multi-Source Pipeline"`).
* **`status`** *(str)*: Status eksekusi (`"SUCCESS"`, `"WARNING"`, `"ERROR"`).
* **`timestamp`** *(str)*: Waktu kompilasi data format ISO 8601 UTC.
* **`data`** *(dict/list)*: Payload isi data yang diminta.

Contoh struktur:
```json
{
  "ticker": "BBCA",
  "data_type": "valuation",
  "period": "current",
  "source": "Sectors",
  "status": "SUCCESS",
  "timestamp": "2026-09-13T10:00:00+00:00",
  "data": {
    "forward_pe": 13.1094,
    "trailing_pe": 13.405,
    "intrinsic_value": 13694,
    "price_to_book": 2.87,
    "peg_ratio": 1.58,
    "enterprise_value": 751206959939584,
    "fifty_two_week_high": 8750,
    "fifty_two_week_low": 4820
  }
}
```

---

## 💻 6. Contoh Kode Python per Skenario

### Skenario A: Analisis Fundamental & Valuasi Saham
```python
from unified_data.endpoint_finaldata import get_api_data

# Mengambil metrik valuasi saham BBCA
res = get_api_data(ticker="BBCA", data_type="valuation", period="current")

if res["status"] == "SUCCESS":
    val = res["data"]
    print(f"Ticker        : {res['ticker']}")
    print(f"Forward P/E   : {val.get('forward_pe')}")
    print(f"Trailing P/E  : {val.get('trailing_pe')}")
    print(f"Intrinsic Val : Rp {val.get('intrinsic_value'):,}")
    print(f"Price to Book : {val.get('price_to_book')}")
```

---

### Skenario B: Mengambil Riwayat Harga 10 Tahun (Time-Series)
```python
from unified_data.endpoint_finaldata import get_api_data

# Mengambil data harga 10 tahun untuk analisis historis
res = get_api_data(ticker="BMRI", data_type="price", period="10y")

if res["status"] == "SUCCESS":
    records = res["data"]["records"]
    print(f"Total Hari Perdagangan: {len(records):,} hari")
    print(f"Harga Penutupan Terakhir: Rp {res['data']['latest_close']:,}")

    # Menampilkan 3 record transaksi terbaru
    for r in records[-3:]:
        print(f"Tanggal: {r['date']} | Close: Rp {r['close']:,} | Volume: {r['volume']:,}")
```

---

### Skenario C: Analisis Proyeksi Laba & Target Analis (*Forecast*)
```python
from unified_data.endpoint_finaldata import get_api_data

# Mengambil konsensus proyeksi laba saham BBRI
res = get_api_data(ticker="BBRI", data_type="forecast", period="current")

if res["status"] == "SUCCESS":
    fc = res["data"]
    print(f"Target Rata-rata Analis : Rp {fc.get('target_mean_price'):,}")
    print(f"Target Tertinggi Analis : Rp {fc.get('target_high_price'):,}")
    print(f"Target Terendah Analis  : Rp {fc.get('target_low_price'):,}")
    print(f"Estimasi EPS            : Rp {fc.get('eps_estimate')}")
```

---

### Skenario D: Melacak Pemegang Saham Pengendali & *Whale Investor*
```python
from unified_data.endpoint_finaldata import get_api_data

# Mengambil data kepemilikan dan relasi konglomerasi saham BUMI
owner_res = get_api_data(ticker="BUMI", data_type="major_shareholders", period="current")
comp_res = get_api_data(ticker="BUMI", data_type="shareholder_composition", period="current")

print("Pemegang Saham Utama:", owner_res["data"].get("major_shareholder_name"))
print("Porsi Kepemilikan   :", f"{owner_res['data'].get('major_shareholder_percentage') * 100:.2f}%")
print("Grup Konglomerasi   :", comp_res["data"].get("conglomerate_group"))
print("Whale Investor      :", comp_res["data"].get("whale_investor"))
```

---

### Skenario E: Mengambil Laporan Keuangan 5 Tahun Terakhir
```python
from unified_data.endpoint_finaldata import get_api_data

# Mengambil laporan laba rugi 5 tahun emiten TLKM
res = get_api_data(ticker="TLKM", data_type="financials", period="5y")

if res["status"] == "SUCCESS":
    stmts = res["data"]["statements"]
    years = res["data"]["years_available"]
    print("Tahun Laporan yang Tersedia:", years)
    for yr in years[:3]:
        rev = stmts[yr].get("total_revenue")
        net = stmts[yr].get("net_income")
        print(f"[{yr}] Pendapatan: Rp {rev/1e12:,.1f}T | Laba Bersih: Rp {net/1e12:,.1f}T")
```

---

### Skenario F: Mengambil Seluruh 11 Domain Sekaligus (`all`)
```python
from unified_data.endpoint_finaldata import get_api_data

# Mengambil seluruh 11 section lengkap untuk Machine Learning / Intelligence Engine
res = get_api_data(ticker="BBCA", data_type="all", period="current")

if res["status"] == "SUCCESS":
    dataset = res["data"]
    print("Domain yang Tersedia:")
    for section_name in dataset.keys():
        print(f"  ✓ {section_name}")
```

---

## 🖥️ 7. Penggunaan Lewat Terminal CLI

Eksekusi cepat melalui terminal PowerShell / Command Prompt:

* **Sintaks Dasar**:
  ```bash
  python unified_data/endpoint_finaldata.py [TICKER] [DATA_TYPE] [PERIOD]
  ```

* **Contoh Perintah**:
  * Mengambil riwayat harga 10 tahun:
    ```bash
    python unified_data/endpoint_finaldata.py BMRI price 10y
    ```
  * Mengambil valuasi terkini:
    ```bash
    python unified_data/endpoint_finaldata.py BBCA valuation current
    ```
  * Mengambil laporan keuangan 5 tahun:
    ```bash
    python unified_data/endpoint_finaldata.py TLKM financials 5y
    ```
  * Mengambil dividen 5 tahun:
    ```bash
    python unified_data/endpoint_finaldata.py BMRI dividend 5y
    ```
  * Mengambil transaksi institusi 6 bulan:
    ```bash
    python unified_data/endpoint_finaldata.py BBCA institutional_transactions 6m
    ```
  * Mengambil seluruh dataset lengkap:
    ```bash
    python unified_data/endpoint_finaldata.py BBCA all current
    ```

---

## 🌐 8. Menjalankan REST API Server Lokal

Menyediakan microservice HTTP server lokal tanpa perlu dependensi tambahan:

* **Menjalankan Server**:
  ```bash
  python unified_data/endpoint_finaldata.py --serve 8080
  ```

* **Daftar Endpoint URL yang Tersedia**:
  * `http://localhost:8080/api/BBCA/price?period=10y`
  * `http://localhost:8080/api/BBCA/valuation?period=current`
  * `http://localhost:8080/api/BBRI/forecast?period=current`
  * `http://localhost:8080/api/BMRI/dividend?period=5y`
  * `http://localhost:8080/api/TLKM/financials?period=5y`
  * `http://localhost:8080/api/TLKM/balance_sheet?period=5y`
  * `http://localhost:8080/api/TLKM/cash_flow?period=5y`
  * `http://localhost:8080/api/BUMI/major_shareholders?period=current`
  * `http://localhost:8080/api/BBCA/all?period=current`
  * `http://localhost:8080/health`