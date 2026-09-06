export interface Work {
  work_id: string;
  work_description: string | null;
  state: string | null;
  constituency: string | null;
  work_category: string | null;
  parliament_house: 'lok_sabha' | 'rajya_sabha';
  sanction_amount: number | null;
  work_status: string | null;
  amount_disbursed: number | null;
  composite_risk: number | null;
  inspection_priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | null;
}

export interface WorkDetail {
  work_id: string;
  work_title: string | null;
  work_category: string | null;
  work_description: string | null;
  state: string | null;
  ida: string | null;
  constituency: string | null;
  parliament_house: string;
  recommended_date: string | null;
  recommended_amount: number | null;
  sanction_date: string | null;
  sanction_amount: number | null;
  completion_date: string | null;
  amount_disbursed: number | null;
  work_status: string | null;
  has_image_proof: boolean;
  is_sc_quota: boolean;
  is_st_quota: boolean;
  vendor_name: string | null;
  mp_name: string | null;
  anomalies: WorkAnomaly[] | null;
  expenditures: WorkExpenditure[] | null;
}

export interface WorkAnomaly {
  id: number;
  anomaly_type: string;
  severity: string;
  description: string | null;
  evidence: any;
  created_at: string | null;
}

export interface WorkExpenditure {
  vendor_name: string | null;
  expenditure_date: string | null;
  fund_disbursed_amount: number | null;
  payment_status: string | null;
}

export interface SignalEvidence {
  related_work_id: string | null;
  similarity: number | null;
  description: string | null;
  metadata: any;
}

export interface RiskSignal {
  signal_code: string;
  signal_name: string;
  version: string | null;
  score: number | null;
  weight: number;
  available: boolean;
  evidence: any;
  explanation: string | null;
}

export interface RiskScore {
  work_id: string;
  composite_risk: number | null;
  confidence_coverage: number | null;
  inspection_priority: string | null;
  signals: RiskSignal[];
  created_at: string | null;
  updated_at: string | null;
}

export interface DashboardSummary {
  total_works: number;
  works_recommended: number;
  works_sanctioned: number;
  works_completed: number;
  total_sanctioned_amount: number;
  total_expenditure: number;
  total_allocation: number;
  budget_utilization: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  active_vendors: number;
  states_covered: number;
}

export interface PaginatedResponse {
  items: Work[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface Anomaly {
  id: string;
  work_id: string;
  signal_code: string;
  signal_name: string;
  anomaly_type: string;
  score: number;
  severity: string;
  composite_risk: number | null;
  inspection_priority: string | null;
  state: string | null;
  constituency: string | null;
  description: string | null;
  evidence: any;
  task_status: string;
  triggered_signals?: { code: string; score: number }[];
}

export interface InspectionQueueItem {
  work_id: string;
  work_description: string | null;
  work_category: string | null;
  state: string | null;
  constituency: string | null;
  parliament_house: string;
  mp_name: string | null;
  sanction_amount: number | null;
  composite_risk: number | null;
  inspection_priority: string | null;
  confidence_coverage: number | null;
  signal_count: number;
  top_signals: { code: string; score: number }[];
  task_status: string;
  assigned_to: string | null;
  notes: string | null;
}

export interface InspectionHistoryItem {
  id: number;
  action: string;
  actor: string | null;
  details: any;
  created_at: string | null;
}

export interface InspectionQueueResponse {
  items: InspectionQueueItem[];
  total: number;
  counts: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    unanalyzed: number;
  };
}
