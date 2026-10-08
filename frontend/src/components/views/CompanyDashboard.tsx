import React, { useMemo } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, ReferenceLine } from 'recharts';
import type { Company, IntelligenceSnapshot, Shareholder, CompanyFundamentals } from '../../types/api';
import { apiService } from '../../services/mockApi';
import { useRemote } from '../../lib/useRemote';
import { EmitenHeader } from '../shared/EmitenHeader';
import { RemoteBody, SourceNote, formatDay } from '../shared/RemoteState';
import { useChartColors } from '../../lib/theme';
import { Panel, Stat, EmptyState } from '../ui/primitives';
import { cx } from '../../lib/ui';

interface CompanyDashboardProps {
  company: Company;
  intelligence: IntelligenceSnapshot;
  onOpenSearch: () => void;
  isWatched: boolean;
  onToggleWatchlist: (symbol: string) => void;
}

const formatBillions = (n: number) => `Rp ${(n / 1000).toLocaleString('id-ID', { maximumFractionDigits: 1 })} T`;

/** Share counts in Indonesian short scale: rb, jt, M (miliar). */
export const formatShares = (n: number): string => {
  const a = Math.abs(n);
  const sign = n < 0 ? '−' : '';
  const fmt = (v: number) => v.toLocaleString('id-ID', { maximumFractionDigits: 1 });
  if (a >= 1e9) return `${sign}${fmt(a / 1e9)} M`;
  if (a >= 1e6) return `${sign}${fmt(a / 1e6)} jt`;
  if (a >= 1e3) return `${sign}${fmt(a / 1e3)} rb`;
  return `${sign}${a}`;
};

/** Rupiah in Indonesian short scale: jt, M (miliar), T (triliun). */
const formatRupiah = (n: number): string => {
  const a = Math.abs(n);
  const sign = n < 0 ? '−' : '';
  const fmt = (v: number) => v.toLocaleString('id-ID', { maximumFractionDigits: 1 });
  if (a >= 1e12) return `${sign}Rp ${fmt(a / 1e12)} T`;
  if (a >= 1e9) return `${sign}Rp ${fmt(a / 1e9)} M`;
  if (a >= 1e6) return `${sign}Rp ${fmt(a / 1e6)} jt`;
  return `${sign}Rp ${a.toLocaleString('id-ID')}`;
};

const pctChange = (curr?: number, prev?: number) =>
  curr !== undefined && prev ? ((curr - prev) / Math.abs(prev)) * 100 : undefined;

const Change: React.FC<{ value?: number; suffix?: string }> = ({ value, suffix = '% YoY' }) =>
  value === undefined ? null : (
    <span className={cx('num', value >= 0 ? 'text-up' : 'text-down')}>
      {value >= 0 ? '+' : '−'}{Math.abs(value).toFixed(1)}{suffix}
    </span>
  );

const ownershipColor: Record<Shareholder['category'], string> = {
  INSTITUTIONAL: 'bg-accent',
  GOVERNMENT: 'bg-ink-2',
  RETAIL: 'bg-line-strong',
  MANAGEMENT: 'bg-warn',
  TREASURY: 'bg-ink-3'
};

const ownershipLabel: Record<Shareholder['category'], string> = {
  INSTITUTIONAL: 'Institusi / pengendali',
  GOVERNMENT: 'Pemerintah',
  RETAIL: 'Publik',
  MANAGEMENT: 'Direksi & komisaris',
  TREASURY: 'Saham treasuri'
};

const Unavailable: React.FC<{ what: string; symbol: string }> = ({ what, symbol }) => (
  <EmptyState title={`Data ${what} ${symbol} tidak tercantum di laporan`}>
    Laporan Sectors untuk emiten ini tidak memuat bagian tersebut.
  </EmptyState>
);

