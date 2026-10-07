import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from 'recharts';
import type { Company, IntelligenceSnapshot, Shareholder } from '../../types/api';
import {
  MOCK_GROWTH_DATA,
  MOCK_DIVIDENDS,
  MOCK_SHAREHOLDERS,
  MOCK_EXECUTIVES,
  MOCK_SMART_MONEY
} from '../../services/mockData';
import { EmitenHeader } from '../shared/EmitenHeader';
import { useChartColors } from '../../lib/theme';
import { Panel, Stat, Tag, EmptyState } from '../ui/primitives';
import { cx } from '../../lib/ui';

interface CompanyDashboardProps {
  company: Company;
  intelligence: IntelligenceSnapshot;
  onOpenSearch: () => void;
  isWatched: boolean;
  onToggleWatchlist: (symbol: string) => void;
}

const formatBillions = (n: number) => `Rp ${(n / 1000).toLocaleString('id-ID', { maximumFractionDigits: 1 })} T`;

const pctChange = (curr?: number, prev?: number) =>
  curr !== undefined && prev ? ((curr - prev) / prev) * 100 : undefined;

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
  MANAGEMENT: 'bg-warn'
};

const ownershipLabel: Record<Shareholder['category'], string> = {
  INSTITUTIONAL: 'Institusi',
  GOVERNMENT: 'Pemerintah',
  RETAIL: 'Publik',
  MANAGEMENT: 'Manajemen'
};

const insiderLabel = { BOUGHT: 'Beli', SOLD: 'Jual', HELD: 'Tahan' } as const;

const Missing: React.FC<{ what: string; symbol: string }> = ({ what, symbol }) => (
  <EmptyState title={`Data ${what} ${symbol} belum tersedia`}>
    Sumber data saat ini baru mencakup sebagian emiten. Data akan muncul otomatis setelah backend menyediakannya.
  </EmptyState>
);

