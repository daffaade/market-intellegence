import React from 'react';
import { AlertTriangle } from 'lucide-react';
import type { IntelligenceSnapshot, Company, StandardizedSignalOutput, WhatChangedItem } from '../../types/api';
import { EvidencePanel } from '../shared/EvidencePanel';
import { EmitenHeader } from '../shared/EmitenHeader';
import { confidenceLabel, opportunityBand, riskLevelLabel } from '../../lib/format';
import { Panel, Tag, EmptyState } from '../ui/primitives';
import { cx } from '../../lib/ui';

interface SignalIntelligenceProps {
  intelligence: IntelligenceSnapshot;
  company: Company;
  signalOutput?: StandardizedSignalOutput;
  onOpenSearch: () => void;
  isWatched: boolean;
  onToggleWatchlist: (symbol: string) => void;
}

const impactTag: Record<WhatChangedItem['impact'], { label: string; tone: 'up' | 'down' | 'neutral' }> = {
  HIGH_BULLISH: { label: 'Positif kuat', tone: 'up' },
  MODERATE_BULLISH: { label: 'Positif', tone: 'up' },
  NEUTRAL: { label: 'Netral', tone: 'neutral' },
  MODERATE_BEARISH: { label: 'Negatif', tone: 'down' },
  HIGH_BEARISH: { label: 'Negatif kuat', tone: 'down' }
};

const ScoreCell: React.FC<{
  label: string;
  value: number;
  verdict: string;
  verdictClass?: string;
  fill: string;
  caption: string;
}> = ({ label, value, verdict, verdictClass, fill, caption }) => (
  <div>
    <div className="flex items-baseline justify-between">
      <span className="text-xs text-ink-3">{label}</span>
      <span className={cx('text-xs font-medium', verdictClass ?? 'text-ink-2')}>{verdict}</span>
    </div>
    <div className="num text-[40px] leading-none text-ink mt-3">
      {Number.isInteger(value) ? value : value.toFixed(1)}
      <span className="text-base text-ink-3 ml-1">/100</span>
    </div>
    <div className="h-1.5 rounded-full bg-surface-2 mt-4 overflow-hidden">
      <div className={cx('h-full rounded-full', fill)} style={{ width: `${Math.min(100, value)}%` }} />
    </div>
    <p className="text-xs text-ink-3 mt-2.5 leading-relaxed">{caption}</p>
  </div>
);

const FactorList: React.FC<{ items: string[]; marker: string; empty: string }> = ({ items, marker, empty }) =>
  items.length ? (
    <ul className="space-y-2.5">
      {items.map((f, i) => (
        <li key={i} className="flex gap-2.5 text-[13px] text-ink-2 leading-relaxed">
          <span className={cx('mt-[7px] w-1.5 h-1.5 rounded-full shrink-0', marker)} />
          <span>{f}</span>
        </li>
      ))}
    </ul>
  ) : (
    <p className="text-[13px] text-ink-3">{empty}</p>
  );

