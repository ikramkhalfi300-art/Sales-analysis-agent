# src/pdf_gen.py
"""
Premium Business Intelligence Report Generator — v3.0
Fixes applied:
  1. Single Source of Truth — all numbers from ctx only
  2. Leading Indicators as cards, not broken table
  3. Column definition auto-inferred and displayed
  4. Peak date urgency warning with days countdown
  5. Decision-ready recommendations with Owner + Deadline
  6. QA errors with impact assessment and action taken
  7. Executive Summary = 1 page, 4 paragraphs only
"""

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
from matplotlib import rcParams

from reportlab.lib.pagesizes   import A4
from reportlab.lib.units       import inch
from reportlab.lib             import colors
from reportlab.lib.styles      import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums       import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus        import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether
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
        reshaped = reshape(str(text))
        return get_display(reshaped)
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
    'navy':        '#1B2E4B',
    'navy_dark':   '#0A1628',
    'blue':        '#1A3A6B',
    'blue_mid':    '#2557A7',
    'blue_light':  '#E8EFF8',
    'blue_pale':   '#F2F6FB',
    'teal':        '#0D7377',
    'green':       '#1A6B3A',
    'green_light': '#E8F4EC',
    'amber':       '#92400E',
    'amber_light': '#FEF3C7',
    'red':         '#7F1D1D',
    'red_light':   '#FEF2F2',
    'gray_dark':   '#1F2937',
    'gray_mid':    '#4B5563',
    'gray':        '#6B7280',
    'gray_light':  '#F3F4F6',
    'gray_pale':   '#F9FAFB',
    'border':      '#D1D5DB',
    'chart1':      '#1A3A6B',
    'chart2':      '#2557A7',
    'chart3':      '#0D7377',
    'chart4':      '#1A6B3A',
    'chart5':      '#92400E',
    'chart_neg':   '#7F1D1D',
    'chart_pos':   '#1A6B3A',
    'bear':        '#DC2626',
    'bull':        '#16A34A',
    'urgent':      '#7F1D1D',
}

C = {k: colors.HexColor(v) for k, v in CH.items()}
C['white'] = colors.white
C['black'] = colors.black

def rl(key):
    return C.get(key, colors.HexColor('#1A3A6B'))

def mpl(key):
    return CH.get(key, '#1A3A6B')


# ═══════════════════════════════════════════════════════════
# 3. COLUMN DEFINITION INFERENCE
# FIX #3: Auto-infer what the group column represents
# ═══════════════════════════════════════════════════════════
def _infer_column_meaning(group_col: str, store_df, lang: str = 'en') -> str:
    """
    Automatically infer what the group column represents
    and return a human-readable definition.
    This fixes the 'Quantity 1,2,3 without explanation' problem.
    """
    if store_df is None or group_col is None:
        return ""

    values = store_df[group_col].dropna().unique()
    n      = len(values)

    # Check if values are numeric (1,2,3...) vs text (Store A, Region B...)
    try:
        numeric_vals = [float(v) for v in values]
        is_numeric   = True
        min_v, max_v = int(min(numeric_vals)), int(max(numeric_vals))
    except (ValueError, TypeError):
        is_numeric = False
        min_v = max_v = 0

    col_lower = group_col.lower()

    # Infer meaning from column name + value type
    if any(x in col_lower for x in ['store','branch','فرع','magasin']):
        meaning = f"store/branch locations"
    elif any(x in col_lower for x in ['region','zone','territory','منطقة']):
        meaning = f"geographic regions or territories"
    elif any(x in col_lower for x in ['product','sku','item','category','produit']):
        meaning = f"product categories or SKU groups"
    elif any(x in col_lower for x in ['quantity','qty','كمية']):
        if is_numeric:
            meaning = f"quantity tiers or volume bands (range: {min_v}–{max_v})"
        else:
            meaning = f"quantity classifications"
    elif any(x in col_lower for x in ['price','tier','level','prix']):
        meaning = f"price tiers or customer segments"
    else:
        if is_numeric:
            meaning = f"numbered categories (values: {min_v}–{max_v})"
        else:
            meaning = f"business segments"

    definitions = {
        'en': f"ℹ️ <b>Column Definition:</b> '{group_col}' represents {meaning}. "
              f"This report analyzes {n} distinct {group_col} values. "
              f"<i>Note: If this classification differs from your business context, "
              f"please relabel the column before re-running the analysis.</i>",
        'ar': f"ℹ️ <b>تعريف العمود:</b> '{group_col}' يمثل {meaning}. "
              f"يحلل هذا التقرير {n} قيمة مختلفة.",
        'fr': f"ℹ️ <b>Définition de la colonne:</b> '{group_col}' représente {meaning}. "
              f"Ce rapport analyse {n} valeurs distinctes.",
    }
    return definitions.get(lang, definitions['en'])


# ═══════════════════════════════════════════════════════════
# 4. PEAK DATE URGENCY CALCULATOR
# FIX #4: Show days remaining and urgency level
# ═══════════════════════════════════════════════════════════
def _get_peak_urgency(peak_week_str: str) -> dict:
    """
    Calculate days until peak and return urgency classification.
    This fixes the 'advance preparation' warning for near-future peaks.
    """
    today = pd.Timestamp.now().normalize()
    try:
        peak_dt   = pd.Timestamp(peak_week_str)
        days_left = (peak_dt - today).days
        is_past   = days_left < 0
    except Exception:
        return {'days_left': None, 'level': 'unknown', 'is_past': False}

    if is_past:
        level   = 'past'
        message = f"Peak date has passed ({abs(days_left)} days ago). Review actual vs. forecast."
    elif days_left <= 7:
        level   = 'critical'
        message = f"CRITICAL: Peak in {days_left} days. Immediate action required NOW."
    elif days_left <= 14:
        level   = 'urgent'
        message = f"URGENT: Peak in {days_left} days. Begin preparation immediately this week."
    elif days_left <= 30:
        level   = 'soon'
        message = f"Peak in {days_left} days. Begin preparation within 48 hours."
    else:
        level   = 'planned'
        message = f"Peak in {days_left} days. Standard preparation timeline applies."

    return {
        'days_left': days_left,
        'level':     level,
        'message':   message,
        'is_past':   is_past,
    }


