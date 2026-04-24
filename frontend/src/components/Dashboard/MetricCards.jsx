import Badge from '../common/Badge';

export default function MetricCards({ results }) {
  if (!results) return null;
  const { overall_metrics, verdict, severity, model_accuracy } = results;

  const cards = [
    {
      label: 'Demographic Parity Ratio',
      value: overall_metrics.demographic_parity_ratio.toFixed(3),
      threshold: '≥ 0.80',
      pass: overall_metrics.demographic_parity_ratio >= 0.8,
      tooltip: 'Are positive outcomes equally distributed across groups?',
    },
    {
      label: 'Equalized Odds Gap',
      value: overall_metrics.equalized_odds_gap.toFixed(3),
      threshold: '≤ 0.10',
      pass: overall_metrics.equalized_odds_gap <= 0.1,
      tooltip: 'Are true positive and false positive rates equal across groups?',
    },
    {
      label: 'Model Accuracy',
      value: `${(model_accuracy * 100).toFixed(1)}%`,
      threshold: 'Baseline',
      pass: true,
      tooltip: 'Overall model prediction accuracy on test data.',
    },
    {
      label: 'Overall Verdict',
      value: verdict,
      threshold: severity + ' RISK',
      pass: verdict === 'PASS',
      tooltip: 'Overall fairness verdict based on EEOC 4/5ths rule.',
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map(({ label, value, threshold, pass, tooltip }) => (
        <div
          key={label}
          title={tooltip}
          className={`p-5 rounded-2xl border transition-all ${
            pass
              ? 'bg-green-500/5 border-green-500/20'
              : 'bg-red-500/5 border-red-500/20'
          }`}
        >
          <p className="text-slate-400 text-xs font-medium mb-3 leading-tight">{label}</p>
          <p className={`text-3xl font-black mb-2 ${pass ? 'text-green-400' : 'text-red-400'}`}>
            {value}
          </p>
          <div className="flex items-center justify-between">
            <span className="text-slate-500 text-xs">Threshold: {threshold}</span>
            <Badge label={pass ? 'PASS' : 'FAIL'} />
          </div>
        </div>
      ))}
    </div>
  );
}