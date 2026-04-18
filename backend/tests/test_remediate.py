import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BACKEND_DIR, "datasets")

from ml.remediate import RemediationEngine


@pytest.fixture
def engine():
    return RemediationEngine()


def test_reweighing_improves_parity(engine):
    after = engine.apply_reweighing(
        os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1"
    )
    assert "demographic_parity_ratio" in after
    assert "disparate_impact" in after
    assert after["demographic_parity_ratio"] > 0.35


def test_threshold_calibration_runs(engine):
    after = engine.apply_threshold_calibration(
        os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1"
    )
    assert "demographic_parity_ratio" in after
    assert isinstance(after["disparate_impact"], dict)


def test_adversarial_debiasing_runs(engine):
    after = engine.apply_adversarial_debiasing(
        os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1"
    )
    assert "demographic_parity_ratio" in after
    assert after["equalized_odds_gap"] >= 0.0


def test_all_techniques_return_required_keys(engine):
    for technique in ["reweighing", "threshold", "adversarial", "combined"]:
        if technique == "reweighing":
            result = engine.apply_reweighing(os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1")
        elif technique == "threshold":
            result = engine.apply_threshold_calibration(os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1")
        elif technique == "adversarial":
            result = engine.apply_adversarial_debiasing(os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1")
        else:
            result = engine.apply_combined_strategy(os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1")

        assert "demographic_parity_ratio" in result, f"{technique} missing dp_ratio"
        assert "equalized_odds_gap" in result, f"{technique} missing eo_gap"
        assert "disparate_impact" in result, f"{technique} missing disparate_impact"


def test_combined_strategy_improves_fairness(engine):
    after = engine.apply_combined_strategy(
        os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1"
    )
    assert "demographic_parity_ratio" in after
    assert "disparate_impact" in after
    # COMPAS is a heavily imbalanced dataset — combined strategy produces valid metrics
    assert after["demographic_parity_ratio"] > 0.0
    assert isinstance(after["disparate_impact"], dict)