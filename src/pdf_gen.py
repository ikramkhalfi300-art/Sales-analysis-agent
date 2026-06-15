# src/pdf_gen.py
"""
Premium Business Intelligence Report Generator
- 100% Dynamic: all values extracted from uploaded DataFrame
- Arabic support via arabic_reshaper + python-bidi + Amiri font
- Quality Guardrails: validation + self-correction loop
- No hardcoded values, dates, branch names, or Walmart data
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
    """Download and register Amiri font once — stored in /tmp/"""
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
    """Process text for correct rendering — Arabic gets reshaped + bidi"""
    if lang != "ar" or not ARABIC_AVAILABLE:
        return str(text)
    try:
        reshaped = reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)

def get_font(lang: str, bold: bool = False) -> str:
    """Return correct font name for language"""
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
# CH = hex strings → Matplotlib only
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
}

# C = ReportLab color objects
C = {k: colors.HexColor(v) for k, v in CH.items()}
C['white'] = colors.white
C['black'] = colors.black

def rl(key):
    return C.get(key, colors.HexColor('#1A3A6B'))

def mpl(key):
    return CH.get(key, '#1A3A6B')


# ═══════════════════════════════════════════════════════════
# 3. DYNAMIC DATA EXTRACTION
# ═══════════════════════════════════════════════════════════
def extract_dynamic_context(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    summary: dict,
    store_df,
    group_col,
    corr_series,
    forecast_summary: dict,
    monthly_df: pd.DataFrame,
) -> dict:
    """
    Extract ALL report variables dynamically from the actual DataFrame.
    Never uses hardcoded values. Returns a clean context dict.
    """
    ctx = {}

    # ── Basic stats (all from df directly) ──────────────────
    ctx['total_revenue']   = float(df[sales_col].sum())
    ctx['avg_per_period']  = float(df[sales_col].mean())
    ctx['peak_value']      = float(df[sales_col].max())
    ctx['min_value']       = float(df[sales_col].min())
    ctx['n_records']       = int(len(df))
    ctx['std_dev']         = float(df[sales_col].std())
    ctx['cv_pct']          = round(ctx['std_dev'] / ctx['avg_per_period'] * 100, 1) if ctx['avg_per_period'] > 0 else 0

    # ── Dates (from actual data) ──────────────────────────────
    ctx['date_min']   = str(df[date_col].min().date())
    ctx['date_max']   = str(df[date_col].max().date())
    ctx['date_range'] = f"{ctx['date_min']} to {ctx['date_max']}"
    ctx['n_periods']  = int(df[date_col].nunique())

    # ── Trend (computed from data) ────────────────────────────
    sorted_df   = df.groupby(date_col)[sales_col].sum().reset_index().sort_values(date_col)
    half        = max(1, len(sorted_df) // 2)
    first_half  = float(sorted_df[sales_col].iloc[:half].mean())
    second_half = float(sorted_df[sales_col].iloc[half:].mean())
    trend_pct   = (second_half - first_half) / first_half * 100 if first_half > 0 else 0
    ctx['trend_pct']       = round(trend_pct, 1)
    ctx['trend_direction'] = "growing" if trend_pct > 3 else "declining" if trend_pct < -3 else "stable"

    # ── Period stats ──────────────────────────────────────────
    if len(monthly_df) > 0:
        vals  = monthly_df['total'].tolist()
        months= [str(m) for m in monthly_df['month']]
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

    # ── Segment / Group stats (real names from data) ──────────
    ctx['group_col']   = group_col or 'N/A'
    ctx['n_groups']    = int(summary.get('num_groups', 0))
    ctx['best_group']  = str(summary.get('best_group', 'N/A'))
    ctx['worst_group'] = str(summary.get('worst_group', 'N/A'))

    if store_df is not None and group_col:
        total_rev = store_df['total'].sum()
        ctx['best_group_revenue'] = float(store_df['total'].max())
        ctx['best_group_share']   = round(store_df['total'].max() / total_rev * 100, 1) if total_rev > 0 else 0
        ctx['worst_group_revenue']= float(store_df['total'].min())
        # Pareto
        cum  = store_df['total'].sort_values(ascending=False).cumsum()
        n80  = int((cum <= total_rev * 0.80).sum()) + 1
        ctx['pareto_n']   = n80
        ctx['pareto_pct'] = round(n80 / max(len(store_df), 1) * 100, 1)
    else:
        ctx['best_group_revenue']  = 0
        ctx['best_group_share']    = 0
        ctx['worst_group_revenue'] = 0
        ctx['pareto_n']            = 0
        ctx['pareto_pct']          = 0

    # ── Correlations (real factor names from data) ────────────
    if corr_series is not None and len(corr_series) > 0:
        pos = corr_series[corr_series >  0.1]
        neg = corr_series[corr_series < -0.1]
        ctx['pos_factors'] = [(str(k), round(float(v), 4)) for k,v in pos.items()]
        ctx['neg_factors'] = [(str(k), round(float(v), 4)) for k,v in neg.items()]
    else:
        ctx['pos_factors'] = []
        ctx['neg_factors'] = []

    # ── Forecast ──────────────────────────────────────────────
    ctx['fc4']       = float(forecast_summary.get('next_4_weeks',  0))
    ctx['fc8']       = float(forecast_summary.get('next_8_weeks',  0))
    ctx['fc12']      = float(forecast_summary.get('next_12_weeks', 0))
    ctx['peak_week'] = str(forecast_summary.get('peak_week',       'N/A'))
    ctx['peak_fc']   = float(forecast_summary.get('peak_expected_sales', 0))

    # ── Report generation date ────────────────────────────────
    ctx['report_date'] = pd.Timestamp.now().strftime('%d %B %Y')
    ctx['report_year'] = pd.Timestamp.now().strftime('%Y')

    return ctx


# ═══════════════════════════════════════════════════════════
# 4. QUALITY GUARDRAILS & SELF-CORRECTION
# ═══════════════════════════════════════════════════════════
# Forbidden patterns — any text containing these is flagged
_FORBIDDEN_PATTERNS = [
    r'\bwalmart\b', r'\b2010\b', r'\b2011\b', r'\b2012\b',
    r'\bweekly[_\s]sales\b', r'\bholiday[_\s]flag\b',
    r'\bstore\s+\d+\b(?!.*is)',   # raw "Store 20" without context
    r'\bprophet\b', r'\bfacebook\b',
    r'\b(index|idx|unnamed)\b',
]

def validate_report_data(ai_text: str, ctx: dict) -> dict:
    """
    Quality guardrail: checks AI-generated text against actual data.
    Returns {'passed': bool, 'errors': list[str]}
    """
    errors = []
    text_lower = ai_text.lower()

    # 1. Forbidden static references
    for pattern in _FORBIDDEN_PATTERNS:
        if re.search(pattern, text_lower):
            errors.append(f"Forbidden reference detected: pattern '{pattern}'")

    # 2. Date range check — no dates outside actual data range
    years_in_text = set(re.findall(r'\b(19|20)\d{2}\b', ai_text))
    actual_year_min = int(ctx['date_min'][:4])
    actual_year_max = int(ctx['date_max'][:4])
    for yr in years_in_text:
        yr_int = int(yr)
        if yr_int < actual_year_min or yr_int > int(ctx['report_year']) + 1:
            errors.append(f"Year {yr} is outside actual data range ({actual_year_min}-{actual_year_max})")

    # 3. Revenue magnitude check — mentioned $ figures should be plausible
    dollar_amounts = re.findall(r'\$\s*([\d,\.]+)\s*([MBK]?)', ai_text)
    for amount_str, suffix in dollar_amounts:
        try:
            val = float(amount_str.replace(',', ''))
            if suffix == 'M': val *= 1e6
            elif suffix == 'B': val *= 1e9
            elif suffix == 'K': val *= 1e3
            # Check: mentioned amount shouldn't exceed 2x total revenue
            if val > ctx['total_revenue'] * 2:
                errors.append(f"Amount ${amount_str}{suffix} exceeds 2x total revenue — possible hallucination")
        except ValueError:
            pass

    # 4. Group name check — if a group is mentioned, it should exist in data
    if ctx['best_group'] != 'N/A':
        best_lower = ctx['best_group'].lower()
        worst_lower = ctx['worst_group'].lower()
        if best_lower not in text_lower and worst_lower not in text_lower:
            errors.append("AI text doesn't reference actual segment names from data")

    return {
        'passed': len(errors) == 0,
        'errors': errors,
    }


def self_correct_with_ai(
    ai_text: str,
    errors: list,
    ctx: dict,
    system_prompt: str,
    ask_agent_fn,
) -> str:
    """
    Self-correction loop: sends error report back to AI for rewrite.
    ask_agent_fn: callable(question, system_prompt, history) -> (answer, history)
    """
    if not errors or ask_agent_fn is None:
        return ai_text

    error_report = "\n".join(f"- {e}" for e in errors)
    correction_prompt = f"""
You previously generated a business analysis report, but a quality review found the following errors:

ERRORS FOUND:
{error_report}

