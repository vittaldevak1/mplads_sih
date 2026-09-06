'use client';

import { WorkDetail, RiskScore } from '@/types';

function getSeverityColor(score: number | null) {
  if (score === null) return { bg: '#F1F5F9', text: '#64748B', border: '#E2E8F0' };
  if (score >= 75) return { bg: '#FEF2F2', text: '#991B1B', border: '#F87171' };
  if (score >= 45) return { bg: '#FFFBEB', text: '#92400E', border: '#FBBF24' };
  return { bg: '#F0FDF4', text: '#166534', border: '#86EFAC' };
}

function getRiskBadge(compositeRisk: number | null) {
  if (compositeRisk === null) return { label: 'UNRATED', bg: '#F1F5F9', color: '#64748B', border: '#E2E8F0' };
  if (compositeRisk >= 65) return { label: 'HIGH RISK', bg: '#FEF2F2', color: '#991B1B', border: '#F87171' };
  if (compositeRisk >= 40) return { label: 'MEDIUM RISK', bg: '#FFFBEB', color: '#92400E', border: '#FBBF24' };
  return { label: 'LOW RISK', bg: '#F0FDF4', color: '#166534', border: '#86EFAC' };
}

export default function ForensicDossier({ work, risk }: { work: WorkDetail; risk: RiskScore | null }) {
  const badge = getRiskBadge(risk?.composite_risk ?? null);

  const handlePrint = () => {
    window.print();
  };

  return (
    <>
      <button
        onClick={handlePrint}
        className="px-4 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 font-bold text-xs transition hover:from-amber-400 hover:to-amber-500"
      >
        Download Forensic Dossier
      </button>

      <div id="dossier-content" className="hidden print:block">
        <style>{`
          @media print {
            body * { visibility: hidden; }
            #dossier-content, #dossier-content * { visibility: visible; }
            #dossier-content { position: absolute; left: 0; top: 0; width: 100%; padding: 40px; font-family: 'Times New Roman', serif; color: #0F172A; }
            .dossier-header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 20px; }
            .dossier-table { width: 100%; border-collapse: collapse; font-size: 12px; margin: 16px 0; }
            .dossier-table th { background: #F1F5F9; border-bottom: 2px solid #64748B; padding: 8px; text-align: left; font-size: 11px; }
            .dossier-table td { padding: 6px 8px; border-bottom: 1px solid #E2E8F0; font-size: 11px; }
            .sig-block { margin-top: 50px; display: flex; justify-content: space-between; text-align: center; }
            .sig-line { width: 220px; border-top: 1px solid #000; margin-top: 40px; font-size: 12px; }
          }
        `}</style>

        <div className="dossier-header">
          <div style={{ fontSize: '11px', letterSpacing: '2px', textTransform: 'uppercase', fontWeight: 'bold', color: '#64748B' }}>
            Government of India · Ministry of Statistics &amp; Programme Implementation
          </div>
          <div style={{ fontSize: '16px', fontWeight: 'bold', marginTop: '8px', letterSpacing: '1px' }}>
            MPLADS FORENSIC AUDIT DOSSIER
          </div>
          <div style={{ fontSize: '11px', color: '#991B1B', marginTop: '4px', fontWeight: 'bold' }}>
            CONFIDENTIAL — RESTRICTED (GFR-144)
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '16px', color: '#475569' }}>
          <span>Ref: MPLADS/{work.work_id}</span>
          <span>Date: {new Date().toLocaleDateString('en-IN')}</span>
          <span style={{ fontWeight: 'bold', color: badge.color, background: badge.bg, border: `1px solid ${badge.border}`, padding: '2px 8px' }}>
            {badge.label} — {risk?.composite_risk?.toFixed(1) ?? 'N/A'}/100
          </span>
        </div>

        <h3 style={{ fontSize: '13px', fontWeight: 'bold', borderBottom: '1px solid #64748B', paddingBottom: '4px', marginTop: '20px' }}>
          Section 1: Project Information
        </h3>
        <table className="dossier-table">
          <tbody>
            <tr><td style={{ fontWeight: 'bold', width: '160px' }}>Work ID</td><td>{work.work_id}</td></tr>
            <tr><td style={{ fontWeight: 'bold' }}>Description</td><td>{work.work_description || '—'}</td></tr>
            <tr><td style={{ fontWeight: 'bold' }}>Category</td><td>{work.work_category || '—'}</td></tr>
            <tr><td style={{ fontWeight: 'bold' }}>State / Constituency</td><td>{work.state || '—'} / {work.constituency || '—'}</td></tr>
            <tr><td style={{ fontWeight: 'bold' }}>IDA</td><td>{work.ida || '—'}</td></tr>
            <tr><td style={{ fontWeight: 'bold' }}>MP</td><td>{work.mp_name || '—'}</td></tr>
            <tr><td style={{ fontWeight: 'bold' }}>Vendor / Contractor</td><td>{work.vendor_name || '—'}</td></tr>
            <tr><td style={{ fontWeight: 'bold' }}>Sanctioned Amount</td><td>₹{work.sanction_amount?.toLocaleString('en-IN') || '—'}</td></tr>
            <tr><td style={{ fontWeight: 'bold' }}>Amount Disbursed</td><td>₹{work.amount_disbursed?.toLocaleString('en-IN') || '—'}</td></tr>
            <tr><td style={{ fontWeight: 'bold' }}>Status</td><td>{work.work_status || '—'}</td></tr>
          </tbody>
        </table>

        <h3 style={{ fontSize: '13px', fontWeight: 'bold', borderBottom: '1px solid #64748B', paddingBottom: '4px', marginTop: '20px' }}>
          Section 2: Multi-Modal Forensic Anomaly Attribution (11-Signal Framework)
        </h3>
        <table className="dossier-table">
          <thead>
            <tr>
              <th>Signal</th>
              <th>Dimension</th>
              <th>Score</th>
              <th>Severity</th>
              <th>Weight</th>
              <th>Evidence / Explanation</th>
            </tr>
          </thead>
          <tbody>
            {risk?.signals.map((signal) => {
              const sev = getSeverityColor(signal.score);
              return (
                <tr key={signal.signal_code}>
                  <td style={{ fontWeight: 'bold' }}>{signal.signal_code}</td>
                  <td>{signal.signal_name}</td>
                  <td style={{ fontWeight: 'bold' }}>{signal.available && signal.score !== null ? signal.score.toFixed(0) : 'N/A'}</td>
                  <td style={{ background: sev.bg, color: sev.text, fontWeight: 'bold' }}>
                    {signal.available && signal.score !== null
                      ? signal.score >= 75 ? 'CRITICAL' : signal.score >= 45 ? 'ELEVATED' : 'CLEAR'
                      : 'UNAVAILABLE'}
                  </td>
                  <td>{(signal.weight * 100).toFixed(0)}%</td>
                  <td>{signal.explanation || '—'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <h3 style={{ fontSize: '13px', fontWeight: 'bold', borderBottom: '1px solid #64748B', paddingBottom: '4px', marginTop: '20px' }}>
          Section 3: Statutory Enforcement Directives under GFR 2017
        </h3>
        <ol style={{ fontSize: '11px', lineHeight: '1.8', paddingLeft: '20px' }}>
          <li>District Magistrate to dispatch Physical Inspection Team within 72 hours.</li>
          <li>PFMS electronic payment token flagged for hold pending Form 24 re-certification.</li>
          <li>Contractor track-record index updated to block concurrent awards under Section 4.2.</li>
        </ol>

        <div className="sig-block">
          <div className="sig-line">
            <div style={{ fontSize: '11px', marginTop: '4px' }}>Nodal Officer (MPLADS)</div>
          </div>
          <div className="sig-line">
            <div style={{ fontSize: '11px', marginTop: '4px' }}>District Magistrate</div>
          </div>
          <div className="sig-line">
            <div style={{ fontSize: '11px', marginTop: '4px' }}>Joint Secretary, MoSPI</div>
          </div>
        </div>
      </div>
    </>
  );
}
