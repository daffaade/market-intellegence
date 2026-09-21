import React from 'react';
import {
  LayoutDashboard,
  Zap,
  Globe2,
  BrainCircuit,
  SlidersHorizontal
} from 'lucide-react';

export type ViewType = 'overview' | 'signals' | 'dashboard' | 'market' | 'ai-portfolio';

interface SidebarProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  anomalyCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onViewChange,
  anomalyCount = 2
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
    <aside className="w-64 glass-panel border-r border-slate-800/80 flex flex-col justify-between py-6 px-3 shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
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

    </aside>
  );
};
