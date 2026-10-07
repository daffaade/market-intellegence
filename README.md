# Market Intelligence Platform (IDX)

> **Track 03: Market Intelligence — Sectors Hackathon Indonesia 2026**
> Platform AI untuk membaca sinyal pasar saham Indonesia secara objektif — bukan untuk menyuruh orang beli/jual saham.

Dokumen ini menjelaskan **alur kerja sistem dari ujung ke ujung**, ditulis supaya orang yang baru lihat repo ini (termasuk yang bukan engineer) bisa paham apa yang terjadi, tanpa harus baca kode dulu.

---

## 1. Apa yang sebenarnya dikerjakan sistem ini?

Bayangkan ini seperti restoran:

| Bagian restoran | Bagian sistem ini | Tugasnya |
|---|---|---|
| 🛒 Belanja bahan | `data_processing/` | Ambil data mentah dari sumber luar (Sectors API, yfinance) |
| 👨‍🍳 Dapur, masak | `ai_engine/` | Olah data mentah jadi analisis: forecast, deteksi anomali, skor peluang |
| 🧾 Pelayan + kasir | `backend/` | Simpan hasil masakan (database), kasih ke pelanggan lewat API, pastikan tidak ada yang curang |
| 🍽️ Meja pelanggan | `frontend/` | Tempat orang benar-benar lihat & pakai hasilnya (app desktop) |

Yang **tidak** dilakukan sistem ini: menyuruh orang beli atau jual saham tertentu. Ini aturan ketat (lihat bagian 6) karena menyangkut regulasi OJK.

**10 emiten yang dipantau:** `BBCA`, `BBRI`, `BMRI`, `BBNI`, `TLKM`, `ASII`, `AMRT`, `GOTO`, `ANTM`, `BUMI`.

---

## 2. Alur data, selangkah demi selangkah

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  SUMBER LUAR     │     │  data_processing │     │   ai_engine       │     │  backend (Go)    │
│                  │     │  (Python)        │     │   (Python/FastAPI)│     │                   │
│  Sectors API ────┼────▶│  ambil + cache   │────▶│  hitung forecast, │────▶│  simpan ke        │
│  yfinance    ────┼────▶│  file di disk    │     │  anomaly, skor    │     │  Supabase +       │
│                  │     │                  │     │  peluang, dll     │     │  cache 24 jam     │
└─────────────────┘     └─────────────────┘     └──────────────────┘     └────────┬──────────┘
                                                                                     │ HTTP :8080
                                                                                     ▼
                                                                          ┌─────────────────┐
                                                                          │  frontend        │
                                                                          │  (Tauri+React)   │
                                                                          │  di laptop kamu  │
                                                                          └─────────────────┘
