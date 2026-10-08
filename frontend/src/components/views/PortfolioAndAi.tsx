import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Check, Plus, X } from 'lucide-react';
import type { IntelligenceSnapshot, Company } from '../../types/api';
import { apiService } from '../../services/mockApi';
import { useRemote } from '../../lib/useRemote';
import { confidenceLabel } from '../../lib/format';
import { loadPortfolio, savePortfolio, EXAMPLE_PORTFOLIO, type PortfolioHolding } from '../../lib/portfolioStore';
import { RemoteBody, SourceNote } from '../shared/RemoteState';
import { PageHeader, Panel, Stat, ScoreBar, DirectionTag, Button, EmptyState } from '../ui/primitives';
import { cx } from '../../lib/ui';

interface PortfolioAndAiProps {
  intelligence: IntelligenceSnapshot;
  company: Company;
  companies: Company[];
  allIntelligence: IntelligenceSnapshot[];
  onSelectSymbol: (symbol: string) => void;
}

// Risk-management rules used to generate the notes below.
const MAX_HIGH_RISK_WEIGHT = 10; // % allocation cap for a position with risk >= HIGH_RISK
const HIGH_RISK = 60;
const MAX_SECTOR_WEIGHT = 35; // % concentration before a sector is flagged

// Allocation segments use shades of ink so they read as parts of one whole.
const SEGMENT_SHADES = ['bg-ink', 'bg-ink-2', 'bg-ink-3', 'bg-line-strong', 'bg-surface-2'];

const pct = (v: number, digits = 1) => `${(v * 100).toLocaleString('id-ID', { maximumFractionDigits: digits })}%`;

const fieldClass =
  'h-8 px-2 rounded-md bg-canvas border border-line text-[13px] text-ink outline-none focus:border-accent';

