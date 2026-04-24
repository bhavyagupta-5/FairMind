import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import StepUpload from '../components/UploadWizard/StepUpload';
import StepConfigure from '../components/UploadWizard/StepConfigure';
import StepPreview from '../components/UploadWizard/StepPreview';

export default function WizardPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [step, setStep] = useState(location.state ? 2 : 1);
  const [jobId, setJobId] = useState(location.state?.jobId || null);
  const [columns, setColumns] = useState(location.state?.columns || []);
  const [config, setConfig] = useState(null);

  const steps = ['Upload', 'Configure', 'Run Audit'];

  return (
    <div className="min-h-screen bg-slate-950 text-white">

      {/* Header */}
      <div className="border-b border-white/10 px-8 py-4 flex items-center gap-4">
        <button
          onClick={() => navigate('/')}
          className="text-slate-400 hover:text-white transition-colors text-sm"
        >
          ← Back
        </button>
        <span className="text-xl font-bold">🔍 FairLens</span>
      </div>

      {/* Step Indicator */}
      <div className="max-w-2xl mx-auto px-8 pt-10">
        <div className="flex items-center justify-center gap-4 mb-12">
          {steps.map((s, i) => (
            <div key={s} className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                  i + 1 < step ? 'bg-green-500 text-white' :
                  i + 1 === step ? 'bg-blue-600 text-white' :
                  'bg-white/10 text-slate-400'
                }`}>
                  {i + 1 < step ? '✓' : i + 1}
                </div>
                <span className={`text-sm font-medium ${i + 1 === step ? 'text-white' : 'text-slate-500'}`}>
                  {s}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div className={`w-16 h-0.5 ${i + 1 < step ? 'bg-green-500' : 'bg-white/10'}`} />
              )}
            </div>
          ))}
        </div>

        {/* Step Content */}
        {step === 1 && (
          <StepUpload
            onNext={(jId, cols) => {
              setJobId(jId);
              setColumns(cols);
              setStep(2);
            }}
          />
        )}
        {step === 2 && (
          <StepConfigure
            columns={columns}
            onNext={(cfg) => {
              setConfig(cfg);
              setStep(3);
            }}
            onBack={() => setStep(1)}
          />
        )}
        {step === 3 && (
          <StepPreview
            jobId={jobId}
            columns={columns}
            config={config}
            onAuditStarted={() => navigate(`/dashboard/${jobId}`)}
            onBack={() => setStep(2)}
          />
        )}
      </div>
    </div>
  );
}