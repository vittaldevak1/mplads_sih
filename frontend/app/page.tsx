'use client';

import { useEffect, useState, useCallback } from 'react';
import { fetchDashboardSummary, fetchInspectionQueue, fetchAnomalies, triggerAIAudit, fetchAuditStatus } from '@/lib/api';
import { DashboardSummary, InspectionQueueItem, Anomaly } from '@/types';
import WorkForensicDrawer from '@/components/WorkForensicDrawer';
import { useAuth, ROLE_LABELS } from '@/lib/auth';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, CartesianGrid, Legend,
} from 'recharts';

function formatCurrency(amount: number): string {
  if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(2)} Cr`;
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(2)} L`;
  return `₹${amount.toLocaleString('en-IN')}`;
}

const RISK_COLORS = ['#DC2626', '#D97706', '#2563EB', '#16A34A'];
const ACCENT = '#1E3A8A';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-[#E2E8F0] rounded-lg px-3 py-2 shadow-lg">
      <div className="text-[10px] font-mono-tech text-[#64748B] mb-1">{label}</div>
      {payload.map((p: any, i: number) => (
        <div key={i} className="text-xs font-mono-tech" style={{ color: p.color }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString('en-IN') : p.value}
        </div>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [criticalWorks, setCriticalWorks] = useState<InspectionQueueItem[]>([]);
  const [recentAnomalies, setRecentAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [auditRunning, setAuditRunning] = useState(false);
  const [auditStatus, setAuditStatus] = useState<string | null>(null);
  const [auditProgress, setAuditProgress] = useState({ processed: 0, total: 0 });
  const [selectedWorkId, setSelectedWorkId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [s, q, a] = await Promise.all([
          fetchDashboardSummary(),
          fetchInspectionQueue({ priority: 'HIGH', limit: 5 }),
          fetchAnomalies({ size: 5, anomaly_type: 'HIGH_RISK' }),
        ]);
        setSummary(s);
        setCriticalWorks(q.items || []);
        setRecentAnomalies(a.items || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleRunAudit = async () => {
    setAuditRunning(true);
    setAuditStatus('Starting AI audit...');
    try {
      const result = await triggerAIAudit(88111);
      setAuditStatus(`Audit started for ${result.total} works.`);
      const pollInterval = setInterval(async () => {
        try {
          const status = await fetchAuditStatus();
          setAuditProgress({ processed: status.works_processed, total: status.total });
          if (!status.running) {
            clearInterval(pollInterval);
            setAuditStatus(`Audit complete. ${status.works_processed} works analyzed.`);
            setAuditRunning(false);
            const data = await fetchDashboardSummary();
            setSummary(data);
          }
        } catch { /* ignore */ }
      }, 5000);
    } catch {
      setAuditStatus('Audit failed. Check backend.');
      setAuditRunning(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-accent font-mono-tech animate-pulse">Loading dashboard...</div>
      </div>
    );
  }

  const riskPieData = [
    { name: 'High Risk', value: summary?.high_risk || 0 },
    { name: 'Medium Risk', value: summary?.medium_risk || 0 },
    { name: 'Low Risk', value: summary?.low_risk || 0 },
  ];

  const kpis = [
    { label: 'Total Works', value: summary?.total_works || 0, border: 'border-l-[#1E3A8A]' },
    { label: 'Recommended', value: summary?.works_recommended || 0, border: 'border-l-[#2563EB]' },
    { label: 'Sanctioned', value: summary?.works_sanctioned || 0, border: 'border-l-[#D97706]' },
    { label: 'Completed', value: summary?.works_completed || 0, border: 'border-l-[#16A34A]' },
    { label: 'Total Sanctioned', value: formatCurrency(summary?.total_sanctioned_amount || 0), border: 'border-l-[#D97706]', isCurrency: true },
    { label: 'Total Expenditure', value: formatCurrency(summary?.total_expenditure || 0), border: 'border-l-[#16A34A]', isCurrency: true },
    { label: 'Budget Utilization', value: `${summary?.budget_utilization || 0}%`, border: 'border-l-[#1E3A8A]' },
    { label: 'Active Vendors', value: summary?.active_vendors || 0, border: 'border-l-[#64748B]' },
  ];

  return (
    <div className="max-w-[1400px] mx-auto px-3 sm:px-5 lg:px-8 py-4 sm:py-6 space-y-4 sm:space-y-5">
      {/* Official Header */}
      <div className="gov-panel p-3 sm:p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="text-[9px] sm:text-[10px] uppercase tracking-[0.15em] font-semibold text-[#1E3A8A]">
              Government of India · Ministry of Statistics &amp; Programme Implementation
            </div>
            <h1 className="text-base sm:text-lg font-serif-luxury font-bold text-[#0F172A] mt-1">
              MPLADS Forensic Audit &amp; Monitoring Platform
            </h1>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {/* Status Indicators */}
            <div className="hidden lg:flex items-center gap-3 px-4 py-2 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0]">
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A]" />
                <span className="text-[10px] font-mono-tech text-[#64748B]">System</span>
              </div>
              <div className="w-px h-3 bg-[#E2E8F0]" />
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${summary && summary.high_risk > 0 ? 'bg-[#D97706]' : 'bg-[#94A3B8]'}`} />
                <span className="text-[10px] font-mono-tech text-[#64748B]">AI Engine</span>
              </div>
              <div className="w-px h-3 bg-[#E2E8F0]" />
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#2563EB]" />
                <span className="text-[10px] font-mono-tech text-[#64748B]">Data</span>
              </div>
            </div>
            <button
              onClick={handleRunAudit}
              disabled={auditRunning}
              className={`px-3 sm:px-4 py-2 rounded-lg text-xs font-bold font-mono-tech transition whitespace-nowrap ${
                auditRunning
                  ? 'bg-[#F1F5F9] text-[#94A3B8] cursor-not-allowed'
                  : 'bg-accent text-white hover:bg-accent-light'
              }`}
            >
              {auditRunning ? `Processing ${auditProgress.processed}/${auditProgress.total}...` : 'Run AI Audit'}
            </button>
          </div>
        </div>
      </div>

      {/* Role Scope Banner */}
      {user && user.role !== 'ministry_admin' && (
        <div className="gov-panel px-3 sm:px-4 py-2 sm:py-2.5 flex items-center gap-2">
          <svg className="w-3.5 h-3.5 text-accent shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-[10px] font-mono-tech text-[#64748B]">
            Viewing as <span className="font-bold text-accent">{ROLE_LABELS[user.role]}</span>
            {user.state && <span> — {user.constituency ? `${user.constituency}, ${user.state}` : user.district ? `${user.district}, ${user.state}` : user.state}</span>}
          </span>
        </div>
      )}

      {auditStatus && (
        <div className="gov-panel px-3 sm:px-4 py-2 sm:py-3 text-xs font-mono-tech text-accent">
          {auditStatus}
          {auditRunning && auditProgress.total > 0 && (
            <div className="mt-2 w-full bg-[#E2E8F0] rounded-full h-1.5">
              <div
                className="h-1.5 rounded-full bg-accent transition-all"
                style={{ width: `${(auditProgress.processed / auditProgress.total) * 100}%` }}
              />
            </div>
          )}
        </div>
      )}

      {/* KPI Grid */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3">
        {kpis.map((kpi, idx) => (
          <div key={idx} className={`gov-panel rounded-lg p-3 sm:p-4 border-l-4 ${kpi.border}`}>
            <div className="text-[9px] sm:text-[10px] font-mono-tech text-[#94A3B8] uppercase tracking-wider">
              {kpi.label}
            </div>
            <div className="text-lg sm:text-xl font-serif-luxury font-bold mt-1 text-[#0F172A] truncate">
              {kpi.value}
            </div>
          </div>
        ))}
      </section>

      {/* Charts Row */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4">
        {/* Risk Distribution */}
        <div className="gov-panel p-3 sm:p-5">
          <div className="text-[10px] font-mono-tech text-[#1E3A8A] uppercase tracking-wider mb-3 font-semibold">
            Risk Distribution
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={riskPieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3} dataKey="value">
                {riskPieData.map((_, i) => <Cell key={i} fill={RISK_COLORS[i]} />)}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '10px', fontFamily: 'JetBrains Mono' }}
                formatter={(value: any) => <span className="text-[#64748B]">{value}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Stage Progression */}
        <div className="gov-panel p-3 sm:p-5">
          <div className="text-[10px] font-mono-tech text-[#1E3A8A] uppercase tracking-wider mb-3 font-semibold">
            Works by Stage
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={[
              { stage: 'Recommended', count: summary?.works_recommended || 0 },
              { stage: 'Sanctioned', count: summary?.works_sanctioned || 0 },
              { stage: 'Completed', count: summary?.works_completed || 0 },
            ]}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="stage" tick={{ fontSize: 10, fill: '#64748B', fontFamily: 'JetBrains Mono' }} />
              <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" fill={ACCENT} radius={[4, 4, 0, 0]} name="Works" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Budget */}
        <div className="gov-panel p-3 sm:p-5">
          <div className="text-[10px] font-mono-tech text-[#1E3A8A] uppercase tracking-wider mb-3 font-semibold">
            Budget vs Expenditure
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={[
              { name: 'Allocated', amount: (summary?.total_allocation || 0) / 10000000 },
              { name: 'Sanctioned', amount: (summary?.total_sanctioned_amount || 0) / 10000000 },
              { name: 'Spent', amount: (summary?.total_expenditure || 0) / 10000000 },
            ]}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748B', fontFamily: 'JetBrains Mono' }} />
              <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="amount" fill="#2563EB" radius={[4, 4, 0, 0]} name="Amount (Cr)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Alerts + Anomalies */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        {/* Critical Alerts */}
        <div className="gov-panel p-3 sm:p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="text-[10px] font-mono-tech text-risk-critical uppercase tracking-wider flex items-center gap-2 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-risk-critical animate-pulse" />
              Priority Alerts — High Risk
            </div>
            <a href="/inspection" className="text-[10px] font-mono-tech text-accent hover:underline">View All →</a>
          </div>
          <div className="space-y-2">
            {criticalWorks.length === 0 ? (
              <div className="text-xs text-[#94A3B8] font-mono-tech py-4 text-center">No high-risk works</div>
            ) : (
              criticalWorks.map((w) => (
                <button key={w.work_id} onClick={() => setSelectedWorkId(w.work_id)}
                  className="flex items-center justify-between p-2.5 sm:p-3 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0] hover:border-risk-critical/30 transition w-full text-left"
                >
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-[#334155] truncate">{w.work_description || w.work_id}</div>
                    <div className="text-[10px] font-mono-tech text-[#94A3B8] mt-0.5">
                      {w.state} · {w.constituency} · {w.signal_count} signals
                    </div>
                  </div>
                  <div className="ml-3 text-right shrink-0">
                    <div className="text-sm font-mono-tech font-bold text-risk-critical">{w.composite_risk?.toFixed(1) ?? '—'}</div>
                    <div className="text-[10px] font-mono-tech text-[#94A3B8]">₹{w.sanction_amount?.toLocaleString('en-IN') || '—'}</div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Recent Anomalies */}
        <div className="gov-panel p-3 sm:p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider font-semibold">
              Recent Anomalies
            </div>
            <a href="/anomalies" className="text-[10px] font-mono-tech text-accent hover:underline">View All →</a>
          </div>
          <div className="space-y-2">
            {recentAnomalies.length === 0 ? (
              <div className="text-xs text-[#94A3B8] font-mono-tech py-4 text-center">No anomalies yet</div>
            ) : (
              recentAnomalies.map((a) => (
                <button key={a.id} onClick={() => setSelectedWorkId(a.work_id)}
                  className="flex items-center justify-between p-2.5 sm:p-3 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0] hover:border-accent/30 transition w-full text-left"
                >
                  <div className="flex items-center gap-2 sm:gap-2.5 flex-1 min-w-0">
                    <span className={`w-1.5 h-6 sm:h-8 rounded-full shrink-0 ${
                      a.severity === 'HIGH' ? 'bg-[#DC2626]' :
                      a.severity === 'MEDIUM' ? 'bg-[#D97706]' : 'bg-[#2563EB]'
                    }`} />
                    <div className="min-w-0">
                      <div className="text-xs text-[#334155] truncate">{a.anomaly_type}</div>
                      <div className="text-[10px] font-mono-tech text-[#94A3B8] truncate">{a.description}</div>
                    </div>
                  </div>
                  <div className="text-[10px] font-mono-tech text-[#94A3B8] shrink-0 ml-2">
                    Risk: {a.composite_risk != null ? a.composite_risk.toFixed(1) : '—'}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      </section>

      {/* 11-Signal Framework */}
      <section className="gov-panel p-3 sm:p-5">
        <div className="flex items-center gap-2 mb-3 sm:mb-4">
          <div className="text-sm font-serif-luxury font-bold text-[#0F172A]">
            11-Signal Risk Framework
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
          {[
            { code: 'F', name: 'Financial Disbursement Alert', weight: '15%' },
            { code: 'D', name: 'Delay / Duration Monitoring', weight: '12%' },
            { code: 'X', name: 'Semantic Similarity Detection', weight: '12%' },
            { code: 'V', name: 'Vendor Network Risk', weight: '10%' },
            { code: 'C', name: 'Citizen Complaints — Unavailable', weight: '10%' },
            { code: 'Q', name: 'Quota Compliance Indicator', weight: '10%' },
            { code: 'O', name: 'OCR / Document — Unavailable', weight: '8%' },
            { code: 'S', name: 'Spatial — Unavailable', weight: '7%' },
            { code: 'G', name: 'Satellite — Unavailable', weight: '8%' },
            { code: 'B', name: 'Statistical Threshold Alert', weight: '4%' },
            { code: 'Rs', name: 'Cost/Gestation Outlier', weight: '4%' },
          ].map((signal) => (
            <div key={signal.code} className="p-2 sm:p-2.5 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0] hover:border-accent/30 transition">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-mono-tech text-accent font-semibold">{signal.code}</span>
                <span className="text-[10px] font-mono-tech px-1.5 py-0.5 rounded bg-accent/10 text-accent border border-accent/20">
                  {signal.weight}
                </span>
              </div>
              <div className="text-[11px] text-[#475569] truncate">{signal.name}</div>
            </div>
          ))}
        </div>
      </section>

      <WorkForensicDrawer workId={selectedWorkId} onClose={() => setSelectedWorkId(null)} sourcePage="Dashboard" />
    </div>
  );
}
