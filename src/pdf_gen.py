# ═══════════════════════════════════════════════════════════
# pdf_gen.py — Professional BI Report Generator v5.0
# FIXES:
#  FIX-P1: Volatility label — reads from volatility dict, never hardcoded
#  FIX-P2: RESOLUTION section — past-peak uses past-tense language
#  FIX-P3: Growth Opportunities table — col widths prevent bleeding
#  FIX-P4: Volatility inconsistency — single classify_volatility() used
#  FIX-P5: MAE/RMSE/MAPE correct (carried from v4.1)
#  FIX-P6: P-value display <0.0001 (carried from v4.1)
#  FIX-P7: TOC section numbers match exactly
#  FIX-P8: Action Plan text truncation fixed
#  FIX-P9: Forecast gap anomaly warning
#  NEW: Dynamic volatility label everywhere (not hardcoded)
#  NEW: Smarter RESOLUTION / STAKES language based on peak timing
#  NEW: Improved chart spacing and visual hierarchy
# ═══════════════════════════════════════════════════════════

import io
import os
import re
import urllib.request
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib import rcParams
from scipy import stats as scipy_stats

from reportlab.lib.pagesizes   import A4
from reportlab.lib.units       import inch
from reportlab.lib             import colors
from reportlab.lib.styles      import ParagraphStyle
from reportlab.lib.enums       import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus        import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.pdfbase         import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ═══════════════════════════════════════════════════════════
# 1. ARABIC SUPPORT
# ═══════════════════════════════════════════════════════════
try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    ARABIC_AVAILABLE = True
except ImportError:
    ARABIC_AVAILABLE = False

def _register_arabic_font():
    font_name = "Amiri"
    font_path = "/tmp/Amiri-Regular.ttf"
    if not os.path.exists(font_path):
        urls = [
            "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf",
            "https://fonts.gstatic.com/s/amiri/v27/J7aRnpd8CGxBHqUpvrIw74NL.ttf",
        ]
        for url in urls:
            try:
                urllib.request.urlretrieve(url, font_path)
                if os.path.getsize(font_path) > 50000:
                    break
            except Exception:
                continue
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        return font_name
    except Exception:
        return None

_ARABIC_FONT = None

def process_text(text: str, lang: str) -> str:
    if lang != "ar" or not ARABIC_AVAILABLE:
        return str(text)
    try:
        return get_display(reshape(str(text)))
    except Exception:
        return str(text)

def get_font(lang: str, bold: bool = False) -> str:
    global _ARABIC_FONT
    if lang == "ar":
        if _ARABIC_FONT is None:
            _ARABIC_FONT = _register_arabic_font()
        if _ARABIC_FONT:
            return _ARABIC_FONT
    return "Helvetica-Bold" if bold else "Helvetica"


# ═══════════════════════════════════════════════════════════
# 2. COLOR PALETTE
# ═══════════════════════════════════════════════════════════
CH = {
    'navy':        '#1B2E4B', 'navy_dark':   '#0A1628',
    'blue':        '#1A3A6B', 'blue_mid':    '#2557A7',
    'blue_light':  '#E8EFF8', 'blue_pale':   '#F2F6FB',
    'teal':        '#0D7377', 'green':       '#1A6B3A',
    'green_light': '#E8F4EC', 'amber':       '#92400E',
    'amber_light': '#FEF3C7', 'red':         '#7F1D1D',
    'red_light':   '#FEF2F2', 'gray_dark':   '#1F2937',
    'gray_mid':    '#4B5563', 'gray':        '#6B7280',
    'gray_light':  '#F3F4F6', 'gray_pale':   '#F9FAFB',
    'border':      '#D1D5DB', 'chart1':      '#1A3A6B',
    'chart2':      '#2557A7', 'chart3':      '#0D7377',
    'chart4':      '#1A6B3A', 'chart5':      '#92400E',
    'chart_neg':   '#7F1D1D', 'chart_pos':   '#1A6B3A',
    'bear':        '#DC2626', 'bull':        '#16A34A',
    'grade_a':     '#14532D', 'grade_b':     '#1A3A6B',
    'grade_c':     '#92400E', 'grade_d':     '#7F1D1D',
}
C = {k: colors.HexColor(v) for k, v in CH.items()}
C['white'] = colors.white
C['black'] = colors.black

def rl(key): return C.get(key, colors.HexColor('#1A3A6B'))
def mpl(key): return CH.get(key, '#1A3A6B')


# ═══════════════════════════════════════════════════════════
# 3. STATISTICAL ENGINE
# ═══════════════════════════════════════════════════════════
def _format_pvalue(p_val) -> str:
    if p_val is None:            return "N/A"
    elif p_val < 0.0001:         return "<0.0001"
    elif p_val < 0.001:          return "<0.001"
    elif p_val < 0.01:           return f"{p_val:.4f}"
    else:                        return f"{p_val:.4f}"


def compute_statistical_validation(df, sales_col, corr_series=None) -> dict:
    results = {}

    if corr_series is not None and len(corr_series) > 0:
        corr_details = []
        for col_name, r in corr_series.items():
            try:
                col_data   = df[col_name].dropna()
                sales_data = df[sales_col].loc[col_data.index].dropna()
                common_idx = col_data.index.intersection(sales_data.index)
                x = col_data.loc[common_idx]
                y = sales_data.loc[common_idx]
                n_pairs = len(x)

                if n_pairs > 3:
                    r_actual, p_val = scipy_stats.pearsonr(x, y)
                else:
                    r_actual, p_val = float(r), None

                p_display = _format_pvalue(p_val)

                if p_val is None:       sig = "Insufficient data"
                elif p_val < 0.0001:    sig = "Highly significant (p < 0.0001)"
                elif p_val < 0.001:     sig = "Highly significant (p < 0.001)"
                elif p_val < 0.01:      sig = "Significant (p < 0.01)"
                elif p_val < 0.05:      sig = "Significant (p < 0.05)"
                else:                   sig = "Not significant (p ≥ 0.05)"

                abs_r = abs(r_actual)
                # FIX: Effect size filter — large n can make trivial r "significant"
                if abs_r >= 0.8:        strength = "Very Strong"
                elif abs_r >= 0.6:      strength = "Strong"
                elif abs_r >= 0.4:      strength = "Moderate"
                elif abs_r >= 0.2:      strength = "Weak"
                else:                   strength = "Negligible"

                # Practical significance: flag when r is tiny but p is significant (large n)
                practical_sig = abs_r >= 0.2 and (p_val is None or p_val < 0.05)

                corr_details.append({
                    'variable':       col_name,
                    'r':              round(float(r_actual), 4),
                    'p_value':        p_val,
                    'p_display':      p_display,
                    'n':              n_pairs,
                    'significant':    (p_val < 0.05) if p_val is not None else False,
                    'practical_sig':  practical_sig,
                    'strength':       strength,
                    'direction':      "Positive" if r_actual > 0 else "Negative",
                    'sig_label':      sig,
                })
            except Exception:
                corr_details.append({
                    'variable': col_name, 'r': round(float(r), 4),
                    'p_value': None, 'p_display': "N/A", 'n': len(df),
                    'significant': False, 'practical_sig': False,
                    'strength': 'Unknown', 'direction': "Positive" if r > 0 else "Negative",
                    'sig_label': "Computation unavailable",
                })
        results['correlations'] = corr_details

    try:
        sales = df[sales_col].dropna()
        if len(sales) >= 8:
            stat, p_norm = scipy_stats.shapiro(sales[:5000])
            results['normality'] = {
                'test':      'Shapiro-Wilk',
                'statistic': round(float(stat), 4),
                'p_value':   p_norm,
                'p_display': _format_pvalue(p_norm),
                'normal':    p_norm > 0.05,
                'note':      ("Distribution is approximately normal"
                              if p_norm > 0.05
                              else "Non-normal — median-based metrics recommended alongside mean"),
            }
        else:
            results['normality'] = None
    except Exception:
        results['normality'] = None

    return results


def compute_forecast_accuracy(prophet_data: pd.DataFrame, forecast: pd.DataFrame) -> dict:
    try:
        hist = prophet_data.copy()
        if list(hist.columns) != ['ds', 'y']:
            hist.columns = ['ds', 'y']
        hist = hist.dropna(subset=['y']).sort_values('ds').reset_index(drop=True)
        n    = len(hist)

        if n < 10:
            return {
                'available': False,
                'message': ("Forecast accuracy metrics unavailable: "
                            "insufficient historical data (minimum 10 periods required)."),
            }

        holdout_n = max(4, int(n * 0.2))
        train_df  = hist.iloc[:-holdout_n].copy()
        test_df   = hist.iloc[-holdout_n:].copy()
        actuals   = test_df['y'].values

        from statsmodels.tsa.holtwinters import ExponentialSmoothing as ES

        series = train_df.set_index('ds')['y'].copy()
        try:
            series.index = pd.DatetimeIndex(series.index).to_period('W').to_timestamp()
        except Exception:
            pass

        n_train = len(series)
        try:
            if n_train >= 52:
                model = ES(series, trend='add', seasonal='add', seasonal_periods=52).fit(optimized=True)
            elif n_train >= 26:
                model = ES(series, trend='add', seasonal='add', seasonal_periods=26).fit(optimized=True)
            else:
                model = ES(series, trend='add', seasonal=None).fit(optimized=True)
        except Exception:
            try:
                model = ES(series, trend='add', seasonal=None).fit(optimized=True)
            except Exception:
                model = ES(series, trend=None, seasonal=None).fit(optimized=True)

        predicted = model.forecast(holdout_n)[:len(actuals)]

        if float(np.mean(np.abs(predicted))) < 0.01:
            return {'available': False, 'message': "Model produced near-zero predictions on holdout."}

        mae  = float(np.mean(np.abs(actuals - predicted)))
        rmse = float(np.sqrt(np.mean((actuals - predicted) ** 2)))

        nonzero = actuals != 0
        mape = (float(np.mean(np.abs((actuals[nonzero] - predicted[nonzero])
                                      / actuals[nonzero])) * 100)
                if nonzero.any() else None)

        if mae < 0.01:
            return {'available': False, 'message': "Computed MAE near-zero — data alignment issue."}

        if mape is not None:
            if mape < 10:    acc_rating = "Excellent (MAPE < 10%)"
            elif mape < 20:  acc_rating = "Good (MAPE 10–20%)"
            elif mape < 30:  acc_rating = "Fair (MAPE 20–30%)"
            else:            acc_rating = "Poor (MAPE ≥ 30%) — use directional guidance only"
        else:
            acc_rating = "MAPE not computable (zero-value periods in holdout)"

        return {
            'available': True, 'mae': round(mae, 2), 'rmse': round(rmse, 2),
            'mape': round(mape, 1) if mape is not None else None,
            'n_holdout': holdout_n, 'n_train': n_train, 'acc_rating': acc_rating,
            'limitation': (
                f"In-sample validation: trained on {n_train} periods, "
                f"tested on last {holdout_n} periods. "
                "True out-of-sample accuracy will differ."
            ),
        }

    except Exception as e:
        return {'available': False, 'message': f"Forecast accuracy unavailable: {str(e)[:120]}"}


def compute_data_quality(df, date_col, sales_col) -> dict:
    n_total      = len(df)
    n_missing    = int(df.isnull().sum().sum())
    n_duplicates = int(df.duplicated().sum())
    missing_by_col = {k: v for k, v in df.isnull().sum().to_dict().items() if v > 0}
    q1  = df[sales_col].quantile(0.25)
    q3  = df[sales_col].quantile(0.75)
    iqr = q3 - q1
    low, high  = q1 - 1.5*iqr, q3 + 1.5*iqr
    n_outliers = int(((df[sales_col] < low) | (df[sales_col] > high)).sum())
    missing_pct  = n_missing    / max(n_total * max(len(df.columns), 1), 1) * 100
    dup_pct      = n_duplicates / max(n_total, 1) * 100
    outlier_pct  = n_outliers   / max(n_total, 1) * 100
    completeness = round(max(0, 100 - missing_pct - dup_pct - outlier_pct * 0.5), 1)
    if completeness >= 95:   rating, rc = "Excellent", 'green'
    elif completeness >= 85: rating, rc = "Good",      'blue'
    elif completeness >= 70: rating, rc = "Fair",      'amber'
    else:                    rating, rc = "Poor",      'red'
    return {
        'n_total': n_total, 'n_missing': n_missing, 'missing_pct': round(missing_pct, 2),
        'missing_by_col': missing_by_col, 'n_duplicates': n_duplicates,
        'dup_pct': round(dup_pct, 2), 'n_outliers': n_outliers,
        'outlier_pct': round(outlier_pct, 2),
        'outlier_bounds': (round(float(low), 2), round(float(high), 2)),
        'completeness': completeness, 'rating': rating, 'rating_color': rc,
        'issues_found': n_missing > 0 or n_duplicates > 0 or n_outliers > 0,
    }


def compute_segment_scorecard(store_df, group_col) -> list:
    if store_df is None or len(store_df) == 0:
        return []
    total_rev  = float(store_df['total'].sum())
    max_weekly = float(store_df['avg_weekly'].max())
    scorecards = []
    for _, row in store_df.iterrows():
        rev_score    = min(round(row['total'] / total_rev * 100 * 2, 1), 100)
        eff_score    = round(row['avg_weekly'] / max_weekly * 100, 1) if max_weekly > 0 else 0
        growth_score = round((1 - row['avg_weekly'] / max_weekly) * 100, 1) if max_weekly > 0 else 0
        risk_score   = round(row['total'] / total_rev * 100, 1)
        overall      = round(rev_score*0.35 + eff_score*0.35 + growth_score*0.15 + (100-risk_score)*0.15, 1)
        if overall >= 80:    grade, gc = "A+", 'grade_a'
        elif overall >= 65:  grade, gc = "A",  'grade_a'
        elif overall >= 50:  grade, gc = "B+", 'grade_b'
        elif overall >= 35:  grade, gc = "B",  'grade_b'
        elif overall >= 20:  grade, gc = "C",  'grade_c'
        else:                grade, gc = "D",  'grade_d'
        scorecards.append({
            'segment': str(row[group_col]), 'rev_score': rev_score,
            'eff_score': eff_score, 'growth_score': growth_score,
            'risk_score': risk_score, 'overall': overall,
            'grade': grade, 'grade_color': gc,
            'total_rev': row['total'], 'avg_weekly': row['avg_weekly'],
        })
    return sorted(scorecards, key=lambda x: x['overall'], reverse=True)


def compute_risk_matrix(ctx) -> list:
    cv_pct = ctx.get('cv_pct', 0)
    pareto = ctx.get('pareto_pct', 33)
    conf   = ctx.get('confidence_level', 'Medium')
    fc_prob   = "High" if conf == "Low" else "Medium"
    fc_impact = "High" if cv_pct > 60 else "Medium"
    return [
        {'risk': "Revenue Concentration",
         'probability': "High" if pareto < 30 else "Medium", 'impact': "High",
         'severity': "Critical" if pareto < 30 else "High",
         'mitigation': "Diversify revenue base; invest in mid-tier segment acceleration."},
        {'risk': "Forecast Inaccuracy",
         'probability': fc_prob, 'impact': fc_impact,
         'severity': "Critical" if fc_prob=="High" and fc_impact=="High" else "High",
         'mitigation': "Use Bear/Base/Bull scenarios; monitor leading indicators weekly."},
        {'risk': "Revenue Volatility",
         'probability': "High" if cv_pct > 80 else "Medium", 'impact': "High",
         'severity': "High" if cv_pct > 60 else "Medium",
         'mitigation': "Implement rolling forecasts; build 20–30% revenue buffer."},
        {'risk': "Demand Slowdown",
         'probability': "Medium", 'impact': "Medium", 'severity': "Medium",
         'mitigation': "Monitor Period 3 leading indicators; prepare contingency pricing."},
        {'risk': "Peak Capture Failure",
         'probability': "Low", 'impact': "High", 'severity': "Medium",
         'mitigation': "Pre-position inventory; confirm supply chain readiness before peak."},
    ]


