import { useState, useEffect } from 'react';
import { JeccLog } from '../types';
import { apiService } from '../services/api';

export const useLog = (id: number) => {
  const [data, setData] = useState<JeccLog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLog = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiService.getLogById(id);
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch log');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchLog();
    }
  }, [id]);

  return { data, loading, error };
};