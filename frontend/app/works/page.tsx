'use client';

import { useEffect, useState, useCallback } from 'react';
import { fetchWorks } from '@/lib/api';
import { Work, PaginatedResponse } from '@/types';
import WorkForensicDrawer from '@/components/WorkForensicDrawer';
import { SortIndicator } from '@/components/SortableTable';
import { useAuth, ROLE_LABELS } from '@/lib/auth';

export default function WorksPage() {
  const { user } = useAuth();
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
    <div className="max-w-[1720px] mx-auto px-3 sm:px-5 lg:px-8 py-4 sm:py-6">
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <div>
          <h1 className="text-base sm:text-lg font-serif-luxury font-bold text-[#0F172A]">Works Registry</h1>
          <div className="text-[10px] sm:text-xs font-mono-tech text-[#64748B] mt-0.5">
            {total.toLocaleString()} total works — {window.innerWidth < 1024 ? 'tap a card' : 'click a row'} to inspect
          </div>
        </div>
      </div>

      {/* Role Scope Banner */}
      {user && user.role !== 'ministry_admin' && (
        <div className="gov-panel px-3 sm:px-4 py-2 sm:py-2.5 mb-3 sm:mb-4 flex items-center gap-2">
          <svg className="w-3.5 h-3.5 text-accent shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-[10px] font-mono-tech text-[#64748B]">
            Filtered for <span className="font-bold text-accent">{ROLE_LABELS[user.role]}</span>
            {user.state && <span> — {user.constituency ? `${user.constituency}, ${user.state}` : user.district ? `${user.district}, ${user.state}` : user.state}</span>}
          </span>
        </div>
      )}

      {/* Filters */}
      <div className="gov-panel rounded-xl p-3 sm:p-4 mb-4 sm:mb-6">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search work ID, description, constituency..."
            className="flex-1 min-w-0 bg-[#F1F5F9] border border-[#E2E8F0] rounded-lg px-3 py-2 text-xs text-[#334155] placeholder-[#94A3B8] focus:outline-none focus:border-accent/50 font-sans transition"
          />
          <div className="flex gap-2">
            <select
              value={parliamentFilter}
              onChange={(e) => { setParliamentFilter(e.target.value); setPage(1); }}
              className="flex-1 sm:flex-none bg-[#F1F5F9] border border-[#E2E8F0] rounded-lg px-3 py-2 text-xs text-[#334155] font-sans focus:outline-none focus:border-accent/50"
            >
              <option value="">All Parliament</option>
              <option value="lok_sabha">Lok Sabha</option>
              <option value="rajya_sabha">Rajya Sabha</option>
            </select>
            <select
              value={riskFilter}
              onChange={(e) => { setRiskFilter(e.target.value); setPage(1); }}
              className="flex-1 sm:flex-none bg-[#F1F5F9] border border-[#E2E8F0] rounded-lg px-3 py-2 text-xs text-[#334155] font-sans focus:outline-none focus:border-accent/50"
            >
              <option value="">All Risk Levels</option>
              <option value="HIGH">High Risk</option>
              <option value="MEDIUM">Medium Risk</option>
              <option value="LOW">Low Risk</option>
            </select>
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-accent text-white font-bold text-xs transition sm:w-auto"
          >
            Search
          </button>
        </form>
      </div>

      {/* Desktop Table View (lg and above) */}
      <div className="hidden lg:block gov-panel rounded-xl overflow-hidden">
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

      {/* Mobile Card View (below lg) */}
      <div className="lg:hidden space-y-3">
        {loading ? (
          <div className="gov-panel rounded-xl p-8 text-center text-[#64748B] font-mono-tech text-xs animate-pulse">
            Loading works...
          </div>
        ) : rawData.length === 0 ? (
          <div className="gov-panel rounded-xl p-8 text-center text-[#64748B] font-mono-tech text-xs">
            No works found
          </div>
        ) : (
          <>
            {rawData.map((work: any, idx: number) => (
              <button
                key={work.work_id}
                onClick={() => handleRowClick(work.work_id)}
                className="w-full text-left gov-panel rounded-xl p-3 sm:p-4 hover:bg-[#F0F7FF] transition border border-transparent hover:border-accent/20"
              >
                {/* Top row: Work ID + Risk + Priority */}
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono-tech text-accent/80 truncate mr-2">
                    {work.work_id}
                  </span>
                  <div className="flex items-center gap-2 shrink-0">
                    {work.composite_risk !== null && work.composite_risk !== undefined && (
                      <span className={`text-sm font-mono-tech font-bold ${getRiskColor(work.composite_risk)}`}>
                        {work.composite_risk.toFixed(1)}
                      </span>
                    )}
                    <span className={`text-[9px] font-mono-tech px-1.5 py-0.5 rounded border ${getPriorityBadge(work.inspection_priority)}`}>
                      {work.inspection_priority || 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Description */}
                <div className="text-xs text-[#334155] line-clamp-2 mb-2">
                  {work.work_description || '-'}
                </div>

                {/* Info row */}
                <div className="flex items-center gap-1.5 text-[10px] text-[#94A3B8] font-mono-tech flex-wrap">
                  <span>{work.state || '-'}</span>
                  <span>·</span>
                  <span>{work.constituency || '-'}</span>
                  {work.sanction_amount && (
                    <>
                      <span>·</span>
                      <span className="text-[#475569]">₹{work.sanction_amount.toLocaleString('en-IN')}</span>
                    </>
                  )}
                </div>

                {/* Status */}
                {work.work_status && (
                  <div className="mt-2">
                    <span className={`text-[9px] font-mono-tech px-1.5 py-0.5 rounded border ${
                      work.work_status === 'Work Completed'
                        ? 'bg-emerald-50/60 border-emerald-400 text-emerald-600'
                        : 'bg-[#F1F5F9] border-[#E2E8F0] text-[#64748B]'
                    }`}>
                      {work.work_status}
                    </span>
                  </div>
                )}
              </button>
            ))}

            {/* Mobile Pagination */}
            {pages > 1 && (
              <div className="gov-panel rounded-xl p-3 flex items-center justify-between">
                <div className="text-[10px] font-mono-tech text-[#64748B]">
                  {page}/{pages}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1.5 rounded bg-[#F1F5F9] border border-[#E2E8F0] text-xs text-[#475569] disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Prev
                  </button>
                  <button
                    onClick={() => setPage(p => Math.min(pages, p + 1))}
                    disabled={page === pages}
                    className="px-3 py-1.5 rounded bg-[#F1F5F9] border border-[#E2E8F0] text-xs text-[#475569] disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <WorkForensicDrawer workId={selectedWorkId} onClose={() => setSelectedWorkId(null)} sourcePage="Works Registry" />
    </div>
  );
}
