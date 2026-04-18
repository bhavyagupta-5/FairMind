import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BACKEND_DIR, "datasets")

from ml.audit import AuditEngine


def test_compas_verdict_is_fail():
    engine = AuditEngine()
    results = engine.run(os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1")
    assert results["verdict"] == "FAIL", f"Expected FAIL, got {results['verdict']}"
    assert results["overall_metrics"]["demographic_parity_ratio"] < 0.8


def test_compas_severity_is_high():
    engine = AuditEngine()
    results = engine.run(os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1")
    assert results["severity"] in ["MEDIUM", "HIGH"]


def test_all_groups_have_required_metrics():
    engine = AuditEngine()
    results = engine.run(os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1")
    for group in results["groups"]:
        m = results["group_metrics"][group]
        assert "selection_rate" in m
        assert "tpr" in m
        assert "fpr" in m
        assert "precision" in m
        assert 0.0 <= m["selection_rate"] <= 1.0
        assert 0.0 <= m["tpr"] <= 1.0
        assert 0.0 <= m["fpr"] <= 1.0


def test_overall_metrics_present():
    engine = AuditEngine()
    results = engine.run(os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1")
    om = results["overall_metrics"]
    assert "demographic_parity_ratio" in om
    assert "equalized_odds_gap" in om
    assert "disparate_impact" in om
    assert isinstance(om["disparate_impact"], dict)


def test_adult_income_runs():
    engine = AuditEngine()
    results = engine.run(os.path.join(DATASETS_DIR, "adult.csv"), "sex", "income", ">50K")
    assert "groups" in results
    assert len(results["groups"]) >= 2
    assert results["verdict"] in ["PASS", "BORDERLINE", "FAIL"]


def test_at_least_two_groups_detected():
    engine = AuditEngine()
    results = engine.run(os.path.join(DATASETS_DIR, "compas.csv"), "race", "two_year_recid", "1")
    assert len(results["groups"]) >= 2