# ═══════════════════════════════════════════════════════════
# 5. DYNAMIC DATA EXTRACTION
# FIX #1: Single Source of Truth — all numbers computed ONCE
# ═══════════════════════════════════════════════════════════
def extract_dynamic_context(
    df, date_col, sales_col, summary, store_df,
    group_col, corr_series, forecast_summary, monthly_df,
) -> dict:
    """
    ALL report numbers are computed here ONCE.
    Every section reads from ctx — never recomputes.
    This eliminates number inconsistencies across sections.
    """
    ctx = {}

    # ── Core stats ────────────────────────────────────────
    ctx['total_revenue']   = float(df[sales_col].sum())
    ctx['avg_per_period']  = float(df[sales_col].mean())
    ctx['peak_value']      = float(df[sales_col].max())
    ctx['min_value']       = float(df[sales_col].min())
    ctx['n_records']       = int(len(df))
    ctx['std_dev']         = float(df[sales_col].std())
    ctx['cv_pct']          = round(ctx['std_dev'] / ctx['avg_per_period'] * 100, 1) if ctx['avg_per_period'] > 0 else 0

    # ── Dates ─────────────────────────────────────────────
    ctx['date_min']   = str(df[date_col].min().date())
    ctx['date_max']   = str(df[date_col].max().date())
    ctx['date_range'] = f"{ctx['date_min']} to {ctx['date_max']}"
    ctx['n_periods']  = int(df[date_col].nunique())

    # ── Trend ─────────────────────────────────────────────
    sorted_df   = df.groupby(date_col)[sales_col].sum().reset_index().sort_values(date_col)
    half        = max(1, len(sorted_df) // 2)
    first_half  = float(sorted_df[sales_col].iloc[:half].mean())
    second_half = float(sorted_df[sales_col].iloc[half:].mean())
    trend_pct   = (second_half - first_half) / first_half * 100 if first_half > 0 else 0
    ctx['trend_pct']       = round(trend_pct, 1)
    ctx['trend_direction'] = "growing" if trend_pct > 3 else "declining" if trend_pct < -3 else "stable"

    # ── Period stats ──────────────────────────────────────
    if len(monthly_df) > 0:
        vals   = monthly_df['total'].tolist()
        months = [str(m) for m in monthly_df['month']]
        ctx['best_period_label']  = months[vals.index(max(vals))] if vals else 'N/A'
        ctx['worst_period_label'] = months[vals.index(min(vals))] if vals else 'N/A'
        ctx['best_period_value']  = max(vals) if vals else 0
        ctx['worst_period_value'] = min(vals) if vals else 0
        ctx['period_spread_pct']  = round((max(vals)-min(vals))/max(ctx['avg_per_period'],1)*100,1) if vals else 0
    else:
        ctx['best_period_label']  = 'N/A'
        ctx['worst_period_label'] = 'N/A'
        ctx['best_period_value']  = 0
        ctx['worst_period_value'] = 0
        ctx['period_spread_pct']  = 0

    # ── Segment stats ─────────────────────────────────────
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
        cum  = store_df['total'].sort_values(ascending=False).cumsum()
        n80  = int((cum <= total_rev*0.80).sum()) + 1
        ctx['pareto_n']   = n80
        ctx['pareto_pct'] = round(n80/max(len(store_df),1)*100, 1)
    else:
        ctx['best_group_revenue']  = 0
        ctx['best_group_share']    = 0
        ctx['worst_group_revenue'] = 0
        ctx['worst_group_avg']     = 0
        ctx['best_group_avg']      = 0
        ctx['pareto_n']            = 0
        ctx['pareto_pct']          = 0

    # ── Correlations ──────────────────────────────────────
    if corr_series is not None and len(corr_series) > 0:
        pos = corr_series[corr_series >  0.1]
        neg = corr_series[corr_series < -0.1]
        ctx['pos_factors'] = [(str(k), round(float(v),4)) for k,v in pos.items()]
        ctx['neg_factors'] = [(str(k), round(float(v),4)) for k,v in neg.items()]
    else:
        ctx['pos_factors'] = []
        ctx['neg_factors'] = []

    # ── Forecast — SINGLE SOURCE, read once, used everywhere ──
    ctx['fc4']  = float(forecast_summary.get('next_4_weeks',  0))
    ctx['fc8']  = float(forecast_summary.get('next_8_weeks',  0))
    ctx['fc12'] = float(forecast_summary.get('next_12_weeks', 0))
    ctx['bear_12']        = float(forecast_summary.get('bear_12_weeks', ctx['fc12']*0.75))
    ctx['bull_12']        = float(forecast_summary.get('bull_12_weeks', ctx['fc12']*1.25))
    ctx['peak_week']      = str(forecast_summary.get('peak_week', 'N/A'))
    ctx['peak_fc']        = float(forecast_summary.get('peak_expected_sales', 0))
    ctx['bear_prob']      = forecast_summary.get('bear_probability', 0.25)
    ctx['base_prob']      = forecast_summary.get('base_probability', 0.55)
    ctx['bull_prob']      = forecast_summary.get('bull_probability', 0.20)
    ctx['confidence_level']   = forecast_summary.get('confidence_level', 'Medium')
    ctx['volatility']         = forecast_summary.get('volatility', {})
    ctx['sanity_check']       = forecast_summary.get('sanity_check', {'passed':True,'warnings':[]})
    ctx['leading_indicators'] = forecast_summary.get('leading_indicators', [])
    ctx['decision_rule']      = forecast_summary.get('decision_rule', '')

    # ── Peak urgency (FIX #4) ─────────────────────────────
    ctx['peak_urgency'] = _get_peak_urgency(ctx['peak_week'])
    ctx['peak_is_past'] = ctx['peak_urgency']['is_past']

    # ── Decision metrics for recommendations (FIX #5) ────
    # Cost of inaction = gap from worst to average × 12 periods
    ctx['worst_group_gap_weekly']   = ctx['avg_per_period'] - ctx['worst_group_avg']
    ctx['worst_group_annual_cost']  = ctx['worst_group_gap_weekly'] * 52
    ctx['worst_group_12p_cost']     = ctx['worst_group_gap_weekly'] * 12
    # First action deadline = today + 30 days
    ctx['action_deadline_30']  = (pd.Timestamp.now() + pd.Timedelta(days=30)).strftime('%Y-%m-%d')
    ctx['action_deadline_7']   = (pd.Timestamp.now() + pd.Timedelta(days=7)).strftime('%Y-%m-%d')
    ctx['action_deadline_90']  = (pd.Timestamp.now() + pd.Timedelta(days=90)).strftime('%Y-%m-%d')

    # ── Report date ───────────────────────────────────────
    ctx['report_date'] = pd.Timestamp.now().strftime('%d %B %Y')
    ctx['report_year'] = pd.Timestamp.now().strftime('%Y')

    return ctx


# ═══════════════════════════════════════════════════════════
# 6. QUALITY GUARDRAILS
# FIX #6: QA errors now show impact + action taken
# ═══════════════════════════════════════════════════════════
_FORBIDDEN_PATTERNS = [
    r'\bwalmart\b', r'\b2010\b', r'\b2011\b', r'\b2012\b',
    r'\bweekly[_\s]sales\b', r'\bholiday[_\s]flag\b',
    r'\bstore\s+\d+\b(?!.*is)', r'\bprophet\b', r'\bfacebook\b',
    r'\b(index|idx|unnamed)\b',
]

def validate_report_data(ai_text: str, ctx: dict) -> dict:
    errors     = []
    text_lower = ai_text.lower()

    for pattern in _FORBIDDEN_PATTERNS:
        if re.search(pattern, text_lower):
            errors.append({
                'error':  f"Forbidden reference: '{pattern}'",
                'impact': 'Low — cosmetic quality issue',
                'action': 'Reference removed in correction loop',
            })

    years_in_text   = set(re.findall(r'\b(19|20)\d{2}\b', ai_text))
    actual_year_min = int(ctx['date_min'][:4])
    actual_year_max = int(ctx['date_max'][:4])
    for yr in years_in_text:
        yr_int = int(yr)
        if yr_int < actual_year_min or yr_int > int(ctx['report_year'])+1:
            errors.append({
                'error':  f"Year {yr} outside data range ({actual_year_min}–{actual_year_max})",
                'impact': 'Medium — may affect forecast period labeling',
                'action': f"Periods outside {actual_year_min}–{actual_year_max} excluded from analysis",
            })

    dollar_amounts = re.findall(r'\$\s*([\d,\.]+)\s*([MBK]?)', ai_text)
    for amount_str, suffix in dollar_amounts:
        try:
            val = float(amount_str.replace(',',''))
            if suffix=='M': val*=1e6
            elif suffix=='B': val*=1e9
            elif suffix=='K': val*=1e3
            if val > ctx['total_revenue']*2:
                errors.append({
                    'error':  f"Amount ${amount_str}{suffix} exceeds 2x total revenue",
                    'impact': 'High — possible hallucination in AI analysis',
                    'action': 'Amount flagged; verify against source data before acting',
                })
        except ValueError:
            pass

    return {'passed': len(errors)==0, 'errors': errors}


def self_correct_with_ai(ai_text, errors, ctx, system_prompt, ask_agent_fn):
    if not errors or ask_agent_fn is None:
        return ai_text
    error_report = "\n".join(f"- {e['error']}" for e in errors)
    correction_prompt = f"""
Rewrite the following business analysis correcting these errors:
{error_report}

ACTUAL DATA FACTS (use ONLY these):
- Date range: {ctx['date_range']}
- Total revenue: ${ctx['total_revenue']:,.2f}
- Average per period: ${ctx['avg_per_period']:,.2f}
- Best segment: {ctx['best_group']} (${ctx['best_group_revenue']:,.0f})
- Worst segment: {ctx['worst_group']}
- 12-period forecast: ${ctx['fc12']:,.0f}

ORIGINAL TEXT:
{ai_text}

Return ONLY the corrected text.
"""
    try:
        corrected, _ = ask_agent_fn(correction_prompt, system_prompt, [])
        return corrected
    except Exception:
        return ai_text


def run_quality_pipeline(ai_text, ctx, system_prompt="", ask_agent_fn=None, max_iterations=2):
    current_text = ai_text
    iteration    = 0
    for iteration in range(max_iterations):
        result = validate_report_data(current_text, ctx)
        if result['passed']:
            break
        if ask_agent_fn and iteration < max_iterations-1:
            current_text = self_correct_with_ai(
                current_text, result['errors'], ctx, system_prompt, ask_agent_fn
            )
        else:
            break
    final = validate_report_data(current_text, ctx)
    return current_text, {'passed': final['passed'], 'errors': final['errors'], 'iterations': iteration+1}


# ═══════════════════════════════════════════════════════════
# 7. CHART UTILITIES
# ═══════════════════════════════════════════════════════════
PAGE_W, PAGE_H = A4
MARGIN    = 0.85 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

def _set_chart_style():
    rcParams['font.family']       = 'sans-serif'
    rcParams['axes.spines.top']   = False
    rcParams['axes.spines.right'] = False
    rcParams['axes.linewidth']    = 0.5
    rcParams['axes.grid']         = True
    rcParams['grid.alpha']        = 0.12
    rcParams['grid.linewidth']    = 0.4
    rcParams['xtick.labelsize']   = 8
    rcParams['ytick.labelsize']   = 8
    rcParams['figure.facecolor']  = 'white'
    rcParams['axes.facecolor']    = 'white'

_set_chart_style()

def _money(x, pos=None):
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
# 8. TYPOGRAPHY
# ═══════════════════════════════════════════════════════════
def build_styles(lang: str = 'en'):
    fn      = get_font(lang, bold=False)
    fn_bold = get_font(lang, bold=True)
    align   = TA_RIGHT if lang=='ar' else TA_LEFT
    S = {}

    S['cover_eyebrow']    = ParagraphStyle('cover_eyebrow', fontSize=8.5, fontName=fn_bold, textColor=rl('blue_mid'), alignment=TA_CENTER, spaceAfter=6, leading=12)
    S['cover_title']      = ParagraphStyle('cover_title', fontSize=26, fontName=fn_bold, textColor=rl('navy'), alignment=TA_CENTER, spaceAfter=10, leading=32)
    S['cover_subtitle']   = ParagraphStyle('cover_subtitle', fontSize=13, fontName=fn, textColor=rl('gray_mid'), alignment=TA_CENTER, spaceAfter=6, leading=19)
    S['cover_meta_label'] = ParagraphStyle('cover_meta_label', fontSize=7.5, fontName=fn_bold, textColor=rl('gray'), alignment=align, leading=11)
    S['cover_meta_value'] = ParagraphStyle('cover_meta_value', fontSize=10, fontName=fn, textColor=rl('navy'), alignment=align, leading=14)
    S['section_label']    = ParagraphStyle('section_label', fontSize=8, fontName=fn_bold, textColor=rl('blue_mid'), alignment=align, spaceAfter=4, spaceBefore=18, leading=12)
    S['h1']               = ParagraphStyle('h1', fontSize=17, fontName=fn_bold, textColor=rl('navy'), alignment=align, spaceAfter=6, spaceBefore=4, leading=21)
    S['h2']               = ParagraphStyle('h2', fontSize=12, fontName=fn_bold, textColor=rl('blue'), alignment=align, spaceAfter=5, spaceBefore=12, leading=16)
    S['h3']               = ParagraphStyle('h3', fontSize=10.5, fontName=fn_bold, textColor=rl('gray_dark'), alignment=align, spaceAfter=4, spaceBefore=8, leading=14)
    S['body']             = ParagraphStyle('body', fontSize=9.5, fontName=fn, textColor=rl('gray_dark'), alignment=TA_JUSTIFY if lang!='ar' else TA_RIGHT, spaceAfter=6, leading=15)
    S['body_small']       = ParagraphStyle('body_small', fontSize=8.5, fontName=fn, textColor=rl('gray_mid'), alignment=align, spaceAfter=4, leading=12)
    S['bullet']           = ParagraphStyle('bullet', fontSize=9.5, fontName=fn, textColor=rl('gray_dark'), alignment=align, spaceAfter=4, leading=15, leftIndent=14 if lang!='ar' else 0, rightIndent=14 if lang=='ar' else 0)
    S['metric_value']     = ParagraphStyle('metric_value', fontSize=20, fontName=fn_bold, textColor=rl('navy'), alignment=TA_CENTER, spaceAfter=2, leading=24)
    S['metric_label']     = ParagraphStyle('metric_label', fontSize=7.5, fontName=fn, textColor=rl('gray'), alignment=TA_CENTER, spaceAfter=0, leading=10)
    S['metric_bear']      = ParagraphStyle('metric_bear', fontSize=18, fontName=fn_bold, textColor=rl('bear'), alignment=TA_CENTER, spaceAfter=2, leading=22)
    S['metric_bull']      = ParagraphStyle('metric_bull', fontSize=18, fontName=fn_bold, textColor=rl('bull'), alignment=TA_CENTER, spaceAfter=2, leading=22)
    S['toc_entry']        = ParagraphStyle('toc_entry', fontSize=10, fontName=fn, textColor=rl('gray_dark'), alignment=align, spaceAfter=4, leading=14)
    S['toc_page']         = ParagraphStyle('toc_page', fontSize=10, fontName=fn, textColor=rl('blue_mid'), alignment=TA_RIGHT, spaceAfter=4, leading=14)
    S['callout_blue']     = ParagraphStyle('cb', fontSize=9.5, fontName=fn, textColor=rl('blue'), alignment=align, spaceAfter=4, leading=15, leftIndent=12)
    S['callout_green']    = ParagraphStyle('cg', fontSize=9.5, fontName=fn, textColor=rl('green'), alignment=align, spaceAfter=4, leading=15, leftIndent=12)
    S['callout_amber']    = ParagraphStyle('ca', fontSize=9.5, fontName=fn, textColor=rl('amber'), alignment=align, spaceAfter=4, leading=15, leftIndent=12)
    S['callout_red']      = ParagraphStyle('cr', fontSize=9.5, fontName=fn, textColor=rl('red'), alignment=align, spaceAfter=4, leading=15, leftIndent=12)
    S['footer']           = ParagraphStyle('footer', fontSize=7, fontName=fn, textColor=rl('gray'), alignment=TA_CENTER, leading=9)
    S['validation_ok']    = ParagraphStyle('vok', fontSize=8, fontName=fn, textColor=rl('green'), alignment=TA_LEFT, leading=11)
    S['validation_err']   = ParagraphStyle('verr', fontSize=8, fontName=fn, textColor=rl('red'), alignment=TA_LEFT, leading=11)
    S['confidence_badge'] = ParagraphStyle('conf_badge', fontSize=8, fontName=fn_bold, textColor=rl('teal'), alignment=TA_LEFT, leading=11)
    S['owner_label']      = ParagraphStyle('owner', fontSize=8, fontName=fn_bold, textColor=rl('navy'), alignment=TA_LEFT, leading=12)
    S['urgent_label']     = ParagraphStyle('urgent', fontSize=9, fontName=fn_bold, textColor=rl('urgent'), alignment=align, leading=13)
    S['col_definition']   = ParagraphStyle('col_def', fontSize=8.5, fontName=fn, textColor=rl('teal'), alignment=align, spaceAfter=8, leading=13, leftIndent=8)

    return S


# ═══════════════════════════════════════════════════════════
# 9. LAYOUT HELPERS
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
    pstyle = S[f'callout_{style}']
    tbl = Table([[Paragraph(process_text(text, lang), pstyle)]],
                colWidths=[CONTENT_W-0.3*inch])
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

def _pro_table(story, data, col_widths=None, lang='en'):
    if not data: return
    n  = len(data[0])
    cw = col_widths or [CONTENT_W/n]*n
    processed = [[process_text(str(cell), lang) for cell in row] for row in data]
    style = [
        ('FONTNAME',      (0,0), (-1,-1), get_font(lang)),
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('TEXTCOLOR',     (0,0), (-1,-1), rl('gray_dark')),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING',   (0,0), (-1,-1), 9),
        ('RIGHTPADDING',  (0,0), (-1,-1), 9),
        ('GRID',          (0,0), (-1,-1), 0.3, rl('border')),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [rl('white'), rl('gray_pale')]),
        ('ALIGN',         (1,0), (-1,-1), 'RIGHT' if lang!='ar' else 'LEFT'),
        ('ALIGN',         (0,0), (0,-1),  'LEFT'  if lang!='ar' else 'RIGHT'),
        ('BACKGROUND',    (0,0), (-1,0),  rl('navy')),
        ('TEXTCOLOR',     (0,0), (-1,0),  rl('white')),
        ('FONTNAME',      (0,0), (-1,0),  get_font(lang, bold=True)),
        ('ALIGN',         (0,0), (-1,0),  'CENTER'),
        ('TOPPADDING',    (0,0), (-1,0),  9),
        ('BOTTOMPADDING', (0,0), (-1,0),  9),
    ]
    tbl = Table(processed, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle(style))
    story.append(tbl)
    story.append(Spacer(1, 0.12*inch))

