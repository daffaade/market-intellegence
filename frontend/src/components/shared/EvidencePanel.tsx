import React from 'react';
import type { IntelligenceSnapshot, StandardizedSignalOutput } from '../../types/api';
import { Panel, Tag, EmptyState } from '../ui/primitives';

interface EvidencePanelProps {
  intelligence: IntelligenceSnapshot;
  signal?: StandardizedSignalOutput;
  symbol: string;
}

const positionTag = (position: string): { label: string; tone: 'up' | 'down' | 'warn' | 'neutral' } => {
  switch (position) {
    case 'TOP_10_PERCENT': return { label: '10% teratas', tone: 'up' };
    case 'BOTTOM_10_PERCENT': return { label: '10% terbawah', tone: 'down' };
    case 'PREMIUM': return { label: 'Premium', tone: 'warn' };
    case 'DISCOUNT': return { label: 'Diskon', tone: 'up' };
    case 'FAIR': return { label: 'Wajar', tone: 'neutral' };
    // Vocabulary the Go backend actually sends from a live engine analysis
    // (see internal/adapter/python_engine/client.go's relative_positions mapping).
    case 'Outperform': return { label: 'Di atas peer', tone: 'up' };
    case 'Underperform': return { label: 'Di bawah peer', tone: 'down' };
    case 'Cheaper': return { label: 'Lebih murah', tone: 'up' };
    case 'Superior': return { label: 'Lebih unggul', tone: 'up' };
    case 'Stronger': return { label: 'Lebih kuat', tone: 'up' };
    case 'Weaker': return { label: 'Lebih lemah', tone: 'down' };
    case 'Neutral': return { label: 'Netral', tone: 'neutral' };
    default: return { label: position, tone: 'neutral' };
  }
};

const strengthLabel = { STRONG: 'Kuat', MODERATE: 'Sedang', WEAK: 'Lemah' } as const;

const CompareTable: React.FC<{
  rows: Array<{ metric: string; value: string; median: string; position: string }>;
  valueHeader: string;
}> = ({ rows, valueHeader }) => (
  <div className="overflow-x-auto">
    <table className="w-full text-[13px]">
      <thead className="border-b border-line">
        <tr className="text-left text-xs text-ink-3">
          <th className="px-4 h-9 font-medium">Metrik</th>
          <th className="px-4 h-9 font-medium text-right">{valueHeader}</th>
          <th className="px-4 h-9 font-medium text-right">Median peer</th>
          <th className="px-4 h-9 font-medium text-right">Posisi</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-line">
        {rows.map((r, i) => {
          const tag = positionTag(r.position);
          return (
            <tr key={i}>
              <td className="px-4 h-10 text-ink">{r.metric}</td>
              <td className="px-4 h-10 num text-ink text-right">{r.value}</td>
              <td className="px-4 h-10 num text-ink-3 text-right">{r.median}</td>
              <td className="px-4 h-10 text-right"><Tag tone={tag.tone}>{tag.label}</Tag></td>
            </tr>
          );
        })}
      </tbody>
    </table>
  </div>
);

/** Metrics and valuation of an emiten against its peer median, plus related signals. */
export const EvidencePanel: React.FC<EvidencePanelProps> = ({ intelligence, signal, symbol }) => {
  const evidence = signal?.evidence.length ? signal.evidence : intelligence.evidence;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Panel title="Bukti kinerja" meta="Dibanding median peer" flush>
          {evidence.length ? (
            <CompareTable
              valueHeader={symbol}
              rows={evidence.map(e => ({ metric: e.metric, value: e.company_value, median: e.peer_median, position: e.position }))}
            />
          ) : (
            <EmptyState title="Belum ada bukti metrik" />
          )}
        </Panel>

        <Panel title="Valuasi" meta="Dibanding median industri" flush>
          {intelligence.peer_comparison.length ? (
            <CompareTable
              valueHeader={symbol}
              rows={intelligence.peer_comparison.map(p => ({ metric: p.metric, value: p.target, median: p.peer_median, position: p.position }))}
            />
          ) : (
            <EmptyState title="Belum ada data valuasi peer" />
          )}
        </Panel>
      </div>

      {signal && signal.related_signals.length > 0 && (
        <Panel title="Sinyal terkait" meta={String(signal.related_signals.length)} flush>
          <ul className="divide-y divide-line">
            {signal.related_signals.map((rs, i) => (
              <li key={i} className="px-4 py-3 flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="text-[13px] font-medium text-ink">{rs.signal_type}</div>
                  <p className="text-[13px] text-ink-2 mt-0.5 leading-relaxed">{rs.description}</p>
                </div>
                <span className="text-xs text-ink-3 shrink-0 mt-0.5">
                  Kekuatan <span className="text-ink-2 font-medium">{strengthLabel[rs.strength]}</span>
                </span>
              </li>
            ))}
          </ul>
        </Panel>
      )}
    </div>
  );
};
