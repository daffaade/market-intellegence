import React from 'react';
import {
  BrainCircuit,
  ShieldCheck,
  PieChart,
  Flame,
  FileText,
  Sparkles
} from 'lucide-react';
import type { IntelligenceSnapshot, Company } from '../../types/api';
import { MOCK_PORTFOLIO, MOCK_DISASTER_RISKS } from '../../services/mockData';

interface PortfolioAndAiProps {
  intelligence: IntelligenceSnapshot;
  company: Company;
}

export const PortfolioAndAi: React.FC<PortfolioAndAiProps> = ({
  intelligence
}) => {
  // Calculate portfolio stats
  const totalAllocation = MOCK_PORTFOLIO.reduce((acc, curr) => acc + curr.allocation_pct, 0);
  const weightedRisk = MOCK_PORTFOLIO.reduce((acc, curr) => acc + (curr.risk_score * curr.allocation_pct / 100), 0).toFixed(1);

  return (
    <div className="space-y-6">
      {/* AI Research Summary Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 relative glow-cyan">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <BrainCircuit className="w-6 h-6 text-cyan-400 animate-pulse" />
            <h3 className="text-base font-bold text-white tracking-wide font-mono">
              AI Research Summary (Explanation Layer)
            </h3>
          </div>
          <span className="text-xs px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-300 font-mono font-semibold border border-cyan-500/30">
            Automated Synthesis Engine
          </span>
        </div>

        <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-800 space-y-4">
          <div className="flex items-start space-x-3">
            <Sparkles className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <p className="text-sm text-slate-200 leading-relaxed font-sans">
              {intelligence.ai_research_summary}
            </p>
          </div>

          <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
            <div className="flex items-center space-x-4">
              <span>Kepercayaan Algoritma: <strong className="text-cyan-300">{intelligence.confidence} CONFIDENCE</strong></span>
              <span>Sanad Data: <strong className="text-slate-200">Laporan Keuangan & IDX Feeds</strong></span>
            </div>
            <div className="text-[10px] text-amber-400 font-mono">
              *Disclaimer: {intelligence.disclaimer}
            </div>
          </div>
        </div>
      </div>

      {/* Portfolio Risk & Concentration Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <PieChart className="w-5 h-5 text-indigo-400" />
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
                Portfolio Risk & Sector Concentration Analysis
              </h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">Portofolio Simulasi User</span>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="glass-card p-3 rounded-xl text-center">
                <span className="text-[10px] text-slate-400 font-mono block">Total Alokasi</span>
                <span className="text-base font-bold font-mono text-cyan-400">{totalAllocation}%</span>
              </div>
              <div className="glass-card p-3 rounded-xl text-center">
                <span className="text-[10px] text-slate-400 font-mono block">Weighted Risk Score</span>
                <span className="text-base font-bold font-mono text-emerald-400">{weightedRisk} / 100</span>
              </div>
              <div className="glass-card p-3 rounded-xl text-center">
                <span className="text-[10px] text-slate-400 font-mono block">Diversifikasi Sektor</span>
                <span className="text-base font-bold font-mono text-indigo-400">MODERATE</span>
              </div>
              <div className="glass-card p-3 rounded-xl text-center">
                <span className="text-[10px] text-slate-400 font-mono block">Konsentrasi Tertinggi</span>
                <span className="text-base font-bold font-mono text-amber-400">Financials (40%)</span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-mono">
                    <th className="pb-2 font-semibold">POSISI EMITEN</th>
                    <th className="pb-2 font-semibold">SEKTOR</th>
                    <th className="pb-2 font-semibold">ALOKASI (%)</th>
                    <th className="pb-2 font-semibold">RISK SCORE</th>
                    <th className="pb-2 font-semibold text-right">OPPORTUNITY SCORE</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {MOCK_PORTFOLIO.map((pos, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2.5 font-bold text-white font-mono">{pos.symbol} - {pos.name}</td>
                      <td className="py-2.5 text-slate-300">{pos.sector}</td>
                      <td className="py-2.5 font-mono text-cyan-400 font-bold">{pos.allocation_pct}%</td>
                      <td className="py-2.5 font-mono text-slate-300">{pos.risk_score}</td>
                      <td className="py-2.5 font-mono text-emerald-400 font-bold text-right">{pos.opportunity_score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Portfolio Risk Assessment Summary */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
                Risk Management Assessment
              </h3>
            </div>

            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">
                <strong>Konsentrasi Sektor Terkendali:</strong> Alokasi 40% pada sektor Financials (BBCA) didukung oleh indikator kesehatan finansial yang solid.
              </div>

              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
                <strong>Peringatan Alokasi High Risk:</strong> GOTO memiliki porsi 15% dengan Risk Score 68.4. Disarankan untuk pembatasan alokasi maksimal 10%.
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-[10px] text-slate-400">
            *Rekomendasi manajemen risiko secara kuantitatif untuk optimalisasi portofolio.
          </div>
        </div>
      </div>

      {/* External Impact: Disaster Risk & Consumer Behavior Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Disaster Risk Analysis */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center space-x-2 mb-4">
            <Flame className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Disaster Risk & Operational Impact Analysis
            </h3>
          </div>

          <div className="space-y-3">
            {MOCK_DISASTER_RISKS.map((risk, idx) => (
              <div key={idx} className="glass-card p-3.5 rounded-xl border border-slate-800 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-200">{risk.region}</span>
                  <span className={`px-2 py-0.5 rounded text-[9px] font-semibold ${
                    risk.severity === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {risk.severity} SEVERITY
                  </span>
                </div>
                <div className="text-xs text-slate-300">
                  Potensi Risiko: <strong className="text-cyan-300">{risk.risk_type}</strong>
                </div>
                <div className="text-[10px] text-slate-400">
                  Operasional Terdampak: {risk.impacted_operations}
                </div>
                <div className="text-[10px] text-emerald-400 font-medium">
                  {risk.mitigation_status}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Consumer Behavior & Digital Shift */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center space-x-2 mb-4">
            <FileText className="w-5 h-5 text-sky-400" />
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Consumer Behavior & Trend Analysis
            </h3>
          </div>

          <div className="space-y-3 text-xs text-slate-300">
            <div className="glass-card p-3 rounded-xl border border-slate-800 space-y-1">
              <span className="font-bold text-cyan-400 block">Adopsi Digital Banking & Cashless Payment</span>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Transaksi QRIS dan mobile banking nasional tumbuh 38% YoY. Hal ini memperkuat retensi CASA emiten perbankan besar seperti BBCA.
              </p>
            </div>

            <div className="glass-card p-3 rounded-xl border border-slate-800 space-y-1">
              <span className="font-bold text-cyan-400 block">Pergeseran Pola Belanja FMCG vs Digital E-Commerce</span>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Konsumen cenderung memilih produk FMCG kemasan lebih kecil (downsizing strategy), sementara volume transaksi e-commerce terkonsolidasi pada platform utama.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
