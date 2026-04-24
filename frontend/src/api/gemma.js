import { GoogleGenerativeAI } from '@google/generative-ai';

const genAI = new GoogleGenerativeAI(import.meta.env.VITE_GEMINI_API_KEY);
const model = genAI.getGenerativeModel({ model: 'gemma-3-27b-it' });

export async function explainBiasWithGemma(results) {
  const { protected_attribute, groups, overall_metrics, verdict, severity, group_metrics } = results;

  const prompt = `
You are an AI fairness expert. Analyze this bias audit result and explain it in 3-4 sentences 
in plain English for a non-technical audience. Be specific about which groups are affected and by how much.

Dataset protected attribute: ${protected_attribute}
Groups analyzed: ${groups.join(', ')}
Demographic Parity Ratio: ${overall_metrics.demographic_parity_ratio} (minimum acceptable: 0.80)
Equalized Odds Gap: ${overall_metrics.equalized_odds_gap}
Disparate Impact per group: ${JSON.stringify(overall_metrics.disparate_impact)}
Group outcome rates: ${JSON.stringify(Object.fromEntries(groups.map(g => [g, group_metrics[g]?.selection_rate])))}
Overall verdict: ${verdict} — ${severity} risk

Write a clear, empathetic explanation. Do not use jargon. Start with the most important finding.
`;

  try {
    const result = await model.generateContent(prompt);
    return result.response.text();
  } catch (error) {
    console.error('Gemma 4 error:', error);
    return `This audit found a ${severity} risk bias. The demographic parity ratio is ${overall_metrics.demographic_parity_ratio}, which ${overall_metrics.demographic_parity_ratio < 0.8 ? 'falls below' : 'meets'} the EEOC 80% threshold.`;
  }
}

export async function recommendRemediationWithGemma(results) {
  const { overall_metrics, severity, group_metrics, groups } = results;

  const prompt = `
You are an AI fairness expert. Based on this bias audit, recommend ONE debiasing technique 
from these three options and explain why in 2 sentences:
1. Reweighing - adjusts sample weights in training data
2. Threshold Calibration - sets different decision thresholds per group  
3. Adversarial Debiasing - trains model to ignore protected attribute

Audit results:
Demographic Parity Ratio: ${overall_metrics.demographic_parity_ratio}
Equalized Odds Gap: ${overall_metrics.equalized_odds_gap}
Severity: ${severity}
Group metrics: ${JSON.stringify(group_metrics)}

Respond in this exact format:
RECOMMENDED: [technique name]
REASON: [2 sentence explanation]
`;

  try {
    const result = await model.generateContent(prompt);
    return result.response.text();
  } catch (error) {
    return 'RECOMMENDED: Reweighing\nREASON: Reweighing is the most reliable technique for datasets with significant group imbalances. It adjusts sample weights during training to give underrepresented groups more influence.';
  }
}

export async function summarizeRemediationWithGemma(before, after, technique) {
  const prompt = `
You are an AI fairness expert. Summarize what changed after applying ${technique} debiasing 
in 2 sentences for a non-technical audience. Be specific about the improvement.

Before:
- Demographic Parity Ratio: ${before.demographic_parity_ratio}
- Equalized Odds Gap: ${before.equalized_odds_gap}

After:
- Demographic Parity Ratio: ${after.demographic_parity_ratio}
- Equalized Odds Gap: ${after.equalized_odds_gap}

Focus on what this means for real people affected by this model.
`;

  try {
    const result = await model.generateContent(prompt);
    return result.response.text();
  } catch (error) {
    const improvement = (after.demographic_parity_ratio - before.demographic_parity_ratio).toFixed(2);
    return `Applying ${technique} improved the demographic parity ratio by ${improvement} points. The model now treats different groups more fairly.`;
  }
}