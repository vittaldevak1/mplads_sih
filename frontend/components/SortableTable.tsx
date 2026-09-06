'use client';

import { useState, useMemo, useCallback } from 'react';

export type SortConfig = {
  key: string;
  direction: 'asc' | 'desc';
};

export interface Column<T> {
  key: string;
  header: string;
  tooltip?: string;
  width?: string;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  sortType?: 'text' | 'number' | 'priority' | 'status';
  render?: (row: T) => React.ReactNode;
}

interface SortableTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (row: T) => void;
  emptyText?: string;
}

const PRIORITY_ORDER: Record<string, number> = {
  CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, None: 4, null: 4, undefined: 4,
};

const STATUS_ORDER: Record<string, number> = {
  pending: 0, assigned: 1, in_progress: 2, request_documents: 3,
  field_inspection: 4, completed: 5, dismissed: 6, closed: 7,
};

function getNestedValue(obj: any, path: string): any {
  return path.split('.').reduce((acc, part) => acc?.[part], obj);
}

function compareValues(a: any, b: any, direction: 'asc' | 'desc', sortType?: string): number {
  if (a === null || a === undefined) return 1;
  if (b === null || b === undefined) return -1;

  if (sortType === 'priority') {
    const aOrder = PRIORITY_ORDER[a] ?? 4;
    const bOrder = PRIORITY_ORDER[b] ?? 4;
    return direction === 'asc' ? aOrder - bOrder : bOrder - aOrder;
  }

  if (sortType === 'status') {
    const aOrder = STATUS_ORDER[a] ?? 99;
    const bOrder = STATUS_ORDER[b] ?? 99;
    return direction === 'asc' ? aOrder - bOrder : bOrder - aOrder;
  }

  if (sortType === 'number' || (typeof a === 'number' && typeof b === 'number')) {
    return direction === 'asc' ? a - b : b - a;
  }

  const strA = String(a).toLowerCase();
  const strB = String(b).toLowerCase();
  if (strA < strB) return direction === 'asc' ? -1 : 1;
  if (strA > strB) return direction === 'asc' ? 1 : -1;
  return 0;
}

export function SortIndicator({ config, columnKey }: { config: SortConfig | null; columnKey: string }) {
  if (!config || config.key !== columnKey) {
    return <span className="text-[#CBD5E1] ml-1 text-[9px]">↕</span>;
  }
  return (
    <span className="text-accent ml-1 font-bold text-[9px]">
      {config.direction === 'asc' ? '↑' : '↓'}
    </span>
  );
}

export function useSortableData<T>(items: T[], initialSort?: SortConfig) {
  const [sortConfig, setSortConfig] = useState<SortConfig | null>(initialSort || null);

  const sorted = useMemo(() => {
    if (!sortConfig) return items;
    return [...items].sort((a, b) => {
      const aVal = getNestedValue(a, sortConfig.key);
      const bVal = getNestedValue(b, sortConfig.key);
      return compareValues(aVal, bVal, sortConfig.direction);
    });
  }, [items, sortConfig]);

  const requestSort = useCallback((key: string) => {
    setSortConfig(prev => {
      if (prev?.key === key) {
        if (prev.direction === 'asc') return { key, direction: 'desc' };
        return null;
      }
      return { key, direction: 'asc' };
    });
  }, []);

  return { sorted, sortConfig, requestSort };
}

export function SortableTable<T extends Record<string, any>>({
  columns, data, onRowClick, emptyText = 'No data'
}: SortableTableProps<T>) {
  const { sorted, sortConfig, requestSort } = useSortableData(data);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-[#E2E8F0]">
            {columns.map(col => (
              <th key={col.key}
                className={`py-2 px-3 font-mono-tech text-[10px] uppercase tracking-wider text-[#94A3B8] ${
                  col.sortable ? 'cursor-pointer hover:text-accent select-none' : ''
                } text-${col.align || 'left'}`}
                style={{ width: col.width }}
                title={col.tooltip}
                onClick={() => col.sortable && requestSort(col.key)}>
                <span className="flex items-center gap-1">
                  {col.header}
                  {col.sortable && <SortIndicator config={sortConfig} columnKey={col.key} />}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.length === 0 ? (
            <tr><td colSpan={columns.length} className="text-center text-[#94A3B8] py-8 font-mono-tech">{emptyText}</td></tr>
          ) : sorted.map((row, i) => (
            <tr key={i}
              className={`border-b border-[#F1F5F9] hover:bg-[#F8FAFC] transition ${onRowClick ? 'cursor-pointer' : ''}`}
              onClick={() => onRowClick?.(row)}>
              {columns.map(col => (
                <td key={col.key} className={`py-2 px-3 text-${col.align || 'left'}`}>
                  {col.render ? col.render(row) : getNestedValue(row, col.key)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
