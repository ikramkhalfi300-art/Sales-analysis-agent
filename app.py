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
    .scenario-bear {{
        background: #FEF2F2; border-left: 4px solid #DC2626;
        padding: 10px 14px; border-radius: 6px; margin-bottom: 6px;
    }}
    .scenario-base {{
        background: #EFF6FF; border-left: 4px solid #2563EB;
        padding: 10px 14px; border-radius: 6px; margin-bottom: 6px;
    }}
    .scenario-bull {{
        background: #F0FDF4; border-left: 4px solid #16A34A;
        padding: 10px 14px; border-radius: 6px; margin-bottom: 6px;
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

    period_options = {
        "Weekly":    ("W",  12, "week"),
        "Monthly":   ("M",  6,  "month"),
        "Quarterly": ("Q",  4,  "quarter"),
        "Yearly":    ("A",  3,  "year"),
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
    st.session_state.period_freq      = period_freq
    st.session_state.forecast_periods = forecast_periods
    st.session_state.period_unit      = period_unit

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

    pap_labels = {
        "en": "Include Priority Action Plan",
        "ar": "تضمين خطة الأولويات",
        "fr": "Inclure le Plan d'Action Prioritaire",
    }
    include_pap = st.checkbox(
        f"⭐ {pap_labels.get(lang, pap_labels['en'])}",
        value=False,
        key="include_pap"
    )
    if include_pap:
        pap_badge = {
            "en": "Premium feature enabled — Priority Action Plan will be included in the PDF.",
            "ar": "الميزة المتميزة مفعّلة — ستُضمَّن خطة الأولويات في تقرير PDF.",
            "fr": "Fonctionnalité premium activée — le Plan d'Action sera inclus dans le PDF.",
        }
        st.success(pap_badge.get(lang, pap_badge["en"]))

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

        df_period = df.copy()
        df_period['period'] = df_period[date_col].dt.to_period(freq)
        monthly_df = (df_period.groupby('period')[sales_col].sum().reset_index()
                      .rename(columns={sales_col:'total','period':'month'}))

        holiday_df   = holiday_vs_normal(df) if 'Holiday_Flag' in df.columns else None
        numeric_cols = [c for c in df.select_dtypes(include='number').columns if c != sales_col]
        corr_series  = df[[sales_col]+numeric_cols].corr()[sales_col].drop(sales_col).round(4) if numeric_cols else None

            # ── KPI ذكية ──────────────────────────────────────────
        df_kpi = df.copy()
        try:
            df_kpi['period'] = df_kpi[date_col].dt.to_period(freq)
            period_totals = df_kpi.groupby('period')[sales_col].sum().reset_index()
            period_totals = period_totals.sort_values('period')
            period_totals = period_totals.dropna(subset=[sales_col])
        except Exception:
            period_totals = pd.DataFrame(columns=['period', sales_col])

        mom_growth = None
        if len(period_totals) >= 2:
            last  = period_totals[sales_col].iloc[-1]
            prev  = period_totals[sales_col].iloc[-2]
            mom_growth = (last - prev) / prev * 100 if prev > 0 else 0

        pareto_pct = None
        if group_col and store_df is not None:
            cumsum = store_df['total'].cumsum()
            total  = store_df['total'].sum()
            n80    = (cumsum <= total * 0.8).sum() + 1
            pareto_pct = round(n80 / len(store_df) * 100, 1)

        # FIX: guard against empty period_totals
        if len(period_totals) > 0 and period_totals[sales_col].notna().any():
            best_period_label  = str(period_totals.loc[period_totals[sales_col].idxmax(), 'period'])
            worst_period_label = str(period_totals.loc[period_totals[sales_col].idxmin(), 'period'])
        else:
            best_period_label  = 'N/A'
            worst_period_label = 'N/A'

        sales_std  = float(df[sales_col].std())
        sales_mean = float(df[sales_col].mean())
        cv_pct     = (sales_std / sales_mean * 100) if sales_mean > 0 else 0

        kpi_data = {
            'mom_growth':  mom_growth,
            'pareto_pct':  pareto_pct,
            'best_period': best_period_label,
            'worst_period':worst_period_label,
            'period_count':len(period_totals),
            'cv_pct':      round(cv_pct, 1),
        }

        from src.decision_engine import generate_decisions, decisions_to_df, get_summary_stats
        decisions      = generate_decisions(df, date_col, sales_col, group_col, lang)
        decisions_df   = decisions_to_df(decisions, lang)
        decision_stats = get_summary_stats(decisions)

        st.session_state.summary        = summary
        st.session_state.store_df       = store_df
        st.session_state.monthly_df     = monthly_df
        st.session_state.holiday_df     = holiday_df
        st.session_state.corr_series    = corr_series
        st.session_state.group_col      = group_col
        st.session_state.kpi_data       = kpi_data
        st.session_state.decisions      = decisions
        st.session_state.decisions_df   = decisions_df
        st.session_state.decision_stats = decision_stats

    with st.spinner("🔮 " + ("Forecasting..." if lang=="en" else "جاري التنبؤ..." if lang=="ar" else "Prévision...")):
        from src.forecaster import train_and_forecast, get_forecast_summary
        n_periods = st.session_state.forecast_periods

        has_qa_errors = any(
            'error' in line.lower() or 'issue' in line.lower()
            for line in st.session_state.get('report', [])
        )

        group_col_avg = None
        if store_df is not None and len(store_df) > 0:
            group_col_avg = float(store_df['avg_weekly'].iloc[0])

        forecast, prophet_data = train_and_forecast(
            df, weeks=n_periods,
            date_col=date_col, sales_col=sales_col,
            has_qa_errors=has_qa_errors,
        )
        forecast_summary = get_forecast_summary(forecast, group_col_avg=group_col_avg)

        st.session_state.forecast         = forecast
        st.session_state.prophet_data     = prophet_data
        st.session_state.forecast_summary = forecast_summary

    with st.spinner("🤖 " + ("Building..." if lang=="en" else "بناء..." if lang=="ar" else "Construction...")):
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
    kpi_data         = st.session_state.get('kpi_data', {})
    decision_stats   = st.session_state.get('decision_stats', {})

    if cname:
        st.markdown(f'<span class="company-badge">🏢 {cname}</span>', unsafe_allow_html=True)

    tab_labels = {
        "en": ["📊 Overview", "🎯 Decision Board", "📈 Charts", "🔮 Forecast", "💬 Performance Overview"],
        "ar": ["📊 نظرة عامة", "🎯 لوحة القرارات", "📈 الرسوم", "🔮 التوقعات", "💬 نظرة الأداء"],
        "fr": ["📊 Vue d'ensemble", "🎯 Tableau de Décision", "📈 Graphiques", "🔮 Prévisions", "💬 Aperçu Performance"],
    }
    tabs = st.tabs(tab_labels.get(lang, tab_labels["en"]))
    tab1, tab_dec, tab2, tab3, tab4 = tabs

    # ── Tab 1: Overview ───────────────────────────────────
    with tab1:
        st.subheader(T["data_summary"])
        col1,col2,col3,col4 = st.columns(4)
        with col1: st.metric(T["total_records"], f"{summary['total_records']:,}")
        with col2: st.metric(T["total_sales"],   f"${summary['total_sales']:,.0f}")
        with col3: st.metric(T["avg_period"],    f"${summary['avg_weekly_sales']:,.0f}")
        with col4: st.metric(T["best_period"],   f"${summary['max_single_week']:,.0f}")

        st.divider()

        # Volatility Warning
        cv_pct     = kpi_data.get('cv_pct', 0)
        volatility = forecast_summary.get('volatility', {})
        if volatility and cv_pct > 40:
            vol_msgs = {
                "en": f"{volatility.get('badge','🔴')} **Revenue Volatility: {volatility.get('level','High')} (CV = {cv_pct:.1f}%)** — {volatility.get('risk','')}",
                "ar": f"{volatility.get('badge','🔴')} **تقلب الإيرادات: {volatility.get('level','عالي')} (CV = {cv_pct:.1f}%)** — {volatility.get('risk','')}",
                "fr": f"{volatility.get('badge','🔴')} **Volatilité: {volatility.get('level','Élevée')} (CV = {cv_pct:.1f}%)** — {volatility.get('risk','')}",
            }
            st.warning(vol_msgs.get(lang, vol_msgs["en"]))

        # Sanity Check Warning
        sanity = forecast_summary.get('sanity_check', {})
        if sanity and not sanity.get('passed', True):
            for warn in sanity.get('warnings', []):
                st.error(warn)

        kpi_title = {"en":"📊 Smart KPIs","ar":"📊 مؤشرات ذكية","fr":"📊 KPIs Intelligents"}
        st.subheader(kpi_title.get(lang,"📊 Smart KPIs"))

        k1,k2,k3,k4 = st.columns(4)
        with k1:
            if kpi_data.get('mom_growth') is not None:
                st.metric(
                    "MoM Growth" if lang=="en" else "نمو شهر/شهر" if lang=="ar" else "Croissance MoM",
                    f"{kpi_data['mom_growth']:+.1f}%",
                    delta=f"{kpi_data['mom_growth']:+.1f}%"
                )
        with k2:
            if kpi_data.get('pareto_pct'):
                st.metric(
                    "80% Revenue from" if lang=="en" else "80% الإيراد من" if lang=="ar" else "80% Revenu par",
                    f"Top {kpi_data['pareto_pct']:.0f}% units"
                )
        with k3:
            st.metric(
                "Best Period" if lang=="en" else "أفضل فترة" if lang=="ar" else "Meilleure Période",
                kpi_data.get('best_period','N/A')
            )
        with k4:
            st.metric(
                "Worst Period" if lang=="en" else "أسوأ فترة" if lang=="ar" else "Pire Période",
                kpi_data.get('worst_period','N/A')
            )

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

        _warn_msgs = {
            "en": "⚠️ Please enter your **Company Name** in the sidebar before generating the report.",
            "ar": "⚠️ الرجاء إدخال **اسم الشركة** في الشريط الجانبي قبل توليد التقرير.",
            "fr": "⚠️ Veuillez saisir le **nom de votre entreprise** avant de générer le rapport.",
        }
        if not cname:
            st.warning(_warn_msgs.get(lang, _warn_msgs["en"]))
        elif st.button(T["download_pdf"], type="secondary"):
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
                    include_action_plan=st.session_state.get('include_pap', False),
                    lang=lang,
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

    # ── Tab 2: Decision Board ─────────────────────────────
    with tab_dec:
        dec_titles = {
            "en": "🎯 Decision Board",
            "ar": "🎯 لوحة القرارات",
            "fr": "🎯 Tableau de Décision",
        }
        st.subheader(dec_titles.get(lang,"🎯 Decision Board"))

        if decision_stats:
            c1,c2,c3,c4 = st.columns(4)
            with c1: st.metric("✅ Invest" if lang=="en" else "✅ استثمر" if lang=="ar" else "✅ Investir", decision_stats.get('invest',0))
            with c2: st.metric("👁️ Monitor" if lang=="en" else "👁️ راقب" if lang=="ar" else "👁️ Surveiller", decision_stats.get('monitor',0))
            with c3: st.metric("🔧 Restructure" if lang=="en" else "🔧 أعد الهيكلة" if lang=="ar" else "🔧 Restructurer", decision_stats.get('restructure',0))
            with c4: st.metric("🔴 Critical" if lang=="en" else "🔴 حرج" if lang=="ar" else "🔴 Critique", decision_stats.get('critical_count',0))

            if decision_stats.get('critical_units'):
                critical_label = {
                    "en": f"⚠️ Units requiring immediate attention: **{', '.join(decision_stats['critical_units'])}**",
                    "ar": f"⚠️ وحدات تحتاج تدخل فوري: **{', '.join(decision_stats['critical_units'])}**",
                    "fr": f"⚠️ Unités nécessitant une action immédiate : **{', '.join(decision_stats['critical_units'])}**",
                }
                st.warning(critical_label.get(lang, critical_label["en"]))

            impact_label = {
                "en": f"💰 Total estimated financial impact: **${decision_stats.get('total_impact',0):,.0f}**",
                "ar": f"💰 إجمالي الأثر المالي المقدر: **${decision_stats.get('total_impact',0):,.0f}**",
                "fr": f"💰 Impact financier total estimé : **${decision_stats.get('total_impact',0):,.0f}**",
            }
            st.info(impact_label.get(lang, impact_label["en"]))

        st.divider()

        if st.session_state.decisions_df is not None and len(st.session_state.decisions_df) > 0:
            decisions_df = st.session_state.decisions_df
            filter_label = {"en":"Filter by rating:","ar":"فلتر حسب التقييم:","fr":"Filtrer par note:"}
            all_label    = {"en":"All","ar":"الكل","fr":"Tout"}
            rating_filter = st.radio(filter_label.get(lang,"Filter:"), [all_label.get(lang,"All"), "🟢", "🟡", "🔴"], horizontal=True)
            rating_col = decisions_df.columns[0]
            filtered_df = decisions_df if rating_filter == all_label.get(lang,"All") else decisions_df[decisions_df[rating_col] == rating_filter]
            st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=min(600, 50 + len(filtered_df) * 38))
            csv_label = {"en":"📥 Download Decisions CSV","ar":"📥 تنزيل القرارات CSV","fr":"📥 Télécharger CSV"}
            st.download_button(csv_label.get(lang, csv_label["en"]), data=filtered_df.to_csv(index=False),
                               file_name=f"decisions_{pd.Timestamp.now().strftime('%Y%m%d')}.csv", mime="text/csv")
        else:
            no_group = {
                "en": "Decision Board requires a group column (Store, Branch, Region...) in your data.",
                "ar": "لوحة القرارات تحتاج عمود تجميع (متجر، فرع، منطقة...) في بياناتك.",
                "fr": "Le tableau de décision nécessite une colonne de groupe dans vos données.",
            }
            st.info(no_group.get(lang, no_group["en"]))

    # ── Tab 3: Charts ─────────────────────────────────────
    with tab2:
        import plotly.graph_objects as go

        st.subheader(T["sales_trend"])
        weekly = df.groupby(date_col)[sales_col].sum().reset_index().sort_values(date_col)
        weekly['ma4'] = weekly[sales_col].rolling(4).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=weekly[date_col], y=weekly[sales_col],
            fill='tozeroy', fillcolor='rgba(37,99,235,0.08)', line=dict(color='#2563EB', width=1.5),
            name='Sales', hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'))
        fig.add_trace(go.Scatter(x=weekly[date_col], y=weekly['ma4'],
            line=dict(color='#DC2626', width=2.5), name=T["period_avg"],
            hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'))
        fig.update_layout(title=chart_title(T["sales_trend"]), hovermode='x unified', height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            yaxis=dict(tickprefix='$', tickformat=',.0f'),
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='#F3F4F6'), yaxis_gridcolor='#F3F4F6')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader(T["monthly_sales"])
        monthly_df = st.session_state.monthly_df
        months_str = [str(m) for m in monthly_df['month']]
        vals       = monthly_df['total'].tolist()
        bar_colors = ['#16A34A' if v >= pd.Series(vals).quantile(0.6)
                      else '#D97706' if v >= pd.Series(vals).quantile(0.3)
                      else '#DC2626' for v in vals]
        fig2 = go.Figure(go.Bar(x=months_str, y=vals, marker_color=bar_colors,
            text=[f'${v/1e6:.1f}M' if v>=1e6 else f'${v/1e3:.0f}K' for v in vals],
            textposition='outside', hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'))
        fig2.update_layout(title=chart_title(T["monthly_sales"]), height=400,
            yaxis=dict(tickprefix='$', tickformat=',.0f'),
            plot_bgcolor='white', paper_bgcolor='white', yaxis_gridcolor='#F3F4F6')
        st.plotly_chart(fig2, use_container_width=True)

        if st.session_state.store_df is not None:
            group_col = st.session_state.group_col
            store_df  = st.session_state.store_df
            st.subheader(f"{T['sales_by']} {group_col}")
            top10 = store_df.head(10)
            fig3 = go.Figure(go.Bar(x=top10[group_col].astype(str), y=top10['total'],
                marker_color='#2563EB', opacity=0.85,
                text=[f'${v/1e6:.1f}M' if v>=1e6 else f'${v/1e3:.0f}K' for v in top10['total']],
                textposition='outside',
                hovertemplate=f'{group_col}: %{{x}}<br>$%{{y:,.0f}}<extra></extra>'))
            fig3.update_layout(title=chart_title(f"{T['sales_by']} {group_col}"), height=400,
                yaxis=dict(tickprefix='$', tickformat=',.0f'),
                plot_bgcolor='white', paper_bgcolor='white', yaxis_gridcolor='#F3F4F6')
            st.plotly_chart(fig3, use_container_width=True)

        if st.session_state.corr_series is not None:
            st.subheader(T["correlation"])
            corr = st.session_state.corr_series
            corr_colors = ['#16A34A' if v>0 else '#DC2626' for v in corr.values]
            fig4 = go.Figure(go.Bar(x=corr.values, y=corr.index, orientation='h',
                marker_color=corr_colors, opacity=0.85,
                text=[f'{v:.4f}' for v in corr.values], textposition='outside',
                hovertemplate='%{y}: %{x:.4f}<extra></extra>'))
            fig4.update_layout(title=chart_title(T["correlation"]), height=350,
                plot_bgcolor='white', paper_bgcolor='white', xaxis_gridcolor='#F3F4F6')
            fig4.add_vline(x=0, line_color='black', line_width=0.8)
            st.plotly_chart(fig4, use_container_width=True)

    # ── Tab 4: Forecast ───────────────────────────────────
    with tab3:
        import plotly.graph_objects as go
        st.subheader(T["forecast_title"])

        # Confidence Badge
        conf_level = forecast_summary.get('confidence_level', 'Medium')
        conf_color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(conf_level, "🟡")
        st.info(f"{conf_color} **{'Forecast Confidence' if lang=='en' else 'مستوى ثقة التوقعات' if lang=='ar' else 'Confiance Prévision'}: {conf_level}**")

        # Sanity Check
        sanity = forecast_summary.get('sanity_check', {})
        if sanity and not sanity.get('passed', True):
            for warn in sanity.get('warnings', []):
                st.error(warn)

        # Three-Scenario Cards
        scenario_title = {"en":"📊 12-Period Forecast Scenarios","ar":"📊 سيناريوهات 12 فترة","fr":"📊 Scénarios — 12 Périodes"}
        st.subheader(scenario_title.get(lang, scenario_title["en"]))

        sc1, sc2, sc3 = st.columns(3)
        bear_12 = forecast_summary.get('bear_12_weeks', forecast_summary['next_12_weeks'] * 0.75)
        bull_12 = forecast_summary.get('bull_12_weeks', forecast_summary['next_12_weeks'] * 1.25)
        base_12 = forecast_summary['next_12_weeks']
        bear_prob = forecast_summary.get('bear_probability', 0.25)
        base_prob = forecast_summary.get('base_probability', 0.55)
        bull_prob = forecast_summary.get('bull_probability', 0.20)

        with sc1:
            st.markdown(f'<div class="scenario-bear"><strong>🐻 Bear Case</strong><br>'
                        f'<span style="font-size:1.4rem;font-weight:700;color:#DC2626">${bear_12:,.0f}</span><br>'
                        f'<small>Probability: {bear_prob*100:.0f}%</small></div>', unsafe_allow_html=True)
        with sc2:
            st.markdown(f'<div class="scenario-base"><strong>📌 Base Case</strong><br>'
                        f'<span style="font-size:1.4rem;font-weight:700;color:#2563EB">${base_12:,.0f}</span><br>'
                        f'<small>Probability: {base_prob*100:.0f}%</small></div>', unsafe_allow_html=True)
        with sc3:
            st.markdown(f'<div class="scenario-bull"><strong>🚀 Bull Case</strong><br>'
                        f'<span style="font-size:1.4rem;font-weight:700;color:#16A34A">${bull_12:,.0f}</span><br>'
                        f'<small>Probability: {bull_prob*100:.0f}%</small></div>', unsafe_allow_html=True)

        # Decision Rule
        decision_rule = forecast_summary.get('decision_rule', '')
        if decision_rule:
            dr_label = {"en":f"💡 **Decision Rule:** {decision_rule}",
                        "ar":f"💡 **قاعدة القرار:** {decision_rule}",
                        "fr":f"💡 **Règle de Décision:** {decision_rule}"}
            st.info(dr_label.get(lang, dr_label["en"]))

        st.divider()

        col1,col2,col3 = st.columns(3)
        with col1: st.metric(T["next_4"],  f"${forecast_summary['next_4_weeks']:,.0f}")
        with col2: st.metric(T["next_8"],  f"${forecast_summary['next_8_weeks']:,.0f}")
        with col3: st.metric(T["next_12"], f"${forecast_summary['next_12_weeks']:,.0f}")

        forecast     = st.session_state.forecast
        prophet_data = st.session_state.prophet_data
        future       = forecast[forecast['ds'] > prophet_data['ds'].max()]

        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(x=prophet_data['ds'], y=prophet_data['y'],
            line=dict(color='#2563EB', width=1.5), name=T["historical"],
            hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'))
        fig5.add_trace(go.Scatter(x=future['ds'], y=future['yhat_upper'],
            line=dict(width=0), showlegend=False, hoverinfo='skip', fill=None))
        fig5.add_trace(go.Scatter(x=future['ds'], y=future['yhat_lower'],
            fill='tonexty', fillcolor='rgba(22,163,74,0.08)',
            line=dict(width=0), showlegend=True, hoverinfo='skip', name='Scenario Range'))
        fig5.add_trace(go.Scatter(x=future['ds'], y=future['yhat'],
            line=dict(color='#0D7377', width=2.5, dash='dash'), name='Base Case',
            hovertemplate='%{x}<br>Base: $%{y:,.0f}<extra></extra>'))
        fig5.add_trace(go.Scatter(x=future['ds'], y=future['yhat_lower'],
            line=dict(color='#DC2626', width=1, dash='dot'), name='Bear Case',
            hovertemplate='%{x}<br>Bear: $%{y:,.0f}<extra></extra>'))
        fig5.add_trace(go.Scatter(x=future['ds'], y=future['yhat_upper'],
            line=dict(color='#16A34A', width=1, dash='dot'), name='Bull Case',
            hovertemplate='%{x}<br>Bull: $%{y:,.0f}<extra></extra>'))
        fig5.add_vline(x=prophet_data['ds'].max(), line_color='gray',
            line_width=1, line_dash='dot', annotation_text="Forecast start", annotation_position="top")
        fig5.update_layout(title=chart_title(T["forecast_title"]), height=500,
            hovermode='x unified', legend=dict(orientation='h', yanchor='bottom', y=1.02),
            yaxis=dict(tickprefix='$', tickformat=',.0f'),
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis_gridcolor='#F3F4F6', yaxis_gridcolor='#F3F4F6')
        st.plotly_chart(fig5, use_container_width=True)

        # Peak Date Validation
        today = pd.Timestamp.now().normalize()
        peak_date_str = forecast_summary['peak_week']
        try:
            peak_dt = pd.Timestamp(peak_date_str)
            is_past = peak_dt < today
        except Exception:
            is_past = False

        if is_past:
            peak_warn = {
                "en": f"⚠️ **Note:** The projected peak date ({peak_date_str}) has already passed. The next peak is being re-estimated from remaining forecast periods.",
                "ar": f"⚠️ **ملاحظة:** تاريخ الذروة ({peak_date_str}) قد مضى. يتم إعادة تقدير الذروة القادمة.",
                "fr": f"⚠️ **Note:** La date de pic ({peak_date_str}) est déjà passée. Le prochain pic est en réévaluation.",
            }
            st.warning(peak_warn.get(lang, peak_warn["en"]))
        else:
            st.info(f"{T['peak_info']} **{peak_date_str}** → **${forecast_summary['peak_expected_sales']:,.0f}**")

        # Leading Indicators
        indicators = forecast_summary.get('leading_indicators', [])
        if indicators:
            st.divider()
            li_title = {"en":"📡 Leading Indicators — Validate the Forecast",
                        "ar":"📡 مؤشرات قيادية — للتحقق من التوقعات",
                        "fr":"📡 Indicateurs Avancés — Valider la Prévision"}
            st.subheader(li_title.get(lang, li_title["en"]))
            li_caption = {"en":"Monitor these signals weekly to confirm or revise the forecast before committing resources.",
                          "ar":"راقب هذه الإشارات أسبوعياً قبل تخصيص الموارد.",
                          "fr":"Surveillez ces signaux chaque semaine avant d'engager des ressources."}
            st.caption(li_caption.get(lang, li_caption["en"]))
            for ind in indicators:
                with st.expander(f"📌 {ind['signal']} — Target: {ind['target']}"):
                    st.markdown(f"**Metric:** {ind['metric']}")
                    st.markdown(f"**Alert:** {ind['alert']}")
                    st.markdown(f"**Action if triggered:** {ind['action']}")

    # ── Tab 5: Performance Overview ───────────────────────
    with tab4:
        perf_titles = {"en":"💬 Performance Overview","ar":"💬 نظرة الأداء","fr":"💬 Aperçu Performance"}
        st.subheader(perf_titles.get(lang,"💬 Performance Overview"))
        captions = {"en":"Ask anything about your sales data — get instant insights",
                    "ar":"اسأل أي شيء عن بيانات مبيعاتك — احصل على رؤى فورية",
                    "fr":"Posez n'importe quelle question sur vos données de ventes"}
        st.caption(captions.get(lang, captions["en"]))

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if len(st.session_state.chat_history) == 0:
            init_labels = {"en":"🔍 Generating performance overview...","ar":"🔍 جاري توليد نظرة الأداء...","fr":"🔍 Génération de l'aperçu..."}
            with st.spinner(init_labels.get(lang, init_labels["en"])):
                from src.agent import ask_agent
                answer, history = ask_agent(T["auto_question"], st.session_state.system_prompt, [])
                st.session_state.chat_history = history
                st.rerun()

        placeholders = {"en":"Ask about your sales data...","ar":"اسأل عن بيانات مبيعاتك...","fr":"Posez une question sur vos données..."}
        if question := st.chat_input(placeholders.get(lang, placeholders["en"])):
            from src.agent import stream_agent
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
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