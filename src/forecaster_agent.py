"""
forecaster_agent.py — وكيل التوقعات
=====================================
المسؤولية الوحيدة: التوقعات الزمنية للمبيعات

القاعدة الذهبية:
  - لا يحمّل بيانات، لا يحلل، لا يرسم، لا يكتب PDF
  - كل رقم توقع مشتق من النموذج — لا تقدير يدوي
  - كل توقع يأتي مع: ثقة + نطاق Bear/Base/Bull + تحذيرات
  - إذا كانت البيانات غير كافية → يقول ذلك صراحةً

الخوارزمية:
  Holt-Winters Exponential Smoothing مع اختيار تلقائي للنموذج:
    ≥ 104 فترة → HW seasonal (52)
    ≥  26 فترة → HW seasonal (26)
    ≥   4 فترة → HW trend only
    <   4 فترة → HW level only
    فشل كل ما سبق → mean fallback

السيناريوهات:
  Bear: المئين العاشر من التغيرات التاريخية (empirical)
  Base: مخرج النموذج مباشرة
  Bull: المئين التسعون من التغيرات التاريخية (empirical)
  Fallback: CV-scaled إذا البيانات < 6 فترات

إصلاحات من النسخة القديمة:
  FIX-1: get_forecast_summary() يعزل المستقبل بـ last_historical_date
  FIX-2: CV يُحسب على إجمالي الفترات لا الصفوف الخام
  FIX-3: Bear/Bull مشتقة من المئينات التاريخية لا multipliers ثابتة
  FIX-4: لا احتمالات مخترعة — spread labels صادقة فقط
  FIX-5: last_historical_date محفوظة في attrs
  FIX-6: model_type محفوظ في attrs للشفافية
  FIX-7 (جديد): اكتشاف تلقائي لتردد البيانات (أسبوعي/شهري/يومي)
  FIX-8 (جديد): in-sample accuracy metrics (MAE/RMSE/MAPE) صحيحة
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from config import CV_LOW, CV_MODERATE, CV_HIGH


# ════════════════════════════════════════════════
# 1. FREQUENCY DETECTION — FIX-7
# ════════════════════════════════════════════════

def detect_data_frequency(series_index: pd.DatetimeIndex) -> Tuple[str, int, str]:
    """
    يكتشف تلقائياً تردد البيانات الزمنية.

    Returns:
        (freq_label, seasonal_period, timedelta_str)
        freq_label:      'Weekly' | 'Monthly' | 'Daily' | 'Quarterly' | 'Unknown'
        seasonal_period: عدد الفترات في دورة موسمية كاملة
        timedelta_str:   'W' | 'ME' | 'D' | 'QE'
    """
    if len(series_index) < 2:
        return 'Unknown', 52, 'W'

    try:
        diffs = pd.Series(series_index).diff().dropna()
        median_diff = diffs.median()
        days = median_diff.days

        if 1 <= days <= 3:
            return 'Daily', 365, 'D'
        elif 4 <= days <= 10:
            return 'Weekly', 52, 'W'
        elif 11 <= days <= 35:
            return 'Monthly', 12, 'ME'
        elif 60 <= days <= 100:
            return 'Quarterly', 4, 'QE'
        else:
            return 'Unknown', 52, 'W'
    except Exception:
        return 'Unknown', 52, 'W'


# ════════════════════════════════════════════════
# 2. VOLATILITY CLASSIFIER
# ════════════════════════════════════════════════

def classify_volatility(cv_pct: float) -> dict:
    """
    تصنيف تقلب الإيراد بناءً على معامل التغيير (CV).
    """
    if cv_pct < CV_LOW:
        return {
            "level": "Low",
            "risk":  "Revenue is highly predictable. Forecasts are reliable.",
            "color": "green",
            "badge": "🟢",
        }
    elif cv_pct < CV_MODERATE:
        return {
            "level": "Moderate",
            "risk":  "Some revenue fluctuation. Forecasts are directionally reliable.",
            "color": "amber",
            "badge": "🟡",
        }
    elif cv_pct < CV_HIGH:
        return {
            "level": "High",
            "risk":  "Significant revenue swings. Treat forecasts as directional only.",
            "color": "red",
            "badge": "🔴",
        }
    else:
        return {
            "level": "Extreme",
            "risk":  (
                "Revenue is highly volatile. Forecasts carry low reliability — "
                "investigate root causes before acting."
            ),
            "color": "red",
            "badge": "🚨",
        }


# ════════════════════════════════════════════════
# 3. CONFIDENCE LEVEL
# ════════════════════════════════════════════════

def compute_confidence_level(
    n_periods: int,
    cv_pct: float,
    has_qa_errors: bool = False,
) -> str:
    """
    يحدد مستوى ثقة التوقع بناءً على:
      - عدد الفترات التاريخية
      - معامل التغيير
      - وجود أخطاء جودة البيانات

    Returns: 'High' | 'Medium' | 'Low'
    """
    if has_qa_errors or cv_pct > 60 or n_periods < 20:
        return "Low"
    elif cv_pct > 35 or n_periods < 52:
        return "Medium"
    else:
        return "High"


# ════════════════════════════════════════════════
# 4. SANITY CHECK
# ════════════════════════════════════════════════

def sanity_check_forecast(
    avg_forecast: float,
    avg_historical: float,
    peak_historical: float,
) -> dict:
    """
    يتحقق من منطقية التوقع قبل عرضه.

    Rules:
      - إذا كان متوسط التوقع > 3× المتوسط التاريخي → تحذير
      - إذا كان متوسط التوقع > 1.5× أعلى فترة تاريخية → تحذير
    """
    warnings = []

    if avg_historical > 0:
        ratio = avg_forecast / avg_historical
        if ratio > 3.0:
            warnings.append(
                f"⚠️ FORECAST WARNING: Projected average (${avg_forecast:,.0f}) is "
                f"{ratio:.1f}× the historical average (${avg_historical:,.0f}). "
                "Possible causes: model overfitting, data anomaly, or unit mismatch. "
                "Treat as directional signal only — do not use for operational budgeting."
            )

    if peak_historical > 0:
        peak_ratio = avg_forecast / peak_historical
        if peak_ratio > 1.5:
            warnings.append(
                f"⚠️ CEILING WARNING: Forecast average exceeds the historical peak by "
                f"{(peak_ratio - 1) * 100:.0f}%. "
                "Verify model assumptions before committing resources."
            )

    return {"passed": len(warnings) == 0, "warnings": warnings}


# ════════════════════════════════════════════════
# 5. DATE VALIDATION
# ════════════════════════════════════════════════

def validate_forecast_dates(
    forecast_df: pd.DataFrame,
    last_historical_date: pd.Timestamp,
) -> pd.DataFrame:
    """
    يحذف أي صفوف في التوقع تسبق آخر تاريخ تاريخي،
    ويضيف عمود is_past لتمييز الفترات الماضية.
    """
    today       = pd.Timestamp.now().normalize()
    forecast_df = forecast_df[forecast_df['ds'] > last_historical_date].copy()
    forecast_df['is_past'] = forecast_df['ds'] < today
    return forecast_df


# ════════════════════════════════════════════════
# 6. EMPIRICAL SCENARIO BUILDER — FIX-3 & FIX-4
# ════════════════════════════════════════════════

def build_scenarios(
    yhat: np.ndarray,
    historical_series: pd.Series,
    cv_pct: float,
) -> dict:
    """
    FIX-3: Bear/Bull مشتقة من المئين العاشر والتسعين
    للتغيرات التاريخية — لا multipliers ثابتة.

    FIX-4: لا احتمالات مخترعة — spread labels صادقة.
    """
    pct_changes = historical_series.pct_change().dropna()

    if len(pct_changes) >= 6:
        p10 = float(np.percentile(pct_changes, 10))
        p90 = float(np.percentile(pct_changes, 90))

        bear_mult  = max(0.40, 1 + p10)
        bull_mult  = min(2.50, 1 + p90)
        bear_basis = f"Historical 10th-pct period shock ({p10*100:+.1f}%)"
        bull_basis = f"Historical 90th-pct period surge ({p90*100:+.1f}%)"
        method     = "empirical_percentile"
    else:
        # Fallback: مشتق من CV الفعلي
        cv_dec = cv_pct / 100
        bear_mult = max(0.50, 1.0 - cv_dec)
        bull_mult = min(2.00, 1.0 + cv_dec)
        bear_basis = f"CV-derived fallback (n<6, CV={cv_pct:.0f}%)"
        bull_basis = f"CV-derived fallback (n<6, CV={cv_pct:.0f}%)"
        method     = "cv_derived_fallback"

    bear_values = np.maximum(yhat * bear_mult, 0)
    bull_values = yhat * bull_mult

    bear_spread_pct = round((bear_mult - 1) * 100, 1)
    bull_spread_pct = round((bull_mult - 1) * 100, 1)

    return {
        "bear": {
            "values":     bear_values,
            "multiplier": round(bear_mult, 4),
            "spread_pct": bear_spread_pct,
            "label":      "Bear Case (Downside)",
            "basis":      bear_basis,
            "assumption": "Demand softens or adverse market conditions materialize",
        },
        "base": {
            "values":     yhat,
            "multiplier": 1.0,
            "spread_pct": 0.0,
            "label":      "Base Case (Trend Continuation)",
            "basis":      "Holt-Winters model output — current trend continues",
            "assumption": "No major market disruption in the forecast window",
        },
        "bull": {
            "values":     bull_values,
            "multiplier": round(bull_mult, 4),
            "spread_pct": bull_spread_pct,
            "label":      "Bull Case (Upside)",
            "basis":      bull_basis,
            "assumption": "Favorable conditions or successful strategic initiatives",
        },
        "method":          method,
        "bear_spread_pct": bear_spread_pct,
        "bull_spread_pct": bull_spread_pct,
    }


# ════════════════════════════════════════════════
# 7. IN-SAMPLE ACCURACY — FIX-8
# ════════════════════════════════════════════════

def compute_forecast_accuracy(prophet_data: pd.DataFrame) -> dict:
    """
    FIX-8: MAE/RMSE/MAPE محسوبة على pseudo-holdout حقيقي.

    المنهجية:
      - تدريب النموذج على أول 80% من البيانات
      - اختبار على آخر 20%
      - حساب الأخطاء على holdout — ليس على training data

    Returns:
        dict يحتوي: available, mae, rmse, mape, acc_rating, limitation
    """
    try:
        hist = prophet_data.copy()
        if list(hist.columns) != ['ds', 'y']:
            hist.columns = ['ds', 'y']
        hist = hist.dropna(subset=['y']).sort_values('ds').reset_index(drop=True)
        n    = len(hist)

        if n < 10:
            return {
                "available": False,
                "message":   (
                    f"Forecast accuracy unavailable: only {n} periods. "
                    "Minimum 10 required."
                ),
            }

        holdout_n = max(4, int(n * 0.2))
        train_df  = hist.iloc[:-holdout_n].copy()
        test_df   = hist.iloc[-holdout_n:].copy()
        actuals   = test_df['y'].values

        # تدريب نموذج جديد على training split فقط
        series = train_df.set_index('ds')['y'].copy()
        try:
            series.index = pd.DatetimeIndex(series.index).to_period('W').to_timestamp()
        except Exception:
            pass

        n_train = len(series)
        try:
            if n_train >= 52:
                model = ExponentialSmoothing(
                    series, trend='add', seasonal='add', seasonal_periods=52
                ).fit(optimized=True)
            elif n_train >= 26:
                model = ExponentialSmoothing(
                    series, trend='add', seasonal='add', seasonal_periods=26
                ).fit(optimized=True)
            else:
                model = ExponentialSmoothing(
                    series, trend='add', seasonal=None
                ).fit(optimized=True)
        except Exception:
            try:
                model = ExponentialSmoothing(
                    series, trend='add', seasonal=None
                ).fit(optimized=True)
            except Exception:
                model = ExponentialSmoothing(
                    series, trend=None, seasonal=None
                ).fit(optimized=True)

        predicted = model.forecast(holdout_n)[:len(actuals)]

        if float(np.mean(np.abs(predicted))) < 0.01:
            return {
                "available": False,
                "message":   "Model produced near-zero predictions on holdout — data alignment issue.",
            }

        mae  = float(np.mean(np.abs(actuals - predicted)))
        rmse = float(np.sqrt(np.mean((actuals - predicted) ** 2)))

        nonzero = actuals != 0
        mape = (
            float(np.mean(np.abs((actuals[nonzero] - predicted[nonzero])
                                 / actuals[nonzero])) * 100)
            if nonzero.any() else None
        )

        if mae < 0.01:
            return {
                "available": False,
                "message":   "Computed MAE near-zero — data alignment issue. Suppressed.",
            }

        if mape is not None:
            if mape < 10:    acc_rating = "Excellent (MAPE < 10%)"
            elif mape < 20:  acc_rating = "Good (MAPE 10–20%)"
            elif mape < 30:  acc_rating = "Fair (MAPE 20–30%)"
            else:            acc_rating = "Poor (MAPE ≥ 30%) — use directional guidance only"
        else:
            acc_rating = "MAPE not computable (zero-value periods in holdout)"

        return {
            "available":   True,
            "mae":         round(mae,  2),
            "rmse":        round(rmse, 2),
            "mape":        round(mape, 1) if mape is not None else None,
            "n_holdout":   holdout_n,
            "n_train":     n_train,
            "acc_rating":  acc_rating,
            "limitation":  (
                f"In-sample pseudo-holdout: trained on {n_train} periods, "
                f"validated on last {holdout_n} periods (20%). "
                "True out-of-sample accuracy will differ."
            ),
        }

    except Exception as e:
        return {
            "available": False,
            "message":   f"Accuracy computation failed: {str(e)}",
        }


# ════════════════════════════════════════════════
# 8. LEADING INDICATORS
# ════════════════════════════════════════════════

def build_leading_indicators(
    forecast_df: pd.DataFrame,
    avg_historical: float,
    group_col_avg: Optional[float] = None,
) -> list:
    """
    يبني مؤشرات قيادية للمراقبة بعد التوقع.
    كل مؤشر مشتق من أرقام التوقع الفعلية.
    """
    # استخدم الصفوف المستقبلية الحقيقية فقط
    if 'is_past' in forecast_df.columns:
        future = forecast_df[~forecast_df['is_past']].copy()
    else:
        future = forecast_df.copy()

    if len(future) < 3:
        return []

    p3_cum      = float(future.head(3)['yhat'].sum())
    period_avg  = float(future['yhat'].mean())

    indicators = [
        {
            "signal": "Revenue Trajectory",
            "metric": "Cumulative revenue — end of Period 3",
            "target": f"${p3_cum:,.0f}",
            "alert":  f"If below ${p3_cum * 0.85:,.0f} → revise forecast downward",
            "action": "Investigate demand-side causes before growth initiatives",
        },
        {
            "signal": "Period Average Check",
            "metric": "Average revenue per period",
            "target": f"${period_avg:,.0f}/period",
            "alert":  f"If drops below ${period_avg * 0.80:,.0f} → pricing or volume erosion",
            "action": "Review segment performance and check for demand erosion",
        },
        {
            "signal": "Volatility Monitor",
            "metric": "Rolling deviation — actual vs forecast",
            "target": "Actual should track within ±20% of base case",
            "alert":  "3 consecutive misses → model recalibration required",
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


# ════════════════════════════════════════════════
# 9. MAIN FORECAST FUNCTION
# ════════════════════════════════════════════════

def train_and_forecast(
    df: pd.DataFrame,
    periods: int = 12,
    date_col: str = 'Date',
    sales_col: str = 'Weekly_Sales',
    has_qa_errors: bool = False,
    # للتوافق مع الكود القديم الذي يستخدم 'weeks'
    weeks: Optional[int] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    التدريب والتوقع الكامل.

    Args:
        df:           DataFrame نظيف
        periods:      عدد الفترات للتوقع (يحل محل 'weeks')
        date_col:     عمود التاريخ
        sales_col:    عمود المبيعات
        has_qa_errors: هل توجد أخطاء جودة بيانات؟
        weeks:        للتوافق مع الكود القديم (يُستخدم إذا لم يُعطَ periods)

    Returns:
        (full_forecast_df, historical_df)

        full_forecast_df: يحتوي تاريخي + مستقبل
          أعمدة: ds, yhat, yhat_lower, yhat_upper, is_past
          attrs:  scenarios, cv_pct, avg_hist, peak_hist,
                  confidence, model_type, last_historical_date,
                  volatility, sanity, freq_label, accuracy

        historical_df:
          أعمدة: ds, y
    """
    # توافق مع 'weeks' القديم
    n_periods = weeks if weeks is not None else periods

    # ── Step 1: تجميع البيانات على مستوى الفترة ──
    try:
        aggregated = (
            df.groupby(date_col)[sales_col]
            .sum()
            .reset_index()
            .sort_values(date_col)
            .rename(columns={date_col: 'ds', sales_col: 'y'})
        )
        aggregated = aggregated.dropna(subset=['y'])
        aggregated = aggregated[aggregated['y'] > 0].reset_index(drop=True)
    except Exception as e:
        return _empty_result(f"Data aggregation failed: {e}", n_periods)

    if len(aggregated) == 0:
        return _empty_result("No valid sales data found after cleaning.", n_periods)
    if len(aggregated) < 3:
        return _empty_result(
            f"Insufficient data: {len(aggregated)} periods. Minimum 3 required.",
            n_periods,
            aggregated,
        )

    # ── Step 2: تحضير السلسلة الزمنية ───────────
    series = aggregated.set_index('ds')['y'].copy()

    # FIX-7: اكتشاف التردد
    freq_label, seasonal_period, freq_str = detect_data_frequency(
        pd.DatetimeIndex(series.index)
    )

    # توحيد الـ index
    try:
        series.index = pd.DatetimeIndex(series.index)
        if freq_str == 'W':
            series.index = series.index.to_period('W').to_timestamp()
    except Exception:
        pass

    n          = len(series)
    avg_hist   = float(series.mean())
    peak_hist  = float(series.max())
    last_date  = pd.Timestamp(aggregated['ds'].max())

    # FIX-2: CV على مستوى الفترة المجمّعة
    cv_pct = _compute_period_cv(series)

    # ── Step 3: اختيار النموذج والتدريب ──────────
    model, model_type = _select_and_train_model(series, n, seasonal_period)

    # ── Step 4: توليد التوقعات ───────────────────
    if model is None:
        # mean fallback
        return _mean_fallback(
            aggregated, series, n_periods,
            avg_hist, peak_hist, last_date,
            cv_pct, freq_str, freq_label,
            has_qa_errors,
        )

    forecast_values = model.forecast(n_periods)

    # ── Step 5: تاريخ الفترات المستقبلية ─────────
    try:
        future_dates = pd.date_range(
            start   = last_date + _get_timedelta(freq_str),
            periods = n_periods,
            freq    = freq_str,
        )
    except Exception:
        future_dates = pd.date_range(
            start   = last_date + pd.Timedelta(weeks=1),
            periods = n_periods,
            freq    = 'W',
        )

    # ── Step 6: FIX-3 — السيناريوهات التجريبية ───
    scenarios = build_scenarios(forecast_values.values, series, cv_pct)

    forecast_df = pd.DataFrame({
        'ds':         future_dates,
        'yhat':       scenarios['base']['values'],
        'yhat_lower': scenarios['bear']['values'],
        'yhat_upper': scenarios['bull']['values'],
    })

    # ── Step 7: FIX-1 — التحقق من التواريخ ───────
    forecast_df = validate_forecast_dates(forecast_df, last_date)

    # ── Step 8: دمج التاريخي مع المستقبل ─────────
    historical    = aggregated.copy()
    full_forecast = pd.concat([
        historical.rename(columns={'y': 'yhat'})[['ds', 'yhat']].assign(
            yhat_lower = lambda x: x['yhat'],
            yhat_upper = lambda x: x['yhat'],
            is_past    = False,
        ),
        forecast_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'is_past']],
    ], ignore_index=True)

    # ── Step 9: FIX-8 — دقة النموذج ──────────────
    accuracy = compute_forecast_accuracy(historical)

    # ── Step 10: FIX-5/6 — metadata في attrs ──────
    full_forecast.attrs.update({
        'scenarios':            scenarios,
        'cv_pct':               cv_pct,
        'avg_hist':             avg_hist,
        'peak_hist':            peak_hist,
        'confidence':           compute_confidence_level(n, cv_pct, has_qa_errors),
        'model_type':           model_type,
        'last_historical_date': last_date,
        'volatility':           classify_volatility(cv_pct),
        'sanity':               sanity_check_forecast(
                                    float(forecast_values.mean()),
                                    avg_hist,
                                    peak_hist,
                                ),
        'freq_label':           freq_label,
        'freq_str':             freq_str,
        'seasonal_period':      seasonal_period,
        'n_historical':         n,
        'accuracy':             accuracy,
    })

    return full_forecast, historical


