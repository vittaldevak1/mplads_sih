'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { fetchWorkDetail, fetchRiskScore } from '@/lib/api';
import { WorkDetail, RiskScore } from '@/types';
import SignalRadarChart from '@/components/SignalRadarChart';
import ForensicDossier from '@/components/ForensicDossier';

function getSeverityColor(score: number | null) {
  if (score === null) return { bg: '#F1F5F9', text: '#64748B', border: '#E2E8F0' };
  if (score >= 75) return { bg: '#FEF2F2', text: '#991B1B', border: '#F87171' };
  if (score >= 45) return { bg: '#FFFBEB', text: '#92400E', border: '#FBBF24' };
  return { bg: '#F0FDF4', text: '#166534', border: '#86EFAC' };
}

function getRiskBadge(risk: number | null) {
  if (risk === null) return { label: 'UNRATED', bg: '#F1F5F9', color: '#64748B', border: '#E2E8F0' };
  if (risk >= 65) return { label: 'HIGH RISK', bg: '#FEF2F2', color: '#991B1B', border: '#F87171' };
  if (risk >= 40) return { label: 'MEDIUM RISK', bg: '#FFFBEB', color: '#92400E', border: '#FBBF24' };
  return { label: 'LOW RISK', bg: '#F0FDF4', color: '#166534', border: '#86EFAC' };
}

const SEVERITY_MAP: Record<string, { bg: string; text: string }> = {
  CRITICAL: { bg: '#FEF2F2', text: '#991B1B' },
  HIGH: { bg: '#FFFBEB', text: '#92400E' },
  MEDIUM: { bg: '#EFF6FF', text: '#1E40AF' },
  LOW: { bg: '#F0FDF4', text: '#166534' },
};

