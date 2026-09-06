'use client';

import { useEffect, useState, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import WorkForensicDrawer from '@/components/WorkForensicDrawer';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const SORT_OPTIONS = [
  { value: 'total_works', label: 'Most Expenditure Records' },
  { value: 'distinct_works', label: 'Most Distinct Works' },
  { value: 'total_expenditure', label: 'Highest Expenditure' },
  { value: 'avg_risk', label: 'Highest Risk' },
  { value: 'high_risk_count', label: 'Most High-Risk Works' },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-[#E2E8F0] rounded-lg px-3 py-2 shadow-xl">
      <div className="text-[10px] font-mono-tech text-[#94A3B8] mb-1">{label}</div>
      {payload.map((p: any, i: number) => (
        <div key={i} className="text-xs font-mono-tech" style={{ color: p.color }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString('en-IN') : p.value}
        </div>
      ))}
    </div>
  );
};

interface Vendor {
  vendor_name: string;
  total_works: number;
  distinct_works: number;
  total_expenditure: number;
  avg_risk: number | null;
  high_risk_count: number;
}

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState('total_works');
  const [loading, setLoading] = useState(true);
  const [selectedVendor, setSelectedVendor] = useState<string | null>(null);
  const [vendorDetail, setVendorDetail] = useState<any>(null);
  const [selectedWorkId, setSelectedWorkId] = useState<string | null>(null);

  const PAGE_SIZE = 15;

  async function load() {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/vendors?page=${page}&size=${PAGE_SIZE}&sort_by=${sortBy}`);
      const data = await res.json();
      setVendors(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function loadDetail(vendorName: string) {
    setSelectedVendor(vendorName);
    try {
      const res = await fetch(`${API_BASE_URL}/vendors/${encodeURIComponent(vendorName)}`);
      const data = await res.json();
      setVendorDetail(data);
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => { load(); }, [page, sortBy]);

  const top10 = vendors.slice(0, 10).map(v => ({
    name: v.vendor_name.length > 20 ? v.vendor_name.slice(0, 20) + '...' : v.vendor_name,
    works: v.total_works,
    expenditure: v.total_expenditure / 100000,
    risk: v.avg_risk || 0,
  }));

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-display text-[#0F172A]">Vendor Analytics</h1>
            <p className="text-sm text-[#94A3B8] mt-1 font-mono-tech">
              {total} vendors tracked across all works
            </p>
          </div>
          <select
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
            className="bg-white border border-[#E2E8F0] rounded-lg px-3 py-2 text-xs text-[#475569] font-mono-tech"
          >
            {SORT_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>

        {/* Charts */}
        {top10.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
            <div className="rounded-xl border border-[#E2E8F0] bg-white p-5">
              <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">
                Top 10 Vendors by Works
              </div>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={top10} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis type="number" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 9, fill: '#64748B', fontFamily: 'JetBrains Mono' }} width={120} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="works" fill="#1E3A8A" radius={[0, 4, 4, 0]} name="Works" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="rounded-xl border border-[#E2E8F0] bg-white p-5">
              <div className="text-[10px] font-mono-tech text-accent uppercase tracking-wider mb-3">
                Top 10 Vendors by Expenditure (Lakhs)
              </div>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={top10} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis type="number" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 9, fill: '#64748B', fontFamily: 'JetBrains Mono' }} width={120} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="expenditure" fill="#2563EB" radius={[0, 4, 4, 0]} name="Expenditure (L)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Vendor Table */}
        <div className="rounded-xl border border-[#E2E8F0] bg-white overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-[#94A3B8] font-mono-tech text-sm animate-pulse">
              Loading vendors...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[#E2E8F0]">
                    <th className="text-left px-4 py-3 text-[#94A3B8] font-mono-tech uppercase tracking-wider text-[10px]" title="Name of the vendor/agency/contractor">Vendor Name</th>
                    <th className="text-left px-4 py-3 text-[#94A3B8] font-mono-tech uppercase tracking-wider text-[10px]" title="Number of distinct works this vendor is associated with">Distinct Works</th>
                    <th className="text-left px-4 py-3 text-[#94A3B8] font-mono-tech uppercase tracking-wider text-[10px]" title="Total expenditure records (may exceed distinct works if multiple payments per work)">Expend. Records</th>
                    <th className="text-left px-4 py-3 text-[#94A3B8] font-mono-tech uppercase tracking-wider text-[10px]" title="Total expenditure amount in INR across all associated works">Total Expenditure</th>
                    <th className="text-left px-4 py-3 text-[#94A3B8] font-mono-tech uppercase tracking-wider text-[10px]" title="Average composite risk score across this vendor's works (0–100)">Avg Risk</th>
                    <th className="text-left px-4 py-3 text-[#94A3B8] font-mono-tech uppercase tracking-wider text-[10px]" title="Number of distinct works with composite risk > 65 (HIGH priority)">High Risk</th>
                    <th className="text-left px-4 py-3 text-[#94A3B8] font-mono-tech uppercase tracking-wider text-[10px]"></th>
                  </tr>
                </thead>
                <tbody>
                  {vendors.map(v => (
                    <tr key={v.vendor_name} className="border-b border-[#F1F5F9] hover:bg-[#F8FAFC] transition">
                      <td className="px-4 py-3 text-[#334155] max-w-[300px] truncate">{v.vendor_name}</td>
                      <td className="px-4 py-3 font-mono-tech text-[#475569]">{v.distinct_works || 0}</td>
                      <td className="px-4 py-3 font-mono-tech text-[#475569]">{v.total_works}</td>
                      <td className="px-4 py-3 font-mono-tech text-[#475569]">₹{v.total_expenditure.toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3">
                        <span className={`font-mono-tech font-bold ${
                          v.avg_risk !== null && v.avg_risk >= 65 ? 'text-red-600' :
                          v.avg_risk !== null && v.avg_risk >= 40 ? 'text-amber-600' : 'text-emerald-600'
                        }`}>
                          {v.avg_risk !== null ? v.avg_risk.toFixed(1) : '—'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {v.high_risk_count > 0 ? (
                          <span className="px-2 py-0.5 rounded bg-red-50 text-red-600 font-mono-tech">
                            {v.high_risk_count}
                          </span>
                        ) : (
                          <span className="text-[#CBD5E1]">0</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => loadDetail(v.vendor_name)}
                          className="px-2 py-1 rounded bg-accent/10 text-accent text-[10px] font-mono-tech hover:bg-accent/20 transition"
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        {Math.ceil(total / PAGE_SIZE) > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6">
            <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}
              className="px-3 py-1.5 rounded bg-[#F1F5F9] text-[#64748B] text-xs font-mono-tech hover:bg-[#E2E8F0] transition disabled:opacity-30">
              Prev
            </button>
            <span className="text-xs font-mono-tech text-[#94A3B8]">Page {page} of {Math.ceil(total / PAGE_SIZE)}</span>
            <button onClick={() => setPage(Math.min(Math.ceil(total / PAGE_SIZE), page + 1))} disabled={page === Math.ceil(total / PAGE_SIZE)}
              className="px-3 py-1.5 rounded bg-[#F1F5F9] text-[#64748B] text-xs font-mono-tech hover:bg-[#E2E8F0] transition disabled:opacity-30">
              Next
            </button>
          </div>
        )}

        {/* Vendor Detail Modal */}
        {selectedVendor && vendorDetail && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
            <div className="w-full max-w-2xl rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-2xl max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-sm font-semibold text-[#0F172A]">{vendorDetail.vendor_name}</div>
                  <div className="text-[10px] font-mono-tech text-[#94A3B8] mt-0.5">
                    {vendorDetail.total_works} works · ₹{vendorDetail.total_expenditure.toLocaleString('en-IN')} total
                  </div>
                </div>
                <button onClick={() => { setSelectedVendor(null); setVendorDetail(null); }}
                  className="text-[#94A3B8] hover:text-[#0F172A] text-lg">×</button>
              </div>
              {vendorDetail.risk_distribution && Object.keys(vendorDetail.risk_distribution).length > 0 && (
                <div className="flex gap-3 mb-4">
                  {Object.entries(vendorDetail.risk_distribution).map(([level, count]) => (
                    <div key={level} className="px-3 py-2 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0]">
                      <div className="text-[10px] font-mono-tech text-[#94A3B8] uppercase">{level}</div>
                      <div className="text-lg font-bold text-[#334155]">{count as number}</div>
                    </div>
                  ))}
                </div>
              )}
              <div className="space-y-2">
                {vendorDetail.works?.map((w: any) => (
                  <button key={w.work_id}
                    onClick={() => { setSelectedWorkId(w.work_id); setSelectedVendor(null); setVendorDetail(null); }}
                    className="w-full flex items-center justify-between p-3 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0] hover:border-accent/30 transition text-left"
                  >
                    <div className="min-w-0">
                      <div className="text-xs text-[#334155] truncate">{w.work_description || w.work_id}</div>
                      <div className="text-[10px] font-mono-tech text-[#94A3B8]">{w.state} · {w.constituency}</div>
                    </div>
                    <span className={`text-xs font-mono-tech font-bold ml-3 ${
                      w.composite_risk !== null && w.composite_risk >= 65 ? 'text-red-600' :
                      w.composite_risk !== null && w.composite_risk >= 40 ? 'text-amber-600' : 'text-emerald-600'
                    }`}>
                      {w.composite_risk !== null ? w.composite_risk.toFixed(1) : '—'}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        <WorkForensicDrawer workId={selectedWorkId} onClose={() => setSelectedWorkId(null)} sourcePage="Vendors" />
      </div>
    </div>
  );
}
