import React, { useEffect, useRef, useState } from 'react';
import { Search, Menu, Moon, Sun, LogOut } from 'lucide-react';
import type { User } from '@supabase/supabase-js';
import { profileOf } from '../lib/auth';
import type { SyncStatus } from '../lib/userData';
import type { DataOrigin } from '../services/mockApi';
import type { Theme } from '../lib/theme';
import { Kbd } from './ui/primitives';
import { cx } from '../lib/ui';

interface NavbarProps {
  onOpenSearch: () => void;
  onOpenPipeline: () => void;
  onToggleMobileNav: () => void;
  dataOrigin: DataOrigin;
  theme: Theme;
  onToggleTheme: () => void;
  loading?: boolean;
  user?: User | null;
  syncStatus?: SyncStatus;
  onSignOut?: () => void;
}

const originCopy: Record<DataOrigin, { label: string; dot: string; title: string }> = {
  backend: {
    label: 'Live',
    dot: 'bg-up',
    title: 'Data berasal dari backend Go'
  },
  dummy: {
    label: 'Simulasi',
    dot: 'bg-warn',
    title: 'Mode data dummy aktif'
  },
  fallback: {
    label: 'Backend offline',
    dot: 'bg-down',
    title: 'Backend tidak merespons, sebagian data diganti dengan data simulasi'
  }
};

export const Navbar: React.FC<NavbarProps> = ({
  onOpenSearch,
  onOpenPipeline,
  onToggleMobileNav,
  dataOrigin,
  theme,
  onToggleTheme,
  loading,
  user,
  syncStatus,
  onSignOut
}) => {
  const origin = originCopy[dataOrigin];

  return (
    <header className="h-12 shrink-0 bg-surface border-b border-line px-3 md:px-4 flex items-center gap-3 relative z-30">
      <button
        onClick={onToggleMobileNav}
        className="md:hidden p-1.5 -ml-1 rounded text-ink-2 hover:bg-surface-2"
        aria-label="Buka navigasi"
      >
        <Menu className="w-4 h-4" />
      </button>

      {/* Wordmark */}
      <div className="flex items-center gap-2 shrink-0 md:w-[204px]">
        <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" className="text-ink">
          <rect x="1" y="9" width="3" height="8" fill="currentColor" />
          <rect x="7.5" y="5" width="3" height="12" fill="currentColor" />
          <rect x="14" y="1" width="3" height="16" fill="var(--accent)" />
        </svg>
        <span className="font-semibold text-[15px] tracking-tight">Marketidex</span>
        <span className="hidden sm:inline text-[11px] text-ink-3 num">IDX</span>
      </div>

      {/* Search trigger — opens the command palette */}
      <button
        onClick={onOpenSearch}
        className="flex-1 max-w-md h-8 px-2.5 flex items-center gap-2 rounded-md border border-line bg-canvas text-ink-3 hover:border-line-strong transition-colors text-left min-w-0"
      >
        <Search className="w-3.5 h-3.5 shrink-0" />
        <span className="text-[13px] truncate">Cari kode atau nama emiten</span>
        <span className="ml-auto hidden sm:flex items-center gap-1">
          <Kbd>/</Kbd>
        </span>
      </button>

      <div className="ml-auto flex items-center gap-1">
        <button
          onClick={onOpenPipeline}
          title={`${origin.title} — klik untuk mengatur sumber data`}
          className="h-8 px-2.5 rounded-md flex items-center gap-2 text-[13px] text-ink-2 hover:bg-surface-2 transition-colors"
        >
          <span className={cx('w-1.5 h-1.5 rounded-full', origin.dot)} />
          <span className="hidden sm:inline">{origin.label}</span>
        </button>
        <button
          onClick={onToggleTheme}
          className="h-8 w-8 rounded-md flex items-center justify-center text-ink-2 hover:bg-surface-2"
          aria-label={theme === 'dark' ? 'Gunakan tema terang' : 'Gunakan tema gelap'}
          title={theme === 'dark' ? 'Tema terang' : 'Tema gelap'}
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
        {user && onSignOut && <AccountMenu user={user} syncStatus={syncStatus} onSignOut={onSignOut} />}
      </div>

      {loading && (
        <div className="absolute left-0 right-0 bottom-[-1px] h-px overflow-hidden">
          <div className="loading-bar h-full w-1/3 bg-accent" />
        </div>
      )}
    </header>
  );
};

const syncCopy: Record<SyncStatus, string> = {
  local: 'Tersimpan di perangkat ini',
  loading: 'Memuat data akun…',
  synced: 'Watchlist & portofolio tersinkron',
  saving: 'Menyimpan…',
  error: 'Gagal sinkron, perubahan tersimpan di perangkat'
};

const AccountMenu: React.FC<{ user: User; syncStatus?: SyncStatus; onSignOut: () => void }> = ({ user, syncStatus, onSignOut }) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { name, email, avatar } = profileOf(user);
  const initials = name.split(/\s+/).map(w => w[0]).slice(0, 2).join('').toUpperCase();

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent | KeyboardEvent) => {
      if (e instanceof KeyboardEvent ? e.key === 'Escape' : !ref.current?.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener('mousedown', close);
    window.addEventListener('keydown', close);
    return () => {
      window.removeEventListener('mousedown', close);
      window.removeEventListener('keydown', close);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative ml-1">
      <button
        onClick={() => setOpen(v => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Akun ${name}`}
        className="w-8 h-8 rounded-full overflow-hidden border border-line flex items-center justify-center bg-accent-soft text-accent text-[11px] font-semibold"
      >
        {avatar ? <img src={avatar} alt="" referrerPolicy="no-referrer" className="w-full h-full object-cover" /> : initials}
      </button>
      {open && (
        <div role="menu" className="absolute right-0 top-10 w-64 bg-surface border border-line-strong rounded-lg shadow-lg overflow-hidden">
          <div className="px-3 py-3 border-b border-line">
            <div className="text-[13px] font-medium text-ink truncate">{name}</div>
            <div className="text-xs text-ink-3 truncate">{email}</div>
            {syncStatus && (
              <div className={cx('text-xs mt-2', syncStatus === 'error' ? 'text-down' : 'text-ink-3')}>{syncCopy[syncStatus]}</div>
            )}
          </div>
          <button
            role="menuitem"
            onClick={onSignOut}
            className="w-full px-3 h-9 flex items-center gap-2 text-[13px] text-ink-2 hover:bg-surface-2 hover:text-ink"
          >
            <LogOut className="w-3.5 h-3.5" /> Keluar
          </button>
        </div>
      )}
    </div>
  );
};
