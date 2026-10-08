# Deploy: frontend hosting + backend di VPS

Backend (Go, port 8080) dan AI engine (Python, port 8000) sudah berjalan di VPS
sebagai service `systemd --user` (`market-backend`, `market-engine`) dan otomatis
hidup setelah reboot. Yang perlu di-hosting hanya **frontend** (`frontend/`).

## 1. Build frontend

- **Node 22.12 ke atas** (Vite 8 menolak versi lebih lama; 22.11 gagal dengan
  error "Cannot find native binding").
- Perintah: `cd frontend && npm ci && npm run build` → hasil di `frontend/dist/`
  (situs statis, bisa di Vercel / Netlify / Cloudflare Pages / Nginx).
- Environment variable saat build:

| Variabel | Nilai |
|---|---|
| `VITE_API_BASE_URL` | URL publik backend **HTTPS** (lihat langkah 2), atau kosong `""` jika memakai proxy `/api` di host yang sama |
| `VITE_SUPABASE_URL` | `https://lxiwfmlblrphwefbtboj.supabase.co` |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | publishable key yang sama dengan `frontend/.env.example` (aman di frontend; data dilindungi RLS) |

Catatan: `VITE_API_BASE_URL=""` → frontend memanggil `/api/...` di domainnya sendiri.

## 2. Backend harus bisa diakses lewat HTTPS

Frontend di HTTPS **tidak boleh** memanggil `http://IP:8080` (browser memblokir
*mixed content*). Pilih salah satu:

**A. Proxy dari host frontend (paling cepat).** Contoh Vercel, `frontend/vercel.json`:

```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "http://IP_VPS:8080/api/:path*" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```
lalu build dengan `VITE_API_BASE_URL=""`. Port 8080 VPS harus terbuka untuk server host.
(Netlify: `_redirects` → `/api/*  http://IP_VPS:8080/api/:splat  200`.)

**B. Domain + HTTPS di VPS** (mis. Caddy: `api.domain.com { reverse_proxy localhost:8080 }`)
lalu `VITE_API_BASE_URL=https://api.domain.com`.

Tunnel SSH (`ssh -L 8080:localhost:8080`) hanya untuk development di laptop.

## 3. Login Google untuk domain baru (wajib, kalau tidak login gagal)

1. **Supabase → Authentication → URL Configuration**
   - Site URL: `https://DOMAIN-FRONTEND`
   - Redirect URLs: tambahkan `https://DOMAIN-FRONTEND/**` (biarkan `http://localhost:5173/**` untuk dev)
2. **Google Cloud Console → Credentials → OAuth client**
   - Authorized JavaScript origins: tambahkan `https://DOMAIN-FRONTEND`
   - Redirect URI tetap `https://lxiwfmlblrphwefbtboj.supabase.co/auth/v1/callback`
3. **OAuth consent screen**: selama status *Testing*, hanya email di *Test users* yang
   bisa login. Untuk juri: tambahkan email mereka, atau *Publish app*.

## 4. Cek setelah deploy

- `https://DOMAIN-FRONTEND/api/v1/health` (opsi A) atau `https://api.domain.com/api/v1/health`
  → `"ai_provider":"gemini"`.
- Buka aplikasi → titik status di kanan atas harus **Live**, bukan "Backend offline".
- Ikon pipeline (titik status) → "Sumber data" menampilkan tanggal cache Sectors.

## Kuota

- **Sectors**: laporan per emiten di-cache 7 hari, arus asing 7 hari, IHSG 1 hari
  (≈1–2 kredit/hari untuk 10 emiten). Endpoint publik hanya menerima emiten yang
  dipantau, jadi pengunjung tidak bisa menghabiskan kredit.
- **Gemini** (`gemini-3.1-flash-lite`, free tier): ringkasan dibuat sekali per
  emiten per hari saat snapshot diperbarui.
