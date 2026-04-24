import { useState } from 'react';

export default function StepConfigure({ columns, onNext, onBack }) {
  const [protectedAttr, setProtectedAttr] = useState('');
  const [targetCol, setTargetCol] = useState('');
  const [positiveLabel, setPositiveLabel] = useState('');

  const canProceed = protectedAttr && targetCol && positiveLabel;

  const selectClass = "w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-colors";

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Configure Your Audit</h2>
        <p className="text-slate-400">Tell FairLens what to look for in your dataset</p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Protected Attribute
            <span className="ml-2 text-slate-500 font-normal">— the demographic column to audit</span>
          </label>
          <select value={protectedAttr} onChange={e => setProtectedAttr(e.target.value)} className={selectClass}>
            <option value="">Select a column...</option>
            {columns.map(col => <option key={col} value={col}>{col}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Target Column
            <span className="ml-2 text-slate-500 font-normal">— what the model predicts</span>
          </label>
          <select value={targetCol} onChange={e => setTargetCol(e.target.value)} className={selectClass}>
            <option value="">Select a column...</option>
            {columns.map(col => <option key={col} value={col}>{col}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Positive Label
            <span className="ml-2 text-slate-500 font-normal">— the favorable outcome value</span>
          </label>
          <input
            type="text"
            value={positiveLabel}
            onChange={e => setPositiveLabel(e.target.value)}
            placeholder="e.g. 1, yes, >50K"
            className={selectClass}
          />
          <p className="text-slate-500 text-xs mt-1">
            For COMPAS: enter <code className="text-blue-400">1</code> · For Adult Income: enter <code className="text-blue-400">&gt;50K</code>
          </p>
        </div>
      </div>

      <div className="flex gap-4">
        <button
          onClick={onBack}
          className="flex-1 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl font-semibold transition-colors"
        >
          ← Back
        </button>
        <button
          onClick={() => onNext({ protected_attr: protectedAttr, target_col: targetCol, positive_label: positiveLabel })}
          disabled={!canProceed}
          className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl font-semibold transition-colors"
        >
          Next →
        </button>
      </div>
    </div>
  );
}