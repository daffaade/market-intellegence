# CONTEXT PROJECT — SECTORS HACKATHON INDONESIA 2026

## 1. IDENTITAS PROJECT

Kami adalah tim berisi **4 orang** yang mengikuti **Sectors Hackathon / Indonesia / 2026**.

Track yang dipilih:

> **Track 03 — Market Intelligence**

Tujuan utama kami adalah membuat aplikasi yang menggunakan data finansial Indonesia dari **Sectors API/MCP** untuk menghasilkan **derived intelligence**, bukan sekadar menampilkan ulang data.

Konsep besar aplikasi:

> **AI-powered Market Intelligence Platform yang menemukan perubahan, anomali, hubungan, peluang relatif, dan risiko dari data pasar Indonesia.**

Prinsip utama:

> **Sectors Data → Data Processing → Intelligence Engine → Signal/Insight → Evidence → AI Explanation → UI**

AI bukan satu-satunya mesin analisis. Logic analisis utama harus deterministic/terukur dan berasal dari data.

---

# 2. ATURAN HACKATHON YANG RELEVAN

Beberapa aturan penting yang harus selalu diperhatikan:

### Eligibility & Team

- Peserta harus memenuhi ketentuan kewarganegaraan/domisili Indonesia.
- Tim terdiri dari **2–4 orang** atau solo.
- Satu peserta hanya boleh berada di satu tim.
- Satu tim hanya mengirimkan satu project.
- Setiap peserta harus membuat akun Sectors dan menyelesaikan onboarding.
- Setelah seluruh onboarding selesai, tim dapat mengklaim API credits.
- Tersedia **1.000 Sectors API credits per tim**.
- Tidak boleh membuat banyak akun untuk mendapatkan credits tambahan.

### Build Period

Build period dimulai **19 Agustus 2026**.

Project code tidak boleh sudah dibuat sebelum build period.

Repository harus dibuat selama build period.

Project tidak boleh merupakan project lama yang dipindahkan ke hackathon.

Boilerplate, framework, library, dan open-source code diperbolehkan selama bukan finished product yang sudah jadi.

Project harus eksklusif untuk hackathon ini dan tidak boleh dikirim ke kompetisi lain.

### Sectors Data

Setiap track harus menggunakan:

> **Sectors MCP atau Sectors REST API**

sebagai **core data source**.

Sectors tidak boleh hanya digunakan sebagai decorative/integrasi tambahan.

Qualifying test:

> Jika data Sectors dihilangkan, core functionality aplikasi harus ikut kehilangan fungsi penting.

### Track 03 — Market Intelligence

Produk harus menghasilkan:

> **derived insight**

yaitu analisis yang dihasilkan dari data.

Contoh yang memenuhi:

- signals/scores
- rankings
- custom screener dengan logic sendiri
- anomaly detection
- comparative analysis
- synthesized research output

Yang tidak cukup:

> hanya menampilkan ulang data Sectors dalam dashboard yang lebih bagus.

### Track Boundary

- Agent dengan dashboard masih bisa masuk Agents & Assistants.
- Autonomous pipeline yang menghasilkan score dapat masuk Automation atau Market Intelligence tergantung core product.
- Kami memilih **Market Intelligence** karena fokus utama produk adalah analytical intelligence.
- **Automated trade execution dilarang.**

### Judging

Penilaian:

- **Real-world usability — 40%**
- **Video demo/storytelling — 30%**
- **Technical depth/execution — 30%**

Jadi project harus:

1. benar-benar functional
2. punya use case nyata
3. punya cerita/demo yang kuat
4. punya technical depth
5. menggunakan Sectors secara substantif

### Financial Advice

Aplikasi harus diposisikan sebagai:

> information / analysis / research tool

bukan financial advice atau personal investment recommendation.

Hindari output seperti:

> BUY / HOLD / SELL

sebagai core output.

Gunakan:

> Opportunity Signal / Risk Signal / Intelligence Finding

---

# 3. TIMELINE HACKATHON

Timeline penting:

- Registration opens: **19 Aug 2026**
- Build period starts: **19 Aug 2026**
- Registration closes: **22 Sep 2026, 23:59 WIB**
- Build/submission closes: **30 Sep 2026, 23:59 WIB**
- Judging: **1–8 Oct 2026**
- Winners announced: **9 Oct 2026**

