import pandas as pd
from src.data_cleaner import clean_data, print_report


def load_data(path=None, dataframe=None):
    """
    يقبل:
    - path: مسار ملف CSV أو Excel
    - dataframe: pandas DataFrame مباشرة (من Streamlit)
    """
    if dataframe is not None:
        df = dataframe.copy()
    elif path is not None:
        if path.endswith('.csv'):
            df = pd.read_csv(path)
        elif path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(path)
        else:
            raise ValueError("❌ Unsupported file type. Use CSV or Excel.")
    else:
        raise ValueError("❌ Provide either path or dataframe.")

    df, report = clean_data(df)
    return df, report


def get_summary(df, date_col, sales_col):
    """
    يقبل أي اسم عمود — ليس مقيداً بـ Walmart dataset
    """
    summary = {
        'total_records':    len(df),
        'date_range':       f"{df[date_col].min().date()} → {df[date_col].max().date()}",
        'total_sales':      round(df[sales_col].sum(), 2),
        'avg_weekly_sales': round(df[sales_col].mean(), 2),
        'max_single_week':  round(df[sales_col].max(), 2),
        'min_single_week':  round(df[sales_col].min(), 2),
    }

    # اكتشاف عمود المتجر/الفرع تلقائياً
    for col in df.columns:
        if col in [date_col, sales_col]:
            continue
        if df[col].dtype in ['int64', 'object']:
            if df[col].nunique() < 100:
                try:
                    grouped = df.groupby(col)[sales_col].sum()
                    if len(grouped) > 0 and grouped.sum() > 0:
                        summary['group_col']   = col
                        summary['num_groups']  = int(df[col].nunique())
                        summary['best_group']  = str(grouped.idxmax())
                        summary['worst_group'] = str(grouped.idxmin())
                        break
                except Exception:
                    continue

    return summary