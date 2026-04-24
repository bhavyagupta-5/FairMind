import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuditJob } from '../hooks/useAuditJob';
import { downloadReport } from '../api/client';
import { explainBiasWithGemma, recommendRemediationWithGemma } from '../api/gemma';
import MetricCards from '../components/Dashboard/MetricCards';
import GroupBarChart from '../components/Dashboard/GroupBarChart';
import SHAPPanel from '../components/Dashboard/SHAPPanel';
import RemediationPanel from '../components/Dashboard/RemediationPanel';
import GemmaInsight from '../components/Dashboard/GemmaInsight';
import Spinner from '../components/common/Spinner';
import Badge from '../components/common/Badge';

export default function DashboardPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const { status, progress, progressMessage, results, explanation, isComplete, isError } = useAuditJob(jobId);

  const [gemmaExplanation, setGemmaExplanation] = useState(null);
  const [gemmaRecommendation, setGemmaRecommendation] = useState(null);
  const [gemmaLoading, setGemmaLoading] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [remediationResult, setRemediationResult] = useState(null);

  // Once audit completes, call Gemma 4
  useEffect(() => {
    if (isComplete && results) {
      setGemmaLoading(true);
      Promise.all([
        explainBiasWithGemma(results),
        recommendRemediationWithGemma(results),
      ]).then(([explanation, recommendation]) => {
        setGemmaExplanation(explanation);
        setGemmaRecommendation(recommendation);
      }).finally(() => setGemmaLoading(false));
    }
  }, [isComplete, results]);

  const handleDownloadPdf = async () => {
    setDownloadingPdf(true);
    try {
      const { data } = await downloadReport(jobId);
      const url = window.URL.createObjectURL(new Blob([data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = `FairLens_Audit_${jobId}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download report. Please try again.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  // ── Loading State ─────────────────────────────────────────────────────────
  if (!isComplete && !isError) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-5xl mb-6">🔬</div>
          <h2 className="text-2xl font-bold mb-3">Analyzing Your Dataset</h2>
          <p className="text-slate-400 mb-8">
            Gemma 4 is reviewing the results as they come in...
          </p>

          {/* Progress Bar */}
          <div className="w-full bg-white/10 rounded-full h-2 mb-3">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-slate-400 text-sm mb-2">{progressMessage}</p>
          <p className="text-slate-600 text-xs">{progress}% complete</p>
        </div>
      </div>
    );
  }

  // ── Error State ───────────────────────────────────────────────────────────
  if (isError) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4">❌</div>
          <h2 className="text-2xl font-bold mb-3">Audit Failed</h2>
          <p className="text-slate-400 mb-6">Something went wrong during the audit.</p>
          <button
            onClick={() => navigate('/wizard')}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // ── Dashboard ─────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-950 text-white">

      {/* Header */}
      <div className="border-b border-white/10 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="text-slate-400 hover:text-white transition-colors text-sm"
          >
            ← Home
          </button>
          <span className="text-xl font-bold">🔍 FairLens</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400 text-sm">{results?.dataset_name}</span>
          <span className="text-slate-600">·</span>
          <span className="text-slate-400 text-sm">Protected: <span className="text-blue-400">{results?.protected_attribute}</span></span>
        </div>
        <div className="flex items-center gap-3">
          <Badge label={results?.severity} />
          <Badge label={results?.verdict} />
          <button
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
            className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {downloadingPdf ? 'Downloading...' : '📄 Download Report'}
          </button>
          <button
            onClick={() => navigate('/wizard')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-semibold transition-colors"
          >
            New Audit
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-8 space-y-8">

        {/* Gemma 4 AI Insight */}
        <GemmaInsight
          explanation={gemmaExplanation}
          recommendation={gemmaRecommendation}
          loading={gemmaLoading}
        />

        {/* Metric Cards */}
        <MetricCards results={results} />

        {/* Charts Row */}
        <div className="grid grid-cols-2 gap-6">
          <GroupBarChart results={results} />
          <SHAPPanel explanation={explanation} />
        </div>

        {/* Remediation Panel */}
        <RemediationPanel
          jobId={jobId}
          results={results}
          remediationResult={remediationResult}
          setRemediationResult={setRemediationResult}
          gemmaRecommendation={gemmaRecommendation}
        />

      </div>
    </div>
  );
}