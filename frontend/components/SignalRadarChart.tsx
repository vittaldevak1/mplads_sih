'use client';

import { Radar, RadarChart as RechartsRadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, ReferenceLine } from 'recharts';
import { RiskSignal } from '@/types';

const SIGNAL_LABELS: Record<string, string> = {
  F: 'F: Financial',
  D: 'D: Delay',
  X: 'X: Duplicate',
  V: 'V: Vendor',
  C: 'C: Citizen',
  Q: 'Q: Quota',
  O: 'O: OCR',
  S: 'S: Spatial',
  G: 'G: Satellite',
  B: 'B: Benford',
  Rs: 'Rs: SoR',
};

export default function SignalRadarChart({ signals, compositeRisk }: { signals: RiskSignal[]; compositeRisk: number | null }) {
  const data = signals.map((s) => ({
    signal: SIGNAL_LABELS[s.signal_code] || s.signal_code,
    score: s.available && s.score !== null ? s.score : 0,
    fullMark: 100,
  }));

  const polyColor = compositeRisk !== null && compositeRisk >= 65
    ? 'rgba(239, 68, 68, 0.25)'
    : compositeRisk !== null && compositeRisk >= 40
      ? 'rgba(245, 158, 11, 0.25)'
      : 'rgba(59, 130, 246, 0.25)';

  const lineColor = compositeRisk !== null && compositeRisk >= 65
    ? '#DC2626'
    : compositeRisk !== null && compositeRisk >= 40
      ? '#D97706'
      : '#2563EB';

  return (
    <div className="w-full">
      <div className="text-[10px] font-mono-tech text-[#64748B] uppercase tracking-wider mb-2 text-center">
        11-Signal Risk Radar
      </div>
      <ResponsiveContainer width="100%" height={350}>
        <RechartsRadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#CBD5E1" />
          <PolarAngleAxis
            dataKey="signal"
            tick={{ fontSize: 10, fill: '#475569', fontFamily: 'JetBrains Mono, monospace' }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fontSize: 9, fill: '#94A3B8' }}
            stroke="#CBD5E1"
          />
          <ReferenceLine y={40} stroke="#22C55E" strokeDasharray="dot" strokeWidth={1} label="" />
          <ReferenceLine y={65} stroke="#EF4444" strokeDasharray="dash" strokeWidth={1.5} label="" />
          <Radar
            name="Risk"
            dataKey="score"
            stroke={lineColor}
            fill={polyColor}
            strokeWidth={2.5}
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
      <div className="flex items-center justify-center gap-4 text-[10px] font-mono-tech text-[#94A3B8] mt-1">
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-green-500 inline-block" /> Safe (40)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-red-500 inline-block border-dashed" /> Critical (65)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 inline-block" style={{ background: lineColor }} /> Project
        </span>
      </div>
    </div>
  );
}
