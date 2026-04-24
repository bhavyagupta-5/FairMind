import { useState } from 'react';
import { startAudit } from '../../api/client';
import Spinner from '../common/Spinner';

export default function StepPreview({ jobId, columns, config, onAuditStarted, onBack }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRunAudit = async () => {
    setLoading(true);
    setError(null);
    try {
      await startAudit({
        job_id: jobId,
        protected_attr: config.protected_attr,
        target_col: config.target_col,
        positive_label: config.positive_label,
      });
      onAuditStarted();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start audit.');
      setLoading(false);
    }
  };

  if (loading) return <Spinner message="Starting audit..." />;

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Ready to Audit</h2>
        <p className="text-slate-400">Review your configuration and run the audit</p>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* Config Summary */}
      <div className="p-6 bg-white/5 border border-white/10 rounded-2xl space-y-4">
        <h3 className="font-semibold text-slate-300 mb-4">Audit Configuration</h3>
        {[
          { label: 'Protected Attribute', value: config?.protected_attr },
          { label: 'Target Column', value: config?.target_col },
          { label: 'Positive Label', value: config?.positive_label },
          { label: 'Total Columns', value: columns.length },
        ].map(({ label, value }) => (
          <div key={label} className="flex justify-between items-center">
            <span className="text-slate-400 text-sm">{label}</span>
            <span className="font-medium text-blue-400">{value}</span>
          </div>
        ))}
      </div>

      {/* What happens next */}
      <div className="p-5 bg-blue-500/10 border border-blue-500/20 rounded-2xl">
        <p className="text-blue-300 text-sm font-medium mb-2">🤖 What Gemma 4 will do</p>
        <p className="text-slate-400 text-sm">
          After the audit completes, Gemma 4 will analyze the results and generate a plain-English
          explanation of any bias found — and recommend the best fix for your specific case.
        </p>
      </div>

      <div className="flex gap-4">
        <button
          onClick={onBack}
          className="flex-1 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl font-semibold transition-colors"
        >
          ← Back
        </button>
        <button
          onClick={handleRunAudit}
          className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold transition-all hover:scale-105"
        >
          🔬 Run Audit
        </button>
      </div>
    </div>
  );
}