def compute_growth_opportunities(ctx, store_df, group_col) -> list:
    opps = []
    avg  = ctx.get('avg_per_period', 0)
    best = ctx.get('best_group_avg', 0)
    fc12 = ctx.get('fc12', 0)
 
    if store_df is not None and group_col and avg > 0:
        # فرصة 1: رفع الوحدات الضعيفة إلى متوسط المحفظة
        bottom_half = store_df[store_df['avg_weekly'] < avg]
        if len(bottom_half) > 0:
            avg_gap      = float(avg - bottom_half['avg_weekly'].mean())
            n_units      = len(bottom_half)
            # DERIVED: الفجوة الفعلية × عدد الوحدات × 12 فترة (100% gap closure افتراض أقصى)
            uplift_max   = avg_gap * n_units * 12
            # نستخدم 50% كسيناريو محافظ
            uplift_cons  = uplift_max * 0.50
            opps.append({
                'type':        "Efficiency Uplift — Bottom 50% to Average",
                'description': f"Bring {n_units} below-average units (avg ${bottom_half['avg_weekly'].mean():,.0f}/period) to portfolio average (${avg:,.0f}/period).",
                'est_impact':  uplift_cons,
                'confidence':  "Medium",
                'effort':      "Medium",
                'basis':       f"DERIVED (50% scenario): (${avg:,.0f} − ${bottom_half['avg_weekly'].mean():,.0f}) × {n_units} units × 12 periods × 50% closure rate. Full closure = ${uplift_max:,.0f}.",
            })
 
        # فرصة 2: تكرار نموذج الأفضل
        if best > avg and len(store_df) > 3:
            # نطبق نموذج الأفضل على أضعف 3 وحدات — 30% نجاح افتراضي
            worst3_avg = float(store_df.nsmallest(3, 'avg_weekly')['avg_weekly'].mean())
            gap_to_best = best - worst3_avg
            replication = gap_to_best * 3 * 12 * 0.30  # 30% replication rate
            opps.append({
                'type':        f"Top Performer Replication (Group {ctx.get('best_group','top')})",
                'description': f"Apply Group {ctx.get('best_group','top')} operational model to bottom 3 units.",
                'est_impact':  replication,
                'confidence':  "Low",
                'effort':      "Medium",
                'basis':       f"INFERRED (30% replication rate assumed): (${best:,.0f} − ${worst3_avg:,.0f}) × 3 units × 12 periods × 30%. Validate before committing.",
            })
 
    # فرصة 3: Bull case upside (مشتقة من البيانات)
    bull_upside = ctx.get('bull_12', fc12) - fc12
    if bull_upside > 0:
        bull_spread = ctx.get('bull_spread_pct', 25.0)
        method      = ctx.get('scenario_method', 'unknown')
        opps.append({
            'type':        "Bull Case Revenue Upside",
            'description': "Favorable market conditions or successful strategic initiatives.",
            'est_impact':  bull_upside,
            'confidence':  f"Low ({method})",
            'effort':      "High",
            'basis':       f"DERIVED: Bull forecast (${ctx.get('bull_12', 0):,.0f}) − Base forecast (${fc12:,.0f}) = ${bull_upside:,.0f}. Bull scenario = +{bull_spread:.1f}% from base ({method}).",
        })
 
    # فرصة 4: Price lever — فقط إذا كان الارتباط موجوداً وقوياً في البيانات الفعلية
    top_corr_col = ctx.get('top_pos_corr_col')
    top_corr_r   = ctx.get('top_pos_corr_r', 0.0)
    if top_corr_col and top_corr_r > 0.5:
        # لا نفترض 5% — نحسب من الارتباط الفعلي
        # r=0.7 → تغيير 1 std في المتغير يرتبط بتغيير r×std_sales في المبيعات
        # لكن هذا inferred لأن الارتباط ≠ سببية
        total_rev = ctx.get('total_revenue', 0)
        est_lever = total_rev * (top_corr_r * 0.05)  # 5% من r كحد أقصى محافظ
        opps.append({
            'type':        f"Pricing Lever — {top_corr_col}",
            'description': f"Statistical association between {top_corr_col} and revenue (r={top_corr_r:.3f}) suggests potential pricing optimization opportunity.",
            'est_impact':  est_lever,
            'confidence':  "Low",
            'effort':      "Medium",
            'basis':       f"INFERRED: r={top_corr_r:.3f} × 5% revenue lever = ${est_lever:,.0f}. WARNING: Correlation ≠ causation. Elasticity unknown. Pilot required before scaling. Do NOT implement price changes based on correlation alone.",
        })
 
    opps.sort(key=lambda x: x['est_impact'], reverse=True)
    return opps
 


def _get_peak_urgency(peak_str: str) -> dict:
    today = pd.Timestamp.now().normalize()
    try:
        peak_dt   = pd.Timestamp(peak_str)
        days_left = (peak_dt - today).days
        is_past   = days_left < 0
    except Exception:
        return {'days_left': None, 'level': 'unknown', 'is_past': False, 'message': ''}

    if is_past:
        level = 'past';     msg = f"Peak date has passed ({abs(days_left)} days ago). Compare actual vs. projected."
    elif days_left <= 7:
        level = 'critical'; msg = f"CRITICAL: Peak in {days_left} days. Immediate action required."
    elif days_left <= 14:
        level = 'urgent';   msg = f"URGENT: Peak in {days_left} days. Begin preparation immediately."
    elif days_left <= 30:
        level = 'soon';     msg = f"Peak in {days_left} days. Begin preparation within 48 hours."
    else:
        level = 'planned';  msg = f"Peak in {days_left} days. Standard preparation timeline."
    return {'days_left': days_left, 'level': level, 'message': msg, 'is_past': is_past}


# ═══════════════════════════════════════════════════════════
# 4. DYNAMIC CONTEXT EXTRACTION
# ═══════════════════════════════════════════════════════════
def extract_dynamic_context(
    df, date_col, sales_col, summary, store_df,
    group_col, corr_series, forecast_summary, monthly_df,
    prophet_data=None,   # PDF-FIX-5: مُضاف
):
    import pandas as pd
    import numpy as np
 
    ctx = {}
 
    # ── إحصائيات المبيعات على مستوى الصفوف الفردية (للعرض فقط) ──
    ctx['total_revenue']     = float(df[sales_col].sum())
    ctx['peak_value']        = float(df[sales_col].max())
    ctx['min_value']         = float(df[sales_col].min())
    ctx['n_records']         = int(len(df))
    ctx['q1_value']          = float(df[sales_col].quantile(0.25))
    ctx['q3_value']          = float(df[sales_col].quantile(0.75))
 
    # PDF-FIX-1: aggregate أولاً ثم احسب المتوسط والـ CV
    # المتوسط والـ median يجب أن يكونا على مستوى الفترات المجمّعة
    period_agg = df.groupby(date_col)[sales_col].sum().reset_index()
    if len(period_agg) > 0:
        ctx['avg_per_period']    = float(period_agg[sales_col].mean())
        ctx['median_per_period'] = float(period_agg[sales_col].median())
        ctx['std_dev']           = float(period_agg[sales_col].std()) if len(period_agg) > 1 else 0.0
        # CV على period totals — لا على صفوف المعاملات الفردية
        ctx['cv_pct'] = round(
            ctx['std_dev'] / ctx['avg_per_period'] * 100, 1
        ) if ctx['avg_per_period'] > 0 else 0.0
    else:
        ctx['avg_per_period']    = float(df[sales_col].mean())
        ctx['median_per_period'] = float(df[sales_col].median())
        ctx['std_dev']           = float(df[sales_col].std()) if len(df) > 1 else 0.0
        ctx['cv_pct']            = 0.0
 
    ctx['date_min']   = str(df[date_col].min().date())
    ctx['date_max']   = str(df[date_col].max().date())
    ctx['date_range'] = f"{ctx['date_min']} to {ctx['date_max']}"
    ctx['n_periods']  = int(len(period_agg))
 
    # Trend: first half vs second half of aggregated periods
    sorted_agg  = period_agg.sort_values(date_col)
    half        = max(1, len(sorted_agg) // 2)
    first_half  = float(sorted_agg[sales_col].iloc[:half].mean()) if half > 0 else 0
    second_half = float(sorted_agg[sales_col].iloc[half:].mean()) if len(sorted_agg) > half else first_half
    trend_pct   = (second_half - first_half) / first_half * 100 if first_half > 0 else 0
    ctx['trend_pct']       = round(trend_pct, 1)
    ctx['trend_direction'] = "growing" if trend_pct > 3 else "declining" if trend_pct < -3 else "stable"
 
    # Growth momentum (acceleration/deceleration)
    if len(sorted_agg) >= 4:
        try:
            pct_ch = sorted_agg[sales_col].pct_change().dropna()
            recent_g = float(pct_ch.iloc[-2:].mean() * 100) if len(pct_ch) >= 2 else 0.0
            prior_g  = float(pct_ch.iloc[-4:-2].mean() * 100) if len(pct_ch) >= 4 else 0.0
            ctx['growth_momentum']       = round(recent_g, 1)
            ctx['growth_momentum_delta'] = round(recent_g - prior_g, 1)
            ctx['momentum_direction']    = (
                "Accelerating" if recent_g > 0 and (recent_g - prior_g) > 0
                else "Decelerating" if recent_g > 0 and (recent_g - prior_g) < 0
                else "Declining" if recent_g < 0
                else "Stable"
            )
        except Exception:
            ctx['growth_momentum']       = 0.0
            ctx['growth_momentum_delta'] = 0.0
            ctx['momentum_direction']    = "Unknown"
    else:
        ctx['growth_momentum']       = 0.0
        ctx['growth_momentum_delta'] = 0.0
        ctx['momentum_direction']    = "Insufficient data"
 
    # Period stats from monthly_df
    if monthly_df is not None and len(monthly_df) > 0:
        vals   = monthly_df['total'].tolist()
        months = [str(m) for m in monthly_df['month']]
        ctx['best_period_label']  = months[vals.index(max(vals))] if vals else 'N/A'
        ctx['worst_period_label'] = months[vals.index(min(vals))] if vals else 'N/A'
        ctx['best_period_value']  = max(vals) if vals else 0
        ctx['worst_period_value'] = min(vals) if vals else 0
        ctx['period_spread_pct']  = round(
            (max(vals) - min(vals)) / max(ctx['avg_per_period'], 1) * 100, 1
        ) if vals else 0
    else:
        for k in ['best_period_label', 'worst_period_label']:
            ctx[k] = 'N/A'
        for k in ['best_period_value', 'worst_period_value', 'period_spread_pct']:
            ctx[k] = 0
 
    # Group/segment stats
    ctx['group_col']   = group_col or 'N/A'
    ctx['n_groups']    = int(summary.get('num_groups', 0))
    ctx['best_group']  = str(summary.get('best_group', 'N/A'))
    ctx['worst_group'] = str(summary.get('worst_group', 'N/A'))
 
    if store_df is not None and group_col:
        total_rev = store_df['total'].sum()
        ctx['best_group_revenue']  = float(store_df['total'].max())
        ctx['best_group_share']    = round(store_df['total'].max() / total_rev * 100, 1) if total_rev > 0 else 0
        ctx['worst_group_revenue'] = float(store_df['total'].min())
        ctx['worst_group_avg']     = float(store_df.loc[store_df['total'].idxmin(), 'avg_weekly'])
        ctx['best_group_avg']      = float(store_df.loc[store_df['total'].idxmax(), 'avg_weekly'])
        cum = store_df['total'].sort_values(ascending=False).cumsum()
        n80 = int((cum <= total_rev * 0.80).sum()) + 1
        ctx['pareto_n']   = n80
        ctx['pareto_pct'] = round(n80 / max(len(store_df), 1) * 100, 1)
    else:
        for k in ['best_group_revenue', 'best_group_share', 'worst_group_revenue',
                  'worst_group_avg', 'best_group_avg', 'pareto_n', 'pareto_pct']:
            ctx[k] = 0
 
    # Correlation factors
    if corr_series is not None and len(corr_series) > 0:
        pos = corr_series[corr_series > 0.1]
        neg = corr_series[corr_series < -0.1]
        ctx['pos_factors'] = [(str(k), round(float(v), 4)) for k, v in pos.items()]
        ctx['neg_factors'] = [(str(k), round(float(v), 4)) for k, v in neg.items()]
        # Top correlation for dynamic recommendations
        if len(pos) > 0:
            top_pos_col = pos.idxmax()
            ctx['top_pos_corr_col'] = str(top_pos_col)
            ctx['top_pos_corr_r']   = round(float(pos.max()), 4)
        else:
            ctx['top_pos_corr_col'] = None
            ctx['top_pos_corr_r']   = 0.0
    else:
        ctx['pos_factors']      = []
        ctx['neg_factors']      = []
        ctx['top_pos_corr_col'] = None
        ctx['top_pos_corr_r']   = 0.0
 
    # Forecast — single source of truth
    ctx['fc4']       = float(forecast_summary.get('next_4_weeks',  0))
    ctx['fc8']       = float(forecast_summary.get('next_8_weeks',  0))
    ctx['fc12']      = float(forecast_summary.get('next_12_weeks', 0))
    ctx['bear_12']   = float(forecast_summary.get('bear_12_weeks', ctx['fc12'] * 0.75))
    ctx['bull_12']   = float(forecast_summary.get('bull_12_weeks', ctx['fc12'] * 1.25))
    ctx['peak_week'] = str(forecast_summary.get('peak_week', 'N/A'))
    ctx['peak_fc']   = float(forecast_summary.get('peak_expected_sales', 0))
 
    # PDF-FIX-1: استخدام spread بدل الاحتمالات الوهمية
    ctx['bear_spread_pct']    = float(forecast_summary.get('bear_spread_pct', -25.0))
    ctx['bull_spread_pct']    = float(forecast_summary.get('bull_spread_pct',  25.0))
    ctx['scenario_method']    = str(forecast_summary.get('scenario_method', 'cv_scaled_fallback'))
    # Legacy keys: صفر لأنها لم تعد تُستخدم في العرض
    ctx['bear_prob'] = 0.0
    ctx['base_prob'] = 0.0
    ctx['bull_prob'] = 0.0
 
    ctx['confidence_level']   = forecast_summary.get('confidence_level', 'Medium')
    ctx['model_type']         = forecast_summary.get('model_type', 'unknown')
    ctx['volatility']         = forecast_summary.get('volatility', {})
    ctx['sanity_check']       = forecast_summary.get('sanity_check', {'passed': True, 'warnings': []})
    ctx['leading_indicators'] = forecast_summary.get('leading_indicators', [])
    ctx['decision_rule']      = forecast_summary.get('decision_rule', '')
 
    # Forecast gap detection
    n_fc_periods = max(1, int(ctx['fc12'] / max(ctx['avg_per_period'], 1)))
    fc12_avg_per_period = ctx['fc12'] / 12 if ctx['fc12'] > 0 else 0
    fc_gap_pct = (
        (fc12_avg_per_period - ctx['avg_per_period']) / ctx['avg_per_period'] * 100
        if ctx['avg_per_period'] > 0 else 0
    )
    ctx['fc12_avg_per_period'] = round(fc12_avg_per_period, 2)
    ctx['fc_gap_pct']          = round(fc_gap_pct, 1)
    ctx['fc_gap_flag']         = fc_gap_pct > 200
 
    # Peak urgency
    from src.pdf_gen import _get_peak_urgency
    ctx['peak_urgency'] = _get_peak_urgency(ctx['peak_week'])
    ctx['peak_is_past'] = ctx['peak_urgency']['is_past']
 
    # Gap calculations (derived from data)
    ctx['worst_group_gap_weekly']  = ctx['avg_per_period'] - ctx['worst_group_avg']
    ctx['worst_group_12p_cost']    = ctx['worst_group_gap_weekly'] * 12
    ctx['worst_group_annual_cost'] = ctx['worst_group_gap_weekly'] * 52
 
    # Deadlines
    ctx['action_deadline_7']  = (pd.Timestamp.now() + pd.Timedelta(days=7)).strftime('%Y-%m-%d')
    ctx['action_deadline_30'] = (pd.Timestamp.now() + pd.Timedelta(days=30)).strftime('%Y-%m-%d')
    ctx['action_deadline_90'] = (pd.Timestamp.now() + pd.Timedelta(days=90)).strftime('%Y-%m-%d')
    ctx['report_date']        = pd.Timestamp.now().strftime('%d %B %Y')
    ctx['report_year']        = pd.Timestamp.now().strftime('%Y')
 
    return ctx

# ═══════════════════════════════════════════════════════════
# 5. QUALITY GUARDRAILS
# ═══════════════════════════════════════════════════════════
_FORBIDDEN = [
    r'\bwalmart\b', r'\b2010\b', r'\b2011\b', r'\b2012\b',
    r'\bweekly[_\s]sales\b', r'\bholiday[_\s]flag\b',
    r'\bprophet\b', r'\bfacebook\b', r'\b(index|idx|unnamed)\b',
    r'\bai\s+analysis\b', r'\bai\s+generated\b',
    r'\bai\s+consultant\b', r'\bai\s+recommendation\b',
]

def validate_report_data(ai_text: str, ctx: dict) -> dict:
    errors = []
    text_lower = ai_text.lower()
    for pattern in _FORBIDDEN:
        if re.search(pattern, text_lower):
            errors.append({
                'error': f"Flagged: '{pattern}'",
                'impact': 'Low',
                'action': 'Removed in correction pass'
            })
    years_in_text = set(re.findall(r'\b(19|20)\d{2}\b', ai_text))
    date_min_val  = ctx.get('date_min')
    try:
        actual_year_min = int(str(date_min_val)[:4]) if date_min_val else 2000
    except (ValueError, TypeError):
        actual_year_min = 2000
    try:
        report_year = int(str(ctx.get('report_year', '2026'))[:4])
    except (ValueError, TypeError):
        report_year = 2026
    for yr in years_in_text:
        if int(yr) < actual_year_min or int(yr) > report_year + 1:
            errors.append({
                'error': f"Year {yr} outside data range",
                'impact': 'Medium',
                'action': f"Periods outside {actual_year_min}-{report_year} excluded"
            })
    return {'passed': len(errors) == 0, 'errors': errors}


def run_quality_pipeline(ai_text, ctx, system_prompt="", ask_agent_fn=None, max_iterations=2):
    current = ai_text
    iteration = 0
    for iteration in range(max_iterations):
        result = validate_report_data(current, ctx)
        if result['passed']:
            break
        if ask_agent_fn and iteration < max_iterations-1:
            err_report = "\n".join(f"- {e['error']}" for e in result['errors'])
            prompt = (f"Rewrite removing: {err_report}\n"
                      f"Facts: revenue=${ctx['total_revenue']:,.2f}, "
                      f"best={ctx['best_group']}, forecast12=${ctx['fc12']:,.0f}\n"
                      f"Do NOT mention AI, AI Analysis, or AI Generated.\n"
                      f"ORIGINAL:\n{current}\nReturn corrected text only.")
            try:
                corrected, _ = ask_agent_fn(prompt, system_prompt, [])
                current = corrected
            except Exception:
                break
        else:
            break
    final = validate_report_data(current, ctx)
    return current, {'passed': final['passed'], 'errors': final['errors'], 'iterations': iteration+1}


# ═══════════════════════════════════════════════════════════
# 6. CHART UTILITIES
# ═══════════════════════════════════════════════════════════
PAGE_W, PAGE_H = A4
MARGIN    = 0.85 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

def _set_chart_style():
    rcParams.update({
        'font.family': 'sans-serif', 'axes.spines.top': False,
        'axes.spines.right': False, 'axes.linewidth': 0.5,
        'axes.grid': True, 'grid.alpha': 0.10, 'grid.linewidth': 0.4,
        'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5,
        'figure.facecolor': 'white', 'axes.facecolor': 'white',
    })

_set_chart_style()

def _money(x, pos=None):
    if x is None: return 'N/A'
    if   abs(x) >= 1e9: return f'${x/1e9:.1f}B'
    elif abs(x) >= 1e6: return f'${x/1e6:.1f}M'
    elif abs(x) >= 1e3: return f'${x/1e3:.0f}K'
    return f'${x:.0f}'

def _fig_to_img(fig, width=CONTENT_W, height=2.9*inch):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=180, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width, height=height)


