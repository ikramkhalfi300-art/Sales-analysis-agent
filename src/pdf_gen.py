# src/pdf_gen.py
"""
Premium Business Intelligence Report Generator
Professional consulting-grade PDF — No AI branding
"""

import io
import re
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib import rcParams

from reportlab.lib.pagesizes   import A4
from reportlab.lib.units       import inch, cm
from reportlab.lib             import colors
from reportlab.lib.styles      import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums       import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus        import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether, ListFlowable, ListItem
)
from reportlab.pdfbase         import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Corporate Color Palette ──────────────────────────────
# CH = hex strings for Matplotlib
# C  = ReportLab color objects (auto-converted from CH)
CH = {
    'navy':        '#1B2E4B',
    'navy_dark':   '#0A1628',
    'blue':        '#1A3A6B',
    'blue_mid':    '#2557A7',
    'blue_light':  '#E8EFF8',
    'blue_pale':   '#F2F6FB',
    'teal':        '#0D7377',
    'teal_light':  '#E6F4F4',
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
    'chart_neu':   '#2557A7',
}
C = {k: colors.HexColor(v) for k, v in CH.items()}
C['white'] = colors.white
C['black'] = colors.black

def rl(key):
    """Get ReportLab color object — always safe for ReportLab contexts"""
    return C.get(key, colors.HexColor('#1A3A6B'))

def mpl(key):
    """Get hex string — always safe for Matplotlib contexts"""
    return CH.get(key, '#1A3A6B')


PAGE_W, PAGE_H = A4
MARGIN = 0.85 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

# ── Chart Styling ─────────────────────────────────────────
def set_chart_style():
    rcParams['font.family']        = 'sans-serif'
    rcParams['font.sans-serif']    = ['DejaVu Sans', 'Arial', 'Helvetica']
    rcParams['axes.spines.top']    = False
    rcParams['axes.spines.right']  = False
    rcParams['axes.spines.left']   = True
    rcParams['axes.spines.bottom'] = True
    rcParams['axes.linewidth']     = 0.6
    rcParams['axes.grid']          = True
    rcParams['grid.alpha']         = 0.15
    rcParams['grid.linewidth']     = 0.5
    rcParams['grid.color']         = '#9CA3AF'
    rcParams['xtick.labelsize']    = 8
    rcParams['ytick.labelsize']    = 8
    rcParams['axes.labelsize']     = 9
    rcParams['axes.titlesize']     = 11
    rcParams['axes.titleweight']   = 'bold'
    rcParams['axes.titlepad']      = 12
    rcParams['figure.facecolor']   = 'white'
    rcParams['axes.facecolor']     = 'white'

set_chart_style()

def money_fmt(x, pos=None):
    if   abs(x) >= 1e9: return f'${x/1e9:.1f}B'
    elif abs(x) >= 1e6: return f'${x/1e6:.1f}M'
    elif abs(x) >= 1e3: return f'${x/1e3:.0f}K'
    return f'${x:.0f}'

def fig_to_img(fig, width=CONTENT_W, height=2.8*inch):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=180, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width, height=height)


