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
    series.index = pd.DatetimeIndex(series.index, freq='infer')

    try:
        model = ExponentialSmoothing(
            series,
            trend='add',
            seasonal='add' if len(series) >= 24 else None,
            seasonal_periods=52 if len(series) >= 104 else (
                26 if len(series) >= 52 else None
            )
        ).fit(optimized=True)
    except Exception:
        # fallback بدون seasonal
        model = ExponentialSmoothing(
            series,
            trend='add',
            seasonal=None
        ).fit(optimized=True)

    # توليد التوقعات
    forecast_values = model.forecast(weeks)
    last_date = weekly['ds'].max()
    future_dates = pd.date_range(start=last_date + pd.Timedelta(weeks=1), periods=weeks, freq='W')

    # بناء forecast DataFrame بنفس شكل Prophet
    std = series.std()
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
    # آخر تاريخ تاريخي = نقطة بداية التوقعات
    future = forecast.tail(12)

    next_4  = future.head(4)['yhat'].sum()
    next_8  = future.head(8)['yhat'].sum()
    next_12 = future['yhat'].sum()

    peak_idx  = future['yhat'].idxmax()
    peak_week = future.loc[peak_idx, 'ds']
    peak_val  = future.loc[peak_idx, 'yhat']

    return {
        'next_4_weeks':         round(next_4, 2),
        'next_8_weeks':         round(next_8, 2),
        'next_12_weeks':        round(next_12, 2),
        'peak_week':            str(peak_week.date()) if hasattr(peak_week, 'date') else str(peak_week),
        'peak_expected_sales':  round(peak_val, 2),
    }