Current project planning date: **15 Sep 2026**.

Karena waktu terbatas, project harus menggunakan pendekatan **MVP-first**.

---

# 4. IDE AWAL DAN PERMASALAHANNYA

Awalnya kami membuat daftar banyak fitur financial analysis seperti:

- Valuation Analysis
- Competitive Analysis
- Growth Analysis
- Dividend Analysis
- Management Analysis
- Insider Confidence Analysis
- Ownership Analysis
- Smart Money Analysis
- Governance Analysis
- Investment Thesis
- Event Study
- Macro Impact Analysis
- Industry Impact Analysis
- Disaster Risk Analysis
- Consumer Behavior Analysis

Masalahnya:

Sebagian fitur tersebut merupakan **basic financial analysis** yang jika berdiri sendiri tidak cukup membedakan project dari aplikasi market intelligence yang sudah ada.

Contoh:

> Valuation → terlalu umum  
> Peer Comparison → terlalu umum  
> Stock Screener → terlalu umum  
> AI Investment Thesis → sudah banyak  
> Anomaly Scanner → juga sudah ada di market

Kesimpulan:

> Fitur dasar harus menjadi **input bagi Intelligence Engine**, bukan menjadi produk utama secara terpisah.

---

# 5. POSITIONING PRODUCT

Positioning yang dipilih:

> **Market Intelligence Platform — sistem yang menemukan perubahan, anomali, hubungan, dan risiko tersembunyi dari data pasar Indonesia.**

Atau secara sederhana:

> **AI-powered Market Intelligence yang mengubah data finansial Indonesia menjadi actionable research insights.**

Namun istilah "actionable" di sini bukan berarti memberikan rekomendasi BUY/SELL.

Core value:

> User tidak perlu membaca puluhan data finansial secara manual. Sistem mencari pola dan perubahan yang signifikan, kemudian menjelaskan evidence di baliknya.

---

# 6. FITUR YANG SUDAH DIRENCANAKAN

## 6.1 Company Intelligence

Fitur dasar sebagai sumber data/analytical input:

1. Valuation Analysis
2. Competitive / Peer Analysis
3. Growth Analysis
4. Income / Dividend Analysis
5. Management Analysis
6. Insider Confidence Analysis
7. Ownership Analysis
8. Smart Money Analysis

Fitur-fitur tersebut bukan tujuan akhir.

Mereka menyediakan input untuk intelligence engine.

---

## 6.2 Anomaly & Signal Intelligence

Ini merupakan core differentiation:

1. **Market Anomaly Detector**
2. **What Changed?**
3. **Fundamental Divergence**
4. **Opportunity Signal**
5. **Risk Signal**
6. **Catalyst Detector**
7. **Signal Relationship / Evidence**

---

## 6.3 Market & Industry Intelligence

1. Sector Intelligence
2. Intelligent Screener
3. Industry Impact Analysis
4. Event Study / Impact Analysis

---

## 6.4 Macro & External Impact Intelligence

Planned/optional:

1. Macro Impact Analysis
2. Disaster Risk Analysis
3. Consumer Behavior Analysis

Fitur-fitur ini membutuhkan data eksternal tambahan dan/atau data exposure yang mungkin belum tersedia.

Karena itu bukan prioritas MVP.

---

## 6.5 Portfolio Intelligence

Optional:

> Portfolio Risk Analysis

Digunakan untuk melihat konsentrasi sektor, risk signals, dan exposure.

---

## 6.6 AI Research Explanation

AI digunakan sebagai explanation layer:

> Intelligence Result → AI → Natural Language Research Summary

AI membantu pengguna memahami hasil analisis.

AI bukan sumber angka atau score.

---

# 7. FITUR YANG DIPRIORITASKAN

## P0 — CORE MVP

1. Peer Analysis
2. What Changed?
3. Anomaly Detector
4. Fundamental Divergence
5. Opportunity Signal
6. Risk Signal
7. Evidence Generation

## P1 — Jika P0 stabil

8. Catalyst Detector
9. Sector Intelligence
10. Intelligent Screener
11. Smart Money Integration
12. AI Research Explanation

