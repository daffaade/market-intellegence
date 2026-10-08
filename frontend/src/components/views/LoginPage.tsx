import React, { useState } from 'react';
import { Activity, BarChart3, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../lib/auth';

const GoogleMark = () => (
  <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
    <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z" />
    <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z" />
    <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z" />
    <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z" />
  </svg>
);

const POINTS = [
  { icon: Activity, title: 'Sinyal yang bisa ditelusuri', body: 'Skor peluang dan risiko selalu disertai angka pembanding dan bukti datanya.' },
  { icon: BarChart3, title: 'Fundamental & arus dana', body: 'Laporan keuangan, kepemilikan, dan pergerakan institusi dalam satu halaman.' },
  { icon: ShieldCheck, title: 'Portofolio tersimpan di akun', body: 'Watchlist dan portofolio ikut ke perangkat mana pun Anda masuk.' }
];

export const LoginPage: React.FC = () => {
  const { signInWithGoogle } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async () => {
    setBusy(true);
    setError(null);
    const err = await signInWithGoogle();
    // On success the browser navigates to Google, so only errors land here.
    if (err) {
      setError(err);
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas text-ink grid lg:grid-cols-2">
      <section className="hidden lg:flex flex-col justify-between p-12 border-r border-line bg-surface">
        <div className="flex items-center gap-2">
          <svg width="20" height="20" viewBox="0 0 18 18" aria-hidden="true" className="text-ink">
            <rect x="1" y="9" width="3" height="8" fill="currentColor" />
            <rect x="7.5" y="5" width="3" height="12" fill="currentColor" />
            <rect x="14" y="1" width="3" height="16" fill="var(--accent)" />
          </svg>
          <span className="font-semibold text-[16px] tracking-tight">Marketidex</span>
          <span className="text-[11px] text-ink-3 num">IDX</span>
        </div>

        <div className="max-w-md">
          <h1 className="text-[28px] leading-tight font-semibold tracking-tight">
            Riset saham Indonesia, dihitung dulu lalu dijelaskan.
          </h1>
          <ul className="mt-8 space-y-5">
            {POINTS.map(({ icon: Icon, title, body }) => (
              <li key={title} className="flex gap-3">
                <span className="w-8 h-8 rounded-md bg-accent-soft text-accent flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4" />
                </span>
                <span>
                  <span className="block text-[14px] font-medium">{title}</span>
                  <span className="block text-[13px] text-ink-2 mt-0.5 leading-relaxed">{body}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <p className="text-xs text-ink-3 max-w-md leading-relaxed">
          Informasi dan analisis merupakan hasil pemrosesan data riset dan bukan anjuran investasi personal (bukan rekomendasi beli/jual).
        </p>
      </section>

      <section className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-2 mb-10">
            <span className="font-semibold text-[16px] tracking-tight">Marketidex</span>
            <span className="text-[11px] text-ink-3 num">IDX</span>
          </div>

          <h2 className="text-[22px] font-semibold tracking-tight">Masuk atau daftar</h2>
          <p className="text-[13px] text-ink-2 mt-1.5 leading-relaxed">
            Gunakan akun Google Anda. Akun Marketidex dibuat otomatis saat pertama kali masuk.
          </p>

          <button
            onClick={start}
            disabled={busy}
            className="mt-8 w-full h-11 rounded-md border border-line-strong bg-surface hover:bg-surface-2 transition-colors flex items-center justify-center gap-3 text-[14px] font-medium disabled:opacity-60"
          >
            <GoogleMark />
            {busy ? 'Mengalihkan ke Google…' : 'Lanjutkan dengan Google'}
          </button>

          {error && (
            <p role="alert" className="mt-4 text-[13px] text-down leading-relaxed">
              Gagal memulai login: {error}
            </p>
          )}

          <p className="mt-8 text-xs text-ink-3 leading-relaxed">
            Kami hanya menyimpan nama, email, dan foto profil Google Anda, serta watchlist dan portofolio yang Anda buat.
          </p>
        </div>
      </section>
    </div>
  );
};
