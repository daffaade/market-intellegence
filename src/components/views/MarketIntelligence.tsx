import React, { useEffect, useMemo, useState } from 'react';
import { ArrowUpRight, ArrowDownRight, Minus, RotateCcw } from 'lucide-react';
import type { MarketOverview, ScreenerFilter, IntelligenceSnapshot, SignalMatrixPoint } from '../../types/api';
import { MOCK_MACRO, MOCK_EVENTS, MOCK_COMPANIES, MOCK_INTELLIGENCE } from '../../services/mockData';
import { apiService } from '../../services/mockApi';
import { SignalMatrix } from '../shared/SignalMatrix';
import { quadrantOf, quadrantShort } from '../../lib/format';
import {
  PageHeader,
  Panel,
  ScoreBar,
  DirectionTag,
  Tag,
  SortHeader,
  EmptyState,
  Button
} from '../ui/primitives';
import { cx } from '../../lib/ui';

interface MarketIntelligenceProps {
  marketOverview: MarketOverview;
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
}

type SortKey = 'symbol' | 'opportunity' | 'risk' | 'anomaly';

const DEFAULT_FILTER = { sector: '', minOpp: 0, maxRisk: 100, divergence: false };

const trendIcon = { UP: ArrowUpRight, DOWN: ArrowDownRight, STABLE: Minus } as const;
const trendLabel = { UP: 'Naik', DOWN: 'Turun', STABLE: 'Stabil' } as const;