## P2 — Jika masih ada waktu

13. Portfolio Risk
14. Event Study
15. Macro Impact
16. Disaster Risk
17. Consumer Behavior

---

# 8. FITUR YANG TIDAK MENJADI CORE

Jangan membuat aplikasi menjadi kumpulan menu yang semuanya berdiri sendiri.

Yang sebaiknya tidak menjadi core:

- standalone Dividend Analysis
- standalone Governance Score
- standalone Valuation Dashboard
- standalone Growth Dashboard
- Buy/Hold/Sell
- AI Investment Thesis sebagai fitur utama

AI Investment Thesis bisa digantikan dengan:

> AI Research Summary

yang menjelaskan hasil intelligence engine.

---

# 9. WORKFLOW SISTEM

Workflow utama:

```text
User
 ↓
Frontend
 ↓
Backend
 ↓
Sectors API / MCP
 ↓
Data Processing
 ↓
Derived Metrics
 ↓
Intelligence Engine
 ↓
Signals / Scores
 ↓
Evidence
 ↓
AI Explanation
 ↓
Frontend
 ↓
User
```

Empat prinsip utama:

### 1. Sectors = Primary Data Source

Sectors harus menjadi sumber data utama yang benar-benar digunakan.

### 2. Intelligence Engine = Product Core

Value utama project ada pada logic yang mengubah data menjadi intelligence.

### 3. Every Insight Has Evidence

Tidak boleh ada score/signal tanpa alasan dan data pendukung.

### 4. AI = Explanation Layer

AI membantu menjelaskan hasil analisis, bukan menggantikan seluruh analytical logic.

---

# 10. DATA YANG DIGUNAKAN

Data yang sudah diidentifikasi dari daftar fitur:

### Priority 1

- Valuation Metrics
- Peer Data
- Future Forecast
- Institutional Transactions
- Executive Shareholdings
- Major Shareholders
- Shareholder Composition

### Priority 2

- Dividend History
- Key Executives
- Historical Price Data

### Priority 3 / Need Verification

- Event data
- Macro data
- Geographic exposure perusahaan
- Disaster data
- Consumer behavior data
- Industry/policy data
- Historical data dengan granularitas yang diperlukan

Penting:

> Jangan mengasumsikan endpoint/tool Sectors tertentu sebelum benar-benar diverifikasi.

---

# 11. DATA PROCESSING

Pipeline:

```text
Raw Sectors Data
 ↓
Validation
 ↓
Normalization
 ↓
Derived Metrics
 ↓
Intelligence
```

Validation mencakup:

- missing data
- duplicate
- invalid value
- period
- unit
- consistency

Normalization diperlukan supaya perusahaan dapat dibandingkan secara valid.

---

# 12. DERIVED METRICS

Contoh:

### Peer Growth Difference

```text
GrowthDiff =
Company Growth - Median Peer Growth
```

### Valuation Difference

```text
ValuationDiff =
Company Metric - Median Peer Metric
```

### Institutional Divergence

Membandingkan perubahan institutional transactions terhadap baseline/fundamental condition.

### Ownership Concentration

Mengukur konsentrasi kepemilikan berdasarkan shareholder data.

Derived metrics menjadi input Intelligence Engine.

---

# 13. PEER ANALYSIS

Perusahaan dibandingkan dengan peer berdasarkan:

- valuation
- growth
- dividend
- ownership
- institutional activity
- forecast

Contoh:

```text
Company Growth      = 18%
Peer Median Growth  = 9%

Difference          = +9%
```

Output:

```text
Growth       → Above Peer
Valuation    → Below Peer
Dividend     → Above Peer
Institution  → Strong
```

---

# 14. WHAT CHANGED?

Tujuan:

> Menemukan perubahan signifikan dari perusahaan dibandingkan periode sebelumnya.

Contoh:

```text
Revenue Growth
Previous = 8%
Current  = 15%

Change = +7 percentage points
```

Kemudian sistem mencari perubahan pada:

- growth
- valuation
- institutional transactions
- ownership
- insider holdings
- dividend
- forecast

Perubahan diberi priority:

- HIGH
- MEDIUM
- LOW