# ── Typography System ─────────────────────────────────────
def build_styles():
    S = {}

    # Cover
    S['cover_eyebrow'] = ParagraphStyle('cover_eyebrow',
        fontSize=9, fontName='Helvetica',
        textColor=CH['blue_mid'], alignment=TA_CENTER,
        spaceAfter=6, tracking=2)

    S['cover_title'] = ParagraphStyle('cover_title',
        fontSize=28, fontName='Helvetica-Bold',
        textColor=CH['navy'], alignment=TA_CENTER,
        spaceAfter=10, leading=34)

    S['cover_subtitle'] = ParagraphStyle('cover_subtitle',
        fontSize=14, fontName='Helvetica',
        textColor=CH['gray_mid'], alignment=TA_CENTER,
        spaceAfter=6, leading=20)

    S['cover_meta'] = ParagraphStyle('cover_meta',
        fontSize=9, fontName='Helvetica',
        textColor=CH['gray'], alignment=TA_CENTER,
        spaceAfter=4, leading=14)

    # Section headers
    S['section_label'] = ParagraphStyle('section_label',
        fontSize=8, fontName='Helvetica-Bold',
        textColor=CH['blue_mid'], alignment=TA_LEFT,
        spaceAfter=4, spaceBefore=20,
        leading=12, tracking=1.5)

    S['h1'] = ParagraphStyle('h1',
        fontSize=18, fontName='Helvetica-Bold',
        textColor=CH['navy'], alignment=TA_LEFT,
        spaceAfter=6, spaceBefore=4, leading=22)

    S['h2'] = ParagraphStyle('h2',
        fontSize=13, fontName='Helvetica-Bold',
        textColor=CH['blue'], alignment=TA_LEFT,
        spaceAfter=6, spaceBefore=14, leading=17)

    S['h3'] = ParagraphStyle('h3',
        fontSize=11, fontName='Helvetica-Bold',
        textColor=CH['gray_dark'], alignment=TA_LEFT,
        spaceAfter=4, spaceBefore=10, leading=15)

    # Body
    S['body'] = ParagraphStyle('body',
        fontSize=10, fontName='Helvetica',
        textColor=CH['gray_dark'], alignment=TA_JUSTIFY,
        spaceAfter=6, leading=16)

    S['body_small'] = ParagraphStyle('body_small',
        fontSize=9, fontName='Helvetica',
        textColor=CH['gray_mid'], alignment=TA_LEFT,
        spaceAfter=4, leading=13)

    S['body_bold'] = ParagraphStyle('body_bold',
        fontSize=10, fontName='Helvetica-Bold',
        textColor=CH['gray_dark'], alignment=TA_LEFT,
        spaceAfter=4, leading=15)

    # Callout boxes
    S['callout_blue'] = ParagraphStyle('callout_blue',
        fontSize=10, fontName='Helvetica',
        textColor=CH['blue'], alignment=TA_LEFT,
        spaceAfter=4, leading=15,
        leftIndent=12, borderPad=8)

    S['callout_green'] = ParagraphStyle('callout_green',
        fontSize=10, fontName='Helvetica',
        textColor=CH['green'], alignment=TA_LEFT,
        spaceAfter=4, leading=15,
        leftIndent=12, borderPad=8)

    S['callout_amber'] = ParagraphStyle('callout_amber',
        fontSize=10, fontName='Helvetica',
        textColor=CH['amber'], alignment=TA_LEFT,
        spaceAfter=4, leading=15,
        leftIndent=12, borderPad=8)

    S['callout_red'] = ParagraphStyle('callout_red',
        fontSize=10, fontName='Helvetica',
        textColor=CH['red'], alignment=TA_LEFT,
        spaceAfter=4, leading=15,
        leftIndent=12, borderPad=8)

    S['bullet'] = ParagraphStyle('bullet',
        fontSize=10, fontName='Helvetica',
        textColor=CH['gray_dark'], alignment=TA_LEFT,
        spaceAfter=4, leading=15,
        leftIndent=14, firstLineIndent=-10)

    # TOC
    S['toc_entry'] = ParagraphStyle('toc_entry',
        fontSize=10, fontName='Helvetica',
        textColor=CH['gray_dark'], alignment=TA_LEFT,
        spaceAfter=5, leading=15)

    S['toc_page'] = ParagraphStyle('toc_page',
        fontSize=10, fontName='Helvetica',
        textColor=CH['blue_mid'], alignment=TA_RIGHT,
        spaceAfter=5, leading=15)

    # Metric
    S['metric_value'] = ParagraphStyle('metric_value',
        fontSize=22, fontName='Helvetica-Bold',
        textColor=CH['navy'], alignment=TA_CENTER,
        spaceAfter=2, leading=26)

    S['metric_label'] = ParagraphStyle('metric_label',
        fontSize=8, fontName='Helvetica',
        textColor=CH['gray'], alignment=TA_CENTER,
        spaceAfter=0, leading=11)

    S['metric_delta'] = ParagraphStyle('metric_delta',
        fontSize=9, fontName='Helvetica-Bold',
        textColor=CH['teal'], alignment=TA_CENTER,
        spaceAfter=0, leading=12)

    # Footer
    S['footer'] = ParagraphStyle('footer',
        fontSize=7.5, fontName='Helvetica',
        textColor=CH['gray'], alignment=TA_CENTER, leading=10)

    return S


# ── Footer / Header on every page ────────────────────────
class ReportCanvas:
    def __init__(self, company_name, report_date, total_pages_ref):
        self.company      = company_name
        self.report_date  = report_date
        self.total_pages  = total_pages_ref

    def __call__(self, canvas, doc):
        canvas.saveState()
        page = doc.page

        # Top accent line
        canvas.setFillColor(CH['blue'])
        canvas.rect(MARGIN, PAGE_H - 0.38*inch, CONTENT_W, 2.5, fill=1, stroke=0)

        # Footer line
        canvas.setStrokeColor(CH['border'])
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN, 0.62*inch, PAGE_W - MARGIN, 0.62*inch)

        # Footer text
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(CH['gray'])
        canvas.drawString(MARGIN, 0.42*inch, "Confidential Business Analysis Report")
        canvas.drawCentredString(PAGE_W/2, 0.42*inch, f"Page {page}")
        canvas.drawRightString(PAGE_W - MARGIN, 0.42*inch, self.report_date)

        canvas.restoreState()


# ── Helpers ───────────────────────────────────────────────
def divider(story, color=None, thickness=0.5, space_before=8, space_after=12):
    story.append(Spacer(1, space_before/72*inch))
    story.append(HRFlowable(
        width="100%", thickness=thickness,
        color=color or CH['border'], spaceAfter=space_after/72*inch
    ))

def section_header(story, number, title, S):
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(f"SECTION {number}", S['section_label']))
    story.append(Paragraph(title, S['h1']))
    divider(story, color=CH['blue'], thickness=1.2, space_before=2, space_after=14)