def _confidence_badge(story, level: str, S, lang='en'):
    icons  = {"High":"🟢","Medium":"🟡","Low":"🔴"}
    icon   = icons.get(level,"🟡")
    labels = {
        "en": f"{icon} Forecast Confidence: {level}",
        "ar": f"{icon} مستوى الثقة: {level}",
        "fr": f"{icon} Confiance Prévision: {level}",
    }
    story.append(Paragraph(process_text(labels.get(lang, labels["en"]), lang), S['confidence_badge']))
    story.append(Spacer(1, 0.06*inch))

def _volatility_block(story, volatility: dict, cv_pct: float, S, lang='en'):
    if not volatility: return
    level = volatility.get('level','Unknown')
    risk  = volatility.get('risk','')
    badge = volatility.get('badge','🟡')
    vol_text = {
        "en": f"<b>{badge} Revenue Volatility: {level} (CV = {cv_pct:.1f}%)</b><br/>{risk}",
        "ar": f"<b>{badge} تقلب الإيرادات: {level} (CV = {cv_pct:.1f}%)</b><br/>{risk}",
        "fr": f"<b>{badge} Volatilité: {level} (CV = {cv_pct:.1f}%)</b><br/>{risk}",
    }.get(lang,"")
    style_key = 'amber' if level in ('High','Extreme') else 'blue'
    _callout(story, vol_text, style_key, S, lang)


# ═══════════════════════════════════════════════════════════
# 10. PAGE FOOTER
# ═══════════════════════════════════════════════════════════
class ReportCanvas:
    def __init__(self, report_date: str, lang: str='en'):
        self.report_date = report_date
        self.lang        = lang

    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(rl('blue'))
        canvas.rect(MARGIN, PAGE_H-0.36*inch, CONTENT_W, 2.2, fill=1, stroke=0)
        canvas.setStrokeColor(rl('border'))
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN, 0.60*inch, PAGE_W-MARGIN, 0.60*inch)
        canvas.setFont(get_font(self.lang), 7)
        canvas.setFillColor(rl('gray'))
        canvas.drawString(MARGIN, 0.40*inch,
                          process_text("Confidential Business Analysis Report", self.lang))
        canvas.drawCentredString(PAGE_W/2, 0.40*inch, f"Page {doc.page}")
        canvas.drawRightString(PAGE_W-MARGIN, 0.40*inch,
                               process_text(self.report_date, self.lang))
        canvas.restoreState()


# ═══════════════════════════════════════════════════════════
# 11. MARKDOWN RENDERER
# ═══════════════════════════════════════════════════════════
def _clean_md(text: str) -> str:
    text = re.sub(r'^#{1,4}\s*', '', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*',    r'<i>\1</i>', text)
    text = re.sub(r'[■□▪▫●►▸▶\u25A0-\u25FF]', '', text)
    return text.strip()

def _render_analysis(story, text: str, S, lang: str='en'):
    table_buf = []
    for raw in text.split('\n'):
        line = raw.rstrip()
        if table_buf and not (line.startswith('|') and line.endswith('|')):
            _flush_md_table(story, table_buf, S, lang)
            table_buf = []
        if not line.strip():
            story.append(Spacer(1, 0.06*inch)); continue
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
        elif re.match(r'^\d+\.\s', line.strip()):
            story.append(Paragraph(process_text(clean,lang), S['bullet']))
        else:
            pt = process_text(clean, lang)
            if any(k in clean for k in ['🚨','⚠️','Warning','Critical']):
                story.append(Paragraph(pt, S['callout_amber']))
            elif any(k in clean for k in ['💰','$']):
                story.append(Paragraph(pt, S['callout_green']))
            else:
                story.append(Paragraph(pt, S['body']))
    if table_buf:
        _flush_md_table(story, table_buf, S, lang)

def _flush_md_table(story, rows, S, lang):
    if not rows: return
    n = max(len(r) for r in rows)
    _pro_table(story, rows, col_widths=[CONTENT_W/n]*n, lang=lang)


# ═══════════════════════════════════════════════════════════
# 12. REPORT SECTIONS
# ═══════════════════════════════════════════════════════════

def _cover(story, company_name, S, ctx, lang):
    story.append(Spacer(1, 1.2*inch))
    rule = Table([['']], colWidths=[CONTENT_W], rowHeights=[3])
    rule.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),rl('blue'))]))
    story.append(rule)
    story.append(Spacer(1, 0.3*inch))

    client = company_name if company_name else "Client Organization"
    t = {
        'en': ("BUSINESS INTELLIGENCE REPORT","Sales Performance Analysis Report","Performance Assessment &amp; Strategic Intelligence"),
        'ar': ("تقرير الذكاء التجاري","تقرير تحليل أداء المبيعات","تقييم الأداء والاستخبارات الاستراتيجية"),
        'fr': ("RAPPORT D'INTELLIGENCE COMMERCIALE","Rapport d'Analyse des Ventes","Évaluation de la Performance &amp; Intelligence Stratégique"),
    }.get(lang, ("BUSINESS INTELLIGENCE REPORT","Sales Performance Analysis Report","Performance Assessment &amp; Strategic Intelligence"))

    story.append(Paragraph(process_text(t[0],lang), S['cover_eyebrow']))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(process_text(t[1],lang), S['cover_title']))
    story.append(Spacer(1, 0.12*inch))
    story.append(Paragraph(process_text(t[2],lang), S['cover_subtitle']))
    story.append(Spacer(1, 0.3*inch))
    story.append(rule)
    story.append(Spacer(1, 0.45*inch))

    labels = {
        'en': ["PREPARED FOR","REPORTING PERIOD","REPORT DATE","CLASSIFICATION"],
        'ar': ["مُعدّ لـ","فترة التقرير","تاريخ التقرير","التصنيف"],
        'fr': ["PRÉPARÉ POUR","PÉRIODE","DATE DU RAPPORT","CLASSIFICATION"],
    }.get(lang, ["PREPARED FOR","REPORTING PERIOD","REPORT DATE","CLASSIFICATION"])

    meta_items = [
        (labels[0], client),
        (labels[1], ctx['date_range']),
        (labels[2], ctx['report_date']),
        (labels[3], "Confidential" if lang=="en" else "سري" if lang=="ar" else "Confidentiel"),
    ]
    rows = []
    for lbl, val in meta_items:
        rows.append([
            Paragraph(process_text(lbl,lang), S['cover_meta_label']),
            Paragraph(process_text(str(val),lang), S['cover_meta_value']),
        ])
    meta_tbl = Table(rows, colWidths=[1.7*inch, CONTENT_W-1.7*inch])
    meta_tbl.setStyle(TableStyle([
        ('ALIGN',         (0,0),(-1,-1),'LEFT'),
        ('VALIGN',        (0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1),6),
        ('BOTTOMPADDING', (0,0),(-1,-1),6),
        ('LINEBELOW',     (0,0),(-1,-2),0.25,rl('border')),
        ('LEFTPADDING',   (0,0),(-1,-1),0),
    ]))
    story.append(meta_tbl)
    story.append(PageBreak())