# ════════════════════════════════════════════════
# 10. FORECAST SUMMARY — FIX-1
# ════════════════════════════════════════════════

def get_forecast_summary(
    forecast: pd.DataFrame,
    prophet_data: Optional[pd.DataFrame] = None,
    group_col_avg: Optional[float] = None,
) -> dict:
    """
    FIX-1: يعزل الصفوف المستقبلية بـ last_historical_date
    المحفوظة في attrs — لا يعتمد على max(ds) الخاطئة.

    Args:
        forecast:      مخرج train_and_forecast()
        prophet_data:  البيانات التاريخية (للـ fallback)
        group_col_avg: متوسط أعلى مجموعة (للـ leading indicators)

    Returns:
        dict شامل لكل مقاييس التوقع
    """
    # ── Guard: بيانات فارغة ───────────────────────
    if forecast is None or len(forecast) == 0:
        return _empty_summary()

    today = pd.Timestamp.now().normalize()

    # ── FIX-1: تحديد آخر تاريخ تاريخي ───────────
    last_hist_date = forecast.attrs.get('last_historical_date', None)

    if last_hist_date is None and prophet_data is not None and len(prophet_data) > 0:
        ds_col = 'ds' if 'ds' in prophet_data.columns else prophet_data.columns[0]
        last_hist_date = pd.Timestamp(prophet_data[ds_col].max())

    if last_hist_date is None:
        last_hist_date = today - pd.Timedelta(days=1)

    last_hist_date = pd.Timestamp(last_hist_date)

    # ── عزل الصفوف المستقبلية ─────────────────────
    future           = forecast[forecast['ds'] > last_hist_date].copy()
    future_from_now  = future[future['ds'] >= today].copy()
    future_for_metrics = future_from_now if len(future_from_now) > 0 else future

    # آخر fallback
    if len(future_for_metrics) == 0:
        future_for_metrics = forecast.tail(12).copy()

    n_future = len(future_for_metrics)

    # ── أرقام التوقع الأساسية ─────────────────────
    next_4  = float(future_for_metrics.head(min(4,  n_future))['yhat'].sum())
    next_8  = float(future_for_metrics.head(min(8,  n_future))['yhat'].sum())
    next_12 = float(future_for_metrics.head(min(12, n_future))['yhat'].sum())

    # ── السيناريوهات من attrs ─────────────────────
    scenarios = forecast.attrs.get('scenarios', {})

    if scenarios and 'bear' in scenarios and 'bull' in scenarios:
        bear_vals = scenarios['bear']['values']
        bull_vals = scenarios['bull']['values']
        n_use     = min(12, n_future, len(bear_vals), len(bull_vals))
        bear_12   = float(np.sum(bear_vals[:n_use]))
        bull_12   = float(np.sum(bull_vals[:n_use]))
        bear_spread = scenarios.get('bear_spread_pct', -25.0)
        bull_spread = scenarios.get('bull_spread_pct',  25.0)
        sc_method   = scenarios.get('method', 'unknown')
    else:
        cv_fb     = forecast.attrs.get('cv_pct', 30) / 100
        bear_mult = max(0.50, 1.0 - cv_fb)
        bull_mult = min(2.00, 1.0 + cv_fb)
        bear_12   = next_12 * bear_mult
        bull_12   = next_12 * bull_mult
        bear_spread = (bear_mult - 1) * 100
        bull_spread = (bull_mult - 1) * 100
        sc_method   = 'cv_derived_fallback'

    # ── اكتشاف الذروة ────────────────────────────
    if len(future_for_metrics) > 0 and future_for_metrics['yhat'].notna().any():
        peak_idx = future_for_metrics['yhat'].idxmax()
        peak_dt  = future_for_metrics.loc[peak_idx, 'ds']
        peak_val = float(future_for_metrics.loc[peak_idx, 'yhat'])
        try:
            peak_str = pd.Timestamp(peak_dt).date().isoformat()
        except Exception:
            peak_str = str(peak_dt)
    else:
        peak_str = "N/A"
        peak_val = 0.0

    # ── metadata من attrs ─────────────────────────
    cv_pct     = forecast.attrs.get('cv_pct',     0)
    avg_hist   = forecast.attrs.get('avg_hist',   0)
    confidence = forecast.attrs.get('confidence', 'Medium')
    volatility = forecast.attrs.get('volatility', classify_volatility(cv_pct))
    sanity     = forecast.attrs.get('sanity',     {'passed': True, 'warnings': []})
    model_type = forecast.attrs.get('model_type', 'unknown')
    freq_label = forecast.attrs.get('freq_label', 'Unknown')
    accuracy   = forecast.attrs.get('accuracy',   {'available': False})

    # ── Leading Indicators ────────────────────────
    li_df = future_from_now if len(future_from_now) >= 3 else future_for_metrics
    leading_indicators = build_leading_indicators(li_df, avg_hist, group_col_avg)

    # ── Decision Rule ─────────────────────────────
    decision_rule = (
        f"Plan operations around the BASE CASE (${next_12:,.0f} over 12 periods). "
        f"Stress-test budgets against the BEAR CASE "
        f"(${bear_12:,.0f}, {bear_spread:+.0f}% from base — {sc_method}). "
        f"Allocate BULL CASE resources (${bull_12:,.0f}) only if leading indicators "
        f"confirm upward trajectory in the first 3 periods."
    )

    # ── الفجوة بين التوقع والتاريخي ──────────────
    fc12_avg_per_period = next_12 / 12 if next_12 > 0 else 0
    fc_gap_pct = (
        (fc12_avg_per_period - avg_hist) / avg_hist * 100
        if avg_hist > 0 else 0
    )

    return {
        # أرقام أساسية
        'next_4_weeks':         round(next_4,  2),
        'next_8_weeks':         round(next_8,  2),
        'next_12_weeks':        round(next_12, 2),
        'peak_week':            peak_str,
        'peak_expected_sales':  round(peak_val, 2),

        # السيناريوهات — FIX-4: لا احتمالات مخترعة
        'bear_12_weeks':        round(bear_12, 2),
        'bull_12_weeks':        round(bull_12, 2),
        'bear_spread_pct':      round(bear_spread, 1),
        'bull_spread_pct':      round(bull_spread, 1),
        'scenario_method':      sc_method,

        # مفاتيح deprecated للتوافق مع الكود القديم
        'bear_probability':     0.0,
        'base_probability':     0.0,
        'bull_probability':     0.0,

        # جودة النموذج
        'confidence_level':     confidence,
        'volatility':           volatility,
        'sanity_check':         sanity,
        'cv_pct':               round(cv_pct, 1),
        'avg_historical':       round(avg_hist, 2),
        'model_type':           model_type,
        'freq_label':           freq_label,
        'accuracy':             accuracy,

        # فجوة التوقع
        'fc12_avg_per_period':  round(fc12_avg_per_period, 2),
        'fc_gap_pct':           round(fc_gap_pct, 1),
        'fc_gap_flag':          fc_gap_pct > 200,

        # مساعدات التخطيط
        'leading_indicators':   leading_indicators,
        'decision_rule':        decision_rule,
    }


