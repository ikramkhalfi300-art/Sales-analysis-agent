import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def train_and_forecast(df, weeks=12, date_col='Date', sales_col='Weekly_Sales'):
    """
    تدريب نموذج التنبؤ وإرجاع التوقعات
    يستخدم statsmodels (متوافق مع Streamlit Cloud)
    """
    # تجميع المبيعات أسبوعياً
    weekly = (
        df.groupby(date_col)[sales_col]
        .sum()
        .reset_index()
        .sort_values(date_col)
    )
    weekly.columns = ['ds', 'y']
    weekly = weekly.dropna(subset=['y'])

    # تدريب النموذج
    series = weekly.set_index('ds')['y']

    try:
        series.index = pd.DatetimeIndex(series.index).to_period('W').to_timestamp()
    except Exception:
        pass

    n = len(series)
    try:
        if n >= 104:
            seasonal_periods = 52
            model = ExponentialSmoothing(
                series, trend='add', seasonal='add', seasonal_periods=seasonal_periods
            ).fit(optimized=True)
        elif n >= 26:
            seasonal_periods = 26
            model = ExponentialSmoothing(
                series, trend='add', seasonal='add', seasonal_periods=seasonal_periods
            ).fit(optimized=True)
        else:
            model = ExponentialSmoothing(
                series, trend='add', seasonal=None
            ).fit(optimized=True)
    except Exception:
        # fallback بدون seasonal
        try:
            model = ExponentialSmoothing(
                series, trend='add', seasonal=None
            ).fit(optimized=True)
        except Exception:
            model = ExponentialSmoothing(
                series, trend=None, seasonal=None
            ).fit(optimized=True)

    # توليد التوقعات
    forecast_values = model.forecast(weeks)
    last_date = weekly['ds'].max()

    try:
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(weeks=1), periods=weeks, freq='W'
        )
    except Exception:
        future_dates = pd.date_range(
            start=pd.Timestamp(last_date) + pd.Timedelta(weeks=1), periods=weeks, freq='W'
        )

    std = float(series.std()) if series.std() > 0 else 1.0

    forecast_df = pd.DataFrame({
        'ds': future_dates,
        'yhat': forecast_values.values,
        'yhat_lower': forecast_values.values - 1.96 * std,
        'yhat_upper': forecast_values.values + 1.96 * std,
    })

    # دمج التاريخي مع التوقعات للرسم
    historical = weekly.copy()
    full_forecast = pd.concat([
        historical.rename(columns={'y': 'yhat'})[['ds', 'yhat']].assign(
            yhat_lower=lambda x: x['yhat'],
            yhat_upper=lambda x: x['yhat']
        ),
        forecast_df
    ], ignore_index=True)

    return full_forecast, historical


def get_forecast_summary(forecast):
    """
    ملخص أرقام التوقعات للـ 12 أسبوع القادمة
    """
    future = forecast.tail(12).copy()

    next_4  = float(future.head(4)['yhat'].sum())
    next_8  = float(future.head(8)['yhat'].sum())
    next_12 = float(future['yhat'].sum())

    peak_idx  = future['yhat'].idxmax()
    peak_week = future.loc[peak_idx, 'ds']
    peak_val  = float(future.loc[peak_idx, 'yhat'])

    try:
        peak_week_str = peak_week.date().isoformat()
    except Exception:
        peak_week_str = str(peak_week)

    return {
        'next_4_weeks':        round(next_4, 2),
        'next_8_weeks':        round(next_8, 2),
        'next_12_weeks':       round(next_12, 2),
        'peak_week':           peak_week_str,
        'peak_expected_sales': round(peak_val, 2),
    }