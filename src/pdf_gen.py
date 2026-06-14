# src/pdf_gen.py
"""
PDF Generator احترافي بـ ReportLab
- صفحة غلاف باسم الشركة واللغة
- فهرس محتويات
- كل رسم في صفحة كاملة مع شرح
- صفحة توصيات بالأولوية
- footer في كل صفحة
"""

import io
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from reportlab.lib.pagesizes   import A4
from reportlab.lib.units       import inch, cm
from reportlab.lib             import colors
from reportlab.lib.styles      import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums       import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus        import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether
)

# ── ألوان الـ brand ──────────────────────────────────────
BLUE       = colors.HexColor('#1E40AF')
BLUE_LIGHT = colors.HexColor('#DBEAFE')
BLUE_MID   = colors.HexColor('#3B82F6')
GREEN      = colors.HexColor('#16A34A')
GREEN_LIGHT= colors.HexColor('#DCFCE7')
RED        = colors.HexColor('#DC2626')
RED_LIGHT  = colors.HexColor('#FEE2E2')
AMBER      = colors.HexColor('#D97706')
GRAY       = colors.HexColor('#6B7280')
GRAY_LIGHT = colors.HexColor('#F9FAFB')
DARK       = colors.HexColor('#111827')
WHITE      = colors.white

PAGE_W, PAGE_H = A4


# ── Styles ───────────────────────────────────────────────
def make_styles():
    s = getSampleStyleSheet()

    cover_company = ParagraphStyle('cover_company',
        fontSize=32, fontName='Helvetica-Bold',
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=8, leading=38)

    cover_title = ParagraphStyle('cover_title',
        fontSize=18, fontName='Helvetica',
        textColor=colors.HexColor('#BFDBFE'), alignment=TA_CENTER, spaceAfter=6)

    cover_date = ParagraphStyle('cover_date',
        fontSize=11, fontName='Helvetica',
        textColor=colors.HexColor('#93C5FD'), alignment=TA_CENTER)

    h1 = ParagraphStyle('h1',
        fontSize=18, fontName='Helvetica-Bold',
        textColor=BLUE, spaceBefore=18, spaceAfter=10,
        borderPad=4)

    h2 = ParagraphStyle('h2',
        fontSize=13, fontName='Helvetica-Bold',
        textColor=BLUE, spaceBefore=12, spaceAfter=6)

    body = ParagraphStyle('body',
        fontSize=10, fontName='Helvetica',
        textColor=DARK, leading=15, spaceAfter=6)

    body_small = ParagraphStyle('body_small',
        fontSize=9, fontName='Helvetica',
        textColor=GRAY, leading=13, spaceAfter=4)

    footer_style = ParagraphStyle('footer_style',
        fontSize=8, fontName='Helvetica',
        textColor=GRAY, alignment=TA_CENTER)

    toc_item = ParagraphStyle('toc_item',
        fontSize=11, fontName='Helvetica',
        textColor=DARK, spaceAfter=8, leading=16)

    highlight_box = ParagraphStyle('highlight_box',
        fontSize=10, fontName='Helvetica-Bold',
        textColor=BLUE, backColor=BLUE_LIGHT,
        borderPad=8, leading=15, spaceAfter=6)

    insight = ParagraphStyle('insight',
        fontSize=10, fontName='Helvetica',
        textColor=DARK, leading=15, spaceAfter=5,
        leftIndent=12)

    return dict(
        cover_company=cover_company,
        cover_title=cover_title,
        cover_date=cover_date,
        h1=h1, h2=h2,
        body=body, body_small=body_small,
        footer_style=footer_style,
        toc_item=toc_item,
        highlight_box=highlight_box,
        insight=insight,
    )


