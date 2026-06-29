"""Unit tests for _calc_trend in analyzer_agent.py"""
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.analyzer_agent import _calc_trend

def test_growing():
    s = pd.Series([100, 110, 120, 130, 140, 150])
    label, pct = _calc_trend(s)
    assert label == "Growing", f"Expected Growing, got {label}"
    assert pct > 5

def test_declining():
    s = pd.Series([150, 140, 130, 120, 110, 100])
    label, pct = _calc_trend(s)
    assert label == "Declining", f"Expected Declining, got {label}"
    assert pct < -5

def test_stable():
    s = pd.Series([100, 102, 101, 103, 100, 101])
    label, pct = _calc_trend(s)
    assert label == "Stable", f"Expected Stable, got {label}"

def test_empty():
    label, pct = _calc_trend(pd.Series([], dtype=float))
    assert label == "Stable"
    assert pct == 0.0

def test_single():
    label, pct = _calc_trend(pd.Series([100]))
    assert label == "Stable"
    assert pct == 0.0

def test_two_values_growing():
    label, pct = _calc_trend(pd.Series([100, 200]))
    assert label == "Growing"
    assert pct > 0

def test_two_values_declining():
    label, pct = _calc_trend(pd.Series([200, 100]))
    assert label == "Declining"
    assert pct < 0

def test_all_zeros():
    label, pct = _calc_trend(pd.Series([0, 0, 0, 0]))
    assert label == "Stable"
    assert pct == 0.0

def test_negative_values_growing():
    s = pd.Series([-100, -80, -60, -40])
    label, pct = _calc_trend(s)
    assert label == "Growing"

def test_noisy_stable():
    np.random.seed(42)
    s = pd.Series(np.random.normal(100, 2, 20))
    label, pct = _calc_trend(s)
    assert label == "Stable"