def callout_box(story, text, style='blue', S=None):
    color_map = {
        'blue':  (CH['blue_light'],  CH['blue_mid'],  S['callout_blue']),
        'green': (CH['green_light'], CH['green'],     S['callout_green']),
        'amber': (CH['amber_light'], CH['amber'],     S['callout_amber']),
        'red':   (CH['red_light'],   CH['red'],       S['callout_red']),
    }
    bg, border, pstyle = color_map.get(style, color_map['blue'])
    tbl = Table([[Paragraph(text, pstyle)]], colWidths=[CONTENT_W - 0.3*inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), bg),
        ('LINEAFTER',    (0,0), (0,-1),  0, colors.transparent),
        ('LINEBEFORE',   (0,0), (0,-1),  3, border),
        ('TOPPADDING',   (0,0), (-1,-1), 10),
        ('BOTTOMPADDING',(0,0), (-1,-1), 10),
        ('LEFTPADDING',  (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('ROWBACKGROUNDS',(0,0),(-1,-1), [bg]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.1*inch))

def pro_table(story, data, col_widths=None, header=True):
    if not data: return
    n_cols = len(data[0])
    if col_widths is None:
        col_widths = [CONTENT_W / n_cols] * n_cols

    style = [
        ('FONTNAME',      (0,0),  (-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,0),  (-1,-1), 9),
        ('TEXTCOLOR',     (0,0),  (-1,-1), CH['gray_dark']),
        ('TOPPADDING',    (0,0),  (-1,-1), 8),
        ('BOTTOMPADDING', (0,0),  (-1,-1), 8),
        ('LEFTPADDING',   (0,0),  (-1,-1), 10),
        ('RIGHTPADDING',  (0,0),  (-1,-1), 10),
        ('GRID',          (0,0),  (-1,-1), 0.3, CH['border']),
        ('ROWBACKGROUNDS',(0,1),  (-1,-1), [C['white'], C['gray_pale']]),
        ('ALIGN',         (1,0),  (-1,-1), 'RIGHT'),
        ('ALIGN',         (0,0),  (0,-1),  'LEFT'),
    ]
    if header:
        style += [
            ('BACKGROUND',  (0,0), (-1,0), CH['navy']),
            ('TEXTCOLOR',   (0,0), (-1,0), C['white']),
            ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0,0), (-1,0), 9),
            ('ALIGN',       (0,0), (-1,0), 'CENTER'),
            ('BOTTOMPADDING',(0,0),(-1,0), 10),
            ('TOPPADDING',  (0,0), (-1,0), 10),
        ]
    tbl = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    tbl.setStyle(TableStyle(style))
    story.append(tbl)
    story.append(Spacer(1, 0.15*inch))


# ── Markdown parser (clean) ───────────────────────────────
def _clean_md(text):
    """Convert markdown to ReportLab XML, remove all squares/symbols"""
    # Remove heading markers
    text = re.sub(r'^#{1,4}\s*', '', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Remove stray symbols: ■ □ ▪ ▫ ● ► ▸
    text = re.sub(r'[■□▪▫●►▸▶]', '', text)
    # Remove emoji squares
    text = re.sub(r'[\U0001F7E5-\U0001F7FF]', '', text)
    return text.strip()

def _is_table_row(line):
    return line.startswith('|') and line.endswith('|')

def _is_separator(line):
    return bool(re.match(r'^[\|\s\-:]+$', line))


# ── COVER PAGE ────────────────────────────────────────────
def build_cover(story, company_name, T, S, summary):
    story.append(Spacer(1, 1.4*inch))

    # Top rule
    rule_data = [['']]
    rule_tbl  = Table(rule_data, colWidths=[CONTENT_W], rowHeights=[3])
    rule_tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1), CH['blue'])]))
    story.append(rule_tbl)
    story.append(Spacer(1, 0.35*inch))

    client_line = company_name if company_name else "Client Organization"
    story.append(Paragraph("BUSINESS INTELLIGENCE REPORT", S['cover_eyebrow']))
    story.append(Spacer(1, 0.18*inch))
    story.append(Paragraph("Sales Performance<br/>Analysis Report", S['cover_title']))
    story.append(Spacer(1, 0.18*inch))
    story.append(Paragraph("Performance Assessment &amp; Strategic Intelligence", S['cover_subtitle']))
    story.append(Spacer(1, 0.35*inch))

    # Bottom rule
    story.append(rule_tbl)
    story.append(Spacer(1, 0.55*inch))

    # Meta block
    date_range = summary.get('date_range', '')
    meta_items = [
        ["Prepared for", client_line],
        ["Reporting Period", date_range],
        ["Report Date", pd.Timestamp.now().strftime('%B %d, %Y')],
        ["Classification", "Confidential"],
    ]
    meta_rows = []
    for label, value in meta_items:
        meta_rows.append([
            Paragraph(label.upper(), ParagraphStyle('ml', fontSize=7.5,
                fontName='Helvetica-Bold', textColor=CH['gray'],
                alignment=TA_LEFT, leading=11, tracking=1)),
            Paragraph(value, ParagraphStyle('mv', fontSize=10,
                fontName='Helvetica', textColor=CH['navy'],
                alignment=TA_LEFT, leading=14)),
        ])
    meta_tbl = Table(meta_rows, colWidths=[1.6*inch, CONTENT_W-1.6*inch])
    meta_tbl.setStyle(TableStyle([
        ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW',     (0,0), (-1,-2), 0.3, CH['border']),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
    ]))
    story.append(meta_tbl)
    story.append(PageBreak())


# ── TABLE OF CONTENTS ─────────────────────────────────────
def build_toc(story, S, has_store, has_corr):
    story.append(Paragraph("TABLE OF CONTENTS", S['section_label']))
    story.append(Paragraph("Report Structure", S['h1']))
    divider(story, color=CH['blue'], thickness=1.2, space_before=2, space_after=18)

    sections = [
        ("01", "Executive Summary",             "3"),
        ("02", "Key Findings",                  "4"),
        ("03", "Sales Performance Overview",    "5"),
        ("04", "Trend Analysis",                "6"),
    ]
    pg = 7
    if has_store:
        sections.append((f"{pg:02d}", "Segment Performance Analysis", str(pg))); pg+=1
    if has_corr:
        sections.append((f"{pg:02d}", "External Factors & Correlations", str(pg))); pg+=1
    sections.append((f"{pg:02d}", "Revenue Forecast",           str(pg))); pg+=1
    sections.append((f"{pg:02d}", "Strategic Recommendations",  str(pg))); pg+=1
    sections.append((f"{pg:02d}", "Appendix — Data Overview",   str(pg)))

    for num, title, page in sections:
        row_data = [[
            Paragraph(f"<b>{num}</b>", ParagraphStyle('tn', fontSize=9,
                fontName='Helvetica-Bold', textColor=CH['blue_mid'],
                alignment=TA_LEFT, leading=13)),
            Paragraph(title, S['toc_entry']),
            Paragraph(page,  S['toc_page']),
        ]]
        row_tbl = Table(row_data, colWidths=[0.45*inch, CONTENT_W-1.1*inch, 0.65*inch])
        row_tbl.setStyle(TableStyle([
            ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LINEBELOW',     (0,0), (-1,-1), 0.25, CH['border']),
            ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ]))
        story.append(row_tbl)

    story.append(PageBreak())


