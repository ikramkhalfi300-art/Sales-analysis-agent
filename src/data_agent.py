"""
data_agent.py — وكيل البيانات
==============================
المسؤولية الوحيدة: تحميل البيانات وتنظيفها وتلخيصها

يدمج:
  - data_loader.py  (تحميل CSV/Excel)
  - data_cleaner.py (تنظيف وتقرير الجودة)
  - get_summary()   (اكتشاف الأعمدة وملخص البيانات)

القاعدة الذهبية:
  - لا يحلل، لا يتوقع، لا يرسم
  - يبلّغ عن كل مشكلة في البيانات — لا يخفيها
  - يعمل مع أي dataset وليس فقط Walmart
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple


# ════════════════════════════════════════════════
# 1. DATA CLEANER — منطق التنظيف الكامل
# ════════════════════════════════════════════════

def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    تنظيف شامل للـ DataFrame مع تقرير مفصل.

    الخطوات بالترتيب:
      1. تنظيف أسماء الأعمدة
      2. إزالة الصفوف المكررة
      3. اكتشاف عمود التاريخ وتحويله
      4. إزالة الصفوف بتواريخ غير صالحة
      5. حذف أعمدة فارغة كلياً
      6. تقرير القيم المفقودة

    Returns:
        (df_clean, report_dict)
    """
    report = {
        'original_rows':    len(df),
        'original_cols':    len(df.columns),
        'steps':            [],
        'n_duplicates':     0,
        'n_missing':        0,
        'missing_pct':      0.0,
        'n_outliers':       0,
        'outlier_pct':      0.0,
        'completeness':     100.0,
        'rating':           'Excellent',
        'date_col_found':   None,
        'warnings':         [],
    }

    df = df.copy()

    # ── Step 1: تنظيف أسماء الأعمدة ─────────────
    original_cols = list(df.columns)
    df.columns = [str(c).strip() for c in df.columns]
    renamed = [(o, n) for o, n in zip(original_cols, df.columns) if o != n]
    if renamed:
        report['steps'].append(f"Cleaned {len(renamed)} column name(s)")

    # ── Step 2: إزالة المكررات ───────────────────
    n_before = len(df)
    df = df.drop_duplicates()
    n_dups = n_before - len(df)
    report['n_duplicates'] = n_dups
    if n_dups > 0:
        report['steps'].append(f"Removed {n_dups} duplicate row(s)")

    # ── Step 3: اكتشاف وتحويل عمود التاريخ ──────
    date_col_found = _detect_and_parse_dates(df, report)
    report['date_col_found'] = date_col_found

    # ── Step 4: إزالة صفوف التاريخ الفاشلة ──────
    if date_col_found:
        n_before = len(df)
        df = df.dropna(subset=[date_col_found])
        n_removed = n_before - len(df)
        if n_removed > 0:
            report['steps'].append(
                f"Removed {n_removed} row(s) with unparseable dates in '{date_col_found}'"
            )

    # ── Step 5: حذف الأعمدة الفارغة كلياً ────────
    empty_cols = [c for c in df.columns if df[c].isna().all()]
    if empty_cols:
        df = df.drop(columns=empty_cols)
        report['steps'].append(f"Dropped {len(empty_cols)} fully-empty column(s): {empty_cols}")

    # ── Step 6: تقرير القيم المفقودة ────────────
    n_missing = int(df.isnull().sum().sum())
    total_cells = len(df) * len(df.columns)
    missing_pct = round(n_missing / max(total_cells, 1) * 100, 2)
    report['n_missing']   = n_missing
    report['missing_pct'] = missing_pct
    if n_missing > 0:
        missing_by_col = df.isnull().sum()
        missing_by_col = missing_by_col[missing_by_col > 0].to_dict()
        report['missing_by_col'] = missing_by_col
        report['steps'].append(
            f"Found {n_missing} missing value(s) ({missing_pct:.1f}%) — retained for analysis"
        )

    # ── Step 7: حساب الـ Outliers (IQR) ──────────
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    total_outliers = 0
    for col in numeric_cols:
        q1  = df[col].quantile(0.25)
        q3  = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            low  = q1 - 1.5 * iqr
            high = q3 + 1.5 * iqr
            n_out = int(((df[col] < low) | (df[col] > high)).sum())
            total_outliers += n_out
    report['n_outliers']  = total_outliers
    report['outlier_pct'] = round(total_outliers / max(len(df), 1) * 100, 2)

    # ── Step 8: تقييم الجودة ─────────────────────
    dup_pct      = n_dups / max(n_before, 1) * 100
    completeness = round(
        max(0, 100 - missing_pct - dup_pct - report['outlier_pct'] * 0.5), 1
    )
    report['completeness'] = completeness
    report['final_rows']   = len(df)
    report['final_cols']   = len(df.columns)

    if completeness >= 95:
        report['rating'] = 'Excellent'
    elif completeness >= 85:
        report['rating'] = 'Good'
    elif completeness >= 70:
        report['rating'] = 'Fair'
    else:
        report['rating'] = 'Poor'
        report['warnings'].append(
            "Data quality is Poor — results may be unreliable. "
            "Consider cleaning the source data before analysis."
        )

    return df, report