# ── Footer على كل صفحة ───────────────────────────────────
class FooterCanvas:
    """Mixin — يُضاف للـ doc عبر onPage"""
    def __init__(self, company_name, T):
        self.company_name = company_name
        self.T = T

    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(GRAY)
        canvas.setFont('Helvetica', 8)
        footer_left  = self.company_name if self.company_name else self.T.get("app_title","Sales Analysis Agent")
        footer_right = f"{self.T.get('pdf_generated','Generated')}: {pd.Timestamp.now().strftime('%Y-%m-%d')}"
        page_num     = f"— {doc.page} —"
        canvas.drawString(inch*0.75, 0.5*inch, footer_left)
        canvas.drawRightString(PAGE_W - inch*0.75, 0.5*inch, footer_right)
        canvas.drawCentredString(PAGE_W/2, 0.5*inch, page_num)
        # خط فاصل
        canvas.setStrokeColor(colors.HexColor('#E5E7EB'))
        canvas.setLineWidth(0.5)
        canvas.line(inch*0.75, 0.65*inch, PAGE_W - inch*0.75, 0.65*inch)
        canvas.restoreState()


# ── مساعد: رسم matplotlib → Image flowable ───────────────
def fig_to_image(fig, width=6.5*inch, height=3.2*inch):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width, height=height)


def fmt_money(x):
    if x >= 1e6: return f'${x/1e6:.1f}M'
    if x >= 1e3: return f'${x/1e3:.0f}K'
    return f'${x:.0f}'

def money_formatter(x, pos):
    return fmt_money(x)


# ── صفحة الغلاف ──────────────────────────────────────────
def build_cover(story, company_name, T, ST, summary):
    # خلفية زرقاء كاملة عبر جدول ملون
    cover_data = [['']]
    cover_table = Table(cover_data, colWidths=[PAGE_W - 1.5*inch], rowHeights=[3.5*inch])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BLUE),
        ('ROUNDEDCORNERS', [8]),
    ]))

    story.append(Spacer(1, 0.5*inch))
    story.append(cover_table)
    # نصوص فوق الجدول — نستخدم Spacer سالب للتراكب بطريقة بسيطة
    # بدلاً من ذلك نبني table بمحتوى نصي
    story.pop()  # نحذف الجدول الفارغ

    # الغلاف الحقيقي
    cname_text = company_name if company_name else T.get("app_title","Sales Analysis Agent")
    date_range = summary.get('date_range','')

    cover_content = [
        [Paragraph(cname_text,            ST['cover_company'])],
        [Paragraph(T.get('pdf_title','Sales Analysis Report'), ST['cover_title'])],
        [Paragraph(date_range,            ST['cover_date'])],
        [Paragraph(
            f"{T.get('pdf_generated','Generated')}: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
            ST['cover_date']
        )],
    ]
    cover_tbl = Table(cover_content, colWidths=[PAGE_W - 1.5*inch],
                      rowHeights=[0.8*inch, 0.4*inch, 0.35*inch, 0.35*inch])
    cover_tbl.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,-1), BLUE),
        ('ALIGN',       (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',  (0,0), (0,0),   28),
        ('BOTTOMPADDING',(0,-1),(-1,-1),20),
        ('ROUNDEDCORNERS',[10]),
    ]))
    story.append(Spacer(1, 0.5*inch))
    story.append(cover_tbl)
    story.append(Spacer(1, 0.35*inch))

    # مربعات الأرقام الكبيرة
    metrics = [
        [
            Paragraph(f"<b>{summary['total_records']:,}</b>", ParagraphStyle('m',
                fontSize=22, fontName='Helvetica-Bold', textColor=BLUE, alignment=TA_CENTER)),
            Paragraph(f"<b>{fmt_money(summary['total_sales'])}</b>", ParagraphStyle('m',
                fontSize=22, fontName='Helvetica-Bold', textColor=GREEN, alignment=TA_CENTER)),
            Paragraph(f"<b>{fmt_money(summary['avg_weekly_sales'])}</b>", ParagraphStyle('m',
                fontSize=22, fontName='Helvetica-Bold', textColor=AMBER, alignment=TA_CENTER)),
        ],
        [
            Paragraph(T.get('total_records','Records'), ParagraphStyle('ml',
                fontSize=9, fontName='Helvetica', textColor=GRAY, alignment=TA_CENTER)),
            Paragraph(T.get('total_sales','Total Sales'), ParagraphStyle('ml',
                fontSize=9, fontName='Helvetica', textColor=GRAY, alignment=TA_CENTER)),
            Paragraph(T.get('avg_period','Avg / Period'), ParagraphStyle('ml',
                fontSize=9, fontName='Helvetica', textColor=GRAY, alignment=TA_CENTER)),
        ],
    ]
    col_w = (PAGE_W - 1.5*inch) / 3
    metrics_tbl = Table(metrics, colWidths=[col_w]*3, rowHeights=[0.45*inch, 0.28*inch])
    metrics_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), GRAY_LIGHT),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('GRID',         (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('TOPPADDING',   (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0), (-1,-1), 6),
        ('ROUNDEDCORNERS',[6]),
    ]))
    story.append(metrics_tbl)
    story.append(PageBreak())