# ════════════════════════════════════════════════
# PRIVATE HELPERS
# ════════════════════════════════════════════════

def _compute_period_cv(series: pd.Series) -> float:
    """FIX-2: CV على مستوى الفترة المجمّعة"""
    if len(series) < 2:
        return 0.0
    mean_val = float(series.mean())
    std_val  = float(series.std())
    if mean_val <= 0:
        return 0.0
    return round(std_val / mean_val * 100, 2)


def _get_timedelta(freq_str: str) -> pd.Timedelta:
    """تحويل freq_str إلى Timedelta للتاريخ الأول بعد آخر فترة"""
    mapping = {
        'W':  pd.Timedelta(weeks=1),
        'ME': pd.DateOffset(months=1),
        'D':  pd.Timedelta(days=1),
        'QE': pd.DateOffset(months=3),
    }
    return mapping.get(freq_str, pd.Timedelta(weeks=1))


def _select_and_train_model(
    series: pd.Series,
    n: int,
    seasonal_period: int,
) -> Tuple[Optional[object], str]:
    """
    اختيار وتدريب النموذج المناسب تلقائياً.

    Returns: (model, model_type_label)
    """
    # محاولة تسلسلية من الأقوى للأبسط
    attempts = []

    if n >= seasonal_period * 2:
        attempts.append((
            {'trend': 'add', 'seasonal': 'add', 'seasonal_periods': seasonal_period},
            f'HW_seasonal_{seasonal_period}',
        ))
    if n >= 26 and seasonal_period != 26:
        attempts.append((
            {'trend': 'add', 'seasonal': 'add', 'seasonal_periods': 26},
            'HW_seasonal_26',
        ))
    if n >= 4:
        attempts.append((
            {'trend': 'add', 'seasonal': None},
            'HW_trend_only',
        ))
    attempts.append((
        {'trend': None, 'seasonal': None},
        'HW_level_only',
    ))

    for params, label in attempts:
        try:
            model = ExponentialSmoothing(series, **params).fit(optimized=True)
            return model, label
        except Exception:
            continue

    return None, 'failed'


