import React, { useMemo } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
  ReferenceArea,
  LabelList
} from 'recharts';
import type { SignalMatrixPoint } from '../../types/api';
import { useChartColors } from '../../lib/theme';
import { OPP_THRESHOLD, RISK_THRESHOLD, quadrantLabel, quadrantShort } from '../../lib/format';
import { Panel } from '../ui/primitives';

interface SignalMatrixProps {
  data: SignalMatrixPoint[];
  selectedSymbol?: string;
  onSelectSymbol?: (symbol: string) => void;
}

const QUADRANTS: SignalMatrixPoint['quadrant'][] = ['PRIME_VALUE', 'HIGH_GROWTH', 'CONSERVATIVE', 'WARNING_ZONE'];

/**
 * Opportunity vs risk scatter. Points are one neutral color; only the selected
 * emiten gets the accent and anomalies get a warning ring, so color always
 * carries meaning.
 */
export const SignalMatrix: React.FC<SignalMatrixProps> = ({ data, selectedSymbol, onSelectSymbol }) => {
  const c = useChartColors();

  const counts = useMemo(() => {
    const out = { PRIME_VALUE: 0, HIGH_GROWTH: 0, CONSERVATIVE: 0, WARNING_ZONE: 0 };
    data.forEach(d => out[d.quadrant]++);
    return out;
  }, [data]);

  const quadrantLabelProps = (value: string, position: 'insideTopLeft' | 'insideTopRight' | 'insideBottomLeft' | 'insideBottomRight') => ({
    value,
    position,
    fill: c.axis,
    fontSize: 11
  });

  return (
    <Panel
      title="Peta peluang vs risiko"
      meta={`${data.length} emiten`}
      actions={
        <div className="hidden sm:flex items-center gap-3 text-xs text-ink-2">
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full" style={{ background: c.muted }} />Emiten</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full" style={{ background: c.series1 }} />Sedang dibuka</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full border-2" style={{ borderColor: c.warn }} />Anomali</span>
        </div>
      }
    >
      <div className="h-[360px]">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 8, right: 16, bottom: 16, left: -8 }}>
            <CartesianGrid stroke={c.grid} />
            <ReferenceArea x1={0} x2={RISK_THRESHOLD} y1={OPP_THRESHOLD} y2={100} fill="transparent" label={quadrantLabelProps(quadrantShort.PRIME_VALUE, 'insideTopLeft')} />
            <ReferenceArea x1={RISK_THRESHOLD} x2={100} y1={OPP_THRESHOLD} y2={100} fill="transparent" label={quadrantLabelProps(quadrantShort.HIGH_GROWTH, 'insideTopRight')} />
            <ReferenceArea x1={0} x2={RISK_THRESHOLD} y1={0} y2={OPP_THRESHOLD} fill="transparent" label={quadrantLabelProps(quadrantShort.CONSERVATIVE, 'insideBottomLeft')} />
            <ReferenceArea x1={RISK_THRESHOLD} x2={100} y1={0} y2={OPP_THRESHOLD} fill="transparent" label={quadrantLabelProps(quadrantShort.WARNING_ZONE, 'insideBottomRight')} />
            <XAxis
              type="number"
              dataKey="risk_score"
              name="Risiko"
              domain={[0, 100]}
              stroke={c.axis}
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: c.grid }}
              label={{ value: 'Skor risiko →', position: 'insideBottomRight', offset: -10, fill: c.axis, fontSize: 11 }}
            />
            <YAxis
              type="number"
              dataKey="opportunity_score"
              name="Peluang"
              domain={[0, 100]}
              stroke={c.axis}
              fontSize={11}
              tickLine={false}
              axisLine={false}
              label={{ value: 'Skor peluang →', angle: -90, position: 'insideLeft', offset: 20, fill: c.axis, fontSize: 11 }}
            />
            <ReferenceLine x={RISK_THRESHOLD} stroke={c.context} />
            <ReferenceLine y={OPP_THRESHOLD} stroke={c.context} />
            <Tooltip
              cursor={false}
              content={({ active, payload }) => {
                const p = payload?.[0]?.payload as SignalMatrixPoint | undefined;
                if (!active || !p) return null;
                return (
                  <div className="bg-surface border border-line-strong rounded-md shadow-lg px-3 py-2 text-xs space-y-1 min-w-[170px]">
                    <div className="flex justify-between gap-3">
                      <span className="num font-medium text-ink">{p.symbol}</span>
                      {p.is_anomaly && <span className="text-warn">Anomali</span>}
                    </div>
                    <div className="text-ink-3 truncate">{p.name}</div>
                    <div className="flex justify-between num text-ink-2 pt-1 border-t border-line">
                      <span>Peluang {p.opportunity_score}</span>
                      <span>Risiko {p.risk_score}</span>
                    </div>
                    <div className="text-ink-3">{quadrantLabel[p.quadrant]}</div>
                  </div>
                );
              }}
            />
            <Scatter
              data={data}
              isAnimationActive={false}
              onClick={(entry: { payload?: SignalMatrixPoint; symbol?: string }) =>
                onSelectSymbol?.(entry.symbol ?? entry.payload?.symbol ?? '')
              }
            >
              {data.map(p => {
                const selected = p.symbol === selectedSymbol;
                return (
                  <Cell
                    key={p.symbol}
                    fill={selected ? c.series1 : c.muted}
                    stroke={p.is_anomaly ? c.warn : c.surface}
                    strokeWidth={2}
                    style={{ cursor: 'pointer' }}
                  />
                );
              })}
              <LabelList
                dataKey="symbol"
                content={({ x, y, value, index }) => {
                  const p = data[index as number];
                  if (!p || (p.symbol !== selectedSymbol && !p.is_anomaly)) return null;
                  return (
                    <text x={Number(x) + 14} y={Number(y) + 8} fontSize={11} fontFamily="IBM Plex Mono" fill={c.ink}>
                      {String(value)}
                    </text>
                  );
                }}
              />
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4 pt-4 border-t border-line">
        {QUADRANTS.map(q => (
          <div key={q}>
            <div className="text-xs text-ink-3">{quadrantShort[q]}</div>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="num text-lg text-ink">{counts[q]}</span>
              <span className="text-xs text-ink-3 truncate">{quadrantLabel[q].toLowerCase()}</span>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
};