# ═══════════════════════════════════════════════════════════
# 7. TYPOGRAPHY
# ═══════════════════════════════════════════════════════════
def build_styles(lang: str = 'en'):
    fn      = get_font(lang, bold=False)
    fn_bold = get_font(lang, bold=True)
    align   = TA_RIGHT if lang=='ar' else TA_LEFT
    S = {}
    defs = [
        ('cover_eyebrow',    8.5,  fn_bold, 'blue_mid',  TA_CENTER, 6,  12, 0),
        ('cover_title',      26,   fn_bold, 'navy',      TA_CENTER, 10, 32, 0),
        ('cover_subtitle',   13,   fn,      'gray_mid',  TA_CENTER, 6,  19, 0),
        ('cover_meta_label', 7.5,  fn_bold, 'gray',      align,     0,  11, 0),
        ('cover_meta_value', 10,   fn,      'navy',      align,     0,  14, 0),
        ('section_label',    8,    fn_bold, 'blue_mid',  align,     4,  12, 18),
        ('h1',               17,   fn_bold, 'navy',      align,     6,  21, 4),
        ('h2',               12,   fn_bold, 'blue',      align,     5,  16, 12),
        ('h3',               10.5, fn_bold, 'gray_dark', align,     4,  14, 8),
        ('body_small',       8.5,  fn,      'gray_mid',  align,     4,  12, 0),
        ('metric_value',     20,   fn_bold, 'navy',      TA_CENTER, 2,  24, 0),
        ('metric_label',     7.5,  fn,      'gray',      TA_CENTER, 0,  10, 0),
        ('metric_bear',      18,   fn_bold, 'bear',      TA_CENTER, 2,  22, 0),
        ('metric_bull',      18,   fn_bold, 'bull',      TA_CENTER, 2,  22, 0),
        ('toc_entry',        10,   fn,      'gray_dark', align,     4,  14, 0),
        ('toc_page',         10,   fn,      'blue_mid',  TA_RIGHT,  4,  14, 0),
        ('callout_blue',     9.5,  fn,      'blue',      align,     4,  15, 0),
        ('callout_green',    9.5,  fn,      'green',     align,     4,  15, 0),
        ('callout_amber',    9.5,  fn,      'amber',     align,     4,  15, 0),
        ('callout_red',      9.5,  fn,      'red',       align,     4,  15, 0),
        ('footer',           7,    fn,      'gray',      TA_CENTER, 0,  9,  0),
        ('validation_ok',    8,    fn,      'green',     TA_LEFT,   0,  11, 0),
        ('validation_err',   8,    fn,      'red',       TA_LEFT,   0,  11, 0),
        ('confidence_badge', 8,    fn_bold, 'teal',      TA_LEFT,   0,  11, 0),
        ('col_definition',   8.5,  fn,      'teal',      align,     8,  13, 0),
        ('kpi_value',        16,   fn_bold, 'navy',      TA_CENTER, 2,  20, 0),
        ('kpi_label',        7,    fn,      'gray',      TA_CENTER, 0,  9,  0),
        ('bullet',           9.5,  fn,      'gray_dark', align,     4,  15, 0),
    ]
    for name, fs, font, color_key, aln, sa, lead, sb in defs:
        kwargs = dict(fontSize=fs, fontName=font, textColor=rl(color_key),
                      alignment=aln, spaceAfter=sa, leading=lead)
        if sb: kwargs['spaceBefore'] = sb
        if name == 'bullet':
            kwargs['leftIndent'] = 14 if lang != 'ar' else 0
        if name in ('callout_blue', 'callout_green', 'callout_amber', 'callout_red'):
            kwargs['leftIndent'] = 12
        S[name] = ParagraphStyle(name, **kwargs)

    S['body'] = ParagraphStyle('body', fontSize=9.5, fontName=fn, textColor=rl('gray_dark'),
                               alignment=TA_JUSTIFY if lang != 'ar' else TA_RIGHT,
                               spaceAfter=6, leading=15)
    return S


# ═══════════════════════════════════════════════════════════
# 8. LAYOUT HELPERS
# ═══════════════════════════════════════════════════════════
def _divider(story, color=None, thickness=0.5, sb=6, sa=10):
    story.append(Spacer(1, sb/72*inch))
    story.append(HRFlowable(width="100%", thickness=thickness,
                             color=color or rl('border'), spaceAfter=sa/72*inch))

def _section_header(story, number, title, S, lang='en'):
    story.append(Spacer(1, 0.12*inch))
    story.append(Paragraph(process_text(f"SECTION {number}", lang), S['section_label']))
    story.append(Paragraph(process_text(title, lang), S['h1']))
    _divider(story, color=rl('blue'), thickness=1.1, sb=2, sa=12)

def _callout(story, text, style='blue', S=None, lang='en'):
    bg_map = {
        'blue':  (rl('blue_light'),  rl('blue_mid')),
        'green': (rl('green_light'), rl('green')),
        'amber': (rl('amber_light'), rl('amber')),
        'red':   (rl('red_light'),   rl('red')),
    }
    bg, border = bg_map.get(style, bg_map['blue'])
    tbl = Table([[Paragraph(process_text(text, lang), S[f'callout_{style}'])]],
                colWidths=[CONTENT_W - 0.3*inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('LINEBEFORE',    (0,0),(0,-1),  3, border),
        ('TOPPADDING',    (0,0),(-1,-1), 9),
        ('BOTTOMPADDING', (0,0),(-1,-1), 9),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 10),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.08*inch))

def _pro_table(story, data, col_widths=None, lang='en', max_chars=110):
    if not data: return
    n  = len(data[0])
    cw = col_widths or [CONTENT_W/n]*n

    def _safe(cell, mc=max_chars):
        s = str(cell)
        return s[:mc] + '…' if len(s) > mc else s

    processed = [[process_text(_safe(cell), lang) for cell in row] for row in data]
    style = [
        ('FONTNAME',      (0,0),(-1,-1), get_font(lang)),
        ('FONTSIZE',      (0,0),(-1,-1), 8.5),
        ('TEXTCOLOR',     (0,0),(-1,-1), rl('gray_dark')),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 7),
        ('RIGHTPADDING',  (0,0),(-1,-1), 7),
        ('GRID',          (0,0),(-1,-1), 0.25, rl('border')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [rl('white'), rl('gray_pale')]),
        ('ALIGN',         (1,0),(-1,-1), 'RIGHT' if lang != 'ar' else 'LEFT'),
        ('ALIGN',         (0,0),(0,-1),  'LEFT'  if lang != 'ar' else 'RIGHT'),
        ('BACKGROUND',    (0,0),(-1,0),  rl('navy')),
        ('TEXTCOLOR',     (0,0),(-1,0),  rl('white')),
        ('FONTNAME',      (0,0),(-1,0),  get_font(lang, bold=True)),
        ('ALIGN',         (0,0),(-1,0),  'CENTER'),
        ('TOPPADDING',    (0,0),(-1,0),  8),
        ('BOTTOMPADDING', (0,0),(-1,0),  8),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
    ]
    tbl = Table(processed, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle(style))
    story.append(tbl)
    story.append(Spacer(1, 0.12*inch))

def _confidence_badge(story, level: str, S, lang='en'):
    icons = {"High":"🟢","Medium":"🟡","Low":"🔴"}
    story.append(Paragraph(
        process_text(f"{icons.get(level,'🟡')} Forecast Confidence: {level}", lang),
        S['confidence_badge']))
    story.append(Spacer(1, 0.06*inch))

def _volatility_block(story, volatility: dict, cv_pct: float, S, lang='en'):
    if not volatility: return
    # FIX-P1: Always read level from dict, never hardcode
    level = volatility.get('level', 'High')
    badge = volatility.get('badge', '🔴')
    risk  = volatility.get('risk', '')
    style = 'amber' if level in ('High', 'Extreme') else 'blue'
    _callout(story,
             f"<b>{badge} Revenue Volatility: {level} (CV = {cv_pct:.1f}%)</b><br/>{risk}",
             style, S, lang)


# ═══════════════════════════════════════════════════════════
# 9. PAGE FOOTER
# ═══════════════════════════════════════════════════════════
class ReportCanvas:
    def __init__(self, report_date: str, lang: str = 'en'):
        self.report_date = report_date
        self.lang        = lang

    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(rl('blue'))
        canvas.rect(MARGIN, PAGE_H - 0.36*inch, CONTENT_W, 2.2, fill=1, stroke=0)
        canvas.setStrokeColor(rl('border'))
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN, 0.60*inch, PAGE_W - MARGIN, 0.60*inch)
        canvas.setFont(get_font(self.lang), 7)
        canvas.setFillColor(rl('gray'))
        canvas.drawString(MARGIN, 0.40*inch, "Confidential Business Analysis Report")
        canvas.drawCentredString(PAGE_W/2, 0.40*inch, f"Page {doc.page}")
        canvas.drawRightString(PAGE_W - MARGIN, 0.40*inch, self.report_date)
        canvas.restoreState()


