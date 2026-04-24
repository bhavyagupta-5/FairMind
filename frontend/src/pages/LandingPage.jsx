import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDemoDatasets, loadDemoDataset } from '../api/client';
import Spinner from '../components/common/Spinner';

export default function LandingPage() {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(null);

  useEffect(() => {
    getDemoDatasets().then(r => setDatasets(r.data)).catch(console.error);
  }, []);

  const handleDemoClick = async (id) => {
    setLoading(id);
    try {
      const { data } = await loadDemoDataset(id);
      navigate('/wizard', { state: { jobId: data.job_id, columns: data.columns, datasetId: id } });
    } catch (err) {
      alert('Failed to load dataset. Make sure backend is running.');
    } finally {
      setLoading(null);
    }
  };

  const domainIcons = {
    'Criminal Justice': '⚖️',
    'Employment': '💼',
    'Finance': '🏦',
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-900 via-blue-950 to-slate-900 text-white">

      {/* Navbar */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-white/10">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🔍</span>
          <span className="text-xl font-bold text-white">FairLens</span>
          <span className="ml-2 px-2 py-0.5 text-xs bg-blue-500/20 text-blue-300 rounded-full border border-blue-500/30">
            Powered by Gemma 4
          </span>
        </div>
        <button
          onClick={() => navigate('/wizard')}
          className="px-5 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-semibold transition-colors"
        >
          Start Audit →
        </button>
      </nav>

      {/* Hero */}
      <div className="max-w-5xl mx-auto px-8 pt-24 pb-16 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-300 text-sm mb-8">
          <span>🤖</span>
          <span>AI-Powered Bias Detection with Gemma 4</span>
        </div>
        <h1 className="text-6xl font-bold mb-6 leading-tight">
          Audit your AI before it
          <span className="text-transparent bg-clip-text bg-linear-to-r from-blue-400 to-cyan-400"> harms real people</span>
        </h1>
        <p className="text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
          FairLens detects bias in your ML models, explains it using Gemma 4,
          and applies automated fixes — in under 2 minutes.
        </p>
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={() => navigate('/wizard')}
            className="px-8 py-4 bg-blue-600 hover:bg-blue-500 rounded-xl text-lg font-semibold transition-all hover:scale-105 shadow-lg shadow-blue-500/25"
          >
            Upload Your Dataset →
          </button>
          <a
            href="#demo"
            className="px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-lg font-semibold transition-colors"
          >
            Try a Demo
          </a>
        </div>
      </div>

      {/* How It Works */}
      <div className="max-w-5xl mx-auto px-8 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
        <div className="grid grid-cols-3 gap-8">
          {[
            { step: '01', icon: '📤', title: 'Upload', desc: 'Upload your CSV dataset or pick one of our demo datasets to get started instantly.' },
            { step: '02', icon: '🔬', title: 'Audit', desc: 'Our engine computes fairness metrics and Gemma 4 explains the bias in plain English.' },
            { step: '03', icon: '🛠️', title: 'Fix', desc: 'Apply automated debiasing techniques and watch metrics improve in real time.' },
          ].map(({ step, icon, title, desc }) => (
            <div key={step} className="relative p-6 bg-white/5 border border-white/10 rounded-2xl">
              <div className="text-5xl font-black text-white/5 absolute top-4 right-4">{step}</div>
              <div className="text-3xl mb-4">{icon}</div>
              <h3 className="text-lg font-bold mb-2">{title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Demo Datasets */}
      <div id="demo" className="max-w-5xl mx-auto px-8 py-16">
        <h2 className="text-3xl font-bold text-center mb-4">Try a Demo Dataset</h2>
        <p className="text-slate-400 text-center mb-12">
          No upload needed — pick a real-world dataset and see FairLens in action
        </p>
        <div className="grid grid-cols-3 gap-6">
          {datasets.map((ds) => (
            <div
              key={ds.id}
              className="p-6 bg-white/5 border border-white/10 hover:border-blue-500/50 rounded-2xl transition-all hover:bg-white/8 group"
            >
              <div className="text-3xl mb-3">{domainIcons[ds.domain] || '📊'}</div>
              <h3 className="font-bold text-lg mb-1">{ds.name}</h3>
              <span className="text-xs text-blue-400 font-medium">{ds.domain}</span>
              <p className="text-slate-400 text-sm mt-3 mb-4 leading-relaxed">{ds.description}</p>
              <div className="flex items-center justify-between text-xs text-slate-500 mb-5">
                <span>{ds.rows.toLocaleString()} rows</span>
                <span>Protected: {ds.protected_attrs.join(', ')}</span>
              </div>
              <button
                onClick={() => handleDemoClick(ds.id)}
                disabled={loading === ds.id}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-semibold transition-colors"
              >
                {loading === ds.id ? 'Loading...' : 'Try This Dataset →'}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-white/10 py-8 text-center text-slate-500 text-sm">
        <p>FairLens — Solution Challenge 2026 | Powered by Gemma 4, Fairlearn, AIF360, SHAP</p>
      </div>
    </div>
  );
}