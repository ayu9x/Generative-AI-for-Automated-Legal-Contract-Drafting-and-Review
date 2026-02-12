import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — attach token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — handle auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const requestUrl = error.config?.url || '';
    const isAuthEndpoint = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/register');
    if (error.response?.status === 401 && !isAuthEndpoint) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ── Auth API ────────────────────────────────────────────────────────

export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (data: { email: string; password: string; full_name: string; organization?: string }) =>
    api.post('/auth/register', data),
  getProfile: () => api.get('/auth/me'),
  updateProfile: (data: { full_name?: string; organization?: string }) =>
    api.put('/auth/me', data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post('/auth/change-password', data),
  refreshToken: (refresh_token: string) =>
    api.post('/auth/refresh', { refresh_token }),
};

// ── Contracts API ───────────────────────────────────────────────────

export const contractsAPI = {
  list: (params?: { page?: number; page_size?: number; status?: string; contract_type?: string; search?: string }) =>
    api.get('/contracts/', { params }),
  get: (id: string) => api.get(`/contracts/${id}`),
  generate: (data: {
    contract_type: string;
    title: string;
    parties: Array<{ name: string; role: string }>;
    jurisdiction?: string;
    variables?: Record<string, unknown>;
    special_requirements?: string;
    use_ai_enhancement?: boolean;
  }) => api.post('/contracts/generate', data),
  update: (id: string, data: { title?: string; content?: string; status?: string }) =>
    api.put(`/contracts/${id}`, data),
  delete: (id: string) => api.delete(`/contracts/${id}`),
  getTemplates: () => api.get('/contracts/templates'),
  getSummary: (id: string) => api.post(`/contracts/${id}/summary`),
  explainClause: (data: { clause_text: string; context?: string; audience?: string }) =>
    api.post('/contracts/explain-clause', data),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/contracts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  export: (id: string, format: string) =>
    api.get(`/contracts/${id}/export`, { params: { format } }),
};

// ── Review / Risk API ───────────────────────────────────────────────

export const reviewAPI = {
  analyzeRisk: (data: {
    contract_id?: string;
    content?: string;
    contract_type?: string;
    jurisdiction?: string;
  }) => api.post('/review/risk-analysis', data),
  getAnalysis: (id: string) => api.get(`/review/analysis/${id}`),
  getHistory: (contractId: string) => api.get(`/review/history/${contractId}`),
  addComment: (data: { contract_id: string; section?: string; comment: string; severity?: string }) =>
    api.post('/review/comments', data),
  getComments: (contractId: string) => api.get(`/review/comments/${contractId}`),
  resolveComment: (commentId: string) => api.put(`/review/comments/${commentId}/resolve`),
  getStatus: (contractId: string) => api.get(`/review/status/${contractId}`),
};

// ── Compliance API ──────────────────────────────────────────────────

export const complianceAPI = {
  check: (data: {
    contract_id?: string;
    content?: string;
    contract_type?: string;
    jurisdictions?: string[];
    frameworks?: string[];
  }) => api.post('/compliance/check', data),
  getCheck: (id: string) => api.get(`/compliance/check/${id}`),
  getHistory: (contractId: string) => api.get(`/compliance/history/${contractId}`),
  listJurisdictions: () => api.get('/compliance/jurisdictions'),
  listFrameworks: () => api.get('/compliance/frameworks'),
  generateReport: (data: { contract_id: string; format?: string }) =>
    api.post('/compliance/report', data),
  getUpdates: (params?: { framework?: string; jurisdiction?: string }) =>
    api.get('/compliance/updates', { params }),
};

// ── Versions API ────────────────────────────────────────────────────

export const versionsAPI = {
  create: (data: { contract_id: string; content: string; change_description: string; branch?: string }) =>
    api.post('/versions/', data),
  getHistory: (contractId: string, branch?: string) =>
    api.get(`/versions/${contractId}`, { params: { branch } }),
  getVersion: (contractId: string, versionId: string) =>
    api.get(`/versions/${contractId}/version/${versionId}`),
  computeDiff: (contractId: string, versionA: string, versionB: string) =>
    api.post('/versions/diff', { version_id_a: versionA, version_id_b: versionB }, { params: { contract_id: contractId } }),
  createBranch: (data: { contract_id: string; branch_name: string; source_branch?: string }) =>
    api.post('/versions/branches', data),
  listBranches: (contractId: string) => api.get(`/versions/${contractId}/branches`),
  merge: (data: { contract_id: string; source_branch: string; target_branch?: string }) =>
    api.post('/versions/merge', data),
  approve: (contractId: string, data: { version_id: string; decision: string; comment?: string }) =>
    api.post('/versions/approve', data, { params: { contract_id: contractId } }),
};

// ── Templates API ──────────────────────────────────────────────────

export const templatesAPI = {
  list: (params?: { category?: string; jurisdiction?: string; risk_level?: string; search?: string; page?: number; page_size?: number }) =>
    api.get('/templates/', { params }),
  get: (templateId: string) => api.get(`/templates/${templateId}`),
  getCategories: () => api.get('/templates/categories'),
};

// ── Audit API ──────────────────────────────────────────────────────

export const auditAPI = {
  getLogs: (params?: { action?: string; resource?: string; user_email?: string; status?: string; page?: number; page_size?: number }) =>
    api.get('/audit/logs', { params }),
  getStats: () => api.get('/audit/stats'),
  getActions: () => api.get('/audit/actions'),
};

// ── Clauses API ────────────────────────────────────────────────────

export const clausesAPI = {
  list: (params?: { category?: string; jurisdiction?: string; risk_level?: string; search?: string; page?: number; page_size?: number }) =>
    api.get('/clauses/', { params }),
  get: (clauseId: string) => api.get(`/clauses/${clauseId}`),
  getCategories: () => api.get('/clauses/categories'),
  explain: (data: { clause_text: string; audience?: string }) =>
    api.post('/clauses/explain', data),
};

// ── Compare API ────────────────────────────────────────────────────

export const compareAPI = {
  compare: (data: { text_a: string; text_b: string; label_a?: string; label_b?: string }) =>
    api.post('/compare/', data),
  getSummary: () => api.get('/compare/summary'),
};

// ── Notifications API ──────────────────────────────────────────────

export const notificationsAPI = {
  list: (params?: { unread_only?: boolean; page?: number; page_size?: number }) =>
    api.get('/notifications/', { params }),
  markAsRead: (id: string) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put('/notifications/read-all'),
  getUnreadCount: () => api.get('/notifications/unread-count'),
};

// ── Assistant API ──────────────────────────────────────────────────

export const assistantAPI = {
  chat: (data: { message: string; context?: string }) =>
    api.post('/assistant/chat', data),
  getSuggestions: () => api.get('/assistant/suggestions'),
};

// ── Reports API ────────────────────────────────────────────────────

export const reportsAPI = {
  getAnalytics: () => api.get('/reports/analytics'),
  exportContract: (contractId: string, format?: string) =>
    api.get(`/reports/export/${contractId}`, { params: { format } }),
  getSummary: () => api.get('/reports/summary'),
};

// ── Calendar API ───────────────────────────────────────────────────

export const calendarAPI = {
  getEvents: (params?: { month?: number; year?: number; event_type?: string }) =>
    api.get('/calendar/events', { params }),
  getUpcoming: (days?: number) => api.get('/calendar/upcoming', { params: { days } }),
  getEventTypes: () => api.get('/calendar/event-types'),
};

export default api;