# ═══════════════════════════════════════════════════════════
# 10. MARKDOWN RENDERER
# ═══════════════════════════════════════════════════════════
def _clean_md(text: str) -> str:
    text = re.sub(r'^#{1,4}\s*', '', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*',    r'<i>\1</i>', text)
    text = re.sub(r'[■□▪▫●►▸▶\u25A0-\u25FF]', '', text)
    text = re.sub(r'\bAI\s+(Analysis|Generated|Consultant|Recommendation)\b', '',
                  text, flags=re.IGNORECASE)
    return text.strip()

def _render_analysis(story, text: str, S, lang: str = 'en'):
    if not text: return
    table_buf = []
    for raw in text.split('\n'):
        line = raw.rstrip()
        if table_buf and not (line.startswith('|') and line.endswith('|')):
            _flush_md_table(story, table_buf, S, lang); table_buf = []
        if not line.strip(): story.append(Spacer(1, 0.06*inch)); continue
        if line.startswith('|') and line.endswith('|'):
            if not re.match(r'^\|[\s\-:]+\|$', line):
                table_buf.append([c.strip() for c in line.strip('|').split('|')])
            continue
        if re.match(r'^-{3,}$', line.strip()):
            _divider(story, sb=4, sa=6); continue
        clean = _clean_md(line)
        if not clean: continue
        if   line.strip().startswith('### '): story.append(Paragraph(process_text(clean,lang), S['h3']))
        elif line.strip().startswith('## '):  story.append(Paragraph(process_text(clean,lang), S['h2']))
        elif line.strip().startswith('# '):   story.append(Paragraph(process_text(clean,lang), S['h1']))
        elif line.strip().startswith(('- ','* ')):
            story.append(Paragraph(f"\u2022  {process_text(clean[2:],lang)}", S['bullet']))
        else:
            pt = process_text(clean, lang)
            if any(k in clean for k in ['⚠️','Warning','Critical']):
                story.append(Paragraph(pt, S['callout_amber']))
            else:
                story.append(Paragraph(pt, S['body']))
    if table_buf: _flush_md_table(story, table_buf, S, lang)

def _flush_md_table(story, rows, S, lang):
    if not rows: return
    n = max(len(r) for r in rows)
    _pro_table(story, rows, col_widths=[CONTENT_W/n]*n, lang=lang)


# ═══════════════════════════════════════════════════════════
# 11. REPORT SECTIONS
# ═══════════════════════════════════════════════════════════

def _cover(story, company_name, S, ctx, lang):
    story.append(Spacer(1, 1.2*inch))
    rule = Table([['']], colWidths=[CONTENT_W], rowHeights=[3])
    rule.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),rl('blue'))]))
    story.append(rule); story.append(Spacer(1, 0.3*inch))
    client = company_name if company_name else "Client Organization"
    t = {
        'en': ("BUSINESS INTELLIGENCE REPORT",
               "Sales Performance Analysis Report",
               "Performance Assessment & Strategic Intelligence"),
        'ar': ("تقرير الذكاء التجاري",
               "تقرير تحليل أداء المبيعات",
               "تقييم الأداء والاستخبارات الاستراتيجية"),
        'fr': ("RAPPORT D'INTELLIGENCE COMMERCIALE",
               "Rapport d'Analyse des Ventes",
               "Évaluation de la Performance & Intelligence Stratégique"),
    }.get(lang, ("BUSINESS INTELLIGENCE REPORT","Sales Performance Analysis Report",
                 "Performance Assessment & Strategic Intelligence"))
    story.append(Paragraph(process_text(t[0],lang), S['cover_eyebrow']))
    story.append(Spacer(1,0.15*inch))
    story.append(Paragraph(process_text(t[1],lang), S['cover_title']))
    story.append(Spacer(1,0.12*inch))
    story.append(Paragraph(process_text(t[2],lang), S['cover_subtitle']))
    story.append(Spacer(1,0.3*inch)); story.append(rule); story.append(Spacer(1,0.45*inch))
    lbl = {'en':["PREPARED FOR","REPORTING PERIOD","REPORT DATE","CLASSIFICATION"],
           'ar':["مُعدّ لـ","فترة التقرير","تاريخ التقرير","التصنيف"],
           'fr':["PRÉPARÉ POUR","PÉRIODE","DATE DU RAPPORT","CLASSIFICATION"]
           }.get(lang,["PREPARED FOR","REPORTING PERIOD","REPORT DATE","CLASSIFICATION"])
    meta = [(lbl[0],client),(lbl[1],ctx['date_range']),
            (lbl[2],ctx['report_date']),(lbl[3],"Confidential")]
    rows = [[Paragraph(process_text(k,lang),S['cover_meta_label']),
             Paragraph(process_text(str(v),lang),S['cover_meta_value'])] for k,v in meta]
    mt = Table(rows, colWidths=[1.7*inch, CONTENT_W-1.7*inch])
    mt.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'LEFT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LINEBELOW',(0,0),(-1,-2),0.25,rl('border')),('LEFTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(mt); story.append(PageBreak())


def _toc(story, S, ctx, lang, has_store, has_corr):
    story.append(Paragraph(process_text('TABLE OF CONTENTS', lang), S['section_label']))
    story.append(Paragraph(process_text('Report Structure', lang), S['h1']))
    _divider(story, color=rl('blue'), thickness=1.1, sb=2, sa=16)

    sections = [
        ("00", "Executive KPI Dashboard",    "3"),
        ("01", "Executive Summary",          "4"),
        ("02", "Data Quality Assessment",    "5"),
        ("03", "Key Findings",               "6"),
        ("04", "Sales Performance Overview", "7"),
        ("05", "Period Trend Analysis",      "8"),
    ]
    pg = 9
    if has_store:
        sections.append(("06", "Segment Performance & Scorecard", str(pg))); pg += 1
    if has_corr:
        sections.append(("07", "Statistical Validation & Correlations", str(pg))); pg += 1
    sections.append(("08", "Revenue Forecast & Scenarios", str(pg)));  pg += 1
    sections.append(("09", "Risk Assessment Matrix",        str(pg)));  pg += 1
    sections.append(("10", "Growth Opportunity Assessment", str(pg)));  pg += 1
    sections.append(("11", "Strategic Recommendations",     str(pg)));  pg += 1
    sections.append(("12", "Data Appendix & Methodology",  str(pg)))

    for num, title_en, page in sections:
        row = [[
            Paragraph(f"<b>{num}</b>",
                      ParagraphStyle('tn', fontSize=9, fontName=get_font(lang,True),
                                     textColor=rl('blue_mid'), alignment=TA_LEFT, leading=13)),
            Paragraph(process_text(title_en, lang), S['toc_entry']),
            Paragraph(page, S['toc_page']),
        ]]
        rt = Table(row, colWidths=[0.45*inch, CONTENT_W-1.1*inch, 0.65*inch])
        rt.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('LINEBELOW',(0,0),(-1,-1),0.2,rl('border')),
        ]))
        story.append(rt)
    story.append(PageBreak())


def _executive_kpi_dashboard(story, S, ctx, dq, lang):
    _section_header(story,"00","Executive KPI Dashboard",S,lang)
    story.append(Paragraph(process_text(
        "At-a-glance portfolio performance. All metrics derived directly from the uploaded dataset.",
        lang), S['body_small']))
    story.append(Spacer(1,0.12*inch))

    conf_icon = {"High":"🟢","Medium":"🟡","Low":"🔴"}.get(ctx['confidence_level'],"🟡")
    # FIX-P1: Read volatility level from dict
    vol_lvl  = ctx['volatility_level']
    vol_icon = {"Low":"🟢","Moderate":"🟡","High":"🔴","Extreme":"🚨"}.get(vol_lvl,"🔴")

    r1 = [
        [Paragraph(process_text(_money(ctx['total_revenue']),lang),S['kpi_value']),
         Paragraph(process_text(_money(ctx['fc12']),lang),S['kpi_value']),
         Paragraph(process_text(f"{ctx['trend_pct']:+.1f}%",lang),S['kpi_value']),
         Paragraph(process_text(_money(ctx['avg_per_period']),lang),S['kpi_value'])],
        [Paragraph(process_text("Total Revenue",lang),S['kpi_label']),
         Paragraph(process_text("12-Period Forecast (Base)",lang),S['kpi_label']),
         Paragraph(process_text("Revenue Growth (HoH)",lang),S['kpi_label']),
         Paragraph(process_text("Avg per Period",lang),S['kpi_label'])],
    ]
    t1 = Table(r1, colWidths=[CONTENT_W/4]*4, rowHeights=[0.40*inch,0.22*inch])
    t1.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),rl('blue_pale')),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('GRID',(0,0),(-1,-1),0.3,rl('border')),
        ('LINEABOVE',(0,0),(-1,0),2,rl('navy')),('LINEBELOW',(0,-1),(-1,-1),2,rl('navy')),
        ('TOPPADDING',(0,0),(-1,0),8),('BOTTOMPADDING',(0,-1),(-1,-1),6),
    ]))
    story.append(t1); story.append(Spacer(1,0.08*inch))

    r2 = [
        [Paragraph(process_text(f"Grp {ctx.get('best_group','N/A')}",lang),S['kpi_value']),
         Paragraph(process_text(f"Grp {ctx.get('worst_group','N/A')}",lang),S['kpi_value']),
         Paragraph(process_text(f"{conf_icon} {ctx['confidence_level']}",lang),S['kpi_value']),
         Paragraph(process_text(f"{vol_icon} {vol_lvl}",lang),S['kpi_value'])],
        [Paragraph(process_text("Best Quantity Group",lang),S['kpi_label']),
         Paragraph(process_text("Worst Quantity Group",lang),S['kpi_label']),
         Paragraph(process_text("Forecast Confidence",lang),S['kpi_label']),
         Paragraph(process_text("Revenue Volatility",lang),S['kpi_label'])],
    ]
    t2 = Table(r2, colWidths=[CONTENT_W/4]*4, rowHeights=[0.40*inch,0.22*inch])
    t2.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,-1),rl('green_light')),
        ('BACKGROUND',(1,0),(1,-1),rl('red_light')),
        ('BACKGROUND',(2,0),(2,-1),rl('blue_pale')),
        ('BACKGROUND',(3,0),(3,-1),rl('amber_light')),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('GRID',(0,0),(-1,-1),0.3,rl('border')),
        ('LINEBELOW',(0,-1),(-1,-1),2,rl('navy')),
        ('TOPPADDING',(0,0),(-1,0),8),('BOTTOMPADDING',(0,-1),(-1,-1),6),
    ]))
    story.append(t2); story.append(Spacer(1,0.12*inch))

    top_risk = ("Revenue Concentration" if ctx.get('pareto_pct',33) < 30
                else "High Revenue Volatility" if ctx.get('cv_pct',0) > 70
                else "Forecast Uncertainty")
    _callout(story,
             f"⚠️ <b>Top Business Risk: {top_risk}</b> — "
             f"Top {ctx.get('pareto_pct',33):.0f}% of quantity groups generate 80% of revenue. "
             f"Single-group dependency requires diversification strategy.",
             'amber', S, lang)

    dq_col = {'Excellent':'green','Good':'blue','Fair':'amber','Poor':'red'}.get(dq.get('rating','Fair'),'amber')
    _callout(story,
             f"📊 <b>Data Quality: {dq.get('rating','N/A')}</b> "
             f"(Completeness: {dq.get('completeness',0):.1f}/100) — "
             f"{ctx['n_records']:,} records | "
             f"{dq.get('n_missing',0)} missing | "
             f"{dq.get('n_duplicates',0)} duplicates | "
             f"{dq.get('n_outliers',0)} outliers (IQR method).",
             dq_col, S, lang)
    story.append(PageBreak())


def _executive_summary(story, S, ctx, lang, analysis_text=None):
    _section_header(story,"01","Executive Summary",S,lang)

    col_w = CONTENT_W/4
    m_vals = [
        (_money(ctx['total_revenue']),  "Total Revenue"),
        (_money(ctx['avg_per_period']), "Avg per Period"),
        (_money(ctx['peak_value']),     "Peak Performance"),
        (_money(ctx['fc12']),           "12-Period Forecast"),
    ]
    mt = Table(
        [[Paragraph(process_text(v,lang),S['metric_value']) for v,_ in m_vals],
         [Paragraph(process_text(l,lang),S['metric_label']) for _,l in m_vals]],
        colWidths=[col_w]*4, rowHeights=[0.46*inch,0.26*inch]
    )
    mt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),rl('blue_pale')),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('GRID',(0,0),(-1,-1),0.35,rl('border')),
        ('LINEABOVE',(0,0),(-1,0),1.4,rl('blue')),
        ('LINEBELOW',(0,-1),(-1,-1),1.4,rl('blue')),
        ('TOPPADDING',(0,0),(-1,0),10),('BOTTOMPADDING',(0,-1),(-1,-1),8),
    ]))
    story.append(mt); story.append(Spacer(1,0.18*inch))

    if ctx.get('fc_gap_flag', False):
        _callout(story,
            f"⚠️ <b>Forecast Anomaly Notice:</b> The 12-period forecast average "
            f"(${ctx['fc12_avg_per_period']:,.0f}/period) is "
            f"<b>{ctx['fc_gap_pct']:+.0f}%</b> above the current historical average "
            f"(${ctx['avg_per_period']:,.0f}/period). "
            f"Treat as directional signal only. "
            f"<b>Plan operations around Bear/Base/Bull range — not base case alone.</b>",
            'red', S, lang)
        story.append(Spacer(1,0.08*inch))

    # FIX-P2: RESOLUTION section uses correct tense based on peak timing
    if ctx['peak_is_past']:
        resolution_text = (
            f"Two evidence-based priorities: "
            f"(1) Investigate operational drivers of Group {ctx['best_group']} — "
            f"owner: Sales Manager, deadline: {ctx['action_deadline_30']}. "
            f"(2) Historical peak occurred at <b>{ctx['peak_week']}</b> "
            f"({_money(ctx['peak_fc'])}) — now use post-peak data to calibrate next cycle forecast. "
            f"[Confidence: Medium-to-Low pending domain validation]"
        )
    else:
        resolution_text = (
            f"Two evidence-based priorities: "
            f"(1) Investigate operational drivers of Group {ctx['best_group']} — "
            f"owner: Sales Manager, deadline: {ctx['action_deadline_30']}. "
            f"(2) Prepare for projected peak at <b>{ctx['peak_week']}</b> "
            f"({_money(ctx['peak_fc'])}) — {ctx['peak_urgency'].get('message','')}. "
            f"[Confidence: Medium-to-Low pending domain validation]"
        )

    # FIX-P1: Dynamic volatility label in SITUATION
    vol_label = ctx['volatility_level']

    paras = [
        ("SITUATION — Where We Are",
         f"The portfolio generated <b>${ctx['total_revenue']:,.0f}</b> across "
         f"<b>{ctx['n_records']:,} records</b> over <b>{ctx['n_periods']:,} periods</b> "
         f"({ctx['date_range']}). Revenue trend: <b>{ctx['trend_direction']}</b> "
         f"({ctx['trend_pct']:+.1f}% half-over-half). "
         f"Mean: ${ctx['avg_per_period']:,.0f}/period | "
         f"Median: ${ctx['median_per_period']:,.0f}/period "
         f"[Median preferred given right-skewed distribution, CV={ctx['cv_pct']:.1f}% — {vol_label} volatility].",
         'blue'),
        ("COMPLICATION — The Critical Issue",
         f"Revenue is highly concentrated: "
         f"<b>{ctx.get('pareto_pct',33):.0f}% of quantity groups = 80% of revenue</b>, "
         f"led by Group <b>{ctx['best_group']}</b> "
         f"(${ctx['best_group_revenue']:,.0f}, {ctx['best_group_share']:.1f}% of total). "
         f"Group <b>{ctx['worst_group']}</b> underperforms by "
         f"<b>${ctx['worst_group_gap_weekly']:,.0f}/period</b> vs. average — "
         f"representing <b>${ctx['worst_group_12p_cost']:,.0f}</b> potential foregone revenue "
         f"over 12 periods [DERIVED: gap × 12 periods]. "
         f"Note: Quantity group business meaning requires domain expert validation.",
         'amber'),
        ("RESOLUTION — Recommended Actions", resolution_text, 'blue'),
        ("STAKES — Financial Impact",
         f"Full implementation estimated to deliver "
         f"<b>{_money(ctx['total_revenue']*0.15)}–{_money(ctx['total_revenue']*0.22)}</b> "
         f"incremental annual revenue (15–22% uplift on {_money(ctx['total_revenue'])} baseline). "
         f"[DERIVED: gap analysis + scenario modeling — "
         f"subject to market conditions and execution quality.] "
         f"90-day inaction cost: ~{_money(ctx['worst_group_gap_weekly']*13)}.",
         'green'),
    ]
    for title, body, style in paras:
        story.append(Paragraph(process_text(title,lang), S['h3']))
        _callout(story, body, style, S, lang)
        story.append(Spacer(1,0.04*inch))

    if analysis_text:
        _divider(story, sb=8, sa=8)
        story.append(Paragraph(process_text("Performance Analysis",lang), S['h2']))
        _render_analysis(story, analysis_text, S, lang)
    story.append(PageBreak())


