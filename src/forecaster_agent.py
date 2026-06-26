"""
forecaster.py — Production-Grade Forecasting Engine v2.0
Fixes Applied:
  FIX-1: get_forecast_summary() now receives prophet_data to correctly isolate future rows
  FIX-2: CV computed on aggregated period totals, not raw transaction rows
  FIX-3: Bear/Bull multipliers derived from empirical historical percentiles (10th/90th)
  FIX-4: Scenario probabilities replaced with data-driven spread labels (no fake %)
  FIX-5: last_historical_date stored in forecast.attrs for downstream use
  FIX-6: Model type stored in attrs for UI transparency
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing


# ─── VOLATILITY CLASSIFIER ────────────────────────────────
def classify_volatility(cv_pct: float) -> dict:
    if cv_pct < 20:
        return {
            "level": "Low",
            "risk": "Revenue is highly predictable. Forecasts are reliable.",
            "color": "green", "badge": "🟢"
        }
    elif cv_pct < 40:
        return {
            "level": "Moderate",
            "risk": "Some revenue fluctuation. Forecasts are directionally reliable.",
            "color": "amber", "badge": "🟡"
        }
    elif cv_pct < 70:
        return {
            "level": "High",
            "risk": "Significant revenue swings. Treat forecasts as directional only.",
            "color": "red", "badge": "🔴"
        }
    else:
        return {
            "level": "Extreme",
            "risk": "Revenue is highly volatile. Forecasts carry low reliability — investigate root causes before acting.",
            "color": "red", "badge": "🚨"
        }


# ─── CONFIDENCE ADJUSTER ─────────────────────────────────
def compute_confidence_level(n_periods: int, cv_pct: float, has_qa_errors: bool = False) -> str:
    if has_qa_errors or cv_pct > 60 or n_periods < 20:
        return "Low"
    elif cv_pct > 35 or n_periods < 52:
        return "Medium"
    else:
        return "High"


# ─── SANITY CHECK ────────────────────────────────────────
def sanity_check_forecast(avg_forecast: float, avg_historical: float, peak_historical: float) -> dict:
    warnings = []
    if avg_historical > 0:
        growth_ratio = avg_forecast / avg_historical
        if growth_ratio > 3.0:
            warnings.append(
                f"⚠️ FORECAST WARNING: Projected average (${avg_forecast:,.0f}) is "
                f"{growth_ratio:.1f}x current historical average (${avg_historical:,.0f}). "
                f"Possible causes: model overfitting, data anomaly, or unit mismatch. "
                f"Treat as directional signal only — do not use for operational budgeting."
            )
    if peak_historical > 0:
        peak_ratio = avg_forecast / peak_historical
        if peak_ratio > 1.5:
            warnings.append(
                f"⚠️ CEILING WARNING: Forecast average exceeds the best historical period by "
                f"{(peak_ratio - 1) * 100:.0f}%. Verify model assumptions before committing resources."
            )
    return {"passed": len(warnings) == 0, "warnings": warnings}


# ─── DATE VALIDATION ─────────────────────────────────────
def validate_forecast_dates(forecast_df: pd.DataFrame, last_historical_date: pd.Timestamp) -> pd.DataFrame:
    today = pd.Timestamp.now().normalize()
    forecast_df = forecast_df[forecast_df['ds'] > last_historical_date].copy()
    forecast_df['is_past'] = forecast_df['ds'] < today
    return forecast_df


# ─── FIX-3: EMPIRICAL SCENARIO BUILDER ───────────────────
def build_scenarios(
    yhat: np.ndarray,
    historical_series: pd.Series,
    cv_pct: float
) -> dict:
    """
    FIX-3: Bear/Bull bounds derived from the 10th and 90th percentile
    of historical period-over-period % changes — not hardcoded multipliers.
    FIX-4: Probabilities removed. Replaced with spread labels that are honest.
    """
    pct_changes = historical_series.pct_change().dropna()

    # Need at least 6 observations to compute meaningful percentiles
    if len(pct_changes) >= 6:
        p10 = float(np.percentile(pct_changes, 10))  # 10th pct historical shock
        p90 = float(np.percentile(pct_changes, 90))  # 90th pct historical surge

        # Compound the shock over forecast horizon (conservative: single-period shock)
        bear_mult = max(0.40, 1 + p10)
        bull_mult = min(2.50, 1 + p90)

        bear_label = f"Historical 10th-percentile period shock ({p10*100:+.1f}%)"
        bull_label = f"Historical 90th-percentile period surge ({p90*100:+.1f}%)"
        method = "empirical_percentile"
    else:
        # Fallback to CV-scaled multipliers when insufficient history
        if cv_pct < 30:
            bear_mult, bull_mult = 0.85, 1.15
        elif cv_pct < 60:
            bear_mult, bull_mult = 0.75, 1.25
        else:
            bear_mult, bull_mult = 0.60, 1.40
        bear_label = f"CV-scaled (data < 6 periods, CV={cv_pct:.0f}%)"
        bull_label = f"CV-scaled (data < 6 periods, CV={cv_pct:.0f}%)"
        method = "cv_scaled_fallback"

    bear_values = np.maximum(yhat * bear_mult, 0)
    bull_values = yhat * bull_mult

    # FIX-4: No fake probabilities — use spread description instead
    bear_spread_pct = (bear_mult - 1) * 100
    bull_spread_pct = (bull_mult - 1) * 100

    return {
        "bear": {
            "values":       bear_values,
            "multiplier":   round(bear_mult, 4),
            "spread_pct":   round(bear_spread_pct, 1),
            "label":        "Bear Case (Downside)",
            "basis":        bear_label,
            "assumption":   "Demand softens or adverse market conditions materialize",
        },
        "base": {
            "values":       yhat,
            "multiplier":   1.0,
            "spread_pct":   0.0,
            "label":        "Base Case (Trend Continuation)",
            "basis":        "Holt-Winters model forecast — current trend continues",
            "assumption":   "No major market disruption in the forecast window",
        },
        "bull": {
            "values":       bull_values,
            "multiplier":   round(bull_mult, 4),
            "spread_pct":   round(bull_spread_pct, 1),
            "label":        "Bull Case (Upside)",
            "basis":        bull_label,
            "assumption":   "Favorable conditions or successful strategic initiatives",
        },
        "method": method,
        "bear_spread_pct": round(bear_spread_pct, 1),
        "bull_spread_pct": round(bull_spread_pct, 1),
    }


# ─── LEADING INDICATORS ──────────────────────────────────
def build_leading_indicators(
    forecast_df: pd.DataFrame,
    avg_historical: float,
    group_col_avg: float = None
) -> list:
    # Only use rows that are genuinely future
    if 'is_past' in forecast_df.columns:
        future = forecast_df[~forecast_df['is_past']].copy()
    else:
        future = forecast_df.copy()

    if len(future) < 3:
        return []

    p3_cumulative = float(future.head(3)['yhat'].sum())
    weekly_target = float(future['yhat'].mean())

    indicators = [
        {
            "signal": "Revenue Trajectory",
            "metric": "Cumulative revenue by end of Period 3",
            "target": f"${p3_cumulative:,.0f}",
            "alert":  f"If below ${p3_cumulative * 0.85:,.0f} → revise forecast downward",
            "action": "Investigate demand-side causes before implementing growth initiatives",
        },
        {
            "signal": "Period Average Check",
            "metric": "Average revenue per period",
            "target": f"${weekly_target:,.0f}/period",
            "alert":  f"If drops below ${weekly_target * 0.80:,.0f} → pricing or volume erosion signal",
            "action": "Review segment performance and check for demand erosion",
        },
        {
            "signal": "Volatility Monitor",
            "metric": "Rolling deviation of actual vs forecast",
            "target": "Actual should track within ±20% of base case",
            "alert":  "If 3 consecutive periods miss target → model recalibration required",
            "action": "Re-run forecast with updated actuals before committing resources",
        },
    ]

    if group_col_avg is not None and group_col_avg > 0:
        indicators.append({
            "signal": "Top Segment Health",
            "metric": "Top segment average per period",
            "target": f">${group_col_avg * 0.90:,.0f}/period",
            "alert":  f"Drop below ${group_col_avg * 0.75:,.0f} → pricing pressure or demand loss",
            "action": "Audit top segment pricing and competitive positioning immediately",
        })

    return indicators


# ═══════════════════════════════════════════════════════════
# MAIN FORECAST FUNCTION
# ═══════════════════════════════════════════════════════════
def train_and_forecast(
    df,
    weeks: int = 12,
    date_col: str = 'Date',
    sales_col: str = 'Weekly_Sales',
    has_qa_errors: bool = False,
):
    # ── Step 1: Aggregate to period level ─────────────────
    weekly = (
        df.groupby(date_col)[sales_col]
        .sum()
        .reset_index()
        .sort_values(date_col)
    )
    weekly.columns = ['ds', 'y']
    weekly = weekly.dropna(subset=['y'])
    weekly = weekly[weekly['y'] > 0].reset_index(drop=True)

    # ── FIX-2: CV on aggregated period totals ─────────────
    # CV must reflect period-level revenue volatility, not row-level noise
    def _compute_period_cv(series: pd.Series) -> float:
        if len(series) < 2:
            return 0.0
        mean_val = float(series.mean())
        std_val  = float(series.std())
        if mean_val <= 0:
            return 0.0
        return round(std_val / mean_val * 100, 2)

    # ── Guard: empty data ─────────────────────────────────
    def _empty_result(msg: str):
        efc = pd.DataFrame(columns=['ds', 'yhat', 'yhat_lower', 'yhat_upper'])
        efc.attrs.update({
            'scenarios': {}, 'cv_pct': 0, 'avg_hist': 0, 'peak_hist': 0,
            'confidence': 'Low', 'model_type': 'none',
            'last_historical_date': pd.Timestamp.now(),
            'volatility': {'level': 'Unknown', 'risk': 'No valid data', 'badge': '❓'},
            'sanity': {'passed': False, 'warnings': [msg]},
        })
        return efc, pd.DataFrame(columns=['ds', 'y'])

    if len(weekly) == 0:
        return _empty_result('No valid sales data found after cleaning.')
    if len(weekly) < 3:
        efc, _ = _empty_result(f'Insufficient data: only {len(weekly)} periods. Minimum 3 required.')
        efc.attrs['avg_hist']  = float(weekly['y'].mean()) if len(weekly) > 0 else 0
        efc.attrs['peak_hist'] = float(weekly['y'].max())  if len(weekly) > 0 else 0
        return efc, weekly

    # ── Step 2: Prepare time series ───────────────────────
    series = weekly.set_index('ds')['y'].copy()
    try:
        series.index = pd.DatetimeIndex(series.index).to_period('W').to_timestamp()
    except Exception:
        pass

    n           = len(series)
    avg_hist    = float(series.mean())
    peak_hist   = float(series.max())
    last_date   = pd.Timestamp(weekly['ds'].max())

    # FIX-2: CV computed on the aggregated series (period totals)
    cv_pct = _compute_period_cv(series)

    std_hist = float(series.std()) if n > 1 and series.std() > 0 else avg_hist * 0.1

    # ── Step 3: Model selection and training ──────────────
    model      = None
    model_type = 'unknown'

    try:
        if n >= 104:
            model = ExponentialSmoothing(
                series, trend='add', seasonal='add', seasonal_periods=52
            ).fit(optimized=True)
            model_type = 'HW_seasonal_52'
        elif n >= 26:
            model = ExponentialSmoothing(
                series, trend='add', seasonal='add', seasonal_periods=26
            ).fit(optimized=True)
            model_type = 'HW_seasonal_26'
        elif n >= 4:
            model = ExponentialSmoothing(
                series, trend='add', seasonal=None
            ).fit(optimized=True)
            model_type = 'HW_trend_only'
        else:
            model = ExponentialSmoothing(
                series, trend=None, seasonal=None
            ).fit(optimized=True)
            model_type = 'HW_level_only'
    except Exception:
        try:
            model = ExponentialSmoothing(
                series, trend='add', seasonal=None
            ).fit(optimized=True)
            model_type = 'HW_trend_fallback'
        except Exception:
            try:
                model = ExponentialSmoothing(
                    series, trend=None, seasonal=None
                ).fit(optimized=True)
                model_type = 'HW_level_fallback'
            except Exception as e:
                # Last resort: mean forecast
                avg_val = float(series.mean())
                try:
                    future_dates = pd.date_range(
                        start=last_date + pd.Timedelta(weeks=1),
                        periods=weeks, freq='W'
                    )
                except Exception:
                    future_dates = pd.date_range(
                        start=pd.Timestamp.now() + pd.Timedelta(weeks=1),
                        periods=weeks, freq='W'
                    )

                scenarios = build_scenarios(
                    np.array([avg_val] * weeks), series, cv_pct
                )
                forecast_df = pd.DataFrame({
                    'ds':         future_dates,
                    'yhat':       scenarios['base']['values'],
                    'yhat_lower': scenarios['bear']['values'],
                    'yhat_upper': scenarios['bull']['values'],
                    'is_past':    [False] * weeks,
                })
                historical    = weekly.copy()
                full_forecast = pd.concat([
                    historical.rename(columns={'y': 'yhat'})[['ds', 'yhat']].assign(
                        yhat_lower=lambda x: x['yhat'],
                        yhat_upper=lambda x: x['yhat'],
                        is_past=False
                    ),
                    forecast_df,
                ], ignore_index=True)

                full_forecast.attrs.update({
                    'scenarios':            scenarios,
                    'cv_pct':               cv_pct,
                    'avg_hist':             avg_hist,
                    'peak_hist':            peak_hist,
                    'confidence':           'Low',
                    'model_type':           'mean_fallback',
                    'last_historical_date': last_date,
                    'volatility':           classify_volatility(cv_pct),
                    'sanity': {
                        'passed': False,
                        'warnings': [f'Model fitting failed ({str(e)}). Using mean forecast as fallback.']
                    },
                })
                return full_forecast, historical

    # ── Step 4: Generate forecast values ──────────────────
    forecast_values = model.forecast(weeks)

    try:
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(weeks=1),
            periods=weeks, freq='W'
        )
    except Exception:
        future_dates = pd.date_range(
            start=pd.Timestamp(last_date) + pd.Timedelta(weeks=1),
            periods=weeks, freq='W'
        )

    # ── Step 5: FIX-3 — Build empirical scenarios ─────────
    scenarios = build_scenarios(forecast_values.values, series, cv_pct)

    forecast_df = pd.DataFrame({
        'ds':         future_dates,
        'yhat':       scenarios['base']['values'],
        'yhat_lower': scenarios['bear']['values'],
        'yhat_upper': scenarios['bull']['values'],
    })

    # ── Step 6: Date validation ───────────────────────────
    forecast_df = validate_forecast_dates(forecast_df, last_date)

    # ── Step 7: Build full timeline ───────────────────────
    historical    = weekly.copy()
    full_forecast = pd.concat([
        historical.rename(columns={'y': 'yhat'})[['ds', 'yhat']].assign(
            yhat_lower=lambda x: x['yhat'],
            yhat_upper=lambda x: x['yhat'],
            is_past=False
        ),
        forecast_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'is_past']],
    ], ignore_index=True)

    # ── Step 8: Attach metadata — FIX-5 & FIX-6 ──────────
    full_forecast.attrs.update({
        'scenarios':            scenarios,
        'cv_pct':               cv_pct,
        'avg_hist':             avg_hist,
        'peak_hist':            peak_hist,
        'confidence':           compute_confidence_level(n, cv_pct, has_qa_errors),
        'model_type':           model_type,          # FIX-6: stored for UI transparency
        'last_historical_date': last_date,           # FIX-5: stored for correct future slice
        'volatility':           classify_volatility(cv_pct),
        'sanity':               sanity_check_forecast(
                                    float(forecast_values.mean()), avg_hist, peak_hist
                                ),
    })

    return full_forecast, historical


# ═══════════════════════════════════════════════════════════
# FORECAST SUMMARY — FIX-1: uses last_historical_date
# ═══════════════════════════════════════════════════════════
def get_forecast_summary(
    forecast: pd.DataFrame,
    prophet_data: pd.DataFrame = None,
    group_col_avg: float = None
) -> dict:
    """
    FIX-1: Accepts prophet_data (historical rows) to correctly isolate
    future forecast rows. No longer relies on forecast['ds'].max() trick
    which always returned an empty DataFrame.
    """

    # Guard: empty forecast
    if forecast is None or len(forecast) == 0:
        return {
            'next_4_weeks': 0, 'next_8_weeks': 0, 'next_12_weeks': 0,
            'peak_week': 'N/A', 'peak_expected_sales': 0,
            'bear_12_weeks': 0, 'bull_12_weeks': 0,
            'bear_spread_pct': -25.0, 'bull_spread_pct': 25.0,
            'scenario_method': 'none',
            'confidence_level': 'Low',
            'volatility': {'level': 'Unknown', 'risk': 'No data', 'badge': '❓'},
            'sanity_check': {'passed': False, 'warnings': ['No forecast data available']},
            'cv_pct': 0, 'avg_historical': 0,
            'model_type': 'none',
            'leading_indicators': [], 'decision_rule': '',
        }

    today = pd.Timestamp.now().normalize()

    # FIX-1: Determine last historical date from attrs or prophet_data
    last_hist_date = forecast.attrs.get('last_historical_date', None)

    if last_hist_date is None and prophet_data is not None and len(prophet_data) > 0:
        ds_col = 'ds' if 'ds' in prophet_data.columns else prophet_data.columns[0]
        last_hist_date = pd.Timestamp(prophet_data[ds_col].max())

    if last_hist_date is None:
        # Fallback: use today as the cutoff (anything before today = historical)
        last_hist_date = today - pd.Timedelta(days=1)

    last_hist_date = pd.Timestamp(last_hist_date)

    # FIX-1: Correctly isolate future rows
    future = forecast[forecast['ds'] > last_hist_date].copy()

    # Further filter to rows that are not in the past (relative to today)
    future_from_today = future[future['ds'] >= today].copy()

    # If all forecast rows are already in the past, use all future rows for metrics
    if len(future_from_today) == 0:
        future_for_metrics = future.copy()
    else:
        future_for_metrics = future_from_today.copy()

    n_future = len(future_for_metrics)

    if n_future == 0:
        # Absolute fallback: use last rows of full forecast
        future_for_metrics = forecast.tail(12).copy()
        n_future = len(future_for_metrics)

    # ── Core forecast figures ─────────────────────────────
    next_4  = float(future_for_metrics.head(min(4,  n_future))['yhat'].sum())
    next_8  = float(future_for_metrics.head(min(8,  n_future))['yhat'].sum())
    next_12 = float(future_for_metrics.head(min(12, n_future))['yhat'].sum())

    # ── Scenario values from attrs ────────────────────────
    scenarios = forecast.attrs.get('scenarios', {})

    if scenarios and 'bear' in scenarios and 'bull' in scenarios:
        bear_vals = scenarios['bear']['values']
        bull_vals = scenarios['bull']['values']
        n_use     = min(12, n_future, len(bear_vals), len(bull_vals))
        bear_12   = float(np.sum(bear_vals[:n_use]))
        bull_12   = float(np.sum(bull_vals[:n_use]))
        bear_spread_pct  = scenarios.get('bear_spread_pct', -25.0)
        bull_spread_pct  = scenarios.get('bull_spread_pct',  25.0)
        scenario_method  = scenarios.get('method', 'unknown')
    else:
        # No scenarios available — derive from CV
        cv_pct_fallback = forecast.attrs.get('cv_pct', 30)
        bear_mult = 0.75 if cv_pct_fallback < 60 else 0.60
        bull_mult = 1.25 if cv_pct_fallback < 60 else 1.40
        bear_12   = next_12 * bear_mult
        bull_12   = next_12 * bull_mult
        bear_spread_pct  = (bear_mult - 1) * 100
        bull_spread_pct  = (bull_mult - 1) * 100
        scenario_method  = 'cv_scaled_fallback'

    # ── Peak detection ────────────────────────────────────
    if len(future_for_metrics) > 0 and future_for_metrics['yhat'].notna().any():
        peak_idx = future_for_metrics['yhat'].idxmax()
        peak_dt  = future_for_metrics.loc[peak_idx, 'ds']
        peak_val = float(future_for_metrics.loc[peak_idx, 'yhat'])
    else:
        peak_dt  = today + pd.Timedelta(weeks=4)
        peak_val = 0.0

    try:
        peak_str = pd.Timestamp(peak_dt).date().isoformat()
    except Exception:
        peak_str = str(peak_dt)

    # ── Pull metadata from attrs ──────────────────────────
    cv_pct      = forecast.attrs.get('cv_pct', 0)
    avg_hist    = forecast.attrs.get('avg_hist', 0)
    confidence  = forecast.attrs.get('confidence', 'Medium')
    volatility  = forecast.attrs.get('volatility', classify_volatility(cv_pct))
    sanity      = forecast.attrs.get('sanity', {'passed': True, 'warnings': []})
    model_type  = forecast.attrs.get('model_type', 'unknown')

    # ── Leading indicators ────────────────────────────────
    # Use future_from_today for leading indicators (real future only)
    li_df = future_from_today if len(future_from_today) >= 3 else future_for_metrics
    leading_indicators = build_leading_indicators(li_df, avg_hist, group_col_avg)

    # ── Decision rule (honest, data-driven) ───────────────
    decision_rule = (
        f"Plan operations around the BASE CASE (${next_12:,.0f} over 12 periods). "
        f"Stress-test budgets against the BEAR CASE (${bear_12:,.0f}, "
        f"{bear_spread_pct:+.0f}% from base — derived from historical downside). "
        f"Only allocate resources for BULL CASE (${bull_12:,.0f}) if leading indicators "
        f"confirm upward trajectory in the first 3 periods."
    )

    return {
        'next_4_weeks':        round(next_4,  2),
        'next_8_weeks':        round(next_8,  2),
        'next_12_weeks':       round(next_12, 2),
        'peak_week':           peak_str,
        'peak_expected_sales': round(peak_val, 2),
        'bear_12_weeks':       round(bear_12, 2),
        'bull_12_weeks':       round(bull_12, 2),
        # FIX-4: No fake probabilities — use spread percentages instead
        'bear_spread_pct':     round(bear_spread_pct, 1),
        'bull_spread_pct':     round(bull_spread_pct, 1),
        'scenario_method':     scenario_method,
        # Legacy keys kept for backward compatibility with app.py display
        'bear_probability':    0.0,   # deprecated — do not use for display
        'base_probability':    0.0,   # deprecated — do not use for display
        'bull_probability':    0.0,   # deprecated — do not use for display
        'confidence_level':    confidence,
        'volatility':          volatility,
        'sanity_check':        sanity,
        'cv_pct':              round(cv_pct, 1),
        'avg_historical':      round(avg_hist, 2),
        'model_type':          model_type,
        'leading_indicators':  leading_indicators,
        'decision_rule':       decision_rule,
    }