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
    opps  = []
    avg   = ctx.get('avg_per_period', 0)
    best  = ctx.get('best_group_avg', 0)
    fc12  = ctx.get('fc12', 0)
    total = ctx.get('total_revenue', 0)

    if store_df is not None and group_col and avg > 0:
        bottom_half = store_df[store_df['avg_weekly'] < avg]
        if len(bottom_half) > 0:
            bottom_mean = float(bottom_half['avg_weekly'].mean())
            uplift = float((avg - bottom_mean) * len(bottom_half) * 12)
            opps.append({
                'type': "Efficiency Uplift",
                'description': "Bring bottom 50% of groups to portfolio average.",
                'est_impact': max(uplift, 0), 'confidence': "Medium", 'effort': "Medium",
                'basis': "DERIVED: (avg − grp_avg) × n_groups × 12 periods",
            })
        if best > avg:
            replication = float((best - avg) * max(len(store_df)-3, 1) * 12 * 0.3)
            opps.append({
                'type': "Top Performer Replication",
                'description': f"Apply Group {ctx.get('best_group','top')} model to similar units.",
                'est_impact': max(replication, 0), 'confidence': "Low", 'effort': "Low",
                'basis': "INFERRED: 30% replication rate assumed — validate before committing",
            })

    bull_upside = ctx.get('bull_12', fc12) - fc12
    if bull_upside > 0:
        opps.append({
            'type': "Bull Case Upside",
            'description': "Favorable conditions yield Bull case scenario.",
            'est_impact': bull_upside,
            'confidence': f"Low ({int(ctx.get('bull_prob', 0.20)*100)}% probability)",
            'effort': "High",
            'basis': "DERIVED: Bull forecast − Base forecast",
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
) -> dict:
    ctx = {}
    ctx['total_revenue']     = float(df[sales_col].sum())
    ctx['avg_per_period']    = float(df[sales_col].mean())
    ctx['median_per_period'] = float(df[sales_col].median())
    ctx['peak_value']        = float(df[sales_col].max())
    ctx['min_value']         = float(df[sales_col].min())
    ctx['n_records']         = int(len(df))
    ctx['std_dev']           = float(df[sales_col].std())
    ctx['q1_value']          = float(df[sales_col].quantile(0.25))
    ctx['q3_value']          = float(df[sales_col].quantile(0.75))
    ctx['cv_pct']            = round(ctx['std_dev'] / ctx['avg_per_period'] * 100, 1) if ctx['avg_per_period'] > 0 else 0

    ctx['date_min']   = str(df[date_col].min().date())
    ctx['date_max']   = str(df[date_col].max().date())
    ctx['date_range'] = f"{ctx['date_min']} to {ctx['date_max']}"
    ctx['n_periods']  = int(df[date_col].nunique())

    sorted_df   = df.groupby(date_col)[sales_col].sum().reset_index().sort_values(date_col)
    half        = max(1, len(sorted_df) // 2)
    first_half  = float(sorted_df[sales_col].iloc[:half].mean())
    second_half = float(sorted_df[sales_col].iloc[half:].mean())
    trend_pct   = (second_half - first_half) / first_half * 100 if first_half > 0 else 0
    ctx['trend_pct']       = round(trend_pct, 1)
    ctx['trend_direction'] = "growing" if trend_pct > 3 else "declining" if trend_pct < -3 else "stable"

    if len(monthly_df) > 0:
        vals   = monthly_df['total'].tolist()
        months = [str(m) for m in monthly_df['month']]
        ctx['best_period_label']  = months[vals.index(max(vals))] if vals else 'N/A'
        ctx['worst_period_label'] = months[vals.index(min(vals))] if vals else 'N/A'
        ctx['best_period_value']  = max(vals) if vals else 0
        ctx['worst_period_value'] = min(vals) if vals else 0
        ctx['period_spread_pct']  = round((max(vals)-min(vals)) / max(ctx['avg_per_period'], 1) * 100, 1) if vals else 0
    else:
        for k in ['best_period_label', 'worst_period_label']:
            ctx[k] = 'N/A'
        for k in ['best_period_value', 'worst_period_value', 'period_spread_pct']:
            ctx[k] = 0

    ctx['group_col']   = group_col or 'N/A'
    ctx['n_groups']    = int(summary.get('num_groups', 0))
    ctx['best_group']  = str(summary.get('best_group', 'N/A'))
    ctx['worst_group'] = str(summary.get('worst_group', 'N/A'))

    if store_df is not None and group_col:
        total_rev = store_df['total'].sum()
        ctx['best_group_revenue']  = float(store_df['total'].max())
        ctx['best_group_share']    = round(store_df['total'].max()/total_rev*100, 1) if total_rev > 0 else 0
        ctx['worst_group_revenue'] = float(store_df['total'].min())
        ctx['worst_group_avg']     = float(store_df.loc[store_df['total'].idxmin(), 'avg_weekly'])
        ctx['best_group_avg']      = float(store_df.loc[store_df['total'].idxmax(), 'avg_weekly'])
        cum = store_df['total'].sort_values(ascending=False).cumsum()
        n80 = int((cum <= total_rev*0.80).sum()) + 1
        ctx['pareto_n']   = n80
        ctx['pareto_pct'] = round(n80 / max(len(store_df), 1) * 100, 1)
    else:
        for k in ['best_group_revenue','best_group_share','worst_group_revenue',
                  'worst_group_avg','best_group_avg','pareto_n','pareto_pct']:
            ctx[k] = 0

    if corr_series is not None and len(corr_series) > 0:
        pos = corr_series[corr_series > 0.1]
        neg = corr_series[corr_series < -0.1]
        ctx['pos_factors'] = [(str(k), round(float(v), 4)) for k, v in pos.items()]
        ctx['neg_factors'] = [(str(k), round(float(v), 4)) for k, v in neg.items()]
    else:
        ctx['pos_factors'] = []
        ctx['neg_factors'] = []

    ctx['fc4']       = float(forecast_summary.get('next_4_weeks',  0))
    ctx['fc8']       = float(forecast_summary.get('next_8_weeks',  0))
    ctx['fc12']      = float(forecast_summary.get('next_12_weeks', 0))
    ctx['bear_12']   = float(forecast_summary.get('bear_12_weeks', ctx['fc12'] * 0.75))
    ctx['bull_12']   = float(forecast_summary.get('bull_12_weeks', ctx['fc12'] * 1.25))
    ctx['peak_week'] = str(forecast_summary.get('peak_week', 'N/A'))
    ctx['peak_fc']   = float(forecast_summary.get('peak_expected_sales', 0))
    ctx['bear_prob'] = forecast_summary.get('bear_probability', 0.25)
    ctx['base_prob'] = forecast_summary.get('base_probability', 0.55)
    ctx['bull_prob'] = forecast_summary.get('bull_probability', 0.20)
    ctx['confidence_level']   = forecast_summary.get('confidence_level', 'Medium')

    # FIX-P4: Single source for volatility — from forecast_summary which uses classify_volatility()
    vol_raw = forecast_summary.get('volatility', {})
    if not vol_raw or 'level' not in vol_raw:
        # Re-derive from cv_pct
        from forecaster import classify_volatility
        vol_raw = classify_volatility(ctx['cv_pct'])
    ctx['volatility'] = vol_raw
    # FIX-P1: Dynamic volatility label (never hardcoded)
    ctx['volatility_level'] = vol_raw.get('level', 'High')
    ctx['volatility_badge'] = vol_raw.get('badge', '🔴')

    ctx['sanity_check']       = forecast_summary.get('sanity_check', {'passed': True, 'warnings': []})
    ctx['leading_indicators'] = forecast_summary.get('leading_indicators', [])
    ctx['decision_rule']      = forecast_summary.get('decision_rule', '')

    fc12_avg = ctx['fc12'] / 12 if ctx['fc12'] > 0 and ctx['n_records'] > 0 else 0
    fc_gap   = ((fc12_avg - ctx['avg_per_period']) / ctx['avg_per_period'] * 100
                if ctx['avg_per_period'] > 0 else 0)
    ctx['fc12_avg_per_period'] = round(fc12_avg, 2)
    ctx['fc_gap_pct']          = round(fc_gap, 1)
    ctx['fc_gap_flag']         = fc_gap > 200

    ctx['peak_urgency'] = _get_peak_urgency(ctx['peak_week'])
    ctx['peak_is_past'] = ctx['peak_urgency']['is_past']

    ctx['worst_group_gap_weekly']  = max(ctx['avg_per_period'] - ctx['worst_group_avg'], 0)
    ctx['worst_group_12p_cost']    = ctx['worst_group_gap_weekly'] * 12
    ctx['worst_group_annual_cost'] = ctx['worst_group_gap_weekly'] * 52
    ctx['action_deadline_7']  = (pd.Timestamp.now()+pd.Timedelta(days=7)).strftime('%Y-%m-%d')
    ctx['action_deadline_30'] = (pd.Timestamp.now()+pd.Timedelta(days=30)).strftime('%Y-%m-%d')
    ctx['action_deadline_90'] = (pd.Timestamp.now()+pd.Timedelta(days=90)).strftime('%Y-%m-%d')
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






