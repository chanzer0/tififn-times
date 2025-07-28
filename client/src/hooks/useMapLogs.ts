import { useState, useEffect } from 'react';
import { LogsResponse, LogFilters } from '../types';
import { apiService } from '../services/api';

export const useMapLogs = () => {
  const [data, setData] = useState<LogsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMapLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch up to 1000 geocoded logs for the map
      const filters: LogFilters = {
        perPage: 1000,
        geocodedOnly: true,
        page: 1
      };
      
      const response = await apiService.getLogs(filters);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch map logs');
    } finally {
      setLoading(false);
    }
  };

  const refresh = () => {
    fetchMapLogs();
  };

  useEffect(() => {
    fetchMapLogs();
  }, []); // Only run on mount

  return {
    data,
    loading,
    error,
    refresh,
  };
};