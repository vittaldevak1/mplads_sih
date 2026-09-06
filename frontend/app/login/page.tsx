'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth, DEMO_ACCOUNTS, ROLE_LABELS, ROLE_COLORS, DemoRole } from '@/lib/auth';

const ROLE_SCOPE_INFO: Record<DemoRole, string> = {
  ministry_admin: 'Full national access — all states, all works',
  state_nodal: 'Scoped to Maharashtra — state-level works and vendors',
  district_authority: 'Scoped to Panchmahal, Gujarat — district works',
  inspection_officer: 'Assigned inspections + high-risk works',
  mp_user: 'Scoped to Lucknow constituency — own MP works',
};

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) router.replace('/');
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    await new Promise((r) => setTimeout(r, 300));
    const success = login(username, password);
    if (success) {
      router.push('/');
    } else {
      setError('Invalid credentials. Try a demo account below.');
    }
    setLoading(false);
  };

  const quickLogin = (un: string) => {
    const acct = DEMO_ACCOUNTS[un];
    if (acct) {
      setUsername(un);
      setPassword(acct.password);
    }
  };

  if (isAuthenticated) return null;

  return (
    <div className="min-h-[calc(100vh-56px)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto rounded-xl bg-accent flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 className="text-xl font-serif-luxury font-bold text-[#0F172A]">e-SAKSHI</h1>
          <p className="text-xs font-mono-tech text-[#64748B] mt-1">MPLADS Forensic Audit Platform</p>
          <p className="text-[10px] font-mono-tech text-[#94A3B8] mt-2">Demo Mode — Select a role to explore</p>
        </div>

        {/* Login Form */}
        <div className="gov-panel p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[10px] font-mono-tech text-[#64748B] uppercase tracking-wider mb-1.5">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] text-sm text-[#0F172A] font-sans focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20 transition"
                placeholder="Enter username"
                required
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono-tech text-[#64748B] uppercase tracking-wider mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] text-sm text-[#0F172A] font-sans focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20 transition"
                placeholder="Enter password"
                required
              />
            </div>

            {error && (
              <div className="px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 font-mono-tech">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-accent text-white text-sm font-bold font-mono-tech hover:bg-accent-light transition disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>

        {/* Quick Access */}
        <div className="mt-6">
          <div className="text-center mb-3">
            <span className="text-[10px] font-mono-tech text-[#94A3B8] uppercase tracking-wider">Quick Access — Demo Accounts</span>
          </div>
          <div className="space-y-2">
            {Object.entries(DEMO_ACCOUNTS).map(([key, acct]) => (
              <button
                key={key}
                onClick={() => {
                  quickLogin(key);
                  setUsername(key);
                  setPassword(acct.password);
                }}
                className="w-full flex items-center gap-3 p-3 rounded-lg bg-white border border-[#E2E8F0] hover:border-accent/30 hover:shadow-sm transition text-left group"
              >
                <span className={`px-2 py-1 rounded text-[10px] font-mono-tech font-bold shrink-0 ${ROLE_COLORS[acct.user.role]}`}>
                  {ROLE_LABELS[acct.user.role]}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-[#0F172A] group-hover:text-accent transition">{acct.user.name}</div>
                  <div className="text-[10px] font-mono-tech text-[#94A3B8] truncate">{ROLE_SCOPE_INFO[acct.user.role]}</div>
                </div>
                <div className="text-[10px] font-mono-tech text-[#CBD5E1] group-hover:text-accent transition shrink-0">
                  {key} / {acct.password}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-[9px] font-mono-tech text-[#CBD5E1]">
            Ministry of Statistics &amp; Programme Implementation · Government of India
          </p>
        </div>
      </div>
    </div>
  );
}
