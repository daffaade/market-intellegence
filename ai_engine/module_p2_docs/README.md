# ai_engine/modules — Backend Integration Guide

> **Scope:** Dokumentasi serah terima untuk tim backend Go.  
> Modul-modul ini dapat dipanggil langsung sebagai Python function — tidak perlu FastAPI router.

---

## Ringkasan Modul

| Modul         | File               | Entry Point                              | Input      | Output                |
| ------------- | ------------------ | ---------------------------------------- | ---------- | --------------------- |
| Event Study   | `event_study.py`   | `run_event_study(ticker, event_id=None)` | ticker IDX | `dict` / `list[dict]` |
| Macro Impact  | `macro_impact.py`  | `run_macro_impact(ticker)`               | ticker IDX | `dict`                |

---

## 1. Event Study

**Fungsi:** `run_event_study(ticker: str, event_id: str | None = None)`

**Cara panggil:**

```python
from ai_engine.models.event_study.event_study import run_event_study

# Semua event untuk BBCA
results = run_event_study("BBCA")          # returns list[dict]

# Event spesifik
result = run_event_study("BBCA", event_id="2024-04-12_dividend")  # returns dict
```

**Contoh output:**

```json
{
  "ticker": "BBCA",
  "event_id": "2024-04-12_dividend",
  "event_type": "dividend",
  "description": "BBCA mengumumkan dividen...",
  "event_date": "2024-04-12",
  "car": 0.018,
  "t_stat": 1.45,
  "p_value": 0.16,
  "significant_at_5pct": false,
  "alpha": 0.00012,
  "beta": 0.85,
  "n_estimation": 180,
  "level": "Low",
  "score": 20,
  "evidence": [
    "CAR[-5,+5] = +1.8%, t-stat=1.45, p=0.16 (tidak signifikan pada 5%)",
    "..."
  ],
  "data_quality": "ok",
  "data_source": "real"
}
```

**`data_quality` yang mungkin:**
| Nilai | Kondisi |
|---|---|
| `ok` | Estimation window ≥ 80 hari, data lengkap |
| `partial` | Histori pendek (GOTO sejak IPO 2022), window dipersempit otomatis |
| `missing` | Data harga tidak tersedia atau estimation window terlalu kecil |

---

## 2. Macro Impact

**Fungsi:** `run_macro_impact(ticker: str)`

**Cara panggil:**

```python
from ai_engine.models.macro_impact.macro_impact import run_macro_impact

result = run_macro_impact("ASII")   # returns dict
```

**Contoh output:**

```json
{
  "ticker": "ASII",
  "as_of": "2026-10-02",
  "forecast_revisions": [
    {
      "date": "2024-09-30",
      "direction": "down",
      "magnitude_pp": -2.1,
      "co_occurring_macro_event": {
        "variable": "USD_IDR",
        "change": "+3.2%",
        "date": "2024-09-30"
      },
      "within_window_days": 0
    }
  ],
  "co_occurrence_rate": 0.33,
  "base_rate": 0.2,
  "level": "Low",
  "score": 30,
  "evidence": [
    "Forecast proxy ASII bergerak turun (-2.1pp) pada 2024-09-30, bertepatan dengan..."
  ],
  "data_quality": "proxy",
  "data_source": "real"
}
```

> **Catatan penting untuk AI Layer:** evidence selalu dibahasakan **korelasional**.
> AI layer tidak boleh menambahkan klaim sebab-akibat atas output ini.

**`data_quality` yang mungkin:**
| Nilai | Kondisi |
|---|---|
| `proxy` | Data lengkap (histori > ~2 tahun) |
| `partial` | Histori pendek atau macro CSV terbatas |
| `missing` | Data harga tidak tersedia sama sekali |

## Data Files & Getters

Kedua modul ini mengambil data alternatif secara dinamis menggunakan **Getters** (`ai_engine/core/data_events.py` & `ai_engine/core/data_macro.py`). Getter ini mengambil data *live* dari sumber eksternal lalu membuat *cache* ke dalam CSV di `ai_engine/data/`. Jika gagal mengambil data live, sistem akan membaca cache tersebut; namun jika file cache tidak ada, sistem akan mereturn array kosong/dataframe kosong tanpa error.

### Sumber Data Eksternal
- **Data Event (Corporate Actions):** Diambil secara live dari **Yahoo Finance** (`yfinance`). Data yang diekstrak meliputi aksi korporasi seperti pembagian dividen (*cash dividend*) dan pemecahan saham (*stock split*).
- **Data Makro Ekonomi:**
  - **USD/IDR & Brent Crude Oil:** Diambil dari **Yahoo Finance** (`yfinance`).
  - **Tingkat Inflasi Indonesia:** Diambil menggunakan API dari **Badan Pusat Statistik (BPS)**.
  - **Suku Bunga BI (BI Rate/BI7DRR):** Diambil via scraping langsung dari situs resmi **Bank Indonesia (BI)** (`bi.go.id`).

| File / Modul               | Isi                          | Keterangan |
| -------------------------- | ---------------------------- | ---------- |
| `core/data_events.py`      | **Dynamic Getter**           | Mengambil data event dari Yahoo Finance (`yfinance`). |
| `core/data_macro.py`       | **Dynamic Getter**           | Mengambil makro (YFinance, BPS API, Web BI). |
| `data/events.csv`          | Cache kalender event korporasi | Ter-generate otomatis jika folder kosong |
| `data/macro_series.csv`    | Cache makro ekonomi          | Ter-generate otomatis jika folder kosong |

---

## Config Files

| File                        | Mengontrol                                                     |
| --------------------------- | -------------------------------------------------------------- |
| `config/event_study.yaml`   | Estimation/event window, minimum observasi, scoring thresholds |
| `config/macro_impact.yaml`  | Shock thresholds per variabel makro, co-occurrence window      |

---

## Menjalankan Tests

```powershell
cd ai_engine
python -m pytest tests/test_event_study.py tests/test_macro_impact.py -v
```

Tests sudah terintegrasi dengan _dynamic getter_ dan mampu membuat folder `data/` secara otomatis jika kosong.

---

## Disclaimer Wajib (Pasal 3 AGENTS.md)

Setiap respons yang mengandung output modul-modul ini HARUS menyertakan:

> _"Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."_