```

### Langkah per langkah:

1. **`data_processing/data_sectors/`** memanggil Sectors API (`api.sectors.app/v2`) untuk data fundamental, harga, kepemilikan institusi, dll. Hasilnya disimpan ke **file cache lokal** dulu — supaya kalau ada yang minta data yang sama lagi, tidak perlu panggil API lagi (lihat bagian 3, soal kuota).
2. **`data_processing/y_finance_data/`** mengambil data historis harga (OHLCV) dari yfinance sebagai pelengkap, terutama untuk data jangka panjang yang Sectors tidak selalu punya.
3. **`ai_engine/`** (jalan di port **8000**) memanggil kedua sumber itu lewat `UnifiedPipeline`, lalu:
   - Model **forecast** (Random Forest) memprediksi arah harga H+1 sampai H+7.
   - Model **anomaly detection** (Isolation Forest) mendeteksi lonjakan volume/harga yang tidak biasa.
   - Model **divergence** membandingkan fundamental emiten vs rata-rata peer-nya.
   - Model **smart money** & **catalyst** membaca pola transaksi institusi.
   - Semua angka ini dihitung **dulu** secara matematis, baru LLM (Gemini/Groq/mock) menjelaskannya dalam kalimat manusia. Jadi AI tidak pernah "mengarang" angka — dia cuma menerjemahkan angka yang sudah pasti.
4. **`backend/`** (jalan di port **8080**, bahasa Go) adalah pintu masuk resmi untuk frontend. Tugasnya:
   - Cek dulu apakah hasil analisis emiten itu sudah ada di database (Supabase) dan belum lewat 24 jam. Kalau sudah ada → langsung kasih balik, **tidak** panggil `ai_engine` lagi.
   - Kalau belum ada / sudah basi → baru panggil `ai_engine`, simpan hasilnya ke database, lalu kasih ke frontend.
   - Kalau `ai_engine` sedang mati/lambat → otomatis pakai data fallback (angka generik) supaya aplikasi tidak pernah crash — tapi ini artinya datanya **bukan** analisis real.
5. **`frontend/`** (Tauri + React, jalan di **laptop kamu**, bukan di VPS) menampilkan semua ini dalam bentuk dashboard: ringkasan market, skor per emiten, sinyal screener, dll.

---

## 3. Kenapa ada "cache" di 3 tempat?

Sectors API cuma kasih kuota **1.000 kredit** untuk tim ini — sekali habis, ya habis. Jadi sistem ini sengaja dibuat berlapis supaya **tidak ada panggilan Sectors yang terbuang**:

| Lapisan | Di mana | Berapa lama |
|---|---|---|
| 1 | File cache di `data_processing/` | Sampai dihapus manual |
| 2 | Memory cache di `ai_engine/` | 1 jam |
| 3 | Tabel `intelligence_snapshots` di Supabase (lewat `backend/`) | 24 jam |

Artinya: kalau kamu minta analisis BBCA dua kali dalam sehari, **cuma panggilan pertama** yang benar-benar menyentuh Sectors API. Panggilan kedua dijawab dari cache, dalam hitungan milidetik.

---

## 4. Non-negotiable: aturan kepatuhan (OJK)

Sistem ini **dilarang keras** memberi rekomendasi langsung seperti "Beli", "Jual", atau "Koleksi saham ini". Yang boleh ditampilkan cuma indikator objektif:

- Arah: `Bullish` / `Bearish` / `Neutral`
- `Opportunity Score` (0–100) dan `Risk Level` (`Low`/`Medium`/`High`)
- `Anomaly Flag` dan `Divergence Detected` (true/false)

Setiap hasil analisis yang ditampilkan ke pengguna **wajib** menyertakan disclaimer ini (persis, tidak boleh diparafrase):

> *"Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."*

---

## 5. Cara menjalankan semuanya

### A. Di VPS (server) — engine & backend

Di VPS ini, kedua service **sudah dipasang sebagai systemd service**, jalan terus otomatis dan restart sendiri kalau crash:

```bash
systemctl --user status market-engine market-backend   # cek status
systemctl --user restart market-backend                # restart kalau perlu
journalctl --user -u market-backend -f                 # lihat log live
```

Kalau mau jalankan manual (misalnya untuk debug), lihat skill `.claude/skills/stack-runbook/SKILL.md` — ada juga catatan soal `psql`, Go 1.25, dan gotcha lokasi file `.env`.

### B. Di laptop kamu — frontend

Frontend **tidak jalan di VPS** (dia app desktop, butuh tampilan). Dua terminal terpisah di laptop:

**Terminal 1 — buka tunnel ke VPS, biarkan terbuka:**
```bash
ssh -L 8080:localhost:8080 heketon@<ip-vps>
```
*(Kenapa perlu tunnel: backend tidak punya login/API-key sama sekali. Kalau diakses langsung lewat IP publik, siapa pun bisa memicu panggilan Sectors API dan menghabiskan kuota tim. Tunnel membungkus koneksi lewat SSH yang sudah diautentikasi, jadi backend tidak pernah "kelihatan" dari internet terbuka.)*

**Terminal 2 — terminal baru, lokal, jalankan frontend:**
```bash
cd frontend
npm install
npm run dev          # preview cepat di browser: http://localhost:5173
# atau, app desktop sungguhan (butuh Rust + Tauri CLI):
npm run tauri dev
```

Default `VITE_API_BASE_URL` sudah mengarah ke `http://localhost:8080`, jadi begitu Terminal 1 (tunnel) aktif, frontend otomatis bicara dengan backend di VPS tanpa perlu setting tambahan.

---

## 6. Peta folder

```
market-intellegence/
 ├── data_processing/     # Ambil & cache data mentah (Sectors API, yfinance)
 ├── ai_engine/            # FastAPI + model ML (port 8000)
 ├── backend/              # REST API Go, Clean Architecture (port 8080)
 ├── frontend/             # Tauri + React + Vite — app desktop, jalan di laptop
 ├── docs/                 # Spesifikasi arsitektur & rencana teknis
 ├── plan/                 # Materi kompetisi hackathon
 └── .claude/skills/       # Panduan kerja untuk AI coding assistant di repo ini
```

Untuk detail arsitektur backend (Clean Architecture layer, endpoint lengkap, constraint hackathon), lihat [`AGENTS.md`](./AGENTS.md).
