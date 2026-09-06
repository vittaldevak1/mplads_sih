'use client';

import { useEffect, useState, useCallback } from 'react';
import { fetchWorkDetail, fetchRiskScore } from '@/lib/api';

const SIGNAL_LABELS: Record<string, { name: string; weight: number }> = {
  F: { name: 'Financial / Cost Overrun', weight: 15 },
  D: { name: 'Delay / Duration', weight: 12 },
  X: { name: 'Semantic Duplicate', weight: 12 },
  V: { name: 'Vendor / Network Risk', weight: 10 },
  C: { name: 'Citizen Complaints', weight: 10 },
  Q: { name: 'Quota Compliance', weight: 10 },
  O: { name: 'OCR / Document', weight: 8 },
  S: { name: 'Spatial Duplication', weight: 7 },
  G: { name: 'Satellite Ground-Truth', weight: 8 },
  B: { name: 'Benford / Statistical', weight: 4 },
  Rs: { name: 'SoR / Statistical', weight: 4 },
};

const SIGNAL_ORDER = ['F', 'D', 'X', 'V', 'C', 'Q', 'O', 'S', 'G', 'B', 'Rs'];

interface WorkDrawerProps {
  workId: string | null;
  onClose: () => void;
}

export default function WorkDrawer({ workId, onClose }: WorkDrawerProps) {
  const [work, setWork] = useState<any>(null);
  const [risk, setRisk] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'signals' | 'timeline'>('overview');

  const loadData = useCallback(async () => {
    if (!workId) return;
    setLoading(true);
    setError(null);
    try {
      const [workData, riskData] = await Promise.allSettled([
        fetchWorkDetail(workId),
        fetchRiskScore(workId),
      ]);
      if (workData.status === 'fulfilled') setWork(workData.value);
      if (riskData.status === 'fulfilled') setRisk(riskData.value);
    } catch (e: any) {
      setError(e.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [workId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (workId) {
      document.addEventListener('keydown', handleEsc);
      return () => document.removeEventListener('keydown', handleEsc);
    }
  }, [workId, onClose]);

  if (!workId) return null;

  const formatCurrency = (val: number | null | undefined) => {
    if (val === null || val === undefined) return '—';
    return `₹${val.toLocaleString('en-IN')}`;
  };

  const formatDate = (val: string | null | undefined) => {
    if (!val) return '—';
    try { return new Date(val).toLocaleDateString('en-IN'); } catch { return val; }
  };

  const getScoreColor = (score: number | null | undefined, available: boolean) => {
    if (!available || score === null || score === undefined) return 'text-[#94A3B8]';
    if (score >= 65) return 'text-red-600';
    if (score >= 40) return 'text-amber-600';
    return 'text-emerald-600';
  };

  const getScoreBg = (score: number | null | undefined, available: boolean) => {
    if (!available || score === null || score === undefined) return 'bg-[#F1F5F9]';
    if (score >= 65) return 'bg-red-50';
    if (score >= 40) return 'bg-amber-50';
    return 'bg-emerald-50';
  };

  const getPriorityStyle = (p: string | null) => {
    switch (p) {
      case 'HIGH': return { bg: '#FEF2F2', text: '#991B1B', border: '#F87171' };
      case 'MEDIUM': return { bg: '#FFFBEB', text: '#92400E', border: '#FBBF24' };
      case 'LOW': return { bg: '#F0FDF4', text: '#166534', border: '#86EFAC' };
      default: return { bg: '#F1F5F9', text: '#64748B', border: '#E2E8F0' };
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/30 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-full max-w-2xl bg-white z-50 shadow-2xl flex flex-col">
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#E2E8F0] flex items-center justify-between shrink-0">
          <div className="min-w-0 flex-1">
            <div className="text-[10px] font-mono-tech text-[#94A3B8] uppercase">Forensic Work Analysis</div>
            <div className="text-sm font-bold text-[#0F172A] font-mono-tech truncate">{workId}</div>
          </div>
          <button
            onClick={onClose}
            className="ml-4 w-8 h-8 rounded-lg bg-[#F1F5F9] hover:bg-[#E2E8F0] flex items-center justify-center text-[#64748B] transition shrink-0"
          >
            ✕
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex-1 flex items-center justify-center text-[#94A3B8] font-mono-tech text-sm animate-pulse">
            Loading forensic data...
          </div>
        )}

        {error && (
          <div className="flex-1 flex items-center justify-center text-red-500 font-mono-tech text-sm">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="flex-1 overflow-y-auto">
            {/* Tabs */}
            <div className="flex border-b border-[#E2E8F0] shrink-0">
              {(['overview', 'signals', 'timeline'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2.5 text-xs font-mono-tech uppercase transition border-b-2 ${
                    activeTab === tab
                      ? 'border-accent text-accent font-bold'
                      : 'border-transparent text-[#94A3B8] hover:text-[#64748B]'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="p-5">
              {/* OVERVIEW TAB */}
              {activeTab === 'overview' && work && (
                <div className="space-y-5">
                  {/* Work Metadata */}
                  <div className="rounded-xl border border-[#E2E8F0] p-4">
                    <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Work Identity</div>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-[#94A3B8]">Description</span>
                        <div className="font-semibold text-[#0F172A] mt-0.5">{work.work_description || work.work_title || '—'}</div>
                      </div>
                      <div>
                        <span className="text-[#94A3B8]">Category</span>
                        <div className="font-semibold text-[#0F172A] mt-0.5">{work.work_category || '—'}</div>
                      </div>
                      <div>
                        <span className="text-[#94A3B8]">State</span>
                        <div className="font-semibold text-[#0F172A] mt-0.5">{work.state || '—'}</div>
                      </div>
                      <div>
                        <span className="text-[#94A3B8]">Constituency</span>
                        <div className="font-semibold text-[#0F172A] mt-0.5">{work.constituency || '—'}</div>
                      </div>
                      <div>
                        <span className="text-[#94A3B8]">MP</span>
                        <div className="font-semibold text-[#0F172A] mt-0.5">{work.mp_name || '—'}</div>
                      </div>
                      <div>
                        <span className="text-[#94A3B8]">Implementing Agency</span>
                        <div className="font-semibold text-[#0F172A] mt-0.5">{work.ida || '—'}</div>
                      </div>
                      <div>
                        <span className="text-[#94A3B8]">Vendor</span>
                        <div className="font-semibold text-[#0F172A] mt-0.5">{work.vendor_name || '—'}</div>
                      </div>
                      <div>
                        <span className="text-[#94A3B8]">Status</span>
                        <div className="font-semibold text-[#0F172A] mt-0.5">{work.work_status || '—'}</div>
                      </div>
                    </div>
                  </div>

                  {/* Financial Details */}
                  <div className="rounded-xl border border-[#E2E8F0] p-4">
                    <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Financial Details</div>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-[#94A3B8]">Recommended Amount</span>
                        <div className="font-bold text-[#0F172A] mt-0.5">{formatCurrency(work.recommended_amount)}</div>
                      </div>
                      <div>
                        <span className="text-[#94A3B8]">Sanction Amount</span>
                        <div className="font-bold text-[#0F172A] mt-0.5">{formatCurrency(work.sanction_amount)}</div>
                      </div>
                      <div>
                        <span className="text-[#94A3B8]">Disbursed Amount</span>
                        <div className="font-bold text-[#0F172A] mt-0.5">{formatCurrency(work.amount_disbursed)}</div>
                      </div>
                      <div>
                        <span className="text-[#94A3B8]">Completion Date</span>
                        <div className="font-semibold text-[#0F172A] mt-0.5">{formatDate(work.completion_date)}</div>
                      </div>
                    </div>
                  </div>

                  {/* Risk Summary */}
                  {risk && (
                    <div className="rounded-xl border border-[#E2E8F0] p-4">
                      <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Risk Assessment</div>
                      <div className="grid grid-cols-3 gap-3">
                        <div className="text-center p-3 rounded-lg bg-[#F8FAFC]">
                          <div className="text-2xl font-bold font-mono-tech text-[#0F172A]">
                            {risk.composite_risk?.toFixed(1) ?? '—'}
                          </div>
                          <div className="text-[10px] font-mono-tech text-[#94A3B8] mt-1">Composite Risk</div>
                        </div>
                        <div className="text-center p-3 rounded-lg bg-[#F8FAFC]">
                          <div className="text-lg font-bold font-mono-tech">
                            <span className={`px-2 py-0.5 rounded text-xs font-bold ${getPriorityStyle(risk.inspection_priority).text}`}
                              style={{ background: getPriorityStyle(risk.inspection_priority).bg, border: `1px solid ${getPriorityStyle(risk.inspection_priority).border}` }}>
                              {risk.inspection_priority || '—'}
                            </span>
                          </div>
                          <div className="text-[10px] font-mono-tech text-[#94A3B8] mt-1">Priority</div>
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

                  {/* Quota Tags */}
                  <div className="flex gap-2">
                    {work.is_sc_quota && (
                      <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 text-[10px] font-mono-tech font-bold border border-purple-200">SC Quota</span>
                    )}
                    {work.is_st_quota && (
                      <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-[10px] font-mono-tech font-bold border border-indigo-200">ST Quota</span>
                    )}
                  </div>
                </div>
              )}

              {/* SIGNALS TAB */}
              {activeTab === 'signals' && risk && (
                <div className="space-y-2">
                  {SIGNAL_ORDER.map((code) => {
                    const signal = risk.signals?.find((s: any) => s.signal_code === code);
                    const meta = SIGNAL_LABELS[code];
                    const available = signal?.available ?? false;
                    const score = signal?.score;

                    return (
                      <div key={code} className={`rounded-xl border border-[#E2E8F0] p-3 ${getScoreBg(score, available)}`}>
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span className="w-7 h-7 rounded-lg bg-white border border-[#E2E8F0] flex items-center justify-center text-[10px] font-bold font-mono-tech text-[#0F172A]">
                              {code}
                            </span>
                            <div>
                              <div className="text-xs font-semibold text-[#0F172A]">{meta?.name || code}</div>
                              <div className="text-[10px] font-mono-tech text-[#94A3B8]">Weight: {meta?.weight || signal?.weight}%</div>
                            </div>
                          </div>
                          <div className="text-right">
                            {available ? (
                              <span className={`text-lg font-bold font-mono-tech ${getScoreColor(score, available)}`}>
                                {score?.toFixed(1) ?? '—'}
                              </span>
                            ) : (
                              <span className="text-xs font-mono-tech text-[#94A3B8] px-2 py-0.5 rounded bg-[#F1F5F9]">
                                Unavailable
                              </span>
                            )}
                          </div>
                        </div>
                        {signal?.explanation && (
                          <div className="text-[11px] text-[#64748B] mt-1 ml-9">{signal.explanation}</div>
                        )}
                        {!available && (
                          <div className="text-[10px] font-mono-tech text-[#94A3B8] mt-1 ml-9">
                            Source data not available for this MVP.
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* TIMELINE TAB */}
              {activeTab === 'timeline' && work && (
                <div className="space-y-3">
                  <div className="rounded-xl border border-[#E2E8F0] p-4">
                    <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">Work Timeline</div>
                    <div className="space-y-3">
                      {[
                        { label: 'Recommended', date: work.recommended_date, amount: work.recommended_amount },
                        { label: 'Sanctioned', date: work.sanction_date, amount: work.sanction_amount },
                        { label: 'Completed', date: work.completion_date, amount: work.amount_disbursed },
                      ].map((item, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="w-2 h-2 rounded-full bg-accent mt-1.5 shrink-0" />
                          <div className="flex-1">
                            <div className="text-xs font-semibold text-[#0F172A]">{item.label}</div>
                            <div className="text-[11px] text-[#64748B]">
                              {formatDate(item.date)} {item.amount ? `— ${formatCurrency(item.amount)}` : ''}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Expenditures */}
                  {work.expenditures && work.expenditures.length > 0 && (
                    <div className="rounded-xl border border-[#E2E8F0] p-4">
                      <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">
                        Expenditures ({work.expenditures.length})
                      </div>
                      <div className="space-y-2">
                        {work.expenditures.slice(0, 5).map((exp: any, i: number) => (
                          <div key={i} className="flex items-center justify-between text-xs p-2 rounded bg-[#F8FAFC]">
                            <div className="truncate max-w-[200px]">{exp.vendor_name || '—'}</div>
                            <div className="font-mono-tech font-bold">{formatCurrency(exp.fund_disbursed_amount)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Anomalies */}
                  {work.anomalies && work.anomalies.length > 0 && (
                    <div className="rounded-xl border border-[#E2E8F0] p-4">
                      <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">
                        Flagged Items ({work.anomalies.length})
                      </div>
                      <div className="space-y-2">
                        {work.anomalies.slice(0, 5).map((a: any, i: number) => (
                          <div key={i} className="text-xs p-2 rounded bg-[#F8FAFC]">
                            <div className="font-semibold text-[#0F172A]">{a.anomaly_type}</div>
                            <div className="text-[#64748B] truncate">{a.description}</div>
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
