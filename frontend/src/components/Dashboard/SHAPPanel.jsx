import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function SHAPPanel({ explanation }) {
  if (!explanation || !explanation.group_shap || Object.keys(explanation.group_shap).length === 0) {
    return (
      <div className="p-6 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center">
        <p className="text-slate-500 text-sm">SHAP data not available</p>
      </div>
    );
  }

  const groups = Object.keys(explanation.group_shap);
  const features = explanation.features?.slice(0, 6) || [];

  const data = features.map(feat => {
    const entry = { feature: feat };
    groups.forEach(g => {
      entry[g] = explanation.group_shap[g]?.[feat] || 0;
    });
    return entry;
  });

  const colors = ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b'];

  return (
    <div className="p-6 bg-white/5 border border-white/10 rounded-2xl">
      <h3 className="font-bold mb-1">Feature Influence (SHAP)</h3>
      <p className="text-slate-400 text-xs mb-6">
        Mean absolute SHAP value per feature per group
      </p>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} layout="vertical" margin={{ left: 20, right: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
          <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} />
          <YAxis type="category" dataKey="feature" tick={{ fill: '#94a3b8', fontSize: 10 }} width={90} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #ffffff20', borderRadius: '8px' }}
            labelStyle={{ color: '#fff' }}
          />
          {groups.slice(0, 2).map((g, i) => (
            <Bar key={g} dataKey={g} fill={colors[i]} opacity={0.85} radius={[0, 4, 4, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>

      {/* Top Bias Drivers */}
      {explanation.top_bias_drivers?.length > 0 && (
        <div className="mt-4 space-y-2">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Top Bias Drivers</p>
          {explanation.top_bias_drivers.slice(0, 2).map((d, i) => (
            <div key={i} className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-300 text-xs leading-relaxed">{d.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}