from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import date, datetime
from decimal import Decimal

# =============================================
# AI Input Schemas (Backend → AI Engine)
# =============================================

class AIWorkInput(BaseModel):
    """Exact fields the backend prepares for the AI engine."""
    work_id: str
    work_title: Optional[str] = None
    work_description: Optional[str] = None
    sanction_amount: Optional[Decimal] = None
    disbursed_amount: Optional[Decimal] = None
    vendor_name: Optional[str] = None
    constituency: Optional[str] = None
    recommended_date: Optional[date] = None
    sanction_date: Optional[date] = None
    status: Optional[str] = None
    completion_date: Optional[date] = None
    has_image_proof: bool = False
    is_sc_quota: bool = False
    is_st_quota: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    citizen_complaint_count: int = 0

class AIPrepareRequest(BaseModel):
    """Request body for POST /api/v1/audit/prepare."""
    works: List[AIWorkInput]

# =============================================
# AI Output Schemas (AI Engine → Backend)
# =============================================

class SignalEvidence(BaseModel):
    """Evidence item from AI signal."""
    related_work_id: Optional[str] = None
    similarity: Optional[float] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None

class AISignalOutput(BaseModel):
    """Single signal output from AI engine."""
    signal_code: str
    signal_name: str
    version: str
    score: Optional[float] = None
    weight: float
    available: bool
    evidence: Optional[List[SignalEvidence]] = None
    explanation: Optional[str] = None

class AIWorkOutput(BaseModel):
    """Single work output from AI engine."""
    work_id: str
    composite_risk: float
    confidence_coverage: float
    inspection_priority: str
    signals: List[AISignalOutput]

class AIResultsRequest(BaseModel):
    """Request body for POST /api/v1/audit/batch (AI returns results)."""
    results: List[AIWorkOutput]

# =============================================
# Work Schemas
# =============================================

class WorkBase(BaseModel):
    work_id: str
    work_title: Optional[str] = None
    work_category: Optional[str] = None
    work_description: Optional[str] = None
    state: Optional[str] = None
    ida: Optional[str] = None
    constituency: Optional[str] = None
    parliament_house: str

class WorkListResponse(BaseModel):
    work_id: str
    work_description: Optional[str] = None
    state: Optional[str] = None
    constituency: Optional[str] = None
    work_category: Optional[str] = None
    parliament_house: str
    sanction_amount: Optional[float] = None
    work_status: Optional[str] = None
    amount_disbursed: Optional[float] = None
    composite_risk: Optional[float] = None
    inspection_priority: Optional[str] = None

class WorkDetailResponse(BaseModel):
    work_id: str
    work_title: Optional[str] = None
    work_category: Optional[str] = None
    work_description: Optional[str] = None
    state: Optional[str] = None
    ida: Optional[str] = None
    constituency: Optional[str] = None
    parliament_house: str
    recommended_date: Optional[str] = None
    recommended_amount: Optional[float] = None
    sanction_date: Optional[str] = None
    sanction_amount: Optional[float] = None
    completion_date: Optional[str] = None
    amount_disbursed: Optional[float] = None
    work_status: Optional[str] = None
    has_image_proof: bool = False
    is_sc_quota: bool = False
    is_st_quota: bool = False
    vendor_name: Optional[str] = None
    mp_name: Optional[str] = None
    anomalies: Optional[List[dict]] = None
    expenditures: Optional[List[dict]] = None

# =============================================
# Risk Schemas
# =============================================

class RiskSignalResponse(BaseModel):
    signal_code: str
    signal_name: str
    version: Optional[str] = None
    score: Optional[float] = None
    weight: float
    available: bool
    evidence: Optional[Any] = None
    explanation: Optional[str] = None

class RiskScoreResponse(BaseModel):
    work_id: str
    composite_risk: Optional[float] = None
    confidence_coverage: Optional[float] = None
    inspection_priority: Optional[str] = None
    signals: List[RiskSignalResponse]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# =============================================
# Dashboard Schemas
# =============================================

class DashboardSummary(BaseModel):
    total_works: int
    works_recommended: int
    works_sanctioned: int
    works_completed: int
    total_sanctioned_amount: float
    total_expenditure: float
    total_allocation: float
    budget_utilization: float
    high_risk: int
    medium_risk: int
    low_risk: int
    active_vendors: int
    states_covered: int

# =============================================
# Pagination Schemas
# =============================================

class PaginatedResponse(BaseModel):
    items: List[WorkListResponse]
    total: int
    page: int
    size: int
    pages: int
