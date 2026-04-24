export default function GemmaInsight({ explanation, recommendation, loading }) {
  const recommendedTechnique = recommendation?.match(/RECOMMENDED:\s*(.+)/)?.[1]?.trim();
  const reason = recommendation?.match(/REASON:\s*(.+)/s)?.[1]?.trim();

  return (
    <div className="p-6 bg-linear-to-r from-purple-900/30 to-blue-900/30 border border-purple-500/20 rounded-2xl">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">🤖</span>
        <span className="font-bold text-purple-300">Gemma 4 AI Analysis</span>
        <span className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-300 rounded-full border border-purple-500/30">
          Powered by Google Gemma 4
        </span>
      </div>

      {loading ? (
        <div className="flex items-center gap-3 text-slate-400">
          <div className="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Gemma 4 is analyzing the bias patterns...</span>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-6">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Bias Explanation
            </p>
            <p className="text-slate-300 text-sm leading-relaxed">
              {explanation || 'Generating explanation...'}
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Recommended Fix
            </p>
            {recommendedTechnique && (
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-500/20 border border-purple-500/30 rounded-full text-purple-300 text-sm font-medium mb-2">
                ✨ {recommendedTechnique}
              </div>
            )}
            <p className="text-slate-300 text-sm leading-relaxed">
              {reason || explanation || 'Generating recommendation...'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}