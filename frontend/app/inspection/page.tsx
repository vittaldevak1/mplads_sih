'use client';

import { useEffect, useState, useCallback } from 'react';
import { fetchInspectionQueue, assignInspection, startReview, dismissInspection, completeInspection, fetchInspectionHistory } from '@/lib/api';
import { InspectionQueueItem, InspectionHistoryItem } from '@/types';
import WorkForensicDrawer from '@/components/WorkForensicDrawer';
import { useAuth, ROLE_LABELS } from '@/lib/auth';

const PRIORITY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CRITICAL: { bg: '#FEF2F2', text: '#991B1B', border: '#F87171' },
  HIGH: { bg: '#FEF2F2', text: '#991B1B', border: '#F87171' },
  MEDIUM: { bg: '#FFFBEB', text: '#92400E', border: '#FBBF24' },
  LOW: { bg: '#F0FDF4', text: '#166534', border: '#86EFAC' },
};

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  pending: { bg: '#F1F5F9', text: '#64748B', label: 'Pending' },
  assigned: { bg: '#EFF6FF', text: '#2563EB', label: 'Assigned' },
  in_progress: { bg: '#FFFBEB', text: '#92400E', label: 'Under Review' },
  request_documents: { bg: '#F5F3FF', text: '#7C3AED', label: 'Docs Requested' },
  field_inspection: { bg: '#FFF7ED', text: '#C2410C', label: 'Field Inspection' },
  completed: { bg: '#F0FDF4', text: '#16A34A', label: 'Verified' },
  dismissed: { bg: '#F8FAFC', text: '#94A3B8', label: 'Dismissed' },
};

