# src/agent.py
import streamlit as st
import os
from anthropic import Anthropic

try:
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
except Exception:
    api_key = None
api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=api_key)

LANG_INSTRUCTION = {
    "en": "Always respond in English.",
    "ar": "يجب أن تجيب دائماً باللغة العربية الفصحى.",
    "fr": "Répondez toujours en français.",
}


def build_system_prompt(summary, store_df, holiday_df, corr_series,
                        forecast_summary, lang="en", company_name=""):
    top5         = store_df.head(5).to_string(index=False) if store_df is not None else "N/A"
    bottom5      = store_df.tail(5).to_string(index=False) if store_df is not None else "N/A"
    holiday_info = holiday_df.to_string(index=False) if holiday_df is not None else "N/A"
    corr_info    = corr_series.to_string()            if corr_series is not None else "N/A"
    lang_instr   = LANG_INSTRUCTION.get(lang, LANG_INSTRUCTION["en"])
    company_line = f"Company: {company_name}" if company_name else ""

    prompt = f"""You are an expert retail sales analyst with 15+ years of experience.
Always be specific with numbers. Never give vague advice.
{lang_instr}
{company_line}

=== DATASET OVERVIEW ===
- Total Records:      {summary.get('total_records','N/A')}
- Date Range:         {summary.get('date_range','N/A')}
- Total Revenue:      ${summary.get('total_sales',0):,.2f}
- Average Per Period: ${summary.get('avg_weekly_sales',0):,.2f}
- Best Period:        ${summary.get('max_single_week',0):,.2f}
- Best Performer:     {summary.get('best_group','N/A')}
- Worst Performer:    {summary.get('worst_group','N/A')}
- Number of Groups:   {summary.get('num_groups','N/A')}

=== TOP 5 PERFORMERS ===
{top5}

=== BOTTOM 5 PERFORMERS ===
{bottom5}

=== HOLIDAY IMPACT ===
{holiday_info}

=== CORRELATIONS WITH SALES ===
{corr_info}

=== FORECAST ===
- Next 4 periods:  ${forecast_summary.get('next_4_weeks',0):,.0f}
- Next 8 periods:  ${forecast_summary.get('next_8_weeks',0):,.0f}
- Next 12 periods: ${forecast_summary.get('next_12_weeks',0):,.0f}
- Peak period:     {forecast_summary.get('peak_week','N/A')}
- Peak sales:      ${forecast_summary.get('peak_expected_sales',0):,.0f}
"""
    return prompt


def ask_agent(question, system_prompt, history=None):
    """استجابة كاملة دفعة واحدة (للتحليل الأولي والتحليلات الطويلة)"""
    if history is None: history = []
    if not isinstance(system_prompt, str): system_prompt = str(system_prompt)
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


def stream_agent(question, system_prompt, history=None):
    """
    Streaming — يولد النص كلمة كلمة مثل ChatGPT
    استخدام: for chunk in stream_agent(...): display(chunk)
    """
    if history is None: history = []
    if not isinstance(system_prompt, str): system_prompt = str(system_prompt)
    messages = history.copy()
    messages.append({"role": "user", "content": question})

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system_prompt,
        messages=messages
    ) as stream:
        for text in stream.text_stream:
            yield text