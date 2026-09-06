'use client';

import { useEffect, useState, useCallback } from 'react';
import { fetchWorkDetail, fetchRiskScore, fetchInspectionHistory } from '@/lib/api';

const SIGNAL_LABELS: Record<string, { name: string; weight: number; category: 'available' | 'unavailable' }> = {
  F: { name: 'Financial Disbursement', weight: 15, category: 'available' },
  D: { name: 'Delay / Duration', weight: 12, category: 'available' },
  X: { name: 'Semantic Similarity', weight: 12, category: 'available' },
  V: { name: 'Vendor Network Risk', weight: 10, category: 'available' },
  C: { name: 'Citizen Complaints', weight: 10, category: 'unavailable' },
  Q: { name: 'Quota Compliance', weight: 10, category: 'available' },
  O: { name: 'OCR / Document', weight: 8, category: 'unavailable' },
  S: { name: 'Spatial Duplication', weight: 7, category: 'unavailable' },
  G: { name: 'Satellite Ground-Truth', weight: 8, category: 'unavailable' },
  B: { name: 'Statistical Threshold', weight: 4, category: 'available' },
  Rs: { name: 'Cost/Gestation Outlier', weight: 4, category: 'available' },
};

const SIGNAL_ORDER = ['F', 'D', 'X', 'V', 'Q', 'B', 'Rs', 'C', 'O', 'S', 'G'];

interface WorkForensicDrawerProps {
  workId: string | null;
  onClose: () => void;
  sourcePage?: string;
  vendorContext?: { vendorName?: string; vendorWorks?: number };
}

