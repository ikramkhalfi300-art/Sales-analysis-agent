import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from src.translations import get_translations

load_dotenv()

st.set_page_config(page_title="Sales Analysis Agent", page_icon="📊", layout="wide")

# ─── اختيار اللغة ────────────────────────────────────────
lang_options = {"English": "en", "العربية": "ar", "Français": "fr"}
lang_label   = st.sidebar.selectbox("🌐 Language / اللغة / Langue", list(lang_options.keys()))
lang         = lang_options[lang_label]
T            = get_translations(lang)

direction = "rtl" if lang == "ar" else "ltr"
st.markdown(f"""
<style>
    .main-header {{
        font-size: 2.2rem; font-weight: 700; color: #1E40AF;
        text-align: center; padding: 1rem 0; direction: {direction};
    }}
    .sub-header {{
        font-size: 1rem; color: #6B7280;
        text-align: center; margin-bottom: 2rem; direction: {direction};
    }}
    .company-badge {{
        display: inline-block; background: #EFF6FF; color: #1E40AF;
        border: 1px solid #BFDBFE; border-radius: 8px;
        padding: 4px 14px; font-size: 0.9rem; font-weight: 600;
        margin-bottom: 0.5rem;
    }}
    .stApp {{ direction: {direction}; }}
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────
with st.sidebar:
    st.header(T["settings"])

    company_name = st.text_input(
        T["company_name"],
        placeholder=T["company_placeholder"],
        value=st.session_state.get("company_name", "")
    )
    st.session_state.company_name = company_name

    # ── فترة التحليل (الخطوة 6) ─────────────────────────
    period_options = {
        "Weekly":    ("W",  12, "week"),
        "Monthly":   ("ME", 6,  "month"),
        "Quarterly": ("QE", 4,  "quarter"),
        "Yearly":    ("YE", 3,  "year"),
    }
    period_labels = {
        "en": {"Weekly":"Weekly","Monthly":"Monthly","Quarterly":"Quarterly","Yearly":"Yearly"},
        "ar": {"Weekly":"أسبوعي","Monthly":"شهري","Quarterly":"ربع سنوي","Yearly":"سنوي"},
        "fr": {"Weekly":"Hebdomadaire","Monthly":"Mensuel","Quarterly":"Trimestriel","Yearly":"Annuel"},
    }
    pl = period_labels.get(lang, period_labels["en"])
    period_display = list(pl.values())
    period_keys    = list(pl.keys())
    sel_period_idx = st.selectbox(
        "📅 " + ("Analysis Period" if lang=="en" else "فترة التحليل" if lang=="ar" else "Période d'analyse"),
        options=range(len(period_display)),
        format_func=lambda i: period_display[i]
    )
    selected_period_key = period_keys[sel_period_idx]
    period_freq, forecast_periods, period_unit = period_options[selected_period_key]
    st.session_state.period_freq    = period_freq
    st.session_state.forecast_periods = forecast_periods
    st.session_state.period_unit    = period_unit

    st.subheader(T["upload_data"])
    uploaded_file = st.file_uploader(T["upload_hint"], type=['csv','xlsx','xls'])

    date_col  = None
    sales_col = None

    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                try:    preview_df = pd.read_csv(uploaded_file)
                except: uploaded_file.seek(0); preview_df = pd.read_csv(uploaded_file, encoding='latin1')
            else:
                preview_df = pd.read_excel(uploaded_file)
            uploaded_file.seek(0)
            preview_df.columns = preview_df.columns.str.strip()
            cols = preview_df.columns.tolist()

            st.subheader(T["map_columns"])
            st.caption(T["date_warning"])

            date_options  = [c for c in cols if any(x in c.lower() for x in ['date','time','week','month','year','day','تاريخ'])] or cols
            date_col      = st.selectbox(T["date_col"], options=cols, index=cols.index(date_options[0]) if date_options else 0)
            sales_options = [c for c in cols if any(x in c.lower() for x in ['sale','revenue','amount','total','مبيع','إيراد','vente'])] or cols
            sales_col     = st.selectbox(T["sales_col"], options=cols, index=cols.index(sales_options[0]) if sales_options else 0)
            analyze_btn   = st.button(T["analyze_btn"], type="primary", use_container_width=True)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            analyze_btn = False
    else:
        analyze_btn = False
        st.info(T["upload_prompt"])

    st.divider()
    st.caption(T["built_with"])

# ─── Header ──────────────────────────────────────────────
cname = st.session_state.get("company_name","").strip()
title_text = f"📊 {cname}" if cname else T["app_title"]
st.markdown(f'<p class="main-header">{title_text}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">{T["app_subtitle"]}</p>', unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────
for key, default in [('analyzed',False),('chat_history',[]),('system_prompt',None),('lang',lang)]:
    if key not in st.session_state:
        st.session_state[key] = default
if st.session_state.lang != lang:
    st.session_state.chat_history = []
    st.session_state.lang = lang

def chart_title(base):
    c = st.session_state.get("company_name","").strip()
    return f"{c} — {base}" if c else base

# ─── التحليل ─────────────────────────────────────────────
if analyze_btn and uploaded_file and date_col and sales_col:

    with st.spinner("🔄 " + ("Loading..." if lang=="en" else "تحميل..." if lang=="ar" else "Chargement...")):
        try:
            uploaded_file.seek(0)
            if uploaded_file.name.endswith('.csv'):
                try:    raw_df = pd.read_csv(uploaded_file)
                except: uploaded_file.seek(0); raw_df = pd.read_csv(uploaded_file, encoding='latin1')
            else:
                raw_df = pd.read_excel(uploaded_file)
            raw_df.columns = raw_df.columns.str.strip()
            date_col  = date_col.strip()
            sales_col = sales_col.strip()
            raw_df[date_col] = pd.to_datetime(raw_df[date_col], errors='coerce')
            from src.data_cleaner import clean_data
            df, report = clean_data(raw_df, date_col=date_col, sales_col=sales_col)
            df = df.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
            st.session_state.df        = df
            st.session_state.date_col  = date_col
            st.session_state.sales_col = sales_col
            st.session_state.report    = report
        except Exception as e:
            st.error(f"❌ {e}"); st.stop()

    with st.spinner("📊 " + ("Analyzing..." if lang=="en" else "جاري التحليل..." if lang=="ar" else "Analyse...")):
        from src.data_loader import get_summary
        from src.analyzer    import holiday_vs_normal
        df        = st.session_state.df
        summary   = get_summary(df, date_col, sales_col)
        group_col = summary.get('group_col')
        freq      = st.session_state.period_freq

        store_df = None
        if group_col:
            store_df = (df.groupby(group_col)[sales_col].agg(['sum','mean'])
                        .rename(columns={'sum':'total','mean':'avg_weekly'})
                        .reset_index().sort_values('total', ascending=False))

        # تجميع حسب الفترة المختارة
        df_period = df.copy()
        df_period['period'] = df_period[date_col].dt.to_period(freq)
        monthly_df = (df_period.groupby('period')[sales_col].sum().reset_index()
                      .rename(columns={sales_col:'total','period':'month'}))

        holiday_df = holiday_vs_normal(df) if 'Holiday_Flag' in df.columns else None
        numeric_cols = [c for c in df.select_dtypes(include='number').columns if c != sales_col]
        corr_series  = df[[sales_col]+numeric_cols].corr()[sales_col].drop(sales_col).round(4) if numeric_cols else None

        st.session_state.summary     = summary
        st.session_state.store_df    = store_df
        st.session_state.monthly_df  = monthly_df
        st.session_state.holiday_df  = holiday_df
        st.session_state.corr_series = corr_series
        st.session_state.group_col   = group_col

    with st.spinner("🔮 " + ("Forecasting..." if lang=="en" else "جاري التنبؤ..." if lang=="ar" else "Prévision...")):
        from src.forecaster import train_and_forecast, get_forecast_summary
        n_periods = st.session_state.forecast_periods
        forecast, prophet_data = train_and_forecast(df, weeks=n_periods, date_col=date_col, sales_col=sales_col)
        forecast_summary = get_forecast_summary(forecast)
        st.session_state.forecast         = forecast
        st.session_state.prophet_data     = prophet_data
        st.session_state.forecast_summary = forecast_summary

    with st.spinner("🤖 " + ("Building Agent..." if lang=="en" else "بناء الوكيل..." if lang=="ar" else "Construction...")):
        from src.agent import build_system_prompt
        system_prompt = build_system_prompt(
            st.session_state.summary, st.session_state.store_df,
            st.session_state.holiday_df, st.session_state.corr_series,
            st.session_state.forecast_summary, lang=lang, company_name=cname
        )
        st.session_state.system_prompt = system_prompt
        st.session_state.analyzed      = True
        st.session_state.chat_history  = []

    st.success("✅ " + ("Done!" if lang=="en" else "اكتمل!" if lang=="ar" else "Terminé!"))
    st.rerun()

# ─── عرض النتائج ─────────────────────────────────────────
if st.session_state.analyzed:
    summary          = st.session_state.summary
    df               = st.session_state.df
    date_col         = st.session_state.date_col
    sales_col        = st.session_state.sales_col
    forecast_summary = st.session_state.forecast_summary
    T                = get_translations(lang)
    cname            = st.session_state.get("company_name","").strip()

    if cname:
        st.markdown(f'<span class="company-badge">🏢 {cname}</span>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([T["tab_overview"], T["tab_charts"], T["tab_forecast"], T["tab_agent"]])

    # ── Tab 1: Overview ────────────────────────────────────
    with tab1:
        st.subheader(T["data_summary"])
        col1,col2,col3,col4 = st.columns(4)
        with col1: st.metric(T["total_records"], f"{summary['total_records']:,}")
        with col2: st.metric(T["total_sales"],   f"${summary['total_sales']:,.0f}")
        with col3: st.metric(T["avg_period"],    f"${summary['avg_weekly_sales']:,.0f}")
        with col4: st.metric(T["best_period"],   f"${summary['max_single_week']:,.0f}")

        st.divider()
        st.subheader(T["ai_analysis"])
        analysis_type = st.selectbox(T["choose_analysis"], options=T["analysis_types"])
        prompts       = T["prompts"]

        if st.button(f"🤖 {T['btn_generate']}", type="primary"):
            with st.spinner(T["generating_ai"]):
                from src.agent import ask_agent
                result_text, _ = ask_agent(prompts[analysis_type], st.session_state.system_prompt, [])
                st.session_state.ai_result      = result_text
                st.session_state.ai_result_type = analysis_type

        if 'ai_result' in st.session_state:
            st.markdown(f"### {st.session_state.ai_result_type}")
            st.markdown(st.session_state.ai_result)
            st.download_button(T["download_txt"], st.session_state.ai_result,
                               file_name="analysis.txt", mime="text/plain")

        st.divider()

        # ── PDF ──────────────────────────────────────────
        
        if st.button(T["download_pdf"], type="secondary"):
            with st.spinner(T["generating_pdf"]):
                from src.pdf_gen import generate_pdf
                pdf_bytes = generate_pdf(
                    df=df, date_col=date_col, sales_col=sales_col,
                    summary=summary,
                    store_df=st.session_state.store_df,
                    corr_series=st.session_state.corr_series,
                    forecast=st.session_state.forecast,
                    prophet_data=st.session_state.prophet_data,
                    forecast_summary=forecast_summary,
                    monthly_df=st.session_state.monthly_df,
                    group_col=st.session_state.group_col,
                    company_name=cname, T=T,
                    ai_result=st.session_state.get('ai_result'),
                    ai_type=st.session_state.get('ai_result_type'),
                )
                st.download_button(T["download_pdf_now"], pdf_bytes,
                    file_name=f"report_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf")

        st.divider()
        with st.expander(T["cleaning_report"]):
            for line in st.session_state.report: st.text(line)
        st.subheader(T["data_preview"])
        st.dataframe(df.head(20), use_container_width=True)
        if st.session_state.store_df is not None:
            st.subheader(f"{T['performance_by']} {st.session_state.group_col}")
            st.dataframe(st.session_state.store_df, use_container_width=True)

    # ── Tab 2: Charts (Plotly - الخطوة 5) ─────────────────
    with tab2:
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        period_unit = st.session_state.get('period_unit','week')

        # رسم اتجاه المبيعات
        st.subheader(T["sales_trend"])
        weekly = df.groupby(date_col)[sales_col].sum().reset_index().sort_values(date_col)
        weekly['ma4'] = weekly[sales_col].rolling(4).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
        x=weekly[date_col], y=weekly[sales_col],
            fill='tozeroy', fillcolor='rgba(37,99,235,0.08)',
            line=dict(color='#2563EB', width=1.5),
            name='Sales', hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=weekly[date_col], y=weekly['ma4'],
            line=dict(color='#DC2626', width=2.5),
            name=T["period_avg"], hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'
        ))
        fig.update_layout(
            title=chart_title(T["sales_trend"]),
            hovermode='x unified', height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            yaxis=dict(tickprefix='$', tickformat=',.0f'),
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='#F3F4F6'),
            yaxis_gridcolor='#F3F4F6'
        )
        st.plotly_chart(fig, use_container_width=True)

        # رسم الفترة المختارة (شهري/أسبوعي/ربعي/سنوي)
        st.subheader(T["monthly_sales"])
        monthly_df = st.session_state.monthly_df
        months_str = [str(m) for m in monthly_df['month']]
        vals       = monthly_df['total'].tolist()
        bar_colors = ['#16A34A' if v >= pd.Series(vals).quantile(0.6)
                      else '#D97706' if v >= pd.Series(vals).quantile(0.3)
                      else '#DC2626' for v in vals]
        fig2 = go.Figure(go.Bar(
            x=months_str, y=vals,
            marker_color=bar_colors,
            text=[f'${v/1e6:.1f}M' if v>=1e6 else f'${v/1e3:.0f}K' for v in vals],
            textposition='outside',
            hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'
        ))
        fig2.update_layout(
            title=chart_title(T["monthly_sales"]),
            height=400, yaxis=dict(tickprefix='$', tickformat=',.0f'),
            plot_bgcolor='white', paper_bgcolor='white',
            yaxis_gridcolor='#F3F4F6'
        )
        st.plotly_chart(fig2, use_container_width=True)

        # رسم المتاجر
        if st.session_state.store_df is not None:
            group_col = st.session_state.group_col
            store_df  = st.session_state.store_df
            st.subheader(f"{T['sales_by']} {group_col}")
            top10 = store_df.head(10)
            fig3 = go.Figure(go.Bar(
                x=top10[group_col].astype(str), y=top10['total'],
                marker_color='#2563EB', opacity=0.85,
                text=[f'${v/1e6:.1f}M' if v>=1e6 else f'${v/1e3:.0f}K' for v in top10['total']],
                textposition='outside',
                hovertemplate=f'{group_col}: %{{x}}<br>Total: $%{{y:,.0f}}<extra></extra>'
            ))
            fig3.update_layout(
                title=chart_title(f"{T['sales_by']} {group_col}"),
                height=400, yaxis=dict(tickprefix='$', tickformat=',.0f'),
                plot_bgcolor='white', paper_bgcolor='white',
                yaxis_gridcolor='#F3F4F6'
            )
            st.plotly_chart(fig3, use_container_width=True)

        # رسم الارتباط
        if st.session_state.corr_series is not None:
            st.subheader(T["correlation"])
            corr = st.session_state.corr_series
            corr_colors = ['#16A34A' if v>0 else '#DC2626' for v in corr.values]
            fig4 = go.Figure(go.Bar(
                x=corr.values, y=corr.index, orientation='h',
                marker_color=corr_colors, opacity=0.85,
                text=[f'{v:.4f}' for v in corr.values], textposition='outside',
                hovertemplate='%{y}: %{x:.4f}<extra></extra>'
            ))
            fig4.update_layout(
                title=chart_title(T["correlation"]),
                height=350, plot_bgcolor='white', paper_bgcolor='white',
                xaxis_gridcolor='#F3F4F6'
            )
            fig4.add_vline(x=0, line_color='black', line_width=0.8)
            st.plotly_chart(fig4, use_container_width=True)

    # ── Tab 3: Forecast (Plotly) ───────────────────────────
    with tab3:
        import plotly.graph_objects as go
        st.subheader(T["forecast_title"])

        col1,col2,col3 = st.columns(3)
        with col1: st.metric(T["next_4"],  f"${forecast_summary['next_4_weeks']:,.0f}")
        with col2: st.metric(T["next_8"],  f"${forecast_summary['next_8_weeks']:,.0f}")
        with col3: st.metric(T["next_12"], f"${forecast_summary['next_12_weeks']:,.0f}")

        forecast     = st.session_state.forecast
        prophet_data = st.session_state.prophet_data
        future       = forecast[forecast['ds'] > prophet_data['ds'].max()]

        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(
            x=prophet_data['ds'], y=prophet_data['y'],
            line=dict(color='#2563EB', width=1.5),
            name=T["historical"],
            hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'
        ))
        fig5.add_trace(go.Scatter(
            x=future['ds'], y=future['yhat_upper'],
            line=dict(width=0), showlegend=False,
            hoverinfo='skip', fillcolor='rgba(220,38,38,0.1)', fill=None
        ))
        fig5.add_trace(go.Scatter(
            x=future['ds'], y=future['yhat_lower'],
            fill='tonexty', fillcolor='rgba(220,38,38,0.1)',
            line=dict(width=0), showlegend=False, hoverinfo='skip'
        ))
        fig5.add_trace(go.Scatter(
            x=future['ds'], y=future['yhat'],
            line=dict(color='#DC2626', width=2.5, dash='dash'),
            name=T["forecast_label"],
            hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'
        ))
        # خط فاصل
        fig5.add_vline(
            x=prophet_data['ds'].max(), line_color='gray',
            line_width=1, line_dash='dot',
            annotation_text="Forecast start", annotation_position="top"
        )
        fig5.update_layout(
            title=chart_title(T["forecast_title"]),
            height=500, hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            yaxis=dict(tickprefix='$', tickformat=',.0f'),
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis_gridcolor='#F3F4F6', yaxis_gridcolor='#F3F4F6'
        )
        st.plotly_chart(fig5, use_container_width=True)
        st.info(f"{T['peak_info']} **{forecast_summary['peak_week']}** → **${forecast_summary['peak_expected_sales']:,.0f}**")

    # ── Tab 4: AI Agent (Streaming - الخطوة 7) ─────────────
    with tab4:
        st.subheader(T["agent_title"])
        st.caption(T["agent_caption"])

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if len(st.session_state.chat_history) == 0:
            with st.spinner(T["initial_analysis"]):
                from src.agent import ask_agent
                answer, history = ask_agent(T["auto_question"], st.session_state.system_prompt, [])
                st.session_state.chat_history = history
                st.rerun()

        if question := st.chat_input(T["chat_placeholder"]):
            from src.agent import stream_agent
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                # Streaming — كلمة كلمة مثل ChatGPT
                response_placeholder = st.empty()
                full_response = ""
                for chunk in stream_agent(question, st.session_state.system_prompt, st.session_state.chat_history):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
            st.session_state.chat_history.append({"role": "user",      "content": question})
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

# ─── Landing Page ─────────────────────────────────────────
else:
    T = get_translations(lang)
    col1,col2,col3 = st.columns(3)
    with col1: st.info(T["step1"])
    with col2: st.info(T["step2"])
    with col3: st.info(T["step3"])
    st.divider()
    st.subheader(T["what_it_does"])
    col1,col2 = st.columns(2)
    with col1: st.markdown(T["feature1"])
    with col2: st.markdown(T["feature2"])