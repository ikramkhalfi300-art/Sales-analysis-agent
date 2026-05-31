from prophet import Prophet
import pandas as pd

def prepare_prophet_data(df, date_col='Date', sales_col='Weekly_Sales'):
    """يقبل أي اسم عمود"""
    if df[date_col].dtype != 'datetime64[ns]':
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
    
    weekly_total = (
        df.groupby(date_col)[sales_col]
        .sum()
        .reset_index()
        .rename(columns={date_col: 'ds', sales_col: 'y'})
    )
    return weekly_total

def train_and_forecast(df, weeks=12, date_col='Date', sales_col='Weekly_Sales'):
    prophet_data = prepare_prophet_data(df, date_col, sales_col)
    
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
    )
    
    model.fit(prophet_data)
    future = model.make_future_dataframe(periods=weeks, freq='W')
    forecast = model.predict(future)
    
    return forecast, prophet_data

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