# ── فهرس المحتويات ───────────────────────────────────────
def build_toc(story, T, ST, has_store, has_corr, has_ai):
    story.append(Paragraph("📑 " + ("Table of Contents" if True else ""), ST['h1']))
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE_LIGHT))
    story.append(Spacer(1, 0.15*inch))

    sections = [
        ("1", T.get('data_summary','Data Summary'),      "3"),
        ("2", T.get('sales_trend','Sales Trend'),        "4"),
        ("3", T.get('monthly_sales','Monthly Sales'),    "5"),
    ]
    page = 6
    if has_store:
        sections.append(("4", T.get('tab_overview','Store Performance'), str(page))); page+=1
    if has_corr:
        sections.append((str(len(sections)+1), T.get('correlation','Correlations'), str(page))); page+=1
    sections.append((str(len(sections)+1), T.get('forecast_title','Forecast'), str(page))); page+=1
    if has_ai:
        sections.append((str(len(sections)+1), T.get('pdf_ai_section','AI Analysis'), str(page)))

    toc_data = []
    for num, title, pg in sections:
        toc_data.append([
            Paragraph(f"<b>{num}.</b>", ST['toc_item']),
            Paragraph(title, ST['toc_item']),
            Paragraph(pg, ParagraphStyle('pg', fontSize=11, fontName='Helvetica',
                          textColor=BLUE, alignment=TA_RIGHT, spaceAfter=8)),
        ])

    toc_tbl = Table(toc_data, colWidths=[0.4*inch, 4.5*inch, 1.6*inch])
    toc_tbl.setStyle(TableStyle([
        ('ALIGN',        (2,0), (2,-1), 'RIGHT'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[WHITE, GRAY_LIGHT]),
        ('TOPPADDING',   (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0), (-1,-1), 5),
        ('LEFTPADDING',  (0,0), (-1,-1), 8),
        ('LINEBELOW',    (0,0), (-1,-2), 0.3, colors.HexColor('#E5E7EB')),
    ]))
    story.append(toc_tbl)
    story.append(PageBreak())


