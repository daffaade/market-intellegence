# Model-P0 — P0 Intelligence Engine

> **Scope:** Forecast, Classification & Signal Engine  
> **Implements:** `implementation-plan-forecast-signal-module.md` §1–§14  
> **Priority:** P0 (wajib) sesuai `logic-ml.md` §5.20

---

## Struktur Folder

```
Model-P0/
├── run.py                 ← Entry point utama (jalankan ini)
├── data_loader.py         ← Akuisisi data via get_api_data()
├── feature_engineering.py ← Cleaning, 16 fitur teknikal+fundamental, label H+1..H+7
├── forecast_model.py      ← 7 clf + 7 reg (RandomForest), scaler, evaluasi
├── peer_analysis.py       ← Peer median, relative position, dividend check
├── signal_engine.py       ← Fundamental Divergence, Opportunity Score, Risk Score
└── README.md              ← Dokumen ini
```

---

## Cara Menjalankan

### Dari project root (`d:\aduhg\projek`)

```powershell
# Default tickers: BBCA, BBRI, BMRI, TLKM, ANTM, BUMI
python Model-P0/run.py

# Custom tickers
python Model-P0/run.py BBCA BBRI BMRI TLKM ANTM
```

### Dari dalam folder Model-P0

```powershell
cd d:\aduhg\projek\Model-P0
python run.py BBCA BBRI BMRI
```

---

## Output

### 1. Progress Log (stderr-style ke terminal)
```
[1/7] Loading data …
  [OK] BBCA — 2464 price rows loaded
[2/7] Feature engineering …
  [OK] BBCA — 2404 rows after feature engineering
[3/7] Training multi-horizon models …
  H+1  clf_acc=0.550  reg_MAE=0.0147  reg_dir_acc=0.467
  ...
[4/7] Computing peer medians …
[5/7] Generating signals per ticker …
  [OK] BBCA  opp=67.2  risk=35.3  anomaly=False
```

### 2. JSON Output (per ticker)
```json
[
  {
    "ticker": "BBCA",
    "forecast": {
      "last_close": 6325.0,
      "horizon_curve": {
        "H+1": {"predicted_return": 0.00186, "direction": 1},
        "H+2": {"predicted_return": 0.00346, "direction": 1},
        "H+3": {"predicted_return": 0.00522, "direction": 1},
        "H+4": {"predicted_return": 0.00620, "direction": 1},
        "H+5": {"predicted_return": 0.00655, "direction": 0},
        "H+6": {"predicted_return": 0.00684, "direction": 1},
        "H+7": {"predicted_return": 0.00892, "direction": 1}
      },
      "model_agreement_flag": false,
      "disagreement_horizons": [5]
    },
    "fundamental_divergence": {
      "detected": true,
      "confidence": "High",
      "pos_factor_count": 3,
      "supporting_factors": [
        "Revenue/Growth improved (↑)",
        "Future Forecast improved (↑)",
        "Valuation compressed vs prior (↓ = cheaper)",
        "Institutional flow decreased (↓)"
      ],
      "window": "~21d"
    },
    "peer_analysis": {
      "growth_proxy":    {"ticker_val": 0.03, "peer_median": 0.01, "diff": 0.02, "position": "Outperform"},
      "valuation_proxy": {"ticker_val": -0.02, "peer_median": -0.01, "diff": -0.01, "position": "Underperform"},
      ...
    },
    "opportunity_signal": {
      "score": 67.2,
      "confidence": "High",
      "direction": "Positive",
      "positive_factors": ["Forecast H+7 positive (+0.89%)", "Valuation attractive vs peer", ...],
      "negative_factors": ["Institutional flow below peer"],
      "evidence": [
        "Forecast H+7 Return: +0.89%",
        "Valuation proxy: -0.0200 vs peer -0.0100 (diff -0.0100)",
        ...
      ]
    },
    "risk_signal": {
      "score": 35.3,
      "level": "Medium",
      "negative_factors": ["Institutional flow below peer (outflow risk)"],
      "evidence": [...]
    },
    "anomaly": false,
    "period": "10y",
    "timestamp": "2026-09-16T15:27:56"
  }
]
```