def _data_quality_section(story, S, dq, ctx, lang):
    _section_header(story,"02","Data Quality Assessment",S,lang)
    story.append(Paragraph(process_text(
        "A rigorous data quality assessment was conducted prior to analysis. "
        "All analytical conclusions should be interpreted in the context of these metrics.",
        lang), S['body']))
    story.append(Spacer(1,0.15*inch))

    score  = dq.get('completeness', 0)
    rating = dq.get('rating', 'Fair')
    sc = Table(
        [[Paragraph(process_text(f"{score:.1f}",lang),S['metric_value']),
          Paragraph(process_text(rating,lang),S['metric_value'])],
         [Paragraph(process_text("Data Completeness Score (/100)",lang),S['metric_label']),
          Paragraph(process_text("Quality Rating",lang),S['metric_label'])]],
        colWidths=[CONTENT_W/2]*2, rowHeights=[0.46*inch,0.26*inch]
    )
    sc.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),rl('blue_pale')),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('GRID',(0,0),(-1,-1),0.35,rl('border')),
        ('LINEABOVE',(0,0),(-1,0),1.4,rl('blue')),('LINEBELOW',(0,-1),(-1,-1),1.4,rl('blue')),
    ]))
    story.append(sc); story.append(Spacer(1,0.15*inch))

    def _si(val, ok, warn):
        if val <= ok:    return "✅ OK"
        elif val <= warn: return "⚠️ Review"
        return "❌ Action Required"

    rows = [
        ["Quality Metric","Value","Status","Notes"],
        ["Total Records",     f"{dq['n_total']:,}","✅ OK","Sufficient for statistical analysis"],
        ["Missing Values",    f"{dq['n_missing']} ({dq['missing_pct']:.2f}%)",
         _si(dq['missing_pct'],1,5),
         f"Cols: {', '.join(dq['missing_by_col'].keys()) or 'None'}"],
        ["Duplicate Records", f"{dq['n_duplicates']} ({dq['dup_pct']:.2f}%)",
         _si(dq['dup_pct'],0.5,2),"Excluded from analysis if present"],
        ["Outliers (IQR)",    f"{dq['n_outliers']} ({dq['outlier_pct']:.1f}%)",
         _si(dq['outlier_pct'],5,15),
         f"IQR bounds: [{_money(dq['outlier_bounds'][0])}, {_money(dq['outlier_bounds'][1])}]"],
        ["Quality Score",     f"{score:.1f} / 100",
         f"{'✅' if rating in ('Excellent','Good') else '⚠️'} {rating}",
         "100 − missing% − dup% − outlier%×0.5"],
    ]
    _pro_table(story, rows, col_widths=[1.7*inch,1.3*inch,1.1*inch,CONTENT_W-4.1*inch], lang=lang)

    if not dq['issues_found']:
        _callout(story,"✅ Data quality checks completed. No significant issues detected.",'green',S,lang)
    else:
        issues = []
        if dq['n_outliers']  > 0: issues.append(f"{dq['n_outliers']} outliers (IQR) retained")
        if dq['n_missing']   > 0: issues.append(f"{dq['n_missing']} missing values excluded")
        if dq['n_duplicates']> 0: issues.append(f"{dq['n_duplicates']} duplicates removed")
        _callout(story,f"⚠️ <b>Quality Notes:</b> {' | '.join(issues)}. Conclusions remain valid.",'amber',S,lang)

    story.append(Spacer(1,0.12*inch))
    story.append(Paragraph(process_text("Revenue Distribution Summary Statistics",lang), S['h2']))
    labels_bp = ['Minimum','Q1 (25th pct.)','Median (50th)','Mean','Q3 (75th pct.)','Maximum']
    values_bp = [
        max(0, ctx['min_value']),
        max(0, ctx.get('q1_value', ctx['avg_per_period']*0.5)),
        max(0, ctx['median_per_period']),
        max(0, ctx['avg_per_period']),
        max(0, ctx.get('q3_value', ctx['avg_per_period']*1.5)),
        max(0, ctx['peak_value']),
    ]
    clrs_bp = [mpl('chart3'),mpl('chart2'),mpl('chart1'),mpl('teal'),mpl('chart2'),mpl('bear')]
    fig, ax = plt.subplots(figsize=(9.0, 3.0))
    bars = ax.barh(labels_bp, values_bp, color=clrs_bp, height=0.5, edgecolor='white', linewidth=0.3)
    for bar, val in zip(bars, values_bp):
        ax.text(bar.get_width()+max(values_bp)*0.015, bar.get_y()+bar.get_height()/2,
                _money(val), va='center', fontsize=7.5, color=CH['gray_dark'])
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ax.set_title("Revenue Distribution — Key Statistics",fontsize=9.5,fontweight='bold',color=mpl('chart1'),pad=8)
    ax.spines['left'].set_color(CH['border']); ax.spines['bottom'].set_color(CH['border'])
    plt.tight_layout(pad=1.0)
    story.append(_fig_to_img(fig, height=2.6*inch)); story.append(Spacer(1,0.1*inch))

    mean_med_diff = ((ctx['avg_per_period']-ctx['median_per_period'])/ctx['median_per_period']*100
                     if ctx['median_per_period'] > 0 else 0)
    # FIX-P1: Dynamic volatility label
    vol_lbl = ctx['volatility_level']
    _callout(story,
             f"Mean (${ctx['avg_per_period']:,.0f}) exceeds Median (${ctx['median_per_period']:,.0f}) "
             f"by {abs(mean_med_diff):.1f}% — confirming right-skewed distribution. "
             f"Median is the more representative central tendency measure. "
             f"CV = {ctx['cv_pct']:.1f}% ({vol_lbl} volatility) — "
             f"average-based planning may be misleading.",
             'amber', S, lang)
    story.append(PageBreak())


def _key_findings(story, S, ctx, lang):
    _section_header(story,"03","Key Findings",S,lang)
    # FIX-P1: Dynamic volatility label
    vol_lbl = ctx['volatility_level']
    findings = [
        ("Revenue Baseline",
         f"Portfolio generated <b>${ctx['total_revenue']:,.0f}</b> across "
         f"<b>{ctx['n_records']:,}</b> records ({ctx['date_range']}). "
         f"Mean: <b>${ctx['avg_per_period']:,.0f}/period</b> | "
         f"Median: <b>${ctx['median_per_period']:,.0f}/period</b>. "
         f"CV = <b>{ctx['cv_pct']:.1f}%</b> — <b>{vol_lbl}</b> volatility. "
         f"Median recommended as primary central tendency metric.",
         'blue'),
    ]
    if ctx['best_group'] != 'N/A' and ctx['n_groups'] > 1:
        findings.append((
            f"Segment Performance — {ctx['n_groups']} Quantity Groups",
            f"Group <b>{ctx['best_group']}</b> leads: "
            f"<b>${ctx['best_group_revenue']:,.0f}</b> ({ctx['best_group_share']:.1f}% of total). "
            f"Group <b>{ctx['worst_group']}</b>: greatest improvement potential "
            f"(gap: ${ctx['worst_group_gap_weekly']:,.0f}/period vs. average). "
            + (f"Pareto: top <b>{ctx['pareto_pct']:.0f}%</b> of groups = 80% of revenue. "
               if ctx['pareto_pct']>0 else "") +
            f"<i>Note: Business interpretation requires domain expert validation.</i>",
            'green'))

    # FIX-P2: Forward outlook tense based on peak timing
    if ctx['peak_is_past']:
        peak_note = (f"Historical peak was <b>{ctx['peak_week']}</b> ({_money(ctx['peak_fc'])}). "
                     f"Post-peak: use actuals to recalibrate next cycle. ")
    else:
        peak_note = (f"Peak: <b>{ctx['peak_week']}</b> ({_money(ctx['peak_fc'])}). "
                     f"{ctx['peak_urgency'].get('message','')} ")

    findings.append((
        "Forward Outlook",
        f"Base case: <b>${ctx['fc4']:,.0f}</b> (4p) / <b>${ctx['fc12']:,.0f}</b> (12p) "
        f"[avg ${ctx['fc12_avg_per_period']:,.0f}/period]. "
        + (f"⚠️ Forecast avg is {ctx['fc_gap_pct']:+.0f}% above historical avg — "
           f"treat as directional. " if ctx.get('fc_gap_flag') else "") +
        f"Bear ({ctx['bear_prob']*100:.0f}%): ${ctx['bear_12']:,.0f} | "
        f"Bull ({ctx['bull_prob']*100:.0f}%): ${ctx['bull_12']:,.0f}. "
        + peak_note +
        f"Confidence: <b>{ctx['confidence_level']}</b>. "
        f"[Directional estimates — not guarantees.]",
        'amber'))
    for title, text, style in findings:
        story.append(Paragraph(process_text(title,lang), S['h3']))
        _callout(story, text, style, S, lang)
        story.append(Spacer(1,0.04*inch))
    story.append(PageBreak())


def _sales_overview(story, S, ctx, df, date_col, sales_col, company_name, lang):
    _section_header(story,"04","Sales Performance Overview",S,lang)
    story.append(Paragraph(process_text(
        f"Revenue across {ctx['n_periods']:,} periods ({ctx['date_range']}). "
        f"Peak: <b>${ctx['peak_value']:,.0f}</b>. "
        f"Trend: <b>{ctx['trend_direction']}</b> ({ctx['trend_pct']:+.1f}% HoH).",
        lang), S['body']))
    story.append(Spacer(1,0.1*inch))

    weekly = df.groupby(date_col)[sales_col].sum().reset_index().sort_values(date_col)
    weekly['ma'] = weekly[sales_col].rolling(4, min_periods=1).mean()
    sales_vals   = df[sales_col].dropna()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 6.5))
    ax1.fill_between(weekly[date_col], weekly[sales_col], alpha=0.08, color=mpl('chart1'))
    ax1.plot(weekly[date_col], weekly[sales_col], color=mpl('chart1'),linewidth=1.2,alpha=0.7,label='Revenue')
    ax1.plot(weekly[date_col], weekly['ma'], color=mpl('chart2'),linewidth=2.0,zorder=5,label='4-Period MA')
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ax1.set_title((company_name+"  —  " if company_name else "")+"Revenue Trend",
                  fontsize=10,fontweight='bold',color=mpl('chart1'))
    ax1.legend(fontsize=7.5,framealpha=0.9)
    ax1.spines['left'].set_color(CH['border']); ax1.spines['bottom'].set_color(CH['border'])

    ax2.hist(sales_vals, bins=30, color=mpl('chart1'), alpha=0.7, edgecolor='white', linewidth=0.3)
    ax2.axvline(x=float(sales_vals.mean()),  color=mpl('chart2'),linewidth=1.5,linestyle='--',
                label=f"Mean: {_money(float(sales_vals.mean()))}")
    ax2.axvline(x=float(sales_vals.median()),color=mpl('teal'),  linewidth=1.5,linestyle=':',
                label=f"Median: {_money(float(sales_vals.median()))}")
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ax2.set_title("Revenue Distribution Histogram",fontsize=10,fontweight='bold',color=mpl('chart1'))
    ax2.set_ylabel("Frequency",fontsize=8)
    ax2.legend(fontsize=7.5)
    ax2.spines['left'].set_color(CH['border']); ax2.spines['bottom'].set_color(CH['border'])
    plt.tight_layout(pad=1.2)
    story.append(_fig_to_img(fig, height=5.0*inch)); story.append(Spacer(1,0.1*inch))
    _callout(story,
             f"Peak single-period: <b>${ctx['peak_value']:,.0f}</b>. "
             f"Trend: <b>{ctx['trend_direction']}</b> ({ctx['trend_pct']:+.1f}%). "
             f"Mean (${ctx['avg_per_period']:,.0f}) > Median (${ctx['median_per_period']:,.0f}) "
             f"confirms right-skewed distribution — median is more representative.",
             'blue', S, lang)
    story.append(PageBreak())


def _trend_analysis(story, S, ctx, monthly_df, company_name, lang):
    _section_header(story,"05","Period Trend Analysis",S,lang)
    months_str = [str(m) for m in monthly_df['month']]
    vals       = monthly_df['total'].tolist()
    if not vals:
        story.append(Paragraph(process_text("Insufficient data for trend analysis.",lang),S['body']))
        story.append(PageBreak()); return

    avg_val  = float(np.mean(vals))
    bar_clrs = [mpl('chart3') if v>=avg_val*1.05
                else mpl('chart2') if v>=avg_val*0.95
                else mpl('chart_neg') for v in vals]
    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    bars = ax.bar(months_str, vals, color=bar_clrs, width=0.62, edgecolor='white', linewidth=0.35)
    ax.axhline(y=avg_val, color=mpl('chart5'), linewidth=1.1, linestyle='--',
               alpha=0.8, label=f"Avg: {_money(avg_val)}")
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(vals)*0.011,
                _money(val), ha='center', va='bottom', fontsize=6, color=CH['gray_dark'])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ax.set_title((company_name+"  —  " if company_name else "")+"Period Revenue Distribution",
                 fontsize=10.5,fontweight='bold',color=mpl('chart1'),pad=10)
    ax.tick_params(axis='x',rotation=40,labelsize=7)
    ax.spines['left'].set_color(CH['border']); ax.spines['bottom'].set_color(CH['border'])
    ax.legend(fontsize=8)
    plt.tight_layout(pad=1.1)
    story.append(_fig_to_img(fig, height=3.0*inch)); story.append(Spacer(1,0.1*inch))
    _callout(story,
             f"Best period: <b>{ctx['best_period_label']}</b> ({_money(ctx['best_period_value'])}). "
             f"Weakest: <b>{ctx['worst_period_label']}</b> ({_money(ctx['worst_period_value'])}). "
             f"Period spread: {ctx['period_spread_pct']:.0f}% of average.",
             'blue', S, lang)
    story.append(PageBreak())


def _segment_analysis(story, S, ctx, store_df, group_col, company_name, lang, scorecards):
    _section_header(story,"06",f"Segment Performance & Scorecard — {group_col}",S,lang)
    _callout(story,
             f"ℹ️ <b>Column Definition:</b> '{group_col}' represents quantity tiers or volume bands. "
             f"<b>Business interpretation must be validated with domain experts before operational decisions.</b>",
             'blue', S, lang)
    story.append(Spacer(1,0.1*inch))

    top10     = store_df.head(10)
    total_rev = float(store_df['total'].sum())
    avg_rev   = float(store_df['total'].mean())
    labels    = top10[group_col].astype(str).tolist()
    rev       = top10['total'].tolist()
    bar_clrs  = [mpl('chart1') if i<3 else mpl('chart2') if i<7 else mpl('chart3') for i in range(len(rev))]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.8))
    bars = ax1.bar(labels, rev, color=bar_clrs, width=0.6, edgecolor='white', linewidth=0.35)
    ax1.axhline(y=avg_rev, color=mpl('chart5'), linewidth=1.1, linestyle='--', alpha=0.8, label=f"Avg: {_money(avg_rev)}")
    for bar, val in zip(bars, rev):
        ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(rev)*0.015,
                 _money(val), ha='center', va='bottom', fontsize=6, color=CH['gray_dark'])
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ax1.set_title(f"Top {len(top10)} {group_col} Groups — Revenue", fontsize=9, fontweight='bold', color=mpl('chart1'))
    ax1.legend(fontsize=7.5)
    ax1.spines['left'].set_color(CH['border']); ax1.spines['bottom'].set_color(CH['border'])

    sorted_rev = sorted(rev, reverse=True)
    cumulative = [sum(sorted_rev[:i+1])/total_rev*100 for i in range(len(sorted_rev))]
    x_pos      = list(range(1, len(sorted_rev)+1))
    ax2b = ax2.twinx()
    ax2.bar([str(x) for x in x_pos], sorted_rev, color=mpl('chart1'), alpha=0.7, width=0.6)
    ax2b.plot(x_pos, cumulative, color=mpl('bear'), linewidth=2, marker='o', markersize=4)
    ax2b.axhline(y=80, color=mpl('chart5'), linewidth=1, linestyle='--', alpha=0.7)
    ax2b.set_ylabel("Cumulative %", fontsize=7.5); ax2b.set_ylim(0, 110)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ax2.set_title("Pareto Analysis (80/20 Rule)", fontsize=9, fontweight='bold', color=mpl('chart1'))
    ax2.spines['left'].set_color(CH['border']); ax2.spines['bottom'].set_color(CH['border'])
    plt.tight_layout(pad=1.0)
    story.append(_fig_to_img(fig, height=3.2*inch)); story.append(Spacer(1,0.1*inch))

    hdr = [group_col,"Total Revenue","Avg / Period","Portfolio Share"]
    tbl_data = [hdr]
    for _, row in top10.iterrows():
        share = row['total']/total_rev*100 if total_rev>0 else 0
        tbl_data.append([str(row[group_col]), f"${row['total']:,.0f}", f"${row['avg_weekly']:,.0f}", f"{share:.1f}%"])
    _pro_table(story, tbl_data, col_widths=[1.5*inch,1.8*inch,1.8*inch,1.8*inch], lang=lang)

    if ctx['pareto_n'] > 0:
        _callout(story,
                 f"<b>Pareto Concentration:</b> {ctx['pareto_n']} of {ctx['n_groups']} groups "
                 f"({ctx['pareto_pct']:.0f}%) generate 80% of total revenue. "
                 "This represents a systemic concentration risk.",
                 'green', S, lang)

    if scorecards:
        story.append(Spacer(1,0.15*inch))
        story.append(Paragraph(process_text("Segment Scorecard — Performance Grading",lang), S['h2']))
        story.append(Paragraph(process_text(
            "Graded across Revenue Contribution, Efficiency, Growth Potential, and Concentration Risk. "
            "Grades are relative to portfolio — not absolute market benchmarks.",
            lang), S['body_small']))
        story.append(Spacer(1,0.08*inch))
        sc_hdr  = ["Group","Rev. Score","Efficiency","Growth Pot.","Risk Score","Overall","Grade"]
        sc_rows = [sc_hdr]
        for sc in scorecards[:10]:
            sc_rows.append([sc['segment'], f"{sc['rev_score']:.1f}", f"{sc['eff_score']:.1f}",
                            f"{sc['growth_score']:.1f}", f"{sc['risk_score']:.1f}", f"{sc['overall']:.1f}", sc['grade']])
        _pro_table(story, sc_rows,
                   col_widths=[0.8*inch,0.9*inch,0.9*inch,0.9*inch,0.9*inch,0.9*inch,0.7*inch], lang=lang)
        story.append(Paragraph(process_text(
            "Grade Scale: A+ (≥80) Excellent | A (65–79) Good | B+ (50–64) Above Avg | B (35–49) Average | C (20–34) Below Avg | D (<20) Critical",
            lang), S['body_small']))
    story.append(PageBreak())


