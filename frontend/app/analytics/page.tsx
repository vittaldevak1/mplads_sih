'use client';

import { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend, Line, ComposedChart, Area,
} from 'recharts';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const RISK_COLORS = ['#DC2626', '#D97706', '#2563EB', '#16A34A'];
const BENFORD_THEORETICAL = '#1E3A8A';
const BENFORD_EMPIRICAL = '#D97706';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-[#E2E8F0] rounded-lg px-3 py-2 shadow-xl">
      <div className="text-[10px] font-mono-tech text-[#94A3B8] mb-1">{label}</div>
      {payload.map((p: any, i: number) => (
        <div key={i} className="text-xs font-mono-tech" style={{ color: p.color || p.fill }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString('en-IN') : p.value}
        </div>
      ))}
    </div>
  );
};

interface BenfordData {
  sample_size: number;
  empirical: Record<string, number>;
  theoretical: Record<string, number>;
}

interface StateRisk {
  state: string;
  CRITICAL: number;
  HIGH: number;
  MEDIUM: number;
  LOW: number;
  total: number;
}

interface CategoryRisk {
  category: string;
  CRITICAL: number;
  HIGH: number;
  MEDIUM: number;
  LOW: number;
  total: number;
}

interface SankeyFlow {
  works_flow: { recommended: number; sanctioned: number; completed: number; ongoing: number };
  amount_flow: { sanctioned: number; disbursed: number; unspent: number };
}

