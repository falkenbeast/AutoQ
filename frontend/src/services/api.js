/**
 * AutoQ Centralized API Client Service
 * Connects React frontend components to the FastAPI backend.
 * Provides error handling, parameter serialization, multipart uploads, and binary file downloads.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiService {
  constructor(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  /**
   * Generic HTTP request dispatcher with error standardization.
   */
  async request(endpoint, options = {}) {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${this.baseUrl}${cleanEndpoint}`;

    const headers = {
      ...(options.isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...options.headers,
    };

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
        try {
          const errorJson = await response.json();
          errorMessage = errorJson.detail || errorJson.message || errorMessage;
          if (Array.isArray(errorMessage)) {
            errorMessage = errorMessage.map((e) => e.msg || JSON.stringify(e)).join(', ');
          }
        } catch {
          // ignore parsing error if response is not JSON
        }
        throw new Error(errorMessage);
      }

      // Handle binary downloads
      if (options.responseType === 'blob') {
        return await response.blob();
      }

      // Empty responses
      if (response.status === 204) {
        return null;
      }

      return await response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        console.warn(`[AutoQ API] Network connection failed to ${url}. Verify FastAPI backend is running.`);
        throw new Error(`Cannot reach AutoQ backend at ${this.baseUrl}. Please check server connectivity.`);
      }
      throw error;
    }
  }

  // ==========================================
  // System & Health Endpoints
  // ==========================================

  async checkHealth() {
    return this.request('/api/health');
  }

  // ==========================================
  // Analytics Endpoints
  // ==========================================

  async getAnalyticsOverview(params = {}) {
    const query = new URLSearchParams();
    if (params.batch && params.batch !== 'ALL') query.append('batch', params.batch);
    if (params.date_range) query.append('date_range', params.date_range);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/analytics/overview${qs}`);
  }

  async getInspectionTrends(params = {}) {
    const query = new URLSearchParams();
    if (params.days) query.append('days', params.days);
    if (params.batch && params.batch !== 'ALL') query.append('batch', params.batch);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/analytics/trends${qs}`);
  }

  async getDefectDistribution(params = {}) {
    const query = new URLSearchParams();
    if (params.batch && params.batch !== 'ALL') query.append('batch', params.batch);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/analytics/defect-distribution${qs}`);
  }

  async getQualityPerformance(params = {}) {
    const query = new URLSearchParams();
    if (params.batch && params.batch !== 'ALL') query.append('batch', params.batch);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/analytics/quality-performance${qs}`);
  }

  async getBatchComparison() {
    return this.request('/api/analytics/batches');
  }

  async getModelInsights() {
    return this.request('/api/analytics/model-insights');
  }

  // ==========================================
  // Inspection Management Endpoints
  // ==========================================

  async getInspections(params = {}) {
    const query = new URLSearchParams();
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size);
    if (params.search) query.append('search', params.search);
    if (params.status && params.status !== 'ALL') query.append('status', params.status);
    if (params.category && params.category !== 'ALL') query.append('category', params.category);
    if (params.batch && params.batch !== 'ALL') query.append('batch', params.batch);

    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/inspections${qs}`);
  }

  async getInspectionById(id) {
    return this.request(`/api/inspections/${id}`);
  }

  async createInspection(payload) {
    return this.request('/api/inspections', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateInspection(id, payload) {
    return this.request(`/api/inspections/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async deleteInspection(id) {
    return this.request(`/api/inspections/${id}`, {
      method: 'DELETE',
    });
  }

  async uploadInspectionsCsv(file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request('/api/inspections/upload', {
      method: 'POST',
      body: formData,
      isFormData: true,
    });
  }

  // ==========================================
  // Defect Prediction Endpoints
  // ==========================================

  async predictDefect(payload) {
    return this.request('/api/predictions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getPredictions(params = {}) {
    const query = new URLSearchParams();
    if (params.skip) query.append('skip', params.skip);
    if (params.limit) query.append('limit', params.limit);
    if (params.component_id) query.append('component_id', params.component_id);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/predictions${qs}`);
  }

  async getPredictionById(id) {
    return this.request(`/api/predictions/${id}`);
  }

  // ==========================================
  // Audit Reports Endpoints
  // ==========================================

  async getReports(params = {}) {
    const query = new URLSearchParams();
    if (params.skip) query.append('skip', params.skip);
    if (params.limit) query.append('limit', params.limit);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/reports${qs}`);
  }

  async generateReport(payload) {
    return this.request('/api/reports/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getReportById(id) {
    return this.request(`/api/reports/${id}`);
  }

  async downloadReport(reportId, filename = null) {
    const blob = await this.request(`/api/reports/${reportId}/download`, {
      responseType: 'blob',
    });

    // Create browser trigger
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = downloadUrl;

    let targetFilename = filename;
    if (!targetFilename) {
      const ext = blob.type?.includes('pdf') ? 'pdf' : (blob.type?.includes('csv') ? 'csv' : 'bin');
      targetFilename = `AutoQ-Report-${reportId}.${ext}`;
    }
    a.download = targetFilename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      window.URL.revokeObjectURL(downloadUrl);
      a.remove();
    }, 1000);
    return true;
  }
}

export const api = new ApiService(API_BASE_URL);
export default api;
