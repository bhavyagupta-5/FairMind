import { useState } from 'react';
import { applyRemediation } from '../api/client';

export function useRemediate() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const applyFix = async (jobId, technique) => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await applyRemediation({ job_id: jobId, technique });
      setResult(data);
      return data;
    } catch (err) {
      setError(err.response?.data?.detail || 'Remediation failed');
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return { applyFix, isLoading, result, error };
}