# ── SECTION 1: Executive Summary ─────────────────────────
def build_executive_summary(story, S, summary, forecast_summary, ai_result=None):
    section_header(story, "01", "Executive Summary", S)

    total  = summary.get('total_sales', 0)
    avg    = summary.get('avg_weekly_sales', 0)
    best   = summary.get('max_single_week', 0)
    n_recs = summary.get('total_records', 0)
    dr     = summary.get('date_range', 'N/A')
    fc12   = forecast_summary.get('next_12_weeks', 0)

    # Opening paragraph
    story.append(Paragraph(
        f"This report presents a comprehensive performance assessment covering <b>{n_recs:,} "
        f"transactional records</b> over the period <b>{dr}</b>. The analysis encompasses "
        f"revenue performance, trend identification, segment benchmarking, and forward-looking "
        f"projections to support executive decision-making.",
        S['body']
    ))
    story.append(Spacer(1, 0.12*inch))

    # Metric strip
    metrics = [
        [
            Paragraph(f"${total/1e6:.1f}M" if total>=1e6 else f"${total:,.0f}", S['metric_value']),
            Paragraph(f"${avg/1e3:.0f}K" if avg>=1e3 else f"${avg:,.0f}", S['metric_value']),
            Paragraph(f"${best/1e6:.1f}M" if best>=1e6 else f"${best:,.0f}", S['metric_value']),
            Paragraph(f"${fc12/1e6:.1f}M" if fc12>=1e6 else f"${fc12:,.0f}", S['metric_value']),
        ],
        [
            Paragraph("Total Revenue", S['metric_label']),
            Paragraph("Avg per Period", S['metric_label']),
            Paragraph("Peak Performance", S['metric_label']),
            Paragraph("12-Period Forecast", S['metric_label']),
        ],
    ]
    col_w = CONTENT_W / 4
    m_tbl = Table(metrics, colWidths=[col_w]*4, rowHeights=[0.48*inch, 0.28*inch])
    m_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), CH['blue_pale']),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('GRID',         (0,0), (-1,-1), 0.4, CH['border']),
        ('TOPPADDING',   (0,0), (-1,0),  12),
        ('BOTTOMPADDING',(0,-1),(-1,-1), 10),
        ('TOPPADDING',   (0,-1),(-1,-1), 2),
        ('LINEABOVE',    (0,0), (-1,0),  1.5, CH['blue']),
        ('LINEBELOW',    (0,-1),(-1,-1), 1.5, CH['blue']),
    ]))
    story.append(m_tbl)
    story.append(Spacer(1, 0.18*inch))

    # If AI result exists, render it cleanly
    if ai_result:
        _render_analysis_text(story, ai_result, S)
    else:
        story.append(Paragraph(
            "Performance data indicates a broadly stable revenue trajectory across the reporting "
            "period. Detailed findings are presented in subsequent sections of this report.",
            S['body']
        ))

    story.append(PageBreak())


# ── SECTION 2: Key Findings ───────────────────────────────
def build_key_findings(story, S, summary, forecast_summary):
    section_header(story, "02", "Key Findings", S)

    best_g  = summary.get('best_group', 'N/A')
    worst_g = summary.get('worst_group', 'N/A')
    peak_w  = forecast_summary.get('peak_week', 'N/A')
    fc4     = forecast_summary.get('next_4_weeks', 0)
    fc12    = forecast_summary.get('next_12_weeks', 0)

    findings = [
        ("Revenue Scale",
         f"The portfolio generated <b>${summary.get('total_sales',0):,.0f}</b> across "
         f"<b>{summary.get('total_records',0):,}</b> recorded periods, establishing a "
         f"performance baseline of <b>${summary.get('avg_weekly_sales',0):,.0f}</b> per period.",
         'blue'),
        ("Performance Concentration",
         f"Analysis indicates significant performance variation across operating units. "
         f"<b>{best_g}</b> demonstrates the strongest revenue contribution, while "
         f"<b>{worst_g}</b> represents the greatest opportunity for performance improvement.",
         'green') if best_g != 'N/A' else None,
        ("Forecast Outlook",
         f"Revenue projections for the immediate term indicate <b>${fc4:,.0f}</b> over the "
         f"next four periods. Extended forecasts project <b>${fc12:,.0f}</b> over the coming "
         f"twelve periods, with peak demand anticipated around <b>{peak_w}</b>.",
         'amber'),
    ]

    for f in findings:
        if f is None: continue
        title, text, style = f
        story.append(Paragraph(f"<b>{title}</b>", S['h3']))
        callout_box(story, text, style, S)
        story.append(Spacer(1, 0.06*inch))

    story.append(PageBreak())


