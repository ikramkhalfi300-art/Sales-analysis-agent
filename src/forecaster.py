import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def prepare_data(df, date_col, sales_col):
    weekly = (
        df.groupby(date_col)[sales_col]
        .sum()
        .reset_index()
        .rename(columns={date_col: 'ds', sales_col: 'y'})
        .sort_values('ds')
    )
    return weekly

def train_and_forecast(df, weeks=12, date_col='Date', sales_col='Weekly_Sales'):
    data = prepare_data(df, date_col, sales_col)

    n = len(data)
    if n >= 104:
        seasonal_periods = 52
    elif n >= 24:
        seasonal_periods = 12
    else:
        seasonal_periods = None

    try:
        if seasonal_periods:
            model = ExponentialSmoothing(
                data['y'],
                trend='add',
                seasonal='add',
                seasonal_periods=seasonal_periods
            ).fit()
        else :model = ExponentialSmoothing(
                data['y'],
                trend='add',
                seasonal_periods=None
            ).fit()
    except :
        from statsmodels.tsa.holtwinters import SimpleExpSmoothing
        model = SimpleExpSmoothing(data['y']).fit()
    
    forecast_values = model.forecast(weeks)
    
    last_date = data['ds'].max()
    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(weeks=1),
        periods=weeks,
        freq='W'
    )
    
    forecast_df = pd.DataFrame({
        'ds': future_dates,
        'yhat': forecast_values.values,
        'yhat_lower': forecast_values.values * 0.9,
        'yhat_upper': forecast_values.values * 1.1
    })
    
    prophet_data = data
    full_forecast = pd.concat([
        data.rename(columns={'y': 'yhat'}).assign(
            yhat_lower=data['y'] * 0.9,
            yhat_upper=data['y'] * 1.1
        ),
        forecast_df
    ]).reset_index(drop=True)
    
    return full_forecast, prophet_data

def get_forecast_summary(forecast, weeks=12):
    future = forecast.tail(weeks)
    return {
        'next_4_weeks': round(future.head(4)['yhat'].sum(), 0),
        'next_8_weeks': round(future.head(8)['yhat'].sum(), 0),
        'next_12_weeks': round(future['yhat'].sum(), 0),
        'peak_week': str(future.loc[future['yhat'].idxmax(), 'ds'].date()),
        'peak_expected_sales': round(future['yhat'].max(), 0),
        'avg_weekly_forecast': round(future['yhat'].mean(), 0),
    }