import streamlit as st
import os
from anthropic import Anthropic

api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=api_key)


def build_system_prompt(summary, store_df, holiday_df, corr_series, forecast_summary):

    top5    = store_df.head(5).to_string(index=False) if store_df is not None else "N/A"
    bottom5 = store_df.tail(5).to_string(index=False) if store_df is not None else "N/A"
    holiday_info = holiday_df.to_string(index=False) if holiday_df is not None else "N/A"
    corr_info    = corr_series.to_string() if corr_series is not None else "N/A"

    prompt = f"""You are an expert retail sales analyst with 15+ years of experience.
You have access to complete sales data and must provide precise, actionable insights.
Always be specific with numbers. Never give vague advice.

=== DATASET OVERVIEW ===
- Total Records:    {summary.get('total_records', 'N/A')}
- Date Range:       {summary.get('date_range', 'N/A')}
- Total Revenue:    ${summary.get('total_sales', 0):,.2f}
- Average Per Period: ${summary.get('avg_weekly_sales', 0):,.2f}
- Best Period:      ${summary.get('max_single_week', 0):,.2f}
- Best Performer:   {summary.get('best_group', 'N/A')}
- Worst Performer:  {summary.get('worst_group', 'N/A')}
- Number of Groups: {summary.get('num_groups', 'N/A')}

=== TOP 5 PERFORMERS ===
{top5}

=== BOTTOM 5 PERFORMERS ===
{bottom5}

=== HOLIDAY IMPACT ===
{holiday_info}

=== CORRELATIONS WITH SALES ===
{corr_info}

=== FORECAST (NEXT 12 WEEKS) ===
- Next 4 weeks:  ${forecast_summary.get('next_4_weeks', 0):,.0f}
- Next 8 weeks:  ${forecast_summary.get('next_8_weeks', 0):,.0f}
- Next 12 weeks: ${forecast_summary.get('next_12_weeks', 0):,.0f}
- Peak week:     {forecast_summary.get('peak_week', 'N/A')}
- Peak sales:    ${forecast_summary.get('peak_expected_sales', 0):,.0f}

Answer in the same language the user uses (Arabic or English).
Be direct, specific with numbers, and always actionable.
"""
    return prompt


def ask_agent(question, system_prompt, history=None):

    if history is None:
        history = []

    if not isinstance(system_prompt, str):
        system_prompt = str(system_prompt)

    messages = history.copy()
    messages.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system_prompt,
        messages=messages
    )

    answer = response.content[0].text
    messages.append({"role": "assistant", "content": answer})

    return answer, messages