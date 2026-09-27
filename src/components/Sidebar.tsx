import React from 'react';
import {
  LayoutDashboard,
  Zap,
  Globe2,
  BrainCircuit,
  SlidersHorizontal,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-react';

export type ViewType = 'overview' | 'signals' | 'dashboard' | 'market' | 'ai-portfolio';

interface SidebarProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  anomalyCount?: number;
  isOpen?: boolean;
  onToggle?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onViewChange,
  anomalyCount = 2,
  isOpen = true,
  onToggle
}) => {
  const navGroups = [
    {
      title: 'P0 - Core Analytics',
      items: [
        {
          id: 'overview' as ViewType,
          label: 'Market Overview',
          subtitle: 'Top Opportunities & Risks',
          icon: Globe2
        },
        {
          id: 'signals' as ViewType,
          label: 'Core Signal Engine',
          subtitle: 'Anomali & Derived Signals',
          icon: Zap,
          badge: `${anomalyCount} Anomali`,
          badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30'
        },
        {
          id: 'dashboard' as ViewType,
          label: 'Company Intelligence',
          subtitle: 'Valuasi, Growth, Smart Money',
          icon: LayoutDashboard
        }
      ]
    },
    {
      title: 'P1 - Discovery',
      items: [
        {
          id: 'market' as ViewType,
          label: 'Sector & Screener',
          subtitle: 'Intelligence Scanner',
          icon: SlidersHorizontal
        }
      ]
    },
    {
      title: 'P2 - Advanced',
      items: [
        {
          id: 'ai-portfolio' as ViewType,
          label: 'Portfolio & AI Summary',
          subtitle: 'Risk Analysis & AI Research',
          icon: BrainCircuit
        }
      ]
    }
  ];

  return (
    <aside
      className={`glass-panel border-r border-slate-800/80 flex flex-col justify-between py-4 shrink-0 min-h-[calc(100vh-4rem)] transition-all duration-300 ease-in-out ${
        isOpen ? 'w-64 px-3' : 'w-14 px-2 items-center'
      }`}
    >
      <div className="space-y-4 w-full">
        {/* Top Header of Sidebar with Toggle Button */}
        <div
          className={`flex items-center pb-3 border-b border-slate-800/60 transition-all ${
            isOpen ? 'justify-between px-1' : 'justify-center'
          }`}
        >
          {isOpen && (
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-widest">
                Navigasi
              </span>
            </div>
          )}
          {onToggle && (
            <button
              onClick={onToggle}
              title={isOpen ? "Sembunyikan Sidebar" : "Tampilkan Sidebar"}
              className={`p-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-cyan-400 border border-slate-800 hover:border-slate-700 transition-all cursor-pointer group ${
                !isOpen ? 'text-cyan-400 shadow-lg shadow-cyan-500/10' : ''
              }`}
              aria-label="Toggle Sidebar"
            >
              {isOpen ? (
                <PanelLeftClose className="w-4 h-4 transition-transform group-hover:-translate-x-0.5" />
              ) : (
                <PanelLeftOpen className="w-4 h-4 text-cyan-400 transition-transform group-hover:scale-110" />
              )}
            </button>
          )}
        </div>

        {/* Navigation Content (Only shown when expanded) */}
        {isOpen && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {navGroups.map((group, gIdx) => (
              <div key={gIdx} className="space-y-2">
                <div className="px-3">
                  <h2 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono">
                    {group.title}
                  </h2>
                </div>
                <nav className="space-y-1">
                  {group.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = currentView === item.id;
                    return (
                      <button
                        key={item.id}
                        onClick={() => onViewChange(item.id)}
                        className={`w-full text-left px-3.5 py-3 rounded-xl transition-all duration-200 flex items-start space-x-3 group relative ${
                          isActive
                            ? 'bg-gradient-to-r from-cyan-500/15 to-blue-500/10 text-cyan-300 border border-cyan-500/30 shadow-lg shadow-cyan-500/5'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
                        }`}
                      >
                        {isActive && (
                          <span className="absolute left-0 top-3 bottom-3 w-1 bg-cyan-400 rounded-r-full shadow-glow" />
                        )}
                        <Icon
                          className={`w-5 h-5 mt-0.5 shrink-0 transition-colors ${
                            isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-slate-200'
                          }`}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold tracking-wide truncate">
                              {item.label}
                            </span>
                            {item.badge && (
                              <span
                                className={`text-[9px] font-mono px-1.5 py-0.5 rounded-full border ${item.badgeColor}`}
                              >
                                {item.badge}
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] text-slate-400 block truncate mt-0.5">
                            {item.subtitle}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </nav>
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
};