# ── SECTION 3: Sales Performance Overview ────────────────
def build_sales_overview(story, S, df, date_col, sales_col, summary, company_name):
    section_header(story, "03", "Sales Performance Overview", S)

    story.append(Paragraph(
        "The following analysis presents revenue performance across the full reporting period, "
        "identifying directional trends and key inflection points relevant to operational planning.",
        S['body']
    ))
    story.append(Spacer(1, 0.15*inch))

    # Sales trend chart
    weekly = df.groupby(date_col)[sales_col].sum().reset_index().sort_values(date_col)
    weekly['ma'] = weekly[sales_col].rolling(4, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    ax.fill_between(weekly[date_col], weekly[sales_col],
                    alpha=0.08, color=CH['chart1'])
    ax.plot(weekly[date_col], weekly[sales_col],
            color=CH['chart1'], linewidth=1.2, alpha=0.65, label='Revenue')
    ax.plot(weekly[date_col], weekly['ma'],
            color=CH['chart2'], linewidth=2.2, label='4-Period Moving Average', zorder=5)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(money_fmt))
    title_txt = f"{company_name} — Revenue Trend" if company_name else "Revenue Trend"
    ax.set_title(title_txt, fontsize=11, fontweight='bold',
                 color=CH['chart1'], pad=12)
    ax.tick_params(colors='#4B5563')
    ax.spines['left'].set_color('#D1D5DB')
    ax.spines['bottom'].set_color('#D1D5DB')
    ax.legend(fontsize=8.5, framealpha=0.9, loc='upper left')
    plt.tight_layout(pad=1.2)
    story.append(fig_to_img(fig, height=3.0*inch))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        f"Historical patterns show a peak single-period result of "
        f"<b>${summary.get('max_single_week',0):,.0f}</b>, representing "
        f"<b>{summary.get('max_single_week',0)/max(summary.get('avg_weekly_sales',1),1)*100:.0f}%</b> "
        f"of the period average. This concentration indicates episodic demand surges that "
        f"merit further investigation for replication opportunity.",
        S['body']
    ))
    story.append(PageBreak())


# ── SECTION 4: Trend Analysis ─────────────────────────────
def build_trend_analysis(story, S, monthly_df, company_name):
    section_header(story, "04", "Trend Analysis", S)

    story.append(Paragraph(
        "Period-over-period revenue analysis reveals the underlying demand trajectory and "
        "seasonal dynamics affecting overall portfolio performance.",
        S['body']
    ))
    story.append(Spacer(1, 0.15*inch))

    months_str = [str(m) for m in monthly_df['month']]
    vals       = monthly_df['total'].tolist()

    if len(vals) == 0:
        story.append(Paragraph("Insufficient data for trend analysis.", S['body']))
        story.append(PageBreak())
        return

    avg_val = np.mean(vals)
    bar_clrs = [CH['chart3'] if v >= avg_val * 1.05
                else CH['chart2'] if v >= avg_val * 0.95
                else CH['chart_neg'] for v in vals]

    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    bars = ax.bar(months_str, vals, color=bar_clrs, width=0.65,
                  edgecolor='white', linewidth=0.4)
    ax.axhline(y=avg_val, color=CH['chart5'], linewidth=1.2,
               linestyle='--', alpha=0.8, label=f'Period Average: {money_fmt(avg_val)}')
    for bar, val in zip(bars, vals):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + max(vals)*0.012,
                    money_fmt(val), ha='center', va='bottom',
                    fontsize=6.5, color='#374151', fontweight='500')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(money_fmt))
    ax.set_title("Period Revenue Distribution", fontsize=11, fontweight='bold',
                 color=CH['chart1'], pad=12)
    ax.tick_params(axis='x', rotation=40, labelsize=7.5)
    ax.legend(fontsize=8, framealpha=0.9)
    ax.spines['left'].set_color('#D1D5DB')
    ax.spines['bottom'].set_color('#D1D5DB')
    plt.tight_layout(pad=1.2)
    story.append(fig_to_img(fig, height=3.0*inch))
    story.append(Spacer(1, 0.1*inch))

    # Stats
    best_m  = months_str[vals.index(max(vals))]
    worst_m = months_str[vals.index(min(vals))]
    spread  = (max(vals) - min(vals)) / avg_val * 100 if avg_val > 0 else 0

    callout_box(story,
        f"Peak period: <b>{best_m}</b> ({money_fmt(max(vals))}). "
        f"Trough period: <b>{worst_m}</b> ({money_fmt(min(vals))}). "
        f"Period-to-period spread of <b>{spread:.0f}%</b> indicates "
        f"{'moderate' if spread < 50 else 'significant'} revenue variability.",
        'blue', S)

    story.append(PageBreak())


