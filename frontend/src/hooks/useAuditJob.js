import { useState, useEffect, useRef } from 'react';
import { pollStatus, getResults, getExplanations } from '../api/client';

export function useAuditJob(jobId) {
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [results, setResults] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [isComplete, setIsComplete] = useState(false);
  const [isError, setIsError] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;

    intervalRef.current = setInterval(async () => {
      try {
        const { data } = await pollStatus(jobId);
        setStatus(data.status);
        setProgress(data.progress);
        setProgressMessage(data.progress_message);

        if (data.status === 'complete') {
          clearInterval(intervalRef.current);
          const [resultsRes, explainRes] = await Promise.all([
            getResults(jobId),
            getExplanations(jobId).catch(() => ({ data: null })),
          ]);
          setResults(resultsRes.data);
          setExplanation(explainRes.data);
          setIsComplete(true);
        }

        if (data.status === 'error') {
          clearInterval(intervalRef.current);
          setIsError(true);
        }
      } catch (err) {
        clearInterval(intervalRef.current);
        setIsError(true);
      }
    }, 2000);

    return () => clearInterval(intervalRef.current);
  }, [jobId]);

  return { status, progress, progressMessage, results, explanation, isComplete, isError };
}