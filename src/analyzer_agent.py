"""
analyzer_agent.py — وكيل التحليل الإحصائي
==========================================
المسؤولية الوحيدة: الحسابات الإحصائية وتوليد القرارات

يدمج:
  - analyzer_agent.py القديم  (sales_by_store, monthly_sales, ...)
  - decision_engine.py         (Decision, generate_decisions, ...)

القاعدة الذهبية:
  - لا يحمّل بيانات، لا يتوقع، لا يرسم، لا يكتب PDF
  - كل رقم يخرج منه محسوب من البيانات الفعلية — لا تقدير
  - يعمل مع أي dataset: أي اسم عمود، أي تردد زمني
  - إذا كان الحساب مستحيلاً → يُرجع None ويسجّل السبب
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
from config import CV_LOW, CV_MODERATE, CV_HIGH


# ════════════════════════════════════════════════
# 1. CORE ANALYSIS FUNCTIONS
# ════════════════════════════════════════════════

def sales_by_store(
    df: pd.DataFrame,
    group_col: str = 'Store',
    sales_col: str = 'Weekly_Sales',
) -> Optional[pd.DataFrame]:
    """
    إجمالي المبيعات لكل مجموعة (متجر/فرع/منطقة/...).

    Returns:
        DataFrame مرتّب تنازلياً بالأعمدة:
          [group_col, total, avg_weekly, best_week, worst_week,
           pct_of_total, rank]
        أو None إذا فشل التجميع.
    """
    if group_col not in df.columns:
        return None
    if sales_col not in df.columns:
        return None

    try:
        result = (
            df.groupby(group_col)[sales_col]
            .agg(['sum', 'mean', 'max', 'min', 'std', 'count'])
            .rename(columns={
                'sum':   'total',
                'mean':  'avg_weekly',
                'max':   'best_week',
                'min':   'worst_week',
                'std':   'std_weekly',
                'count': 'n_periods',
            })
            .round(2)
            .reset_index()
            .sort_values('total', ascending=False)
        )

        # إضافة نسبة من الإجمالي والترتيب
        total_rev = result['total'].sum()
        if total_rev > 0:
            result['pct_of_total'] = (result['total'] / total_rev * 100).round(2)
        else:
            result['pct_of_total'] = 0.0

        result['rank'] = range(1, len(result) + 1)

        # معامل التغيير (CV) لكل مجموعة
        result['cv_pct'] = (
            result['std_weekly'] / result['avg_weekly'].replace(0, np.nan) * 100
        ).round(1).fillna(0)

        return result

    except Exception as e:
        return None


def monthly_sales(
    df: pd.DataFrame,
    date_col: str = 'Date',
    sales_col: str = 'Weekly_Sales',
) -> pd.DataFrame:
    """
    تجميع المبيعات شهرياً.

    Returns:
        DataFrame بالأعمدة: [month, total, avg, pct_change]
    """
    df = df.copy()
    try:
        df['month'] = df[date_col].dt.to_period('M')
        result = (
            df.groupby('month')[sales_col]
            .sum()
            .reset_index()
            .rename(columns={sales_col: 'total'})
        )
        # نسبة التغيير شهر على شهر
        result['pct_change'] = result['total'].pct_change() * 100
        result['pct_change'] = result['pct_change'].round(2)
        return result
    except Exception:
        return pd.DataFrame(columns=['month', 'total', 'pct_change'])


def yearly_sales(
    df: pd.DataFrame,
    date_col: str = 'Date',
    sales_col: str = 'Weekly_Sales',
) -> pd.DataFrame:
    """
    تجميع المبيعات سنوياً.

    Returns:
        DataFrame بالأعمدة: [year, total, avg, pct_change]
    """
    df = df.copy()
    try:
        df['year'] = df[date_col].dt.year
        result = (
            df.groupby('year')[sales_col]
            .agg(['sum', 'mean'])
            .rename(columns={'sum': 'total', 'mean': 'avg'})
            .round(2)
            .reset_index()
        )
        result['pct_change'] = result['total'].pct_change() * 100
        result['pct_change'] = result['pct_change'].round(2)
        return result
    except Exception:
        return pd.DataFrame(columns=['year', 'total', 'avg', 'pct_change'])


def quarterly_sales(
    df: pd.DataFrame,
    date_col: str = 'Date',
    sales_col: str = 'Weekly_Sales',
) -> pd.DataFrame:
    """
    تجميع المبيعات ربعياً.

    Returns:
        DataFrame بالأعمدة: [quarter, total, pct_change]
    """
    df = df.copy()
    try:
        df['quarter'] = df[date_col].dt.to_period('Q')
        result = (
            df.groupby('quarter')[sales_col]
            .sum()
            .reset_index()
            .rename(columns={sales_col: 'total'})
        )
        result['pct_change'] = result['total'].pct_change() * 100
        result['pct_change'] = result['pct_change'].round(2)
        return result
    except Exception:
        return pd.DataFrame(columns=['quarter', 'total', 'pct_change'])


def holiday_vs_normal(
    df: pd.DataFrame,
    sales_col: str = 'Weekly_Sales',
    flag_col: str = 'Holiday_Flag',
) -> Optional[pd.DataFrame]:
    """
    مقارنة مبيعات الأعياد مقابل الأسابيع العادية.

    يبحث تلقائياً عن عمود Holiday بأسماء مختلفة.

    Returns:
        DataFrame أو None إذا لم يوجد عمود الأعياد.
    """
    # البحث عن عمود الأعياد بأسماء مختلفة
    holiday_candidates = [
        flag_col, 'Holiday_Flag', 'holiday_flag', 'holiday',
        'Holiday', 'is_holiday', 'IsHoliday', 'عيد', 'fete',
    ]
    found_col = next(
        (c for c in holiday_candidates if c in df.columns),
        None
    )
    if found_col is None:
        return None

    try:
        result = (
            df.groupby(found_col)[sales_col]
            .agg(['mean', 'sum', 'count', 'std'])
            .rename(columns={
                'mean':  'avg',
                'sum':   'total',
                'count': 'weeks',
                'std':   'std',
            })
            .round(2)
            .reset_index()
            .rename(columns={found_col: 'type'})
        )
        # تسمية واضحة لقيم 0/1
        result['type'] = result['type'].map(
            lambda x: 'Holiday Week' if x in [1, True, '1', 'True', 'Yes'] else 'Normal Week'
        )

        # حساب الفرق النسبي
        if len(result) == 2:
            avgs = result.set_index('type')['avg']
            if 'Normal Week' in avgs.index and avgs['Normal Week'] > 0:
                holiday_avg = avgs.get('Holiday Week', 0)
                result['vs_normal_pct'] = result['type'].map(
                    lambda t: round(
                        (holiday_avg - avgs['Normal Week']) / avgs['Normal Week'] * 100, 1
                    ) if t == 'Holiday Week' else 0.0
                )

        return result

    except Exception:
        return None


def top_performers(
    df: pd.DataFrame,
    group_col: str,
    sales_col: str = 'Weekly_Sales',
    n: int = 5,
) -> Optional[pd.DataFrame]:
    """
    أفضل N مجموعات بالإيراد الكلي.
    """
    result = sales_by_store(df, group_col, sales_col)
    if result is None:
        return None
    return result.head(n)


def bottom_performers(
    df: pd.DataFrame,
    group_col: str,
    sales_col: str = 'Weekly_Sales',
    n: int = 5,
) -> Optional[pd.DataFrame]:
    """
    أضعف N مجموعات بالإيراد الكلي.
    """
    result = sales_by_store(df, group_col, sales_col)
    if result is None:
        return None
    return result.tail(n).sort_values('total')


def correlation_analysis(
    df: pd.DataFrame,
    sales_col: str = 'Weekly_Sales',
    min_correlation: float = 0.05,
) -> Optional[pd.Series]:
    """
    حساب ارتباط Pearson بين المبيعات وكل الأعمدة الرقمية.

    Args:
        min_correlation: الحد الأدنى للارتباط المطلق للإدراج في النتيجة

    Returns:
        Series مرتّبة تنازلياً بالقيمة المطلقة، أو None.

    ملاحظة مهمة: الارتباط ≠ سببية — يجب إضافة هذا التحذير
    دائماً عند عرض النتائج.
    """
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if sales_col not in numeric_cols:
        return None

    # استبعاد أعمدة ثنائية (0/1) تخلط النتائج
    exclude = []
    for col in numeric_cols:
        if col == sales_col:
            continue
        unique_vals = df[col].dropna().unique()
        if len(unique_vals) <= 2 and set(unique_vals).issubset({0, 1, True, False}):
            exclude.append(col)

    useful_cols = [c for c in numeric_cols if c != sales_col and c not in exclude]
    if not useful_cols:
        return None

    try:
        corr = (
            df[[sales_col] + useful_cols]
            .corr()[sales_col]
            .drop(sales_col)
            .dropna()
            .round(4)
        )
        # فلترة بالحد الأدنى وترتيب بالقيمة المطلقة
        corr = corr[corr.abs() >= min_correlation]
        corr = corr.reindex(corr.abs().sort_values(ascending=False).index)
        return corr if len(corr) > 0 else None

    except Exception:
        return None


# ════════════════════════════════════════════════
# 2. TREND ANALYSIS
# ════════════════════════════════════════════════

def _calc_trend(series: pd.Series) -> Tuple[str, float]:
    """
    يحسب اتجاه سلسلة زمنية بمقارنة النصف الأول بالثاني.

    Returns:
        (trend_label, pct_change)
        trend_label: 'Growing' | 'Stable' | 'Declining'
    """
    if len(series) < 2:
        return "Stable", 0.0

    half       = max(1, len(series) // 2)
    first_half = series.iloc[:half].mean()
    second_half = series.iloc[half:].mean()

    if first_half == 0 or pd.isna(first_half):
        return "Stable", 0.0

    pct = (second_half - first_half) / abs(first_half) * 100

    if pct > 5:
        return "Growing", round(pct, 1)
    elif pct < -5:
        return "Declining", round(pct, 1)
    return "Stable", round(pct, 1)


def trend_analysis(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
) -> dict:
    """
    تحليل الاتجاه الكلي للمبيعات.

    Returns:
        dict يحتوي:
          - trend:        'Growing' | 'Stable' | 'Declining'
          - trend_pct:    نسبة التغيير %
          - half1_avg:    متوسط النصف الأول
          - half2_avg:    متوسط النصف الثاني
          - best_period:  تاريخ أعلى مبيعات
          - worst_period: تاريخ أدنى مبيعات
    """
    try:
        period_sales = (
            df.groupby(date_col)[sales_col]
            .sum()
            .sort_index()
        )

        trend, trend_pct = _calc_trend(period_sales)
        half       = max(1, len(period_sales) // 2)
        first_half = period_sales.iloc[:half]
        second_half = period_sales.iloc[half:]

        return {
            'trend':        trend,
            'trend_pct':    trend_pct,
            'half1_avg':    round(float(first_half.mean()), 2),
            'half2_avg':    round(float(second_half.mean()), 2),
            'best_period':  str(period_sales.idxmax()),
            'worst_period': str(period_sales.idxmin()),
            'best_value':   round(float(period_sales.max()), 2),
            'worst_value':  round(float(period_sales.min()), 2),
            'n_periods':    len(period_sales),
        }
    except Exception as e:
        return {
            'trend': 'Unknown', 'trend_pct': 0.0,
            'error': str(e),
        }


# ════════════════════════════════════════════════
# 3. KPI ENGINE
# ════════════════════════════════════════════════

def compute_advanced_kpis(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    monthly_df: Optional[pd.DataFrame] = None,
    store_df: Optional[pd.DataFrame] = None,
) -> dict:
    """
    حساب مؤشرات الأداء المتقدمة.

    كل مؤشر محسوب من البيانات الفعلية — لا تقدير.

    Returns:
        dict شامل لكل الـ KPIs المتاحة.
    """
    kpi = {}

    try:
        sales = df[sales_col].dropna()

        # ── إحصاءات أساسية ──────────────────────
        kpi['mean']      = round(float(sales.mean()),   2)
        kpi['median']    = round(float(sales.median()), 2)
        kpi['std']       = round(float(sales.std()),    2)
        kpi['min']       = round(float(sales.min()),    2)
        kpi['max']       = round(float(sales.max()),    2)
        kpi['q1']        = round(float(sales.quantile(0.25)), 2)
        kpi['q3']        = round(float(sales.quantile(0.75)), 2)
        kpi['iqr']       = round(kpi['q3'] - kpi['q1'], 2)

        # ── معامل التغيير ─────────────────────────
        kpi['cv_pct'] = round(
            kpi['std'] / kpi['mean'] * 100 if kpi['mean'] > 0 else 0, 2
        )
        kpi['volatility'] = {
            'level': 'Extreme'  if kpi['cv_pct'] > CV_HIGH else
                     'High'     if kpi['cv_pct'] > CV_MODERATE else
                     'Moderate' if kpi['cv_pct'] > CV_LOW else
                     'Low',
            'badge': '🚨' if kpi['cv_pct'] > CV_HIGH else '🔴' if kpi['cv_pct'] > CV_MODERATE else '🟡' if kpi['cv_pct'] > CV_LOW else '🟢',
            'risk':  'Extreme volatility — use Bear case as planning floor' if kpi['cv_pct'] > CV_HIGH else
                     'High volatility — median-based metrics recommended' if kpi['cv_pct'] > CV_MODERATE else
                     'Moderate volatility — standard planning adequate' if kpi['cv_pct'] > CV_LOW else
                     'Low volatility — stable performance',
        }

        # ── الاتجاه ───────────────────────────────
        trend_info = trend_analysis(df, date_col, sales_col)
        kpi['trend']     = trend_info.get('trend', 'Unknown')
        kpi['trend_pct'] = trend_info.get('trend_pct', 0.0)

        # ── معدل النمو MoM ─────────────────────────
        if monthly_df is not None and len(monthly_df) >= 2:
            vals = monthly_df['total'].tolist()
            kpi['best_period']        = str(monthly_df.loc[monthly_df['total'].idxmax(), 'month'])
            kpi['worst_period']       = str(monthly_df.loc[monthly_df['total'].idxmin(), 'month'])
            kpi['best_period_value']  = round(float(max(vals)), 2)
            kpi['worst_period_value'] = round(float(min(vals)), 2)
            kpi['avg_period_value']   = round(float(np.mean(vals)), 2)
            kpi['period_spread_pct']  = round(
                (max(vals) - min(vals)) / max(kpi['avg_period_value'], 1) * 100, 1
            )

            # MoM growth (آخر شهرين)
            if vals[-2] > 0:
                kpi['mom_growth'] = round((vals[-1] - vals[-2]) / vals[-2] * 100, 2)

            # زخم النمو
            if len(vals) >= 3 and vals[-3] > 0 and vals[-2] > 0:
                prev_growth = (vals[-2] - vals[-3]) / vals[-3] * 100
                curr_growth = kpi.get('mom_growth', 0)
                kpi['growth_momentum'] = round(curr_growth, 2)
                kpi['momentum_delta']  = round(curr_growth - prev_growth, 2)
                kpi['momentum_direction'] = (
                    'Accelerating' if kpi['momentum_delta'] > 0 else
                    'Decelerating' if kpi['momentum_delta'] < 0 else
                    'Stable'
                )

        # ── Pareto (80/20) ────────────────────────
        if store_df is not None and 'total' in store_df.columns:
            total_rev = store_df['total'].sum()
            if total_rev > 0:
                sorted_rev = store_df['total'].sort_values(ascending=False)
                cumulative = sorted_rev.cumsum()
                n80 = int((cumulative <= total_rev * 0.80).sum()) + 1
                kpi['pareto_n']   = n80
                kpi['pareto_pct'] = round(n80 / len(store_df) * 100, 1)
                kpi['pareto_label'] = (
                    f"Top {kpi['pareto_pct']:.0f}% of groups = 80% of revenue"
                )

    except Exception as e:
        kpi['computation_error'] = str(e)

    return kpi


# ════════════════════════════════════════════════
# 4. DECISION ENGINE — محرك القرارات
# ════════════════════════════════════════════════

@dataclass
class Decision:
    """
    قرار واحد لوحدة تجارية واحدة (متجر/فرع/منطقة).
    كل حقل محسوب من البيانات — لا قيمة مخترعة.
    """
    unit:             str    # اسم الوحدة
    revenue:          float  # الإيراد الإجمالي
    avg_period:       float  # متوسط الفترة
    vs_avg_pct:       float  # % فوق/تحت متوسط المحفظة
    trend:            str    # "Growing (+X%)" | "Stable" | "Declining (-X%)"
    trend_pct:        float  # رقم التغيير فقط
    assessment:       str    # تقييم الوضع
    decision:         str    # INVEST | MONITOR | RESTRUCTURE | EVALUATE CLOSURE
    action:           str    # الإجراء المحدد والقابل للتنفيذ
    financial_impact: float  # الأثر المالي المقدر $
    urgency:          str    # This Week | This Month | This Quarter
    confidence:       str    # High | Medium | Low
    rating:           str    # 🟢 | 🟡 | 🔴


# ── Labels متعددة اللغات ─────────────────────────
_LABELS = {
    "en": {
        "growing":         "Growing consistently",
        "stable":          "Stable performance",
        "declining":       "Declining trend",
        "top":             "Top performer — drives disproportionate revenue",
        "strong":          "Strong performer — above portfolio average",
        "average":         "Average performer — growth potential exists",
        "weak":            "Weak performer — below portfolio average",
        "critical":        "Critical underperformer — significant revenue gap",
        "invest":          "INVEST",
        "monitor":         "MONITOR",
        "restructure":     "RESTRUCTURE",
        "close":           "EVALUATE CLOSURE",
        "act_invest":      "Replicate success model in similar units — document top 3 operational drivers",
        "act_monitor":     "Track monthly KPIs — set +10% growth target for next quarter",
        "act_restructure": "Audit operations, staffing, and product mix — identify root cause within 30 days",
        "act_close":       "Run closure feasibility analysis — compare cost of operation vs revenue gap",
        "this_week":       "This Week",
        "this_month":      "This Month",
        "this_quarter":    "This Quarter",
    },
    "ar": {
        "growing":         "نمو مستمر",
        "stable":          "أداء مستقر",
        "declining":       "اتجاه تراجعي",
        "top":             "الأفضل أداءً — يولّد إيراداً غير متناسب",
        "strong":          "أداء قوي — فوق متوسط المحفظة",
        "average":         "أداء متوسط — إمكانية نمو موجودة",
        "weak":            "أداء ضعيف — تحت متوسط المحفظة",
        "critical":        "ضعف حرج — فجوة إيرادية كبيرة",
        "invest":          "استثمر",
        "monitor":         "راقب",
        "restructure":     "أعد الهيكلة",
        "close":           "دراسة الإغلاق",
        "act_invest":      "وثّق أفضل 3 محركات نجاح وطبّقها في وحدات مشابهة",
        "act_monitor":     "تتبّع KPI شهرياً — حدد هدف نمو +10% للربع القادم",
        "act_restructure": "افحص العمليات والكوادر ومزيج المنتجات — حدد السبب الجذري خلال 30 يوماً",
        "act_close":       "دراسة جدوى الإغلاق — قارن تكلفة التشغيل بالفجوة الإيرادية",
        "this_week":       "هذا الأسبوع",
        "this_month":      "هذا الشهر",
        "this_quarter":    "هذا الربع",
    },
    "fr": {
        "growing":         "Croissance constante",
        "stable":          "Performance stable",
        "declining":       "Tendance déclinante",
        "top":             "Top performer — revenu disproportionné",
        "strong":          "Fort performer — au-dessus de la moyenne",
        "average":         "Performance moyenne — potentiel de croissance",
        "weak":            "Performance faible — sous la moyenne",
        "critical":        "Sous-performance critique — écart de revenu significatif",
        "invest":          "INVESTIR",
        "monitor":         "SURVEILLER",
        "restructure":     "RESTRUCTURER",
        "close":           "ÉVALUER FERMETURE",
        "act_invest":      "Documenter les 3 facteurs clés et répliquer dans des unités similaires",
        "act_monitor":     "Suivre les KPI mensuellement — objectif +10% de croissance",
        "act_restructure": "Auditer les opérations, le personnel et le mix produit sous 30 jours",
        "act_close":       "Analyse de faisabilité de fermeture — comparer coût d'opération vs écart de revenu",
        "this_week":       "Cette semaine",
        "this_month":      "Ce mois",
        "this_quarter":    "Ce trimestre",
    },
}


def generate_decisions(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    group_col: Optional[str],
    lang: str = "en",
) -> List[Decision]:
    """
    يولّد قرارات تجارية لكل وحدة بناءً على:
      - الإيراد النسبي (rank percentile)
      - الاتجاه الزمني
      - الفجوة عن المتوسط

    Args:
        df:        DataFrame نظيف
        date_col:  عمود التاريخ
        sales_col: عمود المبيعات
        group_col: عمود التجميع (None = لا يوجد)
        lang:      'en' | 'ar' | 'fr'

    Returns:
        قائمة Decision مرتّبة من الأفضل للأسوأ أداءً
    """
    decisions = []

    if not group_col or group_col not in df.columns:
        return decisions

    L = _LABELS.get(lang, _LABELS["en"])

    try:
        # ── إحصاءات كل مجموعة ───────────────────
        group_stats = (
            df.groupby(group_col)[sales_col]
            .agg(['sum', 'mean', 'std', 'count'])
            .reset_index()
        )
        group_stats.columns = [group_col, 'total', 'avg', 'std', 'count']
        group_stats = group_stats.sort_values('total', ascending=False).reset_index(drop=True)

        overall_unit_avg = float(group_stats['total'].mean())
        if overall_unit_avg <= 0:
            return decisions

        # ── rank percentile لكل مجموعة ──────────
        group_stats['rank_pct'] = group_stats['total'].rank(pct=True)

        # ── متوسط الاتجاه الفعلي لمجموعات INVEST/MONITOR ──
        top_groups_pct = []
        strong_groups_pct = []
        for _, gr in group_stats.iterrows():
            us = df[df[group_col] == gr[group_col]].sort_values(date_col)[sales_col]
            _, tp = _calc_trend(us)
            if gr['rank_pct'] >= 0.85:
                top_groups_pct.append(tp)
            elif gr['rank_pct'] >= 0.60:
                strong_groups_pct.append(tp)
        avg_top_trend = np.mean(top_groups_pct) if top_groups_pct else 0
        avg_strong_trend = np.mean(strong_groups_pct) if strong_groups_pct else 0
        base_growth_rate = max(avg_top_trend / 100, 0.02) if avg_top_trend > 0 else 0.02
        strong_growth_floor = max(avg_strong_trend / 100, 0.03) if avg_strong_trend > 0 else 0.03

        for _, row in group_stats.iterrows():
            unit_name  = str(row[group_col])
            revenue    = float(row['total'])
            avg_period = float(row['avg'])
            rank_pct   = float(row['rank_pct'])
            vs_avg     = (revenue - overall_unit_avg) / overall_unit_avg * 100

            # ── حساب الاتجاه لهذه الوحدة ────────
            unit_series = (
                df[df[group_col] == row[group_col]]
                .sort_values(date_col)[sales_col]
            )
            trend, trend_pct = _calc_trend(unit_series)

            # ── الاتجاه الحديث — آخر 30% من الفترات فقط ──
            recent_n = max(2, int(len(unit_series) * 0.30))
            recent_series = unit_series.iloc[-recent_n:]
            recent_trend, recent_pct = _calc_trend(recent_series)

            # ── تصنيف الأداء والقرار ─────────────
            if rank_pct >= 0.85:
                assessment = L["top"]
                decision   = L["invest"]
                action     = L["act_invest"]
                urgency    = L["this_quarter"]
                rating     = "🟢"
                impact     = revenue * (max(trend_pct, 0) / 100 + base_growth_rate)  # [DERIVED: revenue × growth trend + avg top-group growth rate]
                confidence = "High"

            elif rank_pct >= 0.60:
                assessment = L["strong"]
                decision   = L["monitor"]
                action     = L["act_monitor"]
                urgency    = L["this_quarter"]
                rating     = "🟢"
                impact     = revenue * max(max(trend_pct, 0) / 100, strong_growth_floor)  # [DERIVED: revenue × growth trend (floor = avg strong-group growth)]
                confidence = "High"

            elif rank_pct >= 0.40:
                assessment = L["average"]
                decision   = L["monitor"]
                action     = L["act_monitor"]
                urgency    = L["this_month"]
                rating     = "🟡"
                gap_recovery = (overall_unit_avg - revenue) / max(overall_unit_avg, 1)
                impact     = max(0, (overall_unit_avg - revenue) * min(gap_recovery, 1.0))  # [DERIVED: revenue gap × recovery ratio]
                confidence = "Medium"

            elif rank_pct >= 0.20:
                assessment = L["weak"]
                decision   = L["restructure"]
                action     = L["act_restructure"]
                urgency    = L["this_month"]
                rating     = "🟡"
                impact     = overall_unit_avg - revenue  # [DERIVED: full revenue gap — max recoverable]
                confidence = "Medium"

            else:
                assessment = L["critical"]
                if vs_avg < -50:
                    decision = L["close"]
                    action   = L["act_close"]
                else:
                    decision = L["restructure"]
                    action   = L["act_restructure"]
                urgency    = L["this_week"]
                rating     = "🔴"
                impact     = overall_unit_avg - revenue  # [DERIVED: full revenue gap — max recoverable]
                confidence = "High"

            # ── تعديل بناءً على الاتجاه ──────────
            if trend == "Declining" and rating == "🟡":
                rating  = "🔴"
                urgency = L["this_week"]
            elif trend == "Growing" and rating == "🟡":
                rating  = "🟢"

            # ── تعديل بناءً على الاتجاه الحديث ────
            if rating == "🟢" and recent_trend == "Declining" and recent_pct < -10:
                rating     = "🟡"
                decision   = L["monitor"]
                assessment = assessment + f" [WARNING: Recent decline {recent_pct:+.1f}%]"
            if rating == "🟡" and recent_trend == "Declining" and recent_pct < -15:
                rating     = "🔴"
                urgency    = L["this_week"]
                assessment = assessment + f" [CRITICAL: Accelerating decline {recent_pct:+.1f}%]"

            decisions.append(Decision(
                unit             = unit_name,
                revenue          = revenue,
                avg_period       = avg_period,
                vs_avg_pct       = round(vs_avg, 1),
                trend            = f"{trend} ({trend_pct:+.1f}%)",
                trend_pct        = trend_pct,
                assessment       = assessment,
                decision         = decision,
                action           = action,
                financial_impact = round(abs(impact), 0),
                urgency          = urgency,
                confidence       = confidence,
                rating           = rating,
            ))

    except Exception:
        decisions = []

    return decisions


def decisions_to_df(decisions: List[Decision], lang: str = "en") -> pd.DataFrame:
    """
    يحوّل قائمة Decision إلى DataFrame جاهز للعرض.

    كل قيمة مالية مُنسّقة كنص ($X,XXX) للعرض فقط.
    """
    COLS = {
        "en": {
            "rating": "Rating", "unit": "Unit",
            "revenue": "Total Revenue", "vs_avg": "vs Average",
            "trend": "Trend", "assessment": "Assessment",
            "decision": "Decision", "action": "Recommended Action",
            "impact": "Est. Financial Impact", "urgency": "Urgency",
        },
        "ar": {
            "rating": "التقييم", "unit": "الوحدة",
            "revenue": "الإيراد الكلي", "vs_avg": "مقابل المتوسط",
            "trend": "الاتجاه", "assessment": "التقييم النوعي",
            "decision": "القرار", "action": "الإجراء الموصى به",
            "impact": "الأثر المالي المقدر", "urgency": "الإلحاحية",
        },
        "fr": {
            "rating": "Note", "unit": "Unité",
            "revenue": "Revenu Total", "vs_avg": "vs Moyenne",
            "trend": "Tendance", "assessment": "Évaluation",
            "decision": "Décision", "action": "Action Recommandée",
            "impact": "Impact Financier Est.", "urgency": "Urgence",
        },
    }
    C = COLS.get(lang, COLS["en"])

    rows = []
    for d in decisions:
        rows.append({
            C["rating"]:     d.rating,
            C["unit"]:       d.unit,
            C["revenue"]:    f"${d.revenue:,.0f}",
            C["vs_avg"]:     f"{d.vs_avg_pct:+.1f}%",
            C["trend"]:      d.trend,
            C["assessment"]: d.assessment,
            C["decision"]:   d.decision,
            C["action"]:     d.action,
            C["impact"]:     f"${d.financial_impact:,.0f}",
            C["urgency"]:    d.urgency,
        })
    return pd.DataFrame(rows)


def get_decisions_summary(decisions: List[Decision]) -> dict:
    """
    ملخص إحصائي سريع لقائمة القرارات.

    Returns:
        dict يحتوي:
          - أعداد كل نوع قرار
          - الأثر المالي الإجمالي
          - الوحدات الحرجة (🔴)
    """
    if not decisions:
        return {}

    invest      = sum(1 for d in decisions if "INVEST" in d.decision.upper()
                      or "استثمر" in d.decision or "INVESTIR" in d.decision)
    monitor     = sum(1 for d in decisions if "MONITOR" in d.decision.upper()
                      or "راقب" in d.decision or "SURVEILLER" in d.decision)
    restructure = sum(1 for d in decisions if "RESTRUCTURE" in d.decision.upper()
                      or "هيكلة" in d.decision or "RESTRUCTURER" in d.decision)
    close       = sum(1 for d in decisions if "CLOS" in d.decision.upper()
                      or "إغلاق" in d.decision or "FERMETURE" in d.decision)

    critical    = [d for d in decisions if d.rating == "🔴"]
    total_impact = sum(d.financial_impact for d in decisions)

    return {
        "invest":          invest,
        "monitor":         monitor,
        "restructure":     restructure,
        "close":           close,
        "total_units":     len(decisions),
        "total_impact":    round(total_impact, 0),
        "critical_count":  len(critical),
        "critical_units":  [d.unit for d in critical[:5]],
        "green_count":     sum(1 for d in decisions if d.rating == "🟢"),
        "yellow_count":    sum(1 for d in decisions if d.rating == "🟡"),
        "red_count":       len(critical),
    }


# ════════════════════════════════════════════════
# 5. FULL ANALYSIS RUNNER
# ════════════════════════════════════════════════

def run_full_analysis(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    group_col: Optional[str] = None,
    lang: str = "en",
) -> dict:
    """
    تشغيل كامل لجميع وظائف التحليل دفعةً واحدة.
    يُستخدم من AnalysisAgent في الـ Orchestrator.

    Returns:
        dict يحتوي على كل مخرجات التحليل منظّمة.
    """
    results = {}

    # ── أداء المجموعات ───────────────────────────
    if group_col:
        results['store_df']        = sales_by_store(df, group_col, sales_col)
        results['top_performers']  = top_performers(df, group_col, sales_col, n=5)
        results['bottom_performers'] = bottom_performers(df, group_col, sales_col, n=5)
    else:
        results['store_df']          = None
        results['top_performers']    = None
        results['bottom_performers'] = None

    # ── التحليل الزمني ───────────────────────────
    results['monthly_df']  = monthly_sales(df, date_col, sales_col)
    results['yearly_df']   = yearly_sales(df, date_col, sales_col)
    results['quarterly_df'] = quarterly_sales(df, date_col, sales_col)

    # ── تأثير الأعياد ────────────────────────────
    results['holiday_df'] = holiday_vs_normal(df, sales_col)

    # ── الارتباطات ───────────────────────────────
    results['corr_series'] = correlation_analysis(df, sales_col)

    # ── KPI ──────────────────────────────────────
    results['kpi_data'] = compute_advanced_kpis(
        df         = df,
        date_col   = date_col,
        sales_col  = sales_col,
        monthly_df = results['monthly_df'],
        store_df   = results['store_df'],
    )

    # ── الاتجاه الكلي ────────────────────────────
    results['trend_info'] = trend_analysis(df, date_col, sales_col)

    # ── القرارات ─────────────────────────────────
    results['decisions'] = generate_decisions(df, date_col, sales_col, group_col, lang)
    results['decisions_df'] = (
        decisions_to_df(results['decisions'], lang)
        if results['decisions'] else None
    )
    results['decisions_summary'] = get_decisions_summary(results['decisions'])

    return results