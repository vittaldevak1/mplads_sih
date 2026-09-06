'use client';

import { useEffect, useState, useCallback } from 'react';
import { fetchAnomalies } from '@/lib/api';
import WorkForensicDrawer from '@/components/WorkForensicDrawer';
import { SortIndicator, useSortableData } from '@/components/SortableTable';

const SEVERITY_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  HIGH: { bg: '#FEF2F2', text: '#991B1B', border: '#F87171' },
  MEDIUM: { bg: '#FFFBEB', text: '#92400E', border: '#FBBF24' },
  INFO: { bg: '#EFF6FF', text: '#1E40AF', border: '#93C5FD' },
  LOW: { bg: '#F0FDF4', text: '#166534', border: '#86EFAC' },
};

const SIGNAL_BADGES: Record<string, string> = {
  F: 'Financial', D: 'Delay', X: 'Semantic', V: 'Vendor',
  Q: 'Quota', B: 'Benford', Rs: 'SoR',
};

export default function AnomaliesPage() {
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [signalUnavailable, setSignalUnavailable] = useState(false);
  const [unavailableMessage, setUnavailableMessage] = useState('');
  const [selectedWorkId, setSelectedWorkId] = useState<string | null>(null);

  const PAGE_SIZE = 30;

  async function load() {
    setLoading(true);
    setSignalUnavailable(false);
    try {
      const data = await fetchAnomalies({
        page,
        size: PAGE_SIZE,
        severity: severityFilter || undefined,
        anomaly_type: typeFilter || undefined,
      });
      if (data.signal_unavailable) {
        setSignalUnavailable(true);
        setUnavailableMessage(data.message || 'Signal data is unavailable in this MVP stage.');
        setAnomalies([]);
        setTotal(0);
      } else {
        setAnomalies(data.items || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [page, severityFilter, typeFilter]);

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const formatScore = (val: number | null | undefined) => {
    if (val === null || val === undefined) return '—';
    return val.toFixed(1);
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#334155] p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-display text-[#0F172A]">Risk Analysis & Flagged Items</h1>
          <p className="text-sm text-[#94A3B8] mt-1 font-mono-tech">
            {signalUnavailable
              ? 'Signal data unavailable'
              : `${total.toLocaleString('en-IN')} items flagged from live risk signals`}
          </p>
        </div>

        <div className="flex flex-wrap gap-3 mb-6 items-center">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono-tech text-[#94A3B8] uppercase">Severity:</span>
            {['HIGH', 'MEDIUM', 'INFO'].map((s) => {
              const style = SEVERITY_STYLES[s] || SEVERITY_STYLES.INFO;
              return (
                <button
                  key={s}
                  onClick={() => { setSeverityFilter(severityFilter === s ? null : s); setPage(1); }}
                  className={`px-2.5 py-1 rounded text-[10px] font-bold uppercase font-mono-tech transition ${
                    severityFilter === s ? 'ring-1 ring-accent' : ''
                  }`}
                  style={{ background: style.bg, color: style.text, border: `1px solid ${style.border}` }}
                >
                  {s}
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono-tech text-[#94A3B8] uppercase">Category:</span>
            <select
              value={typeFilter || ''}
              onChange={(e) => { setTypeFilter(e.target.value || null); setPage(1); }}
              className="bg-white border border-[#E2E8F0] rounded px-3 py-1.5 text-xs text-[#475569] font-mono-tech focus:outline-none focus:border-accent"
              title="Filter by signal type or composite risk level"
            >
              <option value="">High-Risk Works (Composite ≥ 65)</option>
              <option value="F">Financial Disbursement (F ≥ 65)</option>
              <option value="D">Delay / Duration (D ≥ 55)</option>
              <option value="X">Semantic Similarity (X ≥ 65)</option>
              <option value="V">Vendor Concentration (V ≥ 60)</option>
              <option value="Q">Quota Compliance Indicator</option>
              <option value="B">Statistical Threshold (B ≥ 65)</option>
              <option value="Rs">Cost/Gestation Outlier (Rs ≥ 80)</option>
              <option value="C">Citizen Reports — Unavailable</option>
              <option value="O">OCR/Document — Unavailable</option>
              <option value="S">Spatial — Unavailable</option>
              <option value="G">Satellite — Unavailable</option>
            </select>
          </div>
        </div>

        {signalUnavailable && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-amber-900 font-mono-tech text-sm mb-6">
            <div className="font-bold mb-1">Signal Source Unavailable</div>
            <div>{unavailableMessage}</div>
            <div className="text-xs text-amber-700 mt-2">
              Citizen (C), OCR (O), Spatial (S), and Satellite (G) signals require external data sources not active in this stage.
            </div>
          </div>
        )}

        {!signalUnavailable && (
          <div className="space-y-3">
            {loading ? (
              <div className="rounded-xl border border-[#E2E8F0] bg-white p-12 text-center text-[#94A3B8] font-mono-tech text-sm animate-pulse">
                Querying live risk signals...
              </div>
            ) : anomalies.length === 0 ? (
              <div className="rounded-xl border border-[#E2E8F0] bg-white p-12 text-center text-[#94A3B8] font-mono-tech text-sm">
                No items match the current filters.
              </div>
            ) : (
              anomalies.map((a) => {
                const style = SEVERITY_STYLES[a.severity] || SEVERITY_STYLES.INFO;
                return (
                  <div key={a.id} className="rounded-xl border border-[#E2E8F0] bg-white overflow-hidden shadow-sm hover:shadow transition">
                    <button
                      onClick={() => setSelectedWorkId(a.work_id)}
                      className="w-full flex items-center justify-between px-5 py-4 hover:bg-[#F8FAFC] transition text-left"
                    >
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <span
                          className="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase font-mono-tech shrink-0"
                          style={{ background: style.bg, color: style.text, border: `1px solid ${style.border}` }}
                        >
                          {a.severity}
                        </span>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-[#0F172A]">{a.anomaly_type}</span>
                            {a.signal_code && a.signal_code !== 'COMPOSITE' && (
                              <span className="px-1.5 py-0.5 rounded bg-slate-100 text-[10px] font-mono-tech text-[#64748B]">
                                {SIGNAL_BADGES[a.signal_code] || a.signal_code}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-[#64748B] mt-0.5 max-w-[650px] truncate">
                            {a.description}
                          </div>
                          <div className="flex gap-3 mt-1">
                            {a.state && <span className="text-[10px] text-[#94A3B8] font-mono-tech">{a.state}</span>}
                            {a.constituency && <span className="text-[10px] text-[#94A3B8] font-mono-tech">{a.constituency}</span>}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 shrink-0">
                        <div className="text-right">
                          <div className="text-[10px] font-mono-tech text-[#94A3B8]">Risk</div>
                          <div className="text-sm font-bold font-mono-tech text-[#0F172A]">{formatScore(a.composite_risk)}</div>
                        </div>
                        {a.signal_code !== 'COMPOSITE' && (
                          <div className="text-right">
                            <div className="text-[10px] font-mono-tech text-[#94A3B8]">Score</div>
                            <div className="text-sm font-bold font-mono-tech text-[#0F172A]">{formatScore(a.score)}</div>
                          </div>
                        )}
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono-tech font-semibold capitalize bg-[#F1F5F9] text-[#64748B]">
                          {(a.task_status || 'pending').replace('_', ' ')}
                        </span>
                        <span className="text-[9px] font-mono-tech text-accent">View →</span>
                      </div>
                    </button>
                  </div>
                );
              })
            )}
          </div>
        )}

        {!signalUnavailable && totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded bg-[#F1F5F9] text-[#64748B] text-xs font-mono-tech hover:bg-[#E2E8F0] transition disabled:opacity-30"
            >
              Prev
            </button>
            <span className="text-xs font-mono-tech text-[#94A3B8]">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 rounded bg-[#F1F5F9] text-[#64748B] text-xs font-mono-tech hover:bg-[#E2E8F0] transition disabled:opacity-30"
            >
              Next
            </button>
          </div>
        )}
      </div>

      <WorkForensicDrawer workId={selectedWorkId} onClose={() => setSelectedWorkId(null)} sourcePage="Anomalies" />
    </div>
  );
}
