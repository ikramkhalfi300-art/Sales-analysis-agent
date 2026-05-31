import pandas as pd

def sales_by_store(df):
    """إجمالي المبيعات لكل متجر"""
    return (
        df.groupby('Store')['Weekly_Sales']
        .agg(['sum', 'mean', 'max'])
        .rename(columns={'sum': 'total', 'mean': 'avg_weekly', 'max': 'best_week'})
        .round(2)
        .reset_index()
        .sort_values('total', ascending=False)
    )

def monthly_sales(df):
    """المبيعات الشهرية لكل المتاجر مجتمعة"""
    df = df.copy()
    df['month'] = df['Date'].dt.to_period('M')
    return (
        df.groupby('month')['Weekly_Sales']
        .sum()
        .reset_index()
        .rename(columns={'Weekly_Sales': 'total'})
    )

def yearly_sales(df):
    """المبيعات السنوية"""
    df = df.copy()
    df['year'] = df['Date'].dt.year
    return (
        df.groupby('year')['Weekly_Sales']
        .sum()
        .reset_index()
        .rename(columns={'Weekly_Sales': 'total'})
    )

def holiday_vs_normal(df):
    """مقارنة مبيعات الأعياد مقابل العادية"""
    return (
        df.groupby('Holiday_Flag')['Weekly_Sales']
        .agg(['mean', 'sum', 'count'])
        .rename(index={0: 'Normal Week', 1: 'Holiday Week'})
        .rename(columns={'mean': 'avg', 'sum': 'total', 'count': 'weeks'})
        .round(2)
        .reset_index()
        .rename(columns={'Holiday_Flag': 'type'})
    )

def top_stores(df, n=5):
    """أفضل N متاجر"""
    store_sales = sales_by_store(df)
    return store_sales.head(n)

def correlation_analysis(df):
    """علاقة المبيعات مع العوامل الخارجية"""
    cols = ['Weekly_Sales', 'Temperature', 'Fuel_Price', 'CPI', 'Unemployment']
    return df[cols].corr()['Weekly_Sales'].drop('Weekly_Sales').round(4)