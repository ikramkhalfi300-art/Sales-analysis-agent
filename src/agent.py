

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


def build_system_prompt(
    summary,
    store_df,
    holiday_df,
    corr_series,
    forecast_summary,
    kpi_data=None,
    lang="en",
    company_name=""
):
    """
    FIX-A1: system prompt شامل يحتوي على:
    - بيانات الأداء الفعلية
    - سياق الثقة الكامل للتوقعات
    - تحذيرات Sanity Check
    - KPI المتقدمة
    - قواعد منع الهلوسة
    """
    top5         = store_df.head(5).to_string(index=False) if store_df is not None else "N/A"
    bottom5      = store_df.tail(5).to_string(index=False) if store_df is not None else "N/A"
    holiday_info = holiday_df.to_string(index=False) if holiday_df is not None else "N/A"
    corr_info    = corr_series.to_string()            if corr_series is not None else "N/A"
    lang_instr   = LANG_INSTRUCTION.get(lang, LANG_INSTRUCTION["en"])
    company_line = f"Client Organization: {company_name}" if company_name else "Client Organization: [Not specified]"

    # ── بيانات التوقعات مع سياق الثقة الكامل ──────────
    fc_confidence   = forecast_summary.get('confidence_level', 'Medium')
    fc_cv           = forecast_summary.get('cv_pct', 0)
    fc_model        = forecast_summary.get('model_type', 'unknown')
    fc_sanity       = forecast_summary.get('sanity_check', {'passed': True, 'warnings': []})
    fc_volatility   = forecast_summary.get('volatility', {})
    fc_bear_spread  = forecast_summary.get('bear_spread_pct', -25.0)
    fc_bull_spread  = forecast_summary.get('bull_spread_pct',  25.0)
    fc_scenario_method = forecast_summary.get('scenario_method', 'unknown')

    next_4  = forecast_summary.get('next_4_weeks',  0)
    next_8  = forecast_summary.get('next_8_weeks',  0)
    next_12 = forecast_summary.get('next_12_weeks', 0)
    bear_12 = forecast_summary.get('bear_12_weeks', next_12 * 0.75)
    bull_12 = forecast_summary.get('bull_12_weeks', next_12 * 1.25)
    peak_wk = forecast_summary.get('peak_week', 'N/A')
    peak_sv = forecast_summary.get('peak_expected_sales', 0)

    # FIX-A2: تحديد مستوى تحذير التوقعات
    sanity_passed   = fc_sanity.get('passed', True)
    sanity_warnings = fc_sanity.get('warnings', [])

    if not sanity_passed:
        forecast_reliability = "LOW — SANITY CHECK FAILED"
        forecast_instruction = (
            "⚠️ CRITICAL: The forecast has failed the sanity check. "
            "When referencing forecast figures, you MUST state they are directional estimates only "
            "and flag the sanity warnings. Do NOT present these numbers as reliable projections."
        )
    elif fc_confidence == 'Low':
        forecast_reliability = "LOW"
        forecast_instruction = (
            "When referencing forecast figures, always add: "
            "'[Low confidence — treat as directional only]'. "
            "Do not present these as reliable projections."
        )
    elif fc_confidence == 'Medium':
        forecast_reliability = "MEDIUM"
        forecast_instruction = (
            "When referencing forecast figures, state the Bear/Base/Bull range, not just the base case. "
            "Add confidence qualifier: '[Medium confidence]'."
        )
    else:
        forecast_reliability = "HIGH"
        forecast_instruction = (
            "Forecast figures are reliable for planning purposes. "
            "Still reference the Bear/Bull range when discussing resource allocation."
        )

    # ── KPI المتقدمة ────────────────────────────────────
    kpi_section = ""
    if kpi_data:
        mom     = kpi_data.get('mom_growth')
        momentum = kpi_data.get('growth_momentum')
        mom_delta = kpi_data.get('momentum_delta')
        pareto  = kpi_data.get('pareto_pct')
        best_p  = kpi_data.get('best_period', 'N/A')
        worst_p = kpi_data.get('worst_period', 'N/A')
        best_v  = kpi_data.get('best_period_value', 0)
        worst_v = kpi_data.get('worst_period_value', 0)
        avg_v   = kpi_data.get('avg_period_value', 0)
        cv      = kpi_data.get('cv_pct', 0)

        kpi_section = f"""
=== SMART KPIs (DERIVED FROM DATA) ===
- Period-over-Period Growth (MoM):  {f'{mom:+.1f}%' if mom is not None else 'N/A'}
- Growth Momentum:                  {f'{momentum:+.1f}%/period (Δ {mom_delta:+.1f}% vs prior)' if momentum is not None else 'N/A'}
  → Interpretation: {'ACCELERATING ↑' if (momentum or 0) > 0 and (mom_delta or 0) > 0 else 'DECELERATING ↓' if (momentum or 0) > 0 and (mom_delta or 0) < 0 else 'DECLINING' if (momentum or 0) < 0 else 'STABLE'}
- Revenue Concentration (Pareto):   {f'Top {pareto:.0f}% of groups = 80% of revenue' if pareto else 'N/A'}
- Best Period:                      {best_p} (${best_v:,.0f}, {f'+{(best_v-avg_v)/avg_v*100:.0f}% vs avg' if avg_v > 0 else 'N/A'})
- Worst Period:                     {worst_p} (${worst_v:,.0f}, {f'{(worst_v-avg_v)/avg_v*100:.0f}% vs avg' if avg_v > 0 else 'N/A'})
- Revenue Volatility (CV):          {cv:.1f}% → {'EXTREME' if cv > 70 else 'HIGH' if cv > 40 else 'MODERATE' if cv > 20 else 'LOW'}
"""

    # ── Sanity warnings نصية للـ prompt ─────────────────
    sanity_section = ""
    if sanity_warnings:
        sanity_section = "\n=== ⚠️ FORECAST SANITY WARNINGS ===\n"
        for w in sanity_warnings:
            sanity_section += f"- {w}\n"

    prompt = f"""You are a senior business intelligence analyst with 15+ years of experience advising Fortune 500 companies.
You deliver executive-grade analysis: specific, evidence-based, and financially grounded.
{lang_instr}
{company_line}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES — ANTI-HALLUCINATION PROTOCOL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. USE ONLY the numbers provided in this prompt. Never invent, estimate, or extrapolate figures not present here.
2. If a number is not in this prompt, say "data not available" — do NOT fabricate it.
3. For financial impact estimates derived by you (not from data), ALWAYS label them: [ESTIMATED] or [INFERRED].
4. For numbers directly from the dataset, label them: [DATA] when precision matters.
5. NEVER state percentage improvements (e.g., "15% uplift") unless they are directly computed from the data provided.
6. FORECAST RELIABILITY: {forecast_reliability}
   {forecast_instruction}
7. Correlations ≠ causation. Always add this caveat when discussing correlations.
8. Do not mention competitor names, market conditions, or external events not present in the data.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

=== DATASET OVERVIEW ===
- Total Records:        {summary.get('total_records', 'N/A'):,} rows
- Date Range:           {summary.get('date_range', 'N/A')}
- Total Revenue:        ${summary.get('total_sales', 0):,.2f}  [DATA]
- Average Per Period:   ${summary.get('avg_weekly_sales', 0):,.2f}  [DATA]
- Peak Single Period:   ${summary.get('max_single_week', 0):,.2f}  [DATA]
- Min Single Period:    ${summary.get('min_single_week', 0):,.2f}  [DATA]
- Best Performer:       {summary.get('best_group', 'N/A')}
- Worst Performer:      {summary.get('worst_group', 'N/A')}
- Number of Groups:     {summary.get('num_groups', 'N/A')}
{kpi_section}
=== TOP 5 PERFORMERS [DATA] ===
{top5}

=== BOTTOM 5 PERFORMERS [DATA] ===
{bottom5}

=== HOLIDAY IMPACT ===
{holiday_info}

=== CORRELATIONS WITH SALES ===
{corr_info}
NOTE: All correlations are statistical associations only. Causation is NOT established.
Pearson r values — interpret strength as: |r|≥0.8 Very Strong, 0.6-0.8 Strong, 0.4-0.6 Moderate, 0.2-0.4 Weak, <0.2 Negligible.

=== REVENUE FORECAST ===
Model Used:             {fc_model}
Forecast Confidence:    {fc_confidence}  ← {forecast_reliability}
Revenue Volatility:     {fc_volatility.get('level','N/A')} (CV = {fc_cv:.1f}%)
Scenario Method:        {fc_scenario_method}

Forecast Figures [treat per confidence level above]:
- Next 4 Periods:       ${next_4:,.0f}
- Next 8 Periods:       ${next_8:,.0f}
- Next 12 Periods (Base): ${next_12:,.0f}
- Bear Case (12p):      ${bear_12:,.0f}  ({fc_bear_spread:+.1f}% from base — {fc_scenario_method})
- Bull Case (12p):      ${bull_12:,.0f}  (+{fc_bull_spread:.1f}% from base — {fc_scenario_method})
- Projected Peak:       {peak_wk} → ${peak_sv:,.0f}

Planning Range: ${bear_12:,.0f} (Bear) — ${next_12:,.0f} (Base) — ${bull_12:,.0f} (Bull)
{sanity_section}
=== HOW TO REFERENCE FORECASTS IN YOUR RESPONSE ===
- Always state the planning range [Bear–Base–Bull], not just the base case.
- Always include confidence level when citing forecast figures.
- If sanity check failed: flag it explicitly in your response.
- Example correct format: "The base-case forecast projects ${next_12:,.0f} over 12 periods
  [{fc_confidence} confidence], with a Bear/Bull range of ${bear_12:,.0f}–${bull_12:,.0f}."
"""
    return prompt


def ask_agent(question, system_prompt, history=None):
    """
    استجابة كاملة — للتحليلات العميقة والتقارير
    FIX-A5: max_tokens رُفع إلى 4096
    """
    if history is None:
        history = []
    if not isinstance(system_prompt, str):
        system_prompt = str(system_prompt)

    messages = history.copy()
    messages.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=messages
    )
    answer = response.content[0].text
    messages.append({"role": "assistant", "content": answer})
    return answer, messages


def stream_agent(question, system_prompt, history=None):
    """
    Streaming — يولد النص كلمة كلمة
    FIX-A5: max_tokens رُفع إلى 4096
    """
    if history is None:
        history = []
    if not isinstance(system_prompt, str):
        system_prompt = str(system_prompt)

    messages = history.copy()
    messages.append({"role": "user", "content": question})

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=messages
    ) as stream:
        for text in stream.text_stream:
            yield text