export const SignalIntelligence: React.FC<SignalIntelligenceProps> = ({
  intelligence,
  company,
  signalOutput,
  onOpenSearch,
  isWatched,
  onToggleWatchlist
}) => {
  const isHighRisk = intelligence.risk_level === 'HIGH' || intelligence.risk_level === 'CRITICAL';

  return (
    <div className="space-y-6">
      <EmitenHeader
        company={company}
        intelligence={intelligence}
        section="Sinyal"
        onOpenSearch={onOpenSearch}
        isWatched={isWatched}
        onToggleWatchlist={onToggleWatchlist}
      />

      {/* Scores */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-px bg-line border border-line rounded-lg overflow-hidden [&>*]:bg-surface [&>*]:p-5">
        <ScoreCell
          label="Skor peluang"
          value={intelligence.opportunity_score}
          verdict={opportunityBand(intelligence.opportunity_score)}
          fill="bg-accent"
          caption="Gabungan arus dana asing, profitabilitas, dan momentum pertumbuhan."
        />
        <ScoreCell
          label="Skor risiko"
          value={intelligence.risk_score}
          verdict={`Risiko ${riskLevelLabel[intelligence.risk_level].toLowerCase()}`}
          verdictClass={isHighRisk ? 'text-down' : intelligence.risk_level === 'MODERATE' ? 'text-warn' : 'text-ink-2'}
          fill={isHighRisk ? 'bg-down' : intelligence.risk_level === 'MODERATE' ? 'bg-warn' : 'bg-ink-3'}
          caption="Volatilitas valuasi, eksposur makro, dan tekanan distribusi."
        />
        <div className="flex flex-col">
          <div className="text-xs text-ink-3">Keyakinan model</div>
          <div className="text-[28px] leading-none text-ink mt-3 font-medium">
            {confidenceLabel[intelligence.confidence]}
          </div>
          <div className="mt-auto pt-5 space-y-2 text-[13px]">
            <div className="flex justify-between">
              <span className="text-ink-3">Anomali</span>
              {intelligence.is_anomaly ? (
                <span className="text-warn num">Ya · {intelligence.anomaly_score}</span>
              ) : (
                <span className="text-ink-2">Tidak</span>
              )}
            </div>
            <div className="flex justify-between">
              <span className="text-ink-3">Divergensi fundamental</span>
              <span className={intelligence.divergence_detected ? 'text-warn' : 'text-ink-2'}>
                {intelligence.divergence_detected ? 'Terdeteksi' : 'Tidak'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-3">Sumber</span>
              <span className="text-ink-2">{intelligence.is_cached ? 'Cache' : 'Hasil baru'}</span>
            </div>
          </div>
        </div>
      </section>

      {intelligence.divergence_detected && (
        <div className="flex gap-3 p-4 rounded-lg border border-warn/30 bg-warn-soft">
          <AlertTriangle className="w-4 h-4 text-warn shrink-0 mt-0.5" />
          <div className="text-[13px] leading-relaxed">
            <div className="font-medium text-ink">Fundamental dan harga bergerak berlawanan</div>
            <p className="text-ink-2 mt-0.5">
              {intelligence.direction === 'BEARISH'
                ? `Perbaikan sebagian indikator ${company.symbol} belum diikuti arus dana; tekanan jual tetap dominan. Divergensi negatif seperti ini sering mendahului koreksi lanjutan.`
                : `Data fundamental ${company.symbol} menguat sementara pergerakan harga jangka pendek tidak mengikuti. Pola ini kerap muncul saat terjadi akumulasi yang belum tercermin di harga.`}{' '}
              Periksa bukti di bawah sebelum menyimpulkan.
            </p>
          </div>
        </div>
      )}

      {/* Finding — standardized output when available, otherwise the AI summary */}
      <Panel title="Temuan utama" meta={signalOutput ? `Skor komposit ${signalOutput.score.composite}` : 'Ringkasan AI'}>
        <p className="text-[15px] leading-relaxed text-ink max-w-3xl">
          {signalOutput?.finding ?? (intelligence.ai_research_summary || 'Belum ada ringkasan untuk emiten ini.')}
        </p>
        {signalOutput?.explanation && (
          <p className="text-[13px] leading-relaxed text-ink-2 mt-3 max-w-3xl">{signalOutput.explanation}</p>
        )}
      </Panel>

      {/* Factors */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Panel title="Faktor pendorong" meta={String(intelligence.positive_factors.length)}>
          <FactorList items={intelligence.positive_factors} marker="bg-up" empty="Tidak ada faktor pendorong yang tercatat." />
        </Panel>
        <Panel title="Faktor penekan" meta={String(intelligence.negative_factors.length)}>
          <FactorList items={intelligence.negative_factors} marker="bg-down" empty="Tidak ada faktor penekan yang tercatat." />
        </Panel>
        <Panel title="Katalis pendukung" meta={String(intelligence.supporting_factors.length)}>
          <FactorList items={intelligence.supporting_factors} marker="bg-ink-3" empty="Belum ada katalis yang teridentifikasi." />
        </Panel>
      </div>

      {/* What changed */}
      <Panel title="Yang berubah" meta="Dibanding periode sebelumnya" flush>
        {intelligence.what_changed.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead className="border-b border-line">
                <tr className="text-left text-xs text-ink-3">
                  <th className="px-4 h-9 font-medium">Metrik</th>
                  <th className="px-4 h-9 font-medium text-right">Sebelum</th>
                  <th className="px-4 h-9 font-medium text-right">Sekarang</th>
                  <th className="px-4 h-9 font-medium text-right">Perubahan</th>
                  <th className="px-4 h-9 font-medium text-right">Dampak</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {intelligence.what_changed.map((c, i) => {
                  const tag = impactTag[c.impact] ?? impactTag.NEUTRAL;
                  return (
                    <tr key={i}>
                      <td className="px-4 h-10 text-ink">{c.metric}</td>
                      <td className="px-4 h-10 num text-ink-3 text-right">{c.previous}</td>
                      <td className="px-4 h-10 num text-ink text-right">{c.current}</td>
                      <td className={cx('px-4 h-10 num text-right', tag.tone === 'up' ? 'text-up' : tag.tone === 'down' ? 'text-down' : 'text-ink-2')}>
                        {c.delta}
                      </td>
                      <td className="px-4 h-10 text-right"><Tag tone={tag.tone}>{tag.label}</Tag></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title="Belum ada data perubahan antar-periode" />
        )}
      </Panel>

      {/* Evidence vs peers & valuation */}
      <EvidencePanel intelligence={intelligence} signal={signalOutput} symbol={company.symbol} />

      <p className="text-xs text-ink-3 leading-relaxed max-w-3xl">{intelligence.disclaimer}</p>
    </div>
  );
};
