import { useState, useEffect } from 'react';
import { LogsResponse, LogFilters } from '../types';
import { apiService } from '../services/api';

export const useLogs = (initialFilters: LogFilters = {}) => {
  const [data, setData] = useState<LogsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<LogFilters>(initialFilters);

  const fetchLogs = async (newFilters?: LogFilters) => {
    try {
      setLoading(true);
      setError(null);
      const filtersToUse = newFilters || filters;
      const response = await apiService.getLogs(filtersToUse);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
    } finally {
      setLoading(false);
    }
  };

  const updateFilters = (newFilters: Partial<LogFilters>) => {
    const updatedFilters = { ...filters, ...newFilters, page: 1 }; // Reset to page 1 when filters change
    setFilters(updatedFilters);
    fetchLogs(updatedFilters);
  };

  const goToPage = (page: number) => {
    const updatedFilters = { ...filters, page };
    setFilters(updatedFilters);
    fetchLogs(updatedFilters);
  };

  const refresh = () => {
    fetchLogs();
  };

  useEffect(() => {
    fetchLogs();
  }, []); // Only run on mount

  return {
    data,
    loading,
    error,
    filters,
    updateFilters,
    goToPage,
    refresh,
  };
};