import React, { useMemo } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine, Label } from 'recharts';
import { Crosshair, AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { SignalMatrixPoint } from '../../types/api';

interface SignalMatrixProps {
  data: SignalMatrixPoint[];
  onSelectSymbol?: (symbol: string) => void;
}

const QUADRANT_LABELS = {
  PRIME_VALUE: { label: 'Prime Value', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30' },
  HIGH_GROWTH: { label: 'High Growth / Speculative', color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30' },
  CONSERVATIVE: { label: 'Conservative', color: 'text-sky-400', bg: 'bg-sky-500/10 border-sky-500/30' },
  WARNING_ZONE: { label: 'Warning Zone', color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/30' },
};

const getPointColor = (point: SignalMatrixPoint) => {
  switch (point.quadrant) {
    case 'PRIME_VALUE': return '#10b981';
    case 'HIGH_GROWTH': return '#f59e0b';
    case 'CONSERVATIVE': return '#0ea5e9';
    case 'WARNING_ZONE': return '#f43f5e';
    default: return '#64748b';
  }
};

const DirectionIcon = ({ direction }: { direction: string }) => {
  if (direction === 'BULLISH') return <TrendingUp className="w-3 h-3 text-emerald-400" />;
  if (direction === 'BEARISH') return <TrendingDown className="w-3 h-3 text-rose-400" />;
  return <Minus className="w-3 h-3 text-slate-400" />;
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: SignalMatrixPoint }>;
}

const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
  if (!active || !payload || !payload.length) return null;
  const point = payload[0].payload;
  const q = QUADRANT_LABELS[point.quadrant];
  return (
    <div className="glass-panel p-3 rounded-xl border border-slate-700 text-xs space-y-1.5 max-w-[220px]">
      <div className="flex items-center justify-between">
        <span className="font-bold text-white font-mono">{point.symbol}</span>
        {point.is_anomaly && <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />}
      </div>
      <div className="text-slate-400 truncate">{point.name}</div>
      <div className="flex items-center space-x-2 pt-1 border-t border-slate-800">
        <span className="text-cyan-400 font-mono">Opp: {point.opportunity_score}</span>
        <span className="text-slate-600">|</span>
        <span className="text-rose-400 font-mono">Risk: {point.risk_score}</span>
      </div>
      <span className={`inline-block px-2 py-0.5 rounded text-[9px] font-semibold border ${q.bg}`}>
        {q.label}
      </span>
    </div>
  );
};

export const SignalMatrix: React.FC<SignalMatrixProps> = ({ data, onSelectSymbol }) => {
  const quadrantCounts = useMemo(() => {
    const counts = { PRIME_VALUE: 0, HIGH_GROWTH: 0, CONSERVATIVE: 0, WARNING_ZONE: 0 };
    data.forEach(d => { counts[d.quadrant]++; });
    return counts;
  }, [data]);

  return (
    <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Crosshair className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Signal Matrix — Opportunity vs. Risk Quadrant
          </h3>
        </div>
        <span className="text-xs text-slate-400 font-mono">{data.length} Emiten Diplotkan</span>
      </div>

      {/* Quadrant Legend */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {(Object.keys(QUADRANT_LABELS) as Array<keyof typeof QUADRANT_LABELS>).map((key) => {
          const q = QUADRANT_LABELS[key];
          return (
            <div key={key} className={`p-2.5 rounded-xl border text-center ${q.bg}`}>
              <span className={`text-[10px] font-bold font-mono uppercase ${q.color}`}>{q.label}</span>
              <span className="block text-lg font-black text-white font-mono">{quadrantCounts[key]}</span>
            </div>
          );
        })}
      </div>

      {/* 2D Scatter Plot */}
      <div className="h-[380px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              type="number"
              dataKey="risk_score"
              name="Risk Score"
              domain={[0, 100]}
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
            >
              <Label value="← Low Risk                Risk Score                High Risk →" position="bottom" offset={0} style={{ fill: '#64748b', fontSize: 10 }} />
            </XAxis>
            <YAxis
              type="number"
              dataKey="opportunity_score"
              name="Opportunity Score"
              domain={[0, 100]}
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
            >
              <Label value="Opportunity Score" angle={-90} position="insideLeft" offset={15} style={{ fill: '#64748b', fontSize: 10 }} />
            </YAxis>
            <ReferenceLine x={50} stroke="#334155" strokeDasharray="6 4" />
            <ReferenceLine y={50} stroke="#334155" strokeDasharray="6 4" />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3', stroke: '#475569' }} />
            <Scatter data={data} onClick={(entry: any) => onSelectSymbol?.(entry.symbol || entry.payload?.symbol)}>
              {data.map((point, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={getPointColor(point)}
                  stroke={point.is_anomaly ? '#fbbf24' : 'transparent'}
                  strokeWidth={point.is_anomaly ? 2 : 0}
                  r={point.is_anomaly ? 8 : 6}
                  style={{ cursor: 'pointer' }}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed List */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-mono">
              <th className="pb-2 font-semibold">EMITEN</th>
              <th className="pb-2 font-semibold">SEKTOR</th>
              <th className="pb-2 font-semibold">OPP SCORE</th>
              <th className="pb-2 font-semibold">RISK SCORE</th>
              <th className="pb-2 font-semibold">DIRECTION</th>
              <th className="pb-2 font-semibold text-right">KUADRAN</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {data.map((point, idx) => {
              const q = QUADRANT_LABELS[point.quadrant];
              return (
                <tr
                  key={idx}
                  className="hover:bg-slate-800/30 transition-colors cursor-pointer"
                  onClick={() => onSelectSymbol?.(point.symbol)}
                >
                  <td className="py-2.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-white font-mono">{point.symbol}</span>
                      {point.is_anomaly && <AlertTriangle className="w-3 h-3 text-amber-400" />}
                    </div>
                  </td>
                  <td className="py-2.5 text-slate-400">{point.sector}</td>
                  <td className="py-2.5 font-mono font-bold text-cyan-400">{point.opportunity_score}</td>
                  <td className="py-2.5 font-mono text-slate-300">{point.risk_score}</td>
                  <td className="py-2.5">
                    <div className="flex items-center space-x-1">
                      <DirectionIcon direction={point.direction} />
                      <span className="text-[10px] font-semibold text-slate-300">{point.direction}</span>
                    </div>
                  </td>
                  <td className="py-2.5 text-right">
                    <span className={`px-2 py-0.5 rounded text-[9px] font-semibold border ${q.bg}`}>
                      {q.label}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
