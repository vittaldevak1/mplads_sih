'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState, useEffect, useRef } from 'react';
import { fetchWorks } from '@/lib/api';

const navItems = [
  { href: '/', label: 'Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { href: '/works', label: 'Works', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
  { href: '/inspection', label: 'Inspection', icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' },
  { href: '/anomalies', label: 'Anomalies', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' },
  { href: '/vendors', label: 'Vendors', icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4' },
  { href: '/analytics', label: 'Analytics', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setSearchOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(true);
        setTimeout(() => inputRef.current?.focus(), 100);
      }
      if (e.key === 'Escape') setSearchOpen(false);
    }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, []);

  useEffect(() => {
    if (!searchQuery.trim()) { setSearchResults([]); return; }
    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const data = await fetchWorks({ search: searchQuery, size: 8 });
        setSearchResults(data.items || []);
      } catch { setSearchResults([]); }
      setSearching(false);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  return (
    <>
      {/* Tricolor stripe */}
      <div className="tricolor-stripe w-full" />

      <nav className="bg-white border-b-2 border-accent sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-5 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-accent flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <span className="text-sm font-serif-luxury font-bold text-[#0F172A]">
                  e-SAKSHI
                </span>
                <span className="text-[10px] font-sans text-[#64748B] ml-2 hidden sm:inline">
                  MPLADS Forensic Portal
                </span>
              </div>
            </Link>

            <div className="flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = pathname === item.href || 
                  (item.href !== '/' && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                      isActive
                        ? 'bg-accent/10 text-accent border border-accent/20'
                        : 'text-[#64748B] hover:text-[#0F172A] hover:bg-[#F1F5F9]'
                    }`}
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
                    </svg>
                    <span className="hidden md:block">{item.label}</span>
                  </Link>
                );
              })}
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => { setSearchOpen(true); setTimeout(() => inputRef.current?.focus(), 100); }}
                className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-[#F1F5F9] border border-[#E2E8F0] text-[#64748B] hover:border-[#CBD5E1] transition text-xs font-mono-tech"
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span className="hidden lg:block">Search works...</span>
                <kbd className="hidden lg:block px-1 py-0.5 rounded bg-[#E2E8F0] text-[9px] text-[#94A3B8]">⌘K</kbd>
              </button>
              <div className="text-[9px] font-mono-tech text-[#94A3B8] hidden lg:block">
                MoSPI · Govt of India
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Search Modal */}
      {searchOpen && (
        <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-black/30 backdrop-blur-sm">
          <div ref={searchRef} className="w-full max-w-lg mx-4 rounded-xl border border-[#E2E8F0] bg-white shadow-2xl overflow-hidden">
            <div className="flex items-center gap-3 px-4 py-3 border-b border-[#E2E8F0]">
              <svg className="w-4 h-4 text-[#94A3B8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                ref={inputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search works by ID, description, state..."
                className="flex-1 bg-transparent text-sm text-[#0F172A] placeholder-[#94A3B8] outline-none font-sans"
              />
              <kbd className="px-1.5 py-0.5 rounded bg-[#F1F5F9] text-[10px] text-[#94A3B8]">ESC</kbd>
            </div>
            <div className="max-h-[300px] overflow-y-auto">
              {searching ? (
                <div className="py-8 text-center text-[#94A3B8] font-mono-tech text-xs animate-pulse">Searching...</div>
              ) : searchResults.length === 0 && searchQuery.trim() ? (
                <div className="py-8 text-center text-[#94A3B8] font-mono-tech text-xs">No results for &ldquo;{searchQuery}&rdquo;</div>
              ) : (
                searchResults.map((w) => (
                  <button
                    key={w.work_id}
                    onClick={() => { setSearchOpen(false); router.push(`/works/${encodeURIComponent(w.work_id)}`); }}
                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-[#F8FAFC] transition text-left border-b border-[#F1F5F9] last:border-0"
                  >
                    <div className="min-w-0">
                      <div className="text-xs text-[#334155] truncate">{w.work_description || w.work_id}</div>
                      <div className="text-[10px] font-mono-tech text-[#94A3B8] mt-0.5">
                        {w.state} · {w.constituency} · {w.parliament_house}
                      </div>
                    </div>
                    {w.composite_risk !== null && (
                      <span className={`text-xs font-mono-tech font-bold ml-3 ${
                        w.composite_risk >= 65 ? 'text-risk-critical' :
                        w.composite_risk >= 40 ? 'text-risk-high' : 'text-risk-low'
                      }`}>
                        {w.composite_risk.toFixed(1)}
                      </span>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
