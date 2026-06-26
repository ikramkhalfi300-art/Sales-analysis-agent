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


# ── كلمات مفتاحية تدل على عمود تجميع حقيقي ──────────────
_GROUP_KEYWORDS = [
    # متاجر وفروع
    'store', 'branch', 'outlet', 'location', 'site', 'shop',
    # مناطق
    'region', 'area', 'zone', 'territory', 'district', 'city',
    'country', 'market', 'state', 'province',
    # تصنيفات
    'segment', 'category', 'channel', 'division', 'department',
    'product', 'sku', 'brand', 'line', 'type', 'class',
    # عملاء
    'customer', 'client', 'account', 'agent', 'rep', 'team',
    # عربي
    'متجر', 'فرع', 'منطقة', 'قسم', 'عميل', 'فئة',
    # فرنسي
    'magasin', 'region', 'agence', 'succursale',
]

# ── كلمات تدل على أعمدة يجب تجاهلها كـ group ──────────
_EXCLUDE_KEYWORDS = [
    'year', 'month', 'week', 'day', 'date', 'time', 'hour',
    'quarter', 'سنة', 'شهر', 'أسبوع', 'يوم',
    'id', 'index', 'idx', 'row', 'num', 'no', 'seq',
    'flag', 'indicator', 'bool', 'status', 'is_',
    'price', 'cost', 'tax', 'discount', 'rate', 'pct', 'percent',
    'qty', 'quantity', 'count', 'amount', 'total', 'sum', 'avg',
    'unnamed',
]


def _score_column(col: str, series: pd.Series, sales_col: str, date_col: str) -> float:
    """
    يعطي كل عمود مرشح درجة من 0 إلى 100.
    كلما كانت الدرجة أعلى كلما كان العمود أفضل كـ group column.

    معايير التقييم:
    - الاسم يحتوي كلمة مفتاحية للـ group  → +40
    - الاسم يحتوي كلمة مفتاحية للاستبعاد → -100 (استبعاد فوري)
    - عدد القيم الفريدة بين 2 و 50         → +30
    - عدد القيم الفريدة بين 2 و 20         → +10 إضافي
    - النوع object أو int                  → +10
    - الإيراد موزع بشكل معقول (std > 0)   → +10
    """
    col_lower = col.lower().strip()

    # استبعاد فوري للأعمدة التي تطابق كلمات الاستبعاد
    for excl in _EXCLUDE_KEYWORDS:
        if excl in col_lower:
            return -1.0

    score = 0.0

    # مطابقة كلمات المجموعات
    for kw in _GROUP_KEYWORDS:
        if kw in col_lower:
            score += 40
            break

    # عدد القيم الفريدة
    n_unique = series.nunique()
    if 2 <= n_unique <= 50:
        score += 30
    elif 51 <= n_unique <= 100:
        score += 10
    else:
        # أقل من 2 أو أكثر من 100 → ليس عمود تجميع مفيداً
        return -1.0

    if 2 <= n_unique <= 20:
        score += 10  # مثالي للتجميع

    # النوع
    if series.dtype == 'object':
        score += 10
    elif series.dtype in ['int64', 'int32']:
        score += 8
    elif series.dtype in ['float64', 'float32']:
        # float columns نادراً ما تكون group columns حقيقية
        score -= 10

    return score


def get_summary(df, date_col, sales_col):
    """
    يقبل أي اسم عمود — ليس مقيداً بـ Walmart dataset.
    اكتشاف group column محسّن: يستخدم نظام تقييم متعدد المعايير
    بدلاً من nunique() < 100 البسيط.
    """
    summary = {
        'total_records':    len(df),
        'date_range':       f"{df[date_col].min().date()} → {df[date_col].max().date()}",
        'total_sales':      round(df[sales_col].sum(), 2),
        'avg_weekly_sales': round(df[sales_col].mean(), 2),
        'max_single_week':  round(df[sales_col].max(), 2),
        'min_single_week':  round(df[sales_col].min(), 2),
    }

    # ── اكتشاف group column بنظام التقييم ────────────────
    best_col   = None
    best_score = 0.0

    for col in df.columns:
        if col in [date_col, sales_col]:
            continue

        score = _score_column(col, df[col], sales_col, date_col)
        if score <= 0:
            continue

        # تحقق إضافي: هل التجميع بهذا العمود يعطي نتائج منطقية؟
        try:
            grouped = df.groupby(col)[sales_col].sum()
            if len(grouped) < 2:
                continue
            if grouped.sum() <= 0:
                continue
            # هل هناك تباين في الإيرادات؟ (الـ std > 0 يعني أن الوحدات مختلفة)
            if grouped.std() > 0:
                score += 10
        except Exception:
            continue

        if score > best_score:
            best_score = score
            best_col   = col

    # ── ملء ملخص المجموعة إذا وُجد عمود مناسب ───────────
    if best_col is not None:
        try:
            grouped = df.groupby(best_col)[sales_col].sum()
            summary['group_col']   = best_col
            summary['num_groups']  = int(df[best_col].nunique())
            summary['best_group']  = str(grouped.idxmax())
            summary['worst_group'] = str(grouped.idxmin())
            summary['group_score'] = round(best_score, 1)
        except Exception:
            pass  # إذا فشل التجميع لا نضيف group_col

    return summary