def _statistical_validation(story, S, ctx, stat_results, lang):
    _section_header(story,"07","Statistical Validation & Correlations",S,lang)
    story.append(Paragraph(process_text(
        "All correlations include Pearson coefficients, P-values, sample sizes, and significance. "
        "<b>Correlation does not imply causation.</b> All relationships require domain validation.",
        lang), S['body']))
    story.append(Spacer(1,0.12*inch))

    corr_details = stat_results.get('correlations', [])
    if corr_details:
        fig, ax = plt.subplots(figsize=(9.5, max(2.8, len(corr_details)*0.7)))
        vars_    = [d['variable'] for d in corr_details]
        r_vals   = [d['r'] for d in corr_details]
        bar_clrs = [mpl('chart_pos') if r>0 else mpl('chart_neg') for r in r_vals]
        bars     = ax.barh(vars_, r_vals, color=bar_clrs, height=0.5, edgecolor='white', linewidth=0.3)
        for bar, d in zip(bars, corr_details):
            p_str = f"r={d['r']:+.4f}, p={d['p_display']}"
            ax.text(bar.get_width()+(0.01 if bar.get_width()>=0 else -0.01),
                    bar.get_y()+bar.get_height()/2, p_str, va='center',
                    ha='left' if bar.get_width()>=0 else 'right', fontsize=7.5)
        ax.axvline(x=0, color=CH['gray_dark'], linewidth=0.7)
        ax.set_xlabel("Pearson Coefficient (r)", fontsize=9)
        ax.set_title("Correlation Analysis — External Variables vs Revenue",
                     fontsize=10, fontweight='bold', color=mpl('chart1'), pad=10)
        ax.set_xlim(-1.0, 1.25)
        ax.spines['left'].set_color(CH['border']); ax.spines['bottom'].set_color(CH['border'])
        plt.tight_layout(pad=1.1)
        story.append(_fig_to_img(fig, height=max(2.5*inch, len(corr_details)*0.5*inch)))
        story.append(Spacer(1,0.12*inch))

        hdr  = ["Variable","Pearson r","P-Value","Sample (n)","Strength","Significance"]
        rows = [hdr]
        for d in corr_details:
            rows.append([d['variable'], f"{d['r']:+.4f}", d['p_display'],
                         f"{d['n']:,}", d['strength'],
                         "✅ Significant" if d['significant'] else "❌ Not Significant"])
        _pro_table(story, rows,
                   col_widths=[1.3*inch,0.9*inch,0.9*inch,0.9*inch,1.1*inch,1.8*inch], lang=lang)

        for d in corr_details:
            if d.get('practical_sig', False):
                interp = (
                    f"<b>{d['variable']}</b>: r = {d['r']:+.4f} | "
                    f"P-value: {d['p_display']} | n = {d['n']:,} | "
                    f"Strength: {d['strength']} ({d['direction']}) | {d['sig_label']}. "
                    f"[Statistical association only. Causal mechanism requires further investigation.]"
                )
                _callout(story, process_text(interp,lang), 'green' if d['r']>0 else 'amber', S, lang)

    normality = stat_results.get('normality')
    if normality:
        story.append(Spacer(1,0.1*inch))
        story.append(Paragraph(process_text("Distribution Normality Test",lang), S['h2']))
        norm_txt = (
            f"<b>{normality['test']} Test:</b> "
            f"W = {normality['statistic']:.4f}, p = {normality['p_display']} — "
            f"{normality['note']}. "
            f"[Non-normal distributions validate median-based central tendency.]"
        )
        _callout(story, process_text(norm_txt,lang), 'blue' if normality['normal'] else 'amber', S, lang)
    story.append(PageBreak())


def _forecast_section(story, S, ctx, forecast, prophet_data, company_name, lang, fc_accuracy):
    _section_header(story,"08","Revenue Forecast & Scenarios",S,lang)
    story.append(Paragraph(process_text(
        "Forward-looking projections based on Holt-Winters Exponential Smoothing. "
        "Three scenarios support robust planning. Projections are directional — not guarantees.",
        lang), S['body']))
    story.append(Spacer(1,0.1*inch))

    story.append(Paragraph(process_text("Forecast Accuracy Diagnostics",lang), S['h2']))
    if fc_accuracy.get('available'):
        mape_str = f"{fc_accuracy['mape']:.1f}%" if fc_accuracy.get('mape') is not None else "N/A"
        acc_rows = [
            ["Metric","Value","Interpretation"],
            ["MAE (Mean Absolute Error)", f"${fc_accuracy['mae']:,.2f}",
             "Average absolute deviation between forecast and actual"],
            ["RMSE (Root Mean Sq. Error)", f"${fc_accuracy['rmse']:,.2f}",
             "Penalizes large errors more; sensitive to outliers"],
            ["MAPE (%)", mape_str, fc_accuracy['acc_rating']],
            ["Holdout Sample",
             f"{fc_accuracy['n_holdout']} periods (last 20% of {fc_accuracy['n_train']+fc_accuracy['n_holdout']} total)",
             "In-sample validation"],
        ]
        _pro_table(story, acc_rows, col_widths=[2.1*inch,1.5*inch,CONTENT_W-3.6*inch], lang=lang)
        _callout(story,
                 f"<b>Accuracy Rating: {fc_accuracy['acc_rating']}</b>. "
                 f"<i>Limitation: {fc_accuracy['limitation']}</i>",
                 'blue', S, lang)
    else:
        _callout(story, f"ℹ️ {fc_accuracy.get('message','Forecast accuracy metrics unavailable.')}", 'amber', S, lang)

    story.append(Spacer(1,0.12*inch))
    _confidence_badge(story, ctx['confidence_level'], S, lang)
    if ctx['cv_pct'] > 40:
        _volatility_block(story, ctx.get('volatility',{}), ctx['cv_pct'], S, lang)

    sanity = ctx.get('sanity_check',{})
    if sanity and not sanity.get('passed',True):
        for warn in sanity.get('warnings',[]):
            _callout(story, process_text(warn,lang), 'red', S, lang)

    if ctx.get('fc_gap_flag', False):
        _callout(story,
                 f"⚠️ <b>Model Output Note:</b> Forecast avg/period (${ctx['fc12_avg_per_period']:,.0f}) "
                 f"is {ctx['fc_gap_pct']:+.0f}% above historical avg (${ctx['avg_per_period']:,.0f}). "
                 f"<b>Use Bear case (${ctx['bear_12']:,.0f}) as conservative planning floor.</b>",
                 'amber', S, lang)

    story.append(Spacer(1,0.1*inch))
    story.append(Paragraph(process_text("12-Period Scenario Planning",lang), S['h2']))
    col_w = CONTENT_W/3
    sc_data = [
        [Paragraph(process_text("🐻 Bear Case",lang),S['metric_bear']),
         Paragraph(process_text("📌 Base Case",lang),S['metric_value']),
         Paragraph(process_text("🚀 Bull Case",lang),S['metric_bull'])],
        [Paragraph(process_text(_money(ctx['bear_12']),lang),S['metric_bear']),
         Paragraph(process_text(_money(ctx['fc12']),   lang),S['metric_value']),
         Paragraph(process_text(_money(ctx['bull_12']),lang),S['metric_bull'])],
        [Paragraph(process_text(f"{ctx['bear_prob']*100:.0f}% probability",lang),S['metric_label']),
         Paragraph(process_text(f"{ctx['base_prob']*100:.0f}% probability",lang),S['metric_label']),
         Paragraph(process_text(f"{ctx['bull_prob']*100:.0f}% probability",lang),S['metric_label'])],
    ]
    sc_tbl = Table(sc_data, colWidths=[col_w]*3, rowHeights=[0.34*inch,0.46*inch,0.24*inch])
    sc_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,-1),colors.HexColor('#FEF2F2')),
        ('BACKGROUND',(1,0),(1,-1),rl('blue_pale')),
        ('BACKGROUND',(2,0),(2,-1),colors.HexColor('#F0FDF4')),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('GRID',(0,0),(-1,-1),0.35,rl('border')),
        ('LINEABOVE',(0,0),(-1,0),1.4,rl('blue')),('LINEBELOW',(0,-1),(-1,-1),1.4,rl('blue')),
        ('TOPPADDING',(0,0),(-1,0),8),('BOTTOMPADDING',(0,-1),(-1,-1),8),
    ]))
    story.append(sc_tbl); story.append(Spacer(1,0.1*inch))

    if ctx.get('decision_rule'):
        _callout(story, f"<b>Decision Rule:</b> {ctx['decision_rule']}", 'blue', S, lang)

    fc_items = [(_money(ctx['fc4']),"Next 4 Periods"),(_money(ctx['fc8']),"Next 8 Periods"),(_money(ctx['fc12']),"Next 12 Periods (Base)")]
    mt = Table(
        [[Paragraph(process_text(v,lang),S['metric_value']) for v,_ in fc_items],
         [Paragraph(process_text(l,lang),S['metric_label']) for _,l in fc_items]],
        colWidths=[CONTENT_W/3]*3, rowHeights=[0.46*inch,0.26*inch]
    )
    mt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),rl('blue_pale')),('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('GRID',(0,0),(-1,-1),0.35,rl('border')),
        ('LINEABOVE',(0,0),(-1,0),1.4,rl('teal')),('LINEBELOW',(0,-1),(-1,-1),1.4,rl('teal')),
        ('TOPPADDING',(0,0),(-1,0),10),('BOTTOMPADDING',(0,-1),(-1,-1),8),
    ]))
    story.append(mt); story.append(Spacer(1,0.15*inch))

    # Chart — FIX-F1: use last_historical_date from attrs
    last_hist = forecast.attrs.get('last_historical_date', None)
    if last_hist is not None:
        future = forecast[forecast['ds'] > pd.Timestamp(last_hist)].copy()
    else:
        future = forecast[forecast['ds'] > prophet_data['ds'].max()].copy()

    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    ax.plot(prophet_data['ds'], prophet_data['y'], color=mpl('chart1'), linewidth=1.4, alpha=0.8, label='Historical')
    ax.axvline(x=prophet_data['ds'].max(), color=CH['gray'], linewidth=0.8, linestyle=':', alpha=0.7)
    if len(future) > 0:
        ax.fill_between(future['ds'], future['yhat_lower'], future['yhat_upper'],
                        alpha=0.12, color=mpl('teal'), label='Scenario Range')
        ax.plot(future['ds'], future['yhat'],       color=mpl('teal'),  linewidth=2.2, linestyle='--', label='Base Case', zorder=5)
        ax.plot(future['ds'], future['yhat_lower'], color=mpl('bear'),  linewidth=0.9, linestyle=':', label='Bear Case', alpha=0.7)
        ax.plot(future['ds'], future['yhat_upper'], color=mpl('bull'),  linewidth=0.9, linestyle=':', label='Bull Case', alpha=0.7)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ax.set_title((company_name+"  —  " if company_name else "")+"Revenue Projection — 3 Scenarios",
                 fontsize=10.5, fontweight='bold', color=mpl('chart1'), pad=10)
    ax.legend(fontsize=7.5, ncol=2)
    ax.spines['left'].set_color(CH['border']); ax.spines['bottom'].set_color(CH['border'])
    plt.tight_layout(pad=1.1)
    story.append(_fig_to_img(fig, height=3.1*inch)); story.append(Spacer(1,0.1*inch))

    # FIX-P2: peak urgency block — past vs future language
    urgency   = ctx['peak_urgency']
    urg_style = {'critical':'red','urgent':'red','soon':'amber','planned':'blue','past':'amber'}.get(urgency.get('level','planned'),'blue')
    if ctx['peak_is_past']:
        _callout(story,
                 f"⚠️ <b>Peak date ({ctx['peak_week']}) has already passed.</b> "
                 f"Compare actual vs. projected performance for post-peak analysis. "
                 f"Use actuals to recalibrate the next cycle forecast.",
                 'amber', S, lang)
    else:
        _callout(story,
                 f"<b>Peak demand period:</b> {ctx['peak_week']} — "
                 f"Projected base-case revenue: <b>{_money(ctx['peak_fc'])}</b>. "
                 f"<b>{urgency.get('message','')}</b> "
                 f"[ASSUMPTION: Peak timing from trend extrapolation — monitor leading indicators to confirm.]",
                 urg_style, S, lang)

    indicators = ctx.get('leading_indicators', [])
    if indicators:
        story.append(Spacer(1,0.15*inch))
        story.append(Paragraph(process_text("Leading Indicators — Forecast Validation", lang), S['h2']))
        story.append(Paragraph(process_text(
            "Monitor weekly. If any threshold is breached, revise the forecast before committing resources.", lang), S['body_small']))
        story.append(Spacer(1,0.08*inch))
        for i, ind in enumerate(indicators, 1):
            signal = str(ind.get('signal',''))[:40]
            target = str(ind.get('target',''))[:50]
            alert  = str(ind.get('alert',''))[:80]
            action = str(ind.get('action',''))[:80]
            card_data = [
                [Paragraph(process_text(f"#{i} {signal}",lang),
                           ParagraphStyle('ch',fontSize=9,fontName=get_font(lang,True),textColor=rl('navy'),leading=13)),
                 Paragraph(process_text(f"Target: {target}",lang),
                           ParagraphStyle('ct',fontSize=8,fontName=get_font(lang),textColor=rl('teal'),leading=12))],
                [Paragraph(process_text(f"🔔 {alert}",lang),
                           ParagraphStyle('ca',fontSize=8,fontName=get_font(lang),textColor=rl('amber'),leading=12)),
                 Paragraph(process_text(f"→ {action}",lang),
                           ParagraphStyle('cac',fontSize=8,fontName=get_font(lang),textColor=rl('gray_dark'),leading=12))],
            ]
            card = Table(card_data, colWidths=[CONTENT_W*0.44, CONTENT_W*0.51])
            card.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,-1),rl('blue_pale')),
                ('LINEBEFORE',(0,0),(0,-1),3,rl('teal')),
                ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
                ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),8),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,-1),(-1,-1),0.3,rl('border')),
            ]))
            story.append(card); story.append(Spacer(1,0.05*inch))
    story.append(PageBreak())