export const CompanyDashboard: React.FC<CompanyDashboardProps> = ({
  company,
  intelligence,
  onOpenSearch,
  isWatched,
  onToggleWatchlist
}) => {
  const colors = useChartColors();
  const sym = company.symbol;

  // No silent fallback to another emiten's numbers — missing data is shown as missing.
  const growth = MOCK_GROWTH_DATA[sym];
  const dividends = MOCK_DIVIDENDS[sym];
  const shareholders = MOCK_SHAREHOLDERS[sym];
  const executives = MOCK_EXECUTIVES[sym];
  const smartMoney = MOCK_SMART_MONEY[sym];

  const actual = growth?.filter(g => !g.year.includes('F')) ?? [];
  const last = actual[actual.length - 1];
  const prev = actual[actual.length - 2];
  const lastDiv = dividends?.[dividends.length - 1];

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
          value={last ? `${last.margin}%` : '—'}
          hint={last && prev ? <Change value={last.margin - prev.margin} suffix=" poin" /> : undefined}
        />
        <Stat
          label={`Imbal hasil dividen ${lastDiv?.year ?? ''}`}
          value={lastDiv ? `${lastDiv.yield_percent}%` : '—'}
          hint={lastDiv ? `Payout ${lastDiv.payout_ratio}%` : undefined}
        />
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Panel
          className="xl:col-span-2"
          title="Pendapatan dan laba bersih"
          meta="Triliun rupiah · F = proyeksi"
          actions={
            growth && (
              <div className="flex items-center gap-3 text-xs text-ink-2">
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: colors.series1 }} />Pendapatan</span>
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: colors.series2 }} />Laba bersih</span>
              </div>
            )
          }
        >
          {growth ? (
            <>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={growth} margin={{ top: 4, right: 4, left: -8, bottom: 0 }} barGap={2} barCategoryGap="28%">
                    <CartesianGrid stroke={colors.grid} vertical={false} />
                    <XAxis dataKey="year" stroke={colors.axis} fontSize={11} tickLine={false} axisLine={{ stroke: colors.grid }} />
                    <YAxis
                      stroke={colors.axis}
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={v => `${Number(v) / 1000}`}
                    />
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
                    <Bar dataKey="revenue" fill={colors.series1} radius={[4, 4, 0, 0]} isAnimationActive={false}>
                      {growth.map(g => <Cell key={g.year} fill={colors.series1} fillOpacity={g.year.includes('F') ? 0.4 : 1} />)}
                    </Bar>
                    <Bar dataKey="net_profit" fill={colors.series2} radius={[4, 4, 0, 0]} isAnimationActive={false}>
                      {growth.map(g => <Cell key={g.year} fill={colors.series2} fillOpacity={g.year.includes('F') ? 0.4 : 1} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 pt-3 border-t border-line grid gap-2 text-xs" style={{ gridTemplateColumns: `auto repeat(${growth.length}, minmax(0, 1fr))` }}>
                <span className="text-ink-3 pr-2">Marjin</span>
                {growth.map(g => (
                  <span key={g.year} className="num text-ink-2 text-center">{g.margin}%</span>
                ))}
              </div>
            </>
          ) : (
            <Missing what="laporan keuangan" symbol={sym} />
          )}
        </Panel>

        <Panel title="Riwayat dividen" flush>
          {dividends ? (
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
                {[...dividends].reverse().map(d => (
                  <tr key={d.year}>
                    <td className="px-4 h-10 num text-ink">{d.year}</td>
                    <td className="px-4 h-10 num text-ink text-right">Rp {d.dividend_per_share}</td>
                    <td className="px-4 h-10 num text-ink-2 text-right">{d.yield_percent}%</td>
                    <td className="px-4 h-10 num text-ink-2 text-right">{d.payout_ratio}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <Missing what="dividen" symbol={sym} />
          )}
        </Panel>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Panel title="Struktur kepemilikan">
          {shareholders ? (
            <>
              <div className="flex h-2 rounded-full overflow-hidden gap-0.5" aria-hidden="true">
                {shareholders.map(s => (
                  <div key={s.name} className={ownershipColor[s.category]} style={{ width: `${s.share_percentage}%` }} />
                ))}
              </div>
              <ul className="mt-4 space-y-3">
                {shareholders.map(s => (
                  <li key={s.name} className="flex items-start gap-2.5 text-[13px]">
                    <span className={cx('w-2 h-2 rounded-sm mt-1.5 shrink-0', ownershipColor[s.category])} />
                    <span className="min-w-0 flex-1">
                      <span className="block text-ink truncate">{s.name}</span>
                      <span className="block text-xs text-ink-3">{ownershipLabel[s.category]}</span>
                    </span>
                    <span className="num text-ink">{s.share_percentage}%</span>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <Missing what="kepemilikan" symbol={sym} />
          )}
        </Panel>

        <Panel title="Transaksi orang dalam" meta="Direksi & komisaris" flush>
          {executives ? (
            <ul className="divide-y divide-line">
              {executives.map(e => (
                <li key={e.name} className="px-4 py-3 flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-[13px] text-ink truncate">{e.name}</div>
                    <div className="text-xs text-ink-3">{e.position} · {e.tenure}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <Tag tone={e.insider_action === 'BOUGHT' ? 'up' : e.insider_action === 'SOLD' ? 'down' : 'neutral'}>
                      {insiderLabel[e.insider_action]}
                    </Tag>
                    {e.transaction_amount && <div className="num text-xs text-ink-3 mt-1">{e.transaction_amount}</div>}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <Missing what="orang dalam" symbol={sym} />
          )}
        </Panel>

        <Panel title="Arus dana institusi" meta="Transaksi terbaru" flush>
          {smartMoney ? (
            <ul className="divide-y divide-line">
              {smartMoney.map((tx, i) => (
                <li key={i} className="px-4 py-3 flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-[13px] text-ink truncate">{tx.institution}</div>
                    <div className="num text-xs text-ink-3">{tx.date} · {tx.volume} lembar</div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="num text-[13px] text-ink">{tx.value_idr}</div>
                    <div className={cx('text-xs', tx.action === 'ACCUMULATE' ? 'text-up' : 'text-down')}>
                      {tx.action === 'ACCUMULATE' ? 'Akumulasi' : 'Distribusi'}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <Missing what="arus dana institusi" symbol={sym} />
          )}
        </Panel>
      </div>
    </div>
  );
};