def _empty_result(
    msg: str,
    n_periods: int,
    aggregated: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """يُرجع نتيجة فارغة مع تحذير واضح"""
    efc = pd.DataFrame(columns=['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'is_past'])
    efc.attrs.update({
        'scenarios':            {},
        'cv_pct':               0,
        'avg_hist':             0,
        'peak_hist':            0,
        'confidence':           'Low',
        'model_type':           'none',
        'last_historical_date': pd.Timestamp.now(),
        'volatility':           {'level': 'Unknown', 'risk': 'No valid data', 'badge': '❓'},
        'sanity':               {'passed': False, 'warnings': [msg]},
        'freq_label':           'Unknown',
        'accuracy':             {'available': False, 'message': msg},
    })
    hist = aggregated if aggregated is not None else pd.DataFrame(columns=['ds', 'y'])
    return efc, hist


def _mean_fallback(
    aggregated, series, n_periods,
    avg_hist, peak_hist, last_date,
    cv_pct, freq_str, freq_label,
    has_qa_errors,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """آخر ملاذ: توقع بالمتوسط إذا فشل كل النماذج"""
    try:
        future_dates = pd.date_range(
            start   = last_date + _get_timedelta(freq_str),
            periods = n_periods,
            freq    = freq_str,
        )
    except Exception:
        future_dates = pd.date_range(
            start   = last_date + pd.Timedelta(weeks=1),
            periods = n_periods,
            freq    = 'W',
        )

    scenarios   = build_scenarios(np.array([avg_hist] * n_periods), series, cv_pct)
    forecast_df = pd.DataFrame({
        'ds':         future_dates,
        'yhat':       scenarios['base']['values'],
        'yhat_lower': scenarios['bear']['values'],
        'yhat_upper': scenarios['bull']['values'],
        'is_past':    [False] * n_periods,
    })

    historical    = aggregated.copy()
    full_forecast = pd.concat([
        historical.rename(columns={'y': 'yhat'})[['ds', 'yhat']].assign(
            yhat_lower = lambda x: x['yhat'],
            yhat_upper = lambda x: x['yhat'],
            is_past    = False,
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
        'sanity':               {
            'passed':   False,
            'warnings': ['All models failed. Using mean forecast as fallback.'],
        },
        'freq_label':           freq_label,
        'freq_str':             freq_str,
        'accuracy':             {'available': False, 'message': 'Model fitting failed'},
    })

    return full_forecast, historical


def _empty_summary() -> dict:
    """ملخص فارغ للحالات الطارئة"""
    return {
        'next_4_weeks': 0, 'next_8_weeks': 0, 'next_12_weeks': 0,
        'peak_week': 'N/A', 'peak_expected_sales': 0,
        'bear_12_weeks': 0, 'bull_12_weeks': 0,
        'bear_spread_pct': -25.0, 'bull_spread_pct': 25.0,
        'scenario_method': 'none',
        'bear_probability': 0.0, 'base_probability': 0.0, 'bull_probability': 0.0,
        'confidence_level': 'Low',
        'volatility': {'level': 'Unknown', 'risk': 'No data', 'badge': '❓'},
        'sanity_check': {'passed': False, 'warnings': ['No forecast data available']},
        'cv_pct': 0, 'avg_historical': 0,
        'model_type': 'none', 'freq_label': 'Unknown',
        'fc12_avg_per_period': 0, 'fc_gap_pct': 0, 'fc_gap_flag': False,
        'accuracy': {'available': False},
        'leading_indicators': [], 'decision_rule': '',
    }