def _detect_and_parse_dates(df: pd.DataFrame, report: dict) -> Optional[str]:
    """
    اكتشاف عمود التاريخ تلقائياً وتحويله إلى datetime.
    يجرب عدة صيغ تاريخ شائعة.
    """
    # ── الأعمدة المرشحة بالاسم ───────────────────
    date_keywords = ['date', 'time', 'تاريخ', 'دت', 'dt', 'day', 'period', 'week', 'month']
    candidates = [
        c for c in df.columns
        if any(k in c.lower() for k in date_keywords)
    ]

    # إذا لم نجد بالاسم → جرب كل عمود
    if not candidates:
        candidates = list(df.columns)

    date_formats = [
        '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y',
        '%d-%m-%Y', '%m-%d-%Y', '%Y/%m/%d',
        '%d.%m.%Y', '%Y.%m.%d',
        '%d %b %Y', '%b %d, %Y',
    ]

    for col in candidates:
        # إذا كان بالفعل datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col

        # جرب التحويل التلقائي أولاً
        try:
            converted = pd.to_datetime(df[col], infer_datetime_format=True, errors='coerce')
            success_rate = converted.notna().mean()
            if success_rate >= 0.8:
                df[col] = converted
                report['steps'].append(
                    f"Parsed '{col}' as datetime (auto-infer, {success_rate*100:.0f}% success)"
                )
                return col
        except Exception:
            pass

        # جرب الصيغ المعروفة
        for fmt in date_formats:
            try:
                converted = pd.to_datetime(df[col], format=fmt, errors='coerce')
                success_rate = converted.notna().mean()
                if success_rate >= 0.8:
                    df[col] = converted
                    report['steps'].append(
                        f"Parsed '{col}' as datetime (format={fmt}, {success_rate*100:.0f}% success)"
                    )
                    return col
            except Exception:
                continue

    report['warnings'].append(
        "Could not auto-detect a date column. "
        "Please ensure the Date column is in a standard format (YYYY-MM-DD recommended)."
    )
    return None


# ════════════════════════════════════════════════
# 2. DATA LOADER — تحميل الملفات
# ════════════════════════════════════════════════

