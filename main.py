from src.data_agent import load_data, get_summary
from src.analyzer_agent import (
    sales_by_store, monthly_sales,
    holiday_vs_normal, correlation_analysis
)
from src.visualizer_agent import (
    plot_sales_trend, plot_store_comparison, plot_monthly_trend,
    plot_holiday_impact, plot_correlations, plot_forecast
)
from src.forecaster_agent import train_and_forecast, get_forecast_summary
from src.orchestrator_agent import SharedContext, ChatAgent

def main():
    print("=" * 55)
    print("   🤖 Walmart Sales Analysis Agent")
    print("=" * 55)

    # ── 1. تحميل البيانات ──────────────────────────────
    print("\n📂 Loading data...")
    df, report = load_data(path='data/Walmart_Sales.csv')
    summary = get_summary(df, date_col='Date', sales_col='Weekly_Sales')
    print(f"✅ {summary['total_records']:,} records | {summary.get('num_groups','N/A')} groups")
    print(f"   Range: {summary['date_range']}")

    # ── 2. التحليل ────────────────────────────────────
    print("\n📊 Analyzing...")
    store_df      = sales_by_store(df)
    monthly_df    = monthly_sales(df)
    holiday_df    = holiday_vs_normal(df)
    corr_series   = correlation_analysis(df)

    # ── 3. الرسوم البيانية ────────────────────────────
    print("\n📈 Generating charts...")
    plot_sales_trend(df, date_col='Date', sales_col='Weekly_Sales')
    plot_store_comparison(store_df, group_col='Store')
    plot_monthly_trend(monthly_df)
    plot_holiday_impact(holiday_df)
    plot_correlations(corr_series)

    # ── 4. التوقعات ───────────────────────────────────
    print("\n🔮 Forecasting next 12 weeks...")
    forecast, prophet_data = train_and_forecast(df, weeks=12)
    forecast_summary = get_forecast_summary(forecast)
    plot_forecast(forecast, prophet_data)
    print(f"   Next 4 weeks: ${forecast_summary['next_4_weeks']:,.0f}")
    print(f"   Next 12 weeks: ${forecast_summary['next_12_weeks']:,.0f}")

    # ── 5. بناء الـ Context للمحادثة ───────────────────
    ctx = SharedContext(
        df=df, summary=summary, store_df=store_df,
        monthly_df=monthly_df, holiday_df=holiday_df,
        corr_series=corr_series, forecast_summary=forecast_summary,
        forecast_df=forecast, prophet_data=prophet_data,
    )

    # ── 6. تحليل أولي تلقائي ─────────────────────────
    print("\n" + "=" * 55)
    print("🔍 Auto-generating initial analysis...")
    print("=" * 55)

    history = []
    chat = ChatAgent(question="Analyze this data and give me top 3 insights with one actionable recommendation each")
    answer, history = chat.ask(ctx)
    print(f"\n🤖 Agent:\n{answer}")

    # ── 7. حلقة الأسئلة ──────────────────────────────
    print("\n" + "=" * 55)
    print("💬 Ask anything about the data (type 'exit' to quit)")
    print("=" * 55)

    while True:
        print()
        question = input("❓ ").strip()

        if not question:
            continue
        if question.lower() in ['exit', 'quit', 'خروج']:
            print("\n👋 Goodbye!")
            break

        chat = ChatAgent(question=question, history=history)
        answer, history = chat.ask(ctx)
        print(f"\n🤖 {answer}")

if __name__ == "__main__":
    main()
