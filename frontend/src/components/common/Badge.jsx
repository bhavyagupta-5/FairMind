export default function Badge({ label }) {
  const colors = {
    HIGH:       'bg-red-100 text-red-700 border border-red-200',
    MEDIUM:     'bg-amber-100 text-amber-700 border border-amber-200',
    LOW:        'bg-green-100 text-green-700 border border-green-200',
    PASS:       'bg-green-100 text-green-700 border border-green-200',
    FAIL:       'bg-red-100 text-red-700 border border-red-200',
    BORDERLINE: 'bg-amber-100 text-amber-700 border border-amber-200',
  };
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${colors[label] || 'bg-slate-100 text-slate-600'}`}>
      {label}
    </span>
  );
}