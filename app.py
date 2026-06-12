import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from src.translations import get_translations

load_dotenv()

st.set_page_config(page_title="Sales Analysis Agent", page_icon="📊", layout="wide")

# ─── اختيار اللغة (أول شيء يُحدد) ───────────────────────
lang_options = {"English": "en", "العربية": "ar", "Français": "fr"}
lang_label = st.sidebar.selectbox("🌐 Language / اللغة / Langue", list(lang_options.keys()))
lang = lang_options[lang_label]
T = get_translations(lang)

# ─── CSS + اتجاه الصفحة ──────────────────────────────────
direction = "rtl" if lang == "ar" else "ltr"
st.markdown(f"""
<style>
    .main-header {{
        font-size: 2.2rem; font-weight: 700; color: #1E40AF;
        text-align: center; padding: 1rem 0;
        direction: {direction};
    }}
    .sub-header {{
        font-size: 1rem; color: #6B7280;
        text-align: center; margin-bottom: 2rem;
        direction: {direction};
    }}
    .stApp {{ direction: {direction}; }}
</style>
""", unsafe_allow_html=True)

st.markdown(f'<p class="main-header">{T["app_title"]}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">{T["app_subtitle"]}</p>', unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────
with st.sidebar:
    st.header(T["settings"])

    # اسم الشركة
    company_name = st.text_input(
        T["company_name"],
        placeholder=T["company_placeholder"],
        value=st.session_state.get("company_name", "")
    )
    st.session_state.company_name = company_name

    st.subheader(T["upload_data"])
    uploaded_file = st.file_uploader(T["upload_hint"], type=['csv', 'xlsx', 'xls'])

    date_col = None
    sales_col = None

    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                try:
                    preview_df = pd.read_csv(uploaded_file)
                except Exception:
                    uploaded_file.seek(0)
                    preview_df = pd.read_csv(uploaded_file, encoding='latin1')
            else:
                preview_df = pd.read_excel(uploaded_file)
            uploaded_file.seek(0)

            preview_df.columns = preview_df.columns.str.strip()
            cols = preview_df.columns.tolist()

            st.subheader(T["map_columns"])
            st.caption(T["date_warning"])

            date_options = [c for c in cols if any(
                x in c.lower() for x in ['date', 'time', 'week', 'month', 'year', 'day', 'تاريخ']
            )] or cols

            date_col = st.selectbox(T["date_col"], options=cols,
                index=cols.index(date_options[0]) if date_options else 0)

            sales_options = [c for c in cols if any(
                x in c.lower() for x in ['sale', 'revenue', 'amount', 'total', 'مبيع', 'إيراد', 'vente']
            )] or cols

            sales_col = st.selectbox(T["sales_col"], options=cols,
                index=cols.index(sales_options[0]) if sales_options else 0)

            analyze_btn = st.button(T["analyze_btn"], type="primary", use_container_width=True)

        except Exception as e:
            st.error(f"Error reading file: {e}")
            analyze_btn = False
    else:
        analyze_btn = False
        st.info(T["upload_prompt"])

    st.divider()
    st.caption(T["built_with"])

# ─── Session State ────────────────────────────────────────
for key, default in [
    ('analyzed', False),
    ('chat_history', []),
    ('system_prompt', None),
    ('lang', lang),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# اللغة تغيرت → أعد التهيئة
if st.session_state.lang != lang:
    st.session_state.chat_history = []
    st.session_state.lang = lang

# ─── التحليل ─────────────────────────────────────────────
if analyze_btn and uploaded_file and date_col and sales_col:

    with st.spinner("🔄 " + ("Loading and cleaning data..." if lang == "en" else
                              "تحميل وتنظيف البيانات..." if lang == "ar" else
                              "Chargement et nettoyage...")):
        try:
            uploaded_file.seek(0)
            if uploaded_file.name.endswith('.csv'):
                try:
                    raw_df = pd.read_csv(uploaded_file)
                except Exception:
                    uploaded_file.seek(0)
                    raw_df = pd.read_csv(uploaded_file, encoding='latin1')
            else:
                raw_df = pd.read_excel(uploaded_file)

            raw_df.columns = raw_df.columns.str.strip()
            date_col = date_col.strip()
            sales_col = sales_col.strip()
            raw_df[date_col] = pd.to_datetime(raw_df[date_col], errors='coerce')

            from src.data_cleaner import clean_data
            df, report = clean_data(raw_df, date_col=date_col, sales_col=sales_col)
            df = df.dropna(subset=[date_col])
            df = df.sort_values(date_col).reset_index(drop=True)

            st.session_state.df       = df
            st.session_state.date_col = date_col
            st.session_state.sales_col = sales_col
            st.session_state.report   = report

        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            st.stop()

    with st.spinner("📊 " + ("Analyzing..." if lang == "en" else "جاري التحليل..." if lang == "ar" else "Analyse en cours...")):
        from src.data_loader import get_summary
        from src.analyzer import holiday_vs_normal

        df = st.session_state.df
        summary = get_summary(df, date_col, sales_col)
        group_col = summary.get('group_col')

        store_df = None
        if group_col:
            store_df = (
                df.groupby(group_col)[sales_col]
                .agg(['sum', 'mean'])
                .rename(columns={'sum': 'total', 'mean': 'avg_weekly'})
                .reset_index()
                .sort_values('total', ascending=False)
            )

        df_monthly = df.copy()
        df_monthly['month'] = df_monthly[date_col].dt.to_period('M')
        monthly_df = (
            df_monthly.groupby('month')[sales_col]
            .sum().reset_index()
            .rename(columns={sales_col: 'total'})
        )

        holiday_df = None
        if 'Holiday_Flag' in df.columns:
            holiday_df = holiday_vs_normal(df)

        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        if sales_col in numeric_cols:
            numeric_cols.remove(sales_col)
        corr_series = df[[sales_col] + numeric_cols].corr()[sales_col].drop(sales_col).round(4) if numeric_cols else None

        st.session_state.summary    = summary
        st.session_state.store_df   = store_df
        st.session_state.monthly_df = monthly_df
        st.session_state.holiday_df = holiday_df
        st.session_state.corr_series = corr_series
        st.session_state.group_col  = group_col

    with st.spinner("🔮 " + ("Forecasting..." if lang == "en" else "جاري التنبؤ..." if lang == "ar" else "Prévision en cours...")):
        from src.forecaster import train_and_forecast, get_forecast_summary
        forecast, prophet_data = train_and_forecast(df, weeks=12, date_col=date_col, sales_col=sales_col)
        forecast_summary = get_forecast_summary(forecast)
        st.session_state.forecast         = forecast
        st.session_state.prophet_data     = prophet_data
        st.session_state.forecast_summary = forecast_summary

    with st.spinner("🤖 " + ("Building Agent..." if lang == "en" else "بناء الوكيل..." if lang == "ar" else "Construction de l'agent...")):
        from src.agent import build_system_prompt
        system_prompt = build_system_prompt(
            st.session_state.summary,
            st.session_state.store_df,
            st.session_state.holiday_df,
            st.session_state.corr_series,
            st.session_state.forecast_summary,
            lang=lang
        )
        st.session_state.system_prompt = system_prompt
        st.session_state.analyzed      = True
        st.session_state.chat_history  = []

    st.success("✅ " + ("Analysis complete!" if lang == "en" else "اكتمل التحليل!" if lang == "ar" else "Analyse terminée !"))
    st.rerun()

# ─── عرض النتائج ─────────────────────────────────────────
if st.session_state.analyzed:

    summary          = st.session_state.summary
    df               = st.session_state.df
    date_col         = st.session_state.date_col
    sales_col        = st.session_state.sales_col
    forecast_summary = st.session_state.forecast_summary
    T                = get_translations(lang)

    tab1, tab2, tab3, tab4 = st.tabs([
        T["tab_overview"], T["tab_charts"], T["tab_forecast"], T["tab_agent"]
    ])

    # ── Tab 1 ──────────────────────────────────────────────
    with tab1:
        st.subheader(T["data_summary"])

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric(T["total_records"], f"{summary['total_records']:,}")
        with col2: st.metric(T["total_sales"],   f"${summary['total_sales']:,.0f}")
        with col3: st.metric(T["avg_period"],    f"${summary['avg_weekly_sales']:,.0f}")
        with col4: st.metric(T["best_period"],   f"${summary['max_single_week']:,.0f}")

        st.divider()
        st.subheader(T["ai_analysis"])

        analysis_types = T["analysis_types"]
        analysis_type  = st.selectbox(T["choose_analysis"], options=analysis_types)
        prompts        = T["prompts"]

        if st.button(f"🤖 {T['btn_generate']}", type="primary"):
            with st.spinner(T["generating_ai"]):
                from src.agent import ask_agent
                result_text, _ = ask_agent(
                    prompts[analysis_type],
                    st.session_state.system_prompt,
                    []
                )
                st.session_state.ai_result      = result_text
                st.session_state.ai_result_type = analysis_type

        if 'ai_result' in st.session_state:
            st.markdown(f"### {st.session_state.ai_result_type}")
            st.markdown(st.session_state.ai_result)
            st.download_button(
                label=T["download_txt"],
                data=st.session_state.ai_result,
                file_name="analysis_result.txt",
                mime="text/plain"
            )

        st.divider()

        # ── PDF ──────────────────────────────────────────
        if st.button(T["download_pdf"], type="secondary"):
            with st.spinner(T["generating_pdf"]):
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
                from reportlab.lib import colors
                import io
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                import matplotlib.ticker as mticker

                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4,
                    rightMargin=inch*0.75, leftMargin=inch*0.75,
                    topMargin=inch*0.75, bottomMargin=inch*0.75)

                styles = getSampleStyleSheet()
                title_style   = ParagraphStyle('title', fontSize=20, fontName='Helvetica-Bold',
                    spaceAfter=12, textColor=colors.HexColor('#1E40AF'))
                heading_style = ParagraphStyle('heading', fontSize=14, fontName='Helvetica-Bold',
                    spaceAfter=8, textColor=colors.HexColor('#1E40AF'), spaceBefore=16)
                normal_style  = ParagraphStyle('normal', fontSize=10, fontName='Helvetica',
                    spaceAfter=6, leading=14)

                story = []
                cname = st.session_state.get("company_name", "")
                title_text = f"{cname} — {T['pdf_title']}" if cname else T['pdf_title']
                story.append(Paragraph(title_text, title_style))
                story.append(Paragraph(
                    f"{T['pdf_generated']}: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
                    normal_style
                ))
                story.append(Spacer(1, 0.2*inch))

                story.append(Paragraph(T["pdf_key_metrics"], heading_style))
                metrics_data = [
                    [T["pdf_metric"], T["pdf_value"]],
                    [T["total_records"],  f"{summary['total_records']:,}"],
                    [T["pdf_date_range"], summary.get('date_range', 'N/A')],
                    [T["total_sales"],    f"${summary['total_sales']:,.2f}"],
                    [T["pdf_avg_period"], f"${summary['avg_weekly_sales']:,.2f}"],
                    [T["pdf_best_period"],f"${summary['max_single_week']:,.2f}"],
                ]
                metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
                metrics_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E40AF')),
                    ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
                    ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE',   (0,0), (-1,-1), 10),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
                    ('GRID',  (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                    ('PADDING',(0,0), (-1,-1), 8),
                ]))
                story.append(metrics_table)
                story.append(Spacer(1, 0.2*inch))

                story.append(Paragraph(T["pdf_trend"], heading_style))
                weekly = df.groupby(date_col)[sales_col].sum().reset_index()
                fig, ax = plt.subplots(figsize=(7, 3))
                ax.plot(weekly[date_col], weekly[sales_col], color='#2563EB', linewidth=1, alpha=0.6)
                weekly['ma4'] = weekly[sales_col].rolling(4).mean()
                ax.plot(weekly[date_col], weekly['ma4'], color='#DC2626', linewidth=2, label=T["period_avg"])
                ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                    lambda x, p: f'${x/1e6:.1f}M' if x >= 1e6 else f'${x/1e3:.0f}K'))
                ax.legend(fontsize=8); ax.grid(True, alpha=0.3); plt.tight_layout()
                img_buf = io.BytesIO()
                plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
                plt.close(); img_buf.seek(0)
                story.append(Image(img_buf, width=6.5*inch, height=2.5*inch))
                story.append(Spacer(1, 0.2*inch))

                story.append(Paragraph(T["pdf_forecast"], heading_style))
                forecast_data = [
                    [T["pdf_period"], T["pdf_expected"]],
                    [T["next_4"],  f"${forecast_summary['next_4_weeks']:,.0f}"],
                    [T["next_8"],  f"${forecast_summary['next_8_weeks']:,.0f}"],
                    [T["next_12"], f"${forecast_summary['next_12_weeks']:,.0f}"],
                    [T["pdf_peak_week"],  forecast_summary['peak_week']],
                    [T["pdf_peak_sales"], f"${forecast_summary['peak_expected_sales']:,.0f}"],
                ]
                forecast_table = Table(forecast_data, colWidths=[3*inch, 3*inch])
                forecast_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#16A34A')),
                    ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
                    ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE',   (0,0), (-1,-1), 10),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F0FDF4')]),
                    ('GRID',  (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                    ('PADDING',(0,0), (-1,-1), 8),
                ]))
                story.append(forecast_table)
                story.append(Spacer(1, 0.2*inch))

                if 'ai_result' in st.session_state:
                    story.append(Paragraph(T["pdf_ai_section"], heading_style))
                    clean_text = st.session_state.ai_result.replace('#', '').replace('*', '')
                    for line in clean_text.split('\n'):
                        if line.strip():
                            story.append(Paragraph(line.strip(), normal_style))

                doc.build(story)
                buffer.seek(0)
                st.download_button(
                    label=T["download_pdf_now"],
                    data=buffer,
                    file_name=f"sales_report_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )

        st.divider()

        with st.expander(T["cleaning_report"]):
            for line in st.session_state.report:
                st.text(line)

        st.subheader(T["data_preview"])
        st.dataframe(df.head(20), use_container_width=True)

        if st.session_state.store_df is not None:
            st.subheader(f"{T['performance_by']} {st.session_state.group_col}")
            st.dataframe(st.session_state.store_df, use_container_width=True)

    # ── Tab 2 ──────────────────────────────────────────────
    with tab2:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker

        def fmt(x, pos):
            if x >= 1e6: return f'${x/1e6:.1f}M'
            elif x >= 1e3: return f'${x/1e3:.0f}K'
            return f'${x:.0f}'

        st.subheader(T["sales_trend"])
        weekly = df.groupby(date_col)[sales_col].sum().reset_index()
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(weekly[date_col], weekly[sales_col], color='#2563EB', linewidth=1, alpha=0.6)
        weekly['ma4'] = weekly[sales_col].rolling(4).mean()
        ax.plot(weekly[date_col], weekly['ma4'], color='#DC2626', linewidth=2.5, label=T["period_avg"])
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
        ax.legend(); ax.grid(True, alpha=0.3); plt.tight_layout()
        st.pyplot(fig); plt.close()

        st.subheader(T["monthly_sales"])
        monthly_df = st.session_state.monthly_df
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.bar([str(m) for m in monthly_df['month']], monthly_df['total'], color='#16A34A', alpha=0.8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
        ax.grid(True, axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right', fontsize=8); plt.tight_layout()
        st.pyplot(fig); plt.close()

        if st.session_state.store_df is not None:
            group_col = st.session_state.group_col
            store_df  = st.session_state.store_df
            st.subheader(f"{T['sales_by']} {group_col}")
            top10 = store_df.head(10)
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.bar(top10[group_col].astype(str), top10['total'], color='#2563EB', alpha=0.85)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
            ax.grid(True, axis='y', alpha=0.3); plt.tight_layout()
            st.pyplot(fig); plt.close()

        if st.session_state.corr_series is not None:
            st.subheader(T["correlation"])
            corr = st.session_state.corr_series
            fig, ax = plt.subplots(figsize=(8, 4))
            bar_colors = ['#16A34A' if v > 0 else '#DC2626' for v in corr.values]
            ax.barh(corr.index, corr.values, color=bar_colors, alpha=0.85)
            ax.axvline(x=0, color='black', linewidth=0.8)
            ax.grid(True, axis='x', alpha=0.3); plt.tight_layout()
            st.pyplot(fig); plt.close()

    # ── Tab 3 ──────────────────────────────────────────────
    with tab3:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker

        st.subheader(T["forecast_title"])

        col1, col2, col3 = st.columns(3)
        with col1: st.metric(T["next_4"],  f"${forecast_summary['next_4_weeks']:,.0f}")
        with col2: st.metric(T["next_8"],  f"${forecast_summary['next_8_weeks']:,.0f}")
        with col3: st.metric(T["next_12"], f"${forecast_summary['next_12_weeks']:,.0f}")

        forecast     = st.session_state.forecast
        prophet_data = st.session_state.prophet_data
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(prophet_data['ds'], prophet_data['y'], color='#2563EB', linewidth=1,
                label=T["historical"], alpha=0.7)
        future = forecast[forecast['ds'] > prophet_data['ds'].max()]
        ax.plot(future['ds'], future['yhat'], color='#DC2626', linewidth=2.5,
                label=T["forecast_label"])
        ax.fill_between(future['ds'], future['yhat_lower'], future['yhat_upper'],
                        alpha=0.15, color='#DC2626')
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, p: f'${x/1e6:.1f}M' if x >= 1e6 else f'${x/1e3:.0f}K'))
        ax.legend(); ax.grid(True, alpha=0.3); plt.tight_layout()
        st.pyplot(fig); plt.close()

        st.info(f"{T['peak_info']} **{forecast_summary['peak_week']}** → **${forecast_summary['peak_expected_sales']:,.0f}**")

    # ── Tab 4 ──────────────────────────────────────────────
    with tab4:
        st.subheader(T["agent_title"])
        st.caption(T["agent_caption"])

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if len(st.session_state.chat_history) == 0:
            with st.spinner(T["initial_analysis"]):
                from src.agent import ask_agent
                answer, history = ask_agent(
                    T["auto_question"],
                    st.session_state.system_prompt,
                    []
                )
                st.session_state.chat_history = history
                st.rerun()

        if question := st.chat_input(T["chat_placeholder"]):
            from src.agent import ask_agent
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner(T["thinking"]):
                    answer, updated_history = ask_agent(
                        question,
                        st.session_state.system_prompt,
                        st.session_state.chat_history
                    )
                    st.session_state.chat_history = updated_history
                    st.markdown(answer)

# ─── Landing Page ─────────────────────────────────────────
else:
    T = get_translations(lang)
    col1, col2, col3 = st.columns(3)
    with col1: st.info(T["step1"])
    with col2: st.info(T["step2"])
    with col3: st.info(T["step3"])

    st.divider()
    st.subheader(T["what_it_does"])
    col1, col2 = st.columns(2)
    with col1: st.markdown(T["feature1"])
    with col2: st.markdown(T["feature2"])