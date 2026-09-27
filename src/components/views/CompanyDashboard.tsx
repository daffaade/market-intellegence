import React from 'react';
import {
  Building2,
  TrendingUp,
  PieChart as PieChartIcon,
  Users,
  Briefcase,
  DollarSign
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';
import type { Company } from '../../types/api';
import {
  MOCK_GROWTH_DATA,
  MOCK_DIVIDENDS,
  MOCK_SHAREHOLDERS,
  MOCK_EXECUTIVES,
  MOCK_SMART_MONEY
} from '../../services/mockData';
import { EmitenSwitcherModal } from '../shared/EmitenSwitcherModal';

interface CompanyDashboardProps {
  company: Company;
  onSelectSymbol?: (symbol: string) => void;
}

export const CompanyDashboard: React.FC<CompanyDashboardProps> = ({ company, onSelectSymbol }) => {
  const growthData = MOCK_GROWTH_DATA[company.symbol] || MOCK_GROWTH_DATA.BBCA;
  const dividends = MOCK_DIVIDENDS[company.symbol] || MOCK_DIVIDENDS.BBCA;
  const shareholders = MOCK_SHAREHOLDERS[company.symbol] || MOCK_SHAREHOLDERS.BBCA;
  const executives = MOCK_EXECUTIVES[company.symbol] || MOCK_EXECUTIVES.BBCA;
  const smartMoney = MOCK_SMART_MONEY[company.symbol] || MOCK_SMART_MONEY.BBCA;

  const formattedMarketCap = (company.market_cap / 1000000000000).toFixed(2);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-cyan-400">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white flex flex-wrap items-center gap-2">
                <span>{company.name}</span>
                <span className="text-xs px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono font-bold">
                  {company.symbol}
                </span>
                {onSelectSymbol && (
                  <EmitenSwitcherModal
                    currentSymbol={company.symbol}
                    onSelectSymbol={onSelectSymbol}
                    buttonText="Ganti Emiten"
                  />
                )}
              </h1>

              <p className="text-xs text-slate-400 mt-0.5">
                Sektor: <strong className="text-slate-300">{company.sector}</strong> | Sub-sektor: <strong className="text-slate-300">{company.sub_sector}</strong>
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-6">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Kapitalisasi Pasar</span>
            <span className="text-lg font-bold font-mono text-cyan-400">Rp {formattedMarketCap} T</span>
          </div>
          <div className="h-8 w-px bg-slate-800" />
          <div className="text-right">
            <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Update Terakhir</span>
            <span className="text-xs font-mono text-slate-300">2026-09-20 18:00 WIB</span>
          </div>
        </div>
      </div>

      {/* Financial Growth Analysis & Projections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-cyan-400" />
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
                Growth Analysis & Financial Projections (in Billions IDR)
              </h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">Histori & Konsensus 2026</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={growthData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="year" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="revenue" name="Pendapatan (Revenue)" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                <Bar dataKey="net_profit" name="Laba Bersih (Net Profit)" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Dividend History */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <DollarSign className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
                Histori Pembagian Dividen
              </h3>
            </div>

            <div className="space-y-3">
              {dividends.map((div, idx) => (
                <div key={idx} className="glass-card p-3 rounded-xl border border-slate-800 flex justify-between items-center">
                  <div>
                    <span className="text-xs font-bold text-slate-200 font-mono">Tahun {div.year}</span>
                    <div className="text-[10px] text-slate-400">DPS: Rp {div.dividend_per_share}</div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-mono font-bold text-emerald-400">{div.yield_percent}% Yield</span>
                    <div className="text-[10px] text-slate-400">Payout: {div.payout_ratio}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-[10px] text-slate-400">
            *Dividen konsisten dibayarkan 2 kali setahun (Interim & Final).
          </div>
        </div>
      </div>

      {/* Ownership & Insider Confidence & Smart Money */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ownership Structure */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center space-x-2 mb-4">
            <PieChartIcon className="w-5 h-5 text-indigo-400" />
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Peta Kepemilikan Saham (Ownership)
            </h3>
          </div>

          <div className="space-y-3">
            {shareholders.map((sh, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium truncate max-w-[200px]">{sh.name}</span>
                  <span className="font-mono font-bold text-slate-100">{sh.share_percentage}%</span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2">
                  <div
                    className={`h-full rounded-full ${
                      sh.category === 'INSTITUTIONAL'
                        ? 'bg-cyan-500'
                        : sh.category === 'RETAIL'
                        ? 'bg-indigo-500'
                        : 'bg-emerald-500'
                    }`}
                    style={{ width: `${sh.share_percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Key Executives & Insider Confidence */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center space-x-2 mb-4">
            <Users className="w-5 h-5 text-sky-400" />
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Insider Confidence Tracker
            </h3>
          </div>

          <div className="space-y-3">
            {executives.map((exec, idx) => (
              <div key={idx} className="glass-card p-3 rounded-xl border border-slate-800 flex justify-between items-center">
                <div>
                  <div className="text-xs font-semibold text-slate-200">{exec.name}</div>
                  <div className="text-[10px] text-slate-400">{exec.position} ({exec.tenure})</div>
                </div>
                <div className="text-right">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                    exec.insider_action === 'BOUGHT'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : 'bg-slate-800 text-slate-400'
                  }`}>
                    {exec.insider_action}
                  </span>
                  {exec.transaction_amount && (
                    <div className="text-[9px] text-emerald-400 font-mono mt-0.5">{exec.transaction_amount}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Smart Money Analysis (Institutional Transactions) */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center space-x-2 mb-4">
            <Briefcase className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Smart Money Analysis
            </h3>
          </div>

          <div className="space-y-3">
            {smartMoney.map((tx, idx) => (
              <div key={idx} className="glass-card p-3 rounded-xl border border-slate-800 flex justify-between items-center">
                <div>
                  <div className="text-xs font-semibold text-slate-200">{tx.institution}</div>
                  <div className="text-[10px] font-mono text-slate-400">{tx.date} | Vol: {tx.volume}</div>
                </div>
                <div className="text-right">
                  <span className="text-xs font-mono font-bold text-amber-400">{tx.value_idr}</span>
                  <div className="text-[10px] text-emerald-400 font-semibold">{tx.action}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
