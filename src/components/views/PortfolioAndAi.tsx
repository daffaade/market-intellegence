import React, { useMemo } from 'react';
import { AlertTriangle, Check } from 'lucide-react';
import type { IntelligenceSnapshot, Company, DisasterRisk } from '../../types/api';
import { MOCK_PORTFOLIO, MOCK_DISASTER_RISKS } from '../../services/mockData';
import { confidenceLabel } from '../../lib/format';
import { PageHeader, Panel, Stat, ScoreBar, Tag, DirectionTag } from '../ui/primitives';
import { cx } from '../../lib/ui';

interface PortfolioAndAiProps {
  intelligence: IntelligenceSnapshot;
  company: Company;
  onSelectSymbol: (symbol: string) => void;
}

// Risk-management rules used to generate the notes below.
const MAX_HIGH_RISK_WEIGHT = 10; // % allocation cap for a position with risk >= HIGH_RISK
const HIGH_RISK = 60;
const MAX_SECTOR_WEIGHT = 35; // % concentration before a sector is flagged

const severityTone: Record<DisasterRisk['severity'], 'neutral' | 'warn' | 'down'> = {
  LOW: 'neutral',
  MEDIUM: 'warn',
  HIGH: 'down',
  SEVERE: 'down'
};
const severityLabel: Record<DisasterRisk['severity'], string> = {
  LOW: 'Rendah',
  MEDIUM: 'Sedang',
  HIGH: 'Tinggi',
  SEVERE: 'Parah'
};

// Allocation segments use shades of ink so they read as parts of one whole.
const SEGMENT_SHADES = ['bg-ink', 'bg-ink-2', 'bg-ink-3', 'bg-line-strong', 'bg-surface-2'];

