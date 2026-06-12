import pandas as pd


def sales_by_store(df, group_col='Store', sales_col='Weekly_Sales'):
    """إجمالي المبيعات لكل متجر/فرع"""
    return (
        df.groupby(group_col)[sales_col]
        .agg(['sum', 'mean', 'max'])
        .rename(columns={'sum': 'total', 'mean': 'avg_weekly', 'max': 'best_week'})
        .round(2)
        .reset_index()
        .sort_values('total', ascending=False)
    )


def monthly_sales(df, date_col='Date', sales_col='Weekly_Sales'):
    """المبيعات الشهرية"""
    df = df.copy()
    df['month'] = df[date_col].dt.to_period('M')
    return (
        df.groupby('month')[sales_col]
        .sum()
        .reset_index()
        .rename(columns={sales_col: 'total'})
    )


def yearly_sales(df, date_col='Date', sales_col='Weekly_Sales'):
    """المبيعات السنوية"""
    df = df.copy()
    df['year'] = df[date_col].dt.year
    return (
        df.groupby('year')[sales_col]
        .sum()
        .reset_index()
        .rename(columns={sales_col: 'total'})
    )


def holiday_vs_normal(df, sales_col='Weekly_Sales'):
    """مقارنة مبيعات الأعياد مقابل العادية"""
    if 'Holiday_Flag' not in df.columns:
        return None
    return (
        df.groupby('Holiday_Flag')[sales_col]
        .agg(['mean', 'sum', 'count'])
        .rename(index={0: 'Normal Week', 1: 'Holiday Week'})
        .rename(columns={'mean': 'avg', 'sum': 'total', 'count': 'weeks'})
        .round(2)
        .reset_index()
        .rename(columns={'Holiday_Flag': 'type'})
    )


def top_stores(df, group_col='Store', sales_col='Weekly_Sales', n=5):
    """أفضل N متاجر"""
    return sales_by_store(df, group_col, sales_col).head(n)


def correlation_analysis(df, sales_col='Weekly_Sales'):
    """علاقة العوامل الخارجية بالمبيعات"""
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if sales_col not in numeric_cols:
        return None
    cols = [sales_col] + [c for c in numeric_cols if c != sales_col]
    return df[cols].corr()[sales_col].drop(sales_col).round(4)