export const CompanyDashboard: React.FC<CompanyDashboardProps> = ({
  company,
  intelligence,
  onOpenSearch,
  isWatched,
  onToggleWatchlist
}) => {
  const sym = company.symbol;
  const fundamentals = useRemote(() => apiService.getFundamentals(sym), [sym]);
  const f = fundamentals.data?.symbol === sym ? fundamentals.data : null;

  return (
    <div className="space-y-6">
      <EmitenHeader
        company={company}
        intelligence={intelligence}
        section="Fundamental"
        onOpenSearch={onOpenSearch}
        isWatched={isWatched}
        onToggleWatchlist={onToggleWatchlist}
      />

      {f ? (
        <FundamentalsBody f={f} />
      ) : (
        <Panel>
          <RemoteBody remote={{ ...fundamentals, data: null }} skeletonClassName="h-72" errorTitle={`Fundamental ${sym} belum bisa dimuat`}>
            {() => null}
          </RemoteBody>
        </Panel>
      )}
    </div>
  );
};

const FundamentalsBody: React.FC<{ f: CompanyFundamentals }> = ({ f }) => {
  const colors = useChartColors();
  const sym = f.symbol;
  const growth = f.growth_data;
  const last = growth[growth.length - 1];
  const prev = growth[growth.length - 2];
  const lastDiv = f.dividends[f.dividends.length - 1];

  const buyers = f.smart_money.filter(t => t.action === 'ACCUMULATE');
  const sellers = f.smart_money.filter(t => t.action === 'DISTRIBUTE');
  const maxMove = Math.max(1, ...f.smart_money.map(t => Math.abs(t.shares_change)));

  const flow = useMemo(() => f.institutional_flow.slice(-12), [f.institutional_flow]);
  const foreign = useMemo(() => (f.foreign_flow ?? []).slice(-60), [f.foreign_flow]);
  const foreignNet = (n: number) => foreign.slice(-n).reduce((a, p) => a + p.net_idr, 0);
  const flowNet = flow.reduce((a, p) => a + p.net_shares, 0);

  const holders = useMemo(() => {
    // Collapse the long tail of tiny holders so the bar stays readable.
    const big = f.shareholders.filter(s => s.share_percentage >= 1);
    const rest = f.shareholders.filter(s => s.share_percentage < 1);
    const restPct = rest.reduce((a, s) => a + s.share_percentage, 0);
    return { big, rest, restPct };
  }, [f.shareholders]);

  return (
    <>
      <SourceNote source={f.source === 'sectors' ? 'Laporan perusahaan Sectors' : f.source} date={f.fetched_at}>
        disimpan hingga 7 hari
      </SourceNote>

      <section className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line border border-line rounded-lg overflow-hidden [&>*]:bg-surface [&>*]:p-4">
        <Stat
          label={`Pendapatan ${last?.year ?? ''}`}
          value={last ? formatBillions(last.revenue) : '—'}
          hint={<Change value={pctChange(last?.revenue, prev?.revenue)} />}
        />
        <Stat
          label={`Laba bersih ${last?.year ?? ''}`}
          value={last ? formatBillions(last.net_profit) : '—'}
          hint={<Change value={pctChange(last?.net_profit, prev?.net_profit)} />}
        />
        <Stat
          label="Marjin laba bersih"
          value={last ? `${last.margin.toLocaleString('id-ID')}%` : '—'}
          hint={last && prev ? <Change value={last.margin - prev.margin} suffix=" poin" /> : undefined}
        />
        <Stat
          label={`Dividen ${lastDiv?.year ?? ''}`}
          value={lastDiv ? `Rp ${lastDiv.dividend_per_share.toLocaleString('id-ID')}` : '—'}
          hint={lastDiv ? `Imbal hasil ${lastDiv.yield_percent.toLocaleString('id-ID')}%` : undefined}
        />
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Panel
          className="xl:col-span-2"
          title="Pendapatan dan laba bersih"
          meta="Triliun rupiah"
          actions={
            growth.length > 0 && (
              <div className="flex items-center gap-3 text-xs text-ink-2">
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: colors.series1 }} />Pendapatan</span>
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: colors.series2 }} />Laba bersih</span>
              </div>
            )
          }
        >
          {growth.length > 0 ? (
            <>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={growth} margin={{ top: 4, right: 4, left: -8, bottom: 0 }} barGap={2} barCategoryGap="28%">
                    <CartesianGrid stroke={colors.grid} vertical={false} />
                    <XAxis dataKey="year" stroke={colors.axis} fontSize={11} tickLine={false} axisLine={{ stroke: colors.grid }} />
                    <YAxis stroke={colors.axis} fontSize={11} tickLine={false} axisLine={false} tickFormatter={v => `${Number(v) / 1000}`} />
                    <Tooltip
                      cursor={{ fill: colors.grid, opacity: 0.5 }}
                      content={({ active, payload, label }) =>
                        active && payload?.length ? (
                          <div className="bg-surface border border-line-strong rounded-md shadow-lg px-3 py-2 text-xs">
                            <div className="text-ink-3 mb-1">{label}</div>
                            {payload.map(p => (
                              <div key={String(p.dataKey)} className="flex justify-between gap-4">
                                <span className="text-ink-2">{p.dataKey === 'revenue' ? 'Pendapatan' : 'Laba bersih'}</span>
                                <span className="num text-ink">{formatBillions(Number(p.value))}</span>
                              </div>
                            ))}
                          </div>
                        ) : null
                      }
                    />
                    <Bar dataKey="revenue" fill={colors.series1} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                    <Bar dataKey="net_profit" fill={colors.series2} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div
                className="mt-3 pt-3 border-t border-line grid gap-2 text-xs"
                style={{ gridTemplateColumns: `auto repeat(${growth.length}, minmax(0, 1fr))` }}
              >
                <span className="text-ink-3 pr-2">Marjin</span>
                {growth.map(g => (
                  <span key={g.year} className="num text-ink-2 text-center">{g.margin.toLocaleString('id-ID')}%</span>
                ))}
              </div>
            </>
          ) : (
            <Unavailable what="laporan keuangan" symbol={sym} />
          )}
        </Panel>

        <Panel title="Riwayat dividen" meta="Per lembar, tahun pembayaran" flush>
          {f.dividends.length > 0 ? (
            <>
              <table className="w-full text-[13px]">
                <thead className="border-b border-line">
                  <tr className="text-xs text-ink-3">
                    <th className="px-4 h-9 font-medium text-left">Tahun</th>
                    <th className="px-4 h-9 font-medium text-right">DPS</th>
                    <th className="px-4 h-9 font-medium text-right">Yield</th>
                    <th className="px-4 h-9 font-medium text-right">Payout</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {[...f.dividends].reverse().map(d => (
                    <tr key={d.year}>
                      <td className="px-4 h-10 num text-ink">{d.year}</td>
                      <td className="px-4 h-10 num text-ink text-right">Rp {d.dividend_per_share.toLocaleString('id-ID')}</td>
                      <td className="px-4 h-10 num text-ink-2 text-right">{d.yield_percent.toLocaleString('id-ID')}%</td>
                      <td className="px-4 h-10 num text-ink-2 text-right">
                        {d.payout_ratio === null ? <span className="text-ink-3" title="Tidak bisa dihitung andal, misalnya karena stock split">—</span> : `${d.payout_ratio.toLocaleString('id-ID')}%`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="px-4 py-2.5 border-t border-line text-xs text-ink-3 leading-relaxed">
                Payout = DPS ÷ laba per saham tahun sebelumnya. Kosong bila angkanya tidak wajar, misalnya DPS sebelum stock split.
              </p>
            </>
          ) : (
            <Unavailable what="dividen" symbol={sym} />
          )}
        </Panel>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Panel title="Struktur kepemilikan" meta="Pemegang ≥ 1%">
          {f.shareholders.length > 0 ? (
            <>
              <div className="flex h-2 rounded-full overflow-hidden gap-0.5 bg-surface-2" aria-hidden="true">
                {f.shareholders.map(s => (
                  <div key={s.name} className={ownershipColor[s.category]} style={{ width: `${s.share_percentage}%` }} />
                ))}
              </div>
              <ul className="mt-4 space-y-3">
                {holders.big.map(s => (
                  <li key={s.name} className="flex items-start gap-2.5 text-[13px]">
                    <span className={cx('w-2 h-2 rounded-sm mt-1.5 shrink-0', ownershipColor[s.category])} />
                    <span className="min-w-0 flex-1">
                      <span className="block text-ink truncate" title={s.name}>{s.name}</span>
                      <span className="block text-xs text-ink-3">{ownershipLabel[s.category]}</span>
                    </span>
                    <span className="num text-ink">{s.share_percentage.toLocaleString('id-ID')}%</span>
                  </li>
                ))}
              </ul>
              {holders.rest.length > 0 && (
                <p className="mt-3 pt-3 border-t border-line text-xs text-ink-3">
                  {holders.rest.length} pemegang lain di bawah 1%, total{' '}
                  <span className="num text-ink-2">{holders.restPct.toLocaleString('id-ID', { maximumFractionDigits: 2 })}%</span>
                </p>
              )}
            </>
          ) : (
            <Unavailable what="kepemilikan" symbol={sym} />
          )}
        </Panel>

        <Panel title="Direksi & komisaris" meta="Kepemilikan saham pribadi" flush>
          {f.executives.length > 0 ? (
            <ul className="divide-y divide-line max-h-[420px] overflow-y-auto">
              {f.executives.map(e => (
                <li key={`${e.name}-${e.position}`} className="px-4 py-3 flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-[13px] text-ink truncate" title={e.name}>{e.name}</div>
                    <div className="text-xs text-ink-3">{e.position}</div>
                  </div>
                  <div className="text-right shrink-0">
                    {e.share_amount ? (
                      <>
                        <div className="num text-[13px] text-ink">{formatShares(e.share_amount)}</div>
                        <div className="text-xs text-ink-3">lembar</div>
                      </>
                    ) : (
                      <div className="text-xs text-ink-3">Tidak dilaporkan</div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <Unavailable what="direksi" symbol={sym} />
          )}
        </Panel>

        <Panel
          title="Pergerakan institusi"
          meta={f.smart_money_as_of ? `Per ${formatDay(f.smart_money_as_of)}` : undefined}
          flush
        >
          {f.smart_money.length > 0 ? (
            <div className="divide-y divide-line">
              {[
                { label: 'Menambah posisi', rows: buyers, tone: 'up' as const },
                { label: 'Mengurangi posisi', rows: sellers, tone: 'down' as const }
              ].map(group =>
                group.rows.length ? (
                  <div key={group.label} className="px-4 py-3">
                    <div className="text-xs text-ink-3 mb-2">{group.label}</div>
                    <ul className="space-y-2.5">
                      {group.rows.map(t => (
                        <li key={t.institution}>
                          <div className="flex items-baseline justify-between gap-3 text-[13px]">
                            <span className="text-ink truncate" title={t.institution}>{t.institution}</span>
                            <span className={cx('num shrink-0', group.tone === 'up' ? 'text-up' : 'text-down')}>
                              {t.shares_change > 0 ? '+' : ''}{formatShares(t.shares_change)}
                            </span>
                          </div>
                          <div className="h-1 mt-1 rounded-full bg-surface-2 overflow-hidden">
                            <div
                              className={cx('h-full rounded-full', group.tone === 'up' ? 'bg-up' : 'bg-down')}
                              style={{ width: `${(Math.abs(t.shares_change) / maxMove) * 100}%` }}
                            />
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null
              )}
              <p className="px-4 py-2.5 text-xs text-ink-3">Perubahan jumlah lembar selama periode laporan.</p>
            </div>
          ) : (
            <Unavailable what="transaksi institusi" symbol={sym} />
          )}
        </Panel>
      </div>

      {foreign.length > 0 && (
        <Panel
          title="Arus bersih asing"
          meta={`Harian, ${foreign.length} sesi terakhir`}
          actions={
            <span className="flex gap-4 text-xs text-ink-3">
              {[5, 20].map(n => (
                <span key={n}>
                  {n} sesi{' '}
                  <span className={cx('num', foreignNet(n) >= 0 ? 'text-up' : 'text-down')}>{formatRupiah(foreignNet(n))}</span>
                </span>
              ))}
            </span>
          }
        >
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={foreign} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
                <CartesianGrid stroke={colors.grid} vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke={colors.axis}
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: colors.grid }}
                  minTickGap={28}
                  tickFormatter={d => new Date(d).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })}
                />
                <YAxis stroke={colors.axis} fontSize={11} tickLine={false} axisLine={false} width={64} tickFormatter={v => formatRupiah(Number(v)).replace('Rp ', '')} />
                <ReferenceLine y={0} stroke={colors.axis} />
                <Tooltip
                  cursor={{ fill: colors.grid, opacity: 0.5 }}
                  content={({ active, payload }) =>
                    active && payload?.length ? (
                      <div className="bg-surface border border-line-strong rounded-md shadow-lg px-3 py-2 text-xs">
                        <div className="text-ink-3 mb-1">{formatDay(String(payload[0].payload.date))}</div>
                        <div className="num text-ink">{formatRupiah(Number(payload[0].value))}</div>
                        {payload[0].payload.foreign_share != null && (
                          <div className="text-ink-3">Porsi asing {(Number(payload[0].payload.foreign_share) * 100).toFixed(0)}% transaksi</div>
                        )}
                      </div>
                    ) : null
                  }
                />
                <Bar dataKey="net_idr" isAnimationActive={false}>
                  {foreign.map(p => (
                    <Cell key={p.date} fill={p.net_idr >= 0 ? colors.up : colors.down} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-xs text-ink-3">Nilai beli dikurangi nilai jual investor asing per sesi. Sumber: Sectors.</p>
        </Panel>
      )}

      {flow.length > 0 && (
        <Panel
          title="Arus bersih institusi"
          meta="Per bulan pelaporan, lembar saham"
          actions={
            <span className="text-xs text-ink-3">
              Total {flow.length} periode{' '}
              <span className={cx('num', flowNet >= 0 ? 'text-up' : 'text-down')}>
                {flowNet >= 0 ? '+' : ''}{formatShares(flowNet)}
              </span>
            </span>
          }
        >
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={flow} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
                <CartesianGrid stroke={colors.grid} vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke={colors.axis}
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: colors.grid }}
                  tickFormatter={d => new Date(d).toLocaleDateString('id-ID', { month: 'short', year: '2-digit' })}
                />
                <YAxis stroke={colors.axis} fontSize={11} tickLine={false} axisLine={false} tickFormatter={v => formatShares(Number(v))} width={56} />
                <ReferenceLine y={0} stroke={colors.axis} />
                <Tooltip
                  cursor={{ fill: colors.grid, opacity: 0.5 }}
                  content={({ active, payload }) =>
                    active && payload?.length ? (
                      <div className="bg-surface border border-line-strong rounded-md shadow-lg px-3 py-2 text-xs">
                        <div className="text-ink-3 mb-1">{formatDay(String(payload[0].payload.date))}</div>
                        <div className="num text-ink">{formatShares(Number(payload[0].value))} lembar</div>
                      </div>
                    ) : null
                  }
                />
                <Bar dataKey="net_shares" radius={[3, 3, 0, 0]} isAnimationActive={false}>
                  {flow.map(p => (
                    <Cell key={p.date} fill={p.net_shares >= 0 ? colors.up : colors.down} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      )}
    </>
  );
};