### 3. Accuracy Table
```
Horizon   CLF Acc       MAE      RMSE     MAPE%       R²   Dir Acc
------------------------------------------------------------------------
  H+1      0.550   0.01470   0.02134    99.23  -0.0012    0.467
  H+2      0.538   0.02060   0.03012   101.45  -0.0089    0.483
  ...
  H+7      0.564   0.03660   0.05301   103.12  -0.0210    0.534
```

---

## Deskripsi Modul

### `data_loader.py`
- `load_price_df(ticker, period="10y")` — ambil data harga historis
- `load_fundamental_snapshot(ticker)` — valuation, forecast, dividend, institutional, peers
- `load_all_tickers(tickers, price_period)` — batch loader untuk semua ticker

### `feature_engineering.py`
- **16 fitur** per baris:
  - Returns: `return_1d`, `return_5d`, `return_20d`, `return_60d`
  - Volatilitas: `vol_20d`, `vol_60d`, `vol_ratio`
  - Momentum: `price_vs_ma20`, `price_vs_ma60`, `price_vs_ma200`, `rsi_14`, `intraday_range`
  - Fundamental proxy: `growth_proxy`, `valuation_proxy`, `forecast_proxy`, `institutional_flow`
- Label H+1..H+7: `label_dir_h` (0/1) dan `label_ret_h` (return %)
- Temporal split 60% train / 40% test

### `forecast_model.py`
- `train_all_horizons(df)` — latih 14 model (7 clf + 7 reg) pada data gabungan semua ticker
- `generate_forecast_curve(results, features)` — buat kurva H+1..H+7 dari snapshot terbaru
- `build_accuracy_table(results)` — ringkasan metrik per horizon
- **Evaluasi:** Accuracy, MAE, RMSE, MAPE, R², Directional Accuracy

### `peer_analysis.py`
- `compute_peer_medians(snapshots)` — median cross-ticker untuk tiap metrik
- `build_ticker_snapshot(df)` — ambil nilai latest dari feature DataFrame
- `peer_relative_position(snap, medians)` — Outperform / Underperform / Neutral per metrik
- `has_recent_dividend(fundamentals)` — cek ketersediaan dividen terbaru

### `signal_engine.py`
- `compute_fundamental_divergence(current, prior)` — detected (bool), confidence, supporting_factors
- `compute_opportunity_score(...)` — weighted score 0-100, 5 komponen:

  | Komponen | Bobot |
  |---|---|
  | Predicted Return H+7 | 25% |
  | Valuation vs Peer | 25% |
  | Institutional Flow vs Peer | 20% |
  | Fundamental Divergence | 20% |
  | Peer Position (growth + dividend) | 10% |

- `compute_risk_score(...)` — weighted score 0-100 → **Low / Medium / High**

  | Komponen | Bobot |
  |---|---|
  | Negative Return H+7 | 25% |
  | Valuation Stretched | 25% |
  | Institutional Outflow | 20% |
  | Fundamental Deterioration | 20% |
  | High Volatility | 10% |

- `compute_anomaly_flag(...)` — True jika model accuracy rendah atau sinyal kontradiktif

---

## Prinsip Desain (dari `logic-ml.md`)

- **Sistem menghitung, AI menjelaskan** — modul ini adalah computation layer, bukan explanation
- **Evidence trace-back** — setiap score menyimpan angka pembentuknya (`evidence` list)
- **No recommendation language** — output: Risk Signal / Opportunity Signal, bukan Buy/Sell
- **Fundamental Divergence** sebagai reasoning layer terpisah dari features model
- **Temporal split** 60/40 berbasis tanggal, bukan random — menjaga integritas time-series

---

## Dependencies

```
pandas
numpy
scikit-learn
unified_data  (internal — ada di ../unified_data/)
```

---

## Catatan §15 (Open Questions dari Implementation Plan)

| Pertanyaan | Keputusan Default |
|---|---|
| Model gabungan vs per-ticker? | **Gabungan** — semua ticker dikombinasi sebelum training |
| Normalisasi score: min-max atau z-score? | **Min-max** dengan range tetap per komponen |
| Clf-reg disagree di H+7 → turunkan confidence? | **Dicatat sebagai flag** (`disagreement_horizons`), belum otomatis turunkan score |
