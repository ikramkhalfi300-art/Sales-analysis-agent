from src.data_loader import load_data, get_summary
from src.analyzer import (
    sales_by_store, monthly_sales,
    holiday_vs_normal, correlation_analysis
)
from src.visualizer import (
    plot_sales_trend, plot_store_comparison, plot_monthly_trend,
    plot_holiday_impact, plot_correlations, plot_forecast
)
from src.forecaster import train_and_forecast, get_forecast_summary
from src.agent import build_system_prompt, ask_agent

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
    plot_sales_trend(df)
    plot_store_comparison(store_df)
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

    # ── 5. بناء الـ Agent ─────────────────────────────
    system_prompt = build_system_prompt(
        summary, store_df, holiday_df, corr_series, forecast_summary
    )

    # ── 6. تحليل أولي تلقائي ─────────────────────────
    print("\n" + "=" * 55)
    print("🔍 Auto-generating initial analysis...")
    print("=" * 55)
    
    history = []
    auto_q = "حلل هذه البيانات وأعطني أهم 3 insights مع توصية عملية لكل واحدة"
    answer, history = ask_agent(auto_q, system_prompt, history)
    print(f"\n🤖 Agent:\n{answer}")

    # ── 7. حلقة الأسئلة ──────────────────────────────
    print("\n" + "=" * 55)
    print("💬 Ask anything about the data (اكتب 'exit' للخروج)")
    print("=" * 55)
    
    while True:
        print()
        question = input("❓ ").strip()
        
        if not question:
            continue
        if question.lower() in ['exit', 'quit', 'خروج']:
            print("\n👋 Goodbye!")
            break
        
        answer, history = ask_agent(question, system_prompt, history)
        print(f"\n🤖 {answer}")

if __name__ == "__main__":
    main()