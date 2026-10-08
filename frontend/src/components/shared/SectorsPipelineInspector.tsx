import React, { useState, useEffect, useCallback } from 'react';
import { X, RefreshCw } from 'lucide-react';
import type { HealthStatus } from '../../types/api';
import { useRemote } from '../../lib/useRemote';
import { RemoteBody } from './RemoteState';
import { formatDateTime } from '../../lib/format';
import { apiService, getApiBaseUrl, type DataOrigin } from '../../services/mockApi';
import { Button, Segmented, Tag } from '../ui/primitives';
import { cx } from '../../lib/ui';

interface SectorsPipelineInspectorProps {
  isOpen: boolean;
  onClose: () => void;
  useDummyData: boolean;
  dataOrigin: DataOrigin;
  onToggleDummy: (enabled: boolean) => void;
}

export const SectorsPipelineInspector: React.FC<SectorsPipelineInspectorProps> = ({
  isOpen,
  onClose,
  useDummyData,
  dataOrigin,
  onToggleDummy
}) => {
  const sources = useRemote(() => apiService.getPipelineSources(), [isOpen, useDummyData]);
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

          {/* Data sources: real cache freshness from the engine */}
          <section className="px-5 py-4">
            <div className="flex items-baseline justify-between mb-2">
              <div className="text-[13px] font-medium text-ink">Sumber data</div>
              <button onClick={sources.reload} className="text-xs text-accent hover:underline">Muat ulang</button>
            </div>
            <RemoteBody remote={sources} skeletonClassName="h-32" errorTitle="Status sumber data belum bisa dimuat">
              {data => (
                <ul className="divide-y divide-line">
                  {data.sources.map(src => (
                    <li key={src.key} className="py-3">
                      <div className="flex items-baseline justify-between gap-3">
                        <span className="text-[13px] text-ink">{src.label}</span>
                        <Tag tone={src.provider === 'Sectors' ? 'accent' : 'neutral'}>{src.provider}</Tag>
                      </div>
                      <p className="text-xs text-ink-3 mt-0.5 leading-relaxed">{src.used_for}</p>
                      <p className="text-xs text-ink-2 mt-1">
                        {src.newest
                          ? <>
                              {src.items} tersimpan · terbaru {formatDateTime(src.newest)} · diperbarui tiap{' '}
                              {src.ttl_hours >= 24 ? `${src.ttl_hours / 24} hari` : `${src.ttl_hours} jam`}
                            </>
                          : src.items === null
                            ? `Diambil langsung, cache ${src.ttl_hours} jam, tanpa kuota`
                            : 'Belum ada data tersimpan'}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </RemoteBody>
          </section>
        </div>
      </div>
    </div>
  );
};
