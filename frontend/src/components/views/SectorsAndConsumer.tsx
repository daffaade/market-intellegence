import React, { useMemo, useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  ReferenceLine
} from 'recharts';
import { ArrowDown, ArrowUp, Minus, Search } from 'lucide-react';
import type { Company, ConsumerBehaviorResult, SectorRow } from '../../types/api';
import { apiService } from '../../services/mockApi';
import { useRemote } from '../../lib/useRemote';
import { useChartColors } from '../../lib/theme';
import { RemoteBody, SourceNote, formatDay } from '../shared/RemoteState';
import { PageHeader, Panel, Tag, EmptyState, Button, Stat } from '../ui/primitives';
import { cx } from '../../lib/ui';

interface SectorsAndConsumerProps {
  companies: Company[];
  onSelectSymbol: (symbol: string) => void;
}

const pct = (v: number | null | undefined, nd = 1, fromFraction = true) =>
  v == null
    ? '—'
    : `${v >= 0 ? '+' : '−'}${Math.abs(fromFraction ? v * 100 : v).toLocaleString('id-ID', { maximumFractionDigits: nd })}%`;

const sentimentTone = { Bullish: 'up', Bearish: 'down', Neutral: 'neutral' } as const;
const sentimentLabel = { Bullish: 'Bullish', Bearish: 'Bearish', Neutral: 'Netral' } as const;

const SUGGESTIONS: Array<{ keyword: string; sector: string }> = [
  { keyword: 'kopi', sector: 'Consumer Non-Cyclicals' },
  { keyword: 'mobil listrik', sector: 'Industrials' },
  { keyword: 'skincare', sector: 'Healthcare' },
  { keyword: 'tiket pesawat', sector: 'Transportation & Logistic' },
  { keyword: 'kpr', sector: 'Properties & Real Estate' },
  { keyword: 'emas', sector: 'Basic Materials' }
];

export const SectorsAndConsumer: React.FC<SectorsAndConsumerProps> = ({ companies, onSelectSymbol }) => {
  const sectors = useRemote(() => apiService.getSectors(), []);
  const tracked = useMemo(() => new Set(companies.map(c => c.symbol)), [companies]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Pasar"
        title="Sektor & perilaku konsumen"
        description="Sektor mana yang menguat atau melemah dibanding IHSG, dan apakah minat konsumen di Google bergerak bersama saham sektornya."
      />

      <Panel title="Rotasi sektor" meta="Kinerja relatif terhadap IHSG" flush>
        <RemoteBody remote={sectors} skeletonClassName="h-80" errorTitle="Data sektor belum bisa dimuat">
          {data => <SectorBody rows={data.sectors} asOf={data.as_of} tracked={tracked} onSelectSymbol={onSelectSymbol} />}
        </RemoteBody>
      </Panel>

      <ConsumerPanel sectors={sectors.data?.sectors ?? []} tracked={tracked} onSelectSymbol={onSelectSymbol} />
    </div>
  );
};

// ─── Sectors ───────────────────────────────────────────────────

