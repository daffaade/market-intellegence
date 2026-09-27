import React, { useState, useEffect } from 'react';
import { 
  Database, 
  ChevronRight, 
  CheckCircle2, 
  Loader2, 
  Clock, 
  X, 
  Server, 
  FlaskConical, 
  RefreshCw, 
  Wifi, 
  AlertCircle,
  Radio,
  Cpu
} from 'lucide-react';
import type { PipelineStage, HealthStatus } from '../../types/api';
import { apiService, getApiBaseUrl } from '../../services/mockApi';

interface SectorsPipelineInspectorProps {
  stages: PipelineStage[];
  isOpen: boolean;
  onClose: () => void;
  useDummyData: boolean;
  onToggleDummy: (enabled: boolean) => void;
  onRefreshData?: () => void;
}

const statusConfig = {
  COMPLETED: { icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30', label: 'Completed' },
  PROCESSING: { icon: Loader2, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30', label: 'Processing' },
  PENDING: { icon: Clock, color: 'text-slate-400', bg: 'bg-slate-800 border-slate-700', label: 'Pending' },
};

export const SectorsPipelineInspector: React.FC<SectorsPipelineInspectorProps> = ({
  stages,
  isOpen,
  onClose,
  useDummyData,
  onToggleDummy,
  onRefreshData
}) => {
  const [expandedStage, setExpandedStage] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [checkingHealth, setCheckingHealth] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // Ping backend health whenever inspector opens
  const checkBackendHealth = async () => {
    setCheckingHealth(true);
    try {
      const res = await apiService.getHealth();
      if (res.status === 'success' && res.data) {
        setHealth(res.data);
      } else {
        setHealth(null);
      }
    } catch {
      setHealth(null);
    } finally {
      setCheckingHealth(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      checkBackendHealth();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const totalDuration = stages.reduce((acc, s) => acc + (s.duration_ms || 0), 0);
  const backendUrl = getApiBaseUrl();

  const handleToggle = (newValue: boolean) => {
    onToggleDummy(newValue);
    if (onRefreshData) {
      setIsRefreshing(true);
      setTimeout(() => {
        onRefreshData();
        setIsRefreshing(false);
      }, 300);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="glass-panel w-full max-w-2xl max-h-[90vh] rounded-2xl border border-slate-700 shadow-2xl shadow-cyan-500/10 overflow-hidden flex flex-col">
        
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between shrink-0 bg-slate-900/60">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-white font-mono">Sectors API & Intelligence Pipeline</h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  CONTROL PANEL
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">Kontrol sumber data, eksekusi pipeline & verifikasi backend</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">

          {/* ─── TOGGLE ON/OFF SOURCE MODE CARD ─── */}
          <div className="p-4 rounded-xl border transition-all bg-gradient-to-b from-slate-900/90 to-slate-900/50 border-slate-700/80 shadow-lg">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              
              <div className="flex items-start space-x-3.5">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border transition-colors ${
                  useDummyData 
                    ? 'bg-amber-500/15 border-amber-500/40 text-amber-400' 
                    : 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400 shadow-md shadow-emerald-500/20'
                }`}>
                  {useDummyData ? <FlaskConical className="w-5 h-5" /> : <Server className="w-5 h-5" />}
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                      Sumber Data Engine
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold border flex items-center space-x-1 ${
                      useDummyData 
                        ? 'bg-amber-500/10 text-amber-300 border-amber-500/30' 
                        : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                    }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${useDummyData ? 'bg-amber-400' : 'bg-emerald-400 animate-pulse'}`} />
                      <span>{useDummyData ? 'DATA DUMMY (MOCK)' : 'HANYA BACKEND GO'}</span>
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                    {useDummyData 
                      ? 'Mode simulasi offline aktif dengan 18 emiten IDX bawaan untuk demonstrasi.' 
                      : 'Terhubung langsung ke API Go (port 8080) dengan Sectors API & AI Provider.'}
                  </p>
                </div>
              </div>

              {/* Interactive Switch */}
              <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-800">
                <div className="flex items-center space-x-3">
                  <span className="text-[11px] font-mono font-semibold text-slate-300">
                    {useDummyData ? 'Dummy: ON' : 'Dummy: OFF'}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleToggle(!useDummyData)}
                    className={`relative inline-flex h-7 w-14 shrink-0 cursor-pointer rounded-full border-2 transition-colors duration-200 ease-in-out focus:outline-none ${
                      useDummyData 
                        ? 'bg-amber-500 border-amber-400 shadow-md shadow-amber-500/30' 
                        : 'bg-emerald-600 border-emerald-500 shadow-md shadow-emerald-600/30'
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out flex items-center justify-center ${
                        useDummyData ? 'translate-x-7' : 'translate-x-0'
                      }`}
                    >
                      {useDummyData ? (
                        <FlaskConical className="w-3.5 h-3.5 text-amber-600" />
                      ) : (
                        <Server className="w-3.5 h-3.5 text-emerald-600" />
                      )}
                    </span>
                  </button>
                </div>
                <span className="text-[9px] text-slate-500 font-mono mt-1 hidden sm:block">
                  Klik untuk beralih mode
                </span>
              </div>
            </div>

              {/* Segmented Button Shortcut */}
              <div className="mt-3 pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => handleToggle(false)}
                  className={`py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-2 transition-all cursor-pointer ${
                    !useDummyData
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm'
                      : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Server className="w-3.5 h-3.5" />
                  <span>⚡ Hanya Backend Go</span>
                  {!useDummyData && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
                </button>

                <button
                  type="button"
                  onClick={() => handleToggle(true)}
                  className={`py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-2 transition-all cursor-pointer ${
                    useDummyData
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50 shadow-sm'
                      : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <FlaskConical className="w-3.5 h-3.5" />
                  <span>🧪 Pakai Data Dummy</span>
                  {useDummyData && <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />}
                </button>
              </div>
          </div>

          {/* ─── LIVE BACKEND DIAGNOSTIC CARD ─── */}
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Radio className={`w-3.5 h-3.5 ${health ? 'text-emerald-400' : 'text-slate-500'}`} />
                <span className="text-[11px] font-bold font-mono text-slate-300 uppercase">
                  Status Koneksi API Backend
                </span>
              </div>
              <button
                onClick={checkBackendHealth}
                disabled={checkingHealth}
                className="flex items-center space-x-1 text-[10px] font-mono text-cyan-400 hover:text-cyan-300 bg-cyan-950/40 hover:bg-cyan-900/40 px-2 py-0.5 rounded border border-cyan-800/50 transition-colors cursor-pointer"
              >
                <RefreshCw className={`w-3 h-3 ${checkingHealth ? 'animate-spin' : ''}`} />
                <span>{checkingHealth ? 'Pinging...' : 'Ping Server'}</span>
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px] font-mono">
              <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                <span className="text-slate-500 block text-[9px]">TARGET URL</span>
                <span className="text-slate-300 font-medium truncate block">{backendUrl}</span>
              </div>
              <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                <span className="text-slate-500 block text-[9px]">SERVER HEALTH</span>
                {health ? (
                  <span className="text-emerald-400 font-bold flex items-center space-x-1">
                    <Wifi className="w-2.5 h-2.5 inline mr-1" />
                    ONLINE (200)
                  </span>
                ) : (
                  <span className="text-rose-400 font-bold flex items-center space-x-1">
                    <AlertCircle className="w-2.5 h-2.5 inline mr-1" />
                    OFFLINE
                  </span>
                )}
              </div>
              <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                <span className="text-slate-500 block text-[9px]">AI PROVIDER</span>
                <span className="text-cyan-400 font-bold">{health?.ai_provider || 'mock'}</span>
              </div>
              <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                <span className="text-slate-500 block text-[9px]">AI MODEL</span>
                <span className="text-indigo-300 truncate block">{health?.ai_model || 'gemini-3.5-flash'}</span>
              </div>
            </div>

            {!health && (
              <div className="flex items-center space-x-2 text-[10px] text-amber-400/90 bg-amber-500/10 px-3 py-1.5 rounded-lg border border-amber-500/20">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>
                  Backend Go belum merespons di port 8080. Jalankan <code className="bg-slate-900 px-1 py-0.5 rounded font-mono text-slate-200">go run cmd/api/main.go</code> atau tetap gunakan Data Dummy.
                </span>
              </div>
            )}
          </div>

          {/* ─── PIPELINE SUMMARY & STAGES ─── */}
          <div className="pt-2">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2 text-xs text-slate-300 font-mono">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <span className="font-bold">Tahapan Sectors API & Engine</span>
                <span className="text-slate-600">|</span>
                <span className="text-slate-400">{stages.length} Stages</span>
                <span className="text-slate-600">|</span>
                <span className="text-cyan-400">{totalDuration}ms</span>
              </div>

              {isRefreshing && (
                <div className="flex items-center space-x-1 text-[10px] text-cyan-400 font-mono">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Reloading data...</span>
                </div>
              )}
            </div>

            <div className="space-y-2">
              {stages.map((stage, idx) => {
                const config = statusConfig[stage.status];
                const StatusIcon = config.icon;
                const isExpanded = expandedStage === stage.id;
                const isLast = idx === stages.length - 1;

                return (
                  <div key={stage.id}>
                    <button
                      onClick={() => setExpandedStage(isExpanded ? null : stage.id)}
                      className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                        isExpanded
                          ? 'bg-cyan-500/10 border-cyan-500/30'
                          : 'glass-card border-slate-800/80 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="flex items-center justify-center w-6 h-6 rounded-lg bg-slate-900 border border-slate-800">
                            <span className="text-[10px] font-bold text-cyan-400 font-mono">{idx + 1}</span>
                          </div>
                          <div>
                            <span className="text-xs font-bold text-slate-200">{stage.label}</span>
                            <span className="text-[10px] text-slate-400 block font-mono">{stage.data_type}</span>
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

                    {!isLast && (
                      <div className="flex justify-center py-0.5">
                        <div className="w-px h-3 bg-gradient-to-b from-cyan-500/40 to-slate-800" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between text-xs shrink-0 font-mono">
          <div className="flex items-center space-x-2 text-slate-400 text-[11px]">
            <span>Mode Aktif:</span>
            <span className={`font-bold ${useDummyData ? 'text-amber-400' : 'text-emerald-400'}`}>
              {useDummyData ? 'Data Dummy (Simulasi)' : 'Hanya Backend Go'}
            </span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors cursor-pointer"
          >
            Tutup
          </button>
        </div>

      </div>
    </div>
  );
};
