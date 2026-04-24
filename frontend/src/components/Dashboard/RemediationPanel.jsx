import { useState } from 'react';
import { useRemediate } from '../../hooks/useRemediate';
import { summarizeRemediationWithGemma } from '../../api/gemma';
import Badge from '../common/Badge';

const TECHNIQUES = [
  {
    id: 'reweighing',
    name: 'Reweighing',
    icon: '⚖️',
    desc: 'Adjusts sample weights in training data to balance outcomes across groups.',
    best: 'Pre-processing · Best for imbalanced datasets',
  },
  {
    id: 'threshold',
    name: 'Threshold Calibration',
    icon: '🎯',
    desc: 'Sets different decision thresholds per group to equalize positive rates.',
    best: 'Post-processing · Best for quick fixes',
  },
  {
    id: 'adversarial',
    name: 'Adversarial Debiasing',
    icon: '🛡️',
    desc: 'Trains model to ignore protected attribute using strong regularisation.',
    best: 'In-processing · Best for deep bias',
  },
];

export default function RemediationPanel({ jobId, results, remediationResult, setRemediationResult, gemmaRecommendation }) {
  const [selected, setSelected] = useState(null);
  const [gemmaSummary, setGemmaSummary] = useState(null);
  const { applyFix, isLoading, error } = useRemediate();

  const recommendedTechnique = gemmaRecommendation?.match(/RECOMMENDED:\s*(.+)/)?.[1]?.trim()?.toLowerCase();

  const handleApply = async () => {
    if (!selected) return;
    const result = await applyFix(jobId, selected);
    if (result) {
      setRemediationResult(result);
      // Get Gemma 4 summary of what changed
      const summary = await summarizeRemediationWithGemma(result.before, result.after, selected);
      setGemmaSummary(summary);
    }
  };

  return (
    <div className="p-6 bg-white/5 border border-white/10 rounded-2xl">
      <h3 className="font-bold text-lg mb-2">Apply a Fix</h3>
      <p className="text-slate-400 text-sm mb-6">
        Select a debiasing technique and click Apply. Gemma 4 will explain what changed.
      </p>

      {/* Technique Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {TECHNIQUES.map((t) => {
          const isRecommended = recommendedTechnique && t.name.toLowerCase().includes(recommendedTechnique.split(' ')[0].toLowerCase());
          return (
            <div
              key={t.id}
              onClick={() => setSelected(t.id)}
              className={`relative p-4 rounded-xl border cursor-pointer transition-all ${
                selected === t.id
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-white/10 bg-white/5 hover:border-white/20'
              }`}
            >
              {isRecommended && (
                <div className="absolute -top-2 -right-2 px-2 py-0.5 bg-purple-600 text-white text-xs rounded-full font-semibold">
                  Gemma 4 ✨
                </div>
              )}
              <div className="text-2xl mb-2">{t.icon}</div>
              <p className="font-semibold text-sm mb-1">{t.name}</p>
              <p className="text-slate-400 text-xs mb-2 leading-relaxed">{t.desc}</p>
              <p className="text-slate-500 text-xs">{t.best}</p>
            </div>
          );
        })}
      </div>

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm mb-4">
          ⚠️ {error}
        </div>
      )}

      <button
        onClick={handleApply}
        disabled={!selected || isLoading}
        className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl font-semibold transition-colors"
      >
        {isLoading ? '⏳ Applying fix...' : '🛠️ Apply Selected Fix'}
      </button>

      {/* Before / After Results */}
      {remediationResult && (
        <div className="mt-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {/* Before */}
            <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-xl">
              <p className="text-xs font-semibold text-red-400 mb-3 uppercase tracking-wider">Before</p>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Parity Ratio</span>
                  <span className="text-red-400 font-bold">{remediationResult.before.demographic_parity_ratio.toFixed(3)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Eq. Odds Gap</span>
                  <span className="text-red-400 font-bold">{remediationResult.before.equalized_odds_gap.toFixed(3)}</span>
                </div>
              </div>
            </div>

            {/* After */}
            <div className="p-4 bg-green-500/5 border border-green-500/20 rounded-xl">
              <p className="text-xs font-semibold text-green-400 mb-3 uppercase tracking-wider">After</p>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Parity Ratio</span>
                  <span className="text-green-400 font-bold">
                    {remediationResult.after.demographic_parity_ratio.toFixed(3)}
                    <span className="text-xs ml-1">
                      ↑ +{(remediationResult.after.demographic_parity_ratio - remediationResult.before.demographic_parity_ratio).toFixed(3)}
                    </span>
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Eq. Odds Gap</span>
                  <span className="text-green-400 font-bold">{remediationResult.after.equalized_odds_gap.toFixed(3)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Gemma 4 Summary */}
          {gemmaSummary && (
            <div className="p-4 bg-purple-500/10 border border-purple-500/20 rounded-xl">
              <p className="text-xs font-semibold text-purple-400 mb-2">🤖 Gemma 4 Summary</p>
              <p className="text-slate-300 text-sm leading-relaxed">{gemmaSummary}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}