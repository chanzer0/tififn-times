import axios from 'axios';
import { LogsResponse, JeccLog, LogFilters, HealthResponse } from '../types';

const api = axios.create({
  baseURL: import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1',
  timeout: 10000,
});

export const apiService = {
  // Health check
  async getHealth(): Promise<HealthResponse> {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  },

  // Get logs with filtering and pagination
  async getLogs(filters: LogFilters = {}): Promise<LogsResponse> {
    const params = new URLSearchParams();
    
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    if (filters.agency) params.append('agency', filters.agency);
    if (filters.callType) params.append('call_type', filters.callType);
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.perPage) params.append('per_page', filters.perPage.toString());

    const response = await api.get<LogsResponse>(`/logs?${params.toString()}`);
    return response.data;
  },

  // Get specific log by ID
  async getLogById(id: number): Promise<JeccLog> {
    const response = await api.get<JeccLog>(`/logs/${id}`);
    return response.data;
  },

  // Refresh logs (trigger scraper)
  async refreshLogs(): Promise<{ message: string }> {
    const response = await api.post('/logs/refresh');
    return response.data;
  },
};