# Login & daftar dengan Google

Login memakai **Supabase Auth** dengan provider Google. Akun dibuat otomatis
saat seseorang pertama kali masuk, jadi "daftar" dan "masuk" adalah tombol yang sama.
Watchlist dan portofolio tiap pengguna disimpan di tabel `user_watchlists` dan
`user_portfolios` (lihat `supabase/migrations/`), dilindungi row-level security:
setiap akun hanya bisa membaca dan mengubah barisnya sendiri.

## Sekali saja: mengaktifkan Google

### 1. Google Cloud Console
1. Buka <https://console.cloud.google.com/> → buat/pilih project.
2. **APIs & Services → OAuth consent screen**: pilih *External*, isi nama aplikasi
   (Marketidex), email dukungan, lalu simpan. Selama status *Testing*, tambahkan
   email yang boleh login di bagian *Test users*.
3. **APIs & Services → Credentials → Create credentials → OAuth client ID**
   - Application type: **Web application**
   - Authorized JavaScript origins: `http://localhost:5173`
   - Authorized redirect URIs:
     `https://lxiwfmlblrphwefbtboj.supabase.co/auth/v1/callback`
4. Salin **Client ID** dan **Client secret**.

### 2. Dashboard Supabase
1. **Authentication → Sign In / Providers → Google**: aktifkan, tempel Client ID
   dan Client secret, simpan.
2. **Authentication → URL Configuration**:
   - Site URL: `http://localhost:5173`
   - Redirect URLs: tambahkan `http://localhost:5173/**`

Client secret hanya disimpan di Supabase, tidak pernah di repo atau frontend.

## Menjalankan frontend
```bash
cd frontend
cp .env.example .env.local   # berisi URL Supabase + publishable key
npm install
npm run dev
```
Buka <http://localhost:5173> → halaman login muncul → **Lanjutkan dengan Google**.

Tanpa `VITE_SUPABASE_URL`/`VITE_SUPABASE_PUBLISHABLE_KEY`, aplikasi berjalan
tanpa login dan data hanya tersimpan di perangkat.

## Catatan
- Saat pertama login, watchlist dan portofolio yang sudah ada di perangkat
  otomatis dipindahkan ke akun. Setelah itu salinan di akun yang dipakai.
- **Aplikasi desktop Tauri**: Google sering memblokir login di dalam webview
  tertanam. Kalau di jendela Tauri muncul error dari Google, gunakan browser
  untuk sementara; versi desktop perlu alur "buka browser sistem lalu kembali
  ke aplikasi" (deep link), yang belum dibuat.
