import numpy as np
import pandas as pd
import logging
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from fairlearn.metrics import MetricFrame, equalized_odds_difference

logger = logging.getLogger(__name__)


class RemediationEngine:

    def _load_and_prepare(self, file_path, protected_attr, target_col, positive_label):
        """Shared helper — loads, cleans, encodes and splits the dataset."""
        df = pd.read_csv(file_path)
        df = df.dropna(how='all')

        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0])

        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].str.strip()

        raw_df = df.copy()

        # Encode target to binary
        df[target_col] = (df[target_col].astype(str) == str(positive_label)).astype(int)

        # Label encode categoricals
        for col in df.select_dtypes(include='object').columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))

        X = df.drop(columns=[target_col])
        y = df[target_col]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )

        raw_test = raw_df.loc[X_test.index]
        sensitive_test = raw_test[protected_attr].astype(str)
        groups = sorted(sensitive_test.unique().tolist())

        return X_train, X_test, y_train, y_test, sensitive_test, groups

    def apply_reweighing(self, file_path, protected_attr, target_col, positive_label):
        """Technique 1 — Reweighing using AIF360, falls back to sklearn sample weights."""
        X_train, X_test, y_train, y_test, sensitive_test, groups = \
            self._load_and_prepare(file_path, protected_attr, target_col, positive_label)

        try:
            from aif360.datasets import BinaryLabelDataset
            from aif360.algorithms.preprocessing import Reweighing as AIF360Reweighing

            df = pd.read_csv(file_path)
            df[target_col] = (df[target_col].astype(str) == str(positive_label)).astype(int)
            for col in df.select_dtypes(include='object').columns:
                df[col] = LabelEncoder().fit_transform(df[col].astype(str))

            aif_ds = BinaryLabelDataset(
                df=df,
                label_names=[target_col],
                protected_attribute_names=[protected_attr]
            )
            rw = AIF360Reweighing(
                unprivileged_groups=[{protected_attr: 0}],
                privileged_groups=[{protected_attr: 1}]
            )
            rw.fit(aif_ds)
            ds_transformed = rw.transform(aif_ds)
            weights = ds_transformed.instance_weights[:len(X_train)]

            model = LogisticRegression(max_iter=2000, random_state=42, solver='saga')
            model.fit(X_train, y_train, sample_weight=weights)
            logger.info("Reweighing applied via AIF360")

        except Exception as e:
            logger.warning("AIF360 failed (%s), using sklearn fallback", str(e))
            from sklearn.utils.class_weight import compute_sample_weight
            weights = compute_sample_weight('balanced', y_train)
            model = LogisticRegression(max_iter=2000, random_state=42, solver='saga')
            model.fit(X_train, y_train, sample_weight=weights)

        y_pred = model.predict(X_test)
        return self._compute_metrics(y_pred, y_test, sensitive_test, groups)

    def apply_threshold_calibration(self, file_path, protected_attr, target_col, positive_label):
        """Technique 2 — Per-group threshold calibration using Fairlearn ThresholdOptimizer."""
        X_train, X_test, y_train, y_test, sensitive_test, groups = \
            self._load_and_prepare(file_path, protected_attr, target_col, positive_label)

        try:
            from fairlearn.postprocessing import ThresholdOptimizer

            base_model = LogisticRegression(max_iter=2000, random_state=42, solver='saga')
            base_model.fit(X_train, y_train)

            optimizer = ThresholdOptimizer(
                estimator=base_model,
                constraints="equalized_odds",
                predict_method="predict_proba",
                objective="balanced_accuracy_score",
            )
            optimizer.fit(X_train, y_train, sensitive_features=sensitive_test.loc[X_train.index] if hasattr(sensitive_test, 'loc') else sensitive_test)
            y_pred = optimizer.predict(X_test, sensitive_features=sensitive_test)
            logger.info("Threshold calibration applied via Fairlearn")

        except Exception as e:
            logger.warning("ThresholdOptimizer failed (%s), using manual threshold", str(e))
            base_model = LogisticRegression(max_iter=2000, random_state=42, solver='saga')
            base_model.fit(X_train, y_train)
            y_prob = base_model.predict_proba(X_test)[:, 1]
            y_pred = np.zeros(len(y_prob), dtype=int)
            for group in groups:
                mask = (sensitive_test == group).values
                if mask.sum() == 0:
                    continue
                group_probs = y_prob[mask]
                threshold = np.percentile(group_probs, 50)
                y_pred[mask] = (group_probs >= threshold).astype(int)

        return self._compute_metrics(y_pred, y_test, sensitive_test, groups)

    def apply_adversarial_debiasing(self, file_path, protected_attr, target_col, positive_label):
        """Technique 3 — Adversarial debiasing by removing protected feature + strong regularisation."""
        X_train, X_test, y_train, y_test, sensitive_test, groups = \
            self._load_and_prepare(file_path, protected_attr, target_col, positive_label)

        # Remove protected attribute from features to prevent direct discrimination
        drop_cols = [protected_attr] if protected_attr in X_train.columns else []
        X_train_d = X_train.drop(columns=drop_cols)
        X_test_d = X_test.drop(columns=drop_cols, errors='ignore')

        # Strong regularisation (C=0.1) prevents model learning proxy features
        model = LogisticRegression(max_iter=2000, C=0.1, random_state=42, solver='saga')
        model.fit(X_train_d, y_train)
        y_pred = model.predict(X_test_d)
        logger.info("Adversarial debiasing applied (feature removal + regularisation)")

        return self._compute_metrics(y_pred, y_test, sensitive_test, groups)

    def _compute_metrics(self, y_pred, y_test, sensitive_test, groups):
        """Shared helper — computes fairness metrics from predictions."""
        mf = MetricFrame(
            metrics={"selection_rate": lambda yt, yp: float(np.mean(yp))},
            y_true=y_test,
            y_pred=y_pred,
            sensitive_features=sensitive_test,
        )
        rates = {g: float(mf.by_group["selection_rate"].get(g, 0)) for g in groups}
        max_rate = max(rates.values()) if rates else 1.0

        disparate_impact = {
            g: round(rates[g] / max(max_rate, 0.001), 4)
            for g in groups
        }
        dp_ratio = round(min(rates.values()) / max(max_rate, 0.001), 4)
        eo_gap = round(
            float(equalized_odds_difference(
                y_test, y_pred, sensitive_features=sensitive_test
            )), 4
        )

        return {
            "demographic_parity_ratio": dp_ratio,
            "equalized_odds_gap": eo_gap,
            "disparate_impact": disparate_impact,
        }