import React from 'react';
import { RotateCcw } from 'lucide-react';
import type { Remote } from '../../lib/useRemote';
import { EmptyState } from '../ui/primitives';

/**
 * Renders a panel body for a remote resource: a skeleton on first load, an
 * error with a retry button, or the children once data is in.
 */
export function RemoteBody<T>({
  remote,
  skeletonClassName = 'h-48',
  errorTitle = 'Data belum bisa dimuat',
  children
}: {
  remote: Remote<T>;
  skeletonClassName?: string;
  errorTitle?: string;
  children: (data: T) => React.ReactNode;
}) {
  if (remote.data) return <>{children(remote.data)}</>;
  if (remote.loading) {
    return <div className={`animate-pulse bg-surface-2 rounded-md m-4 ${skeletonClassName}`} aria-busy="true" />;
  }
  return (
    <EmptyState title={errorTitle}>
      <span className="block">{remote.error}</span>
      <button
        onClick={remote.reload}
        className="mt-3 inline-flex items-center gap-1.5 text-xs text-accent hover:underline"
      >
        <RotateCcw className="w-3 h-3" /> Coba lagi
      </button>
    </EmptyState>
  );
}

/** "Sumber · diperbarui" footnote shown under live data. */
export const SourceNote: React.FC<{ source: string; date?: string | null; children?: React.ReactNode }> = ({
  source,
  date,
  children
}) => (
  <p className="text-xs text-ink-3">
    Sumber: <span className="text-ink-2">{source}</span>
    {date && (
      <>
        {' · '}data per <span className="num text-ink-2">{formatDay(date)}</span>
      </>
    )}
    {children && <> · {children}</>}
  </p>
);

export const formatDay = (value: string): string => {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
};
