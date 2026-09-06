'use client';

import { useEffect, useState, useCallback } from 'react';
import { fetchWorks } from '@/lib/api';
import { Work, PaginatedResponse } from '@/types';
import WorkForensicDrawer from '@/components/WorkForensicDrawer';
import { SortIndicator } from '@/components/SortableTable';

export default function WorksPage() {
  const [rawData, setRawData] = useState<Work[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState('');
  const [parliamentFilter, setParliamentFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [selectedWorkId, setSelectedWorkId] = useState<string | null>(null);
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);

  useEffect(() => {
    async function loadWorks() {
      setLoading(true);
      try {
        const result = await fetchWorks({
          page,
          size: 20,
          state: stateFilter || undefined,
          parliament: parliamentFilter || undefined,
          risk_level: riskFilter || undefined,
          search: search || undefined,
          sort_by: sortConfig?.key || undefined,
          sort_dir: sortConfig?.direction || undefined,
        });
        setRawData(result.items);
        setTotal(result.total);
        setPages(result.pages);
      } catch (err) {
        console.error('Failed to load works:', err);
      } finally {
        setLoading(false);
      }
    }
    loadWorks();
  }, [page, stateFilter, parliamentFilter, riskFilter, search, sortConfig]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  const handleSort = (key: string) => {
    setSortConfig(prev => {
      if (prev?.key === key) {
        if (prev.direction === 'asc') return { key, direction: 'desc' };
        return null;
      }
      return { key, direction: 'asc' };
    });
    setPage(1);
  };

  const getPriorityBadge = (priority: string | null) => {
    switch (priority) {
      case 'HIGH': return 'bg-red-50/60 border-red-400 text-red-600';
      case 'MEDIUM': return 'bg-amber-50/60 border-amber-400 text-amber-600';
      case 'LOW': return 'bg-emerald-50/60 border-emerald-400 text-emerald-600';
      default: return 'bg-[#F1F5F9] border-[#E2E8F0] text-[#94A3B8]';
    }
  };

  const getRiskColor = (risk: number | null) => {
    if (risk === null) return 'text-[#94A3B8]';
    if (risk >= 65) return 'text-red-600';
    if (risk >= 40) return 'text-amber-600';
    return 'text-emerald-600';
  };

  const handleRowClick = useCallback((workId: string) => {
    setSelectedWorkId(workId);
  }, []);

  return (
    <div className="max-w-[1720px] mx-auto px-5 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-lg font-serif-luxury font-bold text-[#0F172A]">Works Registry</h1>
          <div className="text-xs font-mono-tech text-[#64748B] mt-0.5">
            {total.toLocaleString()} total works — click a row to inspect
          </div>
        </div>
      </div>

      <div className="gov-panel rounded-xl p-4 mb-6">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-3">
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search work ID, description, constituency..."
            className="flex-1 min-w-[250px] bg-[#F1F5F9] border border-[#E2E8F0] rounded-lg px-3 py-2 text-xs text-[#334155] placeholder-[#94A3B8] focus:outline-none focus:border-accent/50 font-sans transition"
          />
          <select
            value={parliamentFilter}
            onChange={(e) => { setParliamentFilter(e.target.value); setPage(1); }}
            className="bg-[#F1F5F9] border border-[#E2E8F0] rounded-lg px-3 py-2 text-xs text-[#334155] font-sans focus:outline-none focus:border-accent/50"
          >
            <option value="">All Parliament</option>
            <option value="lok_sabha">Lok Sabha</option>
            <option value="rajya_sabha">Rajya Sabha</option>
          </select>
          <select
            value={riskFilter}
            onChange={(e) => { setRiskFilter(e.target.value); setPage(1); }}
            className="bg-[#F1F5F9] border border-[#E2E8F0] rounded-lg px-3 py-2 text-xs text-[#334155] font-sans focus:outline-none focus:border-accent/50"
          >
            <option value="">All Risk Levels</option>
            <option value="HIGH">High Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="LOW">Low Risk</option>
          </select>
          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-accent text-white font-bold text-xs transition"
          >
            Search
          </button>
        </form>
      </div>

      <div className="gov-panel rounded-xl overflow-hidden">
        <div className="overflow-x-auto scrollbar-luxury">
          <table className="w-full text-left border-collapse">
            <thead className="bg-[#F1F5F9] text-[10.5px] font-mono-tech text-[#64748B] border-b border-[#E2E8F0] select-none whitespace-nowrap">
              <tr>
                <th className="py-2.5 px-3" title="Row number">#</th>
                <th className="py-2.5 px-3 cursor-pointer hover:text-accent" title="Unique MPLADS work identifier — click to sort" onClick={() => handleSort('work_id')}>
                  <span className="flex items-center">Work ID <SortIndicator config={sortConfig} columnKey="work_id" /></span>
                </th>
                <th className="py-2.5 px-3" title="Brief description of the sanctioned work">Description</th>
                <th className="py-2.5 px-3 cursor-pointer hover:text-accent" title="Indian state where the work is located — click to sort" onClick={() => handleSort('state')}>
                  <span className="flex items-center">State <SortIndicator config={sortConfig} columnKey="state" /></span>
                </th>
                <th className="py-2.5 px-3" title="Sanctioned amount in INR from MPLADS">Sanctioned</th>
                <th className="py-2.5 px-3 cursor-pointer hover:text-accent" title="Composite risk score (0–100). Higher = more risk indicators triggered — click to sort" onClick={() => handleSort('risk')}>
                  <span className="flex items-center">Risk <SortIndicator config={sortConfig} columnKey="risk" /></span>
                </th>
                <th className="py-2.5 px-3 cursor-pointer hover:text-accent" title="Inspection priority derived from composite risk: HIGH ≥ 65, MEDIUM ≥ 40, LOW < 40 — click to sort" onClick={() => handleSort('priority')}>
                  <span className="flex items-center">Priority <SortIndicator config={sortConfig} columnKey="priority" /></span>
                </th>
                <th className="py-2.5 px-3" title="Current work status from sanction record">Status</th>
              </tr>
            </thead>
            <tbody className="text-xs">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-[#64748B]">Loading...</td>
                </tr>
              ) : rawData.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-[#64748B]">No works found</td>
                </tr>
              ) : (
                rawData.map((work: any, idx: number) => (
                  <tr
                    key={work.work_id}
                    onClick={() => handleRowClick(work.work_id)}
                    className="border-b border-[#E2E8F0]/70 hover:bg-[#F0F7FF] cursor-pointer transition"
                  >
                    <td className="py-2.5 px-3 font-mono-tech text-[#64748B]">
                      {(page - 1) * 20 + idx + 1}
                    </td>
                    <td className="py-2.5 px-3 font-mono-tech text-accent/80">
                      {work.work_id}
                    </td>
                    <td className="py-2.5 px-3 max-w-[300px] truncate text-[#334155]">
                      {work.work_description || '-'}
                    </td>
                    <td className="py-2.5 px-3 text-[#475569]">
                      {work.state || '-'}
                    </td>
                    <td className="py-2.5 px-3 font-mono-tech text-[#334155]">
                      {work.sanction_amount ? `₹${work.sanction_amount.toLocaleString('en-IN')}` : '-'}
                    </td>
                    <td className="py-2.5 px-3 font-mono-tech font-bold">
                      <span className={getRiskColor(work.composite_risk)}>
                        {work.composite_risk !== null && work.composite_risk !== undefined ? work.composite_risk.toFixed(1) : '—'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`text-[9.5px] font-mono-tech px-2 py-0.5 rounded border ${getPriorityBadge(work.inspection_priority)}`}>
                        {work.inspection_priority || 'N/A'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`text-[9.5px] font-mono-tech px-2 py-0.5 rounded border ${
                        work.work_status === 'Work Completed'
                          ? 'bg-emerald-50/60 border-emerald-400 text-emerald-600'
                          : 'bg-[#F1F5F9] border-[#E2E8F0] text-[#64748B]'
                      }`}>
                        {work.work_status || 'Unknown'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {pages > 1 && (
          <div className="px-4 py-3 bg-[#F1F5F9] border-t border-[#E2E8F0] flex items-center justify-between">
            <div className="text-[10.5px] font-mono-tech text-[#64748B]">
              Showing {((page - 1) * 20) + 1} to {Math.min(page * 20, total)} of {total.toLocaleString()}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 rounded bg-[#F1F5F9] border border-[#E2E8F0] text-xs text-[#475569] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#F8FAFC]"
              >
                Previous
              </button>
              <span className="text-xs font-mono-tech text-[#64748B]">
                Page {page} of {pages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(pages, p + 1))}
                disabled={page === pages}
                className="px-3 py-1 rounded bg-[#F1F5F9] border border-[#E2E8F0] text-xs text-[#475569] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#F8FAFC]"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      <WorkForensicDrawer workId={selectedWorkId} onClose={() => setSelectedWorkId(null)} sourcePage="Works Registry" />
    </div>
  );
}
