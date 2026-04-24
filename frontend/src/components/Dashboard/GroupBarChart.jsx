import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Cell } from 'recharts';

export default function GroupBarChart({ results }) {
  if (!results) return null;

  const { groups, group_metrics, overall_metrics } = results;

  const data = groups.map(group => ({
    name: group.length > 12 ? group.substring(0, 12) + '...' : group,
    fullName: group,
    rate: parseFloat((group_metrics[group].selection_rate * 100).toFixed(1)),
    di: overall_metrics.disparate_impact[group],
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload?.length) {
      const d = payload[0].payload;
      return (
        <div className="bg-slate-800 border border-white/10 rounded-xl p-3 text-sm">
          <p className="font-semibold text-white mb-1">{d.fullName}</p>
          <p className="text-blue-400">Positive Rate: {d.rate}%</p>
          <p className={d.di >= 0.8 ? 'text-green-400' : 'text-red-400'}>
            Disparate Impact: {d.di?.toFixed(3)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="p-6 bg-white/5 border border-white/10 rounded-2xl">
      <h3 className="font-bold mb-1">Positive Outcome Rate by Group</h3>
      <p className="text-slate-400 text-xs mb-6">
        Dashed line = EEOC 80% threshold. Groups below are flagged.
      </p>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
          <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} domain={[0, 100]} unit="%" />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={80} stroke="#f59e0b" strokeDasharray="5 5" label={{ value: '80%', fill: '#f59e0b', fontSize: 11 }} />
          <Bar dataKey="rate" radius={[6, 6, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.di >= 0.8 ? '#22c55e' : '#ef4444'}
                opacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}