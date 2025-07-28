export interface JeccLog {
  id: number;
  cfs_number?: number;
  address?: string;
  call_type?: string;
  log_date: string;
  log_time?: string;
  apt_suite?: string;
  agency?: string;
  disposition?: string;
  incident_number?: string;
  latitude?: number | string;
  longitude?: number | string;
  geocoded_at?: string;
  geocoded_address?: string;
  created_at: string;
  updated_at: string;
}

export interface LogsResponse {
  logs: JeccLog[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface LogFilters {
  startDate?: string;
  endDate?: string;
  agency?: string;
  callType?: string;
  page?: number;
  perPage?: number;
  geocodedOnly?: boolean;
}

export interface HealthResponse {
  status: string;
  database: string;
  cache: string;
}