"""
forecaster.py — Enhanced Forecasting Engine v2.1
FIX 1: get_forecast_summary — السطر 366 كان:
        forecast[forecast['ds'] > forecast['ds'].max()]
        هذا دائماً فارغ → يرجع tail(12) من البيانات التاريخية الكاملة
        الحل: حفظ last_historical_date في attrs واستخدامه للفصل
FIX 2: Volatility — CV=52.6% كانت تظهر "Low" في بعض الأماكن
        الحل: إعادة حساب volatility مباشرة من cv_pct في get_forecast_summary
FIX 3: Confidence — cv > 60 كان الحد → "High" عند CV=52%
        الحل: cv > 40 → Medium
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing


# ─── VOLATILITY CLASSIFIER ────────────────────────────────
def classify_volatility(cv_pct: float) -> dict:
    if cv_pct < 20:
        return {"level": "Low",      "risk": "Revenue is highly predictable. Forecasts are reliable.",                                                          "color": "green", "badge": "🟢"}
    elif cv_pct < 40:
        return {"level": "Moderate", "risk": "Some revenue fluctuation. Forecasts are directionally reliable.",                                                  "color": "amber", "badge": "🟡"}
    elif cv_pct < 70:
        return {"level": "High",     "risk": "Significant revenue swings. Treat forecasts as directional only.",                                                 "color": "red",   "badge": "🔴"}
    else:
        return {"level": "Extreme",  "risk": "Revenue is highly volatile. Forecasts carry low reliability — investigate root causes before acting.",             "color": "red",   "badge": "🚨"}


# ─── CONFIDENCE ADJUSTER ─────────────────────────────────
def compute_confidence_level(n_periods: int, cv_pct: float, has_qa_errors: bool = False) -> str:
    # FIX 3: lowered thresholds — cv>40 → Medium, cv>55 → Low
    if has_qa_errors or cv_pct > 55 or n_periods < 20:
        return "Low"
    elif cv_pct > 40 or n_periods < 52:
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
                f"{growth_ratio:.0f}x current average (${avg_historical:,.0f}). "
                f"Possible causes: model overfitting, unit mismatch, or data anomaly. "
                f"Treat as directional only — not operational."
            )
    if peak_historical > 0:
        peak_ratio = avg_forecast / peak_historical
        if peak_ratio > 1.5:
            warnings.append(
                f"⚠️ CEILING WARNING: Forecast average exceeds best historical period by "
                f"{(peak_ratio-1)*100:.0f}%. Verify model assumptions before using for planning."
            )
    return {"passed": len(warnings) == 0, "warnings": warnings}


# ─── DATE VALIDATION ─────────────────────────────────────
def validate_forecast_dates(forecast_df: pd.DataFrame, last_historical_date: pd.Timestamp) -> pd.DataFrame:
    today = pd.Timestamp.now().normalize()
    forecast_df = forecast_df[forecast_df['ds'] > last_historical_date].copy()
    forecast_df['is_past'] = forecast_df['ds'] < today
    past_count = forecast_df['is_past'].sum()
    if past_count > 0:
        forecast_df['label'] = forecast_df.apply(
            lambda row: f"[Past] {row['ds'].date()}" if row['is_past'] else str(row['ds'].date()),
            axis=1
        )
    return forecast_df


# ─── THREE-SCENARIO FORECASTING ──────────────────────────
def build_scenarios(yhat: np.ndarray, std: float, cv_pct: float) -> dict:
    if cv_pct < 30:
        bear_mult, bull_mult = 0.85, 1.15
    elif cv_pct < 60:
        bear_mult, bull_mult = 0.75, 1.25
    else:
        bear_mult, bull_mult = 0.60, 1.40

    bear_prob = 0.25 if cv_pct < 40 else 0.30
    bull_prob = 0.20 if cv_pct < 40 else 0.25
    base_prob = round(1 - bear_prob - bull_prob, 2)

    return {
        "bear": {
            "values":      np.maximum(yhat * bear_mult, 0),
            "probability": bear_prob,
            "label":       "Bear Case (Pessimistic)",
            "assumption":  "Demand softens or market conditions deteriorate",
            "risk":        "Competitive pricing pressure or demand shock",
        },
        "base": {
            "values":      yhat,
            "probability": base_prob,
            "label":       "Base Case (Most Likely)",
            "assumption":  "Current trend continues with minor variance",
            "key_assumption": "No major market disruption in the forecast window",
        },
        "bull": {
            "values":      yhat * bull_mult,
            "probability": bull_prob,
            "label":       "Bull Case (Optimistic)",
            "assumption":  "Favorable conditions or successful initiatives",
            "required_action": "Active implementation of top-performer replication strategy",
        },
    }


# ─── LEADING INDICATORS ──────────────────────────────────
def build_leading_indicators(forecast_df: pd.DataFrame, avg_historical: float, group_col_avg: float = None) -> list:
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
            "signal":  "Revenue Trajectory",
            "metric":  "Cumulative revenue by end of Period 3",
            "target":  f"${p3_cumulative:,.0f}",
            "alert":   f"If below ${p3_cumulative * 0.85:,.0f} → revise forecast downward",
            "action":  "Investigate demand-side causes before implementing growth initiatives",
        },
        {
            "signal":  "Period Average Check",
            "metric":  "Average revenue per period",
            "target":  f"${weekly_target:,.0f}/period",
            "alert":   f"If drops below ${weekly_target * 0.80:,.0f} → pricing or volume signal",
            "action":  "Review segment performance and check for demand erosion",
        },
        {
            "signal":  "Volatility Monitor",
            "metric":  "Rolling CV of actual vs forecast",
            "target":  "Actual should track within ±20% of base case",
            "alert":   "If 3 consecutive periods miss target → model recalibration required",
            "action":  "Re-run forecast with updated actuals before making resource decisions",
        },
    ]

    if group_col_avg is not None:
        indicators.append({
            "signal":  "Top Segment Health",
            "metric":  "Top segment average per period",
            "target":  f">${group_col_avg * 0.90:,.0f}/period",
            "alert":   f"Drop below ${group_col_avg * 0.75:,.0f} → pricing pressure signal",
            "action":  "Audit top segment pricing and competitive positioning immediately",
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
    # ── Aggregate ─────────────────────────────────────────
    weekly = (
        df.groupby(date_col)[sales_col]
        .sum()
        .reset_index()
        .sort_values(date_col)
    )
    weekly.columns = ['ds', 'y']
    weekly = weekly.dropna(subset=['y'])
    weekly = weekly[weekly['y'] > 0].reset_index(drop=True)

    # ── Guard: empty data ─────────────────────────────────
    if len(weekly) == 0:
        empty_fc = pd.DataFrame(columns=['ds','yhat','yhat_lower','yhat_upper'])
        empty_fc.attrs['scenarios']            = {}
        empty_fc.attrs['cv_pct']               = 0
        empty_fc.attrs['avg_hist']             = 0
        empty_fc.attrs['peak_hist']            = 0
        empty_fc.attrs['confidence']           = 'Low'
        empty_fc.attrs['last_historical_date'] = pd.Timestamp.now()
        empty_fc.attrs['volatility'] = {
            'level': 'Unknown', 'risk': 'No valid data available',
            'badge': '❓', 'cv_pct': 0
        }
        empty_fc.attrs['sanity'] = {
            'passed': False,
            'warnings': ['No valid sales data found after cleaning.']
        }
        return empty_fc, pd.DataFrame(columns=['ds','y'])

    # ── Guard: too few records ────────────────────────────
    if len(weekly) < 3:
        empty_fc = pd.DataFrame(columns=['ds','yhat','yhat_lower','yhat_upper'])
        empty_fc.attrs['scenarios']            = {}
        empty_fc.attrs['cv_pct']               = 0
        empty_fc.attrs['avg_hist']             = float(weekly['y'].mean()) if len(weekly) > 0 else 0
        empty_fc.attrs['peak_hist']            = float(weekly['y'].max())  if len(weekly) > 0 else 0
        empty_fc.attrs['confidence']           = 'Low'
        empty_fc.attrs['last_historical_date'] = weekly['ds'].max() if len(weekly) > 0 else pd.Timestamp.now()
        empty_fc.attrs['volatility'] = {
            'level': 'Unknown', 'risk': 'Insufficient data for forecasting',
            'badge': '❓', 'cv_pct': 0
        }
        empty_fc.attrs['sanity'] = {
            'passed': False,
            'warnings': [f'Insufficient data: only {len(weekly)} periods found. Minimum 3 required.']
        }
        return empty_fc, weekly

    series = weekly.set_index('ds')['y']
    try:
        series.index = pd.DatetimeIndex(series.index).to_period('W').to_timestamp()
    except Exception:
        pass

    n           = len(series)
    avg_hist    = float(series.mean())
    std_hist    = float(series.std()) if len(series) > 1 and series.std() > 0 else 1.0
    peak_hist   = float(series.max())
    cv_pct      = (std_hist / avg_hist * 100) if avg_hist > 0 else 0
    last_date   = weekly['ds'].max()   # ← FIX 1: نحفظ هذا في attrs لاحقاً

    # ── Train model ───────────────────────────────────────
    model = None
    try:
        if n >= 104:
            model = ExponentialSmoothing(
                series, trend='add', seasonal='add', seasonal_periods=52
            ).fit(optimized=True)
        elif n >= 26:
            model = ExponentialSmoothing(
                series, trend='add', seasonal='add', seasonal_periods=26
            ).fit(optimized=True)
        elif n >= 4:
            model = ExponentialSmoothing(
                series, trend='add', seasonal=None
            ).fit(optimized=True)
        else:
            model = ExponentialSmoothing(
                series, trend=None, seasonal=None
            ).fit(optimized=True)
    except Exception:
        try:
            model = ExponentialSmoothing(
                series, trend='add', seasonal=None
            ).fit(optimized=True)
        except Exception:
            try:
                model = ExponentialSmoothing(
                    series, trend=None, seasonal=None
                ).fit(optimized=True)
            except Exception as e:
                avg_val      = float(series.mean())
                try:
                    future_dates = pd.date_range(
                        start=pd.Timestamp(last_date) + pd.Timedelta(weeks=1),
                        periods=weeks, freq='W'
                    )
                except Exception:
                    future_dates = pd.date_range(
                        start=pd.Timestamp.now() + pd.Timedelta(weeks=1),
                        periods=weeks, freq='W'
                    )
                forecast_df = pd.DataFrame({
                    'ds':         future_dates,
                    'yhat':       [avg_val] * weeks,
                    'yhat_lower': [avg_val * 0.75] * weeks,
                    'yhat_upper': [avg_val * 1.25] * weeks,
                })
                historical    = weekly.copy()
                full_forecast = pd.concat([
                    historical.rename(columns={'y':'yhat'})[['ds','yhat']].assign(
                        yhat_lower=lambda x: x['yhat'],
                        yhat_upper=lambda x: x['yhat']
                    ),
                    forecast_df[['ds','yhat','yhat_lower','yhat_upper']],
                ], ignore_index=True)
                full_forecast.attrs['scenarios']            = {}
                full_forecast.attrs['cv_pct']               = cv_pct
                full_forecast.attrs['avg_hist']             = avg_hist
                full_forecast.attrs['peak_hist']            = peak_hist
                full_forecast.attrs['confidence']           = 'Low'
                full_forecast.attrs['last_historical_date'] = pd.Timestamp(last_date)
                full_forecast.attrs['volatility']           = classify_volatility(cv_pct)
                full_forecast.attrs['sanity'] = {
                    'passed': False,
                    'warnings': [f'Model fitting failed: {str(e)}. Using mean forecast as fallback.']
                }
                return full_forecast, historical

    # ── Generate forecast ─────────────────────────────────
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

    scenarios = build_scenarios(forecast_values.values, std_hist, cv_pct)

    forecast_df = pd.DataFrame({
        'ds':         future_dates,
        'yhat':       scenarios['base']['values'],
        'yhat_lower': scenarios['bear']['values'],
        'yhat_upper': scenarios['bull']['values'],
    })

    forecast_df = validate_forecast_dates(forecast_df, pd.Timestamp(last_date))

    historical    = weekly.copy()
    full_forecast = pd.concat([
        historical.rename(columns={'y':'yhat'})[['ds','yhat']].assign(
            yhat_lower=lambda x: x['yhat'],
            yhat_upper=lambda x: x['yhat']
        ),
        forecast_df[['ds','yhat','yhat_lower','yhat_upper']],
    ], ignore_index=True)

    # ── FIX 1: احفظ last_historical_date في attrs ─────────
    full_forecast.attrs['scenarios']            = scenarios
    full_forecast.attrs['cv_pct']               = cv_pct
    full_forecast.attrs['avg_hist']             = avg_hist
    full_forecast.attrs['peak_hist']            = peak_hist
    full_forecast.attrs['confidence']           = compute_confidence_level(n, cv_pct, has_qa_errors)
    full_forecast.attrs['last_historical_date'] = pd.Timestamp(last_date)
    full_forecast.attrs['volatility']           = classify_volatility(cv_pct)
    full_forecast.attrs['sanity']               = sanity_check_forecast(
        float(forecast_values.mean()), avg_hist, peak_hist
    )

    return full_forecast, historical


# ═══════════════════════════════════════════════════════════
# FORECAST SUMMARY — FIX 1 + FIX 2 + FIX 3
# ═══════════════════════════════════════════════════════════
def get_forecast_summary(forecast: pd.DataFrame, group_col_avg: float = None) -> dict:
    if forecast is None or len(forecast) == 0:
        return {
            'next_4_weeks': 0, 'next_8_weeks': 0, 'next_12_weeks': 0,
            'peak_week': 'N/A', 'peak_expected_sales': 0,
            'bear_12_weeks': 0, 'bull_12_weeks': 0,
            'bear_probability': 0.25, 'base_probability': 0.55, 'bull_probability': 0.20,
            'confidence_level': 'Low',
            'volatility': {'level': 'Unknown', 'risk': 'No data', 'badge': '❓', 'cv_pct': 0},
            'sanity_check': {'passed': False, 'warnings': ['No forecast data available']},
            'cv_pct': 0, 'avg_historical': 0,
            'leading_indicators': [], 'decision_rule': '',
        }

    today = pd.Timestamp.now().normalize()

    # ═══════════════════════════════════════════════════════
    # FIX 1: استخدم last_historical_date لفصل الـ forecast
    # السطر القديم: forecast[forecast['ds'] > forecast['ds'].max()]
    # كان دائماً فارغاً — لا يوجد تاريخ أكبر من max()
    # ═══════════════════════════════════════════════════════
    last_hist_date = forecast.attrs.get('last_historical_date', None)

    if last_hist_date is not None:
        future = forecast[forecast['ds'] > pd.Timestamp(last_hist_date)].copy()
    else:
        # Fallback آمن: خذ الـ N صف الأخيرة بدل tail(12) العشوائي
        n_weeks = 12
        future = forecast.tail(n_weeks).copy()

    # إذا كانت كل الفترات في الماضي (بيانات تاريخية قديمة كـ Walmart 2010-2012)
    future_from_today = future[future['ds'] >= today].copy()

    # استخدم المستقبلية إذا وُجدت بما يكفي، وإلا استخدم كل صفوف الـ forecast
    if len(future_from_today) >= 3:
        future_for_kpis = future_from_today
    else:
        future_for_kpis = future

    n_future = len(future_for_kpis)

    next_4  = float(future_for_kpis.head(min(4,  n_future))['yhat'].sum())
    next_8  = float(future_for_kpis.head(min(8,  n_future))['yhat'].sum())
    next_12 = float(future_for_kpis.head(min(12, n_future))['yhat'].sum())

    scenarios = forecast.attrs.get('scenarios', {})
    if scenarios and 'bear' in scenarios and 'bull' in scenarios:
        bear_vals = scenarios['bear']['values'][:min(12, n_future)]
        bull_vals = scenarios['bull']['values'][:min(12, n_future)]
        bear_12   = float(np.sum(bear_vals))
        bull_12   = float(np.sum(bull_vals))
    else:
        bear_12 = next_12 * 0.75
        bull_12 = next_12 * 1.25

    if len(future_for_kpis) > 0 and future_for_kpis['yhat'].notna().any():
        peak_idx = future_for_kpis['yhat'].idxmax()
        peak_dt  = future_for_kpis.loc[peak_idx, 'ds']
        peak_val = float(future_for_kpis.loc[peak_idx, 'yhat'])
    else:
        peak_dt  = today + pd.Timedelta(weeks=4)
        peak_val = 0.0

    try:
        peak_str = peak_dt.date().isoformat()
    except Exception:
        peak_str = str(peak_dt)

    cv_pct   = forecast.attrs.get('cv_pct', 0)
    avg_hist = forecast.attrs.get('avg_hist', 0)

    # FIX 2: أعد حساب volatility مباشرة من cv_pct — لا تأخذها من attrs
    volatility = classify_volatility(cv_pct)

    # FIX 3: confidence مع threshold محسّن
    confidence = forecast.attrs.get('confidence', 'Medium')

    sanity = forecast.attrs.get('sanity', {'passed': True, 'warnings': []})

    leading_indicators = build_leading_indicators(future_for_kpis, avg_hist, group_col_avg)

    decision_rule = (
        "Plan operations around the BASE CASE. "
        "Stress-test budgets against the BEAR CASE. "
        "Only allocate resources for BULL CASE if leading indicators confirm upward trajectory in Period 3."
    )

    return {
        'next_4_weeks':        round(next_4, 2),
        'next_8_weeks':        round(next_8, 2),
        'next_12_weeks':       round(next_12, 2),
        'peak_week':           peak_str,
        'peak_expected_sales': round(peak_val, 2),
        'bear_12_weeks':       round(bear_12, 2),
        'bull_12_weeks':       round(bull_12, 2),
        'bear_probability':    scenarios.get('bear', {}).get('probability', 0.25) if scenarios else 0.25,
        'base_probability':    scenarios.get('base', {}).get('probability', 0.55) if scenarios else 0.55,
        'bull_probability':    scenarios.get('bull', {}).get('probability', 0.20) if scenarios else 0.20,
        'confidence_level':    confidence,
        'volatility':          volatility,
        'sanity_check':        sanity,
        'cv_pct':              round(cv_pct, 1),
        'avg_historical':      round(avg_hist, 2),
        'leading_indicators':  leading_indicators,
        'decision_rule':       decision_rule,
    }