# ── جدول المؤشرات ─────────────────────────────────────────
def build_metrics_table(story, T, ST, summary):
    story.append(Paragraph(f"1. {T.get('data_summary','Data Summary')}", ST['h1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE))
    story.append(Spacer(1, 0.1*inch))

    data = [
        [T.get('pdf_metric','Metric'),     T.get('pdf_value','Value')],
        [T.get('total_records','Records'), f"{summary['total_records']:,}"],
        [T.get('pdf_date_range','Date Range'), summary.get('date_range','N/A')],
        [T.get('total_sales','Total Sales'),   f"${summary['total_sales']:,.2f}"],
        [T.get('pdf_avg_period','Avg/Period'), f"${summary['avg_weekly_sales']:,.2f}"],
        [T.get('pdf_best_period','Best Period'),f"${summary['max_single_week']:,.2f}"],
    ]
    if summary.get('best_group'):
        data.append([("Best Performer" if True else ""), str(summary['best_group'])])
    if summary.get('worst_group'):
        data.append([("Worst Performer" if True else ""), str(summary['worst_group'])])

    tbl = Table(data, colWidths=[3*inch, 3.5*inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0),  BLUE),
        ('TEXTCOLOR',    (0,0), (-1,0),  WHITE),
        ('FONTNAME',     (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [WHITE, GRAY_LIGHT]),
        ('GRID',         (0,0), (-1,-1), 0.4, colors.HexColor('#E5E7EB')),
        ('PADDING',      (0,0), (-1,-1), 9),
        ('FONTNAME',     (0,1), (0,-1),  'Helvetica-Bold'),
        ('TEXTCOLOR',    (0,1), (0,-1),  BLUE),
    ]))
    story.append(tbl)
    story.append(PageBreak())


# ── رسم المبيعات الأسبوعية ────────────────────────────────
def build_sales_trend(story, T, ST, df, date_col, sales_col, company_name):
    story.append(Paragraph(f"2. {T.get('sales_trend','Sales Trend')}", ST['h1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE))
    story.append(Spacer(1, 0.1*inch))

    weekly = df.groupby(date_col)[sales_col].sum().reset_index().sort_values(date_col)
    weekly['ma4'] = weekly[sales_col].rolling(4).mean()

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.fill_between(weekly[date_col], weekly[sales_col],
                    alpha=0.15, color='#2563EB')
    ax.plot(weekly[date_col], weekly[sales_col],
            color='#2563EB', linewidth=1.2, alpha=0.7, label='Weekly Sales')
    ax.plot(weekly[date_col], weekly['ma4'],
            color='#DC2626', linewidth=2.5, label=T.get('period_avg','4-Period Avg'))
    title = f"{company_name} — {T.get('sales_trend','Sales Trend')}" if company_name else T.get('sales_trend','Sales Trend')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(money_formatter))
    ax.legend(fontsize=9); ax.grid(True, alpha=0.25); ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    story.append(fig_to_image(fig, width=6.5*inch, height=3.2*inch))
    story.append(Spacer(1, 0.15*inch))

    # شرح الرسم
    peak_date = weekly.loc[weekly[sales_col].idxmax(), date_col]
    peak_val  = weekly[sales_col].max()
    story.append(Paragraph(
        f"📌 {T.get('peak_info','Peak')}: <b>{str(peak_date)[:10]}</b> → <b>{fmt_money(peak_val)}</b>",
        ST['highlight_box']
    ))
    story.append(PageBreak())


# ── رسم المبيعات الشهرية ──────────────────────────────────
def build_monthly(story, T, ST, monthly_df, company_name):
    story.append(Paragraph(f"3. {T.get('monthly_sales','Monthly Sales')}", ST['h1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE))
    story.append(Spacer(1, 0.1*inch))

    months = [str(m) for m in monthly_df['month']]
    vals   = monthly_df['total'].tolist()

    bar_colors = ['#16A34A' if v >= pd.Series(vals).quantile(0.6) else
                  '#D97706' if v >= pd.Series(vals).quantile(0.3) else
                  '#DC2626' for v in vals]

    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.bar(months, vals, color=bar_colors, alpha=0.85, edgecolor='white', linewidth=0.5)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(vals)*0.01,
                fmt_money(val), ha='center', va='bottom', fontsize=7, color='#374151')
    title = f"{company_name} — {T.get('monthly_sales','Monthly Sales')}" if company_name else T.get('monthly_sales','Monthly Sales')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(money_formatter))
    ax.grid(True, axis='y', alpha=0.25)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    plt.xticks(rotation=45, ha='right', fontsize=7); plt.tight_layout()
    story.append(fig_to_image(fig, width=6.5*inch, height=3.2*inch))
    story.append(Spacer(1, 0.15*inch))

    best_month = months[vals.index(max(vals))]
    worst_month= months[vals.index(min(vals))]
    story.append(Paragraph(
        f"🟢 Best month: <b>{best_month}</b> ({fmt_money(max(vals))})   "
        f"🔴 Worst month: <b>{worst_month}</b> ({fmt_money(min(vals))})",
        ST['highlight_box']
    ))
    story.append(PageBreak())


# ── رسم المتاجر ───────────────────────────────────────────
def build_store_chart(story, T, ST, store_df, group_col, company_name):
    section_num = "4"
    story.append(Paragraph(f"{section_num}. {T.get('performance_by','Performance by')} {group_col}", ST['h1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE))
    story.append(Spacer(1, 0.1*inch))

    top10 = store_df.head(10)
    fig, ax = plt.subplots(figsize=(9, 4))
    bar_colors = ['#1E40AF' if i < 3 else '#3B82F6' if i < 7 else '#93C5FD'
                  for i in range(len(top10))]
    bars = ax.bar(top10[group_col].astype(str), top10['total'],
                  color=bar_colors, alpha=0.9, edgecolor='white', linewidth=0.5)
    for bar, val in zip(bars, top10['total']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + top10['total'].max()*0.01,
                fmt_money(val), ha='center', va='bottom', fontsize=7.5)
    title = f"{company_name} — Top {group_col}s" if company_name else f"Top {group_col}s"
    ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(money_formatter))
    ax.grid(True, axis='y', alpha=0.25)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    plt.tight_layout()
    story.append(fig_to_image(fig, width=6.5*inch, height=3.2*inch))
    story.append(Spacer(1, 0.15*inch))

    # جدول top 5
    story.append(Paragraph(f"Top 5 {group_col}s", ST['h2']))
    top5 = store_df.head(5)
    tbl_data = [[group_col, 'Total Sales', 'Avg/Period']]
    for _, row in top5.iterrows():
        tbl_data.append([str(row[group_col]), fmt_money(row['total']), fmt_money(row['avg_weekly'])])
    tbl = Table(tbl_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0),  BLUE),
        ('TEXTCOLOR',    (0,0), (-1,0),  WHITE),
        ('FONTNAME',     (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [WHITE, GRAY_LIGHT]),
        ('GRID',         (0,0), (-1,-1), 0.4, colors.HexColor('#E5E7EB')),
        ('PADDING',      (0,0), (-1,-1), 8),
        ('ALIGN',        (1,0), (-1,-1), 'RIGHT'),
    ]))
    story.append(tbl)
    story.append(PageBreak())


# ── رسم الارتباط ─────────────────────────────────────────
def build_correlation(story, T, ST, corr_series, company_name):
    story.append(Paragraph(f"📊 {T.get('correlation','Correlation with Sales')}", ST['h1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE))
    story.append(Spacer(1, 0.1*inch))

    fig, ax = plt.subplots(figsize=(7, 3.5))
    bar_colors = ['#16A34A' if v > 0 else '#DC2626' for v in corr_series.values]
    bars = ax.barh(corr_series.index, corr_series.values, color=bar_colors, alpha=0.85)
    for bar, val in zip(bars, corr_series.values):
        ax.text(val + (0.003 if val > 0 else -0.003),
                bar.get_y() + bar.get_height()/2,
                f'{val:.4f}', va='center', ha='left' if val > 0 else 'right', fontsize=9)
    ax.axvline(x=0, color='black', linewidth=0.8)
    ax.set_title(T.get('correlation','Correlation with Sales'), fontsize=13, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.25)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    plt.tight_layout()
    story.append(fig_to_image(fig, width=6.5*inch, height=2.8*inch))
    story.append(Spacer(1, 0.15*inch))

    pos = corr_series[corr_series > 0.1]
    neg = corr_series[corr_series < -0.1]
    if not pos.empty:
        story.append(Paragraph(
            f"🟢 Positive factors: {', '.join([f'{k} ({v:.3f})' for k,v in pos.items()])}",
            ST['insight']
        ))
    if not neg.empty:
        story.append(Paragraph(
            f"🔴 Negative factors: {', '.join([f'{k} ({v:.3f})' for k,v in neg.items()])}",
            ST['insight']
        ))
    story.append(PageBreak())


# ── رسم التوقعات ──────────────────────────────────────────
def build_forecast(story, T, ST, forecast, prophet_data, forecast_summary, company_name):
    story.append(Paragraph(f"🔮 {T.get('forecast_title','Sales Forecast')}", ST['h1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GREEN))
    story.append(Spacer(1, 0.1*inch))

    # metrics row
    m_data = [[
        Paragraph(f"<b>{fmt_money(forecast_summary['next_4_weeks'])}</b>",
            ParagraphStyle('mv', fontSize=18, fontName='Helvetica-Bold', textColor=BLUE, alignment=TA_CENTER)),
        Paragraph(f"<b>{fmt_money(forecast_summary['next_8_weeks'])}</b>",
            ParagraphStyle('mv', fontSize=18, fontName='Helvetica-Bold', textColor=GREEN, alignment=TA_CENTER)),
        Paragraph(f"<b>{fmt_money(forecast_summary['next_12_weeks'])}</b>",
            ParagraphStyle('mv', fontSize=18, fontName='Helvetica-Bold', textColor=AMBER, alignment=TA_CENTER)),
    ],[
        Paragraph(T.get('next_4','Next 4 Weeks'),
            ParagraphStyle('ml', fontSize=9, fontName='Helvetica', textColor=GRAY, alignment=TA_CENTER)),
        Paragraph(T.get('next_8','Next 8 Weeks'),
            ParagraphStyle('ml', fontSize=9, fontName='Helvetica', textColor=GRAY, alignment=TA_CENTER)),
        Paragraph(T.get('next_12','Next 12 Weeks'),
            ParagraphStyle('ml', fontSize=9, fontName='Helvetica', textColor=GRAY, alignment=TA_CENTER)),
    ]]
    cw = (PAGE_W - 1.5*inch) / 3
    mt = Table(m_data, colWidths=[cw]*3, rowHeights=[0.5*inch, 0.3*inch])
    mt.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), GRAY_LIGHT),
        ('GRID',         (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',   (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0), (-1,-1), 5),
    ]))
    story.append(mt)
    story.append(Spacer(1, 0.15*inch))

    # رسم التوقعات
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(prophet_data['ds'], prophet_data['y'], color='#2563EB',
            linewidth=1.2, label=T.get('historical','Historical'), alpha=0.8)
    future = forecast[forecast['ds'] > prophet_data['ds'].max()]
    ax.plot(future['ds'], future['yhat'], color='#DC2626',
            linewidth=2.5, label=T.get('forecast_label','Forecast'), linestyle='--')
    ax.fill_between(future['ds'], future['yhat_lower'], future['yhat_upper'],
                    alpha=0.12, color='#DC2626', label='Confidence Interval')
    # خط فاصل بين التاريخي والتوقعات
    ax.axvline(x=prophet_data['ds'].max(), color='gray', linewidth=1, linestyle=':')
    title = f"{company_name} — {T.get('forecast_title','Forecast')}" if company_name else T.get('forecast_title','Forecast')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(money_formatter))
    ax.legend(fontsize=9); ax.grid(True, alpha=0.25)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    plt.tight_layout()
    story.append(fig_to_image(fig, width=6.5*inch, height=3.2*inch))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        f"📅 {T.get('peak_info','Peak week')}: <b>{forecast_summary['peak_week']}</b> "
        f"→ <b>{fmt_money(forecast_summary['peak_expected_sales'])}</b>",
        ST['highlight_box']
    ))
    story.append(PageBreak())


# ── صفحة التحليل AI ───────────────────────────────────────
def _md_to_rl(text):
    """
    يحوّل Markdown inline إلى ReportLab XML:
    **bold** → <b>bold</b>
    *italic* → <i>italic</i>
    `code`   → <font name="Courier">code</font>
    يزيل أي رموز متبقية
    """
    import re
    # أزل ### ## # في بداية السطر (تُعالج خارجياً)
    text = re.sub(r'^#{1,4}\s*', '', text)
    # **bold**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # *italic*
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # `code`
    text = re.sub(r'`(.+?)`', r'<font name="Courier">\1</font>', text)
    # escape & < > (ما كانت جزء من تاغات)
    # نحافظ على التاغات الموجودة
    return text


def build_ai_section(story, T, ST, ai_result, ai_type):
    story.append(Paragraph(f"🤖 {T.get('pdf_ai_section','AI Analysis')}", ST['h1']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(f"<i>{ai_type}</i>", ST['body_small']))
    story.append(Spacer(1, 0.1*inch))

    import re

    # Style خاص لصناديق الـ Confidence
    confidence_style = ParagraphStyle('conf',
        fontSize=9, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1E40AF'),
        backColor=colors.HexColor('#EFF6FF'),
        borderPad=5, leading=13, spaceAfter=4,
        leftIndent=8
    )
    alert_style = ParagraphStyle('alert',
        fontSize=9, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#DC2626'),
        backColor=colors.HexColor('#FEF2F2'),
        borderPad=5, leading=13, spaceAfter=4,
        leftIndent=8
    )
    money_style = ParagraphStyle('money',
        fontSize=9, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#16A34A'),
        backColor=colors.HexColor('#F0FDF4'),
        borderPad=5, leading=13, spaceAfter=4,
        leftIndent=8
    )

    for line in ai_result.split('\n'):
        raw = line.strip()
        if not raw:
            story.append(Spacer(1, 0.06*inch))
            continue

        # ── عناوين H1 # و H2 ## و H3 ###
        if raw.startswith('### '):
            txt = _md_to_rl(raw[4:])
            story.append(Paragraph(txt, ST['h2']))

        elif raw.startswith('## '):
            txt = _md_to_rl(raw[3:])
            story.append(Paragraph(txt, ST['h2']))

        elif raw.startswith('# '):
            txt = _md_to_rl(raw[2:])
            story.append(Paragraph(txt, ST['h1']))

        # ── خط فاصل ---
        elif re.match(r'^-{3,}$', raw):
            story.append(Spacer(1, 0.05*inch))
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.HexColor('#E5E7EB')))
            story.append(Spacer(1, 0.05*inch))

        # ── نقاط القائمة - و •
        elif raw.startswith('- ') or raw.startswith('• '):
            content = raw[2:]
            txt = _md_to_rl(content)
            # Confidence → صندوق أزرق
            if '🎯' in txt or 'Confidence' in txt or 'مستوى الثقة' in txt:
                story.append(Paragraph(f"🎯 {txt}", confidence_style))
            # تحذير → صندوق أحمر
            elif '🚨' in txt or '⚠️' in txt or 'CRITICAL' in txt:
                story.append(Paragraph(f"• {txt}", alert_style))
            # مالي → صندوق أخضر
            elif '💰' in txt or '$' in txt:
                story.append(Paragraph(f"• {txt}", money_style))
            else:
                story.append(Paragraph(f"• {txt}", ST['insight']))

        # ── أسطر مرقمة 1. 2. 3.
        elif re.match(r'^\d+\.\s', raw):
            txt = _md_to_rl(raw)
            story.append(Paragraph(txt, ST['insight']))

        # ── جداول Markdown | col | col |
        elif raw.startswith('|') and raw.endswith('|'):
            # تجاهل سطر الفواصل |---|---|
            if re.match(r'^\|[\s\-\|]+\|$', raw):
                continue
            cells = [c.strip() for c in raw.strip('|').split('|')]
            # نبنيه كـ table بسيط
            if not hasattr(build_ai_section, '_table_rows'):
                build_ai_section._table_rows = []
            build_ai_section._table_rows.append(cells)
            continue

        # ── نص عادي
        else:
            txt = _md_to_rl(raw)
            # Confidence inline في نص عادي
            if '🎯' in txt:
                story.append(Paragraph(txt, confidence_style))
            elif '💰' in txt or ('$' in txt and len(txt) < 120):
                story.append(Paragraph(txt, money_style))
            elif '🚨' in txt or '⚠️' in txt:
                story.append(Paragraph(txt, alert_style))
            else:
                story.append(Paragraph(txt, ST['body']))

        # ── flush الجدول المتراكم
        if hasattr(build_ai_section, '_table_rows') and build_ai_section._table_rows:
            rows = build_ai_section._table_rows
            del build_ai_section._table_rows
            if rows:
                n_cols = max(len(r) for r in rows)
                col_w  = (PAGE_W - 1.5*inch) / n_cols
                tbl = Table(rows, colWidths=[col_w]*n_cols)
                tbl.setStyle(TableStyle([
                    ('BACKGROUND',  (0,0), (-1,0),  BLUE),
                    ('TEXTCOLOR',   (0,0), (-1,0),  WHITE),
                    ('FONTNAME',    (0,0), (-1,0),  'Helvetica-Bold'),
                    ('FONTNAME',    (0,1), (-1,-1), 'Helvetica'),
                    ('FONTSIZE',    (0,0), (-1,-1), 8),
                    ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE, GRAY_LIGHT]),
                    ('GRID',        (0,0), (-1,-1), 0.3, colors.HexColor('#E5E7EB')),
                    ('PADDING',     (0,0), (-1,-1), 5),
                    ('ALIGN',       (0,0), (-1,-1), 'LEFT'),
                ]))
                story.append(tbl)
                story.append(Spacer(1, 0.1*inch))


