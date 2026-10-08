import React, { useEffect, useMemo, useState } from 'react';
import { RotateCcw } from 'lucide-react';
import type { Company, MarketOverview, ScreenerFilter, IntelligenceSnapshot, SignalMatrixPoint } from '../../types/api';
import { useRemote } from '../../lib/useRemote';
import { RemoteBody, SourceNote, formatDay } from '../shared/RemoteState';
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
  companies: Company[];
  /** Latest snapshot for every emiten, used for the quadrant matrix. */
  allIntelligence: IntelligenceSnapshot[];
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
}

type SortKey = 'symbol' | 'opportunity' | 'risk' | 'anomaly';

const DEFAULT_FILTER = { sector: '', minOpp: 0, maxRisk: 100, divergence: false };

const ChangePct: React.FC<{ value: number | null; label: string }> = ({ value, label }) => (
  <span className="text-xs text-ink-3">
    {label}{' '}
    {value === null ? (
      '—'
    ) : (
      <span className={cx('num', value >= 0 ? 'text-up' : 'text-down')}>
        {value >= 0 ? '+' : '−'}{Math.abs(value).toLocaleString('id-ID', { maximumFractionDigits: 1 })}%
      </span>
    )}
  </span>
);

/** Tiny inline trend line; neutral ink so it doesn't compete with the numbers. */
const Sparkline: React.FC<{ values: number[] }> = ({ values }) => {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * 80},${22 - ((v - min) / span) * 20}`).join(' ');
  return (
    <svg viewBox="0 0 80 24" className="w-20 h-6 text-ink-3" aria-hidden="true">
      <polyline points={pts} fill="none" stroke="currentColor" strokeWidth="1.25" strokeLinejoin="round" />
    </svg>
  );
};

const formatMacroValue = (v: number, unit: string) =>
  unit === 'rupiah'
    ? `Rp ${v.toLocaleString('id-ID', { maximumFractionDigits: 0 })}`
    : v.toLocaleString('id-ID', { maximumFractionDigits: 2 });

export const MarketIntelligence: React.FC<MarketIntelligenceProps> = ({
  marketOverview,
  companies,
  allIntelligence,
  selectedSymbol,
  onSelectSymbol
}) => {
  const macro = useRemote(() => apiService.getMacroSnapshot(), []);
  const events = useRemote(() => apiService.getCorporateEvents(selectedSymbol), [selectedSymbol]);

  const companyBySymbol = useMemo(() => new Map(companies.map(c => [c.symbol, c])), [companies]);

  const [sector, setSector] = useState(DEFAULT_FILTER.sector);
  const [minOpp, setMinOpp] = useState(DEFAULT_FILTER.minOpp);
  const [maxRisk, setMaxRisk] = useState(DEFAULT_FILTER.maxRisk);
  const [divergence, setDivergence] = useState(DEFAULT_FILTER.divergence);
  const [results, setResults] = useState<IntelligenceSnapshot[]>([]);
  const [searching, setSearching] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>('opportunity');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const sectors = useMemo(
    () => Array.from(new Set([...companies.map(c => c.sector), ...marketOverview.sector_summary.map(s => s.sector)])).filter(Boolean).sort(),
    [companies, marketOverview]
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
      allIntelligence.map(i => ({
        symbol: i.symbol,
        name: companyBySymbol.get(i.symbol)?.name ?? i.symbol,
        sector: companyBySymbol.get(i.symbol)?.sector ?? '',
        opportunity_score: i.opportunity_score,
        risk_score: i.risk_score,
        direction: i.direction,
        is_anomaly: i.is_anomaly,
        quadrant: quadrantOf(i.opportunity_score, i.risk_score)
      })),
    [allIntelligence, companyBySymbol]
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
                      <span className="text-ink-2 truncate">{companyBySymbol.get(item.symbol)?.name}</span>
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
        <Panel title="Indikator pasar & makro" meta="Perubahan 1 bulan dan 1 tahun" flush>
          <RemoteBody remote={macro} errorTitle="Indikator makro belum bisa dimuat">
            {data => (
              <>
                <ul className="divide-y divide-line">
                  {data.indicators.map(m => (
                    <li key={m.key} className="px-4 py-3 flex items-center justify-between gap-4">
                      <div className="min-w-0">
                        <div className="text-[13px] text-ink">{m.name}</div>
                        <div className="flex gap-3 mt-0.5">
                          <ChangePct label="1 bln" value={m.change_1m_pct} />
                          <ChangePct label="1 thn" value={m.change_1y_pct} />
                        </div>
                      </div>
                      <div className="flex items-center gap-4 shrink-0">
                        <Sparkline values={m.sparkline} />
                        <div className="text-right w-28">
                          <div className="num text-[15px] text-ink">{formatMacroValue(m.value, m.unit)}</div>
                          <div className="text-xs text-ink-3">{m.unit === 'rupiah' ? 'per USD' : m.unit}</div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
                <div className="px-4 py-2.5 border-t border-line">
                  <SourceNote source="Yahoo Finance" date={data.indicators[0]?.date}>
                    BI-Rate & inflasi butuh API key BPS
                  </SourceNote>
                </div>
              </>
            )}
          </RemoteBody>
        </Panel>

        <Panel title={`Aksi korporasi · ${selectedSymbol}`} meta="Reaksi harga di tanggal ex" flush>
          <RemoteBody remote={events} errorTitle="Riwayat aksi korporasi belum bisa dimuat">
            {data =>
              data.events.length ? (
                <>
                  <table className="w-full text-[13px]">
                    <thead className="border-b border-line">
                      <tr className="text-xs text-ink-3">
                        <th className="px-4 h-9 font-medium text-left">Peristiwa</th>
                        <th className="px-4 h-9 font-medium text-right">H+1</th>
                        <th className="px-4 h-9 font-medium text-right">H+5</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line">
                      {data.events.map(e => (
                        <tr key={`${e.date}-${e.type}`}>
                          <td className="px-4 py-2.5">
                            <div className="text-ink">
                              {e.type === 'DIVIDEND'
                                ? `Dividen Rp ${e.amount?.toLocaleString('id-ID')}`
                                : `Stock split ${e.ratio}:1`}
                              {e.type === 'DIVIDEND' && e.yield_pct !== undefined && (
                                <span className="text-ink-3"> · {e.yield_pct.toLocaleString('id-ID')}%</span>
                              )}
                            </div>
                            <div className="num text-xs text-ink-3">{formatDay(e.date)}</div>
                          </td>
                          {[e.reaction_1d_pct, e.reaction_5d_pct].map((v, i) => (
                            <td key={i} className={cx('px-4 py-2.5 num text-right', v === null ? 'text-ink-3' : v >= 0 ? 'text-up' : 'text-down')}>
                              {v === null ? '—' : `${v >= 0 ? '+' : '−'}${Math.abs(v).toLocaleString('id-ID')}%`}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="px-4 py-2.5 border-t border-line text-xs text-ink-3 leading-relaxed">
                    Dibanding harga penutupan sebelum tanggal ex. Penurunan di hari ex dividen sebagian besar adalah dividen itu sendiri.
                  </p>
                </>
              ) : (
                <EmptyState title={`Belum ada dividen atau stock split ${selectedSymbol} dalam 5 tahun terakhir`} />
              )
            }
          </RemoteBody>
        </Panel>
      </div>
    </div>
  );
};