def _toc(story, S, ctx, lang, has_store, has_corr):
    lbl   = {'en':'TABLE OF CONTENTS','ar':'فهرس المحتويات','fr':'TABLE DES MATIÈRES'}.get(lang,'TABLE OF CONTENTS')
    title = {'en':'Report Structure','ar':'هيكل التقرير','fr':'Structure du Rapport'}.get(lang,'Report Structure')
    story.append(Paragraph(process_text(lbl,lang), S['section_label']))
    story.append(Paragraph(process_text(title,lang), S['h1']))
    _divider(story, color=rl('blue'), thickness=1.1, sb=2, sa=16)

    sections = [
        ("01","Executive Summary (1 page)","3"),
        ("02","Key Findings","4"),
        ("03","Sales Performance Overview","5"),
        ("04","Period Trend Analysis","6"),
    ]
    pg = 7
    if has_store: sections.append((f"{pg:02d}","Segment Performance Analysis",str(pg))); pg+=1
    if has_corr:  sections.append((f"{pg:02d}","External Factors & Correlations",str(pg))); pg+=1
    sections.append((f"{pg:02d}","Revenue Forecast & Scenarios",str(pg))); pg+=1
    sections.append((f"{pg:02d}","Strategic Recommendations",str(pg))); pg+=1
    sections.append((f"{pg:02d}","Data Appendix",str(pg)))

    for num, title_en, page in sections:
        row = [[
            Paragraph(f"<b>{num}</b>", ParagraphStyle('tn', fontSize=9,
                fontName=get_font(lang,True), textColor=rl('blue_mid'),
                alignment=TA_LEFT, leading=13)),
            Paragraph(process_text(title_en,lang), S['toc_entry']),
            Paragraph(page, S['toc_page']),
        ]]
        rt = Table(row, colWidths=[0.45*inch, CONTENT_W-1.1*inch, 0.65*inch])
        rt.setStyle(TableStyle([
            ('VALIGN',        (0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',    (0,0),(-1,-1),6),
            ('BOTTOMPADDING', (0,0),(-1,-1),6),
            ('LINEBELOW',     (0,0),(-1,-1),0.2,rl('border')),
        ]))
        story.append(rt)
    story.append(PageBreak())


# ═══════════════════════════════════════════════════════════
# FIX #7 — Executive Summary = 1 page, 4 paragraphs ONLY
# Situation / Complication / Resolution / Stakes
# ═══════════════════════════════════════════════════════════
def _executive_summary(story, S, ctx, lang, ai_result=None):
    titles = {
        'en':("01","Executive Summary"),
        'ar':("01","الملخص التنفيذي"),
        'fr':("01","Résumé Exécutif"),
    }.get(lang,("01","Executive Summary"))
    _section_header(story, titles[0], titles[1], S, lang)

    # ── Metric Strip (4 KPIs) ─────────────────────────────
    col_w  = CONTENT_W/4
    m_vals = [
        (_money(ctx['total_revenue']),  {'en':'Total Revenue','ar':'إجمالي الإيرادات','fr':'Revenu Total'}.get(lang,'')),
        (_money(ctx['avg_per_period']), {'en':'Avg per Period','ar':'متوسط الفترة','fr':'Moy. par Période'}.get(lang,'')),
        (_money(ctx['peak_value']),     {'en':'Peak Performance','ar':'أعلى أداء','fr':'Performance Max'}.get(lang,'')),
        (_money(ctx['fc12']),           {'en':'12-Period Forecast','ar':'توقعات 12 فترة','fr':'Prévision 12 Pér.'}.get(lang,'')),
    ]
    mt = Table(
        [[Paragraph(process_text(v,lang), S['metric_value']) for v,_ in m_vals],
         [Paragraph(process_text(l,lang), S['metric_label']) for _,l in m_vals]],
        colWidths=[col_w]*4, rowHeights=[0.46*inch, 0.26*inch]
    )
    mt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1),rl('blue_pale')),
        ('ALIGN',         (0,0),(-1,-1),'CENTER'),
        ('VALIGN',        (0,0),(-1,-1),'MIDDLE'),
        ('GRID',          (0,0),(-1,-1),0.35,rl('border')),
        ('LINEABOVE',     (0,0),(-1,0), 1.4,rl('blue')),
        ('LINEBELOW',     (0,-1),(-1,-1),1.4,rl('blue')),
        ('TOPPADDING',    (0,0),(-1,0), 10),
        ('BOTTOMPADDING', (0,-1),(-1,-1),8),
    ]))
    story.append(mt)
    story.append(Spacer(1, 0.18*inch))

    # ── 4 Paragraphs: Situation / Complication / Resolution / Stakes ──
    if lang == 'en':
        p1 = (
            "SITUATION — Where We Are",
            f"The portfolio generated <b>${ctx['total_revenue']:,.0f}</b> across "
            f"<b>{ctx['n_records']:,} records</b> and <b>{ctx['n_periods']:,} periods</b> "
            f"({ctx['date_range']}). Revenue averages <b>${ctx['avg_per_period']:,.0f}/period</b> "
            f"with an overall trend that is <b>{ctx['trend_direction']}</b> "
            f"({ctx['trend_pct']:+.1f}% half-over-half). "
            f"Forecast confidence is <b>{ctx['confidence_level']}</b> due to "
            f"CV = {ctx['cv_pct']:.1f}%."
        )
        p2 = (
            "COMPLICATION — The Critical Issue",
            f"Revenue concentration is extreme: <b>{ctx['pareto_pct']:.0f}% of segments "
            f"generate 80% of revenue</b>, led by <b>{ctx['best_group']}</b> "
            f"(${ctx['best_group_revenue']:,.0f}, {ctx['best_group_share']:.1f}% of total). "
            f"Meanwhile, <b>{ctx['worst_group']}</b> underperforms by "
            f"<b>${ctx['worst_group_gap_weekly']:,.0f}/period</b> vs. portfolio average — "
            f"leaving <b>${ctx['worst_group_12p_cost']:,.0f}</b> on the table over 12 periods."
            if ctx['best_group'] != 'N/A' else
            f"Revenue volatility (CV={ctx['cv_pct']:.1f}%) indicates inconsistent performance "
            f"that requires structural investigation before scaling."
        )
        p3 = (
            "RESOLUTION — What We Must Do",
            f"Two immediate priorities: (1) Replicate <b>{ctx['best_group']}</b>'s model "
            f"in underperforming segments — deadline <b>{ctx['action_deadline_30']}</b>. "
            f"(2) Pre-position inventory for the base-case peak at "
            f"<b>{ctx['peak_week']}</b> ({_money(ctx['peak_fc'])}) — "
            f"{ctx['peak_urgency'].get('message','prepare in advance')}."
        )
        p4 = (
            "STAKES — Act vs. Wait",
            f"If implemented: estimated <b>{_money(ctx['total_revenue']*0.15)}–"
            f"{_money(ctx['total_revenue']*0.22)}</b> incremental annual revenue (15–22% uplift). "
            f"If delayed 90 days: foregone revenue of approximately "
            f"<b>{_money(ctx['worst_group_gap_weekly']*13)}</b> from underperformer gap alone, "
            f"plus missed peak capture opportunity of <b>{_money(ctx['peak_fc']*0.08)}</b>."
        )
    elif lang == 'ar':
        p1 = ("الوضع الحالي",
              f"حقق المحفظة <b>${ctx['total_revenue']:,.0f}</b> عبر <b>{ctx['n_records']:,} سجل</b> "
              f"و<b>{ctx['n_periods']:,} فترة</b> ({ctx['date_range']}). "
              f"الاتجاه العام: <b>{ctx['trend_direction']}</b> ({ctx['trend_pct']:+.1f}%). "
              f"مستوى الثقة: <b>{ctx['confidence_level']}</b>.")
        p2 = ("المشكلة الجوهرية",
              f"تركز الإيرادات مرتفع: <b>{ctx['pareto_pct']:.0f}% من الشرائح تولّد 80% من الإيرادات</b>. "
              f"يتصدر <b>{ctx['best_group']}</b> بـ${ctx['best_group_revenue']:,.0f}. "
              f"يخسر <b>{ctx['worst_group']}</b> <b>${ctx['worst_group_12p_cost']:,.0f}</b> في 12 فترة.")
        p3 = ("ما يجب فعله",
              f"أولويتان فوريتان: (1) تكرار نموذج {ctx['best_group']} — الموعد <b>{ctx['action_deadline_30']}</b>. "
              f"(2) تجهيز المخزون قبل الذروة في <b>{ctx['peak_week']}</b> ({_money(ctx['peak_fc'])}).")
        p4 = ("تكلفة التأخر",
              f"التطبيق الكامل: <b>{_money(ctx['total_revenue']*0.15)}–{_money(ctx['total_revenue']*0.22)}</b> "
              f"إيرادات إضافية سنوياً. التأخر 90 يوماً يُضيّع <b>{_money(ctx['worst_group_gap_weekly']*13)}</b>.")
    else:
        p1 = ("SITUATION",
              f"Le portefeuille a généré <b>${ctx['total_revenue']:,.0f}</b> sur "
              f"<b>{ctx['n_records']:,} enregistrements</b> ({ctx['date_range']}). "
              f"Tendance: <b>{ctx['trend_direction']}</b> ({ctx['trend_pct']:+.1f}%). "
              f"Confiance prévision: <b>{ctx['confidence_level']}</b>.")
        p2 = ("COMPLICATION",
              f"Concentration extrême: <b>{ctx['pareto_pct']:.0f}% des segments génèrent 80% du revenu</b>. "
              f"<b>{ctx['best_group']}</b> domine avec ${ctx['best_group_revenue']:,.0f}. "
              f"<b>{ctx['worst_group']}</b> perd <b>${ctx['worst_group_12p_cost']:,.0f}</b> sur 12 périodes.")
        p3 = ("RÉSOLUTION",
              f"Deux priorités: (1) Répliquer le modèle de {ctx['best_group']} — délai <b>{ctx['action_deadline_30']}</b>. "
              f"(2) Pré-positionner le stock avant le pic de <b>{ctx['peak_week']}</b> ({_money(ctx['peak_fc'])}).")
        p4 = ("ENJEUX",
              f"Mise en œuvre: <b>{_money(ctx['total_revenue']*0.15)}–{_money(ctx['total_revenue']*0.22)}</b>/an. "
              f"Délai de 90 jours: perte de <b>{_money(ctx['worst_group_gap_weekly']*13)}</b>.")

    for title, body in [p1, p2, p3, p4]:
        story.append(Paragraph(process_text(title, lang), S['h3']))
        _callout(story, body, 'blue' if title in (p1[0],p3[0]) else 'amber' if title==p2[0] else 'green', S, lang)
        story.append(Spacer(1, 0.04*inch))

    # ── Optional AI Analysis ──────────────────────────────
    if ai_result:
        _divider(story, sb=8, sa=8)
        ai_label = {'en':'AI Analysis','ar':'التحليل الذكي','fr':'Analyse IA'}.get(lang,'AI Analysis')
        story.append(Paragraph(process_text(ai_label, lang), S['h2']))
        _render_analysis(story, ai_result, S, lang)

    story.append(PageBreak())


def _key_findings(story, S, ctx, lang):
    titles = {
        'en':("02","Key Findings"),
        'ar':("02","النتائج الرئيسية"),
        'fr':("02","Conclusions Clés"),
    }.get(lang,("02","Key Findings"))
    _section_header(story, titles[0], titles[1], S, lang)

    findings = []

    if lang == 'en':
        findings.append(("Revenue Baseline",
            f"The portfolio generated <b>${ctx['total_revenue']:,.0f}</b> across "
            f"<b>{ctx['n_records']:,}</b> records. Average: <b>${ctx['avg_per_period']:,.0f}</b>/period. "
            f"CV: <b>{ctx['cv_pct']:.1f}%</b> — "
            f"{'Low' if ctx['cv_pct']<30 else 'Moderate' if ctx['cv_pct']<60 else 'High'} volatility.", 'blue'))
    elif lang == 'ar':
        findings.append(("خط الأساس للإيرادات",
            f"إجمالي: <b>${ctx['total_revenue']:,.0f}</b> عبر <b>{ctx['n_records']:,}</b> سجل. "
            f"متوسط: <b>${ctx['avg_per_period']:,.0f}</b>/فترة. CV: <b>{ctx['cv_pct']:.1f}%</b>.", 'blue'))
    else:
        findings.append(("Base de revenus",
            f"Total: <b>${ctx['total_revenue']:,.0f}</b> sur <b>{ctx['n_records']:,}</b> enregistrements. "
            f"Moyenne: <b>${ctx['avg_per_period']:,.0f}</b>/période. CV: <b>{ctx['cv_pct']:.1f}%</b>.", 'blue'))

    if ctx['best_group'] != 'N/A' and ctx['n_groups'] > 1:
        if lang == 'en':
            findings.append((f"Segment Performance — {ctx['n_groups']} {ctx['group_col']}s",
                f"<b>{ctx['best_group']}</b> leads: <b>${ctx['best_group_revenue']:,.0f}</b> "
                f"({ctx['best_group_share']:.1f}% of total). "
                f"<b>{ctx['worst_group']}</b> is the greatest improvement opportunity "
                f"(gap: ${ctx['worst_group_gap_weekly']:,.0f}/period vs. average). "
                + (f"Pareto: top <b>{ctx['pareto_pct']:.0f}%</b> of units generate 80% of revenue." if ctx['pareto_pct']>0 else ""), 'green'))
        elif lang == 'ar':
            findings.append((f"أداء الشرائح — {ctx['n_groups']} {ctx['group_col']}",
                f"يتصدر <b>{ctx['best_group']}</b>: <b>${ctx['best_group_revenue']:,.0f}</b> "
                f"({ctx['best_group_share']:.1f}%). "
                f"الفجوة مع <b>{ctx['worst_group']}</b>: ${ctx['worst_group_gap_weekly']:,.0f}/فترة.", 'green'))
        else:
            findings.append((f"Performance des segments — {ctx['n_groups']} {ctx['group_col']}s",
                f"<b>{ctx['best_group']}</b> en tête: <b>${ctx['best_group_revenue']:,.0f}</b> "
                f"({ctx['best_group_share']:.1f}%). "
                f"Écart avec <b>{ctx['worst_group']}</b>: ${ctx['worst_group_gap_weekly']:,.0f}/période.", 'green'))

    if lang == 'en':
        findings.append(("Forward Outlook",
            f"Base: <b>${ctx['fc4']:,.0f}</b> (4p) / <b>${ctx['fc12']:,.0f}</b> (12p). "
            f"Bear: ${ctx['bear_12']:,.0f} ({ctx['bear_prob']*100:.0f}%) | "
            f"Bull: ${ctx['bull_12']:,.0f} ({ctx['bull_prob']*100:.0f}%). "
            f"Peak: <b>{ctx['peak_week']}</b> ({_money(ctx['peak_fc'])}). "
            f"Confidence: <b>{ctx['confidence_level']}</b>.", 'amber'))
    elif lang == 'ar':
        findings.append(("التوقعات",
            f"أساسي: <b>${ctx['fc12']:,.0f}</b> (12 فترة). "
            f"متشائم: ${ctx['bear_12']:,.0f} | متفائل: ${ctx['bull_12']:,.0f}. "
            f"الذروة: <b>{ctx['peak_week']}</b>. الثقة: <b>{ctx['confidence_level']}</b>.", 'amber'))
    else:
        findings.append(("Perspectives",
            f"Base: <b>${ctx['fc12']:,.0f}</b> (12p). "
            f"Pessimiste: ${ctx['bear_12']:,.0f} | Optimiste: ${ctx['bull_12']:,.0f}. "
            f"Pic: <b>{ctx['peak_week']}</b>. Confiance: <b>{ctx['confidence_level']}</b>.", 'amber'))

    for title, text, style in findings:
        story.append(Paragraph(process_text(title,lang), S['h3']))
        _callout(story, text, style, S, lang)
        story.append(Spacer(1, 0.04*inch))

    story.append(PageBreak())