export const PortfolioAndAi: React.FC<PortfolioAndAiProps> = ({
  intelligence,
  company,
  companies,
  allIntelligence,
  onSelectSymbol
}) => {
  const [holdings, setHoldings] = useState<PortfolioHolding[]>(loadPortfolio);
  useEffect(() => savePortfolio(holdings), [holdings]);

  const companyBySymbol = useMemo(() => new Map(companies.map(c => [c.symbol, c])), [companies]);
  const intelBySymbol = useMemo(() => new Map(allIntelligence.map(i => [i.symbol, i])), [allIntelligence]);

  const total = holdings.reduce((a, h) => a + (h.weight > 0 ? h.weight : 0), 0);
  const valid = holdings.filter(h => h.weight > 0);

  // Debounce the risk request so typing a weight doesn't fire one call per keystroke.
  const riskKey = JSON.stringify(valid.map(h => [h.symbol, h.weight]));
  const [debouncedKey, setDebouncedKey] = useState(riskKey);
  useEffect(() => {
    const t = setTimeout(() => setDebouncedKey(riskKey), 600);
    return () => clearTimeout(t);
  }, [riskKey]);

  const risk = useRemote(async () => {
    const list: Array<[string, number]> = JSON.parse(debouncedKey);
    const sum = list.reduce((a, [, w]) => a + w, 0);
    if (list.length === 0 || sum <= 0) return { status: 'error' as const, message: 'Portofolio masih kosong.' };
    return apiService.calculatePortfolioRisk(list.map(([ticker, w]) => ({ ticker, weight: w / sum })));
  }, [debouncedKey]);

  const stats = useMemo(() => {
    const positions = valid
      .map(h => {
        const c = companyBySymbol.get(h.symbol);
        const i = intelBySymbol.get(h.symbol);
        return {
          symbol: h.symbol,
          name: c?.name ?? h.symbol,
          sector: c?.sector ?? '—',
          alloc: total ? (h.weight / total) * 100 : 0,
          risk: i?.risk_score,
          opp: i?.opportunity_score
        };
      })
      .sort((a, b) => b.alloc - a.alloc);

    const scored = positions.filter(p => p.risk !== undefined && p.opp !== undefined);
    const scoredWeight = scored.reduce((a, p) => a + p.alloc, 0) || 1;
    const weighted = (key: 'risk' | 'opp') => scored.reduce((a, p) => a + (p[key] ?? 0) * p.alloc, 0) / scoredWeight;

    const bySector = new Map<string, number>();
    positions.forEach(p => bySector.set(p.sector, (bySector.get(p.sector) ?? 0) + p.alloc));
    const sectors = [...bySector.entries()].sort((a, b) => b[1] - a[1]);

    const notes: Array<{ tone: 'warn' | 'ok'; title: string; body: string }> = [];
    positions
      .filter(p => (p.risk ?? 0) >= HIGH_RISK && p.alloc > MAX_HIGH_RISK_WEIGHT)
      .forEach(p =>
        notes.push({
          tone: 'warn',
          title: `${p.symbol} melebihi batas posisi berisiko tinggi`,
          body: `Bobot ${p.alloc.toFixed(1)}% dengan skor risiko ${p.risk}. Batas untuk emiten dengan risiko ≥ ${HIGH_RISK} adalah ${MAX_HIGH_RISK_WEIGHT}%.`
        })
      );
    sectors
      .filter(([, w]) => w > MAX_SECTOR_WEIGHT)
      .forEach(([s, w]) =>
        notes.push({
          tone: 'warn',
          title: `Konsentrasi di sektor ${s}`,
          body: `${w.toFixed(1)}% portofolio berada di satu sektor, di atas ambang ${MAX_SECTOR_WEIGHT}%. Guncangan sektoral akan berdampak besar.`
        })
      );
    if (notes.length === 0 && positions.length) {
      notes.push({ tone: 'ok', title: 'Tidak ada pelanggaran batas risiko', body: 'Semua posisi dan sektor berada di bawah ambang yang ditetapkan.' });
    }

    return { positions, scored: scored.length, risk: weighted('risk'), opp: weighted('opp'), sectors, notes };
  }, [valid, total, companyBySymbol, intelBySymbol]);

  const available = companies.filter(c => !holdings.some(h => h.symbol === c.symbol));
  const [adding, setAdding] = useState('');

  const update = (symbol: string, weight: number) =>
    setHoldings(hs => hs.map(h => (h.symbol === symbol ? { ...h, weight } : h)));
  const remove = (symbol: string) => setHoldings(hs => hs.filter(h => h.symbol !== symbol));
  const add = () => {
    const sym = adding || available[0]?.symbol;
    if (!sym) return;
    setHoldings(hs => [...hs, { symbol: sym, weight: 10 }]);
    setAdding('');
  };

  const metrics = risk.data?.metrics;
  const [topSector, topSectorWeight] = stats.sectors[0] ?? ['—', 0];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Portofolio"
        title="Portofolio & riset"
        description="Ringkasan riset AI untuk emiten yang sedang dibuka, serta evaluasi risiko portofolio Anda dari harga historis 1 tahun."
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

      {holdings.length === 0 ? (
        <Panel title="Portofolio Anda">
          <EmptyState title="Belum ada posisi">
            Tambahkan emiten dan bobotnya untuk melihat volatilitas, VaR, drawdown, dan korelasi antarposisi.
            <span className="flex justify-center gap-2 mt-4">
              <Button size="sm" variant="primary" onClick={() => setHoldings(EXAMPLE_PORTFOLIO)}>Pakai contoh</Button>
              <Button size="sm" onClick={() => setHoldings([{ symbol: companies[0]?.symbol ?? 'BBCA', weight: 100 }])}>
                <Plus className="w-3.5 h-3.5" /> Mulai kosong
              </Button>
            </span>
          </EmptyState>
        </Panel>
      ) : (
        <>
          <section className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line border border-line rounded-lg overflow-hidden [&>*]:bg-surface [&>*]:p-4">
            <Stat
              label="Volatilitas tahunan"
              value={metrics ? pct(metrics.portfolio_volatility) : '—'}
              hint="Deviasi standar return, disetahunkan"
            />
            <Stat
              label="VaR 95% · 1 hari"
              value={metrics ? <span className="text-down">−{pct(metrics.historical_var, 2)}</span> : '—'}
              hint="Kerugian harian yang jarang terlampaui"
            />
            <Stat
              label="Drawdown maksimum"
              value={metrics ? <span className="text-down">{pct(metrics.maximum_drawdown)}</span> : '—'}
              hint="Penurunan terdalam dari puncak, 1 tahun"
            />
            <Stat
              label="Risiko tertimbang"
              value={stats.scored ? <span className={stats.risk >= HIGH_RISK ? 'text-down' : undefined}>{stats.risk.toFixed(1)}</span> : '—'}
              hint={`Peluang tertimbang ${stats.scored ? stats.opp.toFixed(1) : '—'}`}
            />
          </section>
          {risk.error && !risk.loading && (
            <p className="text-xs text-down -mt-3">Metrik risiko belum bisa dihitung: {risk.error}</p>
          )}

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <Panel
              className="xl:col-span-2"
              title="Alokasi"
              meta={
                Math.abs(total - 100) < 0.01
                  ? `${stats.positions.length} posisi · ${stats.sectors.length} sektor`
                  : `Total bobot ${total.toLocaleString('id-ID')}% (dinormalkan ke 100%)`
              }
              flush
            >
              <div className="p-4 border-b border-line">
                <div className="flex h-2.5 rounded-full overflow-hidden gap-0.5 bg-surface-2">
                  {stats.positions.map((p, i) => (
                    <div
                      key={p.symbol}
                      className={SEGMENT_SHADES[i % SEGMENT_SHADES.length]}
                      style={{ width: `${p.alloc}%` }}
                      title={`${p.symbol} ${p.alloc.toFixed(1)}%`}
                    />
                  ))}
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px]">
                  <thead className="border-b border-line">
                    <tr className="text-left text-xs text-ink-3">
                      <th className="px-4 h-9 font-medium">Emiten</th>
                      <th className="px-4 h-9 font-medium">Bobot</th>
                      <th className="px-4 h-9 font-medium text-right" title="Porsi volatilitas portofolio yang berasal dari posisi ini">Kontribusi risiko</th>
                      <th className="px-4 h-9 font-medium">Risiko</th>
                      <th className="px-4 h-9 font-medium">Peluang</th>
                      <th className="px-2 h-9" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {stats.positions.map((p, i) => {
                      const contrib = metrics?.risk_contribution[p.symbol];
                      const raw = holdings.find(h => h.symbol === p.symbol)?.weight ?? 0;
                      return (
                        <tr key={p.symbol} className="hover:bg-surface-2">
                          <td className="px-4 h-11">
                            <button onClick={() => onSelectSymbol(p.symbol)} className="flex items-center gap-2.5 min-w-[180px] text-left">
                              <span className={cx('w-2 h-2 rounded-sm shrink-0', SEGMENT_SHADES[i % SEGMENT_SHADES.length])} />
                              <span className="num font-medium text-ink">{p.symbol}</span>
                              <span className="text-ink-2 truncate max-w-[160px]">{p.name}</span>
                            </button>
                          </td>
                          <td className="px-4 h-11">
                            <label className="inline-flex items-center gap-1">
                              <span className="sr-only">Bobot {p.symbol}</span>
                              <input
                                type="number"
                                min={0}
                                max={100}
                                step={1}
                                value={raw}
                                onChange={e => update(p.symbol, Math.max(0, Number(e.target.value) || 0))}
                                className={cx(fieldClass, 'num w-16 text-right')}
                              />
                              <span className="text-xs text-ink-3">%</span>
                            </label>
                          </td>
                          <td className="px-4 h-11 num text-right text-ink-2">
                            {contrib !== undefined ? pct(contrib) : risk.loading ? '…' : '—'}
                          </td>
                          <td className="px-4 h-11">{p.risk !== undefined ? <ScoreBar value={p.risk} tone="risk" width="w-14" /> : <span className="text-xs text-ink-3">Belum dinilai</span>}</td>
                          <td className="px-4 h-11">{p.opp !== undefined ? <ScoreBar value={p.opp} width="w-14" /> : null}</td>
                          <td className="px-2 h-11 text-right">
                            <button onClick={() => remove(p.symbol)} className="p-1 rounded text-ink-3 hover:text-ink hover:bg-surface-2" aria-label={`Hapus ${p.symbol}`}>
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                    {holdings.filter(h => h.weight <= 0).map(h => (
                      <tr key={h.symbol}>
                        <td className="px-4 h-11 num text-ink-3">{h.symbol}</td>
                        <td className="px-4 h-11" colSpan={4}>
                          <input
                            type="number"
                            min={0}
                            value={h.weight}
                            onChange={e => update(h.symbol, Math.max(0, Number(e.target.value) || 0))}
                            className={cx(fieldClass, 'num w-16 text-right')}
                            aria-label={`Bobot ${h.symbol}`}
                          />
                          <span className="text-xs text-ink-3 ml-2">Bobot 0, tidak dihitung</span>
                        </td>
                        <td className="px-2 h-11 text-right">
                          <button onClick={() => remove(h.symbol)} className="p-1 rounded text-ink-3 hover:text-ink" aria-label={`Hapus ${h.symbol}`}>
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="px-4 py-3 border-t border-line flex flex-wrap items-center gap-2">
                {available.length > 0 && (
                  <>
                    <select value={adding} onChange={e => setAdding(e.target.value)} className={fieldClass} aria-label="Emiten yang ditambahkan">
                      {available.map(c => <option key={c.symbol} value={c.symbol}>{c.symbol} · {c.name}</option>)}
                    </select>
                    <Button size="sm" onClick={add}><Plus className="w-3.5 h-3.5" /> Tambah</Button>
                  </>
                )}
                <span className="text-xs text-ink-3 ml-auto">Tersimpan di perangkat ini</span>
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
                Sektor terbesar: {topSector} ({topSectorWeight.toFixed(1)}%).
              </div>
            </Panel>
          </div>

          <Panel title="Korelasi antarposisi" meta="Return harian, 1 tahun" flush>
            <RemoteBody remote={risk} skeletonClassName="h-40" errorTitle="Korelasi belum bisa dihitung">
              {data => <CorrelationMatrix matrix={data.metrics.correlation_matrix} vol={data.metrics.individual_volatility} />}
            </RemoteBody>
          </Panel>
          <SourceNote source="Harga Yahoo Finance, dihitung oleh AI engine">
            {risk.data?.disclaimer ?? 'Bukan rekomendasi Beli/Jual.'}
          </SourceNote>
        </>
      )}
    </div>
  );
};

/** Correlation heatmap: accent intensity = correlation strength, diagonal shows volatility. */
const CorrelationMatrix: React.FC<{
  matrix: Record<string, Record<string, number>>;
  vol: Record<string, number>;
}> = ({ matrix, vol }) => {
  const syms = Object.keys(matrix);
  if (syms.length < 2) {
    return <EmptyState title="Butuh minimal dua posisi untuk melihat korelasi" />;
  }
  return (
    <div className="p-4 overflow-x-auto">
      <table className="text-xs border-separate" style={{ borderSpacing: 3 }}>
        <thead>
          <tr>
            <th />
            {syms.map(s => <th key={s} className="num font-medium text-ink-2 px-1 pb-1">{s}</th>)}
          </tr>
        </thead>
        <tbody>
          {syms.map(row => (
            <tr key={row}>
              <th className="num font-medium text-ink-2 text-left pr-2">{row}</th>
              {syms.map(col => {
                const v = matrix[row]?.[col] ?? 0;
                const diag = row === col;
                return (
                  <td
                    key={col}
                    className={cx('num w-16 h-10 text-center rounded', diag ? 'text-ink-3 bg-surface-2' : Math.abs(v) > 0.5 ? 'text-canvas' : 'text-ink')}
                    style={diag ? undefined : { background: `color-mix(in srgb, var(--accent) ${Math.round(Math.abs(v) * 100)}%, var(--surface-2))` }}
                    title={diag ? `Volatilitas ${row}` : `Korelasi ${row}–${col}`}
                  >
                    {diag ? pct(vol[row] ?? 0, 0) : v.toFixed(2)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-ink-3 mt-3 max-w-xl leading-relaxed">
        Mendekati 1 berarti dua saham cenderung bergerak bersama, sehingga diversifikasinya kecil. Diagonal menunjukkan volatilitas tahunan masing-masing saham.
      </p>
    </div>
  );
};