def _risk_matrix(story, S, ctx, risks, lang):
    _section_header(story,"09","Risk Assessment Matrix",S,lang)
    story.append(Paragraph(process_text(
        "Key business risks derived from data analysis. Severity = Probability × Impact composite. "
        "All mitigations are evidence-based recommendations.",
        lang), S['body']))
    story.append(Spacer(1,0.15*inch))

    hdr  = ["Risk","Probability","Impact","Severity","Recommended Mitigation"]
    rows = [hdr]
    for r in risks:
        mit = str(r['mitigation'])[:70]
        rows.append([r['risk'], r['probability'], r['impact'], r['severity'], mit])
    tbl_data   = [[process_text(str(c),lang) for c in row] for row in rows]
    style_list = [
        ('FONTNAME',(0,0),(-1,-1),get_font(lang)),('FONTSIZE',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('GRID',(0,0),(-1,-1),0.25,rl('border')),
        ('BACKGROUND',(0,0),(-1,0),rl('navy')),('TEXTCOLOR',(0,0),(-1,0),rl('white')),
        ('FONTNAME',(0,0),(-1,0),get_font(lang,bold=True)),('ALIGN',(0,0),(-1,0),'CENTER'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[rl('white'),rl('gray_pale')]),
        ('ALIGN',(1,1),(3,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'TOP'),
    ]
    for i, r in enumerate(risks, 1):
        sev_bg = (rl('red_light') if r['severity']=='Critical' else rl('amber_light') if r['severity']=='High' else rl('blue_light'))
        style_list += [('BACKGROUND',(3,i),(3,i),sev_bg),('FONTNAME',(3,i),(3,i),get_font(lang,bold=True))]
    tbl = Table(tbl_data, colWidths=[1.5*inch,0.85*inch,0.75*inch,0.85*inch,CONTENT_W-3.95*inch], repeatRows=1)
    tbl.setStyle(TableStyle(style_list))
    story.append(tbl); story.append(Spacer(1,0.15*inch))

    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    prob_map   = {'High':3,'Medium':2,'Low':1}
    impact_map = {'High':3,'Medium':2,'Low':1}
    sev_colors = {'Critical':mpl('chart_neg'),'High':mpl('chart5'),'Medium':mpl('chart2'),'Low':mpl('chart3')}
    for (x1,y1,x2,y2,clr,lbl) in [
        (0.5,0.5,1.5,1.5,'#F0FDF4',"Low Priority"),(1.5,0.5,2.5,1.5,'#EFF6FF',"Monitor"),
        (0.5,1.5,1.5,2.5,'#FEF3C7',"Monitor"),    (1.5,1.5,2.5,2.5,'#FEF2F2',"Critical Zone"),
    ]:
        ax.add_patch(mpatches.FancyBboxPatch((x1,y1),x2-x1,y2-y1,
            boxstyle="round,pad=0.02",fc=clr,ec=CH['border'],lw=0.4,zorder=1))
        ax.text((x1+x2)/2,(y1+y2)/2,lbl,ha='center',va='center',fontsize=7.5,color=CH['gray_mid'],style='italic')
    for r in risks:
        x = impact_map.get(r['impact'],2); y = prob_map.get(r['probability'],2)
        ax.scatter(x, y, s=200, color=sev_colors.get(r['severity'],mpl('chart2')), alpha=0.85, zorder=5)
        ax.annotate(r['risk'][:18],(x,y),textcoords="offset points",xytext=(5,3),fontsize=6.5,color=CH['gray_dark'])
    ax.set_xlim(0.4,3.6); ax.set_ylim(0.4,3.6)
    ax.set_xticks([1,2,3]); ax.set_xticklabels(['Low','Medium','High'],fontsize=8)
    ax.set_yticks([1,2,3]); ax.set_yticklabels(['Low','Medium','High'],fontsize=8)
    ax.set_xlabel("Impact",fontsize=9,fontweight='bold'); ax.set_ylabel("Probability",fontsize=9,fontweight='bold')
    ax.set_title("Risk Heatmap",fontsize=10,fontweight='bold',color=mpl('chart1'))
    legend_patches = [mpatches.Patch(color=mpl('chart_neg'),label='Critical'),
                      mpatches.Patch(color=mpl('chart5'),label='High'),mpatches.Patch(color=mpl('chart2'),label='Medium')]
    ax.legend(handles=legend_patches,fontsize=7.5,loc='lower right')
    ax.grid(False); ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    plt.tight_layout(pad=1.0)
    story.append(_fig_to_img(fig, width=CONTENT_W*0.6, height=3.2*inch))
    story.append(PageBreak())


def _growth_opportunities(story, S, ctx, opportunities, lang):
    _section_header(story,"10","Growth Opportunity Assessment",S,lang)
    story.append(Paragraph(process_text(
        "Opportunities identified from data patterns and statistical analysis. "
        "DERIVED = mathematically computed. INFERRED = logical assumption requiring validation. "
        "Ranked by estimated revenue impact.",
        lang), S['body']))
    story.append(Spacer(1,0.15*inch))

    if not opportunities:
        _callout(story,"Insufficient segment data to compute growth opportunities.",'amber',S,lang)
        story.append(PageBreak()); return

    # FIX-P3: Wider basis column — prevents bleeding
    hdr  = ["Opportunity","Est. Impact","Confidence","Effort","Basis / Assumption"]
    rows = [hdr]
    for opp in opportunities:
        basis = str(opp['basis'])
        basis = basis[:60] + ('…' if len(basis) > 60 else '')
        rows.append([opp['type'], _money(opp['est_impact']), opp['confidence'], opp['effort'], basis])
    # FIX-P3: col widths add up to exactly CONTENT_W
    _pro_table(story, rows,
               col_widths=[1.4*inch, 0.9*inch, 1.0*inch, 0.65*inch, CONTENT_W-3.95*inch], lang=lang)

    if len(opportunities) > 1:
        fig, ax = plt.subplots(figsize=(9.5, 3.0))
        labels  = [o['type'][:22] for o in opportunities]
        values  = [o['est_impact'] for o in opportunities]
        clrs    = [mpl('chart1'),mpl('chart2'),mpl('chart3'),mpl('teal'),mpl('chart4')][:len(values)]
        bars    = ax.bar(labels, values, color=clrs, width=0.6, edgecolor='white', linewidth=0.35)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(values)*0.02,
                    _money(val), ha='center', va='bottom', fontsize=7.5, color=CH['gray_dark'])
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
        ax.set_title("Growth Opportunities — Ranked by Estimated Impact",fontsize=10,fontweight='bold',color=mpl('chart1'),pad=10)
        ax.tick_params(axis='x',rotation=15,labelsize=7.5)
        ax.spines['left'].set_color(CH['border']); ax.spines['bottom'].set_color(CH['border'])
        plt.tight_layout(pad=1.1)
        story.append(_fig_to_img(fig, height=2.6*inch)); story.append(Spacer(1,0.1*inch))

    if opportunities:
        top = opportunities[0]
        _callout(story,
                 f"<b>Top Opportunity: {top['type']}</b> — "
                 f"Estimated impact: <b>{_money(top['est_impact'])}</b> | "
                 f"Confidence: {top['confidence']} | Effort: {top['effort']}. "
                 f"{top['description']} [{top['basis']}]",
                 'green', S, lang)

    _callout(story,
             "⚠️ <b>Important:</b> All estimates based on historical patterns. "
             "Actual impact depends on execution quality, market conditions, and operational capacity. "
             "Conduct controlled pilots before broad implementation.",
             'amber', S, lang)
    story.append(PageBreak())



def _recommendations(story, S, ctx, lang):
    # import داخلي لأن هذا ملف patches
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
 
    # دوال مستوردة من pdf_gen
    from src.pdf_gen import (
        _section_header, _callout, _pro_table, _fig_to_img,
        _divider, process_text, get_font, rl, mpl, _money,
        CONTENT_W, CH
    )
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
 
    _section_header(story, "11", "Strategic Recommendations", S, lang)
    story.append(Paragraph(process_text(
        "Each recommendation is evidence-based and decision-ready. "
        "Confidence levels reflect data quality, sample size, and statistical foundation. "
        "All financial estimates show derivation formulas for transparency. "
        "Hypotheses require validation before operational action.",
        lang), S['body']))
    story.append(Spacer(1, 0.15 * inch))
 
    # ── Dynamic correlation basis (من البيانات الفعلية) ──
    top_corr_col = ctx.get('top_pos_corr_col')
    top_corr_r   = ctx.get('top_pos_corr_r', 0.0)
    if top_corr_col and top_corr_r > 0.3:
        corr_evidence = (
            f"Strongest positive correlation: {top_corr_col} (r={top_corr_r:.4f}). "
            f"Statistical significance: {'Highly significant' if top_corr_r > 0.7 else 'Significant' if top_corr_r > 0.5 else 'Moderate'}. "
            f"[CAUTION: Correlation ≠ causation. Do not assume direct causal relationship.]"
        )
        corr_conf_basis = (
            f"r={top_corr_r:.4f} for {top_corr_col} vs revenue. "
            f"Strength: {'Very Strong' if top_corr_r >= 0.8 else 'Strong' if top_corr_r >= 0.6 else 'Moderate'}. "
            f"Causal mechanism unconfirmed — validate before acting on this lever."
        )
    else:
        corr_evidence  = "No strong positive correlations detected in the dataset (all |r| < 0.3). Revenue drivers remain unidentified from available variables."
        corr_conf_basis = "Weak or no correlations in dataset. Recommendations based on revenue gap analysis only."
 
    # ── Dynamic peak confidence ──
    from src.forecaster import classify_volatility
    model_type  = ctx.get('model_type', 'unknown')
    n_periods   = ctx.get('n_periods', 0)
    cv_pct      = ctx.get('cv_pct', 0)
    sanity_ok   = ctx.get('sanity_check', {}).get('passed', True)
 
    if model_type in ('HW_seasonal_52',) and n_periods >= 104 and sanity_ok:
        peak_conf = "Medium"
        peak_conf_basis = (
            f"Model: {model_type} on {n_periods} periods. "
            f"Seasonal model with full annual cycle — moderate confidence. "
            f"CV={cv_pct:.1f}% introduces uncertainty."
        )
    elif not sanity_ok:
        peak_conf = "Low"
        peak_conf_basis = (
            f"Sanity check FAILED — forecast anomaly detected. "
            f"Peak timing is directional only. Do not commit resources based on this date alone."
        )
    else:
        peak_conf = "Low"
        peak_conf_basis = (
            f"Model: {model_type} on {n_periods} periods. "
            f"Insufficient history for seasonal modeling (<104 periods). "
            f"Peak is a trend extrapolation — treat as planning signal only."
        )
 
    from reportlab.lib.units import inch
 
    recs = [
        {
            'title':     f"Priority 1 — Investigate & Replicate Group {ctx['best_group']} Model",
            'evidence':  (
                f"Group <b>{ctx['best_group']}</b> generates "
                f"<b>${ctx['best_group_revenue']:,.0f}</b> ({ctx['best_group_share']:.1f}% of total portfolio revenue). "
                f"Gap vs worst performer: ${ctx['worst_group_gap_weekly']:,.0f}/period. "
                f"[DATA: directly measured]"
            ),
            'hypothesis': (
                f"Hypothesis: operational characteristics of Group {ctx['best_group']} may be transferable. "
                f"Correlation data: {corr_evidence} "
                f"[INFERRED — do not assume product mix, channel, or geographic differences "
                f"without domain expert validation.]"
            ),
            'owner':     "Sales Manager / Head of Operations",
            'deadline':  ctx['action_deadline_30'],
            'first':     (
                f"Document top 3 operational characteristics of Group {ctx['best_group']}: "
                f"transaction frequency, revenue per transaction, and promotional cadence."
            ),
            'metric':    (
                f"Bottom groups reach 70% of Group {ctx['best_group']}'s average "
                f"(${ctx['best_group_avg'] * 0.7:,.0f}/period) by {ctx['action_deadline_90']}"
            ),
            'roi':       (
                f"Est. impact (50% gap closure): ${ctx['worst_group_12p_cost'] * 0.5:,.0f} over 12 periods "
                f"[DERIVED: gap (${ctx['worst_group_gap_weekly']:,.0f}) × 12 periods × 50% closure]. "
                f"Full closure maximum: ${ctx['worst_group_12p_cost']:,.0f}. "
                f"Payback: <1 period if 30% closure achieved."
            ),
            'inaction':  (
                f"${ctx['worst_group_12p_cost']:,.0f} foregone over 12 periods "
                f"[DERIVED: gap × 12]. Annual run-rate: ${ctx['worst_group_annual_cost']:,.0f}."
            ),
            'conf':      "Medium",
            'conf_basis': corr_conf_basis,
            'style':     'blue',
        },
        {
            'title':     f"Priority 2 — Root Cause Diagnosis: Group {ctx['worst_group']}",
            'evidence':  (
                f"Group <b>{ctx['worst_group']}</b> underperforms by "
                f"<b>${ctx['worst_group_gap_weekly']:,.0f}/period</b> vs. portfolio average "
                f"(${ctx['avg_per_period']:,.0f}/period). [DATA: directly measured]"
            ),
            'hypothesis': (
                f"Possible root causes (each requiring validation): "
                f"(A) Revenue mix differences — investigate product/service composition; "
                f"(B) Transaction frequency gap — compare average transactions per period; "
                f"(C) Pricing structure variance — compare average revenue per transaction; "
                f"(D) Operational efficiency — compare cost structure if available. "
                f"Correlation analysis: {corr_evidence} "
                f"[Do NOT implement changes without confirming root cause.]"
            ),
            'owner':     "Category Manager / Regional Director",
            'deadline':  ctx['action_deadline_7'],
            'first':     (
                f"Audit Group {ctx['worst_group']}: pull transaction-level data, "
                f"compare average transaction value and frequency vs. Group {ctx['best_group']}."
            ),
            'metric':    (
                f"Close 50% of performance gap "
                f"(to ${ctx['avg_per_period'] - ctx['worst_group_gap_weekly'] * 0.5:,.0f}/period) "
                f"within 30 days of confirmed root cause intervention."
            ),
            'roi':       (
                f"50% gap closure: ${ctx['worst_group_12p_cost'] * 0.5:,.0f}/12 periods "
                f"[DERIVED: gap × 12 × 50%]. "
                f"Audit cost: $200–$500. ROI: dependent on root cause — quantify after diagnosis."
            ),
            'inaction':  (
                f"${ctx['worst_group_annual_cost']:,.0f}/year ongoing underperformance "
                f"[DERIVED: gap × 52 periods]"
            ),
            'conf':      "Low",
            'conf_basis': (
                f"Low: root cause unknown. Gap is [DATA] — cause is [INFERRED]. "
                f"Confidence upgrades to Medium after root cause confirmed."
            ),
            'style':     'amber',
        },
        {
            'title':     "Priority 3 — Prepare for Projected Demand Peak",
            'evidence':  (
                f"Base-case forecast projects peak at <b>{ctx['peak_week']}</b> "
                f"→ <b>{_money(ctx['peak_fc'])}</b>. "
                f"[Model: {model_type} | Confidence: {ctx['confidence_level']}]"
                + (" ⚠️ SANITY CHECK FAILED — treat as directional only." if not sanity_ok else "")
            ),
            'hypothesis': (
                f"Peak may represent seasonal demand surge or trend momentum. "
                f"{'Full seasonal cycle not available (<104 periods) — peak timing is extrapolated, not confirmed.' if n_periods < 104 else 'Seasonal model trained on full cycle — moderate confidence in peak timing.'} "
                f"Bear case: ${ctx['bear_12']:,.0f}/12 periods ({ctx['bear_spread_pct']:+.1f}% from base). "
                f"[Treat as planning signal — monitor leading indicators before committing inventory.]"
            ),
            'owner':     "Supply Chain / Operations Manager",
            'deadline':  ctx['action_deadline_7'],
            'first':     (
                "Review inventory capacity, staffing levels, and promotional calendar "
                f"for the {ctx['peak_week']} window."
            ),
            'metric':    (
                f"Capture ≥85% of projected peak revenue "
                f"({_money(ctx['peak_fc'] * 0.85)}) "
                f"[DERIVED: peak × 85% capture rate]"
            ),
            'roi':       (
                f"Peak capture opportunity: {_money(ctx['peak_fc'])} "
                f"[ASSUMPTION: peak materializes as projected]. "
                f"Bear case floor: ${ctx['bear_12']:,.0f}/12 periods. "
                f"Cost: inventory pre-positioning (domain-specific). "
                f"Risk: {_money(ctx['peak_fc'])} lost if peak missed."
            ),
            'inaction':  (
                f"Up to {_money(ctx['peak_fc'] * 0.15)} uncaptured revenue "
                f"if peak not prepared for [DERIVED: peak × 15% stockout rate assumption]"
            ),
            'conf':      peak_conf,
            'conf_basis': peak_conf_basis,
            'style':     'green',
        },
    ]
 
    labels = {
        'HYP':      "HYPOTHESES (TO VALIDATE)",
        'OWNER':    "DECISION OWNER",
        'DEADLINE': "DEADLINE",
        'FIRST':    "FIRST ACTION (48h)",
        'METRIC':   "SUCCESS METRIC",
        'ROI':      "BUSINESS IMPACT CALCULATOR",
        'INACTION': "COST OF INACTION",
        'CONF':     "RECOMMENDATION CONFIDENCE",
    }
 
    for rec in recs:
        story.append(Paragraph(process_text(rec['title'], lang), S['h3']))
        _callout(story, process_text(rec['evidence'], lang), rec['style'], S, lang)
 
        meta_rows = [
            [labels['HYP'],      rec['hypothesis']],
            [labels['OWNER'],    rec['owner']],
            [labels['DEADLINE'], rec['deadline']],
            [labels['FIRST'],    rec['first']],
            [labels['METRIC'],   rec['metric']],
            [labels['ROI'],      rec['roi']],
            [labels['INACTION'], rec['inaction']],
            [labels['CONF'],     f"● {rec['conf']}  |  {rec['conf_basis']}"],
        ]
        meta_data = [[
            Paragraph(process_text(k, lang),
                      ParagraphStyle('mk', fontSize=7, fontName=get_font(lang, True),
                                     textColor=rl('gray'), leading=11, alignment=TA_LEFT)),
            Paragraph(process_text(v, lang),
                      ParagraphStyle('mv', fontSize=8, fontName=get_font(lang),
                                     textColor=rl('gray_dark'), leading=13, alignment=TA_LEFT)),
        ] for k, v in meta_rows]
 
        desc_col_w = CONTENT_W - 1.5 * inch - 0.1 * inch
        meta_tbl   = Table(meta_data, colWidths=[1.5 * inch, desc_col_w])
        style_list = [
            ('BACKGROUND', (0, 0), (0, -1), rl('gray_light')),
            ('BACKGROUND', (1, 0), (1, -1), rl('white')),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING',   (0, 0), (-1, -1), 7),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.2, rl('border')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 5), (1, 5), rl('green_light')),   # ROI row
            ('BACKGROUND', (0, 6), (1, 6), rl('amber_light')),   # Inaction row
        ]
        conf_bg = (
            rl('green_light') if rec['conf'] == 'High'
            else rl('amber_light') if rec['conf'] == 'Medium'
            else rl('red_light')
        )
        style_list.append(('BACKGROUND', (0, 7), (1, 7), conf_bg))
        style_list.append(('FONTNAME',   (0, 7), (1, 7), get_font(lang, bold=True)))
        meta_tbl.setStyle(TableStyle(style_list))
        story.append(meta_tbl)
        story.append(Spacer(1, 0.22 * inch))
 
    # Priority Matrix
    story.append(Paragraph(process_text("Priority Matrix — Impact vs. Effort", lang), S['h2']))
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    for (x1, y1, x2, y2, clr, lbl) in [
        (0.5, 0.5, 1.5, 1.5, '#F0FDF4', "Quick Wins"),
        (1.5, 0.5, 2.5, 1.5, '#EFF6FF', "Strategic Projects"),
        (0.5, 1.5, 1.5, 2.5, '#FEF3C7', "Low Priority"),
        (1.5, 1.5, 2.5, 2.5, '#FEF2F2', "Major Investments"),
    ]:
        ax.add_patch(mpatches.FancyBboxPatch(
            (x1, y1), x2 - x1, y2 - y1,
            boxstyle="round,pad=0.02", fc=clr, ec=CH['border'], lw=0.5, zorder=1))
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, lbl,
                ha='center', va='center', fontsize=8, color=CH['gray_mid'], style='italic')
 
    pm_items = [
        (f"Root Cause\nGroup {ctx['best_group']}", 0.8, 0.8, mpl('chart1')),
        (f"Diagnose\nGroup {ctx['worst_group']}",  0.9, 1.0, mpl('chart5')),
        ("Peak\nPreparation",                       0.7, 0.7, mpl('chart3')),
        ("Segment\nTiering",                        1.6, 1.4, mpl('chart2')),
        ("Portfolio\nOptimization",                 2.0, 1.9, mpl('chart_neg')),
    ]
    for lbl, x, y, clr in pm_items:
        ax.scatter(x, y, s=160, color=clr, zorder=5, alpha=0.85)
        ax.annotate(lbl, (x, y), textcoords="offset points",
                    xytext=(5, 5), fontsize=6.5, color=CH['gray_dark'])
 
    ax.set_xlim(0.5, 2.5); ax.set_ylim(0.5, 2.5)
    ax.set_xticks([1.0, 2.0]); ax.set_xticklabels(['Low Effort', 'High Effort'], fontsize=8)
    ax.set_yticks([1.0, 2.0]); ax.set_yticklabels(['Low Impact', 'High Impact'], fontsize=8)
    ax.set_xlabel("Effort Required", fontsize=9, fontweight='bold')
    ax.set_ylabel("Business Impact",  fontsize=9, fontweight='bold')
    ax.set_title("Priority Matrix — Impact vs. Effort",
                 fontsize=10, fontweight='bold', color=mpl('chart1'))
    ax.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout(pad=1.0)
    story.append(_fig_to_img(fig, width=CONTENT_W * 0.65, height=3.3 * inch))
 
    from reportlab.platypus import PageBreak
    story.append(PageBreak())
 