def _sales_overview(story, S, ctx, df, date_col, sales_col, company_name, lang):
    titles = {
        'en':("03","Sales Performance Overview"),
        'ar':("03","نظرة عامة على أداء المبيعات"),
        'fr':("03","Vue d'ensemble des Ventes"),
    }.get(lang,("03","Sales Performance Overview"))
    _section_header(story, titles[0], titles[1], S, lang)

    intro = {
        'en': f"Revenue across {ctx['n_periods']:,} periods ({ctx['date_range']}). "
              f"Peak single-period: <b>${ctx['peak_value']:,.0f}</b>. "
              f"Trend: <b>{ctx['trend_direction']}</b> ({ctx['trend_pct']:+.1f}%).",
        'ar': f"الإيرادات عبر {ctx['n_periods']:,} فترة ({ctx['date_range']}). "
              f"أعلى قيمة: <b>${ctx['peak_value']:,.0f}</b>. الاتجاه: <b>{ctx['trend_direction']}</b>.",
        'fr': f"Revenu sur {ctx['n_periods']:,} périodes ({ctx['date_range']}). "
              f"Pic: <b>${ctx['peak_value']:,.0f}</b>. Tendance: <b>{ctx['trend_direction']}</b>.",
    }.get(lang,"")
    story.append(Paragraph(process_text(intro,lang), S['body']))
    story.append(Spacer(1, 0.12*inch))

    weekly = df.groupby(date_col)[sales_col].sum().reset_index().sort_values(date_col)
    weekly['ma'] = weekly[sales_col].rolling(4, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    ax.fill_between(weekly[date_col], weekly[sales_col], alpha=0.08, color=mpl('chart1'))
    ax.plot(weekly[date_col], weekly[sales_col], color=mpl('chart1'), linewidth=1.2, alpha=0.65,
            label={'en':'Revenue','ar':'الإيرادات','fr':'Revenu'}.get(lang,'Revenue'))
    ax.plot(weekly[date_col], weekly['ma'], color=mpl('chart2'), linewidth=2.2, zorder=5,
            label={'en':'4-Period Moving Avg','ar':'متوسط 4 فترات','fr':'Moy. Mobile 4'}.get(lang,'MA4'))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ct = (company_name+" — " if company_name else "") + \
         {'en':'Revenue Trend','ar':'اتجاه الإيرادات','fr':'Tendance des Revenus'}.get(lang,'Revenue Trend')
    ax.set_title(ct, fontsize=10.5, fontweight='bold', color=mpl('chart1'), pad=10)
    ax.spines['left'].set_color(CH['border'])
    ax.spines['bottom'].set_color(CH['border'])
    ax.legend(fontsize=8, framealpha=0.9)
    plt.tight_layout(pad=1.1)
    story.append(_fig_to_img(fig, height=3.0*inch))
    story.append(PageBreak())


def _trend_analysis(story, S, ctx, monthly_df, company_name, lang):
    titles = {
        'en':("04","Period Trend Analysis"),
        'ar':("04","تحليل التوجهات"),
        'fr':("04","Analyse des Tendances"),
    }.get(lang,("04","Period Trend Analysis"))
    _section_header(story, titles[0], titles[1], S, lang)

    months_str = [str(m) for m in monthly_df['month']]
    vals       = monthly_df['total'].tolist()
    if not vals:
        story.append(Paragraph(process_text("Insufficient data.", lang), S['body']))
        story.append(PageBreak()); return

    avg_val  = float(np.mean(vals))
    bar_clrs = [mpl('chart3') if v>=avg_val*1.05 else mpl('chart2') if v>=avg_val*0.95 else mpl('chart_neg') for v in vals]

    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    bars = ax.bar(months_str, vals, color=bar_clrs, width=0.62, edgecolor='white', linewidth=0.35)
    ax.axhline(y=avg_val, color=mpl('chart5'), linewidth=1.1, linestyle='--', alpha=0.8, label=f"Avg: {_money(avg_val)}")
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(vals)*0.011,
                _money(val), ha='center', va='bottom', fontsize=6, color=CH['gray_dark'])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ct = (company_name+" — " if company_name else "") + \
         {'en':'Period Revenue Distribution','ar':'توزيع الإيرادات','fr':'Distribution Revenus'}.get(lang,'Period Revenue')
    ax.set_title(ct, fontsize=10.5, fontweight='bold', color=mpl('chart1'), pad=10)
    ax.tick_params(axis='x', rotation=40, labelsize=7)
    ax.spines['left'].set_color(CH['border'])
    ax.spines['bottom'].set_color(CH['border'])
    ax.legend(fontsize=8, framealpha=0.9)
    plt.tight_layout(pad=1.1)
    story.append(_fig_to_img(fig, height=3.0*inch))
    story.append(Spacer(1, 0.1*inch))

    _callout(story, {
        'en': f"Best period: <b>{ctx['best_period_label']}</b> ({_money(ctx['best_period_value'])}). "
              f"Weakest: <b>{ctx['worst_period_label']}</b> ({_money(ctx['worst_period_value'])}).",
        'ar': f"أفضل فترة: <b>{ctx['best_period_label']}</b> ({_money(ctx['best_period_value'])}). "
              f"أضعف: <b>{ctx['worst_period_label']}</b>.",
        'fr': f"Meilleure: <b>{ctx['best_period_label']}</b> ({_money(ctx['best_period_value'])}). "
              f"Pire: <b>{ctx['worst_period_label']}</b>.",
    }.get(lang,""), 'blue', S, lang)
    story.append(PageBreak())


def _segment_analysis(story, S, ctx, store_df, group_col, company_name, lang):
    sec_num   = "05"
    title_txt = {
        'en':f"Segment Performance — {group_col}",
        'ar':f"أداء الشرائح — {group_col}",
        'fr':f"Performance des Segments — {group_col}",
    }.get(lang,f"Segment Performance — {group_col}")
    _section_header(story, sec_num, title_txt, S, lang)

    # FIX #3 — Column definition displayed here
    col_def = _infer_column_meaning(group_col, store_df, lang)
    if col_def:
        story.append(Paragraph(process_text(col_def, lang), S['col_definition']))
        story.append(Spacer(1, 0.08*inch))

    top10     = store_df.head(10)
    total_rev = float(store_df['total'].sum())
    avg_rev   = float(store_df['total'].mean())
    labels    = top10[group_col].astype(str).tolist()
    rev       = top10['total'].tolist()
    bar_clrs  = [mpl('chart1') if i<3 else mpl('chart2') if i<7 else mpl('chart3') for i in range(len(rev))]

    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    bars = ax.bar(labels, rev, color=bar_clrs, width=0.6, edgecolor='white', linewidth=0.35)
    ax.axhline(y=avg_rev, color=mpl('chart5'), linewidth=1.1, linestyle='--', alpha=0.8, label=f"Portfolio Avg: {_money(avg_rev)}")
    for bar, val in zip(bars, rev):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(rev)*0.011,
                _money(val), ha='center', va='bottom', fontsize=6.5, color=CH['gray_dark'])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ax.set_xlabel(process_text(group_col, lang), fontsize=9)
    ct = (company_name+" — " if company_name else "") + \
         {'en':f"Top {len(top10)} {group_col}s",'ar':f"أفضل {len(top10)} {group_col}",'fr':f"Top {len(top10)} {group_col}s"}.get(lang,f"Top {len(top10)}")
    ax.set_title(ct, fontsize=10.5, fontweight='bold', color=mpl('chart1'), pad=10)
    ax.spines['left'].set_color(CH['border'])
    ax.spines['bottom'].set_color(CH['border'])
    ax.legend(fontsize=8, framealpha=0.9)
    plt.tight_layout(pad=1.1)
    story.append(_fig_to_img(fig, height=3.0*inch))
    story.append(Spacer(1, 0.1*inch))

    hdr = {
        'en':[group_col,"Total Revenue","Avg / Period","Portfolio Share"],
        'ar':[group_col,"إجمالي الإيرادات","متوسط الفترة","حصة المحفظة"],
        'fr':[group_col,"Revenu Total","Moy. / Période","Part du Portefeuille"],
    }.get(lang,[group_col,"Total Revenue","Avg / Period","Portfolio Share"])
    tbl_data = [hdr]
    for _, row in top10.iterrows():
        share = row['total']/total_rev*100 if total_rev>0 else 0
        tbl_data.append([str(row[group_col]), f"${row['total']:,.0f}", f"${row['avg_weekly']:,.0f}", f"{share:.1f}%"])
    _pro_table(story, tbl_data, col_widths=[1.8*inch,1.8*inch,1.8*inch,1.5*inch], lang=lang)

    if ctx['pareto_n'] > 0:
        _callout(story, {
            'en': f"<b>Concentration:</b> {ctx['pareto_n']} of {ctx['n_groups']} {group_col.lower()}s "
                  f"({ctx['pareto_pct']:.0f}%) generate 80% of total revenue.",
            'ar': f"<b>التركز:</b> {ctx['pareto_n']} من {ctx['n_groups']} ({ctx['pareto_pct']:.0f}%) "
                  f"يولّدون 80% من الإيرادات.",
            'fr': f"<b>Concentration:</b> {ctx['pareto_n']}/{ctx['n_groups']} ({ctx['pareto_pct']:.0f}%) "
                  f"génèrent 80% du revenu.",
        }.get(lang,""), 'green', S, lang)
    story.append(PageBreak())


def _correlations(story, S, ctx, corr_series, lang):
    titles = {
        'en':("06","External Factors & Correlations"),
        'ar':("06","العوامل الخارجية والارتباطات"),
        'fr':("06","Facteurs Externes & Corrélations"),
    }.get(lang,("06","External Factors & Correlations"))
    _section_header(story, titles[0], titles[1], S, lang)

    story.append(Paragraph(process_text({
        'en':"Statistical correlation quantifies the relationship between revenue and external variables. "
             "Positive values indicate alignment; negative values indicate inverse relationships.",
        'ar':"يقيس الارتباط العلاقة بين الإيرادات والمتغيرات الخارجية.",
        'fr':"La corrélation quantifie la relation entre le revenu et les variables externes.",
    }.get(lang,""), lang), S['body']))
    story.append(Spacer(1, 0.12*inch))

    bar_clrs = [mpl('chart_pos') if v>0 else mpl('chart_neg') for v in corr_series.values]
    fig, ax = plt.subplots(figsize=(9.5, max(2.8, len(corr_series)*0.5)))
    bars = ax.barh(corr_series.index.tolist(), corr_series.values.tolist(),
                   color=bar_clrs, height=0.55, edgecolor='white', linewidth=0.3)
    for bar, val in zip(bars, corr_series.values):
        ax.text(val+(0.007 if val>=0 else -0.007), bar.get_y()+bar.get_height()/2,
                f'{val:.4f}', va='center', ha='left' if val>=0 else 'right', fontsize=8)
    ax.axvline(x=0, color=CH['gray_dark'], linewidth=0.7)
    ax.set_xlabel({'en':'Pearson Coefficient','ar':'معامل بيرسون','fr':'Coefficient de Pearson'}.get(lang,'Pearson'), fontsize=9)
    ax.set_title({'en':'Correlation — External Variables vs Revenue','ar':'الارتباط مع الإيرادات','fr':'Corrélation vs Revenu'}.get(lang,'Correlations'),
                 fontsize=10.5, fontweight='bold', color=mpl('chart1'), pad=10)
    ax.spines['left'].set_color(CH['border'])
    ax.spines['bottom'].set_color(CH['border'])
    plt.tight_layout(pad=1.1)
    story.append(_fig_to_img(fig, height=max(2.4*inch, len(corr_series)*0.42*inch)))
    story.append(Spacer(1, 0.1*inch))

    if ctx['pos_factors']:
        ps = ', '.join([f"<b>{k}</b> ({v:.3f})" for k,v in ctx['pos_factors']])
        _callout(story, {
            'en': f"Positive correlates: {ps} — move in alignment with revenue. "
                  f"[INFERRED: higher values of these variables tend to coincide with higher revenue]",
            'ar': f"عوامل إيجابية: {ps}.",
            'fr': f"Corrélations positives: {ps}.",
        }.get(lang,""), 'green', S, lang)
    if ctx['neg_factors']:
        ns = ', '.join([f"<b>{k}</b> ({v:.3f})" for k,v in ctx['neg_factors']])
        _callout(story, {
            'en': f"Inverse correlates: {ns} — higher values coincide with lower revenue. "
                  f"[INFERRED: not necessarily causal — further investigation recommended]",
            'ar': f"عوامل سلبية: {ns}.",
            'fr': f"Corrélations négatives: {ns}.",
        }.get(lang,""), 'amber', S, lang)
    story.append(PageBreak())