export default function InspectionPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<InspectionQueueItem[]>([]);
  const [counts, setCounts] = useState({ critical: 0, high: 0, medium: 0, low: 0, unanalyzed: 0 });
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);
  const [historyModal, setHistoryModal] = useState<string | null>(null);
  const [history, setHistory] = useState<InspectionHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [notesModal, setNotesModal] = useState<{ workId: string; action: string } | null>(null);
  const [notesText, setNotesText] = useState('');
  const [selectedWorkId, setSelectedWorkId] = useState<string | null>(null);
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);

  async function loadQueue(priority?: string) {
    setLoading(true);
    try {
      const data = await fetchInspectionQueue({ priority: priority || undefined, limit: 200 });
      setItems(data.items);
      setCounts(data.counts);
      setTotal(data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadQueue(filter ?? undefined); }, [filter]);

  const handleAction = useCallback(async (workId: string, action: string, notes?: string) => {
    setActionLoading(`${workId}-${action}`);
    try {
      switch (action) {
        case 'assign': await assignInspection(workId); break;
        case 'review': await startReview(workId); break;
        case 'dismiss': await dismissInspection(workId, notes || 'No issues found'); break;
        case 'complete': await completeInspection(workId, notes || 'Inspection verified'); break;
      }
      await loadQueue(filter ?? undefined);
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(null);
      setNotesModal(null);
      setNotesText('');
    }
  }, [filter]);

  const openHistory = useCallback(async (workId: string) => {
    setHistoryModal(workId);
    setHistoryLoading(true);
    try {
      const data = await fetchInspectionHistory(workId);
      setHistory(data.history || []);
    } catch (err) {
      console.error(err);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const priorityCards = [
    { key: 'HIGH', label: 'High Risk', count: counts.high, color: PRIORITY_COLORS.HIGH },
    { key: 'MEDIUM', label: 'Medium Risk', count: counts.medium, color: PRIORITY_COLORS.MEDIUM },
    { key: 'LOW', label: 'Low Risk', count: counts.low, color: PRIORITY_COLORS.LOW },
  ];

  const handleSort = (key: string) => {
    setSortConfig(prev => {
      if (prev?.key === key) {
        if (prev.direction === 'asc') return { key, direction: 'desc' };
        return null;
      }
      return { key, direction: 'asc' };
    });
  };

  const PRIORITY_SORT: Record<string, number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  const STATUS_SORT: Record<string, number> = { pending: 0, assigned: 1, in_progress: 2, request_documents: 3, field_inspection: 4, completed: 5, dismissed: 6 };

  const sortedItems = [...items].sort((a, b) => {
    if (!sortConfig) return 0;
    const { key, direction } = sortConfig;
    let aVal: any, bVal: any;
    switch (key) {
      case 'work_id': aVal = a.work_id; bVal = b.work_id; break;
      case 'state': aVal = a.state || ''; bVal = b.state || ''; break;
      case 'constituency': aVal = a.constituency || ''; bVal = b.constituency || ''; break;
      case 'risk': aVal = a.composite_risk ?? -1; bVal = b.composite_risk ?? -1; break;
      case 'priority': aVal = PRIORITY_SORT[a.inspection_priority || ''] ?? 3; bVal = PRIORITY_SORT[b.inspection_priority || ''] ?? 3; break;
      case 'signals': aVal = a.signal_count; bVal = b.signal_count; break;
      case 'status': aVal = STATUS_SORT[a.task_status || ''] ?? 99; bVal = STATUS_SORT[b.task_status || ''] ?? 99; break;
      default: return 0;
    }
    if (typeof aVal === 'number' && typeof bVal === 'number') return direction === 'asc' ? aVal - bVal : bVal - aVal;
    const sA = String(aVal).toLowerCase(), sB = String(bVal).toLowerCase();
    return direction === 'asc' ? sA.localeCompare(sB) : sB.localeCompare(sA);
  });

  const SortTh = ({ label, sortKey, tooltip }: { label: string; sortKey: string; tooltip: string }) => (
    <th className="text-left px-4 py-3 text-[#94A3B8] font-mono-tech uppercase tracking-wider text-[10px] cursor-pointer hover:text-accent select-none"
      title={tooltip} onClick={() => handleSort(sortKey)}>
      <span className="flex items-center">
        {label}
        {sortConfig?.key === sortKey ? (
          <span className="text-accent ml-1 font-bold text-[9px]">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
        ) : (
          <span className="text-[#CBD5E1] ml-1 text-[9px]">↕</span>
        )}
      </span>
    </th>
  );

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] p-3 sm:p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-4 sm:mb-6">
          <h1 className="text-lg sm:text-2xl font-display text-[#0F172A]">Inspection Workflow</h1>
          <p className="text-xs sm:text-sm text-[#94A3B8] mt-1 font-mono-tech">
            Government audit case management — {total} works in queue
          </p>
        </div>

        {/* Role Scope Banner */}
        {user && user.role !== 'ministry_admin' && (
          <div className="gov-panel px-3 sm:px-4 py-2 sm:py-2.5 mb-3 sm:mb-4 flex items-center gap-2">
            <svg className="w-3.5 h-3.5 text-accent shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-[10px] font-mono-tech text-[#64748B]">
              Viewing as <span className="font-bold text-accent">{ROLE_LABELS[user.role]}</span>
              {user.state && <span> — {user.constituency ? `${user.constituency}, ${user.state}` : user.district ? `${user.district}, ${user.state}` : user.state}</span>}
              {user.role === 'inspection_officer' && <span className="ml-1 text-[#94A3B8]">(filtered to assigned works)</span>}
            </span>
          </div>
        )}

        {/* Priority Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3 mb-4 sm:mb-6">
          {priorityCards.map(({ key, label, count, color }) => (
            <button
              key={key}
              onClick={() => setFilter(filter === key ? null : key)}
              className={`rounded-xl border p-3 sm:p-4 text-left transition ${filter === key ? 'ring-2 ring-accent' : ''}`}
              style={{ background: color.bg, borderColor: color.border }}
            >
              <div className="text-[9px] sm:text-[10px] font-mono-tech uppercase tracking-wider" style={{ color: color.text }}>{label}</div>
              <div className="text-xl sm:text-2xl font-display mt-1" style={{ color: color.text }}>{count}</div>
            </button>
          ))}
          <div className="rounded-xl border border-[#E2E8F0] bg-white p-3 sm:p-4">
            <div className="text-[9px] sm:text-[10px] font-mono-tech text-[#94A3B8] uppercase tracking-wider">Unanalyzed</div>
            <div className="text-xl sm:text-2xl font-display text-[#64748B] mt-1">{counts.unanalyzed}</div>
          </div>
        </div>

        {/* Desktop Table View (lg and above) */}
        <div className="hidden lg:block rounded-xl border border-[#E2E8F0] bg-white overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-[#94A3B8] font-mono-tech text-sm animate-pulse">
              Loading inspection queue...
            </div>
          ) : items.length === 0 ? (
            <div className="p-12 text-center text-[#94A3B8] font-mono-tech text-sm">
              No works match the current filter.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[#E2E8F0] bg-[#F8FAFC]">
                    <SortTh label="Work ID" sortKey="work_id" tooltip="Unique MPLADS work identifier" />
                    <th className="text-left px-4 py-3 text-[#94A3B8] font-mono-tech uppercase tracking-wider text-[10px]" title="Brief description of the sanctioned work">Description</th>
                    <SortTh label="State" sortKey="state" tooltip="Indian state where work is located" />
                    <SortTh label="Constituency" sortKey="constituency" tooltip="Lok Sabha/Rajya Sabha constituency" />
                    <th className="text-left px-4 py-3 text-[#94A3B8] font-mono-tech uppercase tracking-wider text-[10px]" title="Member of Parliament for this constituency">MP</th>
                    <SortTh label="Risk" sortKey="risk" tooltip="Composite risk score (0–100). Higher = more risk indicators triggered" />
                    <SortTh label="Priority" sortKey="priority" tooltip="Inspection priority: HIGH ≥ 65, MEDIUM ≥ 40, LOW < 40" />
                    <SortTh label="Signals" sortKey="signals" tooltip="Number of available risk signals with score ≥ 35" />
                    <SortTh label="Status" sortKey="status" tooltip="Current inspection workflow status" />
                    <th className="text-left px-4 py-3 text-[#94A3B8] font-mono-tech uppercase tracking-wider text-[10px]" title="Available inspection actions">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedItems.map((item) => {
                    const pColor = PRIORITY_COLORS[item.inspection_priority || ''] || PRIORITY_COLORS.LOW;
                    const sStyle = STATUS_STYLES[item.task_status] || STATUS_STYLES.pending;
                    const isLoading = actionLoading?.startsWith(item.work_id);
                    return (
                      <tr key={item.work_id} className="border-b border-[#E2E8F0] hover:bg-[#F8FAFC] transition">
                        <td className="px-4 py-3 font-mono-tech text-accent text-[11px] cursor-pointer hover:underline" onClick={() => setSelectedWorkId(item.work_id)}>{item.work_id.slice(0, 28)}</td>
                        <td className="px-4 py-3 text-[#475569] max-w-[180px] truncate">{item.work_description || '—'}</td>
                        <td className="px-4 py-3 text-[#64748B]">{item.state || '—'}</td>
                        <td className="px-4 py-3 text-[#64748B]">{item.constituency || '—'}</td>
                        <td className="px-4 py-3 text-[#64748B]">{item.mp_name || '—'}</td>
                        <td className="px-4 py-3 text-right font-mono-tech font-bold text-[#0F172A]">
                          {item.composite_risk != null ? item.composite_risk.toFixed(1) : '—'}
                        </td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono-tech"
                            style={{ background: pColor.bg, color: pColor.text, border: `1px solid ${pColor.border}` }}>
                            {item.inspection_priority || '—'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center font-mono-tech text-[#64748B]">{item.signal_count}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono-tech font-semibold"
                            style={{ background: sStyle.bg, color: sStyle.text }}>
                            {sStyle.label}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1 flex-wrap">
                            {item.task_status === 'pending' && (
                              <button onClick={() => handleAction(item.work_id, 'assign')} disabled={isLoading}
                                className="px-2 py-1 rounded bg-[#2563EB]/10 text-[#2563EB] text-[10px] font-mono-tech hover:bg-[#2563EB]/20 transition disabled:opacity-50">
                                Assign
                              </button>
                            )}
                            {(item.task_status === 'assigned' || item.task_status === 'request_documents') && (
                              <button onClick={() => handleAction(item.work_id, 'review')} disabled={isLoading}
                                className="px-2 py-1 rounded bg-accent/10 text-accent text-[10px] font-mono-tech hover:bg-accent/20 transition disabled:opacity-50">
                                Review
                              </button>
                            )}
                            {item.task_status === 'in_progress' && (
                              <>
                                <button onClick={() => setNotesModal({ workId: item.work_id, action: 'complete' })} disabled={isLoading}
                                  className="px-2 py-1 rounded bg-[#16A34A]/10 text-[#16A34A] text-[10px] font-mono-tech hover:bg-[#16A34A]/20 transition disabled:opacity-50">
                                  Verify
                                </button>
                                <button onClick={() => setNotesModal({ workId: item.work_id, action: 'dismiss' })} disabled={isLoading}
                                  className="px-2 py-1 rounded bg-[#94A3B8]/10 text-[#64748B] text-[10px] font-mono-tech hover:bg-[#94A3B8]/20 transition disabled:opacity-50">
                                  Dismiss
                                </button>
                              </>
                            )}
                            <button onClick={() => openHistory(item.work_id)}
                              className="px-2 py-1 rounded bg-[#F1F5F9] text-[#64748B] text-[10px] font-mono-tech hover:bg-[#E2E8F0] transition">
                              Log
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Mobile Card View (below lg) */}
        <div className="lg:hidden space-y-3">
          {loading ? (
            <div className="rounded-xl border border-[#E2E8F0] bg-white p-8 text-center text-[#94A3B8] font-mono-tech text-xs animate-pulse">
              Loading inspection queue...
            </div>
          ) : items.length === 0 ? (
            <div className="rounded-xl border border-[#E2E8F0] bg-white p-8 text-center text-[#94A3B8] font-mono-tech text-xs">
              No works match the current filter.
            </div>
          ) : (
            sortedItems.map((item) => {
              const pColor = PRIORITY_COLORS[item.inspection_priority || ''] || PRIORITY_COLORS.LOW;
              const sStyle = STATUS_STYLES[item.task_status] || STATUS_STYLES.pending;
              const isLoading = actionLoading?.startsWith(item.work_id);
              return (
                <div key={item.work_id} className="rounded-xl border border-[#E2E8F0] bg-white p-3 sm:p-4">
                  {/* Top: Work ID + Risk + Priority */}
                  <div className="flex items-center justify-between mb-2">
                    <button
                      onClick={() => setSelectedWorkId(item.work_id)}
                      className="text-[10px] sm:text-[11px] font-mono-tech text-accent hover:underline truncate mr-2"
                    >
                      {item.work_id}
                    </button>
                    <div className="flex items-center gap-2 shrink-0">
                      {item.composite_risk != null && (
                        <span className="text-sm font-mono-tech font-bold text-[#0F172A]">
                          {item.composite_risk.toFixed(1)}
                        </span>
                      )}
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase font-mono-tech"
                        style={{ background: pColor.bg, color: pColor.text, border: `1px solid ${pColor.border}` }}>
                        {item.inspection_priority || '—'}
                      </span>
                    </div>
                  </div>

                  {/* Description */}
                  <div className="text-xs text-[#475569] line-clamp-2 mb-2">
                    {item.work_description || '—'}
                  </div>

                  {/* Info row */}
                  <div className="flex items-center gap-1.5 text-[10px] text-[#94A3B8] font-mono-tech flex-wrap mb-2">
                    <span>{item.state || '—'}</span>
                    <span>·</span>
                    <span>{item.constituency || '—'}</span>
                    {item.mp_name && (
                      <>
                        <span>·</span>
                        <span className="text-[#475569]">MP: {item.mp_name}</span>
                      </>
                    )}
                    <span>·</span>
                    <span>{item.signal_count} signals</span>
                  </div>

                  {/* Status + Actions */}
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono-tech font-semibold"
                      style={{ background: sStyle.bg, color: sStyle.text }}>
                      {sStyle.label}
                    </span>
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {item.task_status === 'pending' && (
                        <button onClick={() => handleAction(item.work_id, 'assign')} disabled={isLoading}
                          className="px-2.5 py-1 rounded bg-[#2563EB]/10 text-[#2563EB] text-[10px] font-mono-tech hover:bg-[#2563EB]/20 transition disabled:opacity-50">
                          Assign
                        </button>
                      )}
                      {(item.task_status === 'assigned' || item.task_status === 'request_documents') && (
                        <button onClick={() => handleAction(item.work_id, 'review')} disabled={isLoading}
                          className="px-2.5 py-1 rounded bg-accent/10 text-accent text-[10px] font-mono-tech hover:bg-accent/20 transition disabled:opacity-50">
                          Review
                        </button>
                      )}
                      {item.task_status === 'in_progress' && (
                        <>
                          <button onClick={() => setNotesModal({ workId: item.work_id, action: 'complete' })} disabled={isLoading}
                            className="px-2.5 py-1 rounded bg-[#16A34A]/10 text-[#16A34A] text-[10px] font-mono-tech hover:bg-[#16A34A]/20 transition disabled:opacity-50">
                            Verify
                          </button>
                          <button onClick={() => setNotesModal({ workId: item.work_id, action: 'dismiss' })} disabled={isLoading}
                            className="px-2.5 py-1 rounded bg-[#94A3B8]/10 text-[#64748B] text-[10px] font-mono-tech hover:bg-[#94A3B8]/20 transition disabled:opacity-50">
                            Dismiss
                          </button>
                        </>
                      )}
                      <button onClick={() => openHistory(item.work_id)}
                        className="px-2.5 py-1 rounded bg-[#F1F5F9] text-[#64748B] text-[10px] font-mono-tech hover:bg-[#E2E8F0] transition">
                        Log
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Notes Modal */}
        {notesModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-xl border border-[#E2E8F0] bg-white p-4 sm:p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-4">
                <div className="text-sm font-semibold text-[#0F172A]">
                  {notesModal.action === 'complete' ? 'Verification Notes' : 'Dismissal Reason'}
                </div>
                <button onClick={() => setNotesModal(null)} className="text-[#94A3B8] hover:text-[#0F172A] text-lg">×</button>
              </div>
              <div className="text-[10px] font-mono-tech text-[#94A3B8] mb-3 break-all">{notesModal.workId}</div>
              <textarea
                value={notesText}
                onChange={(e) => setNotesText(e.target.value)}
                placeholder={notesModal.action === 'complete' ? 'Enter verification findings...' : 'Enter reason for dismissal...'}
                className="w-full h-24 p-3 border border-[#E2E8F0] rounded-lg text-xs text-[#334155] font-mono-tech focus:outline-none focus:border-accent resize-none"
              />
              <div className="flex justify-end gap-2 mt-4">
                <button onClick={() => setNotesModal(null)}
                  className="px-4 py-2 rounded-lg border border-[#E2E8F0] text-xs text-[#64748B] font-mono-tech hover:bg-[#F8FAFC]">
                  Cancel
                </button>
                <button onClick={() => handleAction(notesModal.workId, notesModal.action, notesText)}
                  disabled={actionLoading !== null}
                  className="px-4 py-2 rounded-lg bg-accent text-white text-xs font-bold font-mono-tech hover:bg-accent/90 transition disabled:opacity-50">
                  {notesModal.action === 'complete' ? 'Verify & Complete' : 'Dismiss'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* History Modal */}
        {historyModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg rounded-xl border border-[#E2E8F0] bg-white p-4 sm:p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-4">
                <div className="text-sm font-semibold text-[#0F172A]">Audit Trail</div>
                <button onClick={() => setHistoryModal(null)} className="text-[#94A3B8] hover:text-[#0F172A] text-lg">×</button>
              </div>
              <div className="text-[10px] font-mono-tech text-[#94A3B8] mb-3 break-all">{historyModal}</div>
              {historyLoading ? (
                <div className="py-8 text-center text-[#94A3B8] font-mono-tech text-xs animate-pulse">Loading...</div>
              ) : history.length === 0 ? (
                <div className="py-8 text-center text-[#94A3B8] font-mono-tech text-xs">No activity recorded yet.</div>
              ) : (
                <div className="space-y-3 max-h-[400px] overflow-y-auto">
                  {history.map((h) => (
                    <div key={h.id} className="p-3 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0]">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono-tech text-accent font-semibold">{h.action.replace(/_/g, ' ')}</span>
                        <span className="text-[10px] text-[#94A3B8]">
                          {h.created_at ? new Date(h.created_at).toLocaleString('en-IN') : '—'}
                        </span>
                      </div>
                      {h.actor && <div className="text-[10px] text-[#94A3B8] mt-1">by {h.actor}</div>}
                      {h.details && (
                        <pre className="text-[10px] text-[#64748B] font-mono-tech mt-2 whitespace-pre-wrap p-2 rounded bg-white overflow-x-auto">
                          {typeof h.details === 'string' ? h.details : JSON.stringify(h.details, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <WorkForensicDrawer workId={selectedWorkId} onClose={() => setSelectedWorkId(null)} sourcePage="Inspection Queue" />
    </div>
  );
}
