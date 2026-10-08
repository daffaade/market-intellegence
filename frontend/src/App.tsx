import { useState, useEffect, useRef, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, type ViewType } from './components/Sidebar';
import { SignalIntelligence } from './components/views/SignalIntelligence';
import { CompanyDashboard } from './components/views/CompanyDashboard';
import { MarketIntelligence } from './components/views/MarketIntelligence';
import { PortfolioAndAi } from './components/views/PortfolioAndAi';
import { MarketOverviewView } from './components/views/MarketOverview';
import { SectorsPipelineInspector } from './components/shared/SectorsPipelineInspector';
import { EmitenSwitcherModal } from './components/shared/EmitenSwitcherModal';
import type { Company, IntelligenceSnapshot, MarketOverview } from './types/api';
import {
  apiService,
  isDummyMode,
  setDummyMode,
  DATA_ORIGIN_EVENT,
  type DataOrigin
} from './services/mockApi';
import { MOCK_PIPELINE_STAGES, MOCK_SIGNAL_OUTPUTS } from './services/mockData';
import { ThemeContext, readInitialTheme, applyTheme, type Theme } from './lib/theme';
import { useAuth } from './lib/auth';
import { authEnabled } from './lib/supabase';
import { useUserData } from './lib/userData';
import { LoginPage } from './components/views/LoginPage';

const VIEWS: ViewType[] = ['overview', 'signals', 'dashboard', 'market', 'ai-portfolio'];

/** Route lives in the hash as #/<view>/<symbol> so pages can be linked and the back button works. */
const parseHash = (): { view: ViewType; symbol: string } => {
  const [, view, symbol] = window.location.hash.split('/');
  return {
    view: VIEWS.includes(view as ViewType) ? (view as ViewType) : 'overview',
    symbol: symbol && /^[A-Z]{2,5}$/.test(symbol.toUpperCase()) ? symbol.toUpperCase() : 'BBCA'
  };
};