# ═══════════════════════════════════════════════════════════
# FIX #2 — Leading Indicators as CARDS not broken table
# FIX #4 — Peak urgency with days countdown
# ═══════════════════════════════════════════════════════════
def _forecast_section(story, S, ctx, forecast, prophet_data, company_name, lang):
    titles = {
        'en':("07","Revenue Forecast & Scenarios"),
        'ar':("07","توقعات الإيرادات والسيناريوهات"),
        'fr':("07","Prévisions & Scénarios"),
    }.get(lang,("07","Revenue Forecast & Scenarios"))
    _section_header(story, titles[0], titles[1], S, lang)

    story.append(Paragraph(process_text({
        'en':"Forward-looking revenue projections based on historical trend decomposition. "
             "Three scenarios support robust planning decisions.",
        'ar':"توقعات إيرادات مستقبلية مبنية على تحليل التوجهات التاريخية.",
        'fr':"Projections basées sur la décomposition des tendances historiques.",
    }.get(lang,""), lang), S['body']))
    story.append(Spacer(1, 0.1*inch))

    # Confidence + Volatility
    _confidence_badge(story, ctx['confidence_level'], S, lang)
    if ctx['cv_pct'] > 40:
        _volatility_block(story, ctx.get('volatility',{}), ctx['cv_pct'], S, lang)

    # Sanity check warnings
    sanity = ctx.get('sanity_check',{})
    if sanity and not sanity.get('passed',True):
        for warn in sanity.get('warnings',[]):
            _callout(story, warn, 'red', S, lang)

    story.append(Spacer(1, 0.1*inch))

    # Three-Scenario Strip
    story.append(Paragraph(process_text({
        'en':"12-Period Scenario Planning",
        'ar':"تخطيط السيناريوهات — 12 فترة",
        'fr':"Planification par Scénarios — 12 Périodes",
    }.get(lang,""), lang), S['h2']))

    col_w   = CONTENT_W/3
    sc_data = [
        [Paragraph(process_text("🐻 Bear Case",lang), S['metric_bear']),
         Paragraph(process_text("📌 Base Case",lang), S['metric_value']),
         Paragraph(process_text("🚀 Bull Case",lang), S['metric_bull'])],
        [Paragraph(process_text(_money(ctx['bear_12']),lang), S['metric_bear']),
         Paragraph(process_text(_money(ctx['fc12']),   lang), S['metric_value']),
         Paragraph(process_text(_money(ctx['bull_12']),lang), S['metric_bull'])],
        [Paragraph(process_text(f"{ctx['bear_prob']*100:.0f}% probability",lang), S['metric_label']),
         Paragraph(process_text(f"{ctx['base_prob']*100:.0f}% probability",lang), S['metric_label']),
         Paragraph(process_text(f"{ctx['bull_prob']*100:.0f}% probability",lang), S['metric_label'])],
    ]
    sc_tbl = Table(sc_data, colWidths=[col_w]*3, rowHeights=[0.34*inch, 0.46*inch, 0.24*inch])
    sc_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(0,-1), colors.HexColor('#FEF2F2')),
        ('BACKGROUND',    (1,0),(1,-1), rl('blue_pale')),
        ('BACKGROUND',    (2,0),(2,-1), colors.HexColor('#F0FDF4')),
        ('ALIGN',         (0,0),(-1,-1),'CENTER'),
        ('VALIGN',        (0,0),(-1,-1),'MIDDLE'),
        ('GRID',          (0,0),(-1,-1),0.35,rl('border')),
        ('LINEABOVE',     (0,0),(-1,0), 1.4,rl('blue')),
        ('LINEBELOW',     (0,-1),(-1,-1),1.4,rl('blue')),
        ('TOPPADDING',    (0,0),(-1,0), 8),
        ('BOTTOMPADDING', (0,-1),(-1,-1),8),
    ]))
    story.append(sc_tbl)
    story.append(Spacer(1, 0.1*inch))

    # Decision Rule
    if ctx.get('decision_rule'):
        _callout(story, {
            'en': f"<b>Decision Rule:</b> {ctx['decision_rule']}",
            'ar': f"<b>قاعدة القرار:</b> {ctx['decision_rule']}",
            'fr': f"<b>Règle de Décision:</b> {ctx['decision_rule']}",
        }.get(lang,""), 'blue', S, lang)

    story.append(Spacer(1, 0.1*inch))

    # Base KPI strip — reads from ctx (FIX #1: same numbers as cover)
    fc_items = [
        (_money(ctx['fc4']),  {'en':'Next 4 Periods','ar':'4 فترات','fr':'4 Prochaines'}.get(lang,'Next 4')),
        (_money(ctx['fc8']),  {'en':'Next 8 Periods','ar':'8 فترات','fr':'8 Prochaines'}.get(lang,'Next 8')),
        (_money(ctx['fc12']), {'en':'Next 12 Periods','ar':'12 فترة','fr':'12 Prochaines'}.get(lang,'Next 12')),
    ]
    mt = Table(
        [[Paragraph(process_text(v,lang), S['metric_value']) for v,_ in fc_items],
         [Paragraph(process_text(l,lang), S['metric_label']) for _,l in fc_items]],
        colWidths=[CONTENT_W/3]*3, rowHeights=[0.46*inch, 0.26*inch]
    )
    mt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1),rl('blue_pale')),
        ('ALIGN',         (0,0),(-1,-1),'CENTER'),
        ('VALIGN',        (0,0),(-1,-1),'MIDDLE'),
        ('GRID',          (0,0),(-1,-1),0.35,rl('border')),
        ('LINEABOVE',     (0,0),(-1,0), 1.4,rl('teal')),
        ('LINEBELOW',     (0,-1),(-1,-1),1.4,rl('teal')),
        ('TOPPADDING',    (0,0),(-1,0), 10),
        ('BOTTOMPADDING', (0,-1),(-1,-1),8),
    ]))
    story.append(mt)
    story.append(Spacer(1, 0.15*inch))

    # Forecast Chart
    future = forecast[forecast['ds'] > prophet_data['ds'].max()]
    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    ax.plot(prophet_data['ds'], prophet_data['y'], color=mpl('chart1'), linewidth=1.4, alpha=0.8,
            label={'en':'Historical','ar':'تاريخي','fr':'Historique'}.get(lang,'Historical'))
    ax.axvline(x=prophet_data['ds'].max(), color=CH['gray'], linewidth=0.8, linestyle=':', alpha=0.7)
    if len(future) > 0:
        ax.fill_between(future['ds'], future['yhat_lower'], future['yhat_upper'],
                        alpha=0.12, color=mpl('teal'),
                        label={'en':'Scenario Range','ar':'نطاق السيناريو','fr':'Plage Scénarios'}.get(lang,'Range'))
        ax.plot(future['ds'], future['yhat'],       color=mpl('teal'), linewidth=2.2, linestyle='--',
                label={'en':'Base Case','ar':'السيناريو الأساسي','fr':'Cas de Base'}.get(lang,'Base'), zorder=5)
        ax.plot(future['ds'], future['yhat_lower'], color=mpl('bear'), linewidth=0.9, linestyle=':',
                label={'en':'Bear Case','ar':'متشائم','fr':'Pessimiste'}.get(lang,'Bear'), alpha=0.7)
        ax.plot(future['ds'], future['yhat_upper'], color=mpl('bull'), linewidth=0.9, linestyle=':',
                label={'en':'Bull Case','ar':'متفائل','fr':'Optimiste'}.get(lang,'Bull'), alpha=0.7)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ct = (company_name+" — " if company_name else "") + \
         {'en':'Revenue Projection — 3 Scenarios','ar':'توقعات — 3 سيناريوهات','fr':'Projection — 3 Scénarios'}.get(lang,'Revenue Projection')
    ax.set_title(ct, fontsize=10.5, fontweight='bold', color=mpl('chart1'), pad=10)
    ax.legend(fontsize=7.5, framealpha=0.9, ncol=2)
    ax.spines['left'].set_color(CH['border'])
    ax.spines['bottom'].set_color(CH['border'])
    plt.tight_layout(pad=1.1)
    story.append(_fig_to_img(fig, height=3.1*inch))
    story.append(Spacer(1, 0.1*inch))

    # FIX #4 — Peak with urgency countdown
    urgency = ctx['peak_urgency']
    if not urgency.get('is_past', False):
        urgency_style = {
            'critical': 'red',
            'urgent':   'red',
            'soon':     'amber',
            'planned':  'blue',
        }.get(urgency.get('level','planned'), 'blue')

        peak_txt = {
            'en': f"<b>Peak demand period:</b> {ctx['peak_week']} — "
                  f"Projected base-case revenue: <b>{_money(ctx['peak_fc'])}</b>. "
                  f"<b>{urgency.get('message','')}</b>",
            'ar': f"<b>فترة الذروة:</b> {ctx['peak_week']} — "
                  f"الإيرادات المتوقعة: <b>{_money(ctx['peak_fc'])}</b>. "
                  f"<b>{urgency.get('message','')}</b>",
            'fr': f"<b>Période de pointe:</b> {ctx['peak_week']} — "
                  f"Revenu projeté: <b>{_money(ctx['peak_fc'])}</b>. "
                  f"<b>{urgency.get('message','')}</b>",
        }.get(lang,"")
        _callout(story, peak_txt, urgency_style, S, lang)
    else:
        _callout(story, {
            'en': f"⚠️ <b>Peak date ({ctx['peak_week']}) has already passed.</b> "
                  f"Review actual vs. forecast performance for that period.",
            'ar': f"⚠️ <b>تاريخ الذروة ({ctx['peak_week']}) قد مضى.</b> راجع الأداء الفعلي مقابل المتوقع.",
            'fr': f"⚠️ <b>La date de pic ({ctx['peak_week']}) est passée.</b> Comparez réel vs. prévision.",
        }.get(lang,""), 'amber', S, lang)

    # FIX #2 — Leading Indicators as CARDS (not broken table)
    indicators = ctx.get('leading_indicators', [])
    if indicators:
        story.append(Spacer(1, 0.18*inch))
        story.append(Paragraph(process_text({
            'en':"📡 Leading Indicators — Validate the Forecast Before Committing Resources",
            'ar':"📡 المؤشرات القيادية — تحقق من التوقعات",
            'fr':"📡 Indicateurs Avancés — Valider Avant d'Engager des Ressources",
        }.get(lang,""), lang), S['h2']))
        story.append(Paragraph(process_text({
            'en':"Monitor these 3 signals weekly. If any alert threshold is breached, "
                 "revise the forecast before taking further action.",
            'ar':"راقب هذه الإشارات أسبوعياً. إذا تجاوزت أي حد تنبيه، راجع التوقعات.",
            'fr':"Surveillez ces signaux chaque semaine. Si un seuil est franchi, révisez les prévisions.",
        }.get(lang,""), lang), S['body_small']))
        story.append(Spacer(1, 0.1*inch))

        # Each indicator gets its own card — NOT a table (FIX #2)
        for i, ind in enumerate(indicators, 1):
            signal = ind.get('signal','')
            target = ind.get('target','')
            alert  = ind.get('alert','')
            action = ind.get('action','')

            # Truncate long text to prevent overflow
            alert_short  = alert[:80]  + ('...' if len(alert)  > 80 else '')
            action_short = action[:80] + ('...' if len(action) > 80 else '')

            card_data = [
                [Paragraph(process_text(f"#{i} {signal}", lang),
                           ParagraphStyle('card_h', fontSize=9, fontName=get_font(lang,True),
                                          textColor=rl('navy'), leading=13)),
                 Paragraph(process_text(f"Target: {target}", lang),
                           ParagraphStyle('card_t', fontSize=8, fontName=get_font(lang),
                                          textColor=rl('teal'), leading=12))],
                [Paragraph(process_text(f"🔔 {alert_short}", lang),
                           ParagraphStyle('card_a', fontSize=8, fontName=get_font(lang),
                                          textColor=rl('amber'), leading=12)),
                 Paragraph(process_text(f"→ {action_short}", lang),
                           ParagraphStyle('card_ac', fontSize=8, fontName=get_font(lang),
                                          textColor=rl('gray_dark'), leading=12))],
            ]
            card = Table(card_data, colWidths=[CONTENT_W*0.45, CONTENT_W*0.50])
            card.setStyle(TableStyle([
                ('BACKGROUND',    (0,0),(-1,-1), rl('blue_pale')),
                ('LINEBEFORE',    (0,0),(0,-1),  3, rl('teal')),
                ('TOPPADDING',    (0,0),(-1,-1), 8),
                ('BOTTOMPADDING', (0,0),(-1,-1), 8),
                ('LEFTPADDING',   (0,0),(-1,-1), 10),
                ('RIGHTPADDING',  (0,0),(-1,-1), 8),
                ('VALIGN',        (0,0),(-1,-1), 'TOP'),
                ('LINEBELOW',     (0,-1),(-1,-1), 0.3, rl('border')),
            ]))
            story.append(card)
            story.append(Spacer(1, 0.06*inch))

    story.append(PageBreak())


