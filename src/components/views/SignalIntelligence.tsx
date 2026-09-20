import React from 'react';
import {
  Zap,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  ArrowRightLeft,
  CheckCircle2,
  XCircle,
  Info,
  ShieldCheck,
  Layers,
  Sparkles
} from 'lucide-react';
import type { IntelligenceSnapshot, Company, StandardizedSignalOutput } from '../../types/api';
import { EvidencePanel } from '../shared/EvidencePanel';

interface SignalIntelligenceProps {
  intelligence: IntelligenceSnapshot;
  company: Company;
  signalOutput?: StandardizedSignalOutput;
}

export const SignalIntelligence: React.FC<SignalIntelligenceProps> = ({
  intelligence,
  company,
  signalOutput
}) => {
  const isBullish = intelligence.direction === 'BULLISH';
  const isHighRisk = intelligence.risk_level === 'HIGH' || intelligence.risk_level === 'CRITICAL';

  return (
    <div className="space-y-6">
      {/* Core Signal Summary Header */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 relative overflow-hidden">
        <div className="absolute -right-16 -top-16 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <span className="text-2xl font-bold tracking-tight text-white">{company.symbol}</span>
              <span className="text-sm text-slate-400">({company.name})</span>
              <span className="text-xs px-2.5 py-0.5 rounded-md bg-slate-800 text-slate-300 font-medium">
                {company.sector}
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-2xl">
              Derived intelligence snapshot berdasarkan pemrosesan data real-time, deteksi deviasi fundamental, dan pelacakan arus modal institusional.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {/* Direction & Confidence Badge */}
            <div className={`px-4 py-2 rounded-xl border flex items-center space-x-2 ${
              isBullish 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
            }`}>
              {isBullish ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
              <div>
                <div className="text-xs font-bold leading-tight">{intelligence.direction} SIGNAL</div>
                <div className="text-[10px] opacity-80">Confidence: {intelligence.confidence}</div>
              </div>
            </div>

            {/* Anomaly Indicator */}
            {intelligence.is_anomaly && (
              <div className="px-4 py-2 rounded-xl border bg-amber-500/10 border-amber-500/30 text-amber-400 flex items-center space-x-2 animate-pulse">
                <AlertTriangle className="w-5 h-5" />
                <div>
                  <div className="text-xs font-bold leading-tight">ANOMALY DETECTED</div>
                  <div className="text-[10px] opacity-90">Score: {intelligence.anomaly_score}/100</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Indicators: Opportunity vs Risk Score */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Opportunity Score Card */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 relative glow-cyan">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-cyan-400" />
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
                Opportunity Signal Score
              </h3>
            </div>
            <span className="text-xs text-cyan-400 font-mono font-medium">Algorithmic Score</span>
          </div>

          <div className="flex items-end justify-between my-4">
            <div>
              <div className="text-5xl font-black text-white tracking-tight font-mono">
                {intelligence.opportunity_score}
                <span className="text-xl text-slate-500 font-normal">/100</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Kombinasi nilai akumulasi asing, marjin profitabilitas & momentum pertumbuhan.
              </p>
            </div>
            <div className="text-right">
              <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                STRONG SIGNAL
              </span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-900 rounded-full h-3 p-0.5 border border-slate-800">
            <div
              className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full rounded-full transition-all duration-1000"
              style={{ width: `${intelligence.opportunity_score}%` }}
            />
          </div>
        </div>

        {/* Risk Score Card */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 relative glow-rose">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
                Risk Signal Score
              </h3>
            </div>
            <span className="text-xs text-emerald-400 font-mono font-medium">Risk Level: {intelligence.risk_level}</span>
          </div>

          <div className="flex items-end justify-between my-4">
            <div>
              <div className="text-5xl font-black text-white tracking-tight font-mono">
                {intelligence.risk_score}
                <span className="text-xl text-slate-500 font-normal">/100</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Mengukur volatilitas valuasi, eksposur makro & potensi tekanan distribusi modal.
              </p>
            </div>
            <div className="text-right">
              <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold border ${
                isHighRisk 
                  ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' 
                  : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
              }`}>
                {intelligence.risk_level} RISK
              </span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-900 rounded-full h-3 p-0.5 border border-slate-800">
            <div
              className="bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-500 h-full rounded-full transition-all duration-1000"
              style={{ width: `${intelligence.risk_score}%` }}
            />
          </div>
        </div>
      </div>

      {/* Fundamental Divergence Alert & What Changed Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: What Changed? Timeline */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <ArrowRightLeft className="w-5 h-5 text-cyan-400" />
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
                What Changed? (Perubahan Antar-Periode)
              </h3>
            </div>
            <span className="text-xs text-slate-400">Instan Delta Monitor</span>
          </div>

          <div className="space-y-3">
            {intelligence.what_changed.map((change, index) => (
              <div
                key={index}
                className="glass-card p-4 rounded-xl border border-slate-800/80 flex items-center justify-between hover:border-slate-700 transition-all"
              >
                <div className="space-y-1">
                  <div className="text-xs font-semibold text-slate-200">{change.metric}</div>
                  <div className="flex items-center space-x-3 text-xs font-mono text-slate-400">
                    <span>Prev: <strong className="text-slate-300">{change.previous}</strong></span>
                    <span>→</span>
                    <span>Curr: <strong className="text-cyan-300">{change.current}</strong></span>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-sm font-bold font-mono text-emerald-400">{change.delta}</div>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {change.impact}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right 1 Col: Fundamental Divergence & Catalyst Box */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Sparkles className="w-5 h-5 text-amber-400" />
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
                Catalyst & Divergence
              </h3>
            </div>

            {intelligence.divergence_detected ? (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 space-y-2 mb-4">
                <div className="flex items-center space-x-2 font-semibold text-xs">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>Divergensi Fundamental Terdeteksi</span>
                </div>
                <p className="text-[11px] leading-relaxed opacity-90">
                  Data fundamental emiten bergerak berlawanan arah dengan tren aksi transaksi ritel / harga jangka pendek. Hal ini sering menandakan pola akumulasi tersembunyi.
                </p>
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-400 text-xs mb-4">
                Tidak ada divergensi esensial yang terdeteksi pada siklus saat ini.
              </div>
            )}

            <div className="space-y-2">
              <div className="text-xs font-semibold text-slate-300">Catalyst Detector:</div>
              <ul className="text-xs text-slate-400 space-y-1.5 list-disc list-inside">
                <li>Akumulasi Asing Beruntun (&gt;Rp 500B)</li>
                <li>Ekspansi Margin Efisiensi Operasional (CIR 34%)</li>
                <li>Pertumbuhan Kredit Konsumer Kuartal II</li>
              </ul>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800/80">
            <span className="text-[10px] text-slate-500 block font-mono">
              Last System Scan: {intelligence.created_at}
            </span>
          </div>
        </div>
      </div>

      {/* Signal Evidence & Peer Comparison Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Evidence Matrix */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center space-x-2 mb-4">
            <Layers className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Signal Relationship & Evidence (Bukti Analitis)
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono">
                  <th className="pb-3 font-semibold">METRIK</th>
                  <th className="pb-3 font-semibold">NILAI EMITEN</th>
                  <th className="pb-3 font-semibold">MEDIAN PEER</th>
                  <th className="pb-3 font-semibold text-right">POSISI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {intelligence.evidence.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 font-medium text-slate-200">{item.metric}</td>
                    <td className="py-3 font-mono font-bold text-cyan-400">{item.company_value}</td>
                    <td className="py-3 font-mono text-slate-400">{item.peer_median}</td>
                    <td className="py-3 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                        {item.position}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Peer Comparison */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center space-x-2 mb-4">
            <Info className="w-5 h-5 text-sky-400" />
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Valuation Peer Matrix
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono">
                  <th className="pb-3 font-semibold">METRIK VALUASI</th>
                  <th className="pb-3 font-semibold">TARGET ({company.symbol})</th>
                  <th className="pb-3 font-semibold">MEDIAN INDUSTRI</th>
                  <th className="pb-3 font-semibold text-right">STATUS VALUASI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {intelligence.peer_comparison.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 font-medium text-slate-200">{item.metric}</td>
                    <td className="py-3 font-mono font-bold text-slate-100">{item.target}</td>
                    <td className="py-3 font-mono text-slate-400">{item.peer_median}</td>
                    <td className="py-3 text-right">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        item.position === 'PREMIUM'
                          ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                          : 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                      }`}>
                        {item.position}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Factors Breakdown: Positive vs Negative */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center space-x-2 text-emerald-400 mb-4">
            <CheckCircle2 className="w-5 h-5" />
            <h3 className="text-sm font-semibold uppercase tracking-wider font-mono">
              Positive Contributing Factors ({intelligence.positive_factors.length})
            </h3>
          </div>
          <ul className="space-y-2.5">
            {intelligence.positive_factors.map((factor, idx) => (
              <li key={idx} className="flex items-start space-x-2 text-xs text-slate-300 leading-relaxed">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center space-x-2 text-rose-400 mb-4">
            <XCircle className="w-5 h-5" />
            <h3 className="text-sm font-semibold uppercase tracking-wider font-mono">
              Risk & Risk Factors ({intelligence.negative_factors.length})
            </h3>
          </div>
          <ul className="space-y-2.5">
            {intelligence.negative_factors.map((factor, idx) => (
              <li key={idx} className="flex items-start space-x-2 text-xs text-slate-300 leading-relaxed">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-1.5 shrink-0" />
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Standardized Evidence Panel */}
      {signalOutput && (
        <EvidencePanel signal={signalOutput} symbol={company.symbol} />
      )}
    </div>
  );
};