---

# 15. ANOMALY DETECTOR

Untuk MVP, gunakan **rule-based anomaly detection** terlebih dahulu.

Contoh konsep:

```text
IF metric deviation > threshold
THEN anomaly = TRUE
```

Contoh:

```text
Peer median growth = 7%
Company growth = 22%

Difference = +15%
```

Jika threshold awal = +10%:

```text
Growth Anomaly = TRUE
```

Catatan:

> Threshold bukan nilai final. Harus dikalibrasi berdasarkan distribusi data aktual.

---

# 16. FUNDAMENTAL DIVERGENCE

Mencari indikator yang bergerak tidak searah.

Contoh:

```text
Revenue Growth       ↑
Future Forecast      ↑
Valuation            ↓
Institutional Flow   ↑
```

Sistem menghasilkan:

```text
Divergence Detected
Confidence: High
```

dengan supporting factors.

Contoh negatif:

```text
Revenue Growth       ↓
Future Forecast      ↓
Institutional Flow   ↓
Valuation             ↑
```

→ possible risk/deterioration signal.

---

# 17. OPPORTUNITY SCORE

Konsep:

```text
OpportunityScore =
w1 Growth +
w2 Valuation +
w3 Institutional +
w4 Forecast +
w5 PeerPosition
```

Contoh bobot awal:

```text
Growth          25%
Valuation       25%
Institutional   20%
Forecast        20%
Peer Position   10%
```

Score dinormalisasi menjadi:

```text
0–100
```

Contoh:

```text
Opportunity Score = 84
```

Tetapi score harus selalu disertai factors/evidence.

Contoh:

```text
84/100

Positive:
+ Growth above peer
+ Valuation below peer
+ Institutional activity increasing

Negative:
- Dividend declining
```

---

# 18. RISK SCORE

Konsep sama tetapi fokus pada negative signals.

Contoh:

```text
Revenue Growth       ↓
Future Forecast      ↓
Institutional Flow   ↓
Peer Position        ↓
```

Output:

```text
Risk Score = 78/100
```

Factors:

1. Growth deterioration
2. Forecast revision
3. Institutional activity weakening

Gunakan istilah:

> Risk Signal / Risk Level

bukan:

> Sell Recommendation

---

# 19. CATALYST DETECTOR

Mencari kombinasi perubahan yang berpotensi menjadi catalyst.

Contoh:

```text
Future Forecast ↑
+
Institutional Activity ↑
+
Valuation below peer
```

→ Catalyst Signal

Output:

```text
Catalyst Detected
Strength: High

Drivers:
- Forecast improvement
- Institutional accumulation
- Relative undervaluation
```

---

# 20. SECTOR INTELLIGENCE

Mengagregasi perusahaan berdasarkan sektor.

Metrics:

- average growth
- median valuation
- number of anomalies
- opportunity signals
- risk signals
- institutional activity

Contoh:

```text
Technology

Growth Trend       ↑
Opportunity Signals 8
Risk Signals        2
Anomalies            5
```

Kemudian ranking perusahaan di sektor tersebut.

---

# 21. INTELLIGENT SCREENER

Bukan sekadar:

```text
P/E < 15
Growth > 10%
```

Tetapi menggunakan intelligence logic:

```text
Growth > Peer Median
AND
Valuation < Peer Median
AND
Institutional Activity > Baseline
AND
Risk Score < Threshold
```

Output berupa ranked result.

Contoh:

```text
Rank #1
Opportunity Score = 87

Why:
- Growth +12% vs peer
- Valuation -18% vs peer
- Institutional activity +24%
```

---

# 22. EVENT STUDY

Jika data historis dan event tersedia, dapat dilakukan:

```text
Return =
(Pt - Pt-1) / Pt-1
```

Abnormal return sederhana:

```text
AR =
Stock Return - Benchmark Return
```

Contoh:

```text
Event Day Return = -4.8%
Abnormal Return  = -4.2%
```

Output:

```text
Event Impact:
Negative
```

Tetapi fitur ini **data-dependent** dan bukan prioritas sebelum data tersedia.

---

# 23. EVIDENCE ENGINE

Setiap insight harus dapat ditelusuri.

Contoh:

