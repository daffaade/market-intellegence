import React, { useState, useEffect, useCallback } from 'react';
import { X, RefreshCw, Check, Loader2, Circle, ChevronRight } from 'lucide-react';
import type { PipelineStage, HealthStatus } from '../../types/api';
import { apiService, getApiBaseUrl, type DataOrigin } from '../../services/mockApi';
import { Button, Segmented, Tag } from '../ui/primitives';
import { cx } from '../../lib/ui';

interface SectorsPipelineInspectorProps {
  stages: PipelineStage[];
  isOpen: boolean;
  onClose: () => void;
  useDummyData: boolean;
  dataOrigin: DataOrigin;
  onToggleDummy: (enabled: boolean) => void;
}

const statusIcon = {
  COMPLETED: <Check className="w-3.5 h-3.5 text-up" />,
  PROCESSING: <Loader2 className="w-3.5 h-3.5 text-warn animate-spin" />,
  PENDING: <Circle className="w-3.5 h-3.5 text-ink-3" />
};

const statusLabel = { COMPLETED: 'Selesai', PROCESSING: 'Berjalan', PENDING: 'Menunggu' };

export const SectorsPipelineInspector: React.FC<SectorsPipelineInspectorProps> = ({
  stages,
  isOpen,
  onClose,
  useDummyData,
  dataOrigin,
  onToggleDummy
}) => {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [checking, setChecking] = useState(false);
  const [checked, setChecked] = useState(false);

  const checkHealth = useCallback(async () => {
    setChecking(true);
    try {
      const res = await apiService.getHealth();
      // getHealth simulates a response in dummy mode; only a real backend counts as online.
      setHealth(res.status === 'success' && res.data && res.data.status !== 'simulated' ? res.data : null);
    } catch {
      setHealth(null);
    } finally {
      setChecking(false);
      setChecked(true);
    }
  }, []);

  useEffect(() => {
    if (isOpen) checkHealth();
  }, [isOpen, checkHealth]);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const totalMs = stages.reduce((a, s) => a + (s.duration_ms || 0), 0);

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center px-4 pt-[8vh] bg-black/40" onMouseDown={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="pipeline-title"
        className="w-full max-w-xl bg-surface border border-line-strong rounded-lg shadow-2xl flex flex-col max-h-[84vh]"
        onMouseDown={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 h-12 border-b border-line shrink-0">
          <h2 id="pipeline-title" className="text-[14px] font-semibold text-ink">Sumber data & pipeline</h2>
          <button onClick={onClose} className="p-1 rounded text-ink-3 hover:text-ink hover:bg-surface-2" aria-label="Tutup">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {/* Data source */}
          <section className="px-5 py-4 border-b border-line">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-[13px] font-medium text-ink">Sumber data</div>
                <p className="text-xs text-ink-3 mt-0.5 leading-relaxed">
                  {useDummyData
                    ? 'Menggunakan 18 emiten simulasi. Tidak ada permintaan ke jaringan.'
                    : 'Mengambil data dari backend Go. Jika backend gagal, data simulasi dipakai dan ditandai.'}
                </p>
              </div>
              <Segmented
                ariaLabel="Sumber data"
                value={useDummyData ? 'dummy' : 'backend'}
                onChange={v => onToggleDummy(v === 'dummy')}
                options={[
                  { value: 'backend', label: 'Backend' },
                  { value: 'dummy', label: 'Simulasi' }
                ]}
              />
            </div>
            {dataOrigin === 'fallback' && (
              <p className="mt-3 text-xs text-down leading-relaxed">
                Sebagian data yang tampil saat ini adalah data simulasi karena backend tidak merespons.
              </p>
            )}
          </section>

          {/* Backend health */}
          <section className="px-5 py-4 border-b border-line">
            <div className="flex items-center justify-between">
              <div className="text-[13px] font-medium text-ink">Status backend</div>
              <Button size="sm" variant="ghost" onClick={checkHealth} disabled={checking}>
                <RefreshCw className={cx('w-3 h-3', checking && 'animate-spin')} />
                {checking ? 'Memeriksa…' : 'Periksa ulang'}
              </Button>
            </div>
            <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-6 gap-y-1.5 text-[13px]">
              <dt className="text-ink-3">Alamat</dt>
              <dd className="num text-ink-2 truncate">{getApiBaseUrl()}</dd>
              <dt className="text-ink-3">Status</dt>
              <dd>
                {!checked ? (
                  <span className="text-ink-3">—</span>
                ) : health ? (
                  <span className="text-up">Online{health.version ? ` · ${health.version}` : ''}</span>
                ) : (
                  <span className="text-down">Tidak merespons</span>
                )}
              </dd>
              <dt className="text-ink-3">Penyedia AI</dt>
              <dd className="text-ink-2">{health?.ai_provider ?? '—'}</dd>
              <dt className="text-ink-3">Model</dt>
              <dd className="num text-ink-2 truncate">{health?.ai_model ?? '—'}</dd>
            </dl>
            {checked && !health && (
              <p className="mt-3 text-xs text-ink-3 leading-relaxed">
                Jalankan backend dengan <code className="num text-ink-2 bg-surface-2 px-1 py-0.5 rounded">go run cmd/api/main.go</code>,
                atau pakai mode simulasi.
              </p>
            )}
          </section>

          {/* Pipeline stages */}
          <section className="px-5 py-4">
            <div className="flex items-baseline justify-between mb-2">
              <div className="text-[13px] font-medium text-ink">Tahapan pipeline</div>
              <div className="text-xs text-ink-3">
                {stages.length} tahap · <span className="num">{totalMs} ms</span>
              </div>
            </div>
            <ol className="relative">
              {stages.map((stage, idx) => {
                const open = expanded === stage.id;
                return (
                  <li key={stage.id} className="relative pl-7">
                    {idx < stages.length - 1 && <span className="absolute left-[9px] top-7 bottom-0 w-px bg-line" aria-hidden="true" />}
                    <span className="absolute left-0 top-2 w-[19px] h-[19px] rounded-full bg-surface border border-line flex items-center justify-center">
                      {statusIcon[stage.status]}
                    </span>
                    <button
                      onClick={() => setExpanded(open ? null : stage.id)}
                      aria-expanded={open}
                      className="w-full text-left py-2 flex items-center gap-3 group"
                    >
                      <span className="min-w-0 flex-1">
                        <span className="block text-[13px] text-ink">{stage.label}</span>
                        <span className="block text-xs text-ink-3 truncate">{stage.data_type}</span>
                      </span>
                      {stage.duration_ms !== undefined && <span className="num text-xs text-ink-3">{stage.duration_ms} ms</span>}
                      {stage.status !== 'COMPLETED' && <Tag tone={stage.status === 'PROCESSING' ? 'warn' : 'neutral'}>{statusLabel[stage.status]}</Tag>}
                      <ChevronRight className={cx('w-3.5 h-3.5 text-ink-3 transition-transform', open && 'rotate-90')} />
                    </button>
                    {open && <p className="pb-3 text-[13px] text-ink-2 leading-relaxed">{stage.description}</p>}
                  </li>
                );
              })}
            </ol>
          </section>
        </div>
      </div>
    </div>
  );
};
