import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, type ViewType } from './components/Sidebar';
import { SignalIntelligence } from './components/views/SignalIntelligence';
import { CompanyDashboard } from './components/views/CompanyDashboard';
import { MarketIntelligence } from './components/views/MarketIntelligence';
import { PortfolioAndAi } from './components/views/PortfolioAndAi';
import { MarketOverviewView } from './components/views/MarketOverview';
import { SectorsPipelineInspector } from './components/shared/SectorsPipelineInspector';
import type { Company, IntelligenceSnapshot, MarketOverview } from './types/api';
import { apiService } from './services/mockApi';
import { MOCK_PIPELINE_STAGES, MOCK_SIGNAL_OUTPUTS } from './services/mockData';
import { Loader2 } from 'lucide-react';

export function App() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('BBCA');
  const [currentView, setCurrentView] = useState<ViewType>('overview');
  
  // New States
  const [isPipelineOpen, setIsPipelineOpen] = useState<boolean>(false);
  const [watchlist, setWatchlist] = useState<string[]>(['BBCA', 'TLKM']);
  
  const [company, setCompany] = useState<Company | null>(null);
  const [intelligence, setIntelligence] = useState<IntelligenceSnapshot | null>(null);
  const [marketOverview, setMarketOverview] = useState<MarketOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Fetch initial data & handle symbol changes
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [compRes, intelRes, mktRes] = await Promise.all([
        apiService.getCompany(selectedSymbol),
        apiService.getIntelligence(selectedSymbol),
        apiService.getMarketOverview()
      ]);

      if (compRes.data) setCompany(compRes.data);
      if (intelRes.data) setIntelligence(intelRes.data);
      if (mktRes.data) setMarketOverview(mktRes.data);
      setLoading(false);
    }

    loadData();
  }, [selectedSymbol]);

  const handleSelectSymbol = (sym: string) => {
    setSelectedSymbol(sym);
    if (currentView === 'overview') {
      setCurrentView('signals'); // Auto-navigate to signals when searching specific emiten from overview
    }
  };

  const toggleWatchlist = (symbol: string) => {
    setWatchlist(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      {/* Top Navigation */}
      <Navbar
        activeView={currentView}
        onOpenPipeline={() => setIsPipelineOpen(true)}
        onSelectSymbol={handleSelectSymbol}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          currentView={currentView}
          onViewChange={setCurrentView}
          anomalyCount={marketOverview?.detected_anomalies.length || 2}
        />

        {/* Main Workspace Area */}
        <main className="flex-1 p-6 overflow-y-auto max-h-[calc(100vh-4rem)]">
          {loading || !company || !intelligence || !marketOverview ? (
            <div className="h-96 flex flex-col items-center justify-center space-y-4">
              <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
              <span className="text-xs font-mono text-slate-400 tracking-wider">
                MEMPROSES DATA INTELIJEN PASAR...
              </span>
            </div>
          ) : (
            <>
              {currentView === 'overview' && (
                <MarketOverviewView
                  marketOverview={marketOverview}
                  onSelectSymbol={handleSelectSymbol}
                  onNavigate={setCurrentView}
                  watchlist={watchlist}
                  onToggleWatchlist={toggleWatchlist}
                />
              )}

              {currentView === 'signals' && (
                <SignalIntelligence
                  intelligence={intelligence}
                  company={company}
                  signalOutput={MOCK_SIGNAL_OUTPUTS[company.symbol]}
                />
              )}

              {currentView === 'dashboard' && (
                <CompanyDashboard
                  company={company}
                />
              )}

              {currentView === 'market' && (
                <MarketIntelligence
                  marketOverview={marketOverview}
                  onSelectSymbol={handleSelectSymbol}
                />
              )}

              {currentView === 'ai-portfolio' && (
                <PortfolioAndAi
                  intelligence={intelligence}
                  company={company}
                />
              )}
            </>
          )}
        </main>
      </div>

      <SectorsPipelineInspector
        stages={MOCK_PIPELINE_STAGES}
        isOpen={isPipelineOpen}
        onClose={() => setIsPipelineOpen(false)}
      />
    </div>
  );
}

export default App;