def load_data(
    path: Optional[str] = None,
    dataframe=None,
) -> Tuple[pd.DataFrame, dict]:
    """
    تحميل البيانات من ملف أو DataFrame مباشر + تنظيفها.

    Args:
        path:      مسار ملف CSV أو Excel
        dataframe: pandas DataFrame مباشر (من Streamlit uploader)

    Returns:
        (df_clean, quality_report)

    Raises:
        ValueError: إذا لم يُعطَ path أو dataframe
        ValueError: إذا كان نوع الملف غير مدعوم
    """
    if dataframe is not None:
        df = dataframe.copy()

    elif path is not None:
        ext = path.lower()
        if ext.endswith('.csv'):
            # جرب عدة encodings شائعة
            for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(path, encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                df = pd.read_csv(path, encoding='utf-8', errors='replace')

        elif ext.endswith(('.xlsx', '.xls', '.xlsm')):
            df = pd.read_excel(path)

        else:
            raise ValueError(
                f"❌ Unsupported file type: '{path}'. "
                "Supported formats: CSV (.csv), Excel (.xlsx, .xls, .xlsm)"
            )

    else:
        raise ValueError(
            "❌ Provide either 'path' (file path) or 'dataframe' (pandas DataFrame)."
        )

    # تنظيف البيانات
    df_clean, report = clean_data(df)
    return df_clean, report


# ════════════════════════════════════════════════
# 3. GROUP COLUMN DETECTION — اكتشاف عمود التجميع
# ════════════════════════════════════════════════

# كلمات تدل على عمود تجميع حقيقي
_GROUP_KEYWORDS = [
    # متاجر وفروع
    'store', 'branch', 'outlet', 'location', 'site', 'shop',
    # مناطق جغرافية
    'region', 'area', 'zone', 'territory', 'district',
    'city', 'country', 'market', 'state', 'province',
    # تصنيفات المنتجات
    'segment', 'category', 'channel', 'division', 'department',
    'product', 'sku', 'brand', 'line', 'type', 'class',
    # العملاء والمبيعات
    'customer', 'client', 'account', 'agent', 'rep', 'team',
    # عربي
    'متجر', 'فرع', 'منطقة', 'قسم', 'عميل', 'فئة',
    # فرنسي
    'magasin', 'agence', 'succursale',
]

# كلمات تدل على أعمدة يجب تجاهلها كـ group
_EXCLUDE_KEYWORDS = [
    # زمن
    'year', 'month', 'week', 'day', 'date', 'time', 'hour',
    'quarter', 'سنة', 'شهر', 'أسبوع', 'يوم',
    # معرفات تقنية
    'id', 'index', 'idx', 'row', 'num', 'no', 'seq', 'unnamed',
    # مؤشرات ثنائية
    'flag', 'indicator', 'bool', 'status', 'is_',
    # مالية/كمية — ليست مجموعات
    'price', 'cost', 'tax', 'discount', 'rate', 'pct', 'percent',
    'qty', 'quantity', 'count', 'amount', 'total', 'sum', 'avg',
    'revenue', 'sales', 'profit', 'margin',
]


def _score_column(
    col: str,
    series: pd.Series,
    sales_col: str,
    date_col: str,
) -> float:
    """
    نظام تقييم متعدد المعايير لاختيار أفضل عمود تجميع.

    الدرجة القصوى النظرية: 100
    معايير:
      +40  — الاسم يحتوي كلمة مفتاحية للـ group
      -inf — الاسم يحتوي كلمة استبعاد (يُرجع -1 فوراً)
      +30  — عدد القيم الفريدة بين 2 و50
      +10  — إضافي إذا كانت بين 2 و20 (مثالي)
      +10  — النوع object أو int
      +10  — تباين الإيرادات بين المجموعات (std > 0)
    """
    col_lower = col.lower().strip()

    # استبعاد فوري
    for excl in _EXCLUDE_KEYWORDS:
        if excl in col_lower:
            return -1.0

    # تجاهل أعمدة تاريخ أو مبيعات
    if col in [sales_col, date_col]:
        return -1.0

    score = 0.0

    # كلمات المجموعات
    for kw in _GROUP_KEYWORDS:
        if kw in col_lower:
            score += 40
            break

    # عدد القيم الفريدة
    try:
        n_unique = series.nunique()
    except Exception:
        return -1.0

    if 2 <= n_unique <= 50:
        score += 30
        if 2 <= n_unique <= 20:
            score += 10  # مثالي
    elif 51 <= n_unique <= 100:
        score += 10
    else:
        return -1.0  # أقل من 2 أو أكثر من 100

    # نوع البيانات
    if series.dtype == 'object':
        score += 10
    elif series.dtype in ['int64', 'int32', 'int16', 'int8']:
        score += 8
    elif series.dtype in ['float64', 'float32']:
        score -= 10  # float نادراً ما يكون group column

    return score


# ════════════════════════════════════════════════
# 4. GET SUMMARY — ملخص البيانات الكامل
# ════════════════════════════════════════════════

def get_summary(df: pd.DataFrame, date_col: str, sales_col: str) -> dict:
    """
    يولّد ملخصاً شاملاً للبيانات مع اكتشاف تلقائي لعمود التجميع.

    يعمل مع أي dataset وليس مقيداً بـ Walmart.

    Args:
        df:        DataFrame نظيف
        date_col:  اسم عمود التاريخ
        sales_col: اسم عمود المبيعات

    Returns:
        dict يحتوي على:
          - إحصاءات أساسية (total, avg, max, min)
          - النطاق الزمني
          - معلومات عمود التجميع إذا اكتُشف
    """
    summary = {
        'total_records':    len(df),
        'date_range':       _safe_date_range(df, date_col),
        'total_sales':      round(float(df[sales_col].sum()), 2),
        'avg_weekly_sales': round(float(df[sales_col].mean()), 2),
        'max_single_week':  round(float(df[sales_col].max()), 2),
        'min_single_week':  round(float(df[sales_col].min()), 2),
        'std_sales':        round(float(df[sales_col].std()), 2),
        'median_sales':     round(float(df[sales_col].median()), 2),
        'n_periods':        int(df[date_col].nunique()) if date_col in df.columns else 0,
    }

    # ── اكتشاف عمود التجميع ──────────────────────
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
            if grouped.std() > 0:
                score += 10
        except Exception:
            continue

        if score > best_score:
            best_score = score
            best_col   = col

    # ── ملء بيانات المجموعة ──────────────────────
    if best_col is not None:
        try:
            grouped = df.groupby(best_col)[sales_col].sum()
            summary['group_col']   = best_col
            summary['num_groups']  = int(df[best_col].nunique())
            summary['best_group']  = str(grouped.idxmax())
            summary['worst_group'] = str(grouped.idxmin())
            summary['group_score'] = round(best_score, 1)
        except Exception:
            pass

    return summary


def _safe_date_range(df: pd.DataFrame, date_col: str) -> str:
    """استخراج النطاق الزمني بأمان"""
    try:
        if date_col in df.columns and pd.api.types.is_datetime64_any_dtype(df[date_col]):
            min_d = df[date_col].min().date()
            max_d = df[date_col].max().date()
            return f"{min_d} → {max_d}"
    except Exception:
        pass
    return "N/A"


# ════════════════════════════════════════════════
# 5. PRINT REPORT — طباعة تقرير التنظيف (للـ CLI)
# ════════════════════════════════════════════════

def print_report(report: dict) -> None:
    """طباعة تقرير التنظيف في الـ terminal"""
    print("\n" + "="*55)
    print("  DATA CLEANING REPORT")
    print("="*55)
    print(f"  Original:    {report.get('original_rows', 0):,} rows × "
          f"{report.get('original_cols', 0)} cols")
    print(f"  Final:       {report.get('final_rows', 0):,} rows × "
          f"{report.get('final_cols', 0)} cols")
    print(f"  Duplicates:  {report.get('n_duplicates', 0)}")
    print(f"  Missing:     {report.get('n_missing', 0)} "
          f"({report.get('missing_pct', 0):.1f}%)")
    print(f"  Outliers:    {report.get('n_outliers', 0)} "
          f"({report.get('outlier_pct', 0):.1f}%)")
    print(f"  Quality:     {report.get('completeness', 0):.1f}/100 "
          f"— {report.get('rating', 'Unknown')}")
    print(f"  Date Col:    {report.get('date_col_found', 'Not found')}")

    steps = report.get('steps', [])
    if steps:
        print("\n  Steps performed:")
        for s in steps:
            print(f"    ✓ {s}")

    warnings = report.get('warnings', [])
    if warnings:
        print("\n  ⚠️  Warnings:")
        for w in warnings:
            print(f"    ! {w}")

    print("="*55 + "\n")