import {
  User, FDRRecord, DashboardMetrics, NotificationItem,
  Institution, Bank, AuditLogItem, ExtractedField
} from '../types';

const API_BASE = '/api/v1';

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...(options.headers || {})
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401 && !endpoint.includes('/auth/login')) {
    // Session expired
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/login?expired=1';
  }

  if (!response.ok) {
    let errorDetail = 'Request failed';
    try {
      const errData = await response.json();
      errorDetail = errData.detail || errData.message || JSON.stringify(errData);
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Auth & MFA
  async login(email: string, password: string) {
    return request<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  },

  async mfaChallenge(temp_mfa_token: string, code?: string, recovery_code?: string) {
    return request<any>('/auth/mfa/challenge', {
      method: 'POST',
      body: JSON.stringify({ temp_mfa_token, code, recovery_code })
    });
  },

  async setupMFA() {
    return request<any>('/auth/mfa/setup', { method: 'POST' });
  },

  async verifyMFAEnrollment(secret: string, code: string) {
    return request<any>('/auth/mfa/verify-enrollment', {
      method: 'POST',
      body: JSON.stringify({ secret, code })
    });
  },

  async getMe(): Promise<User> {
    return request<User>('/auth/me');
  },

  // Dashboards
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return request<DashboardMetrics>('/dashboards/metrics');
  },

  // FDRs
  async getFDRs(params: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
    bank_name?: string;
    has_discrepancy?: boolean;
    sort_by?: string;
    sort_order?: string;
  }) {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.page_size) query.set('page_size', params.page_size.toString());
    if (params.search) query.set('search', params.search);
    if (params.status) query.set('status', params.status);
    if (params.bank_name) query.set('bank_name', params.bank_name);
    if (params.has_discrepancy !== undefined) query.set('has_discrepancy', params.has_discrepancy.toString());
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.sort_order) query.set('sort_order', params.sort_order);

    return request<{ items: FDRRecord[]; total: number; page: number; page_size: number; total_pages: number }>(
      `/fdrs/?${query.toString()}`
    );
  },

  async getFDR(id: string): Promise<FDRRecord> {
    return request<FDRRecord>(`/fdrs/${id}`);
  },

  async createFDR(data: any): Promise<FDRRecord> {
    return request<FDRRecord>('/fdrs/', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async updateFDR(id: string, data: any): Promise<FDRRecord> {
    return request<FDRRecord>(`/fdrs/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  async verifyFDR(id: string): Promise<FDRRecord> {
    return request<FDRRecord>(`/fdrs/${id}/verify`, { method: 'POST' });
  },

  // Document Upload & OCR
  async uploadDocument(fdr_id: string, file: File, document_type = 'FDR_RECEIPT') {
    const formData = new FormData();
    formData.append('fdr_id', fdr_id);
    formData.append('document_type', document_type);
    formData.append('file', file);

    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Upload failed');
    }
    return response.json();
  },

  async correctField(fieldId: string, correctedValue: string): Promise<ExtractedField> {
    return request<ExtractedField>(`/documents/fields/${fieldId}`, {
      method: 'PUT',
      body: JSON.stringify({ user_corrected_value: correctedValue })
    });
  },

  // Workflows
  async renewFDR(fdrId: string, new_maturity_date: string, rationale: string, supporting_doc_name?: string) {
    return request<any>(`/workflows/fdrs/${fdrId}/renew`, {
      method: 'POST',
      body: JSON.stringify({ new_maturity_date, rationale, supporting_doc_name })
    });
  },

  async releaseFDR(fdrId: string, clearance_reference: string, rationale: string, supporting_doc_name?: string) {
    return request<any>(`/workflows/fdrs/${fdrId}/release`, {
      method: 'POST',
      body: JSON.stringify({ clearance_reference, rationale, supporting_doc_name })
    });
  },

  async decideFDR(fdrId: string, decision_type: string, new_status: string, reason: string, remarks?: string) {
    return request<any>(`/workflows/fdrs/${fdrId}/decide`, {
      method: 'POST',
      body: JSON.stringify({ decision_type, new_status, reason, remarks })
    });
  },

  async getReviewQueue() {
    return request<{ total: number; items: any[] }>('/workflows/review-queue');
  },

  // Institutions & Banks
  async getInstitutions(search?: string): Promise<Institution[]> {
    const q = search ? `?search=${encodeURIComponent(search)}` : '';
    return request<Institution[]>(`/institutions/${q}`);
  },

  async getBanks(search?: string): Promise<Bank[]> {
    const q = search ? `?search=${encodeURIComponent(search)}` : '';
    return request<Bank[]>(`/banks/${q}`);
  },

  // Notifications
  async getNotifications(): Promise<{ items: NotificationItem[]; unread_count: number }> {
    return request<{ items: NotificationItem[]; unread_count: number }>('/notifications/');
  },

  async markNotificationRead(id: string) {
    return request<any>(`/notifications/${id}/read`, { method: 'PUT' });
  },

  async markAllNotificationsRead() {
    return request<any>('/notifications/read-all', { method: 'PUT' });
  },

  // Audit Logs
  async getAuditLogs(page = 1, page_size = 25, search?: string) {
    const q = new URLSearchParams({ page: page.toString(), page_size: page_size.toString() });
    if (search) q.set('search', search);
    return request<{ items: AuditLogItem[]; total: number; page: number; total_pages: number }>(
      `/audit-logs/?${q.toString()}`
    );
  },

  // Synthetic Dataset
  async generateDataset(mode: 'DEMO' | 'FULL' = 'DEMO', seed = 42) {
    return request<any>('/datasets/generate', {
      method: 'POST',
      body: JSON.stringify({ mode, seed })
    });
  },

  async resetDemoData() {
    return request<any>('/datasets/reset-demo-data', { method: 'POST' });
  }
};