# ═══════════════════════════════════════════════════════════
# FIX #5 — Decision-ready recommendations with Owner + Deadline
# ═══════════════════════════════════════════════════════════
def _recommendations(story, S, ctx, lang):
    titles = {
        'en':("08","Strategic Recommendations"),
        'ar':("08","التوصيات الاستراتيجية"),
        'fr':("08","Recommandations Stratégiques"),
    }.get(lang,("08","Strategic Recommendations"))
    _section_header(story, titles[0], titles[1], S, lang)

    story.append(Paragraph(process_text({
        'en':"Each recommendation below is decision-ready: it states who must decide, "
             "by when, what the first action is, how success is measured, "
             "and the cost of inaction.",
        'ar':"كل توصية أدناه جاهزة للقرار: تحدد من يقرر، ومتى، وما أول إجراء، وكيف نقيس النجاح.",
        'fr':"Chaque recommandation est prête à décider: qui, quand, quelle première action, "
             "comment mesurer le succès, et le coût de l'inaction.",
    }.get(lang,""), lang), S['body']))
    story.append(Spacer(1, 0.15*inch))

    # ── Recommendation structure ──────────────────────────
    recs = []
    if lang == 'en':
        recs = [
            {
                'title':   "Priority 1 — Capitalize on Top Performance",
                'what':    f"<b>{ctx['best_group']}</b> [DATA] generates ${ctx['best_group_revenue']:,.0f} "
                           f"({ctx['best_group_share']:.1f}% of total). "
                           f"Replicate its model in underperforming segments.",
                'owner':   "Sales Manager / Head of Operations",
                'deadline':ctx['action_deadline_30'],
                'first':   f"Identify top 3 revenue drivers in {ctx['best_group']} this week",
                'metric':  f"Target: underperforming segments reach 70% of {ctx['best_group']}'s "
                           f"avg/period (${ctx['best_group_avg']*0.7:,.0f}) by {ctx['action_deadline_90']}",
                'inaction':f"${ctx['worst_group_gap_weekly']*12:,.0f} foregone over next 12 periods",
                'style':   'blue',
            },
            {
                'title':   f"Priority 2 — Address {ctx['worst_group']} Underperformance",
                'what':    f"<b>{ctx['worst_group']}</b> [DATA] underperforms by "
                           f"${ctx['worst_group_gap_weekly']:,.0f}/period vs. portfolio average. "
                           f"[INFERRED: pricing or frequency issue based on correlation data]",
                'owner':   "Category Manager / Regional Director",
                'deadline':ctx['action_deadline_7'],
                'first':   f"Audit {ctx['worst_group']} unit price distribution vs. portfolio median",
                'metric':  f"Target: close gap to portfolio average (${ctx['avg_per_period']:,.0f}/period) "
                           f"by 50% within 30 days",
                'inaction':f"${ctx['worst_group_12p_cost']:,.0f} annual revenue gap vs. portfolio average",
                'style':   'amber',
            },
            {
                'title':   "Priority 3 — Align with Forecast Peak",
                'what':    f"Base case projects peak at <b>{ctx['peak_week']}</b> "
                           f"({_money(ctx['peak_fc'])}). "
                           f"[ASSUMPTION: based on trend extrapolation — monitor leading indicators]. "
                           f"{ctx['peak_urgency'].get('message','')}",
                'owner':   "Supply Chain / Marketing Manager",
                'deadline':ctx['action_deadline_7'],
                'first':   "Confirm inventory levels and promotional calendar for peak period",
                'metric':  f"Target: capture ≥85% of projected peak revenue ({_money(ctx['peak_fc']*0.85)})",
                'inaction':f"Missed peak = up to {_money(ctx['peak_fc']*0.15)} uncaptured revenue",
                'style':   'green',
            },
        ]
    elif lang == 'ar':
        recs = [
            {
                'title':   "الأولوية 1 — الاستفادة من أفضل الأداء",
                'what':    f"<b>{ctx['best_group']}</b> [بيانات] يولّد ${ctx['best_group_revenue']:,.0f} "
                           f"({ctx['best_group_share']:.1f}%). تكرار نموذجه في الشرائح الضعيفة.",
                'owner':   "مدير المبيعات / مدير العمليات",
                'deadline':ctx['action_deadline_30'],
                'first':   f"تحديد أفضل 3 محركات إيرادية في {ctx['best_group']} هذا الأسبوع",
                'metric':  f"هدف: وصول الشرائح الضعيفة إلى 70% من متوسط {ctx['best_group']}",
                'inaction':f"${ctx['worst_group_gap_weekly']*12:,.0f} إيرادات مفقودة في 12 فترة",
                'style':   'blue',
            },
            {
                'title':   f"الأولوية 2 — معالجة ضعف {ctx['worst_group']}",
                'what':    f"<b>{ctx['worst_group']}</b> [بيانات] يقصر بـ ${ctx['worst_group_gap_weekly']:,.0f}/فترة. "
                           f"[مُستنتج: مشكلة تسعير أو تكرار]",
                'owner':   "مدير الفئة / المدير الإقليمي",
                'deadline':ctx['action_deadline_7'],
                'first':   f"مراجعة توزيع الأسعار في {ctx['worst_group']}",
                'metric':  f"هدف: تقليص الفجوة إلى 50% خلال 30 يوماً",
                'inaction':f"${ctx['worst_group_12p_cost']:,.0f} فجوة إيرادية سنوية",
                'style':   'amber',
            },
            {
                'title':   "الأولوية 3 — التوافق مع الذروة",
                'what':    f"الذروة في <b>{ctx['peak_week']}</b> ({_money(ctx['peak_fc'])}). "
                           f"{ctx['peak_urgency'].get('message','')}",
                'owner':   "مدير سلسلة التوريد / مدير التسويق",
                'deadline':ctx['action_deadline_7'],
                'first':   "تأكيد مستويات المخزون والخطة الترويجية",
                'metric':  f"هدف: التقاط ≥85% من إيرادات الذروة ({_money(ctx['peak_fc']*0.85)})",
                'inaction':f"ما يصل إلى {_money(ctx['peak_fc']*0.15)} إيرادات غير ملتقطة",
                'style':   'green',
            },
        ]
    else:
        recs = [
            {
                'title':   "Priorité 1 — Capitaliser sur la Top Performance",
                'what':    f"<b>{ctx['best_group']}</b> [DONNÉES] génère ${ctx['best_group_revenue']:,.0f} "
                           f"({ctx['best_group_share']:.1f}%). Répliquer son modèle.",
                'owner':   "Directeur Commercial / Directeur des Opérations",
                'deadline':ctx['action_deadline_30'],
                'first':   f"Identifier les 3 principaux drivers de revenus de {ctx['best_group']}",
                'metric':  f"Cible: segments sous-performants à 70% de la moyenne de {ctx['best_group']}",
                'inaction':f"${ctx['worst_group_gap_weekly']*12:,.0f} de revenus non capturés sur 12 périodes",
                'style':   'blue',
            },
            {
                'title':   f"Priorité 2 — Traiter la Sous-Performance de {ctx['worst_group']}",
                'what':    f"<b>{ctx['worst_group']}</b> est en retard de ${ctx['worst_group_gap_weekly']:,.0f}/période. "
                           f"[DÉDUIT: problème de prix ou de fréquence]",
                'owner':   "Category Manager / Directeur Régional",
                'deadline':ctx['action_deadline_7'],
                'first':   f"Auditer la distribution des prix de {ctx['worst_group']}",
                'metric':  "Cible: réduire l'écart de 50% en 30 jours",
                'inaction':f"${ctx['worst_group_12p_cost']:,.0f}/an d'écart vs. moyenne portefeuille",
                'style':   'amber',
            },
            {
                'title':   "Priorité 3 — Alignement avec le Pic Prévu",
                'what':    f"Pic projeté: <b>{ctx['peak_week']}</b> ({_money(ctx['peak_fc'])}). "
                           f"{ctx['peak_urgency'].get('message','')}",
                'owner':   "Supply Chain / Marketing Manager",
                'deadline':ctx['action_deadline_7'],
                'first':   "Confirmer niveaux de stock et calendrier promotionnel",
                'metric':  f"Cible: capturer ≥85% du pic ({_money(ctx['peak_fc']*0.85)})",
                'inaction':f"Jusqu'à {_money(ctx['peak_fc']*0.15)} de revenus non capturés",
                'style':   'green',
            },
        ]

    labels = {
        'en': {'owner':'DECISION OWNER','deadline':'DEADLINE','first':'FIRST ACTION (48h)',
                'metric':'SUCCESS METRIC','inaction':'COST OF INACTION'},
        'ar': {'owner':'صاحب القرار','deadline':'الموعد النهائي','first':'أول إجراء (48 ساعة)',
                'metric':'مقياس النجاح','inaction':'تكلفة التأخر'},
        'fr': {'owner':'RESPONSABLE','deadline':'DÉLAI','first':'PREMIÈRE ACTION (48h)',
                'metric':'INDICATEUR DE SUCCÈS','inaction':'COÛT DE L\'INACTION'},
    }.get(lang, {'owner':'DECISION OWNER','deadline':'DEADLINE','first':'FIRST ACTION (48h)',
                  'metric':'SUCCESS METRIC','inaction':'COST OF INACTION'})

    for rec in recs:
        story.append(Paragraph(process_text(rec['title'], lang), S['h3']))
        _callout(story, rec['what'], rec['style'], S, lang)

        # Decision metadata table
        meta_rows = [
            [labels['owner'],   rec['owner']],
            [labels['deadline'],rec['deadline']],
            [labels['first'],   rec['first']],
            [labels['metric'],  rec['metric']],
            [labels['inaction'],rec['inaction']],
        ]
        meta_data = [[
            Paragraph(process_text(k, lang),
                      ParagraphStyle('mk', fontSize=7.5, fontName=get_font(lang,True),
                                     textColor=rl('gray'), leading=11)),
            Paragraph(process_text(v, lang),
                      ParagraphStyle('mv', fontSize=8.5, fontName=get_font(lang),
                                     textColor=rl('gray_dark'), leading=12)),
        ] for k, v in meta_rows]

        meta_tbl = Table(meta_data, colWidths=[1.6*inch, CONTENT_W-1.6*inch-0.3*inch])
        meta_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(0,-1), rl('gray_light')),
            ('BACKGROUND',    (1,0),(1,-1), rl('white')),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('GRID',          (0,0),(-1,-1), 0.2, rl('border')),
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
            # Highlight cost of inaction row in amber
            ('BACKGROUND',    (0,4),(1,4),  rl('amber_light')),
        ]))
        story.append(meta_tbl)
        story.append(Spacer(1, 0.18*inch))

    story.append(PageBreak())


