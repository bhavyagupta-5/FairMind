import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadCSV, getDemoDatasets, loadDemoDataset } from '../../api/client';
import Spinner from '../common/Spinner';
import { useEffect } from 'react';

export default function StepUpload({ onNext }) {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDemoDatasets().then(r => setDatasets(r.data)).catch(console.error);
  }, []);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;
    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file only.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await uploadCSV(formData);
      onNext(data.job_id, data.columns);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [onNext]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
  });

  const handleDemoClick = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await loadDemoDataset(id);
      onNext(data.job_id, data.columns);
    } catch (err) {
      setError('Failed to load demo dataset.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spinner message="Processing your dataset..." />;

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Upload Your Dataset</h2>
        <p className="text-slate-400">Upload a CSV file or choose a demo dataset below</p>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-blue-500 bg-blue-500/10'
            : 'border-white/20 hover:border-blue-500/50 hover:bg-white/5'
        }`}
      >
        <input {...getInputProps()} />
        <div className="text-4xl mb-4">📂</div>
        <p className="text-lg font-medium mb-2">
          {isDragActive ? 'Drop your CSV here...' : 'Drag & drop your CSV file'}
        </p>
        <p className="text-slate-400 text-sm mb-4">or click to browse</p>
        <span className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors">
          Browse File
        </span>
        <p className="text-slate-500 text-xs mt-4">CSV only · Max 50MB · Min 50 rows</p>
      </div>

      {/* Demo Datasets */}
      <div>
        <p className="text-slate-400 text-sm text-center mb-4">— or try a demo dataset —</p>
        <div className="grid grid-cols-3 gap-3">
          {datasets.map((ds) => (
            <button
              key={ds.id}
              onClick={() => handleDemoClick(ds.id)}
              className="p-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-blue-500/50 rounded-xl text-left transition-all"
            >
              <p className="font-semibold text-sm mb-1">{ds.name}</p>
              <p className="text-slate-400 text-xs">{ds.domain}</p>
              <p className="text-slate-500 text-xs mt-1">{ds.rows.toLocaleString()} rows</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}