ACTUAL DATA FACTS (use ONLY these):
- Date range: {ctx['date_range']}
- Total revenue: ${ctx['total_revenue']:,.2f}
- Average per period: ${ctx['avg_per_period']:,.2f}
- Peak value: ${ctx['peak_value']:,.2f}
- Best performing segment: {ctx['best_group']} (${ctx['best_group_revenue']:,.0f})
- Worst performing segment: {ctx['worst_group']} (${ctx['worst_group_revenue']:,.0f})
- Trend: {ctx['trend_direction']} ({ctx['trend_pct']:+.1f}%)
- 12-period forecast: ${ctx['fc12']:,.0f}

YOUR ORIGINAL TEXT TO CORRECT:
{ai_text}

INSTRUCTIONS:
1. Rewrite the text correcting ALL errors listed above
2. Use ONLY the actual data facts provided
3. Do NOT reference Walmart, 2010, 2011, 2012, or any data not in the facts above
4. Keep the same professional consulting tone and structure
5. Return ONLY the corrected text, no preamble
"""
    try:
        corrected, _ = ask_agent_fn(correction_prompt, system_prompt, [])
        return corrected
    except Exception:
        return ai_text  # fallback to original if correction fails


def run_quality_pipeline(
    ai_text: str,
    ctx: dict,
    system_prompt: str = "",
    ask_agent_fn=None,
    max_iterations: int = 2,
) -> tuple:
    """
    Full quality pipeline with self-correction loop.
    Returns (final_text, validation_report)
    """
    current_text = ai_text
    all_errors   = []

    for iteration in range(max_iterations):
        result = validate_report_data(current_text, ctx)
        if result['passed']:
            break
        all_errors.extend(result['errors'])
        if ask_agent_fn and iteration < max_iterations - 1:
            current_text = self_correct_with_ai(
                current_text, result['errors'], ctx, system_prompt, ask_agent_fn
            )
        else:
            break

    final_validation = validate_report_data(current_text, ctx)
    return current_text, {
        'passed':     final_validation['passed'],
        'errors':     final_validation['errors'],
        'iterations': iteration + 1,
    }


# ═══════════════════════════════════════════════════════════
# 5. CHART UTILITIES
# ═══════════════════════════════════════════════════════════
PAGE_W, PAGE_H = A4
MARGIN    = 0.85 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

def _set_chart_style():
    rcParams['font.family']        = 'sans-serif'
    rcParams['axes.spines.top']    = False
    rcParams['axes.spines.right']  = False
    rcParams['axes.linewidth']     = 0.5
    rcParams['axes.grid']          = True
    rcParams['grid.alpha']         = 0.12
    rcParams['grid.linewidth']     = 0.4
    rcParams['xtick.labelsize']    = 8
    rcParams['ytick.labelsize']    = 8
    rcParams['figure.facecolor']   = 'white'
    rcParams['axes.facecolor']     = 'white'

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
# 6. TYPOGRAPHY
# ═══════════════════════════════════════════════════════════
def build_styles(lang: str = 'en'):
    fn      = get_font(lang, bold=False)
    fn_bold = get_font(lang, bold=True)
    align   = TA_RIGHT if lang == 'ar' else TA_LEFT
    S = {}

    S['cover_eyebrow'] = ParagraphStyle('cover_eyebrow',
        fontSize=8.5, fontName=fn_bold, textColor=rl('blue_mid'),
        alignment=TA_CENTER, spaceAfter=6, leading=12)

    S['cover_title'] = ParagraphStyle('cover_title',
        fontSize=26, fontName=fn_bold, textColor=rl('navy'),
        alignment=TA_CENTER, spaceAfter=10, leading=32)

    S['cover_subtitle'] = ParagraphStyle('cover_subtitle',
        fontSize=13, fontName=fn, textColor=rl('gray_mid'),
        alignment=TA_CENTER, spaceAfter=6, leading=19)

    S['cover_meta_label'] = ParagraphStyle('cover_meta_label',
        fontSize=7.5, fontName=fn_bold, textColor=rl('gray'),
        alignment=align, leading=11)

    S['cover_meta_value'] = ParagraphStyle('cover_meta_value',
        fontSize=10, fontName=fn, textColor=rl('navy'),
        alignment=align, leading=14)

    S['section_label'] = ParagraphStyle('section_label',
        fontSize=8, fontName=fn_bold, textColor=rl('blue_mid'),
        alignment=align, spaceAfter=4, spaceBefore=18, leading=12)

    S['h1'] = ParagraphStyle('h1',
        fontSize=17, fontName=fn_bold, textColor=rl('navy'),
        alignment=align, spaceAfter=6, spaceBefore=4, leading=21)

    S['h2'] = ParagraphStyle('h2',
        fontSize=12, fontName=fn_bold, textColor=rl('blue'),
        alignment=align, spaceAfter=5, spaceBefore=12, leading=16)

    S['h3'] = ParagraphStyle('h3',
        fontSize=10.5, fontName=fn_bold, textColor=rl('gray_dark'),
        alignment=align, spaceAfter=4, spaceBefore=8, leading=14)

    S['body'] = ParagraphStyle('body',
        fontSize=9.5, fontName=fn, textColor=rl('gray_dark'),
        alignment=TA_JUSTIFY if lang != 'ar' else TA_RIGHT,
        spaceAfter=6, leading=15)

    S['body_small'] = ParagraphStyle('body_small',
        fontSize=8.5, fontName=fn, textColor=rl('gray_mid'),
        alignment=align, spaceAfter=4, leading=12)

    S['bullet'] = ParagraphStyle('bullet',
        fontSize=9.5, fontName=fn, textColor=rl('gray_dark'),
        alignment=align, spaceAfter=4, leading=15,
        leftIndent=14 if lang != 'ar' else 0,
        rightIndent=14 if lang == 'ar' else 0)

    S['metric_value'] = ParagraphStyle('metric_value',
        fontSize=20, fontName=fn_bold, textColor=rl('navy'),
        alignment=TA_CENTER, spaceAfter=2, leading=24)

    S['metric_label'] = ParagraphStyle('metric_label',
        fontSize=7.5, fontName=fn, textColor=rl('gray'),
        alignment=TA_CENTER, spaceAfter=0, leading=10)

    S['toc_entry'] = ParagraphStyle('toc_entry',
        fontSize=10, fontName=fn, textColor=rl('gray_dark'),
        alignment=align, spaceAfter=4, leading=14)

    S['toc_page'] = ParagraphStyle('toc_page',
        fontSize=10, fontName=fn, textColor=rl('blue_mid'),
        alignment=TA_RIGHT, spaceAfter=4, leading=14)

    S['callout_blue'] = ParagraphStyle('cb',
        fontSize=9.5, fontName=fn, textColor=rl('blue'),
        alignment=align, spaceAfter=4, leading=15, leftIndent=12)

    S['callout_green'] = ParagraphStyle('cg',
        fontSize=9.5, fontName=fn, textColor=rl('green'),
        alignment=align, spaceAfter=4, leading=15, leftIndent=12)

    S['callout_amber'] = ParagraphStyle('ca',
        fontSize=9.5, fontName=fn, textColor=rl('amber'),
        alignment=align, spaceAfter=4, leading=15, leftIndent=12)

    S['callout_red'] = ParagraphStyle('cr',
        fontSize=9.5, fontName=fn, textColor=rl('red'),
        alignment=align, spaceAfter=4, leading=15, leftIndent=12)

    S['footer'] = ParagraphStyle('footer',
        fontSize=7, fontName=fn, textColor=rl('gray'),
        alignment=TA_CENTER, leading=9)

    S['validation_ok'] = ParagraphStyle('vok',
        fontSize=8, fontName=fn, textColor=rl('green'),
        alignment=TA_LEFT, leading=11)

    S['validation_err'] = ParagraphStyle('verr',
        fontSize=8, fontName=fn, textColor=rl('red'),
        alignment=TA_LEFT, leading=11)

    return S


# ═══════════════════════════════════════════════════════════
# 7. LAYOUT HELPERS
# ═══════════════════════════════════════════════════════════
def _divider(story, color=None, thickness=0.5, sb=6, sa=10):
    story.append(Spacer(1, sb/72*inch))
    story.append(HRFlowable(width="100%", thickness=thickness,
                             color=color or rl('border'), spaceAfter=sa/72*inch))

def _section_header(story, number, title, S, lang='en'):
    story.append(Spacer(1, 0.12*inch))
    t = process_text(f"SECTION {number}", lang)
    story.append(Paragraph(t, S['section_label']))
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
                colWidths=[CONTENT_W - 0.3*inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), bg),
        ('LINEBEFORE',   (0,0), (0,-1),  3, border),
        ('TOPPADDING',   (0,0), (-1,-1), 9),
        ('BOTTOMPADDING',(0,0), (-1,-1), 9),
        ('LEFTPADDING',  (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.08*inch))

def _pro_table(story, data, col_widths=None, lang='en'):
    if not data: return
    n  = len(data[0])
    cw = col_widths or [CONTENT_W / n] * n
    processed = []
    for i, row in enumerate(data):
        processed.append([process_text(str(cell), lang) for cell in row])
    style = [
        ('FONTNAME',      (0,0),  (-1,-1), get_font(lang)),
        ('FONTSIZE',      (0,0),  (-1,-1), 9),
        ('TEXTCOLOR',     (0,0),  (-1,-1), rl('gray_dark')),
        ('TOPPADDING',    (0,0),  (-1,-1), 7),
        ('BOTTOMPADDING', (0,0),  (-1,-1), 7),
        ('LEFTPADDING',   (0,0),  (-1,-1), 9),
        ('RIGHTPADDING',  (0,0),  (-1,-1), 9),
        ('GRID',          (0,0),  (-1,-1), 0.3, rl('border')),
        ('ROWBACKGROUNDS',(0,1),  (-1,-1), [rl('white'), rl('gray_pale')]),
        ('ALIGN',         (1,0),  (-1,-1), 'RIGHT' if lang != 'ar' else 'LEFT'),
        ('ALIGN',         (0,0),  (0,-1),  'LEFT'  if lang != 'ar' else 'RIGHT'),
        ('BACKGROUND',    (0,0),  (-1,0),  rl('navy')),
        ('TEXTCOLOR',     (0,0),  (-1,0),  rl('white')),
        ('FONTNAME',      (0,0),  (-1,0),  get_font(lang, bold=True)),
        ('ALIGN',         (0,0),  (-1,0),  'CENTER'),
        ('TOPPADDING',    (0,0),  (-1,0),  9),
        ('BOTTOMPADDING', (0,0),  (-1,0),  9),
    ]
    tbl = Table(processed, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle(style))
    story.append(tbl)
    story.append(Spacer(1, 0.12*inch))


# ═══════════════════════════════════════════════════════════
# 8. PAGE FOOTER
# ═══════════════════════════════════════════════════════════
class ReportCanvas:
    def __init__(self, report_date: str, lang: str = 'en'):
        self.report_date = report_date
        self.lang        = lang

    def __call__(self, canvas, doc):
        canvas.saveState()
        # Top accent
        canvas.setFillColor(rl('blue'))
        canvas.rect(MARGIN, PAGE_H - 0.36*inch, CONTENT_W, 2.2, fill=1, stroke=0)
        # Footer line
        canvas.setStrokeColor(rl('border'))
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN, 0.60*inch, PAGE_W - MARGIN, 0.60*inch)
        # Footer text
        canvas.setFont(get_font(self.lang), 7)
        canvas.setFillColor(rl('gray'))
        left_txt  = process_text("Confidential Business Analysis Report", self.lang)
        right_txt = process_text(self.report_date, self.lang)
        canvas.drawString(MARGIN, 0.40*inch, left_txt)
        canvas.drawCentredString(PAGE_W/2, 0.40*inch, f"Page {doc.page}")
        canvas.drawRightString(PAGE_W - MARGIN, 0.40*inch, right_txt)
        canvas.restoreState()


# ═══════════════════════════════════════════════════════════
# 9. MARKDOWN RENDERER (clean — no raw symbols)
# ═══════════════════════════════════════════════════════════
def _clean_md(text: str) -> str:
    text = re.sub(r'^#{1,4}\s*', '', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*',   r'<i>\1</i>', text)
    text = re.sub(r'[■□▪▫●►▸▶\u25A0-\u25FF]', '', text)
    return text.strip()

def _render_analysis(story, text: str, S, lang: str = 'en'):
    table_buf = []
    for raw in text.split('\n'):
        line = raw.rstrip()

        # flush table
        if table_buf and not (line.startswith('|') and line.endswith('|')):
            _flush_md_table(story, table_buf, S, lang)
            table_buf = []

        if not line.strip():
            story.append(Spacer(1, 0.06*inch)); continue

        if line.startswith('|') and line.endswith('|'):
            if not re.match(r'^\|[\s\-:]+\|$', line):
                cells = [c.strip() for c in line.strip('|').split('|')]
                table_buf.append(cells)
            continue

        if re.match(r'^-{3,}$', line.strip()):
            _divider(story, sb=4, sa=6); continue

        clean = _clean_md(line)
        if not clean: continue

        if line.strip().startswith('### '):
            story.append(Paragraph(process_text(clean, lang), S['h3']))
        elif line.strip().startswith('## '):
            story.append(Paragraph(process_text(clean, lang), S['h2']))
        elif line.strip().startswith('# '):
            story.append(Paragraph(process_text(clean, lang), S['h1']))
        elif line.strip().startswith(('- ', '* ')):
            content = process_text(clean[2:] if len(clean) > 2 else clean, lang)
            story.append(Paragraph(f"\u2022  {content}", S['bullet']))
        elif re.match(r'^\d+\.\s', line.strip()):
            story.append(Paragraph(process_text(clean, lang), S['bullet']))
        else:
            pt = process_text(clean, lang)
            if '$' in pt and any(k in pt for k in ['Confidence','confidence','High','Medium','Low']):
                story.append(Paragraph(pt, S['callout_blue']))
            elif any(k in clean for k in ['🎯','Confidence','مستوى']):
                story.append(Paragraph(pt, S['callout_blue']))
            elif any(k in clean for k in ['💰','$']):
                story.append(Paragraph(pt, S['callout_green']))
            elif any(k in clean for k in ['🚨','⚠️','Warning','Critical']):
                story.append(Paragraph(pt, S['callout_amber']))
            else:
                story.append(Paragraph(pt, S['body']))

    if table_buf:
        _flush_md_table(story, table_buf, S, lang)

def _flush_md_table(story, rows, S, lang):
    if not rows: return
    n  = max(len(r) for r in rows)
    cw = CONTENT_W / n
    _pro_table(story, rows, col_widths=[cw]*n, lang=lang)


# ═══════════════════════════════════════════════════════════
# 10. REPORT SECTIONS
# ═══════════════════════════════════════════════════════════
def _cover(story, company_name, S, ctx, lang):
    story.append(Spacer(1, 1.2*inch))
    rule = Table([['']], colWidths=[CONTENT_W], rowHeights=[3])
    rule.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1), rl('blue'))]))
    story.append(rule)
    story.append(Spacer(1, 0.3*inch))

    client = company_name if company_name else "Client Organization"
    t = {
        'en': ("BUSINESS INTELLIGENCE REPORT",
               "Sales Performance Analysis Report",
               "Performance Assessment &amp; Strategic Intelligence"),
        'ar': ("تقرير الذكاء التجاري",
               "تقرير تحليل أداء المبيعات",
               "تقييم الأداء والاستخبارات الاستراتيجية"),
        'fr': ("RAPPORT D'INTELLIGENCE COMMERCIALE",
               "Rapport d'Analyse des Ventes",
               "Évaluation de la Performance &amp; Intelligence Stratégique"),
    }.get(lang, ("BUSINESS INTELLIGENCE REPORT",
                 "Sales Performance Analysis Report",
                 "Performance Assessment &amp; Strategic Intelligence"))

    story.append(Paragraph(process_text(t[0], lang), S['cover_eyebrow']))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(process_text(t[1], lang), S['cover_title']))
    story.append(Spacer(1, 0.12*inch))
    story.append(Paragraph(process_text(t[2], lang), S['cover_subtitle']))
    story.append(Spacer(1, 0.3*inch))
    story.append(rule)
    story.append(Spacer(1, 0.45*inch))

    # Dynamic meta block — all from ctx
    labels = {
        'en': ["PREPARED FOR", "REPORTING PERIOD", "REPORT DATE", "CLASSIFICATION"],
        'ar': ["مُعدّ لـ", "فترة التقرير", "تاريخ التقرير", "التصنيف"],
        'fr': ["PRÉPARÉ POUR", "PÉRIODE", "DATE DU RAPPORT", "CLASSIFICATION"],
    }.get(lang, ["PREPARED FOR", "REPORTING PERIOD", "REPORT DATE", "CLASSIFICATION"])

    meta_items = [
        (labels[0], client),
        (labels[1], ctx['date_range']),
        (labels[2], ctx['report_date']),
        (labels[3], "Confidential" if lang=="en" else "سري" if lang=="ar" else "Confidentiel"),
    ]
    rows = []
    for lbl, val in meta_items:
        rows.append([
            Paragraph(process_text(lbl, lang), S['cover_meta_label']),
            Paragraph(process_text(str(val), lang), S['cover_meta_value']),
        ])
    meta_tbl = Table(rows, colWidths=[1.7*inch, CONTENT_W-1.7*inch])
    meta_tbl.setStyle(TableStyle([
        ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW',     (0,0), (-1,-2), 0.25, rl('border')),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
    ]))
    story.append(meta_tbl)
    story.append(PageBreak())


def _toc(story, S, ctx, lang, has_store, has_corr):
    lbl = {'en':'TABLE OF CONTENTS','ar':'فهرس المحتويات','fr':'TABLE DES MATIÈRES'}.get(lang,'TABLE OF CONTENTS')
    title = {'en':'Report Structure','ar':'هيكل التقرير','fr':'Structure du Rapport'}.get(lang,'Report Structure')
    story.append(Paragraph(process_text(lbl, lang), S['section_label']))
    story.append(Paragraph(process_text(title, lang), S['h1']))
    _divider(story, color=rl('blue'), thickness=1.1, sb=2, sa=16)

    sections_en = [
        ("01","Executive Summary","3"),
        ("02","Key Findings","4"),
        ("03","Sales Performance Overview","5"),
        ("04","Period Trend Analysis","6"),
    ]
    pg = 7
    if has_store:
        sections_en.append((f"{pg:02d}","Segment Performance Analysis",str(pg))); pg+=1
    if has_corr:
        sections_en.append((f"{pg:02d}","External Factors & Correlations",str(pg))); pg+=1
    sections_en.append((f"{pg:02d}","Revenue Forecast",str(pg))); pg+=1
    sections_en.append((f"{pg:02d}","Strategic Recommendations",str(pg))); pg+=1
    sections_en.append((f"{pg:02d}","Data Appendix",str(pg)))

    for num, title_en, page in sections_en:
        t = process_text(title_en, lang)
        row = [[
            Paragraph(f"<b>{num}</b>", ParagraphStyle('tn', fontSize=9,
                fontName=get_font(lang,True), textColor=rl('blue_mid'),
                alignment=TA_LEFT, leading=13)),
            Paragraph(t, S['toc_entry']),
            Paragraph(page, S['toc_page']),
        ]]
        rt = Table(row, colWidths=[0.45*inch, CONTENT_W-1.1*inch, 0.65*inch])
        rt.setStyle(TableStyle([
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LINEBELOW',     (0,0), (-1,-1), 0.2, rl('border')),
        ]))
        story.append(rt)
    story.append(PageBreak())


def _executive_summary(story, S, ctx, lang, ai_result=None):
    titles = {
        'en': ("01","Executive Summary"),
        'ar': ("01","الملخص التنفيذي"),
        'fr': ("01","Résumé Exécutif"),
    }.get(lang, ("01","Executive Summary"))
    _section_header(story, titles[0], titles[1], S, lang)

    # Dynamic opening — all numbers from ctx
    if lang == 'en':
        intro = (
            f"This report presents a comprehensive performance assessment covering "
            f"<b>{ctx['n_records']:,} records</b> across <b>{ctx['n_periods']:,} periods</b> "
            f"spanning <b>{ctx['date_range']}</b>. Total portfolio revenue reached "
            f"<b>${ctx['total_revenue']:,.0f}</b> with an average of "
            f"<b>${ctx['avg_per_period']:,.0f}</b> per period. "
            f"The overall performance trajectory is <b>{ctx['trend_direction']}</b> "
            f"({ctx['trend_pct']:+.1f}% half-over-half)."
        )
    elif lang == 'ar':
        intro = (
            f"يقدم هذا التقرير تقييماً شاملاً للأداء يغطي "
            f"<b>{ctx['n_records']:,} سجل</b> عبر <b>{ctx['n_periods']:,} فترة</b> "
            f"خلال <b>{ctx['date_range']}</b>. بلغ إجمالي الإيرادات "
            f"<b>${ctx['total_revenue']:,.0f}</b> بمتوسط "
            f"<b>${ctx['avg_per_period']:,.0f}</b> لكل فترة."
        )
    else:
        intro = (
            f"Ce rapport présente une évaluation complète couvrant "
            f"<b>{ctx['n_records']:,} enregistrements</b> sur <b>{ctx['n_periods']:,} périodes</b> "
            f"de <b>{ctx['date_range']}</b>. Le revenu total du portefeuille est de "
            f"<b>${ctx['total_revenue']:,.0f}</b> avec une moyenne de "
            f"<b>${ctx['avg_per_period']:,.0f}</b> par période."
        )
    story.append(Paragraph(process_text(intro, lang), S['body']))
    story.append(Spacer(1, 0.12*inch))

    # Dynamic metric strip from ctx
    col_w = CONTENT_W / 4
    m_vals = [
        (_money(ctx['total_revenue']),  {'en':'Total Revenue','ar':'إجمالي الإيرادات','fr':'Revenu Total'}.get(lang,'Total Revenue')),
        (_money(ctx['avg_per_period']), {'en':'Avg per Period','ar':'متوسط الفترة','fr':'Moy. par Période'}.get(lang,'Avg per Period')),
        (_money(ctx['peak_value']),     {'en':'Peak Performance','ar':'أعلى أداء','fr':'Performance Max'}.get(lang,'Peak Performance')),
        (_money(ctx['fc12']),           {'en':'12-Period Forecast','ar':'توقعات 12 فترة','fr':'Prévision 12 Pér.'}.get(lang,'12-Period Forecast')),
    ]
    metrics = [
        [Paragraph(process_text(v, lang), S['metric_value']) for v,_ in m_vals],
        [Paragraph(process_text(l, lang), S['metric_label']) for _,l in m_vals],
    ]
    mt = Table(metrics, colWidths=[col_w]*4, rowHeights=[0.46*inch, 0.26*inch])
    mt.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), rl('blue_pale')),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('GRID',         (0,0), (-1,-1), 0.35, rl('border')),
        ('LINEABOVE',    (0,0), (-1,0),  1.4, rl('blue')),
        ('LINEBELOW',    (0,-1),(-1,-1), 1.4, rl('blue')),
        ('TOPPADDING',   (0,0), (-1,0),  10),
        ('BOTTOMPADDING',(0,-1),(-1,-1), 8),
    ]))
    story.append(mt)
    story.append(Spacer(1, 0.15*inch))

    if ai_result:
        _render_analysis(story, ai_result, S, lang)

    story.append(PageBreak())


def _key_findings(story, S, ctx, lang):
    titles = {'en':("02","Key Findings"),'ar':("02","النتائج الرئيسية"),'fr':("02","Conclusions Clés")}.get(lang,("02","Key Findings"))
    _section_header(story, titles[0], titles[1], S, lang)

    # All finding text built dynamically from ctx
    findings = []

    # Finding 1: Revenue baseline — dynamic numbers
    if lang == 'en':
        f1 = (
            "Revenue Baseline",
            f"The portfolio generated <b>${ctx['total_revenue']:,.0f}</b> across "
            f"<b>{ctx['n_records']:,}</b> records. The average revenue per period is "
            f"<b>${ctx['avg_per_period']:,.0f}</b> with a coefficient of variation of "
            f"<b>{ctx['cv_pct']:.1f}%</b>, indicating "
            f"{'low' if ctx['cv_pct'] < 30 else 'moderate' if ctx['cv_pct'] < 60 else 'high'} volatility.",
            'blue'
        )
    elif lang == 'ar':
        f1 = (
            "خط الأساس للإيرادات",
            f"بلغ إجمالي الإيرادات <b>${ctx['total_revenue']:,.0f}</b> عبر "
            f"<b>{ctx['n_records']:,}</b> سجل بمتوسط <b>${ctx['avg_per_period']:,.0f}</b> للفترة.",
            'blue'
        )
    else:
        f1 = (
            "Base de revenus",
            f"Le portefeuille a généré <b>${ctx['total_revenue']:,.0f}</b> sur "
            f"<b>{ctx['n_records']:,}</b> enregistrements. Moyenne: <b>${ctx['avg_per_period']:,.0f}</b> par période.",
            'blue'
        )
    findings.append(f1)

    # Finding 2: Segment performance — uses real segment names
    if ctx['best_group'] != 'N/A' and ctx['n_groups'] > 1:
        if lang == 'en':
            f2 = (
                f"Segment Performance — {ctx['n_groups']} {ctx['group_col']}s",
                f"<b>{ctx['best_group']}</b> leads with <b>${ctx['best_group_revenue']:,.0f}</b> "
                f"({ctx['best_group_share']:.1f}% of total). "
                f"<b>{ctx['worst_group']}</b> represents the greatest improvement opportunity. "
                + (f"Pareto analysis: top <b>{ctx['pareto_pct']:.0f}%</b> of units generate 80% of revenue." if ctx['pareto_pct'] > 0 else ""),
                'green'
            )
        elif lang == 'ar':
            f2 = (
                f"أداء الشرائح — {ctx['n_groups']} {ctx['group_col']}",
                f"يتصدر <b>{ctx['best_group']}</b> بإيرادات <b>${ctx['best_group_revenue']:,.0f}</b> "
                f"({ctx['best_group_share']:.1f}% من الإجمالي). "
                f"<b>{ctx['worst_group']}</b> يمثل أكبر فرصة للتحسين.",
                'green'
            )
        else:
            f2 = (
                f"Performance des segments — {ctx['n_groups']} {ctx['group_col']}s",
                f"<b>{ctx['best_group']}</b> est en tête avec <b>${ctx['best_group_revenue']:,.0f}</b> "
                f"({ctx['best_group_share']:.1f}% du total). "
                f"<b>{ctx['worst_group']}</b> représente la plus grande opportunité.",
                'green'
            )
        findings.append(f2)

    # Finding 3: Forecast — dynamic
    if lang == 'en':
        f3 = (
            "Forward Outlook",
            f"Revenue projections indicate <b>${ctx['fc4']:,.0f}</b> over the next 4 periods "
            f"and <b>${ctx['fc12']:,.0f}</b> over 12 periods. "
            f"Peak demand is projected at <b>{ctx['peak_week']}</b> ({_money(ctx['peak_fc'])}).",
            'amber'
        )
    elif lang == 'ar':
        f3 = (
            "التوقعات المستقبلية",
            f"تشير التوقعات إلى <b>${ctx['fc4']:,.0f}</b> في الـ 4 فترات القادمة "
            f"و<b>${ctx['fc12']:,.0f}</b> في 12 فترة. ذروة الطلب: <b>{ctx['peak_week']}</b>.",
            'amber'
        )
    else:
        f3 = (
            "Perspectives",
            f"Les projections indiquent <b>${ctx['fc4']:,.0f}</b> sur 4 périodes "
            f"et <b>${ctx['fc12']:,.0f}</b> sur 12 périodes. Pic: <b>{ctx['peak_week']}</b>.",
            'amber'
        )
    findings.append(f3)

    for title, text, style in findings:
        story.append(Paragraph(process_text(title, lang), S['h3']))
        _callout(story, text, style, S, lang)
        story.append(Spacer(1, 0.04*inch))

    story.append(PageBreak())


def _sales_overview(story, S, ctx, df, date_col, sales_col, company_name, lang):
    titles = {'en':("03","Sales Performance Overview"),'ar':("03","نظرة عامة على أداء المبيعات"),'fr':("03","Vue d'ensemble des Ventes")}.get(lang,("03","Sales Performance Overview"))
    _section_header(story, titles[0], titles[1], S, lang)

    intro = {
        'en': f"Revenue performance across {ctx['n_periods']:,} periods spanning {ctx['date_range']}. "
              f"The following trend chart illustrates period-by-period dynamics.",
        'ar': f"أداء الإيرادات عبر {ctx['n_periods']:,} فترة من {ctx['date_range']}.",
        'fr': f"Performance sur {ctx['n_periods']:,} périodes de {ctx['date_range']}.",
    }.get(lang, "")
    story.append(Paragraph(process_text(intro, lang), S['body']))
    story.append(Spacer(1, 0.12*inch))

    # Dynamic chart from actual df
    weekly = df.groupby(date_col)[sales_col].sum().reset_index().sort_values(date_col)
    weekly['ma'] = weekly[sales_col].rolling(4, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    ax.fill_between(weekly[date_col], weekly[sales_col], alpha=0.08, color=mpl('chart1'))
    ax.plot(weekly[date_col], weekly[sales_col], color=mpl('chart1'), linewidth=1.2, alpha=0.65,
            label={'en':'Revenue','ar':'الإيرادات','fr':'Revenu'}.get(lang,'Revenue'))
    ax.plot(weekly[date_col], weekly['ma'], color=mpl('chart2'), linewidth=2.2, zorder=5,
            label={'en':'4-Period Moving Avg','ar':'متوسط 4 فترات','fr':'Moy. Mobile 4 Pér.'}.get(lang,'4-Period Moving Avg'))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    chart_title = f"{company_name} — " if company_name else ""
    chart_title += {'en':'Revenue Trend','ar':'اتجاه الإيرادات','fr':'Tendance des Revenus'}.get(lang,'Revenue Trend')
    ax.set_title(chart_title, fontsize=10.5, fontweight='bold', color=mpl('chart1'), pad=10)
    ax.spines['left'].set_color(CH['border'])
    ax.spines['bottom'].set_color(CH['border'])
    ax.legend(fontsize=8, framealpha=0.9)
    plt.tight_layout(pad=1.1)
    story.append(_fig_to_img(fig, height=3.0*inch))
    story.append(Spacer(1, 0.1*inch))

    # Dynamic insight from ctx
    insight = {
        'en': f"Peak single-period value: <b>${ctx['peak_value']:,.0f}</b> "
              f"({ctx['peak_value']/max(ctx['avg_per_period'],1)*100:.0f}% of period average). "
              f"Overall trend: <b>{ctx['trend_direction']}</b> ({ctx['trend_pct']:+.1f}% half-over-half).",
        'ar': f"أعلى قيمة لفترة واحدة: <b>${ctx['peak_value']:,.0f}</b>. "
              f"الاتجاه العام: <b>{ctx['trend_direction']}</b> ({ctx['trend_pct']:+.1f}%).",
        'fr': f"Valeur de pointe: <b>${ctx['peak_value']:,.0f}</b>. "
              f"Tendance globale: <b>{ctx['trend_direction']}</b> ({ctx['trend_pct']:+.1f}%).",
    }.get(lang, "")
    _callout(story, insight, 'blue', S, lang)
    story.append(PageBreak())


def _trend_analysis(story, S, ctx, monthly_df, company_name, lang):
    titles = {'en':("04","Period Trend Analysis"),'ar':("04","تحليل التوجهات"),'fr':("04","Analyse des Tendances")}.get(lang,("04","Period Trend Analysis"))
    _section_header(story, titles[0], titles[1], S, lang)

    months_str = [str(m) for m in monthly_df['month']]
    vals       = monthly_df['total'].tolist()
    if not vals:
        story.append(Paragraph(process_text("Insufficient data.", lang), S['body']))
        story.append(PageBreak()); return

    avg_val  = float(np.mean(vals))
    bar_clrs = [mpl('chart3') if v >= avg_val * 1.05
                else mpl('chart2') if v >= avg_val * 0.95
                else mpl('chart_neg') for v in vals]

    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    bars = ax.bar(months_str, vals, color=bar_clrs, width=0.62,
                  edgecolor='white', linewidth=0.35)
    ax.axhline(y=avg_val, color=mpl('chart5'), linewidth=1.1, linestyle='--', alpha=0.8,
               label=f"Avg: {_money(avg_val)}")
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(vals)*0.011,
                _money(val), ha='center', va='bottom', fontsize=6, color=CH['gray_dark'])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    chart_title = (company_name + " — " if company_name else "") + \
                  {'en':'Period Revenue Distribution','ar':'توزيع الإيرادات','fr':'Distribution Revenus'}.get(lang,'Period Revenue Distribution')
    ax.set_title(chart_title, fontsize=10.5, fontweight='bold', color=mpl('chart1'), pad=10)
    ax.tick_params(axis='x', rotation=40, labelsize=7)
    ax.spines['left'].set_color(CH['border'])
    ax.spines['bottom'].set_color(CH['border'])
    ax.legend(fontsize=8, framealpha=0.9)
    plt.tight_layout(pad=1.1)
    story.append(_fig_to_img(fig, height=3.0*inch))
    story.append(Spacer(1, 0.1*inch))

    # Dynamic insight — all from ctx
    insight = {
        'en': f"Best period: <b>{ctx['best_period_label']}</b> ({_money(ctx['best_period_value'])}). "
              f"Weakest: <b>{ctx['worst_period_label']}</b> ({_money(ctx['worst_period_value'])}). "
              f"Period spread: <b>{ctx['period_spread_pct']:.0f}%</b> of average.",
        'ar': f"أفضل فترة: <b>{ctx['best_period_label']}</b> ({_money(ctx['best_period_value'])}). "
              f"أضعف فترة: <b>{ctx['worst_period_label']}</b> ({_money(ctx['worst_period_value'])}).",
        'fr': f"Meilleure période: <b>{ctx['best_period_label']}</b> ({_money(ctx['best_period_value'])}). "
              f"Pire: <b>{ctx['worst_period_label']}</b> ({_money(ctx['worst_period_value'])}).",
    }.get(lang, "")
    _callout(story, insight, 'blue', S, lang)
    story.append(PageBreak())


def _segment_analysis(story, S, ctx, store_df, group_col, company_name, lang):
    sec_num = "05"
    title_txt = {'en':f"Segment Performance — {group_col}",'ar':f"أداء الشرائح — {group_col}",'fr':f"Performance des Segments — {group_col}"}.get(lang,f"Segment Performance — {group_col}")
    _section_header(story, sec_num, title_txt, S, lang)

    top10      = store_df.head(10)
    total_rev  = float(store_df['total'].sum())
    avg_rev    = float(store_df['total'].mean())
    labels     = top10[group_col].astype(str).tolist()
    rev        = top10['total'].tolist()
    bar_clrs   = [mpl('chart1') if i<3 else mpl('chart2') if i<7 else mpl('chart3') for i in range(len(rev))]

    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    bars = ax.bar(labels, rev, color=bar_clrs, width=0.6, edgecolor='white', linewidth=0.35)
    ax.axhline(y=avg_rev, color=mpl('chart5'), linewidth=1.1, linestyle='--', alpha=0.8,
               label=f"Portfolio Avg: {_money(avg_rev)}")
    for bar, val in zip(bars, rev):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(rev)*0.011,
                _money(val), ha='center', va='bottom', fontsize=6.5, color=CH['gray_dark'])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ax.set_xlabel(process_text(group_col, lang), fontsize=9)
    ct = (company_name + " — " if company_name else "") + \
         {'en':f"Top {len(top10)} {group_col}s",'ar':f"أفضل {len(top10)} {group_col}",'fr':f"Top {len(top10)} {group_col}s"}.get(lang,f"Top {len(top10)} {group_col}s")
    ax.set_title(ct, fontsize=10.5, fontweight='bold', color=mpl('chart1'), pad=10)
    ax.spines['left'].set_color(CH['border'])
    ax.spines['bottom'].set_color(CH['border'])
    ax.legend(fontsize=8, framealpha=0.9)
    plt.tight_layout(pad=1.1)
    story.append(_fig_to_img(fig, height=3.0*inch))
    story.append(Spacer(1, 0.1*inch))

    # Table with real segment names from data
    hdr_en = [group_col, "Total Revenue", "Avg / Period", "Portfolio Share"]
    hdr_ar = [group_col, "إجمالي الإيرادات", "متوسط الفترة", "حصة المحفظة"]
    hdr_fr = [group_col, "Revenu Total", "Moy. / Période", "Part du Portefeuille"]
    hdr = {'en':hdr_en,'ar':hdr_ar,'fr':hdr_fr}.get(lang, hdr_en)
    tbl_data = [hdr]
    for _, row in top10.iterrows():
        share = row['total'] / total_rev * 100 if total_rev > 0 else 0
        tbl_data.append([
            str(row[group_col]),          # real name from data
            f"${row['total']:,.0f}",
            f"${row['avg_weekly']:,.0f}",
            f"{share:.1f}%",
        ])
    _pro_table(story, tbl_data,
               col_widths=[1.8*inch, 1.8*inch, 1.8*inch, 1.5*inch], lang=lang)

    if ctx['pareto_n'] > 0:
        pareto_txt = {
            'en': f"<b>Concentration:</b> {ctx['pareto_n']} of {ctx['n_groups']} {group_col.lower()}s "
                  f"({ctx['pareto_pct']:.0f}% of portfolio) generate 80% of total revenue.",
            'ar': f"<b>التركز:</b> {ctx['pareto_n']} من {ctx['n_groups']} {group_col} "
                  f"({ctx['pareto_pct']:.0f}%) تولّد 80% من الإيرادات.",
            'fr': f"<b>Concentration:</b> {ctx['pareto_n']} sur {ctx['n_groups']} {group_col.lower()}s "
                  f"({ctx['pareto_pct']:.0f}%) génèrent 80% du revenu total.",
        }.get(lang, "")
        _callout(story, pareto_txt, 'green', S, lang)
    story.append(PageBreak())


def _correlations(story, S, ctx, corr_series, lang):
    titles = {'en':("06","External Factors & Correlations"),'ar':("06","العوامل الخارجية والارتباطات"),'fr':("06","Facteurs Externes & Corrélations")}.get(lang,("06","External Factors & Correlations"))
    _section_header(story, titles[0], titles[1], S, lang)

    intro = {
        'en': "Statistical correlation analysis quantifies the relationship between revenue and external variables. Positive values indicate alignment; negative values indicate inverse relationships.",
        'ar': "يقيس تحليل الارتباط العلاقة بين الإيرادات والمتغيرات الخارجية. القيم الموجبة تدل على توافق، والسالبة على علاقة عكسية.",
        'fr': "L'analyse de corrélation quantifie la relation entre le revenu et les variables externes.",
    }.get(lang, "")
    story.append(Paragraph(process_text(intro, lang), S['body']))
    story.append(Spacer(1, 0.12*inch))

    # Dynamic chart from actual corr_series
    bar_clrs = [mpl('chart_pos') if v > 0 else mpl('chart_neg') for v in corr_series.values]
    fig, ax = plt.subplots(figsize=(9.5, max(2.8, len(corr_series)*0.5)))
    bars = ax.barh(corr_series.index.tolist(), corr_series.values.tolist(),
                   color=bar_clrs, height=0.55, edgecolor='white', linewidth=0.3)
    for bar, val in zip(bars, corr_series.values):
        ax.text(val + (0.007 if val >= 0 else -0.007),
                bar.get_y() + bar.get_height()/2,
                f'{val:.4f}', va='center', ha='left' if val >= 0 else 'right', fontsize=8)
    ax.axvline(x=0, color=CH['gray_dark'], linewidth=0.7)
    ax.set_xlabel({'en':'Pearson Coefficient','ar':'معامل بيرسون','fr':'Coefficient de Pearson'}.get(lang,'Pearson Coefficient'), fontsize=9)
    ax.set_title({'en':'Correlation — External Variables vs Revenue','ar':'الارتباط مع الإيرادات','fr':'Corrélation — Variables Externes vs Revenu'}.get(lang,'Correlations'), fontsize=10.5, fontweight='bold', color=mpl('chart1'), pad=10)
    ax.spines['left'].set_color(CH['border'])
    ax.spines['bottom'].set_color(CH['border'])
    plt.tight_layout(pad=1.1)
    story.append(_fig_to_img(fig, height=max(2.4*inch, len(corr_series)*0.42*inch)))
    story.append(Spacer(1, 0.1*inch))

    # Dynamic insight using real factor names
    if ctx['pos_factors']:
        pos_str = ', '.join([f"<b>{k}</b> ({v:.3f})" for k,v in ctx['pos_factors']])
        pos_txt = {'en':f"Positive correlates: {pos_str} — move in alignment with revenue.",
                   'ar':f"عوامل إيجابية: {pos_str} — تتحرك بما يتوافق مع الإيرادات.",
                   'fr':f"Corrélations positives: {pos_str}."}.get(lang,"")
        _callout(story, pos_txt, 'green', S, lang)
    if ctx['neg_factors']:
        neg_str = ', '.join([f"<b>{k}</b> ({v:.3f})" for k,v in ctx['neg_factors']])
        neg_txt = {'en':f"Inverse correlates: {neg_str} — exert downward pressure on revenue.",
                   'ar':f"عوامل سلبية: {neg_str} — تضغط على الإيرادات.",
                   'fr':f"Corrélations négatives: {neg_str}."}.get(lang,"")
        _callout(story, neg_txt, 'amber', S, lang)
    story.append(PageBreak())


def _forecast_section(story, S, ctx, forecast, prophet_data, company_name, lang):
    titles = {'en':("07","Revenue Forecast"),'ar':("07","توقعات الإيرادات"),'fr':("07","Prévisions de Revenus")}.get(lang,("07","Revenue Forecast"))
    _section_header(story, titles[0], titles[1], S, lang)

    intro = {
        'en': "Forward-looking revenue projections are based on historical trend decomposition. Confidence intervals reflect the range of probable outcomes.",
        'ar': "تستند توقعات الإيرادات إلى تحليل التوجهات التاريخية. تعكس فترات الثقة نطاق النتائج المحتملة.",
        'fr': "Les prévisions sont basées sur la décomposition des tendances historiques.",
    }.get(lang, "")
    story.append(Paragraph(process_text(intro, lang), S['body']))
    story.append(Spacer(1, 0.12*inch))

    # Dynamic metric strip from ctx
    col_w = CONTENT_W / 3
    fc_items = [
        (_money(ctx['fc4']),  {'en':'Next 4 Periods','ar':'الـ 4 فترات القادمة','fr':'4 Prochaines Pér.'}.get(lang,'Next 4')),
        (_money(ctx['fc8']),  {'en':'Next 8 Periods','ar':'الـ 8 فترات القادمة','fr':'8 Prochaines Pér.'}.get(lang,'Next 8')),
        (_money(ctx['fc12']), {'en':'Next 12 Periods','ar':'الـ 12 فترة القادمة','fr':'12 Prochaines Pér.'}.get(lang,'Next 12')),
    ]
    mt = Table(
        [[Paragraph(process_text(v,lang), S['metric_value']) for v,_ in fc_items],
         [Paragraph(process_text(l,lang), S['metric_label']) for _,l in fc_items]],
        colWidths=[col_w]*3, rowHeights=[0.46*inch, 0.26*inch]
    )
    mt.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), rl('blue_pale')),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('GRID',         (0,0), (-1,-1), 0.35, rl('border')),
        ('LINEABOVE',    (0,0), (-1,0),  1.4, rl('teal')),
        ('LINEBELOW',    (0,-1),(-1,-1), 1.4, rl('teal')),
        ('TOPPADDING',   (0,0), (-1,0),  10),
        ('BOTTOMPADDING',(0,-1),(-1,-1), 8),
    ]))
    story.append(mt)
    story.append(Spacer(1, 0.15*inch))

    future = forecast[forecast['ds'] > prophet_data['ds'].max()]
    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    ax.plot(prophet_data['ds'], prophet_data['y'], color=mpl('chart1'), linewidth=1.4, alpha=0.8,
            label={'en':'Historical','ar':'تاريخي','fr':'Historique'}.get(lang,'Historical'))
    ax.axvline(x=prophet_data['ds'].max(), color=CH['gray'], linewidth=0.8, linestyle=':', alpha=0.7)
    ax.plot(future['ds'], future['yhat'], color=mpl('teal'), linewidth=2.2, linestyle='--',
            label={'en':'Projection','ar':'التوقع','fr':'Projection'}.get(lang,'Projection'), zorder=5)
    ax.fill_between(future['ds'], future['yhat_lower'], future['yhat_upper'],
                    alpha=0.11, color=mpl('teal'),
                    label={'en':'Confidence Range','ar':'نطاق الثقة','fr':'Plage de Confiance'}.get(lang,'Confidence Range'))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_money))
    ct = (company_name + " — " if company_name else "") + \
         {'en':'Revenue Projection','ar':'توقعات الإيرادات','fr':'Projection des Revenus'}.get(lang,'Revenue Projection')
    ax.set_title(ct, fontsize=10.5, fontweight='bold', color=mpl('chart1'), pad=10)
    ax.legend(fontsize=8, framealpha=0.9)
    ax.spines['left'].set_color(CH['border'])
    ax.spines['bottom'].set_color(CH['border'])
    plt.tight_layout(pad=1.1)
    story.append(_fig_to_img(fig, height=3.1*inch))
    story.append(Spacer(1, 0.1*inch))

    peak_txt = {
        'en': f"<b>Peak demand period:</b> {ctx['peak_week']} — Projected revenue of <b>{_money(ctx['peak_fc'])}</b>.",
        'ar': f"<b>فترة الذروة:</b> {ctx['peak_week']} — إيرادات متوقعة: <b>{_money(ctx['peak_fc'])}</b>.",
        'fr': f"<b>Période de pointe:</b> {ctx['peak_week']} — Revenu projeté: <b>{_money(ctx['peak_fc'])}</b>.",
    }.get(lang, "")
    _callout(story, peak_txt, 'blue', S, lang)
    story.append(PageBreak())


def _recommendations(story, S, ctx, lang):
    titles = {'en':("08","Strategic Recommendations"),'ar':("08","التوصيات الاستراتيجية"),'fr':("08","Recommandations Stratégiques")}.get(lang,("08","Strategic Recommendations"))
    _section_header(story, titles[0], titles[1], S, lang)

    intro = {
        'en': "Based on the performance data analyzed in this report, the following recommendations are presented in order of estimated impact.",
        'ar': "بناءً على بيانات الأداء المحللة، فيما يلي التوصيات مرتبة حسب الأثر المقدر.",
        'fr': "Sur la base des données analysées, les recommandations suivantes sont présentées par ordre d'impact estimé.",
    }.get(lang, "")
    story.append(Paragraph(process_text(intro, lang), S['body']))
    story.append(Spacer(1, 0.12*inch))

    # Dynamic recommendations using real ctx values
    recs = []

    if lang == 'en':
        recs = [
            ("Priority 1 — Capitalize on Top Performance",
             f"<b>{ctx['best_group']}</b> consistently outperforms the portfolio average. "
             f"A structured replication initiative — identifying and applying the operational "
             f"factors driving this unit's {_money(ctx['best_group_revenue'])} revenue — "
             f"could unlock incremental revenue across underperforming segments.",
             'blue'),
            ("Priority 2 — Address Underperformance",
             f"<b>{ctx['worst_group']}</b> and similarly positioned units require structured review. "
             f"Operational realignment could recover an estimated "
             f"<b>{_money(ctx['avg_per_period'] * 4)}</b> annually.",
             'amber'),
            ("Priority 3 — Align with Forecast Peak",
             f"Projections identify peak demand at <b>{ctx['peak_week']}</b> "
             f"({_money(ctx['peak_fc'])}). Advance preparation in inventory, staffing, "
             f"and promotions will maximize revenue capture.",
             'green'),
        ]
    elif lang == 'ar':
        recs = [
            ("الأولوية 1 — الاستفادة من أفضل الأداء",
             f"يتفوق <b>{ctx['best_group']}</b> باستمرار على متوسط المحفظة بإيرادات "
             f"{_money(ctx['best_group_revenue'])}. توثيق وتكرار نموذج نجاحه يمكن أن يفتح "
             f"إيرادات إضافية عبر الشرائح الضعيفة.",
             'blue'),
            ("الأولوية 2 — معالجة ضعف الأداء",
             f"يحتاج <b>{ctx['worst_group']}</b> مراجعة هيكلية. يمكن استعادة ما يصل إلى "
             f"<b>{_money(ctx['avg_per_period'] * 4)}</b> سنوياً.",
             'amber'),
            ("الأولوية 3 — التوافق مع ذروة التوقعات",
             f"تحدد التوقعات ذروة الطلب في <b>{ctx['peak_week']}</b> ({_money(ctx['peak_fc'])}). "
             f"التحضير المسبق يضمن تعظيم الإيرادات.",
             'green'),
        ]
    else:
        recs = [
            ("Priorité 1 — Capitaliser sur la Top Performance",
             f"<b>{ctx['best_group']}</b> surperforme constamment avec {_money(ctx['best_group_revenue'])}. "
             f"Une initiative de réplication structurée pourrait débloquer des revenus supplémentaires.",
             'blue'),
            ("Priorité 2 — Traiter la Sous-Performance",
             f"<b>{ctx['worst_group']}</b> nécessite une révision structurée. "
             f"Récupération estimée: <b>{_money(ctx['avg_per_period'] * 4)}</b> par an.",
             'amber'),
            ("Priorité 3 — Alignement avec le Pic Prévu",
             f"Le pic est projeté à <b>{ctx['peak_week']}</b> ({_money(ctx['peak_fc'])}). "
             f"Préparez stocks, effectifs et promotions en avance.",
             'green'),
        ]

    for title, text, style in recs:
        story.append(Paragraph(process_text(title, lang), S['h3']))
        _callout(story, text, style, S, lang)
        story.append(Spacer(1, 0.04*inch))
    story.append(PageBreak())


def _appendix(story, S, ctx, lang, validation_report=None):
    titles = {'en':("09","Data Appendix"),'ar':("09","ملحق البيانات"),'fr':("09","Annexe — Données")}.get(lang,("09","Data Appendix"))
    _section_header(story, titles[0], titles[1], S, lang)

    # Dynamic table from ctx — no hardcoded values
    hdr = {
        'en': ["Parameter", "Value"],
        'ar': ["المعيار", "القيمة"],
        'fr': ["Paramètre", "Valeur"],
    }.get(lang, ["Parameter", "Value"])

    params_en = [
        ("Total Records",       f"{ctx['n_records']:,}"),
        ("Unique Periods",      f"{ctx['n_periods']:,}"),
        ("Reporting Period",    ctx['date_range']),
        ("Total Revenue",       f"${ctx['total_revenue']:,.2f}"),
        ("Average per Period",  f"${ctx['avg_per_period']:,.2f}"),
        ("Peak Single Period",  f"${ctx['peak_value']:,.2f}"),
        ("Minimum Period",      f"${ctx['min_value']:,.2f}"),
        ("Revenue Std Dev",     f"${ctx['std_dev']:,.2f}"),
        ("Coeff. of Variation", f"{ctx['cv_pct']:.1f}%"),
        ("Trend Direction",     ctx['trend_direction'].capitalize()),
        ("Trend Change",        f"{ctx['trend_pct']:+.1f}%"),
    ]
    if ctx['best_group'] != 'N/A':
        params_en.append(("Best Segment",  f"{ctx['best_group']} (${ctx['best_group_revenue']:,.0f})"))
        params_en.append(("Worst Segment", ctx['worst_group']))
    if ctx['pareto_n'] > 0:
        params_en.append(("Pareto (80% Revenue)", f"Top {ctx['pareto_pct']:.0f}% of segments"))

    tbl_data = [hdr] + [[p, v] for p, v in params_en]
    _pro_table(story, tbl_data, col_widths=[2.8*inch, CONTENT_W-2.8*inch], lang=lang)

    # Methodology note
    method_title = {'en':'Methodology','ar':'المنهجية','fr':'Méthodologie'}.get(lang,'Methodology')
    story.append(Paragraph(process_text(method_title, lang), S['h2']))
    method_body = {
        'en': "Revenue forecasts use Holt-Winters Exponential Smoothing with additive trend and seasonal components where sufficient data exists. Confidence intervals are computed at the 95% level. Correlation analysis uses Pearson coefficients. All values are computed dynamically from the uploaded dataset.",
        'ar': "تستخدم توقعات الإيرادات نموذج Holt-Winters مع مكونات الاتجاه والموسمية. نطاقات الثقة محسوبة عند مستوى 95%. جميع القيم محسوبة ديناميكياً من البيانات المرفوعة.",
        'fr': "Les prévisions utilisent le lissage exponentiel de Holt-Winters. Les intervalles de confiance sont calculés à 95%. Toutes les valeurs sont calculées dynamiquement à partir des données téléchargées.",
    }.get(lang, "")
    story.append(Paragraph(process_text(method_body, lang), S['body']))

    # Quality report (if validation ran)
    if validation_report:
        story.append(Spacer(1, 0.15*inch))
        qr_title = {'en':'Quality Assurance Report','ar':'تقرير ضمان الجودة','fr':'Rapport d\'Assurance Qualité'}.get(lang,'Quality Report')
        story.append(Paragraph(process_text(qr_title, lang), S['h2']))
        status = validation_report.get('passed', True)
        status_txt = {
            'en': f"Quality check: {'PASSED' if status else 'ISSUES DETECTED'} — {validation_report.get('iterations',1)} iteration(s)",
            'ar': f"فحص الجودة: {'اجتاز' if status else 'تم اكتشاف مشكلات'} — {validation_report.get('iterations',1)} تكرار",
            'fr': f"Contrôle qualité: {'RÉUSSI' if status else 'PROBLÈMES DÉTECTÉS'} — {validation_report.get('iterations',1)} itération(s)",
        }.get(lang, "")
        pstyle = S['validation_ok'] if status else S['validation_err']
        story.append(Paragraph(process_text(status_txt, lang), pstyle))
        if not status and validation_report.get('errors'):
            for err in validation_report['errors'][:5]:
                story.append(Paragraph(f"  • {err}", S['validation_err']))


def _action_plan(story, S, ctx, lang):
    titles = {'en':("AP","Priority Action Plan"),'ar':("AP","خطة الأولويات"),'fr':("AP","Plan d'Action Prioritaire")}.get(lang,("AP","Priority Action Plan"))
    _section_header(story, titles[0], titles[1], S, lang)

    intro = {
        'en': "The following action plan translates analytical findings into a time-bound execution roadmap, sequenced by urgency and estimated financial impact.",
        'ar': "تترجم خطة العمل التالية النتائج التحليلية إلى خارطة طريق تنفيذية محددة زمنياً.",
        'fr': "Ce plan d'action traduit les résultats analytiques en feuille de route d'exécution séquencée par urgence et impact financier estimé.",
    }.get(lang, "")
    story.append(Paragraph(process_text(intro, lang), S['body']))
    story.append(Spacer(1, 0.15*inch))

    # All estimates computed from ctx — no hardcoded numbers
    qw_title  = {'en':'Quick Wins (0–30 Days)','ar':'مكاسب سريعة (0-30 يوم)','fr':'Gains Rapides (0–30 Jours)'}.get(lang,'Quick Wins')
    mt_title  = {'en':'Medium-Term Strategy (1–3 Months)','ar':'استراتيجية متوسطة المدى','fr':'Stratégie Moyen Terme (1–3 Mois)'}.get(lang,'Medium-Term')
    lt_title  = {'en':'Long-Term Initiatives (6–12 Months)','ar':'مبادرات طويلة المدى','fr':'Initiatives Long Terme (6–12 Mois)'}.get(lang,'Long-Term')

    for section_title, items in [
        (qw_title, [
            {'en': (f"Replicate {ctx['best_group']} Model",
                    f"Systematize operations of {ctx['best_group']} and apply to 3 comparable units.",
                    f"+{_money(ctx['avg_per_period']*4)}/quarter","Low","High"),
             'ar': (f"تكرار نموذج {ctx['best_group']}",
                    f"توثيق عمليات {ctx['best_group']} وتطبيقها على 3 وحدات مشابهة.",
                    f"+{_money(ctx['avg_per_period']*4)}/ربع","منخفض","عالي"),
             'fr': (f"Répliquer {ctx['best_group']}",
                    f"Systématiser les opérations de {ctx['best_group']} pour 3 unités comparables.",
                    f"+{_money(ctx['avg_per_period']*4)}/trimestre","Faible","Élevée"),
            },
            {'en': ("Forecast-Aligned Inventory",
                    f"Pre-position inventory ahead of peak at {ctx['peak_week']} ({_money(ctx['peak_fc'])}).",
                    f"+{_money(ctx['peak_fc']*0.08)} capture","Low","High"),
             'ar': ("تموضع مخزون متوافق مع التوقعات",
                    f"تجهيز المخزون قبل ذروة {ctx['peak_week']} ({_money(ctx['peak_fc'])}).",
                    f"+{_money(ctx['peak_fc']*0.08)}","منخفض","عالي"),
             'fr': ("Stock Aligné sur Prévisions",
                    f"Pré-positionner le stock avant le pic de {ctx['peak_week']}.",
                    f"+{_money(ctx['peak_fc']*0.08)}","Faible","Élevée"),
            },
        ]),
        (mt_title, [
            {'en': ("Segment Performance Tiering",
                    "Classify all segments into tiers and implement differentiated investment levels.",
                    f"+{_money(ctx['total_revenue']*0.06)}/year","Medium","Medium"),
             'ar': ("تصنيف أداء الشرائح",
                    "تصنيف الشرائح إلى فئات وتطبيق مستويات استثمار مختلفة.",
                    f"+{_money(ctx['total_revenue']*0.06)}/سنة","متوسط","متوسط"),
             'fr': ("Hiérarchisation des Segments",
                    "Classifier les segments et appliquer des niveaux d'investissement différenciés.",
                    f"+{_money(ctx['total_revenue']*0.06)}/an","Moyen","Moyen"),
            },
        ]),
        (lt_title, [
            {'en': ("Portfolio Optimization",
                    f"Expand top performers, restructure mid-tier, evaluate {ctx['worst_group']} for repositioning.",
                    f"+{_money(ctx['total_revenue']*0.12)}/year","High","Medium"),
             'ar': ("تحسين المحفظة",
                    f"توسيع الأفضل أداءً، إعادة هيكلة المتوسط، تقييم {ctx['worst_group']}.",
                    f"+{_money(ctx['total_revenue']*0.12)}/سنة","عالي","متوسط"),
             'fr': ("Optimisation du Portefeuille",
                    f"Développer les top performers, restructurer le mid-tier, évaluer {ctx['worst_group']}.",
                    f"+{_money(ctx['total_revenue']*0.12)}/an","Élevé","Moyen"),
            },
        ]),
    ]:
        story.append(Paragraph(process_text(section_title, lang), S['h2']))

        hdr = {
            'en': ["Initiative","Description","Est. Impact","Effort","Confidence"],
            'ar': ["المبادرة","الوصف","الأثر المقدر","الجهد","الثقة"],
            'fr': ["Initiative","Description","Impact Est.","Effort","Confiance"],
        }.get(lang, ["Initiative","Description","Est. Impact","Effort","Confidence"])

        tbl_data = [hdr]
        for item in items:
            row = item.get(lang, item.get('en', ('','','','','')))
            tbl_data.append(list(row))
        _pro_table(story, tbl_data,
                   col_widths=[1.35*inch, 2.55*inch, 1.3*inch, 0.6*inch, 0.85*inch],
                   lang=lang)
        story.append(Spacer(1, 0.1*inch))

    # Dynamic total impact from ctx
    total_impact_txt = {
        'en': f"<b>Combined impact projection:</b> Full implementation estimated to deliver "
              f"<b>{_money(ctx['total_revenue']*0.15)} — {_money(ctx['total_revenue']*0.22)}</b> "
              f"in incremental annual revenue (15–22% uplift on current baseline of {_money(ctx['total_revenue'])}).",
        'ar': f"<b>التأثير الإجمالي المقدر:</b> يُتوقع أن يحقق التطبيق الكامل "
              f"<b>{_money(ctx['total_revenue']*0.15)} — {_money(ctx['total_revenue']*0.22)}</b> "
              f"كإيرادات إضافية سنوية (15-22% نمو على الأساس الحالي).",
        'fr': f"<b>Impact combiné:</b> La mise en œuvre complète devrait générer "
              f"<b>{_money(ctx['total_revenue']*0.15)} — {_money(ctx['total_revenue']*0.22)}</b> "
              f"de revenus supplémentaires annuels (hausse de 15–22%).",
    }.get(lang, "")
    _callout(story, total_impact_txt, 'green', S, lang)
    story.append(PageBreak())


# ═══════════════════════════════════════════════════════════
# 11. MAIN GENERATOR
# ═══════════════════════════════════════════════════════════
def generate_pdf(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    summary: dict,
    store_df,
    corr_series,
    forecast: pd.DataFrame,
    prophet_data: pd.DataFrame,
    forecast_summary: dict,
    monthly_df: pd.DataFrame,
    group_col,
    company_name: str,
    T: dict,
    ai_result=None,
    ai_type=None,
    include_action_plan: bool = False,
    lang: str = 'en',
    system_prompt: str = "",
    ask_agent_fn=None,
) -> bytes:
    """
    Generate a premium, fully dynamic Business Intelligence PDF report.
    - All values extracted from df/summary — no hardcoded data
    - Arabic text support via arabic_reshaper + bidi + Amiri font
    - Quality guardrails with optional self-correction loop
    """
    # ── Step 1: Extract dynamic context from actual data ───
    ctx = extract_dynamic_context(
        df, date_col, sales_col, summary,
        store_df, group_col, corr_series,
        forecast_summary, monthly_df
    )

    # ── Step 2: Quality pipeline on AI text ───────────────
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

    # ── Step 3: Build PDF ──────────────────────────────────
    buffer     = io.BytesIO()
    S          = build_styles(lang)
    footer_fn  = ReportCanvas(ctx['report_date'], lang)

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.62*inch, bottomMargin=0.82*inch,
        title="Sales Performance Analysis Report",
        author="Business Intelligence Division",
        subject="Confidential Business Analysis",
        creator="Performance Analytics Platform",
    )

    story = []
    has_store = store_df is not None and group_col is not None and len(store_df) > 0
    has_corr  = corr_series is not None and len(corr_series) > 0

    _cover(story, company_name, S, ctx, lang)
    _toc(story, S, ctx, lang, has_store, has_corr)
    _executive_summary(story, S, ctx, lang, cleaned_ai)
    _key_findings(story, S, ctx, lang)
    _sales_overview(story, S, ctx, df, date_col, sales_col, company_name, lang)
    _trend_analysis(story, S, ctx, monthly_df, company_name, lang)

    if has_store:
        _segment_analysis(story, S, ctx, store_df, group_col, company_name, lang)

    if has_corr:
        _correlations(story, S, ctx, corr_series, lang)

    _forecast_section(story, S, ctx, forecast, prophet_data, company_name, lang)
    _recommendations(story, S, ctx, lang)

    if include_action_plan:
        _action_plan(story, S, ctx, lang)

    _appendix(story, S, ctx, lang, validation_report)

    doc.build(story, onFirstPage=footer_fn, onLaterPages=footer_fn)
    buffer.seek(0)
    return buffer.read()