"""Unit tests for forecaster_agent.py"""
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.forecaster_agent import _compute_period_cv, build_scenarios

def test_cv_period_agg():
    """CV on period-aggregated data should differ from raw"""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=20, freq='W')
    # Two stores with offset trends
    rows = []
    for s, base in [(1, 10000), (2, 5000)]:
        for i, d in enumerate(dates):
            rows.append({'Date': d, 'Store': s, 'Sales': base + i * 10})
    df = pd.DataFrame(rows)
    agg = df.groupby('Date')['Sales'].sum()
    cv_agg = _compute_period_cv(agg)
    cv_raw = _compute_period_cv(df['Sales'])
    assert cv_agg > 0
    assert cv_raw > 0
    assert cv_agg != cv_raw, "Period-agg CV should differ from raw CV"

def test_cv_constant():
    s = pd.Series([100] * 10)
    assert _compute_period_cv(s) == 0.0

def test_cv_insufficient():
    assert _compute_period_cv(pd.Series([100])) == 0.0
    assert _compute_period_cv(pd.Series([])) == 0.0

def test_cv_all_zeros():
    assert _compute_period_cv(pd.Series([0, 0, 0])) == 0.0

def test_build_scenarios_empirical():
    """With >=6 periods, should use empirical percentile"""
    hist = pd.Series([100, 110, 95, 105, 115, 90, 108, 120])
    yhat = np.array([110, 112, 115])
    result = build_scenarios(yhat, hist, cv_pct=20)
    assert 'bear' in result
    assert 'bull' in result
    assert 'method' in result
    assert result['method'] == 'empirical_percentile'

def test_build_scenarios_fallback():
    """With <6 periods, should use CV-derived fallback"""
    hist = pd.Series([100, 110, 95, 105])
    yhat = np.array([110, 112, 115])
    result = build_scenarios(yhat, hist, cv_pct=30)
    assert result['method'] == 'cv_derived_fallback'
    bear = result['bear']
    bull = result['bull']
    assert bear['spread_pct'] < 0
    assert bull['spread_pct'] > 0
    # CV=30 → bear_mult = max(0.50, 0.70) = 0.70, bull = min(2.00, 1.30) = 1.30
    assert bear['spread_pct'] >= -50.0
    assert bull['spread_pct'] <= 100.0

def test_build_scenarios_no_negative_bear():
    """Bear values should never be negative"""
    hist = pd.Series([100, 110, 95, 105, 115, 90])
    yhat = np.array([100, 100, 100])
    result = build_scenarios(yhat, hist, cv_pct=20)
    assert all(v >= 0 for v in result['bear']['values'])

def test_build_scenarios_high_cv():
    """High CV should produce wider spreads"""
    hist_low = pd.Series([100, 102, 98, 101, 99, 103] * 2)
    hist_high = pd.Series([100, 150, 80, 200, 50, 120] * 2)
    yhat = np.array([110, 112, 115])
    low = build_scenarios(yhat, hist_low, cv_pct=5)
    high = build_scenarios(yhat, hist_high, cv_pct=60)
    assert abs(high['bear']['spread_pct']) > abs(low['bear']['spread_pct'])
