export type UserRole = 'SUPER_ADMIN' | 'INSTITUTION_USER' | 'REVIEWING_OFFICIAL' | 'READONLY_AUDITOR';

export type FDRStatus = 
  | 'Draft'
  | 'Submitted'
  | 'Under Review'
  | 'Additional Information Required'
  | 'Verified by Authorized Source'
  | 'Manually Reviewed'
  | 'Verification Pending'
  | 'Approved'
  | 'Renewal Pending'
  | 'Release Requested'
  | 'Released'
  | 'Rejected'
  | 'Expired';

export type VerificationOutcome = 
  | 'Passed'
  | 'Warning'
  | 'Failed'
  | 'Not Checked'
  | 'Awaiting External Verification';

export type SeverityLevel = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  is_mfa_enabled: boolean;
  institution_id?: string;
}

export interface ExtractedField {
  id: string;
  field_name: string;
  extracted_value?: string;
  confidence: number;
  page_number: number;
  user_corrected_value?: string;
  is_corrected: boolean;
}

export interface FDRDocument {
  id: string;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  document_type: string;
  ocr_status: string;
  created_at: string;
  extracted_fields: ExtractedField[];
}

export interface VerificationCheck {
  id: string;
  check_name: string;
  outcome: VerificationOutcome;
  severity: SeverityLevel;
  evidence?: string;
  explanation: string;
  recommended_action?: string;
  requires_human_review: boolean;
  created_at: string;
}

export interface FDRRecord {
  id: string;
  fdr_number: string;
  institution_id: string;
  institution_name?: string;
  bank_id?: string;
  bank_name: string;
  branch_name?: string;
  principal_amount: number | string;
  currency: string;
  interest_rate?: number | string;
  issue_date: string;
  maturity_date: string;
  purpose: string;
  status: FDRStatus;
  verification_status: VerificationOutcome;
  assigned_reviewer_id?: string;
  has_discrepancy: boolean;
  discrepancy_notes?: string;
  anomaly_score?: number;
  is_synthetic: boolean;
  created_at: string;
  updated_at: string;
  documents: FDRDocument[];
  verification_checks: VerificationCheck[];
}

export interface UrgentActionItem {
  fdr_id: string;
  fdr_number: string;
  institution_name: string;
  bank_name: string;
  principal_amount: number | string;
  maturity_date: string;
  days_to_maturity: number;
  status: string;
  urgency: 'OVERDUE' | 'CRITICAL' | 'WARNING' | 'UPCOMING' | 'HIGH';
  action_type: string;
}

export interface DashboardMetrics {
  total_institutions: number;
  total_fdrs: number;
  total_recorded_principal: number | string;
  records_awaiting_review: number;
  records_with_discrepancies: number;
  fdrs_approaching_maturity_30d: number;
  fdrs_overdue_maturity: number;
  pending_renewal_requests: number;
  pending_release_requests: number;
  documents_requiring_verification: number;
  status_distribution: { status: string; count: number }[];
  maturity_timeline: { month_year: string; count: number; total_amount: number | string }[];
  bank_distribution: { bank_name: string; count: number; total_amount: number | string }[];
  urgent_actions: UrgentActionItem[];
  disclaimer: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  category: string;
  link?: string;
  is_read: boolean;
  fdr_id?: string;
  created_at: string;
}

export interface Institution {
  id: string;
  code: string;
  name: string;
  state: string;
  city: string;
  contact_email?: string;
  contact_phone?: string;
  is_active: boolean;
}

export interface Bank {
  id: string;
  code: string;
  name: string;
  branch?: string;
  ifsc_prefix?: string;
}

export interface AuditLogItem {
  id: string;
  actor_email?: string;
  actor_role?: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  details?: string;
  ip_address?: string;
  created_at: string;
}

export interface RiskTriggeredRule {
  rule_id: string;
  severity: 'INFO' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  title: string;
  explanation: string;
  action: string;
}

export interface RiskRadarItem {
  fdr_id: string;
  fdr_number: string;
  bank_name: string;
  branch_name?: string;
  principal_amount: number;
  status: string;
  maturity_date: string;
  days_left: number;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  risk_score: number;
  triggered_rules: RiskTriggeredRule[];
  has_discrepancy: boolean;
  doc_count: number;
}

export interface RiskRadarSummary {
  total_evaluated: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  discrepancy_count: number;
  items: RiskRadarItem[];
}

export interface ConsistencyCheckItem {
  id: string;
  fdr_id: string;
  fdr_number: string;
  bank_name: string;
  field: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  issue_type: string;
  description: string;
  recommended_action: string;
}

export interface ConsistencyCheckResponse {
  disclaimer: string;
  total_records_checked: number;
  inconsistency_count: number;
  items: ConsistencyCheckItem[];
}

export interface TimelineEvent {
  stage: string;
  title: string;
  timestamp: string;
  status: string;
  actor: string;
  details: string;
}

export interface FDRLifecycleChain {
  fdr_id: string;
  fdr_number: string;
  bank_name: string;
  principal_amount: number;
  current_status: string;
  issue_date: string;
  maturity_date: string;
  timeline_events: TimelineEvent[];
}

export interface MaturityBucketItem {
  id: string;
  fdr_number: string;
  bank_name: string;
  principal_amount: number;
  status: string;
  maturity_date: string;
  days_left: number;
  has_discrepancy: boolean;
}

export interface MaturityCalendarResponse {
  as_of_date: string;
  summary: {
    total_records: number;
    expired_count: number;
    within_7_days_count: number;
    within_15_days_count: number;
    within_30_days_count: number;
    future_count: number;
  };
  buckets: {
    expired: MaturityBucketItem[];
    within_7_days: MaturityBucketItem[];
    within_15_days: MaturityBucketItem[];
    within_30_days: MaturityBucketItem[];
    future: MaturityBucketItem[];
  };
}

export interface BottleneckItem {
  id: string;
  fdr_id?: string;
  fdr_number: string;
  bank_name: string;
  type: string;
  status: string;
  pending_days: number;
  responsible_role: string;
  action_required: string;
}

export interface BottleneckResponse {
  total_stalled_items: number;
  verification_queue_pending: number;
  renewal_requests_pending: number;
  release_requests_pending: number;
  critical_breaches_count: number;
  items: BottleneckItem[];
}