export const PortfolioAndAi: React.FC<PortfolioAndAiProps> = ({ intelligence, company, onSelectSymbol }) => {
  const stats = useMemo(() => {
    const positions = [...MOCK_PORTFOLIO].sort((a, b) => b.allocation_pct - a.allocation_pct);
    const total = positions.reduce((a, p) => a + p.allocation_pct, 0) || 1;
    const weighted = (key: 'risk_score' | 'opportunity_score') =>
      positions.reduce((a, p) => a + p[key] * p.allocation_pct, 0) / total;

    const bySector = new Map<string, number>();
    positions.forEach(p => bySector.set(p.sector, (bySector.get(p.sector) ?? 0) + p.allocation_pct));
    const sectors = [...bySector.entries()].sort((a, b) => b[1] - a[1]);

    const notes: Array<{ tone: 'warn' | 'ok'; title: string; body: string }> = [];
    positions
      .filter(p => p.risk_score >= HIGH_RISK && p.allocation_pct > MAX_HIGH_RISK_WEIGHT)
      .forEach(p =>
        notes.push({
          tone: 'warn',
          title: `${p.symbol} melebihi batas posisi berisiko tinggi`,
          body: `Bobot ${p.allocation_pct}% dengan skor risiko ${p.risk_score}. Batas yang disarankan untuk emiten dengan risiko ≥ ${HIGH_RISK} adalah ${MAX_HIGH_RISK_WEIGHT}%.`
        })
      );
    sectors
      .filter(([, w]) => w > MAX_SECTOR_WEIGHT)
      .forEach(([s, w]) =>
        notes.push({
          tone: 'warn',
          title: `Konsentrasi di sektor ${s}`,
          body: `${w}% portofolio berada di satu sektor, di atas ambang ${MAX_SECTOR_WEIGHT}%. Guncangan sektoral akan berdampak besar.`
        })
      );
    if (notes.length === 0) {
      notes.push({ tone: 'ok', title: 'Tidak ada pelanggaran batas risiko', body: 'Semua posisi dan sektor berada di bawah ambang yang ditetapkan.' });
    }

    return {
      positions,
      total,
      risk: weighted('risk_score'),
      opp: weighted('opportunity_score'),
      sectors,
      notes
    };
  }, []);

  const [topSector, topSectorWeight] = stats.sectors[0] ?? ['—', 0];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Portofolio"
        title="Portofolio & riset"
        description="Ringkasan riset AI untuk emiten yang sedang dibuka, serta evaluasi risiko portofolio contoh."
      />

      {/* AI research summary */}
      <Panel
        title={`Ringkasan riset · ${company.symbol}`}
        meta={company.name}
        actions={<DirectionTag direction={intelligence.direction} />}
      >
        <p className="text-[15px] leading-[1.7] text-ink max-w-3xl">
          {intelligence.ai_research_summary || 'Ringkasan riset untuk emiten ini belum tersedia.'}
        </p>
        <div className="mt-4 pt-3 border-t border-line flex flex-wrap gap-x-6 gap-y-1 text-xs text-ink-3">
          <span>Keyakinan model <span className="text-ink-2">{confidenceLabel[intelligence.confidence]}</span></span>
          <span>Sumber data <span className="text-ink-2">Laporan keuangan & data IDX</span></span>
          <span>Dihasilkan oleh model bahasa — verifikasi sebelum mengambil keputusan.</span>
        </div>
        <p className="text-xs text-ink-3 mt-2 leading-relaxed max-w-3xl">{intelligence.disclaimer}</p>
      </Panel>

      {/* Portfolio */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line border border-line rounded-lg overflow-hidden [&>*]:bg-surface [&>*]:p-4">
        <Stat label="Posisi" value={stats.positions.length} hint={`${stats.sectors.length} sektor`} />
        <Stat
          label="Risiko tertimbang"
          value={<span className={stats.risk >= HIGH_RISK ? 'text-down' : undefined}>{stats.risk.toFixed(1)}</span>}
          hint="Rata-rata skor risiko × bobot"
        />
        <Stat label="Peluang tertimbang" value={stats.opp.toFixed(1)} hint="Rata-rata skor peluang × bobot" />
        <Stat
          label="Sektor terbesar"
          value={<span className={topSectorWeight > MAX_SECTOR_WEIGHT ? 'text-warn' : undefined}>{topSectorWeight}%</span>}
          hint={topSector}
        />
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Panel className="xl:col-span-2" title="Alokasi" meta="Portofolio contoh" flush>
          <div className="p-4 border-b border-line">
            <div className="flex h-2.5 rounded-full overflow-hidden gap-0.5">
              {stats.positions.map((p, i) => (
                <div
                  key={p.symbol}
                  className={SEGMENT_SHADES[i % SEGMENT_SHADES.length]}
                  style={{ width: `${(p.allocation_pct / stats.total) * 100}%` }}
                  title={`${p.symbol} ${p.allocation_pct}%`}
                />
              ))}
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead className="border-b border-line">
                <tr className="text-left text-xs text-ink-3">
                  <th className="px-4 h-9 font-medium">Emiten</th>
                  <th className="px-4 h-9 font-medium">Sektor</th>
                  <th className="px-4 h-9 font-medium text-right">Bobot</th>
                  <th className="px-4 h-9 font-medium">Risiko</th>
                  <th className="px-4 h-9 font-medium">Peluang</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {stats.positions.map((p, i) => (
                  <tr key={p.symbol} onClick={() => onSelectSymbol(p.symbol)} className="hover:bg-surface-2 cursor-pointer">
                    <td className="px-4 h-11">
                      <div className="flex items-center gap-2.5 min-w-[180px]">
                        <span className={cx('w-2 h-2 rounded-sm shrink-0', SEGMENT_SHADES[i % SEGMENT_SHADES.length])} />
                        <span className="num font-medium text-ink">{p.symbol}</span>
                        <span className="text-ink-2 truncate">{p.name}</span>
                      </div>
                    </td>
                    <td className="px-4 h-11 text-ink-2 whitespace-nowrap">{p.sector}</td>
                    <td className="px-4 h-11 num text-ink text-right">{p.allocation_pct}%</td>
                    <td className="px-4 h-11"><ScoreBar value={p.risk_score} tone="risk" width="w-16" /></td>
                    <td className="px-4 h-11"><ScoreBar value={p.opportunity_score} width="w-16" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Catatan risiko" meta={`${stats.notes.filter(n => n.tone === 'warn').length} peringatan`} flush>
          <ul className="divide-y divide-line">
            {stats.notes.map((n, i) => (
              <li key={i} className="px-4 py-3 flex gap-2.5">
                {n.tone === 'warn' ? (
                  <AlertTriangle className="w-4 h-4 text-warn shrink-0 mt-0.5" />
                ) : (
                  <Check className="w-4 h-4 text-up shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="text-[13px] font-medium text-ink">{n.title}</div>
                  <p className="text-[13px] text-ink-2 mt-0.5 leading-relaxed">{n.body}</p>
                </div>
              </li>
            ))}
          </ul>
          <div className="px-4 py-3 border-t border-line text-xs text-ink-3 leading-relaxed">
            Aturan: posisi berisiko ≥ {HIGH_RISK} maks. {MAX_HIGH_RISK_WEIGHT}%, satu sektor maks. {MAX_SECTOR_WEIGHT}%.
          </div>
        </Panel>
      </div>

      <Panel title="Risiko bencana & operasional" meta="Wilayah operasi emiten" flush>
        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead className="border-b border-line">
              <tr className="text-left text-xs text-ink-3">
                <th className="px-4 h-9 font-medium">Wilayah</th>
                <th className="px-4 h-9 font-medium">Jenis risiko</th>
                <th className="px-4 h-9 font-medium">Tingkat</th>
                <th className="px-4 h-9 font-medium">Operasi terdampak</th>
                <th className="px-4 h-9 font-medium">Mitigasi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {MOCK_DISASTER_RISKS.map(r => (
                <tr key={r.region}>
                  <td className="px-4 py-3 text-ink align-top">{r.region}</td>
                  <td className="px-4 py-3 text-ink-2 align-top">{r.risk_type}</td>
                  <td className="px-4 py-3 align-top"><Tag tone={severityTone[r.severity]}>{severityLabel[r.severity]}</Tag></td>
                  <td className="px-4 py-3 text-ink-2 align-top">{r.impacted_operations}</td>
                  <td className="px-4 py-3 text-ink-2 align-top">{r.mitigation_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
};