export default function AnalyticsPage() {
  const [benford, setBenford] = useState<BenfordData | null>(null);
  const [stateRisk, setStateRisk] = useState<StateRisk[]>([]);
  const [categoryRisk, setCategoryRisk] = useState<CategoryRisk[]>([]);
  const [sankey, setSankey] = useState<SankeyFlow | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [b, s, c, f] = await Promise.all([
          fetch(`${API_BASE_URL}/dashboard/benford`).then(r => r.json()),
          fetch(`${API_BASE_URL}/dashboard/state-risk`).then(r => r.json()),
          fetch(`${API_BASE_URL}/dashboard/category-risk`).then(r => r.json()),
          fetch(`${API_BASE_URL}/dashboard/sankey`).then(r => r.json()),
        ]);
        setBenford(b);
        setStateRisk(s.states || []);
        setCategoryRisk(c.categories || []);
        setSankey(f);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const benfordChartData = benford
    ? Object.keys(benford.empirical).map(d => ({
        digit: d,
        empirical: benford.empirical[d],
        theoretical: benford.theoretical[d],
      }))
    : [];

  const stateRiskData = stateRisk.map(s => ({
    name: s.state?.length > 15 ? s.state.slice(0, 15) + '...' : s.state,
    CRITICAL: s.CRITICAL,
    HIGH: s.HIGH,
    MEDIUM: s.MEDIUM,
    LOW: s.LOW,
  }));

  const categoryRiskData = categoryRisk.map(c => ({
    name: c.category?.length > 20 ? c.category.slice(0, 20) + '...' : c.category,
    CRITICAL: c.CRITICAL,
    HIGH: c.HIGH,
    MEDIUM: c.MEDIUM,
    LOW: c.LOW,
  }));

  const budgetFlowData = sankey
    ? [
        { stage: 'Sanctioned', amount: sankey.amount_flow.sanctioned / 1e7 },
        { stage: 'Disbursed', amount: sankey.amount_flow.disbursed / 1e7 },
        { stage: 'Unspent', amount: sankey.amount_flow.unspent / 1e7 },
      ]
    : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
        <div className="text-accent font-mono-tech text-sm animate-pulse">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-display text-[#0F172A]">Analytics</h1>
          <p className="text-sm text-[#94A3B8] mt-1 font-mono-tech">
            Statistical analysis and risk distributions across MPLADS works
          </p>
        </div>

        {/* Benford's Law */}
        <div className="rounded-xl border border-[#E2E8F0] bg-white p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider font-semibold">
                Benford&apos;s Law — First-Digit Distribution
              </div>
              <div className="text-xs text-[#94A3B8] mt-1">
                Comparing empirical sanction amount distribution against theoretical Benford curve
                {benford && <span className="ml-2 font-mono-tech">({benford.sample_size.toLocaleString()} amounts)</span>}
              </div>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={benfordChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="digit" tick={{ fontSize: 11, fill: '#64748B' }} />
              <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} unit="%" />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="empirical" name="Empirical" fill={BENFORD_EMPIRICAL} radius={[4, 4, 0, 0]} opacity={0.8} />
              <Line type="monotone" dataKey="theoretical" name="Theoretical Benford" stroke={BENFORD_THEORETICAL} strokeWidth={2} dot={{ fill: BENFORD_THEORETICAL, r: 4 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* State Risk Distribution */}
          <div className="rounded-xl border border-[#E2E8F0] bg-white p-5">
            <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider font-semibold mb-3">
              Risk by State (Top 20)
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={stateRiskData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis type="number" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 9, fill: '#64748B', fontFamily: 'JetBrains Mono' }} width={120} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Bar dataKey="CRITICAL" stackId="a" fill={RISK_COLORS[0]} />
                <Bar dataKey="HIGH" stackId="a" fill={RISK_COLORS[1]} />
                <Bar dataKey="MEDIUM" stackId="a" fill={RISK_COLORS[2]} />
                <Bar dataKey="LOW" stackId="a" fill={RISK_COLORS[3]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Budget Flow */}
          <div className="rounded-xl border border-[#E2E8F0] bg-white p-5">
            <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider font-semibold mb-3">
              Budget Flow (Crores)
            </div>
            {sankey && (
              <>
                <div className="grid grid-cols-3 gap-3 mb-4">
                  {[
                    { label: 'Sanctioned', value: sankey.amount_flow.sanctioned, color: '#1E3A8A' },
                    { label: 'Disbursed', value: sankey.amount_flow.disbursed, color: '#16A34A' },
                    { label: 'Unspent', value: sankey.amount_flow.unspent, color: '#D97706' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="p-3 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0] text-center">
                      <div className="text-[10px] font-mono-tech text-[#94A3B8] uppercase">{label}</div>
                      <div className="text-lg font-bold font-mono-tech mt-1" style={{ color }}>
                        {(value / 1e7).toFixed(1)} Cr
                      </div>
                    </div>
                  ))}
                </div>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={budgetFlowData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis dataKey="stage" tick={{ fontSize: 11, fill: '#64748B' }} />
                    <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="amount" name="Amount (Cr)" radius={[4, 4, 0, 0]}>
                      {budgetFlowData.map((_, i) => (
                        <Cell key={i} fill={[RISK_COLORS[2], RISK_COLORS[3], RISK_COLORS[1]][i]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </>
            )}
            {sankey && (
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0]">
                  <div className="text-[10px] font-mono-tech text-[#94A3B8]">Works Flow</div>
                  <div className="flex items-center gap-2 mt-1 text-xs font-mono-tech text-[#475569]">
                    <span>{sankey.works_flow.recommended} recommended</span>
                    <span>→</span>
                    <span>{sankey.works_flow.sanctioned} sanctioned</span>
                    <span>→</span>
                    <span>{sankey.works_flow.completed} completed</span>
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0]">
                  <div className="text-[10px] font-mono-tech text-[#94A3B8]">Utilization</div>
                  <div className="text-sm font-bold text-[#334155] mt-1">
                    {sankey.amount_flow.sanctioned > 0
                      ? `${((sankey.amount_flow.disbursed / sankey.amount_flow.sanctioned) * 100).toFixed(1)}%`
                      : '—'}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Category Risk Distribution */}
        <div className="rounded-xl border border-[#E2E8F0] bg-white p-5">
          <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider font-semibold mb-3">
            Risk by Work Category (Top 15)
          </div>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={categoryRiskData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis type="number" tick={{ fontSize: 10, fill: '#94A3B8' }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 9, fill: '#64748B', fontFamily: 'JetBrains Mono' }} width={200} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Bar dataKey="CRITICAL" stackId="a" fill={RISK_COLORS[0]} />
              <Bar dataKey="HIGH" stackId="a" fill={RISK_COLORS[1]} />
              <Bar dataKey="MEDIUM" stackId="a" fill={RISK_COLORS[2]} />
              <Bar dataKey="LOW" stackId="a" fill={RISK_COLORS[3]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