```text
Opportunity Score = 84
```

Evidence:

```text
Growth:
Company = 18%
Peer Median = 9%
Difference = +9%

Valuation:
Company = 11x
Peer Median = 16x

Institutional:
Current = +24%
Baseline = +8%
```

Traceability:

```text
Raw Data
 ↓
Metric
 ↓
Signal
 ↓
Score
```

Ini penting untuk explainability dan technical depth.

---

# 24. CONFIDENCE SCORE

Selain score, sistem dapat memberikan:

```text
Confidence:
High / Medium / Low
```

Confidence dapat mempertimbangkan:

- jumlah evidence
- data completeness
- consistency antar indikator
- strength of deviation
- agreement antar signal

Untuk MVP bisa dimulai dengan rule-based confidence.

---

# 25. AI RESEARCH SUMMARY

Input AI:

```json
{
  "signal": "opportunity",
  "score": 84,
  "factors": [
    "growth_above_peer",
    "valuation_below_peer",
    "institutional_activity_increase"
  ],
  "evidence": []
}
```

AI menghasilkan natural-language explanation.

AI TIDAK boleh:

- mengarang angka
- mengubah score
- mengarang event
- mengklaim data yang tidak tersedia
- memberikan personal investment recommendation

Jika data tidak ada:

> Data unavailable

bukan AI mengisi sendiri.

---

# 26. STANDARD OUTPUT INTELLIGENCE ENGINE

Semua intelligence result sebaiknya mempunyai format konsisten:

```text
Signal
Score
Confidence
Direction
Severity
Factors
Evidence
Timestamp
```

Contoh:

```text
Signal      : Opportunity
Score       : 84
Confidence  : High
Direction   : Positive
Severity    : Medium

Factors:
- Growth above peer
- Valuation below peer
- Institutional activity increased

Evidence:
- Growth: 18% vs peer 9%
- Valuation: 11x vs peer 16x
- Institutional: +24% vs baseline +8%
```

---

# 27. UI / PRODUCT STRUCTURE

Navigasi utama:

```text
Application
│
├── Market Overview
├── Intelligence Scanner
├── Company Intelligence
├── Sector Intelligence
├── Event Study
└── Portfolio Intelligence
```

AI Research Summary dan Evidence bukan harus menjadi menu utama karena merupakan output layer.

---

# 28. MARKET OVERVIEW

Tujuan:

> "Apa yang sedang menarik perhatian intelligence engine?"

Isi:

- Market Signals
- Top Opportunities
- Top Risks
- Top Anomalies
- Sector Intelligence

---

# 29. INTELLIGENCE SCANNER

User memilih:

```text
Universe
- All Market
- Sector
- Watchlist
- Custom Selection

Analysis
- Opportunity
- Risk
- Anomaly
- Growth
- Valuation
- Institutional Activity
```

Hasil berupa ranking.

---

# 30. COMPANY INTELLIGENCE

Struktur:

```text
Company Intelligence
│
├── Overview
├── What Changed?
├── Valuation
├── Growth
├── Peer Position
├── Ownership
├── Institutional Activity
├── Anomalies
├── Signals
└── Research Summary
```

Overview menampilkan:

```text
Opportunity Signal
84/100

Risk Level
Medium

Peer Position
Outperform

Detected Anomalies
3
```

---

# 31. WHAT CHANGED UI

Contoh:

```text
WHAT CHANGED?

Growth
18% ↑ from 9%

Institutional Activity
+24% ↑ from +8%

Future Forecast
Improved

Valuation
11x ↓ from 14x
```

Kemudian:

> Why does it matter?

---

# 32. PEER COMPARISON UI

Tabel:

| Metric | Target | Peer Median | Position |
|---|---:|---:|---|
| Growth | 18% | 9% | ↑ |
| Valuation | 11x | 16x | ↓ |
| Dividend | 4% | 3% | ↑ |
| Institutional | +24% | +8% | ↑ |

---

# 33. ANOMALY UI

Contoh:

```text
Detected Anomalies

HIGH
Growth Anomaly

MEDIUM
Institutional Activity Anomaly

MEDIUM
Valuation Divergence
```

User dapat membuka detail anomaly dan melihat:

- current value
- baseline
- deviation
- evidence

---

# 34. SIGNAL UI

Contoh:

```text
SIGNALS

Opportunity
84 / 100

Risk
32 / 100
```

Opportunity Drivers:

1. Growth outperforming peers
2. Valuation below peer median
3. Institutional activity increasing

Risk Factors:

1. Forecast uncertainty
2. Dividend deterioration

---

# 35. EVIDENCE PANEL

Tombol:

> View Evidence

Menampilkan angka yang membentuk signal.

Tujuan:

> User dapat memverifikasi mengapa sistem menghasilkan suatu signal.

---

# 36. AI RESEARCH SUMMARY UI

Contoh:

```text
AI Research Summary

The company currently shows stronger growth
than its peer group while trading below the
peer valuation median. Institutional activity
has also increased.

However, forecast uncertainty remains a
factor that should be monitored.
```

Di bawahnya:

```text
Based on:
✓ Peer Analysis
✓ Growth Analysis
✓ Valuation Analysis
✓ Institutional Activity
```

---

# 37. SECTOR INTELLIGENCE UI

Contoh:

```text
Technology

Growth Trend       ↑
Opportunity        12
Risk Signals        4
Anomalies           7
```

Kemudian company ranking berdasarkan intelligence.

---

# 38. SIGNAL MATRIX

Salah satu visual yang dapat menjadi ciri khas:

```text
                 Opportunity
                      ↑
                      │
         A            │       B
                      │
──────────────────────┼────────────→
                      │
         C            │       D
                      │
                      ↓
                    Risk
```

Perusahaan diposisikan berdasarkan:

- Opportunity Score
- Risk Score

---

# 39. VISUALIZATION PRINCIPLES

Visual harus membantu analisis.

### Comparison Chart

Untuk:

> posisi perusahaan vs peer

### Trend Chart

Untuk:

> apa yang berubah

### Distribution

Untuk:

> apakah value merupakan anomaly

### Ranking

Untuk:

> perusahaan mana paling menonjol

### Signal Matrix

Untuk:

> kombinasi opportunity dan risk

Jangan membuat visual hanya untuk dekorasi.

---

# 40. DISCLAIMER UI

Gunakan disclaimer:

> **Disclaimer:** Informasi dan analisis yang disediakan merupakan hasil pengolahan data untuk tujuan informasi dan riset. Aplikasi ini bukan merupakan nasihat atau rekomendasi investasi personal. Pengguna bertanggung jawab atas keputusan investasinya sendiri.

---

# 41. ARCHITECTURE

Architecture yang dirancang:

```text
┌──────────────────────────────┐
│ Frontend                     │
│ React + TypeScript + Tauri   │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Backend                      │
│ Go                           │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Data Layer                   │
│ Sectors API/MCP + DB/Cache   │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Intelligence Engine          │
│ Python                       │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ AI Layer                     │
└──────────────────────────────┘
```

---

# 42. FRONTEND

Technology:

> React + TypeScript + Tauri

Responsibility:

- UI
- navigation
- charts
- visualization
- signal display
- evidence
- user interaction

Frontend tidak melakukan core financial calculation.

---

# 43. BACKEND

Technology:

> Go

Responsibility:

- API
- orchestration
- validation
- request handling
- communication dengan Intelligence Engine
- AI integration
- error handling
- logging

---

# 44. DATA LAYER

Responsibility:

- Sectors API/MCP
- database
- cache
- data transformation awal
- historical data

Database choice masih konseptual dan ditentukan setelah kebutuhan aktual diketahui.

---

# 45. INTELLIGENCE ENGINE

Technology:

> Python

Alasan:

Python cocok untuk:

- data processing
- numerical analysis
- statistical analysis
- scoring
- anomaly detection
- ranking
- future ML development

Modules:

```text
valuation
growth
peer
institutional
insider
ownership
anomaly
divergence
signal
scoring
evidence
```

---

# 46. CONCEPTUAL FOLDER STRUCTURE

```text
project/
│
├── frontend/
├── backend/
├── intelligence/
├── data/
├── docs/
└── README.md
```

Ownership:

```text
frontend/     → Frontend Engineer
backend/      → Backend Engineer
intelligence/ → Intelligence Engineer
data/         → Data Engineer
docs/         → Shared
```

---

# 47. TEAM OF 4

## Anggota 1 — Data Engineer

Fokus:

- Sectors API/MCP
- data ingestion
- validation
- normalization
- database
- cache
- historical data

Output:

> Sectors → clean structured financial data

---

## Anggota 2 — Intelligence / Quant Engineer

Fokus:

- derived metrics
- peer analysis
- What Changed
- anomaly detection
- divergence
- opportunity
- risk
- catalyst
- sector intelligence
- screener
- evidence

Output:

> Financial data → derived intelligence

Ini merupakan role yang paling berhubungan dengan differentiation produk.

---

## Anggota 3 — Backend Engineer

Fokus:

- Go backend
- API
- orchestration
- communication antar-layer
- AI integration
- error handling

Output:

> Intelligence → reliable application service

---

## Anggota 4 — Frontend / Product Engineer

Fokus:

- React
- TypeScript
- Tauri
- UI/UX
- charts
- dashboard
- signal visualization
- evidence panel

Output:

> Backend/API → usable intelligence interface

---

# 48. FEATURE OWNERSHIP

| Feature | Data | Intelligence | Backend | Frontend |
|---|:---:|:---:|:---:|:---:|
| Valuation | A1 | A2 | A3 | A4 |
| Peer Analysis | A1 | **A2** | A3 | A4 |
| What Changed | A1 | **A2** | A3 | A4 |
| Anomaly | A1 | **A2** | A3 | A4 |
| Divergence | A1 | **A2** | A3 | A4 |
| Opportunity | A1 | **A2** | A3 | A4 |
| Risk | A1 | **A2** | A3 | A4 |
| Catalyst | A1 | **A2** | A3 | A4 |
| Sector Intelligence | A1 | **A2** | A3 | A4 |
| Screener | A1 | **A2** | **A3** | A4 |
| AI Summary | — | A2 | **A3** | A4 |
| Portfolio | A1 | **A2** | A3 | A4 |
| Event Study | A1 | **A2** | A3 | A4 |

Ownership berarti owner utama, bukan berarti orang lain tidak ikut mengerjakan.

---

# 49. INTEGRATION FLOW ANTAR ANGGOTA

```text
Data Engineer
      ↓
CompanyData
      ↓
Intelligence Engineer
      ↓
IntelligenceResult
      ↓
Backend Engineer
      ↓
API Response
      ↓
Frontend Engineer
      ↓
UI
```

Contoh `IntelligenceResult`:

```json
{
  "type": "ANOMALY",
  "company": "XXX",
  "score": 82,
  "severity": "HIGH",
  "summary": "...",
  "factors": [],
  "evidence": []
}
```

Format final masih bisa berubah saat implementasi.

---

# 50. DEFINITION OF DONE

## Data

- data berhasil diperoleh
- format konsisten
- error handling

## Intelligence

- logic berjalan
- output terstruktur
- evidence tersedia
- edge case ditangani

## Backend

- service/API berjalan
- response sesuai contract
- error handling

## Frontend

- UI selesai
- data berhasil ditampilkan
- loading state
- error state

## Integration

Pipeline harus benar-benar berjalan:

```text
Sectors
 ↓
Backend
 ↓
Intelligence
 ↓
AI
 ↓
Frontend
```

---

# 51. GIT WORKFLOW

Branch contoh:

```text
main
│
├── feature/data-integration
├── feature/intelligence-engine
├── feature/backend-api
└── feature/frontend-dashboard
```

Commit harus menunjukkan development nyata.

Contoh:

```text
feat: integrate company valuation data
feat: implement peer comparison
feat: add anomaly detection
feat: create intelligence API
feat: implement company intelligence page
```

Jangan menunggu akhir lalu membuat satu commit besar.

---

# 52. HAL YANG MASIH HARUS DIVERIFIKASI

Ini penting sebelum implementasi final.

Jangan menganggap semua data di bawah pasti tersedia di Sectors.

Harus diverifikasi:

1. Sectors API/MCP tools yang benar-benar tersedia
2. valuation endpoint/data
3. peer data
4. future forecast
5. institutional transactions
6. executive shareholdings
7. ownership
8. historical price
9. historical granularity
10. event data
11. macro data
12. company geographic exposure
13. disaster data
14. consumer behavior data

Terutama:

> **Event Study, Macro Impact, Disaster Risk, Consumer Behavior**

jangan dijadikan dependency MVP sebelum sumber datanya jelas.

---

# 53. HAL YANG TIDAK BOLEH DILAKUKAN

Jangan membuat:

> Sectors API → Dashboard

lalu mengklaim sebagai Market Intelligence.

Harus ada:

> Sectors Data → Derived Metrics → Analysis → Signal/Insight

Jangan membuat:

> AI → langsung memberikan Buy/Sell

Jangan membuat:

> Score tanpa evidence

Jangan membuat:

> AI mengarang data yang tidak tersedia

Jangan membuat:

> 20+ fitur sederhana yang tidak terhubung

Lebih baik:

> 5–7 intelligence features yang benar-benar matang.

---

# 54. PRIORITAS PROJECT SECARA KESELURUHAN

Urutan development yang disarankan:

### Step 1 — Verify Sectors

Pastikan data dan API/MCP benar-benar tersedia.

### Step 2 — Data Contract

Data Engineer menentukan struktur data.

### Step 3 — Intelligence MVP

Buat:

```text
Peer
What Changed
Anomaly
Divergence
Opportunity
Risk
Evidence
```

### Step 4 — Backend

Expose intelligence melalui API.

### Step 5 — Frontend

Bangun:

```text
Market Overview
Company Intelligence
Evidence
Signals
```

### Step 6 — AI

Tambahkan AI Research Summary.

### Step 7 — P1

Jika MVP stabil:

```text
Catalyst
Sector Intelligence
Screener
```

### Step 8 — Polish

- UX
- performance
- error handling
- demo data
- README
- architecture documentation
- demo video

---

# 55. PRODUCT STORY

Story yang dapat digunakan saat demo:

### Problem

Investor/researcher menghadapi banyak data finansial tetapi sulit mengetahui:

> "Apa yang benar-benar berubah?"

> "Mana yang abnormal?"

> "Mana yang outperform dibanding peer?"

> "Mengapa perusahaan ini menarik?"

### Solution

Aplikasi mengambil data finansial dari Sectors lalu menganalisisnya secara otomatis.

```text
Data
 ↓
Compare
 ↓
Detect
 ↓
Score
 ↓
Explain
```

### Result

User tidak hanya melihat:

> "Growth = 18%"

tetapi:

> "Growth perusahaan 18%, jauh di atas peer median 9%, sementara valuation berada di bawah peer. Sistem mendeteksi Opportunity Signal dengan evidence tersebut."

Itulah perbedaan antara **financial dashboard** dan **Market Intelligence product**.

---

# 56. CURRENT PROJECT DEFINITION

Jika harus diringkas menjadi satu kalimat:

> **Kami membangun Market Intelligence Platform yang menggunakan Sectors sebagai sumber data finansial utama untuk mendeteksi perubahan, anomaly, divergence, dan relative opportunity/risk pada perusahaan dan sektor, kemudian menyajikan hasilnya bersama evidence dan AI-generated explanation.**

Core pipeline:

```text
Sectors
  ↓
Financial Data
  ↓
Derived Metrics
  ↓
Comparative Analysis
  ↓
Anomaly / Divergence Detection
  ↓
Opportunity / Risk / Catalyst
  ↓
Evidence
  ↓
AI Explanation
  ↓
Market Intelligence UI
```

**Status dokumentasi saat ini sudah sampai Subbab 7:**

1. **Explanation of Features** ✅
2. **Workflow / How System Works** ✅
3. **Architecture** ✅
4. **Data Used** ✅
5. **Logic / Analysis Methods** ✅
6. **Output & UI** ✅
7. **Team Task Division** ✅
8. **Timeline & Priorities** ⏳

Langkah berikutnya adalah membuat **Subbab 8 — Timeline & Priorities**, tetapi sebelum coding sebaiknya juga dilakukan **verifikasi aktual Sectors API/MCP** supaya semua rancangan data dan fitur tidak berdasarkan asumsi.