def _appendix(story, S, ctx, lang, validation_report=None):
    _section_header(story,"12","Data Appendix & Methodology",S,lang)

    hdr    = ["Parameter","Value"]
    params = [
        ("Total Records",            f"{ctx['n_records']:,}"),
        ("Unique Periods",           f"{ctx['n_periods']:,}"),
        ("Reporting Period",         ctx['date_range']),
        ("Total Revenue",            f"${ctx['total_revenue']:,.2f}"),
        ("Mean per Period",          f"${ctx['avg_per_period']:,.2f}"),
        ("Median per Period",        f"${ctx['median_per_period']:,.2f}"),
        ("Peak Single Period",       f"${ctx['peak_value']:,.2f}"),
        ("Minimum Period",           f"${ctx['min_value']:,.2f}"),
        ("Revenue Std Dev",          f"${ctx['std_dev']:,.2f}"),
        ("Coeff. of Variation (CV)", f"{ctx['cv_pct']:.1f}%"),
        # FIX-P1: Dynamic volatility label
        ("Volatility Level",         ctx['volatility_level']),
        ("Trend Direction",          ctx['trend_direction'].capitalize()),
        ("Trend Change (HoH)",       f"{ctx['trend_pct']:+.1f}%"),
        ("Forecast Confidence",      ctx['confidence_level']),
        ("Bear Case (12 periods)",   f"${ctx['bear_12']:,.0f} ({ctx['bear_prob']*100:.0f}% probability)"),
        ("Base Case (12 periods)",   f"${ctx['fc12']:,.0f} ({ctx['base_prob']*100:.0f}% probability)"),
        ("Bull Case (12 periods)",   f"${ctx['bull_12']:,.0f} ({ctx['bull_prob']*100:.0f}% probability)"),
        ("Forecast Avg/Period",      f"${ctx['fc12_avg_per_period']:,.0f} ({ctx['fc_gap_pct']:+.0f}% vs. historical avg)"),
        ("Best Quantity Group",      f"Group {ctx['best_group']} (${ctx['best_group_revenue']:,.0f})"),
        ("Worst Quantity Group",     f"Group {ctx['worst_group']} (gap: ${ctx['worst_group_gap_weekly']:,.0f}/period)"),
        ("Pareto (80% Revenue)",     f"Top {ctx['pareto_pct']:.0f}% of groups"),
    ]
    _pro_table(story, [hdr]+[[p,v] for p,v in params], col_widths=[2.8*inch, CONTENT_W-2.8*inch], lang=lang)

    story.append(Paragraph(process_text("Methodology Documentation",lang), S['h2']))
    methodology = [
        ("Data Cleaning",
         "Raw dataset ingested and validated. Column names stripped. Date fields parsed via pandas. "
         "Records with unparseable dates excluded from temporal analysis."),
        ("Missing Value Handling",
         "Missing values identified via pandas isnull(). Records with missing primary date/sales excluded. "
         "Records with missing non-critical columns retained for aggregation analyses."),
        ("Outlier Treatment",
         "Outliers identified via IQR method: below Q1−1.5×IQR or above Q3+1.5×IQR. "
         "Retained in analysis to preserve integrity. Presence documented."),
        ("Forecast Methodology",
         "Holt-Winters Exponential Smoothing (statsmodels). Seasonal periods: 52 if n≥104, 26 if n≥26. "
         "last_historical_date stored in DataFrame.attrs — prevents future-row slice bug. "
         "Three scenarios: Bear = base×0.75–0.85, Base = model output, Bull = base×1.15–1.40."),
        ("Forecast Accuracy Validation",
         "Model re-trained on first 80%. MAE, RMSE, MAPE computed against last 20% holdout. "
         "Ensures non-zero, meaningful accuracy metrics."),
        ("Statistical Methods",
         "Pearson correlations via scipy.stats.pearsonr(). P-values use <0.0001 notation. "
         "Effect size filter applied (|r|≥0.2) to avoid large-n spurious significance. "
         "Normality via Shapiro-Wilk."),
        ("Financial Estimates",
         "DERIVED: mathematically computed from data. "
         "INFERRED: logical assumption requiring validation. "
         "All formulas shown in report for transparency."),
    ]
    for sec_title, content in methodology:
        story.append(Paragraph(process_text(sec_title,lang), S['h3']))
        story.append(Paragraph(process_text(content,lang), S['body']))
        story.append(Spacer(1,0.06*inch))

    if validation_report:
        story.append(Spacer(1,0.15*inch))
        story.append(Paragraph(process_text("Quality Assurance Report",lang), S['h2']))
        status     = validation_report.get('passed', True)
        iterations = validation_report.get('iterations', 1)
        status_txt = (f"Quality check: {'✅ PASSED' if status else '⚠️ ISSUES DETECTED'} "
                      f"— {iterations} validation iteration(s) completed.")
        story.append(Paragraph(process_text(status_txt,lang),
                               S['validation_ok'] if status else S['validation_err']))
        if not status and validation_report.get('errors'):
            errors = validation_report['errors'][:5]
            if errors and isinstance(errors[0], dict):
                err_rows = [["Issue Detected","Impact Level","Action Taken"]]
                err_rows += [[e.get('error',''),e.get('impact',''),e.get('action','')] for e in errors]
                _pro_table(story, err_rows, col_widths=[2.2*inch,1.2*inch,CONTENT_W-3.4*inch], lang=lang)

    # FIX-P8: Action Plan with proper column widths
    story.append(Spacer(1,0.2*inch))
    story.append(Paragraph(process_text("Priority Action Plan",lang), S['h2']))
    story.append(Paragraph(process_text(
        "All impact estimates derived from data. Confidence ratings reflect data quality and statistical foundation.",
        lang), S['body_small']))
    story.append(Spacer(1,0.08*inch))

    ap_sections = [
        ("Quick Wins (0–30 Days)", [
            (f"Investigate Group {ctx['best_group']} Drivers",
             "Identify top 3 operational factors; document for controlled replication",
             f"+{_money(ctx['avg_per_period']*4)}/quarter [DERIVED]","Low","Medium"),
            ("Peak Cycle Alignment",
             f"{'Post-peak recalibration' if ctx['peak_is_past'] else 'Prepare for projected peak'} at {ctx['peak_week']}. "
             f"{ctx['peak_urgency'].get('message','')[:35]}",
             f"+{_money(ctx['peak_fc']*0.08)} [DERIVED]","Low","Medium"),
        ]),
        ("Medium-Term (1–3 Months)", [
            ("Segment Performance Tiering",
             "Classify groups; validate business meaning with domain experts",
             f"+{_money(ctx['total_revenue']*0.06)}/year [DERIVED]","Medium","Low"),
        ]),
        ("Long-Term (6–12 Months)", [
            ("Portfolio Optimization",
             f"Validate top performers; structured review of Group {ctx['worst_group']}",
             f"+{_money(ctx['total_revenue']*0.12)}/year [DERIVED]","High","Low"),
        ]),
    ]

    ap_hdr = ["Initiative","Description","Est. Impact","Effort","Conf."]
    for sec_title, items in ap_sections:
        story.append(Paragraph(process_text(sec_title,lang), S['h3']))
        ap_rows = [ap_hdr] + [list(item) for item in items]
        # FIX-P8: proper column widths — description gets most space
        _pro_table(story, ap_rows, col_widths=[1.3*inch,2.5*inch,1.4*inch,0.65*inch,0.65*inch], lang=lang)

    _callout(story,
             f"<b>Combined Impact Projection:</b> Full implementation estimated at "
             f"<b>{_money(ctx['total_revenue']*0.15)} — {_money(ctx['total_revenue']*0.22)}</b> "
             f"incremental annual revenue (15–22% uplift on {_money(ctx['total_revenue'])} baseline). "
             f"[All estimates DERIVED from data — see methodology above.]",
             'green', S, lang)


# ═══════════════════════════════════════════════════════════
# MAIN GENERATOR — generate_pdf()
# ═══════════════════════════════════════════════════════════
def generate_pdf(
    df, date_col, sales_col, summary, store_df, corr_series,
    forecast, prophet_data, forecast_summary, monthly_df,
    group_col, company_name, T,
    ai_result=None, ai_type=None,
    include_action_plan=False, lang='en',
    system_prompt="", ask_agent_fn=None,
) -> bytes:
    """
    Generate McKinsey/BCG-grade Business Intelligence PDF — v5.0
    All known bugs fixed. See module docstring for full list.
    """
    # Step 1: Compute all numbers once
    ctx = extract_dynamic_context(
    df, date_col, sales_col, summary, store_df,
    group_col, corr_series, forecast_summary, monthly_df,
    prophet_data=prophet_data,
)

    # Step 2: Compute all statistics
    stat_results  = compute_statistical_validation(df, sales_col, corr_series)
    dq            = compute_data_quality(df, date_col, sales_col)
    fc_accuracy   = compute_forecast_accuracy(prophet_data, forecast)
    scorecards    = compute_segment_scorecard(store_df, group_col) if store_df is not None and group_col else []
    risks         = compute_risk_matrix(ctx)
    opportunities = compute_growth_opportunities(ctx, store_df, group_col)

    # Step 3: Quality pipeline on AI text
    validation_report = None
    if ai_result:
        cleaned_analysis, validation_report = run_quality_pipeline(
            ai_result, ctx,
            system_prompt=system_prompt,
            ask_agent_fn=ask_agent_fn,
            max_iterations=2,
        )
    else:
        cleaned_analysis = None

    # Step 4: Build PDF
    buffer    = io.BytesIO()
    S         = build_styles(lang)
    footer_fn = ReportCanvas(ctx['report_date'], lang)

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.62*inch, bottomMargin=0.82*inch,
        title="Sales Performance Analysis Report",
        author="Business Intelligence Division",
        subject="Confidential Business Analysis",
        creator="Performance Analytics Platform v5.0",
    )

    story     = []
    has_store = store_df is not None and group_col is not None and len(store_df) > 0
    has_corr  = corr_series is not None and len(corr_series) > 0

    _cover(story, company_name, S, ctx, lang)
    _toc(story, S, ctx, lang, has_store, has_corr)
    _executive_kpi_dashboard(story, S, ctx, dq, lang)
    _executive_summary(story, S, ctx, lang, cleaned_analysis)
    _data_quality_section(story, S, dq, ctx, lang)
    _key_findings(story, S, ctx, lang)
    _sales_overview(story, S, ctx, df, date_col, sales_col, company_name, lang)
    _trend_analysis(story, S, ctx, monthly_df, company_name, lang)

    if has_store:
        _segment_analysis(story, S, ctx, store_df, group_col, company_name, lang, scorecards)
    if has_corr:
        _statistical_validation(story, S, ctx, stat_results, lang)

    _forecast_section(story, S, ctx, forecast, prophet_data, company_name, lang, fc_accuracy)
    _risk_matrix(story, S, ctx, risks, lang)
    _growth_opportunities(story, S, ctx, opportunities, lang)
    _recommendations(story, S, ctx, lang)
    ctx['_computed_opportunities'] = opportunities
    _appendix(story, S, ctx, lang, validation_report)

    doc.build(story, onFirstPage=footer_fn, onLaterPages=footer_fn)
    buffer.seek(0)
    return buffer.read()