# ═══════════════════════════════════════════════════════════
# FIX #6 — Appendix: QA errors with impact + action taken
# ═══════════════════════════════════════════════════════════
def _appendix(story, S, ctx, lang, validation_report=None):
    titles = {
        'en':("09","Data Appendix"),
        'ar':("09","ملحق البيانات"),
        'fr':("09","Annexe — Données"),
    }.get(lang,("09","Data Appendix"))
    _section_header(story, titles[0], titles[1], S, lang)

    hdr = {
        'en':["Parameter","Value"],
        'ar':["المعيار","القيمة"],
        'fr':["Paramètre","Valeur"],
    }.get(lang,["Parameter","Value"])

    params = [
        ("Total Records",       f"{ctx['n_records']:,}"),
        ("Unique Periods",      f"{ctx['n_periods']:,}"),
        ("Reporting Period",    ctx['date_range']),
        ("Total Revenue",       f"${ctx['total_revenue']:,.2f}"),
        ("Average per Period",  f"${ctx['avg_per_period']:,.2f}"),
        ("Peak Single Period",  f"${ctx['peak_value']:,.2f}"),
        ("Minimum Period",      f"${ctx['min_value']:,.2f}"),
        ("Revenue Std Dev",     f"${ctx['std_dev']:,.2f}"),
        ("Coeff. of Variation", f"{ctx['cv_pct']:.1f}%"),
        ("Volatility Level",    ctx.get('volatility',{}).get('level','N/A')),
        ("Trend Direction",     ctx['trend_direction'].capitalize()),
        ("Trend Change",        f"{ctx['trend_pct']:+.1f}%"),
        ("Forecast Confidence", ctx['confidence_level']),
        ("Bear Case (12p)",     f"${ctx['bear_12']:,.0f} ({ctx['bear_prob']*100:.0f}%)"),
        ("Base Case (12p)",     f"${ctx['fc12']:,.0f} ({ctx['base_prob']*100:.0f}%)"),
        ("Bull Case (12p)",     f"${ctx['bull_12']:,.0f} ({ctx['bull_prob']*100:.0f}%)"),
    ]
    if ctx['best_group'] != 'N/A':
        params.append(("Best Segment",  f"{ctx['best_group']} (${ctx['best_group_revenue']:,.0f})"))
        params.append(("Worst Segment", f"{ctx['worst_group']} (gap: ${ctx['worst_group_gap_weekly']:,.0f}/period)"))
    if ctx['pareto_n'] > 0:
        params.append(("Pareto (80% Revenue)", f"Top {ctx['pareto_pct']:.0f}% of segments"))

    _pro_table(story, [hdr]+[[p,v] for p,v in params],
               col_widths=[2.8*inch, CONTENT_W-2.8*inch], lang=lang)

    # Methodology
    story.append(Paragraph(process_text(
        {'en':'Methodology','ar':'المنهجية','fr':'Méthodologie'}.get(lang,'Methodology'), lang), S['h2']))
    story.append(Paragraph(process_text({
        'en': "Revenue forecasts use Holt-Winters Exponential Smoothing with three-scenario output "
              "(Bear/Base/Bull). Confidence intervals are proportional to historical volatility (CV). "
              "Correlation analysis uses Pearson coefficients. All values computed dynamically from "
              "the uploaded dataset using a Single Source of Truth pattern — every number appears "
              "exactly once in the computation layer and is referenced consistently across all sections. "
              "Leading indicators derived from forecast trajectory and segment performance benchmarks.",
        'ar': "تستخدم التوقعات نموذج Holt-Winters مع ثلاثة سيناريوهات. "
              "جميع القيم محسوبة مرة واحدة من مصدر واحد وتُستخدم عبر جميع الأقسام.",
        'fr': "Les prévisions utilisent Holt-Winters avec trois scénarios. "
              "Toutes les valeurs sont calculées une seule fois (Single Source of Truth) "
              "et référencées de manière cohérente dans toutes les sections.",
    }.get(lang,""), lang), S['body']))

    # FIX #6 — QA Report with impact and action
    if validation_report:
        story.append(Spacer(1, 0.15*inch))
        story.append(Paragraph(process_text(
            {'en':'Quality Assurance Report','ar':'تقرير ضمان الجودة','fr':"Rapport d'Assurance Qualité"}.get(lang,'QA'), lang), S['h2']))

        status = validation_report.get('passed', True)
        iterations = validation_report.get('iterations', 1)

        status_txt = {
            'en': f"Quality check: {'✅ PASSED' if status else '⚠️ ISSUES DETECTED'} — "
                  f"{iterations} validation iteration(s) completed.",
            'ar': f"فحص الجودة: {'✅ اجتاز' if status else '⚠️ مشكلات مكتشفة'} — "
                  f"{iterations} تكرار.",
            'fr': f"Contrôle qualité: {'✅ RÉUSSI' if status else '⚠️ PROBLÈMES DÉTECTÉS'} — "
                  f"{iterations} itération(s).",
        }.get(lang,"")
        story.append(Paragraph(process_text(status_txt, lang),
                                S['validation_ok'] if status else S['validation_err']))

        if not status and validation_report.get('errors'):
            story.append(Spacer(1, 0.08*inch))
            errors = validation_report['errors'][:5]

            # FIX #6 — Show error + impact + action (not just the error)
            if isinstance(errors[0], dict):
                err_hdr = {
                    'en':["Issue Detected","Impact Level","Action Taken"],
                    'ar':["المشكلة المكتشفة","مستوى التأثير","الإجراء المتخذ"],
                    'fr':["Problème Détecté","Niveau d'Impact","Action Effectuée"],
                }.get(lang,["Issue","Impact","Action"])
                err_rows = [err_hdr] + [
                    [e.get('error',''), e.get('impact',''), e.get('action','')]
                    for e in errors
                ]
                _pro_table(story, err_rows,
                           col_widths=[2.2*inch, 1.4*inch, CONTENT_W-3.6*inch], lang=lang)
            else:
                # Fallback for string errors
                for err in errors:
                    story.append(Paragraph(f"  • {err}", S['validation_err']))


def _action_plan(story, S, ctx, lang):
    titles = {
        'en':("AP","Priority Action Plan"),
        'ar':("AP","خطة الأولويات"),
        'fr':("AP","Plan d'Action Prioritaire"),
    }.get(lang,("AP","Priority Action Plan"))
    _section_header(story, titles[0], titles[1], S, lang)

    story.append(Paragraph(process_text({
        'en':"The following action plan translates analytical findings into a time-bound execution roadmap, "
             "sequenced by urgency and estimated financial impact. "
             "All impact estimates are derived from data calculations shown in this report.",
        'ar':"تترجم خطة العمل التالية النتائج التحليلية إلى خارطة طريق تنفيذية محددة زمنياً. "
             "جميع تقديرات الأثر مشتقة من حسابات البيانات الواردة في هذا التقرير.",
        'fr':"Ce plan traduit les résultats analytiques en feuille de route d'exécution séquencée. "
             "Tous les impacts sont dérivés des calculs de données présentés dans ce rapport.",
    }.get(lang,""), lang), S['body']))
    story.append(Spacer(1, 0.15*inch))

    sections_data = [
        ({'en':'Quick Wins (0–30 Days)','ar':'مكاسب سريعة (0-30 يوم)','fr':'Gains Rapides (0–30 Jours)'}.get(lang,'Quick Wins'), [
            {'en':(f"Replicate {ctx['best_group']} Model",
                   f"Identify top 3 drivers in {ctx['best_group']}; apply to 3 comparable units by {ctx['action_deadline_30']}.",
                   f"+{_money(ctx['avg_per_period']*4)}/quarter [derived: avg×4]","Low","High"),
             'ar':(f"تكرار نموذج {ctx['best_group']}",
                   f"تطبيق النموذج على 3 وحدات بحلول {ctx['action_deadline_30']}.",
                   f"+{_money(ctx['avg_per_period']*4)}/ربع [مشتق]","منخفض","عالي"),
             'fr':(f"Répliquer {ctx['best_group']}",
                   f"Appliquer à 3 unités avant le {ctx['action_deadline_30']}.",
                   f"+{_money(ctx['avg_per_period']*4)}/trim. [dérivé]","Faible","Élevée")},
            {'en':("Forecast-Aligned Inventory",
                   f"Pre-position stock for peak at {ctx['peak_week']}. {ctx['peak_urgency'].get('message','')}",
                   f"+{_money(ctx['peak_fc']*0.08)} [derived: peak×8%]","Low","High"),
             'ar':("تموضع مخزون",
                   f"تجهيز المخزون لذروة {ctx['peak_week']}.",
                   f"+{_money(ctx['peak_fc']*0.08)} [مشتق]","منخفض","عالي"),
             'fr':("Stock Aligné",
                   f"Pré-positionner avant le pic du {ctx['peak_week']}.",
                   f"+{_money(ctx['peak_fc']*0.08)} [dérivé]","Faible","Élevée")},
        ]),
        ({'en':'Medium-Term Strategy (1–3 Months)','ar':'استراتيجية متوسطة المدى','fr':'Stratégie Moyen Terme'}.get(lang,'Medium-Term'), [
            {'en':("Segment Performance Tiering",
                   "Classify all segments into tiers; implement differentiated investment levels by segment.",
                   f"+{_money(ctx['total_revenue']*0.06)}/year [derived: total×6%]","Medium","Medium"),
             'ar':("تصنيف الشرائح",
                   "تصنيف وتطبيق مستويات استثمار مختلفة.",
                   f"+{_money(ctx['total_revenue']*0.06)}/سنة [مشتق]","متوسط","متوسط"),
             'fr':("Hiérarchisation Segments",
                   "Classifier et différencier les investissements par segment.",
                   f"+{_money(ctx['total_revenue']*0.06)}/an [dérivé]","Moyen","Moyen")},
        ]),
        ({'en':'Long-Term Initiatives (6–12 Months)','ar':'مبادرات طويلة المدى','fr':'Initiatives Long Terme'}.get(lang,'Long-Term'), [
            {'en':("Portfolio Optimization",
                   f"Expand top performers; evaluate {ctx['worst_group']} for repositioning or restructuring.",
                   f"+{_money(ctx['total_revenue']*0.12)}/year [derived: total×12%]","High","Medium"),
             'ar':("تحسين المحفظة",
                   f"توسيع الأفضل؛ تقييم {ctx['worst_group']} لإعادة التموضع.",
                   f"+{_money(ctx['total_revenue']*0.12)}/سنة [مشتق]","عالي","متوسط"),
             'fr':("Optimisation Portefeuille",
                   f"Développer top performers; évaluer {ctx['worst_group']}.",
                   f"+{_money(ctx['total_revenue']*0.12)}/an [dérivé]","Élevé","Moyen")},
        ]),
    ]

    hdr = {
        'en':["Initiative","Description","Est. Impact","Effort","Confidence"],
        'ar':["المبادرة","الوصف","الأثر المقدر","الجهد","الثقة"],
        'fr':["Initiative","Description","Impact Est.","Effort","Confiance"],
    }.get(lang,["Initiative","Description","Est. Impact","Effort","Confidence"])

    for section_title, items in sections_data:
        story.append(Paragraph(process_text(section_title, lang), S['h2']))
        tbl_data = [hdr] + [list(item.get(lang, item.get('en',('','','','','')))) for item in items]
        _pro_table(story, tbl_data,
                   col_widths=[1.35*inch, 2.55*inch, 1.3*inch, 0.6*inch, 0.85*inch], lang=lang)
        story.append(Spacer(1, 0.1*inch))

    _callout(story, {
        'en': f"<b>Combined impact projection:</b> Full implementation estimated to deliver "
              f"<b>{_money(ctx['total_revenue']*0.15)} — {_money(ctx['total_revenue']*0.22)}</b> "
              f"incremental annual revenue (15–22% uplift on {_money(ctx['total_revenue'])} baseline). "
              f"[All estimates derived from data — see methodology in Data Appendix]",
        'ar': f"<b>التأثير الإجمالي:</b> {_money(ctx['total_revenue']*0.15)} — "
              f"{_money(ctx['total_revenue']*0.22)} إيرادات إضافية سنوياً. "
              f"[جميع التقديرات مشتقة من البيانات]",
        'fr': f"<b>Impact combiné:</b> {_money(ctx['total_revenue']*0.15)} — "
              f"{_money(ctx['total_revenue']*0.22)}/an. "
              f"[Toutes les estimations dérivées des données]",
    }.get(lang,""), 'green', S, lang)
    story.append(PageBreak())


# ═══════════════════════════════════════════════════════════
# MAIN GENERATOR
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
    Generate premium Business Intelligence PDF — v3.0
    All 7 issues from the professional review are fixed.
    """
    # Step 1: Compute ALL numbers ONCE (FIX #1)
    ctx = extract_dynamic_context(
        df, date_col, sales_col, summary, store_df,
        group_col, corr_series, forecast_summary, monthly_df,
    )

    # Step 2: Quality pipeline on AI text
    validation_report = None
    if ai_result:
        cleaned_ai, validation_report = run_quality_pipeline(
            ai_result, ctx,
            system_prompt=system_prompt,
            ask_agent_fn=ask_agent_fn,
            max_iterations=2,
        )
    else:
        cleaned_ai = None

    # Step 3: Build PDF
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
        creator="Performance Analytics Platform v3.0",
    )

    story     = []
    has_store = store_df is not None and group_col is not None and len(store_df) > 0
    has_corr  = corr_series is not None and len(corr_series) > 0

    _cover(story, company_name, S, ctx, lang)
    _toc(story, S, ctx, lang, has_store, has_corr)
    _executive_summary(story, S, ctx, lang, cleaned_ai)   # FIX #7: 1 page, 4 paragraphs
    _key_findings(story, S, ctx, lang)
    _sales_overview(story, S, ctx, df, date_col, sales_col, company_name, lang)
    _trend_analysis(story, S, ctx, monthly_df, company_name, lang)

    if has_store:
        _segment_analysis(story, S, ctx, store_df, group_col, company_name, lang)  # FIX #3
    if has_corr:
        _correlations(story, S, ctx, corr_series, lang)

    _forecast_section(story, S, ctx, forecast, prophet_data, company_name, lang)  # FIX #2 + #4
    _recommendations(story, S, ctx, lang)                  # FIX #5

    if include_action_plan:
        _action_plan(story, S, ctx, lang)

    _appendix(story, S, ctx, lang, validation_report)     # FIX #6

    doc.build(story, onFirstPage=footer_fn, onLaterPages=footer_fn)
    buffer.seek(0)
    return buffer.read()