# ── الدالة الرئيسية ───────────────────────────────────────
def generate_pdf(
    df, date_col, sales_col,
    summary, store_df, corr_series,
    forecast, prophet_data, forecast_summary,
    monthly_df, group_col,
    company_name, T,
    ai_result=None, ai_type=None
) -> bytes:
    """
    يولد PDF احترافي ويرجع bytes جاهز للتنزيل
    """
    buffer = io.BytesIO()
    ST     = make_styles()
    footer = FooterCanvas(company_name, T)

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=0.75*inch, leftMargin=0.75*inch,
        topMargin=0.85*inch,   bottomMargin=0.85*inch,
        title=f"{company_name} Sales Report" if company_name else "Sales Report",
        author="Sales Analysis Agent",
    )

    story = []

    # 1. غلاف
    build_cover(story, company_name, T, ST, summary)

    # 2. فهرس
    build_toc(story, T, ST,
              has_store=(store_df is not None),
              has_corr=(corr_series is not None),
              has_ai=(ai_result is not None))

    # 3. مؤشرات
    build_metrics_table(story, T, ST, summary)

    # 4. اتجاه المبيعات
    build_sales_trend(story, T, ST, df, date_col, sales_col, company_name)

    # 5. شهري
    build_monthly(story, T, ST, monthly_df, company_name)

    # 6. متاجر
    if store_df is not None and group_col:
        build_store_chart(story, T, ST, store_df, group_col, company_name)

    # 7. ارتباطات
    if corr_series is not None and len(corr_series) > 0:
        build_correlation(story, T, ST, corr_series, company_name)

    # 8. توقعات
    build_forecast(story, T, ST, forecast, prophet_data, forecast_summary, company_name)

    # 9. AI
    if ai_result:
        build_ai_section(story, T, ST, ai_result, ai_type or "")

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer.read()