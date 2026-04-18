import pandas as pd
import numpy as np
import logging
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from fairlearn.metrics import MetricFrame, equalized_odds_difference
import sklearn.metrics as skm

logger = logging.getLogger(__name__)


class AuditEngine:
    def __init__(self):
        self.model = None
        self.X_test = None
        self.y_test = None
        self.X_test_raw = None
        self.groups = None
        self.sensitive_test = None

    def run(self, file_path, protected_attr, target_col, positive_label, update_fn=None):

        def u(p, m):
            if update_fn:
                update_fn(p, m)

        # --- Load & Clean ---
        u(10, "Loading and cleaning dataset...")
        df = pd.read_csv(file_path)
        df = df.dropna(how='all')

        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0])

        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].str.strip()

        # Store raw copy for group labels (before encoding)
        raw_df = df.copy()

        # --- Encode target to binary ---
        df[target_col] = (df[target_col].astype(str) == str(positive_label)).astype(int)

        # --- Label encode all categoricals ---
        for col in df.select_dtypes(include='object').columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))

        # --- Train/test split ---
        X = df.drop(columns=[target_col])
        y = df[target_col]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )

        # Keep raw test rows aligned (for group labels)
        self.X_test = X_test
        self.y_test = y_test
        self.X_test_raw = raw_df.loc[X_test.index]
        self.sensitive_test = self.X_test_raw[protected_attr].astype(str)
        self.groups = sorted(self.sensitive_test.unique().tolist())

        # --- Train model ---
        u(30, "Training baseline model...")
        self.model = LogisticRegression(max_iter=2000, random_state=42, solver='liblinear')
        self.model.fit(X_train, y_train)
        logger.info("Model trained on %d samples", len(X_train))

        # --- Compute fairness metrics ---
        u(60, "Computing fairness metrics...")
        y_pred = self.model.predict(X_test)
        accuracy = float(skm.accuracy_score(y_test, y_pred))

        mf = MetricFrame(
            metrics={
                "selection_rate": lambda y_t, y_p: float(np.mean(y_p)),
                "tpr": lambda y_t, y_p: float(skm.recall_score(y_t, y_p, zero_division=0)),
                "fpr": lambda y_t, y_p: float(
                    np.sum((y_p == 1) & (y_t == 0)) / max(np.sum(y_t == 0), 1)
                ),
                "precision": lambda y_t, y_p: float(
                    skm.precision_score(y_t, y_p, zero_division=0)
                ),
            },
            y_true=y_test,
            y_pred=y_pred,
            sensitive_features=self.sensitive_test,
        )

        # Build per-group metrics dict
        group_metrics = {}
        for group in self.groups:
            group_metrics[group] = {
                "selection_rate": round(float(mf.by_group["selection_rate"][group]), 4),
                "tpr":            round(float(mf.by_group["tpr"][group]), 4),
                "fpr":            round(float(mf.by_group["fpr"][group]), 4),
                "precision":      round(float(mf.by_group["precision"][group]), 4),
            }

        # Overall metrics
        rates = {g: group_metrics[g]["selection_rate"] for g in self.groups}
        max_rate = max(rates.values())

        disparate_impact = {
            g: round(rates[g] / max(max_rate, 0.001), 4)
            for g in self.groups
        }
        dp_ratio = round(min(rates.values()) / max(max_rate, 0.001), 4)
        eo_gap = round(
            float(equalized_odds_difference(
                y_test, y_pred, sensitive_features=self.sensitive_test
            )), 4
        )

        verdict, severity = self._verdict(disparate_impact)

        u(80, "Finalising results...")

        dataset_name = (
            file_path.split("/")[-1]
            .replace(".csv", "")
            .replace("_", " ")
            .title()
        )

        return {
            "job_id": "placeholder",
            "dataset_name": dataset_name,
            "protected_attribute": protected_attr,
            "target_column": target_col,
            "model_accuracy": round(accuracy, 4),
            "groups": self.groups,
            "group_metrics": group_metrics,
            "overall_metrics": {
                "demographic_parity_ratio": dp_ratio,
                "equalized_odds_gap": eo_gap,
                "disparate_impact": disparate_impact,
            },
            "verdict": verdict,
            "severity": severity,
        }

    def _verdict(self, disparate_impact):
        min_di = min(disparate_impact.values())
        if min_di >= 0.9:
            return "PASS", "LOW"
        elif min_di >= 0.8:
            return "BORDERLINE", "MEDIUM"
        elif min_di >= 0.6:
            return "FAIL", "MEDIUM"
        else:
            return "FAIL", "HIGH"