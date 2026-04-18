import numpy as np
import logging

logger = logging.getLogger(__name__)


class ExplainEngine:

    def run(self, model, X_test, y_test, X_test_raw, protected_attr, groups):
        feature_names = list(X_test.columns)

        try:
            import shap
            explainer = shap.LinearExplainer(model, X_test)
            shap_values = explainer.shap_values(X_test)

            # Per-group mean absolute SHAP per feature
            sensitive_series = X_test_raw[protected_attr].astype(str)
            group_shap = {}
            for group in groups:
                mask = (sensitive_series == group).values
                if mask.sum() == 0:
                    continue
                group_shap_vals = np.abs(shap_values[mask])
                group_shap[group] = {
                    feat: round(float(group_shap_vals[:, i].mean()), 4)
                    for i, feat in enumerate(feature_names)
                }

            # Top bias drivers
            group_list = list(group_shap.keys())
            top_bias_drivers = []
            if len(group_list) >= 2:
                bias_scores = {}
                for feat in feature_names:
                    vals = [group_shap[g].get(feat, 0) for g in group_list]
                    bias_scores[feat] = max(vals) / max(min(vals), 0.001)

                sorted_feats = sorted(bias_scores, key=bias_scores.get, reverse=True)[:5]
                for feat in sorted_feats:
                    feat_vals = {g: group_shap[g].get(feat, 0) for g in group_list}
                    worst_group = max(feat_vals, key=feat_vals.get)
                    best_group = min(feat_vals, key=feat_vals.get)
                    differential = round(bias_scores[feat], 1)
                    top_bias_drivers.append({
                        "feature": feat,
                        "differential": differential,
                        "description": f"'{feat}' contributes {differential}x more to negative predictions for {worst_group} than {best_group}"
                    })

        except Exception as e:
            logger.warning("SHAP computation failed, returning empty explanation: %s", str(e))
            group_shap = {}
            top_bias_drivers = []

        return {
            "features": feature_names,
            "group_shap": group_shap,
            "top_bias_drivers": top_bias_drivers,
        }