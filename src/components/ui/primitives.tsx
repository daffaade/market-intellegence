import React from 'react';
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';
import type { Direction } from '../../lib/format';
import { directionLabel } from '../../lib/format';
import { cx, directionTone, type Tone } from '../../lib/ui';


// ─── Layout ────────────────────────────────────────────────────

export const PageHeader: React.FC<{
  eyebrow?: React.ReactNode;
  title: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
}> = ({ eyebrow, title, description, actions }) => (
  <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between pb-5 border-b border-line">
    <div className="min-w-0">
      {eyebrow && <div className="text-xs text-ink-3 mb-1.5">{eyebrow}</div>}
      <h1 className="text-[22px] leading-tight font-semibold tracking-tight text-ink">{title}</h1>
      {description && <p className="text-[13px] text-ink-2 mt-1.5 max-w-2xl leading-relaxed">{description}</p>}
    </div>
    {actions && <div className="flex flex-wrap items-center gap-2 shrink-0">{actions}</div>}
  </header>
);

export const Panel: React.FC<{
  title?: React.ReactNode;
  meta?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
  flush?: boolean;
}> = ({ title, meta, actions, children, className, bodyClassName, flush }) => (
  <section className={cx('bg-surface border border-line rounded-lg min-w-0', className)}>
    {(title || actions || meta) && (
      <div className="flex items-center justify-between gap-3 px-4 h-11 border-b border-line">
        <div className="flex items-baseline gap-2 min-w-0">
          {title && <h2 className="text-[13px] font-semibold text-ink truncate">{title}</h2>}
          {meta && <span className="text-xs text-ink-3 truncate">{meta}</span>}
        </div>
        {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
      </div>
    )}
    <div className={cx(!flush && 'p-4', bodyClassName)}>{children}</div>
  </section>
);

export const EmptyState: React.FC<{ title: string; children?: React.ReactNode }> = ({ title, children }) => (
  <div className="py-10 px-4 text-center">
    <div className="text-[13px] font-medium text-ink-2">{title}</div>
    {children && <div className="text-xs text-ink-3 mt-1 max-w-sm mx-auto leading-relaxed">{children}</div>}
  </div>
);

// ─── Controls ──────────────────────────────────────────────────

export const Button: React.FC<
  React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost'; size?: 'sm' | 'md' }
> = ({ variant = 'secondary', size = 'md', className, children, ...rest }) => (
  <button
    {...rest}
    className={cx(
      'inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors disabled:opacity-50 whitespace-nowrap',
      size === 'sm' ? 'h-7 px-2.5 text-xs' : 'h-8 px-3 text-[13px]',
      variant === 'primary' && 'bg-ink text-canvas hover:opacity-90',
      variant === 'secondary' && 'bg-surface border border-line-strong text-ink hover:bg-surface-2',
      variant === 'ghost' && 'text-ink-2 hover:text-ink hover:bg-surface-2',
      className
    )}
  >
    {children}
  </button>
);

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  ariaLabel
}: {
  options: Array<{ value: T; label: string }>;
  value: T;
  onChange: (v: T) => void;
  ariaLabel?: string;
}) {
  return (
    <div role="radiogroup" aria-label={ariaLabel} className="inline-flex p-0.5 rounded-md bg-surface-2 border border-line">
      {options.map(opt => (
        <button
          key={opt.value}
          role="radio"
          aria-checked={value === opt.value}
          onClick={() => onChange(opt.value)}
          className={cx(
            'h-6 px-2.5 rounded text-xs transition-colors',
            value === opt.value ? 'bg-surface text-ink font-medium shadow-sm' : 'text-ink-3 hover:text-ink'
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

export const Kbd: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <kbd className="num inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded border border-line-strong bg-surface-2 text-[10px] text-ink-3">
    {children}
  </kbd>
);

// ─── Data display ──────────────────────────────────────────────


const toneClass: Record<Tone, string> = {
  neutral: 'bg-surface-2 text-ink-2',
  up: 'bg-up-soft text-up',
  down: 'bg-down-soft text-down',
  warn: 'bg-warn-soft text-warn',
  accent: 'bg-accent-soft text-accent'
};

export const Tag: React.FC<{ tone?: Tone; children: React.ReactNode; className?: string; title?: string }> = ({
  tone = 'neutral',
  children,
  className,
  title
}) => (
  <span
    title={title}
    className={cx(
      'inline-flex items-center gap-1 h-5 px-1.5 rounded text-[11px] font-medium whitespace-nowrap',
      toneClass[tone],
      className
    )}
  >
    {children}
  </span>
);


export const DirectionTag: React.FC<{ direction: Direction }> = ({ direction }) => {
  const Icon = direction === 'BULLISH' ? ArrowUpRight : direction === 'BEARISH' ? ArrowDownRight : Minus;
  return (
    <Tag tone={directionTone(direction)}>
      <Icon className="w-3 h-3" strokeWidth={2.5} />
      {directionLabel[direction]}
    </Tag>
  );
};

/** Horizontal meter for a 0–100 score. The number is always shown beside it. */
export const ScoreBar: React.FC<{
  value: number;
  tone?: 'accent' | 'risk';
  width?: string;
  showValue?: boolean;
}> = ({ value, tone = 'accent', width = 'w-20', showValue = true }) => {
  const clamped = Math.max(0, Math.min(100, value));
  const fill =
    tone === 'accent' ? 'bg-accent' : clamped >= 60 ? 'bg-down' : clamped >= 40 ? 'bg-warn' : 'bg-ink-3';
  return (
    <div className="flex items-center gap-2">
      {showValue && <span className="num text-[13px] text-ink w-9 text-right">{Number.isInteger(value) ? value : value.toFixed(1)}</span>}
      <div className={cx('h-1.5 rounded-full bg-surface-2 overflow-hidden', width)}>
        <div className={cx('h-full rounded-full', fill)} style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
};

export const Stat: React.FC<{
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  className?: string;
}> = ({ label, value, hint, className }) => (
  <div className={cx('min-w-0', className)}>
    <div className="text-xs text-ink-3">{label}</div>
    <div className="num text-[22px] leading-tight text-ink mt-1">{value}</div>
    {hint && <div className="text-xs text-ink-3 mt-1">{hint}</div>}
  </div>
);

/** Sortable table header cell. */
export function SortHeader<K extends string>({
  label,
  sortKey,
  current,
  dir,
  onSort,
  align = 'left'
}: {
  label: string;
  sortKey: K;
  current: K;
  dir: 'asc' | 'desc';
  onSort: (k: K) => void;
  align?: 'left' | 'right';
}) {
  const active = current === sortKey;
  return (
    <th
      className={cx('px-4 h-9 font-medium text-xs text-ink-3', align === 'right' && 'text-right')}
      aria-sort={active ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}
    >
      <button
        onClick={() => onSort(sortKey)}
        className={cx('inline-flex items-center gap-1 hover:text-ink', active && 'text-ink')}
      >
        {label}
        <span className="text-[10px] w-2">{active ? (dir === 'asc' ? '↑' : '↓') : ''}</span>
      </button>
    </th>
  );
}
