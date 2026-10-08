import React from 'react';
import {
  LayoutGrid,
  Activity,
  FileBarChart,
  SlidersHorizontal,
  Briefcase,
  PanelLeftClose,
  PanelLeftOpen,
  Star,
  PieChart
} from 'lucide-react';
import type { Company, IntelligenceSnapshot } from '../types/api';
import { cx } from '../lib/ui';

export type ViewType = 'overview' | 'signals' | 'dashboard' | 'market' | 'sectors' | 'ai-portfolio';

interface SidebarProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  anomalyCount: number;
  isOpen: boolean;
  onToggle: () => void;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
  company: Company | null;
  watchlist: string[];
  /** Latest snapshot per emiten, for the watchlist score/direction. */
  allIntelligence: IntelligenceSnapshot[];
  companies: Company[];
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
}

type NavItem = { id: ViewType; label: string; icon: React.ElementType; count?: number };

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onViewChange,
  anomalyCount,
  isOpen,
  onToggle,
  isMobileOpen,
  onCloseMobile,
  company,
  watchlist,
  allIntelligence,
  companies,
  selectedSymbol,
  onSelectSymbol
}) => {
  const marketItems: NavItem[] = [
    { id: 'overview', label: 'Ringkasan pasar', icon: LayoutGrid },
    { id: 'market', label: 'Screener & makro', icon: SlidersHorizontal },
    { id: 'sectors', label: 'Sektor & konsumen', icon: PieChart }
  ];
  const emitenItems: NavItem[] = [
    { id: 'signals', label: 'Sinyal', icon: Activity, count: anomalyCount },
    { id: 'dashboard', label: 'Fundamental', icon: FileBarChart }
  ];
  const portfolioItems: NavItem[] = [{ id: 'ai-portfolio', label: 'Portofolio & riset', icon: Briefcase }];

  // On mobile the drawer is always shown expanded.
  const expanded = isOpen || isMobileOpen;

  const renderItem = (item: NavItem) => {
    const Icon = item.icon;
    const active = currentView === item.id;
    return (
      <button
        key={item.id}
        onClick={() => onViewChange(item.id)}
        title={!expanded ? item.label : undefined}
        aria-current={active ? 'page' : undefined}
        className={cx(
          'w-full flex items-center gap-2.5 h-8 rounded-md text-[13px] transition-colors',
          expanded ? 'px-2.5' : 'justify-center',
          active ? 'bg-surface-2 text-ink font-medium' : 'text-ink-2 hover:text-ink hover:bg-surface-2/60'
        )}
      >
        <Icon className={cx('w-4 h-4 shrink-0', active ? 'text-accent' : 'text-ink-3')} />
        {expanded && <span className="truncate">{item.label}</span>}
        {expanded && item.count ? (
          <span className="ml-auto num text-[11px] text-warn" title={`${item.count} anomali terdeteksi di pasar`}>
            {item.count}
          </span>
        ) : null}
      </button>
    );
  };

  const groupLabel = (text: React.ReactNode) =>
    expanded ? <div className="px-2.5 pt-5 pb-1.5 text-[11px] text-ink-3">{text}</div> : <div className="h-4" />;

  return (
    <>
      {isMobileOpen && (
        <div className="fixed inset-0 top-12 z-20 bg-black/40 md:hidden" onClick={onCloseMobile} aria-hidden="true" />
      )}
      <aside
        className={cx(
          'bg-surface border-r border-line flex flex-col shrink-0 overflow-y-auto no-scrollbar transition-[width] duration-200',
          'fixed md:static top-12 bottom-0 left-0 z-20 md:z-auto',
          isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
          expanded ? 'w-[228px] px-2' : 'w-[52px] px-1.5'
        )}
      >
        <nav className="flex-1 pt-1" aria-label="Navigasi utama">
          {groupLabel('Pasar')}
          <div className="space-y-0.5">{marketItems.map(renderItem)}</div>

          {groupLabel(
            <span className="flex items-center justify-between">
              <span>Emiten</span>
              {company && <span className="num text-ink-2">{company.symbol}</span>}
            </span>
          )}
          <div className="space-y-0.5">{emitenItems.map(renderItem)}</div>

          {groupLabel('Portofolio')}
          <div className="space-y-0.5">{portfolioItems.map(renderItem)}</div>

          {expanded && (
            <>
              <div className="px-2.5 pt-5 pb-1.5 text-[11px] text-ink-3 flex items-center justify-between">
                <span>Watchlist</span>
                <span className="num">{watchlist.length}</span>
              </div>
              {watchlist.length === 0 ? (
                <p className="px-2.5 text-xs text-ink-3 leading-relaxed">
                  Tandai emiten dengan <Star className="inline w-3 h-3 -mt-0.5" /> untuk memantau di sini.
                </p>
              ) : (
                <ul className="space-y-0.5">
                  {watchlist.map(sym => {
                    const intel = allIntelligence.find(i => i.symbol === sym);
                    const active = sym === selectedSymbol;
                    return (
                      <li key={sym}>
                        <button
                          onClick={() => onSelectSymbol(sym)}
                          title={companies.find(c => c.symbol === sym)?.name}
                          className={cx(
                            'w-full h-7 px-2.5 rounded-md flex items-center gap-2 text-[13px] transition-colors',
                            active ? 'bg-surface-2 text-ink' : 'text-ink-2 hover:bg-surface-2/60 hover:text-ink'
                          )}
                        >
                          <span className="num font-medium">{sym}</span>
                          {intel && (
                            <span
                              className={cx(
                                'ml-auto num text-xs',
                                intel.direction === 'BULLISH' ? 'text-up' : intel.direction === 'BEARISH' ? 'text-down' : 'text-ink-3'
                              )}
                            >
                              {intel.opportunity_score}
                            </span>
                          )}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </>
          )}
        </nav>

        <div className={cx('py-2 border-t border-line hidden md:flex', expanded ? 'justify-end' : 'justify-center')}>
          <button
            onClick={onToggle}
            title={isOpen ? 'Ciutkan sidebar' : 'Lebarkan sidebar'}
            aria-label={isOpen ? 'Ciutkan sidebar' : 'Lebarkan sidebar'}
            className="p-1.5 rounded-md text-ink-3 hover:text-ink hover:bg-surface-2"
          >
            {isOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
          </button>
        </div>
      </aside>
    </>
  );
};