# ── SECTION 5: Segment Performance ───────────────────────
def build_segment_analysis(story, S, store_df, group_col, company_name):
    section_header(story, "05", "Segment Performance Analysis", S)

    story.append(Paragraph(
        f"The following section benchmarks performance across all {group_col.lower()} segments, "
        f"identifying high-performing units and those presenting improvement opportunities.",
        S['body']
    ))
    story.append(Spacer(1, 0.15*inch))

    top10 = store_df.head(10)
    labels  = top10[group_col].astype(str).tolist()
    rev     = top10['total'].tolist()
    avg_rev = store_df['total'].mean()
    bar_clrs= [CH['chart1'] if i < 3 else CH['chart2'] if i < 7 else CH['chart3']
               for i in range(len(rev))]

    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    bars = ax.bar(labels, rev, color=bar_clrs, width=0.6,
                  edgecolor='white', linewidth=0.4)
    ax.axhline(y=avg_rev, color=CH['chart5'], linewidth=1.2,
               linestyle='--', alpha=0.8, label=f'Portfolio Average: {money_fmt(avg_rev)}')
    for bar, val in zip(bars, rev):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + max(rev)*0.012,
                money_fmt(val), ha='center', va='bottom',
                fontsize=6.5, color='#374151', fontweight='500')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(money_fmt))
    ax.set_title(f"Top {len(top10)} {group_col} Segments by Revenue",
                 fontsize=11, fontweight='bold', color=CH['chart1'], pad=12)
    ax.set_xlabel(group_col, fontsize=9)
    ax.legend(fontsize=8, framealpha=0.9)
    ax.spines['left'].set_color('#D1D5DB')
    ax.spines['bottom'].set_color('#D1D5DB')
    plt.tight_layout(pad=1.2)
    story.append(fig_to_img(fig, height=3.0*inch))
    story.append(Spacer(1, 0.1*inch))

    # Table — top 10
    tbl_data = [[group_col, "Total Revenue", "Avg / Period", "Share of Portfolio"]]
    total_portfolio = store_df['total'].sum()
    for _, row in top10.iterrows():
        share = row['total'] / total_portfolio * 100 if total_portfolio > 0 else 0
        tbl_data.append([
            str(row[group_col]),
            f"${row['total']:,.0f}",
            f"${row['avg_weekly']:,.0f}",
            f"{share:.1f}%",
        ])
    pro_table(story, tbl_data,
              col_widths=[1.8*inch, 1.8*inch, 1.8*inch, 1.5*inch])

    # Pareto insight
    cum = store_df['total'].cumsum()
    n80 = int((cum <= total_portfolio * 0.8).sum()) + 1
    pct = round(n80 / len(store_df) * 100, 1)
    callout_box(story,
        f"<b>Concentration insight:</b> {n80} of {len(store_df)} {group_col.lower()} segments "
        f"({pct:.0f}% of the portfolio) account for 80% of total revenue. "
        f"This concentration profile suggests focused resource allocation "
        f"toward top-performing units will yield disproportionate returns.",
        'green', S)

    story.append(PageBreak())


# ── SECTION 6: Correlations ───────────────────────────────
def build_correlations(story, S, corr_series):
    section_header(story, "06", "External Factors & Correlations", S)

    story.append(Paragraph(
        "Statistical correlation analysis quantifies the relationship between revenue performance "
        "and external environmental variables. Positive coefficients indicate factors that "
        "move in alignment with revenue; negative coefficients suggest inverse relationships.",
        S['body']
    ))
    story.append(Spacer(1, 0.15*inch))

    bar_clrs = [CH['chart_pos'] if v > 0 else CH['chart_neg'] for v in corr_series.values]

    fig, ax = plt.subplots(figsize=(9.5, max(2.8, len(corr_series)*0.45)))
    bars = ax.barh(corr_series.index, corr_series.values,
                   color=bar_clrs, height=0.55, edgecolor='white', linewidth=0.4)
    for bar, val in zip(bars, corr_series.values):
        offset = 0.008 if val >= 0 else -0.008
        ax.text(val + offset, bar.get_y() + bar.get_height()/2,
                f'{val:.4f}', va='center',
                ha='left' if val >= 0 else 'right',
                fontsize=8, color='#374151')
    ax.axvline(x=0, color=CH['gray_dark'], linewidth=0.8)
    ax.set_title("Correlation Coefficients — External Variables vs Revenue",
                 fontsize=11, fontweight='bold', color=CH['chart1'], pad=12)
    ax.set_xlabel("Pearson Correlation Coefficient", fontsize=9)
    ax.spines['left'].set_color('#D1D5DB')
    ax.spines['bottom'].set_color('#D1D5DB')
    plt.tight_layout(pad=1.2)
    story.append(fig_to_img(fig, height=max(2.5*inch, len(corr_series)*0.4*inch)))
    story.append(Spacer(1, 0.1*inch))

    pos = corr_series[corr_series >  0.1]
    neg = corr_series[corr_series < -0.1]
    if not pos.empty:
        callout_box(story,
            f"<b>Positive correlates:</b> {', '.join([f'<b>{k}</b> ({v:.3f})' for k,v in pos.items()])}. "
            f"These factors move in alignment with revenue and represent potential "
            f"performance levers for operational planning.",
            'green', S)
    if not neg.empty:
        callout_box(story,
            f"<b>Inverse correlates:</b> {', '.join([f'<b>{k}</b> ({v:.3f})' for k,v in neg.items()])}. "
            f"Observed trends reveal these variables exert downward pressure on revenue "
            f"and warrant risk mitigation planning.",
            'amber', S)

    story.append(PageBreak())


