import React, { useState } from 'react';
import { Database, ChevronRight, CheckCircle2, Loader2, Clock, X } from 'lucide-react';
import type { PipelineStage } from '../../types/api';

interface SectorsPipelineInspectorProps {
  stages: PipelineStage[];
  isOpen: boolean;
  onClose: () => void;
}

const statusConfig = {
  COMPLETED: { icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30', label: 'Completed' },
  PROCESSING: { icon: Loader2, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30', label: 'Processing' },
  PENDING: { icon: Clock, color: 'text-slate-400', bg: 'bg-slate-800 border-slate-700', label: 'Pending' },
};

export const SectorsPipelineInspector: React.FC<SectorsPipelineInspectorProps> = ({
  stages,
  isOpen,
  onClose
}) => {
  const [expandedStage, setExpandedStage] = useState<string | null>(null);

  if (!isOpen) return null;

  const totalDuration = stages.reduce((acc, s) => acc + (s.duration_ms || 0), 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="glass-panel w-full max-w-2xl max-h-[85vh] rounded-2xl border border-slate-700 shadow-2xl shadow-cyan-500/10 overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Database className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white font-mono">Sectors API / MCP Data Pipeline</h2>
              <p className="text-[10px] text-slate-400 mt-0.5">Alur pengolahan data mentah → derived insight</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Pipeline Summary */}
        <div className="px-5 py-3 bg-slate-900/50 border-b border-slate-800 flex items-center justify-between text-xs shrink-0">
          <div className="flex items-center space-x-4 text-slate-300">
            <span>{stages.length} Stages</span>
            <span className="text-slate-600">|</span>
            <span>Total Latency: <strong className="text-cyan-400 font-mono">{totalDuration}ms</strong></span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-emerald-400 font-medium font-mono text-[10px]">ALL STAGES COMPLETED</span>
          </div>
        </div>

        {/* Pipeline Stages */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {stages.map((stage, idx) => {
            const config = statusConfig[stage.status];
            const StatusIcon = config.icon;
            const isExpanded = expandedStage === stage.id;
            const isLast = idx === stages.length - 1;

            return (
              <div key={stage.id}>
                <button
                  onClick={() => setExpandedStage(isExpanded ? null : stage.id)}
                  className={`w-full text-left p-4 rounded-xl border transition-all ${
                    isExpanded
                      ? 'bg-cyan-500/10 border-cyan-500/30'
                      : 'glass-card border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-slate-900 border border-slate-800">
                        <span className="text-[10px] font-bold text-cyan-400 font-mono">{idx + 1}</span>
                      </div>
                      <div>
                        <span className="text-xs font-bold text-slate-200">{stage.label}</span>
                        <span className="text-[10px] text-slate-400 block mt-0.5 font-mono">{stage.data_type}</span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      {stage.duration_ms && (
                        <span className="text-[10px] text-slate-500 font-mono">{stage.duration_ms}ms</span>
                      )}
                      <span className={`px-2 py-0.5 rounded text-[9px] font-semibold border flex items-center space-x-1 ${config.bg}`}>
                        <StatusIcon className={`w-3 h-3 ${config.color} ${stage.status === 'PROCESSING' ? 'animate-spin' : ''}`} />
                        <span className={config.color}>{config.label}</span>
                      </span>
                      <ChevronRight className={`w-4 h-4 text-slate-500 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-slate-800/60">
                      <p className="text-xs text-slate-300 leading-relaxed">{stage.description}</p>
                    </div>
                  )}
                </button>

                {/* Connector Arrow */}
                {!isLast && (
                  <div className="flex justify-center py-1">
                    <div className="w-px h-4 bg-gradient-to-b from-cyan-500/40 to-slate-800" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-800 text-[10px] text-slate-400 shrink-0 font-mono">
          Sumber Data: Sectors API/MCP → Raw Data → Validated → Normalized → Transformed → Features → Intelligence Output
        </div>
      </div>
    </div>
  );
};