export default function WorkForensicDrawer({ workId, onClose, sourcePage, vendorContext }: WorkForensicDrawerProps) {
  const [work, setWork] = useState<any>(null);
  const [risk, setRisk] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'signals' | 'evidence'>('overview');

  const loadData = useCallback(async () => {
    if (!workId) return;
    setLoading(true);
    setError(null);
    try {
      const [workData, riskData, histData] = await Promise.allSettled([
        fetchWorkDetail(workId),
        fetchRiskScore(workId),
        fetchInspectionHistory(workId),
      ]);
      if (workData.status === 'fulfilled') setWork(workData.value);
      if (riskData.status === 'fulfilled') setRisk(riskData.value);
      if (histData.status === 'fulfilled') setHistory(histData.value?.history || []);
    } catch (e: any) {
      setError(e.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [workId]);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    if (workId) { document.addEventListener('keydown', handleEsc); return () => document.removeEventListener('keydown', handleEsc); }
  }, [workId, onClose]);

  if (!workId) return null;

  const fmt = (val: number | null | undefined, prefix = '₹') => {
    if (val === null || val === undefined) return '—';
    return `${prefix}${val.toLocaleString('en-IN')}`;
  };
  const fmtDate = (val: string | null | undefined) => {
    if (!val) return '—';
    try { return new Date(val).toLocaleDateString('en-IN'); } catch { return val; }
  };
  const scoreColor = (s: number | null | undefined, a: boolean) => {
    if (!a || s === null || s === undefined) return 'text-[#94A3B8]';
    return s >= 65 ? 'text-red-600' : s >= 40 ? 'text-amber-600' : 'text-emerald-600';
  };
  const scoreBg = (s: number | null | undefined, a: boolean) => {
    if (!a || s === null || s === undefined) return 'bg-[#F1F5F9]';
    return s >= 65 ? 'bg-red-50' : s >= 40 ? 'bg-amber-50' : 'bg-emerald-50';
  };
  const prioStyle = (p: string | null) => {
    switch (p) {
      case 'HIGH': return { bg: '#FEF2F2', text: '#991B1B', border: '#F87171' };
      case 'MEDIUM': return { bg: '#FFFBEB', text: '#92400E', border: '#FBBF24' };
      case 'LOW': return { bg: '#F0FDF4', text: '#166534', border: '#86EFAC' };
      default: return { bg: '#F1F5F9', text: '#64748B', border: '#E2E8F0' };
    }
  };

  const ps = prioStyle(risk?.inspection_priority);
  const signals = risk?.signals || [];

  return (
    <>
      <div className="fixed inset-0 bg-black/30 z-40 transition-opacity" onClick={onClose} />
      <div className="fixed right-0 top-0 h-full w-full max-w-2xl bg-white z-50 shadow-2xl flex flex-col">
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#E2E8F0] flex items-center justify-between shrink-0 bg-[#F8FAFC]">
          <div className="min-w-0 flex-1">
            <div className="text-[10px] font-mono-tech text-[#94A3B8] uppercase">
              Forensic Work Analysis {sourcePage ? `— from ${sourcePage}` : ''}
            </div>
            <div className="text-sm font-bold text-[#0F172A] font-mono-tech truncate">{workId}</div>
            {work?.work_description && (
              <div className="text-[11px] text-[#64748B] mt-0.5 truncate max-w-[500px]">{work.work_description}</div>
            )}
          </div>
          <div className="flex items-center gap-2 ml-4 shrink-0">
            {risk?.inspection_priority && (
              <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono-tech"
                style={{ background: ps.bg, color: ps.text, border: `1px solid ${ps.border}` }}>
                {risk.inspection_priority}
              </span>
            )}
            <button onClick={onClose}
              className="w-8 h-8 rounded-lg bg-[#F1F5F9] hover:bg-[#E2E8F0] flex items-center justify-center text-[#64748B] transition">
              ✕
            </button>
          </div>
        </div>

        {loading && <div className="flex-1 flex items-center justify-center text-[#94A3B8] font-mono-tech text-sm animate-pulse">Loading forensic data...</div>}
        {error && <div className="flex-1 flex items-center justify-center text-red-500 font-mono-tech text-sm">{error}</div>}

        {!loading && !error && (
          <div className="flex-1 overflow-y-auto">
            {/* Tabs */}
            <div className="flex border-b border-[#E2E8F0] shrink-0 sticky top-0 bg-white z-10">
              {(['overview', 'signals', 'evidence'] as const).map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2.5 text-xs font-mono-tech uppercase transition border-b-2 ${
                    activeTab === tab ? 'border-accent text-accent font-bold' : 'border-transparent text-[#94A3B8] hover:text-[#64748B]'
                  }`}>
                  {tab}
                </button>
              ))}
            </div>

            <div className="p-5 space-y-4">
              {/* OVERVIEW TAB */}
              {activeTab === 'overview' && work && (
                <>
                  {/* Risk Summary */}
                  {risk && (
                    <div className="rounded-xl border border-[#E2E8F0] p-4">
                      <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Risk Assessment</div>
                      <div className="grid grid-cols-3 gap-3">
                        <div className="text-center p-3 rounded-lg bg-[#F8FAFC]">
                          <div className="text-2xl font-bold font-mono-tech text-[#0F172A]">{risk.composite_risk?.toFixed(1) ?? '—'}</div>
                          <div className="text-[10px] font-mono-tech text-[#94A3B8] mt-1">Composite Risk</div>
                        </div>
                        <div className="text-center p-3 rounded-lg bg-[#F8FAFC]">
                          <span className="px-2 py-0.5 rounded text-xs font-bold font-mono-tech"
                            style={{ background: ps.bg, color: ps.text, border: `1px solid ${ps.border}` }}>
                            {risk.inspection_priority || '—'}
                          </span>
                          <div className="text-[10px] font-mono-tech text-[#94A3B8] mt-2">Priority</div>
                        </div>
                        <div className="text-center p-3 rounded-lg bg-[#F8FAFC]">
                          <div className="text-2xl font-bold font-mono-tech text-[#0F172A]">
                            {risk.confidence_coverage != null ? `${(risk.confidence_coverage * 100).toFixed(0)}%` : '—'}
                          </div>
                          <div className="text-[10px] font-mono-tech text-[#94A3B8] mt-1">Coverage</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Work Identity */}
                  <div className="rounded-xl border border-[#E2E8F0] p-4">
                    <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Work Identity</div>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      {[
                        ['State', work.state],
                        ['Constituency', work.constituency],
                        ['MP', work.mp_name],
                        ['Agency', work.ida],
                        ['Vendor', work.vendor_name],
                        ['Status', work.work_status],
                        ['Category', work.work_category],
                        ['Parliament', work.parliament_house],
                      ].map(([label, val]) => (
                        <div key={label}>
                          <span className="text-[#94A3B8]">{label}</span>
                          <div className="font-semibold text-[#0F172A] mt-0.5">{val || '—'}</div>
                        </div>
                      ))}
                    </div>
                    <div className="flex gap-2 mt-3">
                      {work.is_sc_quota && <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 text-[10px] font-mono-tech font-bold border border-purple-200">SC Quota</span>}
                      {work.is_st_quota && <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-[10px] font-mono-tech font-bold border border-indigo-200">ST Quota</span>}
                    </div>
                  </div>

                  {/* Financial Details */}
                  <div className="rounded-xl border border-[#E2E8F0] p-4">
                    <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Financial Details</div>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div><span className="text-[#94A3B8]">Recommended</span><div className="font-bold text-[#0F172A] mt-0.5">{fmt(work.recommended_amount)}</div></div>
                      <div><span className="text-[#94A3B8]">Sanctioned</span><div className="font-bold text-[#0F172A] mt-0.5">{fmt(work.sanction_amount)}</div></div>
                      <div><span className="text-[#94A3B8]">Disbursed</span><div className="font-bold text-[#0F172A] mt-0.5">{fmt(work.amount_disbursed)}</div>
                        <div className="text-[9px] text-[#94A3B8]">Source: {work.expenditures?.length ? 'Expenditure records' : 'Completion record'}</div>
                      </div>
                      {work.sanction_amount && work.amount_disbursed && (
                        <div><span className="text-[#94A3B8]">Disbursement Ratio</span>
                          <div className="font-bold text-[#0F172A] mt-0.5">{((work.amount_disbursed / work.sanction_amount) * 100).toFixed(1)}%</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Timeline */}
                  <div className="rounded-xl border border-[#E2E8F0] p-4">
                    <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Timeline</div>
                    <div className="space-y-3">
                      {[
                        { label: 'Recommended', date: work.recommended_date, amt: work.recommended_amount },
                        { label: 'Sanctioned', date: work.sanction_date, amt: work.sanction_amount },
                        { label: 'Completed', date: work.completion_date, amt: work.amount_disbursed },
                      ].filter(i => i.date).map((item, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="w-2 h-2 rounded-full bg-accent mt-1.5 shrink-0" />
                          <div>
                            <div className="text-xs font-semibold text-[#0F172A]">{item.label}</div>
                            <div className="text-[11px] text-[#64748B]">{fmtDate(item.date)} {item.amt ? `— ${fmt(item.amt)}` : ''}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Expenditures */}
                  {work.expenditures && work.expenditures.length > 0 && (
                    <div className="rounded-xl border border-[#E2E8F0] p-4">
                      <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Expenditures ({work.expenditures.length})</div>
                      <div className="space-y-1.5">
                        {work.expenditures.slice(0, 8).map((e: any, i: number) => (
                          <div key={i} className="flex items-center justify-between text-xs p-2 rounded bg-[#F8FAFC]">
                            <span className="truncate max-w-[200px] text-[#475569]">{e.vendor_name || '—'}</span>
                            <span className="font-mono-tech font-bold text-[#0F172A]">{fmt(e.fund_disbursed_amount)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* SIGNALS TAB */}
              {activeTab === 'signals' && (
                <div className="space-y-2">
                  {SIGNAL_ORDER.map(code => {
                    const signal = signals.find((s: any) => s.signal_code === code);
                    const meta = SIGNAL_LABELS[code];
                    const avail = signal?.available ?? false;
                    const sc = signal?.score;
                    return (
                      <div key={code} className={`rounded-xl border border-[#E2E8F0] p-3 ${scoreBg(sc, avail)}`}>
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span className="w-7 h-7 rounded-lg bg-white border border-[#E2E8F0] flex items-center justify-center text-[10px] font-bold font-mono-tech text-[#0F172A]">{code}</span>
                            <div>
                              <div className="text-xs font-semibold text-[#0F172A]">{meta?.name}</div>
                              <div className="text-[10px] font-mono-tech text-[#94A3B8]">Weight: {meta?.weight || signal?.weight}%</div>
                            </div>
                          </div>
                          <div className="text-right">
                            {avail ? (
                              <span className={`text-lg font-bold font-mono-tech ${scoreColor(sc, avail)}`}>{sc?.toFixed(1) ?? '—'}</span>
                            ) : (
                              <span className="text-[10px] font-mono-tech text-[#94A3B8] px-2 py-0.5 rounded bg-[#F1F5F9]">Unavailable</span>
                            )}
                          </div>
                        </div>
                        {signal?.explanation && <div className="text-[11px] text-[#64748B] mt-1 ml-9">{signal.explanation}</div>}
                        {!avail && <div className="text-[10px] font-mono-tech text-[#94A3B8] mt-1 ml-9">Source data not available for this MVP.</div>}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* EVIDENCE TAB */}
              {activeTab === 'evidence' && (
                <div className="space-y-4">
                  {/* X Signal Evidence */}
                  {signals.find((s: any) => s.signal_code === 'X')?.evidence?.top_duplicate_matches && (
                    <div className="rounded-xl border border-[#E2E8F0] p-4">
                      <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Semantic Similarity Matches</div>
                      <div className="space-y-2">
                        {signals.find((s: any) => s.signal_code === 'X')?.evidence.top_duplicate_matches.map((m: any, i: number) => (
                          <div key={i} className="p-2 rounded bg-[#F8FAFC] text-xs">
                            <div className="flex justify-between">
                              <span className="font-mono-tech text-[#0F172A] font-semibold">{m.historical_work_id}</span>
                              <span className="font-mono-tech font-bold text-amber-600">{m.similarity_pct}%</span>
                            </div>
                            <div className="text-[#64748B] truncate mt-0.5">{m.work_description || '—'}</div>
                            <div className="text-[10px] text-[#94A3B8]">{m.constituency || '—'}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Q Signal Evidence */}
                  {signals.find((s: any) => s.signal_code === 'Q')?.evidence && (
                    <div className="rounded-xl border border-[#E2E8F0] p-4">
                      <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Quota Compliance Evidence</div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {Object.entries(signals.find((s: any) => s.signal_code === 'Q')?.evidence || {}).map(([k, v]) => (
                          <div key={k}>
                            <span className="text-[#94A3B8] text-[10px] uppercase">{k.replace(/_/g, ' ')}</span>
                            <div className="font-semibold text-[#0F172A] mt-0.5">{String(v)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* V Signal Evidence */}
                  {signals.find((s: any) => s.signal_code === 'V')?.evidence && (
                    <div className="rounded-xl border border-[#E2E8F0] p-4">
                      <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Vendor Concentration Evidence</div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {Object.entries(signals.find((s: any) => s.signal_code === 'V')?.evidence || {}).map(([k, v]) => (
                          <div key={k}>
                            <span className="text-[#94A3B8] text-[10px] uppercase">{k.replace(/_/g, ' ')}</span>
                            <div className="font-semibold text-[#0F172A] mt-0.5">{String(v)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* All Signal Evidence (raw) */}
                  <details className="rounded-xl border border-[#E2E8F0] p-4">
                    <summary className="text-[10px] font-mono-tech text-[#94A3B8] uppercase cursor-pointer">Technical Evidence (all signals)</summary>
                    <pre className="text-[10px] text-[#64748B] font-mono-tech whitespace-pre-wrap mt-2 p-3 rounded bg-[#F8FAFC] max-h-60 overflow-y-auto">
                      {JSON.stringify(risk?.signals?.map((s: any) => ({ code: s.signal_code, score: s.score, avail: s.available, evidence: s.evidence })), null, 2)}
                    </pre>
                  </details>

                  {/* Inspection History */}
                  {history.length > 0 && (
                    <div className="rounded-xl border border-[#E2E8F0] p-4">
                      <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Inspection Audit Trail</div>
                      <div className="space-y-2">
                        {history.slice(0, 10).map((h: any) => (
                          <div key={h.id} className="p-2 rounded bg-[#F8FAFC] text-xs">
                            <div className="flex justify-between">
                              <span className="font-mono-tech text-accent font-semibold">{h.action?.replace(/_/g, ' ')}</span>
                              <span className="text-[10px] text-[#94A3B8]">{h.created_at ? new Date(h.created_at).toLocaleString('en-IN') : '—'}</span>
                            </div>
                            {h.actor && <div className="text-[10px] text-[#94A3B8] mt-0.5">by {h.actor}</div>}
                            {h.details && <pre className="text-[10px] text-[#64748B] font-mono-tech mt-1 whitespace-pre-wrap">{typeof h.details === 'string' ? h.details : JSON.stringify(h.details, null, 2)}</pre>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
