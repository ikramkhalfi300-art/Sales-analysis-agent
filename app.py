"""
app.py — واجهة Streamlit للـ Sales Analysis Multi-Agent System
==============================================================
هذا الملف مسؤول فقط عن:
  - عرض الـ UI
  - استقبال مدخلات المستخدم
  - استدعاء OrchestratorAgent
  - عرض النتائج

لا يحتوي على أي منطق تحليل أو حسابات.
"""

import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── إعداد الصفحة — يجب أن يكون أول شيء ─────────────────
st.set_page_config(
    page_title="Sales Analysis Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS مخصص ─────────────────────────────────────────────
st.markdown("""
<style>
    /* خلفية وألوان رئيسية */
    .stApp { background-color: #0F1117; }

    /* بطاقات KPI */
    .kpi-card {
        background: linear-gradient(135deg, #1E2130 0%, #252A3D 100%);
        border: 1px solid #2D3250;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-2px); }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #7C9EFF;
        margin: 0;
    }
    .kpi-label {
        font-size: 12px;
        color: #8B92A5;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* شارة الحالة */
    .status-success {
        background: #0D2B1F;
        border: 1px solid #1A6B3A;
        border-radius: 8px;
        padding: 10px 16px;
        color: #4ADE80;
        font-size: 13px;
    }
    .status-warning {
        background: #2B1F0D;
        border: 1px solid #6B3A1A;
        border-radius: 8px;
        padding: 10px 16px;
        color: #FCD34D;
        font-size: 13px;
    }
    .status-error {
        background: #2B0D0D;
        border: 1px solid #6B1A1A;
        border-radius: 8px;
        padding: 10px 16px;
        color: #F87171;
        font-size: 13px;
    }

    /* بطاقة Agent */
    .agent-card {
        background: #1A1F2E;
        border-left: 3px solid #7C9EFF;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 6px 0;
        font-size: 13px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #141824;
        border-right: 1px solid #1E2130;
    }

    /* Divider */
    hr { border-color: #1E2130; }

    /* Tab styling */
    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        font-weight: 500;
    }

    /* Chat messages */
    .chat-user {
        background: #1E2130;
        border-radius: 12px 12px 4px 12px;
        padding: 12px 16px;
        margin: 8px 0;
        margin-left: 20%;
        color: #E2E8F0;
    }
    .chat-assistant {
        background: #141E35;
        border: 1px solid #2D3250;
        border-radius: 12px 12px 12px 4px;
        padding: 12px 16px;
        margin: 8px 0;
        margin-right: 10%;
        color: #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ════════════════════════════════════════════════
def init_session():
    defaults = {
        "ctx":          None,       # SharedContext من آخر pipeline
        "chat_history": [],         # تاريخ المحادثة
        "lang":         "en",
        "analyzed":     False,
        "last_file":    None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ════════════════════════════════════════════════
# TRANSLATIONS (مستخرجة من translations.py)
# ════════════════════════════════════════════════
from translations import get_translations

def T(key: str) -> str:
    return get_translations(st.session_state.lang).get(key, key)


# ════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        # ── اللغة ────────────────────────────────
        st.markdown("### 🌐 Language / اللغة / Langue")
        lang = st.selectbox(
            "",
            options=["en", "ar", "fr"],
            format_func=lambda x: {"en": "🇬🇧 English", "ar": "🇸🇦 العربية", "fr": "🇫🇷 Français"}[x],
            index=["en", "ar", "fr"].index(st.session_state.lang),
            label_visibility="collapsed",
        )
        if lang != st.session_state.lang:
            st.session_state.lang = lang
            st.rerun()

        st.divider()

        # ── رفع الملف ────────────────────────────
        st.markdown(f"### {T('upload_data')}")
        uploaded = st.file_uploader(
            T("upload_hint"),
            type=["csv", "xlsx", "xls"],
            label_visibility="collapsed",
        )

        # ── اسم الشركة ───────────────────────────
        company_name = st.text_input(
            T("company_name"),
            placeholder=T("company_placeholder"),
        )

        st.divider()

        # ── إعداد الأعمدة (تظهر فقط بعد رفع الملف) ──
        date_col  = "Date"
        sales_col = "Weekly_Sales"

        if uploaded:
            st.markdown(f"### {T('map_columns')}")
            st.caption(T("date_warning"))

            try:
                preview_df = (
                    pd.read_csv(uploaded, nrows=0)
                    if uploaded.name.endswith('.csv')
                    else pd.read_excel(uploaded, nrows=0)
                )
                uploaded.seek(0)
                cols = list(preview_df.columns)
            except Exception:
                cols = []

            if cols:
                # تخمين ذكي للأعمدة
                date_default  = next((i for i, c in enumerate(cols)
                                      if any(k in c.lower() for k in ['date','time','تاريخ'])), 0)
                sales_default = next((i for i, c in enumerate(cols)
                                      if any(k in c.lower() for k in ['sale','revenue','مبيعات','sales'])), 0)

                date_col = st.selectbox(
                    T("date_col"), cols,
                    index=date_default,
                )
                sales_col = st.selectbox(
                    T("sales_col"), cols,
                    index=sales_default,
                )

        st.divider()

        # ── إعدادات متقدمة ───────────────────────
        with st.expander("⚙️ Advanced Settings", expanded=False):
            forecast_weeks = st.slider("Forecast Periods", 4, 26, 12)
            analysis_type_label = st.selectbox(
                "Analysis Type",
                ["Executive Summary", "Performance Analysis",
                 "Problem Detection", "Profit Improvement"],
            )
            analysis_type_map = {
                "Executive Summary":     "executive_summary",
                "Performance Analysis":  "performance_analysis",
                "Problem Detection":     "problem_detection",
                "Profit Improvement":    "profit_improvement",
            }
            analysis_type = analysis_type_map[analysis_type_label]
        st.divider()

        # ── زر التحليل ───────────────────────────
        analyze_clicked = False
        if uploaded:
            analyze_clicked = st.button(
                T("analyze_btn"),
                type="primary",
                use_container_width=True,
            )
        else:
            st.info(T("upload_prompt"))

        return uploaded, company_name, date_col, sales_col, \
               forecast_weeks, analysis_type, analyze_clicked


# ════════════════════════════════════════════════
# PIPELINE RUNNER
# ════════════════════════════════════════════════
def run_pipeline(uploaded, company_name, date_col, sales_col,
                 forecast_weeks, analysis_type):
    """يشغّل الـ pipeline الكامل ويعرض التقدم"""

    from orchestrator_agent import create_orchestrator, run_pipeline_with_progress

    # قراءة الملف
    try:
        if uploaded.name.endswith('.csv'):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"❌ فشل قراءة الملف: {e}")
        return None

    # إنشاء الـ Orchestrator
    orch = create_orchestrator(
        lang           = st.session_state.lang,
        company_name   = company_name,
        date_col       = date_col,
        sales_col      = sales_col,
        forecast_weeks = forecast_weeks,
    )
    orch.analysis_type = analysis_type

    # شريط التقدم
    st.markdown("---")
    st.markdown("#### ⚙️ Running Pipeline...")
    progress_bar = st.progress(0)

    # تشغيل الـ pipeline
    ctx = run_pipeline_with_progress(
        orch,
        dataframe          = df,
        streamlit_progress = progress_bar,
    )

    progress_bar.empty()
    return ctx


# ════════════════════════════════════════════════
# RENDER: PIPELINE STATUS
# ════════════════════════════════════════════════
def render_pipeline_status(ctx):
    """عرض حالة كل agent بعد التشغيل"""
    with st.expander("🔍 Pipeline Status", expanded=False):
        cols = st.columns(len(ctx.agent_statuses) or 1)
        for i, s in enumerate(ctx.agent_statuses):
            with cols[i % len(cols)]:
                icon  = "✅" if s.success else "❌"
                color = "#4ADE80" if s.success else "#F87171"
                st.markdown(
                    f'<div class="agent-card">'
                    f'<span style="color:{color}">{icon}</span> '
                    f'<b>{s.name}</b><br/>'
                    f'<span style="color:#8B92A5;font-size:11px">{s.duration_sec}s</span>'
                    f'{"<br/><span style=color:#F87171;font-size:11px>"+s.error[:60]+"...</span>" if s.error else ""}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # تحذيرات
        if ctx.warnings:
            st.markdown("**⚠️ Warnings:**")
            for w in ctx.warnings:
                st.warning(w, icon="⚠️")

        # أخطاء
        if ctx.errors:
            st.markdown("**❌ Errors:**")
            for e in ctx.errors:
                st.error(e)


# ════════════════════════════════════════════════
# RENDER: KPI CARDS
# ════════════════════════════════════════════════
def render_kpi_cards(ctx):
    """بطاقات KPI الرئيسية"""
    summary = ctx.summary or {}
    fc      = ctx.forecast_summary or {}

    total   = summary.get('total_sales', 0)
    avg     = summary.get('avg_weekly_sales', 0)
    peak    = summary.get('max_single_week', 0)
    fc12    = fc.get('next_12_weeks', 0)
    conf    = fc.get('confidence_level', 'Medium')
    conf_icon = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(conf, "🟡")

    def money(v):
        if v >= 1e9:  return f"${v/1e9:.1f}B"
        if v >= 1e6:  return f"${v/1e6:.1f}M"
        if v >= 1e3:  return f"${v/1e3:.0f}K"
        return f"${v:.0f}"

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, money(total),   T("total_sales"),   "#7C9EFF"),
        (c2, money(avg),     T("avg_period"),     "#4ADE80"),
        (c3, money(peak),    T("best_period"),    "#FBBF24"),
        (c4, money(fc12),    "12-Period Forecast","#A78BFA"),
        (c5, f"{conf_icon} {conf}", "Forecast Confidence", "#60A5FA"),
    ]
    for col, val, label, color in cards:
        with col:
            st.markdown(
                f'<div class="kpi-card">'
                f'<p class="kpi-value" style="color:{color}">{val}</p>'
                f'<p class="kpi-label">{label}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════════
# RENDER: CHARTS (من VisualAgent)
# ════════════════════════════════════════════════
def render_charts(ctx):
    """عرض الرسوم البيانية المحفوظة من VisualAgent"""
    charts = ctx.chart_paths or []

    if not charts:
        st.info("لم يتم إنشاء رسوم بيانية — تحقق من Pipeline Status")
        return

    chart_labels = {
        "01_sales_trend":       "📈 " + T("sales_trend"),
        "02_store_comparison":  "🏪 " + T("sales_by") + f" {ctx.group_col or 'Group'}",
        "03_monthly_trend":     "📅 " + T("monthly_sales"),
        "04_holiday_impact":    "🎉 Holiday Impact",
        "05_correlations":      "🔗 " + T("correlation"),
        "06_forecast":          "🔮 " + T("forecast_title"),
    }

    # عرض الرسوم في شبكة 2×3
    pairs = [charts[i:i+2] for i in range(0, len(charts), 2)]
    for pair in pairs:
        cols = st.columns(len(pair))
        for col, path in zip(cols, pair):
            with col:
                key = next((k for k in chart_labels if k in path), path)
                label = chart_labels.get(key, path)
                st.markdown(f"**{label}**")
                st.image(path, use_container_width=True)


# ════════════════════════════════════════════════
# RENDER: FORECAST TAB
# ════════════════════════════════════════════════
def render_forecast_tab(ctx):
    """تبويب التوقعات"""
    fc = ctx.forecast_summary or {}

    if not fc:
        st.info("التوقعات غير متاحة — تحقق من Pipeline Status")
        return

    # ── KPI التوقعات ─────────────────────────────
    def money(v):
        if v >= 1e6: return f"${v/1e6:.2f}M"
        if v >= 1e3: return f"${v/1e3:.1f}K"
        return f"${v:.0f}"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(T("next_4"),  money(fc.get('next_4_weeks', 0)))
    with c2:
        st.metric(T("next_8"),  money(fc.get('next_8_weeks', 0)))
    with c3:
        st.metric(T("next_12"), money(fc.get('next_12_weeks', 0)))

    st.divider()

    # ── Bear / Base / Bull ───────────────────────
    st.markdown("#### 📊 Scenario Planning")
    b1, b2, b3 = st.columns(3)
    bear = fc.get('bear_12_weeks', 0)
    base = fc.get('next_12_weeks', 0)
    bull = fc.get('bull_12_weeks', 0)

    with b1:
        st.markdown(
            f'<div class="kpi-card" style="border-left:3px solid #EF4444">'
            f'<p class="kpi-value" style="color:#EF4444">🐻 {money(bear)}</p>'
            f'<p class="kpi-label">Bear Case</p>'
            f'<p style="color:#8B92A5;font-size:11px">{fc.get("bear_spread_pct",0):+.1f}% from base</p>'
            f'</div>', unsafe_allow_html=True)
    with b2:
        st.markdown(
            f'<div class="kpi-card" style="border-left:3px solid #7C9EFF">'
            f'<p class="kpi-value" style="color:#7C9EFF">📌 {money(base)}</p>'
            f'<p class="kpi-label">Base Case</p>'
            f'<p style="color:#8B92A5;font-size:11px">Trend continuation</p>'
            f'</div>', unsafe_allow_html=True)
    with b3:
        st.markdown(
            f'<div class="kpi-card" style="border-left:3px solid #4ADE80">'
            f'<p class="kpi-value" style="color:#4ADE80">🚀 {money(bull)}</p>'
            f'<p class="kpi-label">Bull Case</p>'
            f'<p style="color:#8B92A5;font-size:11px">+{fc.get("bull_spread_pct",0):.1f}% from base</p>'
            f'</div>', unsafe_allow_html=True)

    st.divider()

    # ── رسم التوقعات ─────────────────────────────
    if ctx.forecast_df is not None and ctx.prophet_data is not None:
        st.markdown("#### 📈 Forecast Chart")
        forecast_df  = ctx.forecast_df
        historical   = ctx.prophet_data
        last_hist_dt = historical['ds'].max()
        future       = forecast_df[forecast_df['ds'] > last_hist_dt]

        fig, ax = plt.subplots(figsize=(12, 5))
        fig.patch.set_facecolor('#0F1117')
        ax.set_facecolor('#141824')

        ax.plot(historical['ds'], historical['y'],
                color='#7C9EFF', linewidth=1.5, alpha=0.8, label=T("historical"))

        if len(future) > 0:
            ax.fill_between(future['ds'], future['yhat_lower'], future['yhat_upper'],
                            alpha=0.15, color='#4ADE80')
            ax.plot(future['ds'], future['yhat'],
                    color='#4ADE80', linewidth=2.5, linestyle='--', label=T("forecast_label"))
            ax.plot(future['ds'], future['yhat_lower'],
                    color='#EF4444', linewidth=1, linestyle=':', alpha=0.7, label='Bear')
            ax.plot(future['ds'], future['yhat_upper'],
                    color='#FBBF24', linewidth=1, linestyle=':', alpha=0.7, label='Bull')

        ax.axvline(x=last_hist_dt, color='#8B92A5', linewidth=0.8, linestyle='--', alpha=0.5)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x:,.0f}")
        )
        ax.tick_params(colors='#8B92A5')
        ax.spines['bottom'].set_color('#2D3250')
        ax.spines['left'].set_color('#2D3250')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.08, color='#2D3250')
        ax.legend(fontsize=9, facecolor='#1A1F2E', labelcolor='#E2E8F0', framealpha=0.9)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # ── Peak ─────────────────────────────────────
    peak_wk  = fc.get('peak_week', 'N/A')
    peak_val = fc.get('peak_expected_sales', 0)
    if peak_wk != 'N/A':
        st.info(f"{T('peak_info')} **{peak_wk}** → **{money(peak_val)}**")

    # ── Sanity Warning ───────────────────────────
    sanity = fc.get('sanity_check', {})
    if not sanity.get('passed', True):
        for w in sanity.get('warnings', []):
            st.warning(w)

    # ── Leading Indicators ───────────────────────
    indicators = fc.get('leading_indicators', [])
    if indicators:
        st.divider()
        st.markdown("#### 🎯 Leading Indicators")
        for ind in indicators:
            with st.expander(f"📍 {ind.get('signal', '')}"):
                st.markdown(f"**Target:** {ind.get('target', '')}")
                st.markdown(f"**Alert:** {ind.get('alert', '')}")
                st.markdown(f"**Action:** {ind.get('action', '')}")


# ════════════════════════════════════════════════
# RENDER: AI AGENT TAB (Chat)
# ════════════════════════════════════════════════
def render_chat_tab(ctx):
    """تبويب المحادثة مع الـ AI"""
    from orchestrator_agent import OrchestratorAgent

    st.markdown(f"#### {T('agent_title')}")
    st.caption(T("agent_caption"))

    # ── عرض تاريخ المحادثة ───────────────────────
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-user">👤 {msg["content"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="chat-assistant">🤖 {msg["content"]}</div>',
                unsafe_allow_html=True
            )

    # ── حقل الإدخال ──────────────────────────────
    question = st.chat_input(T("chat_placeholder"))

    if question and ctx is not None:
        # عرض سؤال المستخدم فوراً
        st.markdown(
            f'<div class="chat-user">👤 {question}</div>',
            unsafe_allow_html=True
        )

        # Streaming response
        with st.spinner(T("thinking")):
            orch = OrchestratorAgent(lang=st.session_state.lang)

            # جمع الـ streaming في نص كامل
            full_response = ""
            response_placeholder = st.empty()

            for chunk in orch.chat(
                question = question,
                ctx      = ctx,
                history  = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_history
                ],
                stream   = True,
            ):
                full_response += chunk
                response_placeholder.markdown(
                    f'<div class="chat-assistant">🤖 {full_response}▌</div>',
                    unsafe_allow_html=True
                )

            response_placeholder.markdown(
                f'<div class="chat-assistant">🤖 {full_response}</div>',
                unsafe_allow_html=True
            )

        # حفظ في التاريخ
        st.session_state.chat_history.append({"role": "user",      "content": question})
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})

    elif question and ctx is None:
        st.warning("⚠️ يجب تحليل البيانات أولاً قبل استخدام المحادثة")

    # ── مسح تاريخ المحادثة ───────────────────────
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()


# ════════════════════════════════════════════════
# RENDER: OVERVIEW TAB
# ════════════════════════════════════════════════
def render_overview_tab(ctx):
    """التبويب الأول — نظرة عامة"""
    summary = ctx.summary or {}

    # ── KPI Cards ────────────────────────────────
    render_kpi_cards(ctx)
    st.divider()

    col_left, col_right = st.columns([1.2, 1])

    # ── ملخص البيانات ─────────────────────────────
    with col_left:
        st.markdown(f"#### {T('data_summary')}")
        summary_rows = [
            (T("total_records"),   f"{summary.get('total_records', 0):,}"),
            ("Date Range",         summary.get('date_range', 'N/A')),
            (T("total_sales"),     f"${summary.get('total_sales', 0):,.2f}"),
            (T("avg_period"),      f"${summary.get('avg_weekly_sales', 0):,.2f}"),
            ("Peak Period",        f"${summary.get('max_single_week', 0):,.2f}"),
            ("Best Group",         str(summary.get('best_group', 'N/A'))),
            ("Worst Group",        str(summary.get('worst_group', 'N/A'))),
            ("Num Groups",         str(summary.get('num_groups', 'N/A'))),
        ]
        df_summary = pd.DataFrame(summary_rows, columns=["Metric", "Value"])
        st.dataframe(df_summary, use_container_width=True, hide_index=True)

    # ── جودة البيانات ────────────────────────────
    with col_right:
        st.markdown("#### 🧹 Data Quality")
        dq = ctx.data_quality_report or {}
        if dq:
            completeness = dq.get('completeness', 0)
            rating       = dq.get('rating', 'Unknown')
            color        = {"Excellent": "#4ADE80", "Good": "#60A5FA",
                            "Fair": "#FBBF24", "Poor": "#EF4444"}.get(rating, "#8B92A5")

            st.markdown(
                f'<div class="kpi-card">'
                f'<p class="kpi-value" style="color:{color}">{completeness:.0f}/100</p>'
                f'<p class="kpi-label">Data Quality — {rating}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown("")
            dq_rows = [
                ("Total Records",  f"{dq.get('n_total', 0):,}"),
                ("Missing Values", f"{dq.get('n_missing', 0)} ({dq.get('missing_pct', 0):.1f}%)"),
                ("Duplicates",     f"{dq.get('n_duplicates', 0)}"),
                ("Outliers (IQR)", f"{dq.get('n_outliers', 0)} ({dq.get('outlier_pct', 0):.1f}%)"),
            ]
            df_dq = pd.DataFrame(dq_rows, columns=["Check", "Result"])
            st.dataframe(df_dq, use_container_width=True, hide_index=True)
        else:
            st.info("تقرير جودة البيانات غير متاح")

    st.divider()

    # ── AI Analysis ──────────────────────────────
    st.markdown(f"#### {T('ai_analysis')}")
    if ctx.ai_analysis_text:
        st.markdown(ctx.ai_analysis_text)
    else:
        st.info("لم يتم توليد تحليل ذكي — تحقق من Pipeline Status")

    st.divider()

    # ── تنزيل التقرير ────────────────────────────
    st.markdown("#### 📄 Download Report")
    col_pdf, col_txt = st.columns(2)

    with col_pdf:
        if ctx.pdf_bytes:
            st.download_button(
                label     = T("download_pdf_now"),
                data      = ctx.pdf_bytes,
                file_name = f"sales_report_{ctx.session_id}.pdf",
                mime      = "application/pdf",
                use_container_width=True,
                type      = "primary",
            )
        else:
            st.button(T("download_pdf"), disabled=True, use_container_width=True)

    with col_txt:
        if ctx.ai_analysis_text:
            st.download_button(
                label     = T("download_txt"),
                data      = ctx.ai_analysis_text,
                file_name = f"analysis_{ctx.session_id}.txt",
                mime      = "text/plain",
                use_container_width=True,
            )


# ════════════════════════════════════════════════
# LANDING PAGE (قبل رفع الملف)
# ════════════════════════════════════════════════
def render_landing():
    """صفحة البداية قبل رفع الملف"""
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px 40px;">
        <h1 style="font-size:48px; font-weight:800; color:#7C9EFF; margin-bottom:8px;">
            📊 Sales Analysis Agent
        </h1>
        <p style="font-size:18px; color:#8B92A5; max-width:600px; margin:0 auto 40px;">
            Upload any sales data → Get instant AI-powered analysis, forecasts & reports
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    steps = [
        (c1, "01", "Upload Data",    "CSV or Excel file — any column structure", "#7C9EFF"),
        (c2, "02", "Map Columns",    "Tell us which column is Date and which is Sales", "#4ADE80"),
        (c3, "03", "Get Results",    "AI analysis, charts, forecast & PDF report", "#FBBF24"),
    ]
    for col, num, title, desc, color in steps:
        with col:
            st.markdown(
                f'<div class="kpi-card">'
                f'<p style="font-size:36px;font-weight:800;color:{color};margin:0">{num}</p>'
                f'<p style="font-size:16px;font-weight:600;color:#E2E8F0;margin:8px 0 4px">{title}</p>'
                f'<p style="font-size:13px;color:#8B92A5;margin:0">{desc}</p>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.divider()
    c4, c5 = st.columns(2)
    with c4:
        st.markdown("#### ✨ What this tool does")
        st.markdown("""
        - 📊 Smart data cleaning & validation
        - 📈 Sales trend & pattern analysis
        - 🏪 Group/store/branch comparison
        - 🔗 External factor correlation
        """)
    with c5:
        st.markdown("#### 🚀 Powered by")
        st.markdown("""
        - 🤖 Claude AI (Anti-Hallucination Protocol)
        - 📊 Holt-Winters Forecasting
        - 📄 Professional PDF Reports
        - 💬 Interactive AI Chat
        """)


# ════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════
def main():
    # ── Header ───────────────────────────────────
    st.markdown(
        f'<h2 style="color:#7C9EFF;margin-bottom:0">{T("app_title")}</h2>'
        f'<p style="color:#8B92A5;margin-top:4px;font-size:13px">{T("app_subtitle")}</p>',
        unsafe_allow_html=True
    )

    # ── Sidebar ───────────────────────────────────
    (uploaded, company_name, date_col, sales_col,
     forecast_weeks, analysis_type, analyze_clicked) = render_sidebar()

    # ── Pipeline Trigger ──────────────────────────
    if analyze_clicked and uploaded:
        # reset chat عند تحليل جديد
        st.session_state.chat_history = []
        st.session_state.ctx = None

        ctx = run_pipeline(
            uploaded, company_name, date_col, sales_col,
            forecast_weeks, analysis_type,
        )
        if ctx:
            st.session_state.ctx      = ctx
            st.session_state.analyzed = True
            st.session_state.last_file = uploaded.name
            st.rerun()

    # ── Main Content ──────────────────────────────
    ctx = st.session_state.ctx

    if ctx is None:
        # لم يتم التحليل بعد
        render_landing()
        return

    # ── Pipeline Status (دائماً مرئي) ────────────
    render_pipeline_status(ctx)

    # ── Tabs ──────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        T("tab_overview"),
        T("tab_charts"),
        T("tab_forecast"),
        T("tab_agent"),
    ])

    with tab1:
        render_overview_tab(ctx)

    with tab2:
        st.markdown(f"#### 📈 {T('tab_charts')}")
        render_charts(ctx)

    with tab3:
        render_forecast_tab(ctx)

    with tab4:
        render_chat_tab(ctx)


# ── Entry Point ──────────────────────────────────
if __name__ == "__main__":
    main()
    