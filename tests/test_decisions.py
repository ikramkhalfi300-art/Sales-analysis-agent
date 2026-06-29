"""Unit tests for generate_decisions in analyzer_agent.py"""
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.analyzer_agent import generate_decisions, decisions_to_df, get_decisions_summary

def _make_df(n_stores=5, n_weeks=52, declining_stores=None):
    """Create test dataframe with optional declining stores"""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=n_weeks, freq='W')
    rows = []
    declining_stores = declining_stores or []
    for s in range(1, n_stores + 1):
        base = 10000 + s * 2000
        for i, d in enumerate(dates):
            if s in declining_stores:
                val = base - i * 50  # declining trend
            else:
                val = base + i * 10   # growing trend
            rows.append({'Date': d, 'Store': s, 'Sales': max(1000, val)})
    return pd.DataFrame(rows)

def test_all_stores_have_decisions():
    df = _make_df(5, 104)
    decisions = generate_decisions(df, 'Date', 'Sales', 'Store')
    assert len(decisions) == 5
    assert all(d.trend_pct > 0 or ('Stable' in d.trend and abs(d.trend_pct) <= 5) for d in decisions)

def test_recent_decline_triggers_warning():
    """A store that ranks high but recently declined should get downgraded & WARNING"""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=104, freq='W')
    rows = []
    for s in range(1, 6):
        base = 10000 * s  # store 4 = 40000, store 5 = 50000 (top)
        vals = np.linspace(base, base * 1.5, 80)  # grow first 80 weeks
        vals = np.append(vals, np.linspace(base * 1.5, base * 0.8, 24))  # decline last 24 weeks
        for i, d in enumerate(dates):
            rows.append({'Date': d, 'Store': s, 'Sales': max(100, vals[i] + np.random.normal(0, 500))})
    df = pd.DataFrame(rows)
    decisions = generate_decisions(df, 'Date', 'Sales', 'Store')
    top = [d for d in decisions if d.unit == '5.0']
    # Store 5 is top-ranked ($50000 base) but had a recent -30%+ swing
    if top:
        flags = [kw for kw in ['WARNING', 'CRITICAL'] if kw in top[0].assessment]
        assert len(flags) > 0, f"Expected WARNING or CRITICAL in assessment, got: {top[0].assessment}"
    else:
        assert False, "Store 5 not found in decisions"

def test_no_group_col():
    df = _make_df(5, 12)
    decisions = generate_decisions(df, 'Date', 'Sales', None)
    assert len(decisions) == 0

def test_invalid_group_col():
    df = _make_df(5, 12)
    decisions = generate_decisions(df, 'Date', 'Sales', 'NonExistent')
    assert len(decisions) == 0

def test_decisions_to_df():
    df = _make_df(3, 20)
    decisions = generate_decisions(df, 'Date', 'Sales', 'Store')
    result_df = decisions_to_df(decisions)
    assert result_df is not None
    assert len(result_df) == 3
    assert 'Rating' in result_df.columns
    assert 'Decision' in result_df.columns

def test_decisions_summary():
    df = _make_df(5, 20)
    decisions = generate_decisions(df, 'Date', 'Sales', 'Store')
    summary = get_decisions_summary(decisions)
    assert summary['total_units'] == 5
    assert isinstance(summary.get('total_impact'), (int, float))

def test_all_stores_declining():
    """All stores declining should produce correct decisions"""
    df = _make_df(4, 104, declining_stores=[1, 2, 3, 4])
    decisions = generate_decisions(df, 'Date', 'Sales', 'Store')
    assert len(decisions) == 4
    # At least 1 store should show Declining (-X.X%) with enough decline
    declining = [d for d in decisions if 'Declining' in d.trend or d.trend_pct < -5]
    assert len(declining) >= 1
