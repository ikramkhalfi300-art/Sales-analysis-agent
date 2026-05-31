import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Sales Analysis Agent", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E40AF; text-align: center; padding: 1rem 0; }
    .sub-header { font-size: 1rem; color: #6B7280; text-align: center; margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📊 Sales Analysis Agent</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Upload any sales data → Get instant analysis & forecasts</p>', unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    st.subheader("📁 Upload Data")
    uploaded_file = st.file_uploader("CSV or Excel file", type=['csv', 'xlsx', 'xls'])

    date_col = None
    sales_col = None

    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                try:
                    preview_df = pd.read_csv(uploaded_file)
                except:
                    uploaded_file.seek(0)
                    preview_df = pd.read_csv(uploaded_file, encoding='latin1')
            else:
                preview_df = pd.read_excel(uploaded_file)
            uploaded_file.seek(0)

            # تنظيف أسماء الأعمدة
            preview_df.columns = preview_df.columns.str.strip()
            cols = preview_df.columns.tolist()

            st.subheader("🗂️ Map Columns")
            st.caption("⚠️ Make sure Date Column contains actual dates")

            date_options = [c for c in cols if any(
                x in c.lower() for x in ['date', 'time', 'week', 'month', 'year', 'day', 'تاريخ']
            )] or cols

            date_col = st.selectbox("📅 Date Column", options=cols,
                index=cols.index(date_options[0]) if date_options else 0)

            sales_options = [c for c in cols if any(
                x in c.lower() for x in ['sale', 'revenue', 'amount', 'total', 'مبيع', 'إيراد']
            )] or cols

            sales_col = st.selectbox("💰 Sales Column", options=cols,
                index=cols.index(sales_options[0]) if sales_options else 0)

            analyze_btn = st.button("🚀 Analyze", type="primary", use_container_width=True)

        except Exception as e:
            st.error(f"Error reading file: {e}")
            analyze_btn = False
    else:
        analyze_btn = False
        st.info("👆 Upload a file to get started")

    st.divider()
    st.caption("Built with Claude AI + Prophet")

# ─── Session State ────────────────────────────────────────
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = None

# ─── التحليل ─────────────────────────────────────────────
if analyze_btn and uploaded_file and date_col and sales_col:

    with st.spinner("🔄 Loading and cleaning data..."):
        try:
            uploaded_file.seek(0)
            if uploaded_file.name.endswith('.csv'):
                try:
                    raw_df = pd.read_csv(uploaded_file)
                except:
                    uploaded_file.seek(0)
                    raw_df = pd.read_csv(uploaded_file, encoding='latin1')
            else:
                raw_df = pd.read_excel(uploaded_file)

            # تنظيف أسماء الأعمدة
            raw_df.columns = raw_df.columns.str.strip()
            date_col = date_col.strip()
            sales_col = sales_col.strip()

            # تحويل التاريخ بكل الطرق الممكنة
            raw_df[date_col] = pd.to_datetime(raw_df[date_col], errors='coerce')

            from src.data_cleaner import clean_data
            df, report = clean_data(raw_df, date_col=date_col, sales_col=sales_col)

            df = df.dropna(subset=[date_col])
            df = df.sort_values(date_col).reset_index(drop=True)

            st.session_state.df = df
            st.session_state.date_col = date_col
            st.session_state.sales_col = sales_col
            st.session_state.report = report

        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            st.stop()

    with st.spinner("📊 Analyzing..."):
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

        st.session_state.summary = summary
        st.session_state.store_df = store_df
        st.session_state.monthly_df = monthly_df
        st.session_state.holiday_df = holiday_df
        st.session_state.corr_series = corr_series
        st.session_state.group_col = group_col

    with st.spinner("🔮 Forecasting..."):
        from src.forecaster import train_and_forecast, get_forecast_summary
        forecast, prophet_data = train_and_forecast(df, weeks=12, date_col=date_col, sales_col=sales_col)
        forecast_summary = get_forecast_summary(forecast)
        st.session_state.forecast = forecast
        st.session_state.prophet_data = prophet_data
        st.session_state.forecast_summary = forecast_summary

    with st.spinner("🤖 Building Agent..."):
        from src.agent import build_system_prompt
        system_prompt = build_system_prompt(
            st.session_state.summary,
            st.session_state.store_df,
            st.session_state.holiday_df,
            st.session_state.corr_series,
            st.session_state.forecast_summary
        )
        st.session_state.system_prompt = system_prompt
        st.session_state.analyzed = True
        st.session_state.chat_history = []

    st.success("✅ Analysis complete!")
    st.rerun()

# ─── عرض النتائج ─────────────────────────────────────────
if st.session_state.analyzed:

    summary = st.session_state.summary
    df = st.session_state.df
    date_col = st.session_state.date_col
    sales_col = st.session_state.sales_col

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Charts", "🔮 Forecast", "🤖 AI Agent"])

    # ── Tab 1 ──────────────────────────────────────────
    with tab1:
        st.subheader("📋 Data Summary")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", f"{summary['total_records']:,}")
        with col2:
            st.metric("Total Sales", f"${summary['total_sales']:,.0f}")
        with col3:
            st.metric("Avg per Period", f"${summary['avg_weekly_sales']:,.0f}")
        with col4:
            st.metric("Best Period", f"${summary['max_single_week']:,.0f}")

        st.divider()

        # Executive Summary
        st.subheader("📋 Executive Summary")
        if st.button("🤖 Generate Executive Summary", type="primary"):
            with st.spinner("Generating report..."):
                from src.agent import ask_agent
                exec_prompt = """
Generate a professional Executive Summary with these sections:

## 1. 📊 Overall Performance
How is the business doing overall? Growth or decline?

## 2. 🏆 Top Performers
Which stores/branches are excelling and why?

## 3. ⚠️ Underperforming Units
Which stores are struggling? What are the likely causes?

## 4. 🔴 Critical Decisions Required
For each underperforming store:
- IMPROVE: specific action to take
- CLOSE: if numbers suggest closure is better

## 5. 💡 Top 3 Actionable Recommendations
Ranked by potential revenue impact.

## 6. 🔮 Outlook
What should management expect next quarter?

Be direct, specific with numbers, and actionable.
"""
                summary_text, _ = ask_agent(exec_prompt, st.session_state.system_prompt, [])
                st.session_state.exec_summary = summary_text

        if 'exec_summary' in st.session_state:
            st.markdown(st.session_state.exec_summary)
            st.download_button(
                label="📥 Download Report",
                data=st.session_state.exec_summary,
                file_name="executive_summary.txt",
                mime="text/plain"
            )

        st.divider()

        with st.expander("🧹 Data Cleaning Report"):
            for line in st.session_state.report:
                st.text(line)

        st.subheader("👀 Data Preview")
        st.dataframe(df.head(20), use_container_width=True)

        if st.session_state.store_df is not None:
            st.subheader(f"🏪 Performance by {st.session_state.group_col}")
            st.dataframe(st.session_state.store_df, use_container_width=True)

    # ── Tab 2 ──────────────────────────────────────────
    with tab2:
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker

        def fmt(x, pos):
            if x >= 1e6: return f'${x/1e6:.1f}M'
            elif x >= 1e3: return f'${x/1e3:.0f}K'
            return f'${x:.0f}'

        st.subheader("📈 Sales Trend")
        weekly = df.groupby(date_col)[sales_col].sum().reset_index()
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(weekly[date_col], weekly[sales_col], color='#2563EB', linewidth=1, alpha=0.6)
        weekly['ma4'] = weekly[sales_col].rolling(4).mean()
        ax.plot(weekly[date_col], weekly['ma4'], color='#DC2626', linewidth=2.5, label='4-Period Avg')
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
        ax.legend(); ax.grid(True, alpha=0.3); plt.tight_layout()
        st.pyplot(fig); plt.close()

        st.subheader("📅 Monthly Sales")
        monthly_df = st.session_state.monthly_df
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.bar([str(m) for m in monthly_df['month']], monthly_df['total'], color='#16A34A', alpha=0.8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
        ax.grid(True, axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right', fontsize=8); plt.tight_layout()
        st.pyplot(fig); plt.close()

        if st.session_state.store_df is not None:
            group_col = st.session_state.group_col
            store_df = st.session_state.store_df
            st.subheader(f"🏪 Sales by {group_col}")
            top10 = store_df.head(10)
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.bar(top10[group_col].astype(str), top10['total'], color='#2563EB', alpha=0.85)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
            ax.grid(True, axis='y', alpha=0.3); plt.tight_layout()
            st.pyplot(fig); plt.close()

        if st.session_state.corr_series is not None:
            st.subheader("🔗 Correlation with Sales")
            corr = st.session_state.corr_series
            fig, ax = plt.subplots(figsize=(8, 4))
            colors = ['#16A34A' if v > 0 else '#DC2626' for v in corr.values]
            ax.barh(corr.index, corr.values, color=colors, alpha=0.85)
            ax.axvline(x=0, color='black', linewidth=0.8)
            ax.grid(True, axis='x', alpha=0.3); plt.tight_layout()
            st.pyplot(fig); plt.close()

    # ── Tab 3 ──────────────────────────────────────────
    with tab3:
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker

        st.subheader("🔮 Sales Forecast - Next 12 Weeks")
        forecast_summary = st.session_state.forecast_summary

        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Next 4 Weeks", f"${forecast_summary['next_4_weeks']:,.0f}")
        with col2: st.metric("Next 8 Weeks", f"${forecast_summary['next_8_weeks']:,.0f}")
        with col3: st.metric("Next 12 Weeks", f"${forecast_summary['next_12_weeks']:,.0f}")

        forecast = st.session_state.forecast
        prophet_data = st.session_state.prophet_data
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(prophet_data['ds'], prophet_data['y'], color='#2563EB', linewidth=1, label='Historical', alpha=0.7)
        future = forecast[forecast['ds'] > prophet_data['ds'].max()]
        ax.plot(future['ds'], future['yhat'], color='#DC2626', linewidth=2.5, label='Forecast')
        ax.fill_between(future['ds'], future['yhat_lower'], future['yhat_upper'], alpha=0.15, color='#DC2626')
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, p: f'${x/1e6:.1f}M' if x >= 1e6 else f'${x/1e3:.0f}K'))
        ax.legend(); ax.grid(True, alpha=0.3); plt.tight_layout()
        st.pyplot(fig); plt.close()

        st.info(f"📅 Peak week: **{forecast_summary['peak_week']}** → **${forecast_summary['peak_expected_sales']:,.0f}**")

    # ── Tab 4 ──────────────────────────────────────────
    with tab4:
        st.subheader("🤖 Ask the AI Agent")
        st.caption("Ask anything about your data in Arabic or English")

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if len(st.session_state.chat_history) == 0:
            with st.spinner("🔍 Generating initial analysis..."):
                from src.agent import ask_agent
                auto_q = "حلل هذه البيانات وأعطني أهم 3 insights مع توصية عملية لكل واحدة"
                answer, history = ask_agent(auto_q, st.session_state.system_prompt, [])
                st.session_state.chat_history = history
                st.rerun()

        if question := st.chat_input("Ask about your sales data..."):
            from src.agent import ask_agent
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer, updated_history = ask_agent(
                        question, st.session_state.system_prompt, st.session_state.chat_history)
                    st.session_state.chat_history = updated_history
                    st.markdown(answer)

# ─── Landing Page ─────────────────────────────────────────
else:
    col1, col2, col3 = st.columns(3)
    with col1: st.info("📁 **Step 1**\nUpload your CSV or Excel file")
    with col2: st.info("🗂️ **Step 2**\nSelect date and sales columns")
    with col3: st.info("🚀 **Step 3**\nClick Analyze and explore!")

    st.divider()
    st.subheader("✨ What this tool does:")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
- 📊 Automatic data cleaning
- 📈 Sales trend charts
- 🏪 Store/branch comparison
- 🔗 External factor analysis
""")
    with col2:
        st.markdown("""
- 🔮 12-week sales forecast
- 🤖 AI-powered insights
- 💬 Chat with your data
- 🌐 Works with any CSV/Excel
""")