function App() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>(() => parseHash().symbol);
  const [currentView, setCurrentView] = useState<ViewType>(() => parseHash().view);

  const [theme, setTheme] = useState<Theme>(readInitialTheme);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState<boolean>(false);
  const [isPipelineOpen, setIsPipelineOpen] = useState<boolean>(false);
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);
  const [useDummyData, setUseDummyData] = useState<boolean>(() => isDummyMode());
  const auth = useAuth();
  const { portfolio, setPortfolio, watchlist, setWatchlist, status: syncStatus } = useUserData(auth.user);

  const [companies, setCompanies] = useState<Company[]>([]);
  const [company, setCompany] = useState<Company | null>(null);
  const [intelligence, setIntelligence] = useState<IntelligenceSnapshot | null>(null);
  const [marketOverview, setMarketOverview] = useState<MarketOverview | null>(null);
  const [allIntelligence, setAllIntelligence] = useState<IntelligenceSnapshot[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [dataOrigin, setDataOrigin] = useState<DataOrigin>(useDummyData ? 'dummy' : 'backend');

  const mainRef = useRef<HTMLElement>(null);
  const originsThisLoad = useRef<Set<DataOrigin>>(new Set());

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    const next = `#/${currentView}/${selectedSymbol}`;
    if (window.location.hash !== next) window.history.pushState(null, '', next);
  }, [currentView, selectedSymbol]);

  useEffect(() => {
    const onPop = () => {
      const { view, symbol } = parseHash();
      setCurrentView(view);
      setSelectedSymbol(symbol);
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  // Collect the origin of every response in a load so a single fallback is not
  // hidden by a later successful call.
  useEffect(() => {
    const onOrigin = (e: Event) => originsThisLoad.current.add((e as CustomEvent<DataOrigin>).detail);
    window.addEventListener(DATA_ORIGIN_EVENT, onOrigin);
    return () => window.removeEventListener(DATA_ORIGIN_EVENT, onOrigin);
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    originsThisLoad.current = new Set();
    try {
      const [compRes, intelRes, mktRes, allRes] = await Promise.all([
        apiService.getCompany(selectedSymbol),
        apiService.getIntelligence(selectedSymbol),
        apiService.getMarketOverview(),
        apiService.getAllIntelligence()
      ]);

      if (compRes.data) setCompany(compRes.data);
      if (intelRes.data) setIntelligence(intelRes.data);
      if (mktRes.data) setMarketOverview(mktRes.data);
      if (allRes.data) setAllIntelligence(allRes.data);
    } finally {
      const seen = originsThisLoad.current;
      setDataOrigin(seen.has('fallback') ? 'fallback' : seen.has('dummy') ? 'dummy' : 'backend');
      setLoading(false);
    }
  }, [selectedSymbol]);

  useEffect(() => {
    loadData();
  }, [loadData, useDummyData]);

  useEffect(() => {
    apiService.getCompanies().then(res => {
      if (res.data) setCompanies(res.data);
    });
  }, [useDummyData]);

  // Global shortcuts: "/" or Ctrl/Cmd+K opens search.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const typing = target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable);
      if ((e.key === 'k' && (e.metaKey || e.ctrlKey)) || (e.key === '/' && !typing)) {
        e.preventDefault();
        setIsSearchOpen(true);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const navigate = (view: ViewType) => {
    setCurrentView(view);
    setIsMobileNavOpen(false);
    mainRef.current?.scrollTo({ top: 0 });
  };

  const handleToggleDummy = (enabled: boolean) => {
    setDummyMode(enabled);
    setUseDummyData(enabled);
  };

  // Picking a stock from a market-wide view opens its signal page; from a
  // stock-level view it keeps you on the same page.
  const handleSelectSymbol = (sym: string) => {
    setSelectedSymbol(sym);
    if (currentView === 'overview' || currentView === 'market') {
      navigate('signals');
    } else {
      mainRef.current?.scrollTo({ top: 0 });
    }
  };

  const toggleWatchlist = (symbol: string) => {
    setWatchlist(prev => (prev.includes(symbol) ? prev.filter(s => s !== symbol) : [...prev, symbol]));
  };

  const ready = company && intelligence && marketOverview;
  const openSearch = () => setIsSearchOpen(true);

  return (
    <ThemeContext.Provider value={theme}>
      <div className="h-screen flex flex-col bg-canvas text-ink">
        <Navbar
          onOpenSearch={openSearch}
          onOpenPipeline={() => setIsPipelineOpen(true)}
          onToggleMobileNav={() => setIsMobileNavOpen(v => !v)}
          dataOrigin={dataOrigin}
          theme={theme}
          onToggleTheme={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))}
          loading={loading && !!ready}
          user={auth.user}
          syncStatus={syncStatus}
          onSignOut={auth.signOut}
        />

        <div className="flex-1 flex min-h-0 relative">
          <Sidebar
            currentView={currentView}
            onViewChange={navigate}
            anomalyCount={marketOverview?.detected_anomalies.length ?? 0}
            isOpen={isSidebarOpen}
            onToggle={() => setIsSidebarOpen(prev => !prev)}
            isMobileOpen={isMobileNavOpen}
            onCloseMobile={() => setIsMobileNavOpen(false)}
            company={company}
            watchlist={watchlist}
            allIntelligence={allIntelligence}
            companies={companies}
            selectedSymbol={selectedSymbol}
            onSelectSymbol={sym => {
              setSelectedSymbol(sym);
              if (currentView === 'overview' || currentView === 'market') navigate('signals');
              setIsMobileNavOpen(false);
            }}
          />

          <main ref={mainRef} className="flex-1 overflow-y-auto min-w-0">
            <div className="max-w-[1320px] mx-auto px-4 md:px-8 py-6 md:py-8">
              {!ready ? (
                <LoadingSkeleton />
              ) : (
                <>
                  {currentView === 'overview' && (
                    <MarketOverviewView
                      marketOverview={marketOverview}
                      companies={companies}
                      allIntelligence={allIntelligence}
                      onSelectSymbol={handleSelectSymbol}
                      onNavigate={navigate}
                      watchlist={watchlist}
                      onToggleWatchlist={toggleWatchlist}
                    />
                  )}

                  {currentView === 'signals' && (
                    <SignalIntelligence
                      intelligence={intelligence}
                      company={company}
                      signalOutput={MOCK_SIGNAL_OUTPUTS[company.symbol]}
                      onOpenSearch={openSearch}
                      isWatched={watchlist.includes(company.symbol)}
                      onToggleWatchlist={toggleWatchlist}
                    />
                  )}

                  {currentView === 'dashboard' && (
                    <CompanyDashboard
                      company={company}
                      intelligence={intelligence}
                      onOpenSearch={openSearch}
                      isWatched={watchlist.includes(company.symbol)}
                      onToggleWatchlist={toggleWatchlist}
                    />
                  )}

                  {currentView === 'market' && (
                    <MarketIntelligence
                      marketOverview={marketOverview}
                      companies={companies}
                      allIntelligence={allIntelligence}
                      selectedSymbol={selectedSymbol}
                      onSelectSymbol={handleSelectSymbol}
                    />
                  )}

                  {currentView === 'ai-portfolio' && (
                    <PortfolioAndAi
                      intelligence={intelligence}
                      company={company}
                      companies={companies}
                      allIntelligence={allIntelligence}
                      holdings={portfolio}
                      onChangeHoldings={setPortfolio}
                      syncedToAccount={!!auth.user}
                      onSelectSymbol={handleSelectSymbol}
                    />
                  )}
                </>
              )}
            </div>
          </main>
        </div>

        {isSearchOpen && (
          <EmitenSwitcherModal
            isOpen={isSearchOpen}
            onClose={() => setIsSearchOpen(false)}
            companies={companies}
            allIntelligence={allIntelligence}
            currentSymbol={selectedSymbol}
            watchlist={watchlist}
            onSelectSymbol={handleSelectSymbol}
          />
        )}

        <SectorsPipelineInspector
          stages={MOCK_PIPELINE_STAGES}
          isOpen={isPipelineOpen}
          onClose={() => setIsPipelineOpen(false)}
          useDummyData={useDummyData}
          dataOrigin={dataOrigin}
          onToggleDummy={handleToggleDummy}
        />
      </div>
    </ThemeContext.Provider>
  );
}

const LoadingSkeleton = () => (
  <div className="animate-pulse space-y-6" aria-busy="true" aria-label="Memuat data">
    <div className="space-y-2 pb-5 border-b border-line">
      <div className="h-3 w-24 bg-surface-2 rounded" />
      <div className="h-6 w-64 bg-surface-2 rounded" />
      <div className="h-3 w-96 max-w-full bg-surface-2 rounded" />
    </div>
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {[0, 1, 2, 3].map(i => <div key={i} className="h-20 bg-surface border border-line rounded-lg" />)}
    </div>
    <div className="h-80 bg-surface border border-line rounded-lg" />
  </div>
);

/** Requires sign-in when Supabase is configured; without it the app runs local-only. */
export function AuthGate() {
  const { ready, user } = useAuth();
  // App applies the theme itself; the login screen needs it too.
  useEffect(() => applyTheme(readInitialTheme()), []);
  if (!authEnabled) return <App />;
  if (!ready) return <div className="h-screen bg-canvas" aria-busy="true" />;
  return user ? <App /> : <LoginPage />;
}

export default AuthGate;
