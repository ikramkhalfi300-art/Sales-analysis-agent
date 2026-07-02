"""Unit tests for _build_peak_rec in pdf_gen_agent.py"""
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.pdf_gen_agent import _build_peak_rec, _get_peak_urgency

def _make_ctx(peak_week_str):
    return {
        'fc12': 100000, 'bear_12': 85000, 'bear_spread': -15.0,
        'bull_12': 115000, 'bull_spread': 15.0, 'peak_week': peak_week_str,
        'peak_fc': 25000, 'action_deadline_7': '2026-07-06',
        'action_deadline_30': '2026-07-29',
        'avg_per_period': 5000,
    }

def test_peak_past():
    ctx = _make_ctx('2020-01-01')
    rec = _build_peak_rec(ctx)
    assert rec['title'] == "Priority 3 — Post-Peak Performance Analysis"
    assert 'Post-Peak' in rec['title']
    assert rec['style'] == 'amber'

def test_peak_within_90():
    ctx = _make_ctx('2026-08-01')
    rec = _build_peak_rec(ctx)
    assert rec['title'] == "Priority 3 — Align with Forecast Peak"
    assert rec['style'] == 'green'

def test_peak_far_future():
    ctx = _make_ctx('2027-06-01')
    rec = _build_peak_rec(ctx)
    assert "Long-Term" in rec['title']
    assert rec['style'] == 'blue'

def test_peak_missing():
    ctx = _make_ctx('N/A')
    rec = _build_peak_rec(ctx)
    assert "Long-Term" in rec['title']

def test_peak_urgency_past():
    result = _get_peak_urgency('2020-01-01')
    assert result['is_past'] == True
    assert result['level'] == 'past'

def test_peak_urgency_planned():
    # A date far in the future
    result = _get_peak_urgency('2027-12-25')
    assert result['is_past'] == False
    assert result['level'] == 'planned'

def test_peak_urgency_invalid():
    result = _get_peak_urgency('not-a-date')
    assert result['level'] == 'unknown'
    assert result['days_left'] is None