# ── SECTION 7: Forecast ───────────────────────────────────
def build_forecast_section(story, S, forecast, prophet_data,
                           forecast_summary, company_name):
    section_header(story, "07", "Revenue Forecast", S)

    story.append(Paragraph(
        "Forward-looking revenue projections are derived from historical trend decomposition "
        "and exponential smoothing methodology. Confidence intervals reflect the range of "
        "probable outcomes based on observed volatility patterns.",
        S['body']
    ))
    story.append(Spacer(1, 0.15*inch))

    # Metric strip
    fc4  = forecast_summary.get('next_4_weeks',  0)
    fc8  = forecast_summary.get('next_8_weeks',  0)
    fc12 = forecast_summary.get('next_12_weeks', 0)
    pw   = forecast_summary.get('peak_week',     'N/A')
    ps   = forecast_summary.get('peak_expected_sales', 0)

    metrics = [
        [Paragraph(money_fmt(fc4),  S['metric_value']),
         Paragraph(money_fmt(fc8),  S['metric_value']),
         Paragraph(money_fmt(fc12), S['metric_value'])],
        [Paragraph("Next 4 Periods",  S['metric_label']),
         Paragraph("Next 8 Periods",  S['metric_label']),
         Paragraph("Next 12 Periods", S['metric_label'])],
    ]
    col_w = CONTENT_W / 3
    m_tbl = Table(metrics, colWidths=[col_w]*3, rowHeights=[0.48*inch, 0.28*inch])
    m_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), CH['blue_pale']),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('GRID',         (0,0), (-1,-1), 0.4, CH['border']),
        ('TOPPADDING',   (0,0), (-1,0),  12),
        ('BOTTOMPADDING',(0,-1),(-1,-1), 10),
        ('TOPPADDING',   (0,-1),(-1,-1), 2),
        ('LINEABOVE',    (0,0), (-1,0),  1.5, CH['teal']),
        ('LINEBELOW',    (0,-1),(-1,-1), 1.5, CH['teal']),
    ]))
    story.append(m_tbl)
    story.append(Spacer(1, 0.18*inch))

    future = forecast[forecast['ds'] > prophet_data['ds'].max()]

    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    ax.plot(prophet_data['ds'], prophet_data['y'],
            color=CH['chart1'], linewidth=1.4, label='Historical Revenue', alpha=0.8)
    ax.axvline(x=prophet_data['ds'].max(), color=CH['gray'],
               linewidth=0.8, linestyle=':', alpha=0.7)
    ax.plot(future['ds'], future['yhat'],
            color=CH['teal'], linewidth=2.2, linestyle='--', label='Projected Revenue', zorder=5)
    ax.fill_between(future['ds'], future['yhat_lower'], future['yhat_upper'],
                    alpha=0.12, color=CH['teal'], label='Confidence Range')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(money_fmt))
    title_txt = f"{company_name} — Revenue Projection" if company_name else "Revenue Projection"
    ax.set_title(title_txt, fontsize=11, fontweight='bold',
                 color=CH['chart1'], pad=12)
    ax.legend(fontsize=8.5, framealpha=0.9)
    ax.text(prophet_data['ds'].max(), ax.get_ylim()[1]*0.97,
            ' Forecast\n Start', fontsize=7.5, color=CH['gray'], va='top')
    ax.spines['left'].set_color('#D1D5DB')
    ax.spines['bottom'].set_color('#D1D5DB')
    plt.tight_layout(pad=1.2)
    story.append(fig_to_img(fig, height=3.1*inch))
    story.append(Spacer(1, 0.1*inch))

    callout_box(story,
        f"<b>Peak demand period:</b> {pw} — Projected revenue of "
        f"<b>{money_fmt(ps)}</b>. Historical patterns suggest advance preparation "
        f"in inventory, staffing, and promotional planning is advisable.",
        'teal' if False else 'blue', S)

    story.append(PageBreak())


# ── SECTION 8: Strategic Recommendations ─────────────────
def build_recommendations(story, S, summary, forecast_summary,
                           store_df, group_col):
    section_header(story, "08", "Strategic Recommendations", S)

    story.append(Paragraph(
        "Based on the performance data analyzed in this report, the following strategic "
        "recommendations are presented in order of priority and estimated impact.",
        S['body']
    ))
    story.append(Spacer(1, 0.15*inch))

    best_g  = summary.get('best_group', None)
    worst_g = summary.get('worst_group', None)
    fc12    = forecast_summary.get('next_12_weeks', 0)
    avg_s   = summary.get('avg_weekly_sales', 0)

    recs = []
    recs.append(("Priority 1 — Capitalize on Top Performance",
        f"Performance data indicates <b>{best_g}</b> consistently outperforms portfolio averages. "
        f"A structured replication initiative — identifying and applying the operational "
        f"factors driving this unit's success — could unlock significant incremental revenue "
        f"across underperforming segments.",
        'blue'))

    recs.append(("Priority 2 — Address Underperformance Systematically",
        f"<b>{worst_g}</b> and similarly positioned units require structured performance review. "
        f"Analysis suggests operational realignment, product mix optimization, or targeted "
        f"marketing investment could close the performance gap and recover an estimated "
        f"<b>{money_fmt(avg_s * 4)}</b> annually.",
        'amber'))

    recs.append(("Priority 3 — Align Resources with Forecast Peaks",
        f"Forward projections indicate demand concentration in identifiable periods. "
        f"Proactive resource allocation — inventory pre-positioning, staffing scale-up, "
        f"and promotional scheduling — aligned with the forecast peak of "
        f"<b>{money_fmt(forecast_summary.get('peak_expected_sales',0))}</b> will "
        f"maximize revenue capture during high-demand windows.",
        'green'))

    recs.append(("Priority 4 — Establish Performance Monitoring Cadence",
        f"The revenue variability observed across periods underscores the importance of "
        f"structured performance monitoring. A monthly review process with defined KPI "
        f"thresholds will enable earlier identification of both risk and opportunity.",
        'blue'))

    for title, text, style in recs:
        story.append(Paragraph(f"<b>{title}</b>", S['h3']))
        callout_box(story, text, style, S)
        story.append(Spacer(1, 0.04*inch))

    story.append(PageBreak())


