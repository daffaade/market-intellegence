import React from 'react';
import { Search, Menu, Moon, Sun } from 'lucide-react';
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
  loading
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
      </div>

      {loading && (
        <div className="absolute left-0 right-0 bottom-[-1px] h-px overflow-hidden">
          <div className="loading-bar h-full w-1/3 bg-accent" />
        </div>
      )}
    </header>
  );
};