export default function WorkDetailPage() {
  const params = useParams();
  const workId = params.work_id as string;
  const [work, setWork] = useState<WorkDetail | null>(null);
  const [risk, setRisk] = useState<RiskScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedSignal, setExpandedSignal] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'signals' | 'anomalies' | 'timeline'>('overview');

  useEffect(() => {
    async function load() {
      try {
        const [w, r] = await Promise.allSettled([
          fetchWorkDetail(workId),
          fetchRiskScore(workId),
        ]);
        if (w.status === 'fulfilled') setWork(w.value);
        if (r.status === 'fulfilled') setRisk(r.value);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [workId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="text-accent font-mono-tech text-sm animate-pulse">
          Loading forensic dossier...
        </div>
      </div>
    );
  }

  if (!work) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#F8FAFC] text-[#64748B]">
        <div className="text-6xl mb-4">404</div>
        <div className="font-mono-tech text-sm">Work not found</div>
        <Link href="/works" className="mt-4 text-accent hover:underline font-mono-tech text-xs">
          Back to Works
        </Link>
      </div>
    );
  }

  const badge = getRiskBadge(risk?.composite_risk ?? null);
  const anomalyCount = work.anomalies?.length ?? 0;

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A]">
      {/* Header */}
      <div className="border-b border-[#E2E8F0] px-3 sm:px-6 py-3 sm:py-4 bg-white">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3 sm:gap-4">
            <Link href="/works" className="text-[#64748B] hover:text-accent font-mono-tech text-xs transition shrink-0">
              ← Back
            </Link>
            <div className="min-w-0">
              <div className="text-[10px] font-mono-tech text-[#94A3B8] uppercase tracking-wider truncate">
                {work.parliament_house === 'lok_sabha' ? 'Lok Sabha' : 'Rajya Sabha'} · {work.work_id}
              </div>
              <h1 className="text-base sm:text-xl font-display text-[#0F172A] mt-1">
                Forensic Audit Dossier
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            <span
              className="px-2 sm:px-3 py-1 sm:py-1.5 rounded font-mono-tech text-[10px] sm:text-xs font-bold uppercase tracking-wider border"
              style={{ background: badge.bg, color: badge.color, borderColor: badge.border }}
            >
              {badge.label} {risk?.composite_risk?.toFixed(1) ?? '—'}
            </span>
            <ForensicDossier work={work} risk={risk} />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-[#E2E8F0] px-3 sm:px-6 bg-white overflow-x-auto">
        <div className="max-w-7xl mx-auto flex gap-0 min-w-max">
          {(['overview', 'signals', 'anomalies', 'timeline'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 sm:px-5 py-2.5 sm:py-3 font-mono-tech text-[10px] sm:text-xs uppercase tracking-wider border-b-2 transition whitespace-nowrap ${
                activeTab === tab
                  ? 'border-accent text-accent'
                  : 'border-transparent text-[#94A3B8] hover:text-[#475569]'
              }`}
            >
              {tab}
              {tab === 'anomalies' && anomalyCount > 0 && (
                <span className="ml-1.5 sm:ml-2 px-1 sm:px-1.5 py-0.5 rounded bg-red-100 text-red-600 text-[9px] sm:text-[10px]">
                  {anomalyCount}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Project Info */}
            <div className="space-y-4">
              <div className="rounded-xl border border-[#E2E8F0] bg-white p-5">
                <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">
                  Project Information
                </div>
                <div className="space-y-2.5 text-sm">
                  {[
                    ['Work ID', work.work_id],
                    ['Description', work.work_description || '—'],
                    ['Category', work.work_category || '—'],
                    ['State', work.state || '—'],
                    ['Constituency', work.constituency || '—'],
                    ['IDA', work.ida || '—'],
                    ['MP', work.mp_name || '—'],
                  ].map(([label, value]) => (
                    <div key={label} className="flex justify-between">
                      <span className="text-[#94A3B8] font-mono-tech text-xs">{label}</span>
                      <span className="text-[#334155] text-xs max-w-[60%] text-right">{value}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-[#E2E8F0] bg-white p-5">
                <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">
                  Financial Summary
                </div>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    ['Sanctioned', `₹${work.sanction_amount?.toLocaleString('en-IN') || '—'}`],
                    ['Disbursed', `₹${work.amount_disbursed?.toLocaleString('en-IN') || '—'}`],
                    ['Sanction Date', work.sanction_date || '—'],
                    ['Completion Date', work.completion_date || '—'],
                    ['Status', work.work_status || '—'],
                    ['Vendor', work.vendor_name || '—'],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <div className="text-[10px] font-mono-tech text-[#94A3B8] uppercase">{label}</div>
                      <div className="text-sm text-[#334155] mt-0.5">{value}</div>
                    </div>
                  ))}
                </div>
              </div>

              {work.expenditures && work.expenditures.length > 0 && (
                <div className="rounded-xl border border-[#E2E8F0] bg-white p-5">
                  <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">
                    Expenditure Entries
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#E2E8F0]">
                          <th className="text-left py-2 text-[#94A3B8] font-mono-tech">Date</th>
                          <th className="text-left py-2 text-[#94A3B8] font-mono-tech">Vendor</th>
                          <th className="text-right py-2 text-[#94A3B8] font-mono-tech">Amount</th>
                          <th className="text-right py-2 text-[#94A3B8] font-mono-tech">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {work.expenditures.map((e, i) => (
                          <tr key={i} className="border-b border-[#F1F5F9]">
                            <td className="py-1.5 text-[#475569]">{e.expenditure_date || '—'}</td>
                            <td className="py-1.5 text-[#475569]">{e.vendor_name || '—'}</td>
                            <td className="py-1.5 text-right text-[#475569]">
                              ₹{e.fund_disbursed_amount?.toLocaleString('en-IN') || '—'}
                            </td>
                            <td className="py-1.5 text-right text-[#94A3B8]">{e.payment_status || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Right: Radar + Confidence */}
            <div className="space-y-4">
              <div className="rounded-xl border border-[#E2E8F0] bg-white p-5">
                <SignalRadarChart signals={risk?.signals ?? []} compositeRisk={risk?.composite_risk ?? null} />
              </div>

              {risk && (
                <div className="rounded-xl border border-[#E2E8F0] bg-white p-5">
                  <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">
                    AI Confidence Coverage
                  </div>
                  <div className="flex items-end gap-3">
                    <div className="text-4xl font-display text-[#0F172A]">
                      {risk.confidence_coverage !== null ? `${(risk.confidence_coverage * 100).toFixed(0)}%` : '—'}
                    </div>
                    <div className="text-xs text-[#94A3B8] mb-1">
                      of available signals scored
                    </div>
                  </div>
                  <div className="mt-3 w-full bg-[#E2E8F0] rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-accent to-blue-400"
                      style={{ width: `${(risk.confidence_coverage ?? 0) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Signals Tab */}
        {activeTab === 'signals' && (
          <div className="space-y-3">
            {risk?.signals.map((signal) => {
              const sev = getSeverityColor(signal.score);
              const isExpanded = expandedSignal === signal.signal_code;
              return (
                <div key={signal.signal_code} className="rounded-xl border border-[#E2E8F0] bg-white overflow-hidden">
                  <button
                    onClick={() => setExpandedSignal(isExpanded ? null : signal.signal_code)}
                    className="w-full flex items-center justify-between px-5 py-4 hover:bg-[#F8FAFC] transition text-left"
                  >
                    <div className="flex items-center gap-4">
                      <span
                        className="w-10 h-10 rounded-lg flex items-center justify-center font-mono-tech text-sm font-bold"
                        style={{ background: sev.bg, color: sev.text, border: `1px solid ${sev.border}` }}
                      >
                        {signal.signal_code}
                      </span>
                      <div>
                        <div className="text-sm font-semibold text-[#334155]">{signal.signal_name}</div>
                        <div className="text-[10px] font-mono-tech text-[#94A3B8]">
                          v{signal.version || '—'} · Weight {(signal.weight * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span
                        className="px-2.5 py-1 rounded text-xs font-bold font-mono-tech"
                        style={{ background: sev.bg, color: sev.text }}
                      >
                        {signal.available && signal.score !== null ? signal.score.toFixed(0) : 'N/A'}
                      </span>
                      <span
                        className="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                        style={{ background: sev.bg, color: sev.text }}
                      >
                        {signal.available && signal.score !== null
                          ? signal.score >= 75 ? 'CRITICAL' : signal.score >= 45 ? 'ELEVATED' : 'CLEAR'
                          : 'UNAVAILABLE'}
                      </span>
                      <span className={`text-[#94A3B8] transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                        ▼
                      </span>
                    </div>
                  </button>
                  {isExpanded && (
                    <div className="border-t border-[#E2E8F0] px-5 py-4 bg-[#F8FAFC]">
                      <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-2">
                        Why This Risk Score?
                      </div>
                      <p className="text-sm text-[#475569] leading-relaxed">
                        {signal.explanation || 'No explanation provided by AI engine.'}
                      </p>
                      {signal.evidence && typeof signal.evidence === 'object' && !Array.isArray(signal.evidence) && (
                        <div className="mt-3 p-3 rounded-lg bg-white border border-[#E2E8F0]">
                          <div className="text-[10px] font-mono-tech text-[#94A3B8] mb-2">Evidence</div>
                          <pre className="text-xs text-[#64748B] font-mono-tech whitespace-pre-wrap overflow-x-auto">
                            {JSON.stringify(signal.evidence, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
            {!risk && (
              <div className="text-center py-12 text-[#94A3B8] font-mono-tech text-sm">
                No risk signals available for this work.
              </div>
            )}
          </div>
        )}

        {/* Anomalies Tab */}
        {activeTab === 'anomalies' && (
          <div className="space-y-3">
            {work.anomalies && work.anomalies.length > 0 ? (
              work.anomalies.map((anomaly) => {
                const sevStyle = SEVERITY_MAP[anomaly.severity] || SEVERITY_MAP.LOW;
                return (
                  <div key={anomaly.id} className="rounded-xl border border-[#E2E8F0] bg-white p-5">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <span
                          className="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono-tech"
                          style={{ background: sevStyle.bg, color: sevStyle.text }}
                        >
                          {anomaly.severity}
                        </span>
                        <div>
                          <div className="text-sm font-semibold text-[#334155]">{anomaly.anomaly_type}</div>
                          <div className="text-xs text-[#64748B] mt-1">{anomaly.description}</div>
                        </div>
                      </div>
                      <div className="text-[10px] font-mono-tech text-[#94A3B8]">
                        {anomaly.created_at ? new Date(anomaly.created_at).toLocaleDateString('en-IN') : '—'}
                      </div>
                    </div>
                    {anomaly.evidence && (
                      <div className="mt-3 p-3 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0]">
                        <pre className="text-xs text-[#64748B] font-mono-tech whitespace-pre-wrap overflow-x-auto">
                          {JSON.stringify(anomaly.evidence, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="text-center py-12 text-[#94A3B8] font-mono-tech text-sm">
                No anomalies detected for this work.
              </div>
            )}
          </div>
        )}

        {/* Timeline Tab */}
        {activeTab === 'timeline' && (
          <div className="rounded-xl border border-[#E2E8F0] bg-white p-6">
            <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-4">
              Work Lifecycle Timeline
            </div>
            <div className="relative">
              <div className="absolute left-[18px] top-0 bottom-0 w-px bg-[#E2E8F0]" />
              {[
                { label: 'Recommended', date: work.recommended_date, amount: work.recommended_amount },
                { label: 'Sanctioned', date: work.sanction_date, amount: work.sanction_amount },
                { label: 'Completed', date: work.completion_date, amount: work.amount_disbursed },
              ].map((step, i) => {
                const isActive = !!step.date;
                return (
                  <div key={step.label} className="relative flex items-start gap-4 mb-6 last:mb-0">
                    <div
                      className={`w-9 h-9 rounded-full flex items-center justify-center z-10 border-2 ${
                        isActive
                          ? 'bg-accent/10 border-accent text-accent'
                          : 'bg-white border-[#E2E8F0] text-[#CBD5E1]'
                      }`}
                    >
                      <span className="text-xs font-bold">{i + 1}</span>
                    </div>
                    <div className="pt-1">
                      <div className="text-sm font-semibold text-[#334155]">{step.label}</div>
                      <div className="text-xs text-[#94A3B8] mt-0.5">
                        {step.date || 'Not recorded'}
                        {step.amount !== null && step.amount !== undefined && (
                          <span className="ml-2 text-accent">₹{step.amount.toLocaleString('en-IN')}</span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