# ── SECTION 9: Appendix ───────────────────────────────────
def build_appendix(story, S, summary, df, date_col, sales_col):
    section_header(story, "09", "Appendix — Data Overview", S)

    story.append(Paragraph(
        "The following tables present the underlying dataset characteristics "
        "and summary statistics referenced throughout this report.",
        S['body']
    ))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph("Dataset Summary", S['h2']))
    meta_data = [
        ["Parameter", "Value"],
        ["Total Records",         f"{summary.get('total_records',0):,}"],
        ["Reporting Period",      summary.get('date_range','N/A')],
        ["Total Revenue",         f"${summary.get('total_sales',0):,.2f}"],
        ["Average per Period",    f"${summary.get('avg_weekly_sales',0):,.2f}"],
        ["Peak Single Period",    f"${summary.get('max_single_week',0):,.2f}"],
        ["Minimum Single Period", f"${summary.get('min_single_week',0):,.2f}"],
        ["Best Segment",          str(summary.get('best_group','N/A'))],
        ["Weakest Segment",       str(summary.get('worst_group','N/A'))],
        ["Number of Segments",    str(summary.get('num_groups','N/A'))],
    ]
    pro_table(story, meta_data,
              col_widths=[2.8*inch, CONTENT_W-2.8*inch])

    story.append(Paragraph("Methodology Notes", S['h2']))
    story.append(Paragraph(
        "Revenue forecasts are generated using Holt-Winters Exponential Smoothing with "
        "additive trend and seasonal components where sufficient data exists. Confidence "
        "intervals are computed at the 95% level based on in-sample residual standard deviation. "
        "Correlation analysis uses Pearson coefficients computed against numeric variables "
        "present in the source dataset. All monetary figures are presented in the native "
        "currency of the source data.",
        S['body']
    ))


# ── Analysis Text Renderer ────────────────────────────────
def _render_analysis_text(story, ai_result, S):
    """Render analysis text with clean professional formatting"""
    table_rows = []

    for line in ai_result.split('\n'):
        raw = line.rstrip()

        # Flush pending table
        if table_rows and not _is_table_row(raw):
            if table_rows:
                _flush_table(story, table_rows, S)
                table_rows = []

        if not raw.strip():
            story.append(Spacer(1, 0.07*inch))
            continue

        # Table rows
        if _is_table_row(raw):
            if not _is_separator(raw):
                cells = [c.strip() for c in raw.strip('|').split('|')]
                table_rows.append(cells)
            continue

        # Headings
        if raw.strip().startswith('### '):
            story.append(Paragraph(_clean_md(raw.strip()), S['h3']))
        elif raw.strip().startswith('## '):
            story.append(Paragraph(_clean_md(raw.strip()), S['h2']))
        elif raw.strip().startswith('# '):
            story.append(Paragraph(_clean_md(raw.strip()), S['h1']))
        elif re.match(r'^-{3,}$', raw.strip()):
            divider(story, space_before=6, space_after=8)
        elif raw.strip().startswith('- ') or raw.strip().startswith('* '):
            content = _clean_md(raw.strip()[2:])
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;{chr(8226)}&nbsp; {content}", S['bullet']))
        elif re.match(r'^\d+\.\s', raw.strip()):
            content = _clean_md(raw.strip())
            story.append(Paragraph(content, S['bullet']))
        else:
            content = _clean_md(raw.strip())
            if content:
                # Financial highlights
                if '$' in content and any(k in content for k in ['Confidence','confidence','High','Medium','Low']):
                    story.append(Paragraph(content, S['callout_blue']))
                else:
                    story.append(Paragraph(content, S['body']))

    if table_rows:
        _flush_table(story, table_rows, S)


def _flush_table(story, rows, S):
    if not rows: return
    n  = max(len(r) for r in rows)
    cw = CONTENT_W / n
    pro_table(story, rows, col_widths=[cw]*n)


# ── MAIN GENERATOR ────────────────────────────────────────
def generate_pdf(
    df, date_col, sales_col,
    summary, store_df, corr_series,
    forecast, prophet_data, forecast_summary,
    monthly_df, group_col,
    company_name, T,
    ai_result=None, ai_type=None
) -> bytes:
    buffer     = io.BytesIO()
    S          = build_styles()
    report_date= pd.Timestamp.now().strftime('%d %B %Y')
    footer_fn  = ReportCanvas(company_name, report_date, {})

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.65*inch, bottomMargin=0.85*inch,
        title=f"Sales Performance Analysis Report",
        author="Business Intelligence Division",
        subject="Confidential Business Analysis",
        creator="Performance Analytics Platform",
    )

    story = []

    # 1. Cover
    build_cover(story, company_name, T, S, summary)

    # 2. TOC
    try:
        build_toc(story, S,
                  has_store=(store_df is not None and group_col is not None),
                  has_corr=(corr_series is not None and len(corr_series) > 0))
    except Exception:
        story.append(PageBreak())

    # 3. Executive Summary
    build_executive_summary(story, S, summary, forecast_summary, ai_result)

    # 4. Key Findings
    build_key_findings(story, S, summary, forecast_summary)

    # 5. Sales Overview
    build_sales_overview(story, S, df, date_col, sales_col, summary, company_name)

    # 6. Trend Analysis
    build_trend_analysis(story, S, monthly_df, company_name)

    # 7. Segment Performance
    if store_df is not None and group_col:
        build_segment_analysis(story, S, store_df, group_col, company_name)

    # 8. Correlations
    if corr_series is not None and len(corr_series) > 0:
        build_correlations(story, S, corr_series)

    # 9. Forecast
    build_forecast_section(story, S, forecast, prophet_data,
                           forecast_summary, company_name)

    # 10. Recommendations
    build_recommendations(story, S, summary, forecast_summary, store_df, group_col)

    # 11. Appendix
    build_appendix(story, S, summary, df, date_col, sales_col)

    doc.build(story, onFirstPage=footer_fn, onLaterPages=footer_fn)
    buffer.seek(0)
    return buffer.read()