const SectorBody: React.FC<{
  rows: SectorRow[];
  asOf: string;
  tracked: Set<string>;
  onSelectSymbol: (s: string) => void;
}> = ({ rows, asOf, tracked, onSelectSymbol }) => {
  const colors = useChartColors();
  const [focus, setFocus] = useState<string>(rows[0]?.sector ?? '');
  const selected = rows.find(r => r.sector === focus) ?? rows[0];

  const bars = rows.map(r => ({ label: r.label, sector: r.sector, value: r.rs_20d == null ? 0 : r.rs_20d * 100 }));

  // All sector indices on one weekly axis; the focused one is highlighted.
  const lines = useMemo(() => {
    const dates = rows[0]?.index_weekly.map(p => p.date) ?? [];
    return dates.map((d, i) => {
      const point: Record<string, string | number | null> = { date: d };
      rows.forEach(r => {
        const v = r.index_weekly[i]?.value;
        point[r.sector] = v == null ? null : +(v - 100).toFixed(2);
      });
      return point;
    });
  }, [rows]);

  return (
    <div>
      <div className="grid grid-cols-1 xl:grid-cols-5 border-b border-line">
        <div className="xl:col-span-2 p-4 xl:border-r border-line">
          <div className="text-xs text-ink-3 mb-2">Return 20 sesi dikurangi IHSG</div>
          <div style={{ height: rows.length * 30 + 20 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={bars} layout="vertical" margin={{ top: 0, right: 12, left: 0, bottom: 0 }} barCategoryGap={6}>
                <CartesianGrid stroke={colors.grid} horizontal={false} />
                <XAxis type="number" stroke={colors.axis} fontSize={11} tickLine={false} axisLine={false} tickFormatter={v => `${v}%`} />
                <YAxis type="category" dataKey="label" stroke={colors.axis} fontSize={11} tickLine={false} axisLine={false} width={150} />
                <ReferenceLine x={0} stroke={colors.axis} />
                <Tooltip
                  cursor={{ fill: colors.grid, opacity: 0.5 }}
                  content={({ active, payload }) =>
                    active && payload?.length ? (
                      <div className="bg-surface border border-line-strong rounded-md shadow-lg px-3 py-2 text-xs">
                        <div className="text-ink-3 mb-1">{String(payload[0].payload.label)}</div>
                        <div className="num text-ink">{pct(Number(payload[0].value), 1, false)} vs IHSG</div>
                      </div>
                    ) : null
                  }
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]} isAnimationActive={false} onClick={d => setFocus(String((d as { sector?: string }).sector))}>
                  {bars.map(b => (
                    <Cell
                      key={b.sector}
                      cursor="pointer"
                      fill={b.value >= 0 ? colors.up : colors.down}
                      fillOpacity={b.sector === selected?.sector ? 1 : 0.55}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="xl:col-span-3 p-4">
          <div className="flex items-baseline justify-between gap-3 mb-2">
            <div className="text-xs text-ink-3">Indeks sektor (bobot sama), perubahan 26 minggu</div>
            {selected && (
              <span className="text-xs text-ink-2">
                Disorot: <span className="text-ink font-medium">{selected.label}</span>
              </span>
            )}
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={lines} margin={{ top: 4, right: 8, left: -12, bottom: 0 }}>
                <CartesianGrid stroke={colors.grid} vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke={colors.axis}
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: colors.grid }}
                  minTickGap={32}
                  tickFormatter={d => new Date(d).toLocaleDateString('id-ID', { month: 'short' })}
                />
                <YAxis stroke={colors.axis} fontSize={11} tickLine={false} axisLine={false} tickFormatter={v => `${v}%`} />
                <ReferenceLine y={0} stroke={colors.axis} strokeDasharray="3 3" />
                <Tooltip
                  cursor={{ stroke: colors.context }}
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length || !selected) return null;
                    const v = payload.find(p => p.dataKey === selected.sector)?.value;
                    return (
                      <div className="bg-surface border border-line-strong rounded-md shadow-lg px-3 py-2 text-xs">
                        <div className="text-ink-3 mb-1">{formatDay(String(label))}</div>
                        <div className="flex justify-between gap-4">
                          <span className="text-ink-2">{selected.label}</span>
                          <span className="num text-ink">{pct(v == null ? null : Number(v), 1, false)}</span>
                        </div>
                      </div>
                    );
                  }}
                />
                {rows.filter(r => r.sector !== selected?.sector).map(r => (
                  <Line key={r.sector} dataKey={r.sector} stroke={colors.context} strokeWidth={1.25} dot={false} activeDot={false} isAnimationActive={false} connectNulls />
                ))}
                {selected && (
                  <Line
                    dataKey={selected.sector}
                    stroke={colors.series1}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, stroke: colors.surface, strokeWidth: 2 }}
                    isAnimationActive={false}
                    connectNulls
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-[13px]">
          <thead className="border-b border-line">
            <tr className="text-xs text-ink-3 text-left">
              <th className="px-4 h-9 font-medium">#</th>
              <th className="px-4 h-9 font-medium">Sektor</th>
              <th className="px-4 h-9 font-medium">Sentimen</th>
              <th className="px-4 h-9 font-medium text-right">vs IHSG 20 sesi</th>
              <th className="px-4 h-9 font-medium text-right">vs IHSG 60 sesi</th>
              <th className="px-4 h-9 font-medium">Di atas MA50</th>
              <th className="px-4 h-9 font-medium">Rotasi</th>
              <th className="px-4 h-9 font-medium">Penggerak</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {rows.map(r => (
              <tr
                key={r.sector}
                onClick={() => setFocus(r.sector)}
                className={cx('cursor-pointer hover:bg-surface-2', r.sector === selected?.sector && 'bg-accent-soft/40')}
              >
                <td className="px-4 h-11 num text-ink-3">{r.rank}</td>
                <td className="px-4 h-11 text-ink whitespace-nowrap">{r.label}</td>
                <td className="px-4 h-11"><Tag tone={sentimentTone[r.sentiment]}>{sentimentLabel[r.sentiment]}</Tag></td>
                <td className={cx('px-4 h-11 num text-right', (r.rs_20d ?? 0) >= 0 ? 'text-up' : 'text-down')}>{pct(r.rs_20d)}</td>
                <td className={cx('px-4 h-11 num text-right', (r.rs_60d ?? 0) >= 0 ? 'text-up' : 'text-down')}>{pct(r.rs_60d)}</td>
                <td className="px-4 h-11">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 rounded-full bg-surface-2 overflow-hidden">
                      <div className="h-full bg-ink-2 rounded-full" style={{ width: `${(r.breadth_ma50 ?? 0) * 100}%` }} />
                    </div>
                    <span className="num text-xs text-ink-2">
                      {Math.round((r.breadth_ma50 ?? 0) * r.n_constituents)}/{r.n_constituents}
                    </span>
                  </div>
                </td>
                <td className="px-4 h-11 whitespace-nowrap">
                  <span
                    className={cx(
                      'inline-flex items-center gap-1 text-xs',
                      r.rotation === 'Menguat' ? 'text-up' : r.rotation === 'Melemah' ? 'text-down' : 'text-ink-3'
                    )}
                    title={`Peringkat 20 sesi lalu: ${r.rank_prev}`}
                  >
                    {r.rotation === 'Menguat' ? <ArrowUp className="w-3 h-3" /> : r.rotation === 'Melemah' ? <ArrowDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
                    {r.rotation} <span className="num text-ink-3">({r.rank_prev}→{r.rank})</span>
                  </span>
                </td>
                <td className="px-4 h-11">
                  <div className="flex gap-1">
                    {r.constituents.slice(0, 3).map(c =>
                      tracked.has(c.symbol) ? (
                        <button
                          key={c.symbol}
                          onClick={e => {
                            e.stopPropagation();
                            onSelectSymbol(c.symbol);
                          }}
                          className="num text-xs px-1.5 h-6 rounded border border-line text-accent hover:border-accent"
                        >
                          {c.symbol}
                        </button>
                      ) : (
                        <span key={c.symbol} className="num text-xs px-1.5 h-6 inline-flex items-center rounded border border-line text-ink-2">
                          {c.symbol}
                        </span>
                      )
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <div className="px-4 py-3 border-t border-line">
          <div className="text-xs text-ink-3 mb-2">Konstituen {selected.label}</div>
          <div className="flex flex-wrap gap-2">
            {selected.constituents.map(c => (
              <span key={c.symbol} className="inline-flex items-center gap-2 h-7 px-2 rounded-md border border-line text-xs">
                <span className="num text-ink font-medium">{c.symbol}</span>
                <span className={cx('num', (c.rs_20d ?? 0) >= 0 ? 'text-up' : 'text-down')}>{pct(c.rs_20d)}</span>
                <span className="text-ink-3">{c.above_ma50 ? '> MA50' : '< MA50'}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="px-4 py-2.5 border-t border-line">
        <SourceNote source="Yahoo Finance, harga disesuaikan dividen" date={asOf}>
          Bullish bila median kinerja relatif &gt; +2% dan ≥ 60% saham di atas MA50; rotasi = perubahan peringkat dalam 20 sesi
        </SourceNote>
      </div>
    </div>
  );
};

// ─── Consumer behavior ─────────────────────────────────────────

const ConsumerPanel: React.FC<{ sectors: SectorRow[]; tracked: Set<string>; onSelectSymbol: (s: string) => void }> = ({
  sectors,
  tracked,
  onSelectSymbol
}) => {
  const [keyword, setKeyword] = useState('kopi');
  const [sector, setSector] = useState('Consumer Non-Cyclicals');
  const [query, setQuery] = useState<{ keyword: string; sector: string } | null>(null);
  const result = useRemote(
    () => (query ? apiService.analyzeConsumerBehavior(query.keyword, query.sector) : Promise.resolve({ status: 'success' as const, data: undefined })),
    [query?.keyword, query?.sector]
  );

  const options = sectors.length
    ? sectors.map(s => ({ key: s.sector, label: s.label }))
    : SUGGESTIONS.map(s => ({ key: s.sector, label: s.sector }));

  const submit = (k = keyword, s = sector) => {
    const kw = k.trim();
    if (kw) setQuery({ keyword: kw, sector: s });
  };

  return (
    <Panel title="Perilaku konsumen" meta="Minat pencarian Google (Indonesia) vs saham sektor" flush>
      <form
        className="p-4 border-b border-line flex flex-col md:flex-row gap-2 md:items-end"
        onSubmit={e => {
          e.preventDefault();
          submit();
        }}
      >
        <label className="flex-1">
          <span className="text-xs text-ink-3">Kata kunci pencarian</span>
          <div className="mt-1.5 relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-3" />
            <input
              value={keyword}
              onChange={e => setKeyword(e.target.value)}
              maxLength={60}
              placeholder="mis. kopi, mobil listrik, skincare"
              className="w-full h-8 pl-8 pr-2 rounded-md bg-canvas border border-line text-[13px] text-ink outline-none focus:border-accent"
            />
          </div>
        </label>
        <label className="md:w-72">
          <span className="text-xs text-ink-3">Sektor</span>
          <select
            value={sector}
            onChange={e => setSector(e.target.value)}
            className="mt-1.5 w-full h-8 px-2 rounded-md bg-canvas border border-line text-[13px] text-ink outline-none focus:border-accent"
          >
            {options.map(o => <option key={o.key} value={o.key}>{o.label}</option>)}
          </select>
        </label>
        <Button type="submit" variant="primary" disabled={result.loading && !!query}>
          {result.loading && query ? 'Menganalisis…' : 'Analisis'}
        </Button>
      </form>

      {!query ? (
        <div className="p-4">
          <p className="text-[13px] text-ink-2">Coba salah satu:</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {SUGGESTIONS.map(s => (
              <button
                key={s.keyword}
                onClick={() => {
                  setKeyword(s.keyword);
                  setSector(s.sector);
                  submit(s.keyword, s.sector);
                }}
                className="h-7 px-2.5 rounded-md border border-line text-xs text-ink-2 hover:border-accent hover:text-accent"
              >
                {s.keyword} · {options.find(o => o.key === s.sector)?.label ?? s.sector}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <RemoteBody remote={result} skeletonClassName="h-72" errorTitle="Analisis belum bisa dijalankan">
          {data => (data ? <ConsumerResult r={data} tracked={tracked} onSelectSymbol={onSelectSymbol} /> : <></>)}
        </RemoteBody>
      )}
    </Panel>
  );
};

const directionCopy = {
  Positive: { label: 'Positif', tone: 'up' },
  Negative: { label: 'Negatif', tone: 'down' },
  Neutral: { label: 'Netral', tone: 'neutral' }
} as const;

const CorrText: React.FC<{ c: { r: number; significant: boolean; n_weeks: number } | null | undefined }> = ({ c }) =>
  c ? (
    <span>
      <span className="num text-ink">{c.r.toLocaleString('id-ID', { maximumFractionDigits: 2 })}</span>
      <span className={cx('ml-1.5 text-xs', c.significant ? 'text-warn' : 'text-ink-3')}>
        {c.significant ? 'signifikan' : 'tidak signifikan'}
      </span>
    </span>
  ) : (
    <span className="text-ink-3">—</span>
  );

const ConsumerResult: React.FC<{ r: ConsumerBehaviorResult; tracked: Set<string>; onSelectSymbol: (s: string) => void }> = ({
  r,
  tracked,
  onSelectSymbol
}) => {
  const colors = useChartColors();
  if (r.error) {
    return <EmptyState title={r.error}>Pilih salah satu sektor dari daftar.</EmptyState>;
  }
  const t = r.search_trend;
  const sig = r.impact_signal;
  const dir = sig ? directionCopy[sig.impact_direction] : null;

  return (
    <div>
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line border-b border-line [&>*]:bg-surface [&>*]:p-4">
        <Stat
          label="Skor dampak"
          value={sig ? sig.impact_score.toLocaleString('id-ID') : '—'}
          hint={dir ? <Tag tone={dir.tone}>{dir.label}</Tag> : undefined}
        />
        <Stat
          label="Pencarian vs tahun lalu"
          value={<span className={(t?.yoy_pct ?? 0) >= 0 ? 'text-up' : 'text-down'}>{pct(t?.yoy_pct, 1, false)}</span>}
          hint="4 minggu terakhir"
        />
        <Stat label="Posisi dalam 5 tahun" value={t ? `P${t.percentile_5y}` : '—'} hint="Persentil minat pencarian" />
        <Stat
          label={`Saham ${r.sector_label ?? 'sektor'}`}
          value={<span className={(r.sector_return_60d_pct ?? 0) >= 0 ? 'text-up' : 'text-down'}>{pct(r.sector_return_60d_pct, 1, false)}</span>}
          hint="60 sesi, bobot sama"
        />
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-3">
        <div className="xl:col-span-2 p-4 xl:border-r border-line">
          <div className="text-xs text-ink-3 mb-2">Minat pencarian "{r.keyword}" per minggu (0–100, Google Trends)</div>
          {t ? (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={t.weekly} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke={colors.grid} vertical={false} />
                  <XAxis
                    dataKey="date"
                    stroke={colors.axis}
                    fontSize={11}
                    tickLine={false}
                    axisLine={{ stroke: colors.grid }}
                    minTickGap={40}
                    tickFormatter={d => new Date(d).toLocaleDateString('id-ID', { month: 'short', year: '2-digit' })}
                  />
                  <YAxis stroke={colors.axis} fontSize={11} tickLine={false} axisLine={false} domain={[0, 100]} />
                  <Tooltip
                    cursor={{ stroke: colors.context }}
                    content={({ active, payload }) =>
                      active && payload?.length ? (
                        <div className="bg-surface border border-line-strong rounded-md shadow-lg px-3 py-2 text-xs">
                          <div className="text-ink-3 mb-1">Minggu {formatDay(String(payload[0].payload.date))}</div>
                          <div className="num text-ink">{Number(payload[0].value)}</div>
                        </div>
                      ) : null
                    }
                  />
                  <Line dataKey="value" stroke={colors.series1} strokeWidth={2} dot={false} activeDot={{ r: 4, stroke: colors.surface, strokeWidth: 2 }} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState title="Data Google Trends tidak tersedia untuk kata kunci ini">
              Coba kata kunci yang lebih umum. Tidak ada angka pengganti yang ditampilkan.
            </EmptyState>
          )}
        </div>

        <div className="p-4 space-y-4">
          <div>
            <div className="text-xs text-ink-3 mb-1.5">Korelasi perubahan pencarian (4 minggu) dengan return sektor</div>
            <dl className="grid grid-cols-[1fr_auto] gap-y-1.5 text-[13px]">
              <dt className="text-ink-2">Periode yang sama</dt>
              <dd className="text-right"><CorrText c={r.correlation?.same_period} /></dd>
              <dt className="text-ink-2">Pencarian mendahului 4 minggu</dt>
              <dd className="text-right"><CorrText c={r.correlation?.search_leads_4w} /></dd>
            </dl>
            <p className="text-xs text-ink-3 mt-1.5">Korelasional, bukan sebab-akibat. Signifikan bila p &lt; 0,05.</p>
          </div>
          {r.evidence && r.evidence.length > 0 && (
            <ul className="space-y-1.5">
              {r.evidence.map((e, i) => (
                <li key={i} className="flex gap-2 text-[13px] text-ink-2 leading-relaxed">
                  <span className="mt-[7px] w-1.5 h-1.5 rounded-full bg-ink-3 shrink-0" />
                  {e}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {r.companies && r.companies.length > 0 && (
        <div className="border-t border-line overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead className="border-b border-line">
              <tr className="text-xs text-ink-3">
                <th className="px-4 h-9 font-medium text-left">Emiten {r.sector_label}</th>
                <th className="px-4 h-9 font-medium text-right">Pertumbuhan pendapatan (TTM)</th>
                <th className="px-4 h-9 font-medium text-right">Return 20 sesi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {r.companies.map(c => (
                <tr key={c.symbol}>
                  <td className="px-4 h-10">
                    {tracked.has(c.symbol) ? (
                      <button onClick={() => onSelectSymbol(c.symbol)} className="num text-accent hover:underline">{c.symbol}</button>
                    ) : (
                      <span className="num text-ink">{c.symbol}</span>
                    )}
                  </td>
                  <td className="px-4 h-10 num text-right text-ink-2" title={c.revenue_growth_ttm == null ? 'Laporan Sectors untuk emiten ini belum diambil' : undefined}>
                    {pct(c.revenue_growth_ttm, 1, false)}
                  </td>
                  <td className={cx('px-4 h-10 num text-right', c.return_20d_pct >= 0 ? 'text-up' : 'text-down')}>{pct(c.return_20d_pct, 1, false)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="px-4 py-2.5 border-t border-line space-y-1">
        <SourceNote source="Google Trends, Yahoo Finance, laporan Sectors">
          pertumbuhan pendapatan hanya untuk emiten yang laporannya sudah diambil (tanda —)
        </SourceNote>
        <p className="text-xs text-ink-3 leading-relaxed">{r.disclaimer}</p>
      </div>
    </div>
  );
};