export const MarketIntelligence: React.FC<MarketIntelligenceProps> = ({
  marketOverview,
  selectedSymbol,
  onSelectSymbol
}) => {
  const [sector, setSector] = useState(DEFAULT_FILTER.sector);
  const [minOpp, setMinOpp] = useState(DEFAULT_FILTER.minOpp);
  const [maxRisk, setMaxRisk] = useState(DEFAULT_FILTER.maxRisk);
  const [divergence, setDivergence] = useState(DEFAULT_FILTER.divergence);
  const [results, setResults] = useState<IntelligenceSnapshot[]>([]);
  const [searching, setSearching] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>('opportunity');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const sectors = useMemo(
    () => Array.from(new Set([...Object.values(MOCK_COMPANIES).map(c => c.sector), ...marketOverview.sector_summary.map(s => s.sector)])).sort(),
    [marketOverview]
  );

  // Filters apply live; a short debounce keeps slider drags from flooding the backend.
  useEffect(() => {
    let cancelled = false;
    const filter: ScreenerFilter = {
      sector: sector || undefined,
      min_opportunity: minOpp,
      max_risk: maxRisk,
      must_have_divergence: divergence
    };
    setSearching(true);
    const t = setTimeout(async () => {
      const res = await apiService.runScreener(filter);
      if (!cancelled) {
        if (res.status === 'success' && res.data) setResults(res.data);
        setSearching(false);
      }
    }, 200);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [sector, minOpp, maxRisk, divergence]);

  const sorted = useMemo(() => {
    const v = (i: IntelligenceSnapshot) =>
      sortKey === 'symbol' ? i.symbol : sortKey === 'opportunity' ? i.opportunity_score : sortKey === 'risk' ? i.risk_score : i.anomaly_score;
    return [...results].sort((a, b) => {
      const va = v(a);
      const vb = v(b);
      const cmp = typeof va === 'string' ? va.localeCompare(vb as string) : (va as number) - (vb as number);
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [results, sortKey, sortDir]);

  const onSort = (k: SortKey) => {
    if (k === sortKey) setSortDir(d => (d === 'asc' ? 'desc' : 'asc'));
    else {
      setSortKey(k);
      setSortDir(k === 'symbol' ? 'asc' : 'desc');
    }
  };

  const isDefault =
    sector === DEFAULT_FILTER.sector && minOpp === DEFAULT_FILTER.minOpp && maxRisk === DEFAULT_FILTER.maxRisk && divergence === DEFAULT_FILTER.divergence;

  const reset = () => {
    setSector(DEFAULT_FILTER.sector);
    setMinOpp(DEFAULT_FILTER.minOpp);
    setMaxRisk(DEFAULT_FILTER.maxRisk);
    setDivergence(DEFAULT_FILTER.divergence);
  };

  // Matrix is derived from the same intelligence snapshots as everything else,
  // so every emiten appears and quadrants follow one rule.
  const matrix: SignalMatrixPoint[] = useMemo(
    () =>
      Object.values(MOCK_INTELLIGENCE).map(i => ({
        symbol: i.symbol,
        name: MOCK_COMPANIES[i.symbol]?.name ?? i.symbol,
        sector: MOCK_COMPANIES[i.symbol]?.sector ?? '',
        opportunity_score: i.opportunity_score,
        risk_score: i.risk_score,
        direction: i.direction,
        is_anomaly: i.is_anomaly,
        quadrant: quadrantOf(i.opportunity_score, i.risk_score)
      })),
    []
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Pasar"
        title="Screener & sektor"
        description="Saring emiten berdasarkan skor peluang dan risiko, lalu lihat posisinya di peta kuadran dan konteks makro."
      />

      <Panel
        title="Screener"
        meta={searching ? 'Memuat…' : `${results.length} emiten cocok`}
        actions={
          !isDefault && (
            <Button variant="ghost" size="sm" onClick={reset}>
              <RotateCcw className="w-3 h-3" /> Atur ulang
            </Button>
          )
        }
        flush
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-4 p-4 border-b border-line">
          <label className="block">
            <span className="text-xs text-ink-3">Sektor</span>
            <select
              value={sector}
              onChange={e => setSector(e.target.value)}
              className="mt-1.5 w-full h-8 px-2 rounded-md bg-canvas border border-line text-[13px] text-ink outline-none focus:border-accent"
            >
              <option value="">Semua sektor</option>
              {sectors.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>

          <label className="block">
            <span className="flex justify-between text-xs text-ink-3">
              Peluang minimum <span className="num text-ink">{minOpp}</span>
            </span>
            <input type="range" min={0} max={100} value={minOpp} onChange={e => setMinOpp(Number(e.target.value))} className="mt-2.5 w-full" />
          </label>

          <label className="block">
            <span className="flex justify-between text-xs text-ink-3">
              Risiko maksimum <span className="num text-ink">{maxRisk}</span>
            </span>
            <input type="range" min={0} max={100} value={maxRisk} onChange={e => setMaxRisk(Number(e.target.value))} className="mt-2.5 w-full" />
          </label>

          <label className="flex items-center gap-2 text-[13px] text-ink-2 cursor-pointer sm:pt-5">
            <input
              type="checkbox"
              checked={divergence}
              onChange={e => setDivergence(e.target.checked)}
              className="w-4 h-4 accent-[var(--accent)]"
            />
            Hanya dengan anomali / divergensi
          </label>
        </div>

        <div className={cx('overflow-x-auto transition-opacity', searching && 'opacity-60')}>
          <table className="w-full text-[13px]">
            <thead className="border-b border-line">
              <tr className="text-left">
                <SortHeader label="Emiten" sortKey="symbol" current={sortKey} dir={sortDir} onSort={onSort} />
                <th className="px-4 h-9 font-medium text-xs text-ink-3">Arah</th>
                <SortHeader label="Peluang" sortKey="opportunity" current={sortKey} dir={sortDir} onSort={onSort} />
                <SortHeader label="Risiko" sortKey="risk" current={sortKey} dir={sortDir} onSort={onSort} />
                <SortHeader label="Anomali" sortKey="anomaly" current={sortKey} dir={sortDir} onSort={onSort} />
                <th className="px-4 h-9 font-medium text-xs text-ink-3">Kuadran</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {sorted.map(item => (
                <tr key={item.symbol} onClick={() => onSelectSymbol(item.symbol)} className="hover:bg-surface-2 cursor-pointer">
                  <td className="px-4 h-11">
                    <div className="flex items-baseline gap-2.5 min-w-[180px]">
                      <span className="num font-medium text-ink">{item.symbol}</span>
                      <span className="text-ink-2 truncate">{MOCK_COMPANIES[item.symbol]?.name}</span>
                    </div>
                  </td>
                  <td className="px-4 h-11"><DirectionTag direction={item.direction} /></td>
                  <td className="px-4 h-11"><ScoreBar value={item.opportunity_score} width="w-16" /></td>
                  <td className="px-4 h-11"><ScoreBar value={item.risk_score} tone="risk" width="w-16" /></td>
                  <td className="px-4 h-11">
                    {item.is_anomaly || item.divergence_detected ? (
                      <Tag tone="warn">{item.is_anomaly ? `Skor ${item.anomaly_score}` : 'Divergensi'}</Tag>
                    ) : (
                      <span className="text-ink-3">—</span>
                    )}
                  </td>
                  <td className="px-4 h-11 text-ink-2 whitespace-nowrap">
                    {quadrantShort[quadrantOf(item.opportunity_score, item.risk_score)]}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!searching && sorted.length === 0 && (
            <EmptyState title="Tidak ada emiten yang memenuhi kriteria">
              Longgarkan batas skor atau hapus filter sektor.
            </EmptyState>
          )}
        </div>
      </Panel>

      <SignalMatrix data={matrix} selectedSymbol={selectedSymbol} onSelectSymbol={onSelectSymbol} />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Panel title="Indikator makro" flush>
          <ul className="divide-y divide-line">
            {MOCK_MACRO.map(m => {
              const Icon = trendIcon[m.trend];
              return (
                <li key={m.name} className="px-4 py-3 flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="text-[13px] text-ink">{m.name}</div>
                    <div className="text-xs text-ink-3 mt-0.5">{m.correlation_with_market}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="num text-[15px] text-ink">{m.value}</div>
                    <div className="text-xs text-ink-3 inline-flex items-center gap-0.5">
                      <Icon className="w-3 h-3" /> {trendLabel[m.trend]}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </Panel>

        <Panel title="Dampak peristiwa" meta="Reaksi harga" flush>
          <ul className="divide-y divide-line">
            {[...MOCK_EVENTS].sort((a, b) => b.date.localeCompare(a.date)).map(e => (
              <li key={e.event_name} className="px-4 py-3 flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="text-[13px] text-ink">{e.event_name}</div>
                  <div className="text-xs text-ink-3 mt-0.5">
                    <span className="num">{e.date}</span> · {e.category}
                  </div>
                </div>
                <div className={cx('num text-[15px] shrink-0', e.price_reaction_pct >= 0 ? 'text-up' : 'text-down')}>
                  {e.price_reaction_pct >= 0 ? '+' : '−'}{Math.abs(e.price_reaction_pct)}%
                </div>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
};
