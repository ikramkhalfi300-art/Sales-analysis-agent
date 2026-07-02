# src/translations.py

TRANSLATIONS = {
    "en": {
        # ── General ──────────────────────────────────────
        "app_title":        "📊 Sales Analysis Agent",
        "app_subtitle":     "Upload any sales data → Get instant analysis & forecasts",
        "built_with":       "Built with Claude AI + Statsmodels",
        "language_label":   "🌐 Language",

        # ── Sidebar ───────────────────────────────────────
        "settings":         "⚙️ Settings",
        "upload_data":      "📁 Upload Data",
        "upload_hint":      "CSV or Excel file",
        "map_columns":      "🗂️ Map Columns",
        "date_warning":     "⚠️ Make sure Date Column contains actual dates",
        "date_col":         "📅 Date Column",
        "sales_col":        "💰 Sales Column",
        "analyze_btn":      "🚀 Analyze",
        "upload_prompt":    "👆 Upload a file to get started",
        "company_name":     "🏢 Company Name (optional)",
        "company_placeholder": "e.g. Acme Corp",

        # ── Tabs ──────────────────────────────────────────
        "tab_overview":     "📊 Overview",
        "tab_charts":       "📈 Charts",
        "tab_forecast":     "🔮 Forecast",
        "tab_agent":        "🤖 AI Agent",

        # ── Tab 1 ─────────────────────────────────────────
        "data_summary":     "📋 Data Summary",
        "total_records":    "Total Records",
        "total_sales":      "Total Sales",
        "avg_period":       "Avg per Period",
        "best_period":      "Best Period",
        "ai_analysis":      "🤖 AI Analysis",
        "choose_analysis":  "Choose analysis type:",
        "analysis_types": [
            "📋 Executive Summary",
            "📊 Performance Analysis",
            "🔴 Problem Detection",
            "💡 Profit Improvement Suggestions",
        ],
        "btn_generate":     "Generate",
        "download_txt":     "📥 Download as Text",
        "download_pdf":     "📥 Download PDF Report",
        "download_pdf_now": "📄 Download PDF Now",
        "cleaning_report":  "🧹 Data Cleaning Report",
        "data_preview":     "👀 Data Preview",
        "performance_by":   "🏪 Performance by",
        "generating_pdf":   "Generating PDF...",
        "generating_ai":    "Generating analysis...",

        # ── Tab 2 ─────────────────────────────────────────
        "sales_trend":      "📈 Sales Trend",
        "monthly_sales":    "📅 Period Sales",
        "sales_by":         "🏪 Sales by",
        "correlation":      "🔗 Correlation with Sales",
        "period_avg":       "4-Period Avg",

        # ── Tab 3 ─────────────────────────────────────────
        "forecast_title":   "🔮 Sales Forecast",
        "next_4":           "Next 4 Periods",
        "next_8":           "Next 8 Periods",
        "next_12":          "Next 12 Periods",
        "historical":       "Historical",
        "forecast_label":   "Forecast",
        "peak_info":        "📅 Peak period:",

        # ── Tab 4 ─────────────────────────────────────────
        "agent_title":      "🤖 Ask the AI Agent",
        "agent_caption":    "Ask anything about your data in Arabic, English or French",
        "chat_placeholder": "Ask about your sales data...",
        "thinking":         "Thinking...",
        "initial_analysis": "🔍 Generating initial analysis...",

        # ── Landing ───────────────────────────────────────
        "step1": "📁 **Step 1**\nUpload your CSV or Excel file",
        "step2": "🗂️ **Step 2**\nSelect date and sales columns",
        "step3": "🚀 **Step 3**\nClick Analyze and explore!",
        "what_it_does": "✨ What this tool does:",
        "feature1": "- 📊 Smart data cleaning\n- 📈 Sales trend charts\n- 🏪 Store/branch comparison\n- 🔗 External factor analysis",
        "feature2": "- 🔮 AI-powered forecasts\n- 🤖 Deep AI insights\n- 📊 Decision-grade analysis\n- 💰 Financial impact estimates",

        # ── PDF ───────────────────────────────────────────
        "pdf_title":        "Sales Analysis Report",
        "pdf_generated":    "Generated",
        "pdf_key_metrics":  "📊 Key Metrics",
        "pdf_metric":       "Metric",
        "pdf_value":        "Value",
        "pdf_date_range":   "Date Range",
        "pdf_avg_period":   "Avg per Period",
        "pdf_best_period":  "Best Period",
        "pdf_trend":        "📈 Sales Trend",
        "pdf_forecast":     "🔮 Forecast Summary",
        "pdf_period":       "Period",
        "pdf_expected":     "Expected Sales",
        "pdf_peak_week":    "Peak Period",
        "pdf_peak_sales":   "Peak Sales",
        "pdf_ai_section":   "🤖 AI Analysis",

        # ── PDF Sections (en) ────────────────────────────────
        "pdf_section_toc_title":       "TABLE OF CONTENTS",
        "pdf_section_toc_subtitle":    "Report Structure",
        "pdf_section_kpi_dashboard":   "Executive KPI Dashboard",
        "pdf_section_exec_summary":    "Executive Summary",
        "pdf_section_data_quality":    "Data Quality Assessment",
        "pdf_section_key_findings":    "Key Findings",
        "pdf_section_sales_overview":  "Sales Performance Overview",
        "pdf_section_trend_analysis":  "Period Trend Analysis",
        "pdf_section_segment":         "Segment Performance & Scorecard",
        "pdf_section_statistical":     "Statistical Validation & Correlations",
        "pdf_section_forecast":        "Revenue Forecast & Scenarios",
        "pdf_section_risk":            "Risk Assessment Matrix",
        "pdf_section_growth":          "Growth Opportunity Assessment",
        "pdf_section_recommendations":  "Strategic Recommendations",
        "pdf_section_appendix":        "Data Appendix & Methodology",
        "pdf_section_advanced_viz":    "Advanced Visual Analytics",

        # ── PDF Exec Summary (en) ────────────────────────────
        "pdf_exec_situation":          "SITUATION \u2014 Where We Are",
        "pdf_exec_complication":       "COMPLICATION \u2014 The Critical Issue",
        "pdf_exec_resolution":         "RESOLUTION \u2014 Recommended Actions",
        "pdf_exec_stakes":             "STAKES \u2014 Financial Impact",
        "pdf_exec_insight_highlights": "Insight Highlights",
        "pdf_exec_performance_analysis": "Performance Analysis",

        # ── PDF KPIs (en) ────────────────────────────────────
        "pdf_kpi_total_revenue":       "Total Revenue",
        "pdf_kpi_12p_forecast":        "12-Period Forecast (Base)",
        "pdf_kpi_revenue_growth":      "Revenue Growth",
        "pdf_kpi_avg_per_period":      "Avg per Period",
        "pdf_kpi_best_group":          "Best Group",
        "pdf_kpi_worst_group":         "Worst Group",
        "pdf_kpi_forecast_confidence": "Forecast Confidence",
        "pdf_kpi_revenue_volatility":  "Revenue Volatility",
        "pdf_kpi_peak_performance":    "Peak Performance",
        "pdf_kpi_12p_forecast_short":  "12-Period Forecast",
        "pdf_kpi_data_quality":        "Data Quality",
        "pdf_kpi_top_risk":            "Top Business Risk",

        # ── PDF Table Headers (en) ───────────────────────────
        "pdf_th_metric":               "Quality Metric",
        "pdf_th_value":                "Value",
        "pdf_th_status":               "Status",
        "pdf_th_notes":                "Notes",
        "pdf_th_num":                  "#",
        "pdf_th_finding":              "Finding",
        "pdf_th_confidence":           "Confidence",
        "pdf_th_evidence":             "Evidence",
        "pdf_th_biz_implication":      "Business Implication",
        "pdf_th_group":                "Group",
        "pdf_th_total_revenue":        "Total Revenue",
        "pdf_th_avg_period":           "Avg / Period",
        "pdf_th_share":                "Portfolio Share",
        "pdf_th_rev_score":            "Rev. Score",
        "pdf_th_efficiency":           "Efficiency",
        "pdf_th_growth_pot":           "Growth Pot.",
        "pdf_th_risk_score":           "Risk Score",
        "pdf_th_overall":              "Overall",
        "pdf_th_grade":                "Grade",
        "pdf_th_variable":             "Variable",
        "pdf_th_pearson_r":            "Pearson r",
        "pdf_th_pvalue":               "P-Value",
        "pdf_th_sample_n":             "Sample (n)",
        "pdf_th_strength":             "Strength",
        "pdf_th_significance":         "Significance",
        "pdf_th_metric_fc":            "Metric",
        "pdf_th_value_fc":             "Value",
        "pdf_th_interpretation":       "Interpretation",
        "pdf_th_risk":                 "Risk",
        "pdf_th_probability":          "Probability",
        "pdf_th_impact":               "Impact",
        "pdf_th_severity":             "Severity",
        "pdf_th_mitigation":           "Recommended Mitigation",
        "pdf_th_opportunity":          "Opportunity",
        "pdf_th_est_impact":           "Est. Impact",
        "pdf_th_effort":               "Effort",
        "pdf_th_basis":                "Basis",
        "pdf_th_parameter":            "Parameter",
        "pdf_th_initiative":           "Initiative",
        "pdf_th_description":          "Description",
        "pdf_th_conf_short":           "Conf.",
        "pdf_th_issue":                "Issue Detected",
        "pdf_th_impact_level":          "Impact Level",
        "pdf_th_action_taken":         "Action Taken",

        # ── PDF Rec Labels (en) ──────────────────────────────
        "pdf_rec_priority":    "PRIORITY",
        "pdf_rec_impact":      "BUSINESS IMPACT",
        "pdf_rec_confidence":  "CONFIDENCE",
        "pdf_rec_roi":         "EXPECTED ROI",
        "pdf_rec_cost":        "EST. IMPLEMENTATION COST",
        "pdf_rec_timeline":    "TIMELINE",
        "pdf_rec_owner":       "DECISION OWNER",
        "pdf_rec_resources":   "REQUIRED RESOURCES",
        "pdf_rec_metric":      "SUCCESS KPI",
        "pdf_rec_risks":       "KEY RISKS",
        "pdf_rec_deps":        "DEPENDENCIES",
        "pdf_rec_hyp":         "HYPOTHESES (TO VALIDATE)",
        "pdf_rec_first":       "FIRST ACTION (48h)",

        # ── PDF Methodology (en) ─────────────────────────────
        "pdf_methodology_doc":          "Methodology Documentation",
        "pdf_method_data_cleaning":     "Data Cleaning",
        "pdf_method_missing_values":    "Missing Value Handling",
        "pdf_method_outliers":          "Outlier Treatment",
        "pdf_method_aggregation":       "Aggregation Logic",
        "pdf_method_forecast":          "Forecast Methodology",
        "pdf_method_forecast_accuracy": "Forecast Accuracy Validation (BUG FIX #1)",
        "pdf_method_statistical":       "Statistical Methods",
        "pdf_method_financial":         "Financial Estimates",

        # ── PDF Other (en) ───────────────────────────────────
        "pdf_footer":           "Confidential Business Analysis Report",
        "pdf_qa_report":        "Quality Assurance Report",
        "pdf_action_plan":      "Priority Action Plan",
        "pdf_cover_classification": "Classification",

        # ── UI Additional (en) ───────────────────────────────
        "ui_advanced_settings": "⚙️ Advanced Settings",
        "ui_forecast_periods":  "Forecast Periods",
        "ui_analysis_type":     "Analysis Type",
        "ui_running_pipeline":  "⚙️ Running Pipeline...",
        "ui_scenario_planning": "📊 Scenario Planning",
        "ui_bear_case":         "Bear Case",
        "ui_base_case":         "Base Case",
        "ui_bull_case":         "Bull Case",
        "ui_trend_continuation":"Trend continuation",
        "ui_forecast_chart":    "📈 Forecast Chart",
        "ui_leading_indicators":"🎯 Leading Indicators",
        "ui_target":            "Target:",
        "ui_alert":             "Alert:",
        "ui_action":            "Action:",
        "ui_data_quality":      "🧹 Data Quality",
        "ui_download_report":   "📄 Download Report",
        "ui_clear_chat":        "🗑️ Clear Chat",
        "ui_what_it_does":      "✨ What this tool does",
        "ui_powered_by":        "🚀 Powered by",
        "ui_step1_title":       "Upload Data",
        "ui_step1_desc":        "CSV or Excel file — any column structure",
        "ui_step2_title":       "Map Columns",
        "ui_step2_desc":        "Tell us which column is Date and which is Sales",
        "ui_step3_title":       "Get Results",
        "ui_step3_desc":        "AI analysis, charts, forecast & PDF report",
        "ui_peak_period":       "Peak Period",
        "ui_best_group":        "Best Group",
        "ui_worst_group":       "Worst Group",
        "ui_num_groups":        "Num Groups",
        "ui_date_range":        "Date Range",
        "ui_metric_col":        "Metric",
        "ui_value_col":         "Value",
        "ui_check_col":         "Check",
        "ui_result_col":        "Result",
        "ui_data_quality_rating":"Data Quality — {rating}",
        "ui_holiday_impact":    "🎉 Holiday Impact",

        # ── Landing page (en) ─────────────────────────────
        "ui_landing_title":     "📊 Sales Analysis Agent",
        "ui_landing_subtitle":  "Upload any sales data → Get instant AI-powered analysis, forecasts & reports",
        "ui_step1_title":       "Upload Data",
        "ui_step1_desc":        "CSV or Excel file — any column structure",
        "ui_step2_title":       "Map Columns",
        "ui_step2_desc":        "Tell us which column is Date and which is Sales",
        "ui_step3_title":       "Get Results",
        "ui_step3_desc":        "AI analysis, charts, forecast & PDF report",
        "ui_what_it_does_tool": "✨ What this tool does",
        "ui_feature_1":         "📊 Smart data cleaning & validation",
        "ui_feature_2":         "📈 Sales trend & pattern analysis",
        "ui_feature_3":         "🏪 Group/store/branch comparison",
        "ui_feature_4":         "🔗 External factor correlation",
        "ui_powered_by_section":"🚀 Powered by",
        "ui_powered_1":         "🤖 Claude AI (Anti-Hallucination Protocol)",
        "ui_powered_2":         "📊 Holt-Winters Forecasting",
        "ui_powered_3":         "📄 Professional PDF Reports",
        "ui_powered_4":         "💬 Interactive AI Chat",

        # ── Analysis types (en) ───────────────────────────
        "ui_analysis_exec_summary":   "Executive Summary",
        "ui_analysis_perf_analysis":  "Performance Analysis",
        "ui_analysis_prob_detect":    "Problem Detection",
        "ui_analysis_profit_improve": "Profit Improvement",

        # ── Pipeline status (en) ──────────────────────────
        "ui_pipeline_status":   "🔍 Pipeline Status",
        "ui_warnings_heading":  "⚠️ Warnings:",
        "ui_errors_heading":    "❌ Errors:",

        # ── Data quality labels (en) ──────────────────────
        "ui_dq_total_records":  "Total Records",
        "ui_dq_missing_values": "Missing Values",
        "ui_dq_duplicates":     "Duplicates",
        "ui_dq_outliers":       "Outliers (IQR)",

        # ── Rating / Confidence labels (en) ───────────────
        "ui_rating_excellent":  "Excellent",
        "ui_rating_good":       "Good",
        "ui_rating_fair":       "Fair",
        "ui_rating_poor":       "Poor",
        "ui_rating_unknown":    "Unknown",
        "ui_conf_high":         "High",
        "ui_conf_medium":       "Medium",
        "ui_conf_low":          "Low",

        # ── Forecast chart labels (en) ────────────────────
        "ui_from_base":         "from base",
        "ui_legend_bear":       "Bear",
        "ui_legend_bull":       "Bull",

        # ── Default column names (en) ─────────────────────
        "ui_date_default":      "Date",
        "ui_sales_default":     "Weekly_Sales",
        "ui_group_fallback":    "Group",

        # ── Misc labels (en) ──────────────────────────────
        "ui_na":                "N/A",
        "ui_currency_sym":      "$",
        "ui_currency_suffix_b":"B",
        "ui_currency_suffix_m":"M",
        "ui_currency_suffix_k":"K",

        # ── Status messages (en) ──────────────────────────
        "ui_file_read_error":   "❌ Failed to read file: {error}",
        "ui_no_charts":         "No charts generated — check Pipeline Status",
        "ui_no_forecast":       "Forecast not available — check Pipeline Status",
        "ui_chat_before_analysis":"⚠️ You must analyze data first before using chat",
        "ui_no_dq_report":      "Data quality report not available",
        "ui_no_ai_analysis":    "AI analysis not generated — check Pipeline Status",

        # ── Auto question ─────────────────────────────────
        "auto_question": "Analyze this data and give me the top 3 insights with one actionable recommendation and estimated financial impact for each.",

        # ── AI Prompts (عميقة + Confidence Score) ─────────
        "prompts": {
            "📋 Executive Summary": """
You are a senior retail consultant. Generate a professional Executive Summary.
Use ONLY numbers from the data provided. Never invent figures.

---

## 1. 📊 Overall Performance
- State exact total revenue, number of periods, and average per period
- Is the trend growing, declining, or flat? Back it up with numbers
- 💰 Financial Baseline: What is the revenue run-rate for next 12 periods?
- 🎯 Confidence: [High/Medium/Low] — state how many periods of data support this

## 2. 🏆 Top Performers
For each top performer:
- 📊 Exact revenue figure and % of total revenue
- 🔍 Why are they outperforming? (location, season, product mix — infer from data)
- 💡 Recommendation: How to replicate their success elsewhere?
- 💰 Estimated impact if replicated: $X additional revenue

## 3. ⚠️ Underperforming Units
For each underperformer:
- 📊 Exact revenue and gap vs average
- 🔍 Root cause: Is it consistent underperformance or recent decline?
- 💡 Decision: IMPROVE (specific action) or RESTRUCTURE (if gap > 40% below average)
- 💰 Cost of inaction vs cost of action

## 4. 🔴 Top 3 Critical Decisions Required RIGHT NOW
Each decision must include:
- The specific problem with exact numbers
- The recommended action (not generic advice)
- Expected financial outcome: $X gain or $X saved
- Deadline: This week / This month / This quarter
- 🎯 Confidence: High / Medium / Low

## 5. 💡 Top 3 Revenue Growth Opportunities
Ranked by potential impact:
1. Highest impact opportunity + estimated $ gain
2. Second opportunity + estimated $ gain
3. Third opportunity + estimated $ gain

## 6. 🔮 12-Period Outlook
- Expected revenue range (low/mid/high scenario)
- Key risks that could reduce revenue
- Key opportunities that could boost revenue
- 🎯 Forecast Confidence: [High/Medium/Low] — based on data quality and trend stability

---
Format numbers clearly. Be direct. Every claim must reference the data.
""",

            "📊 Performance Analysis": """
You are a senior retail performance analyst. Provide deep performance analysis.
Use ONLY numbers from the data. Never invent figures.

---

## 1. 📈 Sales Trend Analysis
- Exact trajectory: growing X% / declining X% / flat
- Identify the 3 most significant turning points with dates and $ impact
- What caused each turning point? (infer from correlations and seasonality)
- 🎯 Confidence in trend: [High/Medium/Low] — based on [N] periods

## 2. 🏪 Unit Performance Ranking
Create a clear ranking:
- 🟢 TOP TIER (top 20%): List each with revenue and what makes them succeed
- 🟡 MID TIER (middle 60%): Which have growth potential? Estimate $ upside
- 🔴 BOTTOM TIER (bottom 20%): Are they declining or just low? Recovery possible?
- 💰 Pareto insight: What % of units drive 80% of revenue?

## 3. 📅 Seasonality & Time Patterns
- Best performing periods: exact dates and revenue
- Worst performing periods: exact dates and revenue
- Is there a consistent weekly/monthly/quarterly pattern?
- 💡 Actionable: When should management prepare extra inventory/staff?
- 💰 Revenue opportunity if peaks are capitalized: estimated $X

## 4. 🔗 External Factor Impact
For each correlated factor:
- Correlation strength and direction
- Estimated $ impact per unit change
- 💡 Specific action to leverage or mitigate this factor
- 🎯 Confidence: [High/Medium/Low]

## 5. 📊 KPI Scorecard
| KPI | Value | vs Average | Rating |
|-----|-------|-----------|--------|
| Revenue Growth | X% | +/- X% | 🟢/🟡/🔴 |
| Peak vs Trough | $X vs $X | ratio | 🟢/🟡/🔴 |
| Consistency Score | X% | | 🟢/🟡/🔴 |

---
Be specific. Every number must come from the data provided.
""",

            "🔴 Problem Detection": """
You are a business turnaround specialist. Identify all problems with surgical precision.
Use ONLY numbers from the data. Never invent figures.

---

## 1. 🚨 CRITICAL — Immediate Action Required (This Week)
For each critical problem:
- 📊 Exact numbers: revenue, decline rate, affected units
- 🔍 Root cause: What is actually causing this?
- 💸 Cost of delay: Every week of inaction costs approximately $X
- 🛠️ Exact fix: Not "improve marketing" but "run promotion in Store X targeting Y demographic"
- ⏰ Deadline: Act within [X days]
- 🎯 Confidence: [High/Medium/Low]

## 2. ⚠️ WARNING SIGNS — Monitor Closely (This Month)
For each warning:
- 📊 Current trajectory and where it leads in 4 weeks if unchanged
- 🔍 Early indicators: What data points signal this problem?
- 💰 Potential revenue at risk: $X
- 💡 Preventive action: Specific step to take now
- 🎯 Confidence: [High/Medium/Low]

## 3. 📉 Chronic Underperformance
Units that have been underperforming consistently:
- Duration of underperformance
- Total revenue lost vs average: $X
- Is recovery realistic? Evidence from data
- 💡 Verdict: Invest / Restructure / Close
- 💰 Financial impact of each option

## 4. 🔗 Hidden Risk Factors
External factors creating hidden vulnerability:
- Which factors correlate negatively with sales?
- Estimated $ impact if factor worsens by 10%
- 💡 Hedge strategy: How to reduce this dependency?

## 5. 🛠️ Priority Fix List
Ranked by urgency × financial impact:
1. Fix [X] → saves/gains $X → do by [date]
2. Fix [Y] → saves/gains $X → do by [date]
3. Fix [Z] → saves/gains $X → do by [date]

---
Be blunt. Use exact numbers. Every problem needs a price tag and a solution.
""",

            "💡 Profit Improvement Suggestions": """
You are a revenue optimization specialist. Provide a concrete profit improvement plan.
Use ONLY numbers from the data. Never invent figures.

---

## 1. 💰 QUICK WINS — Do This Week (0-30 Days)
For each quick win:
- 📊 Opportunity identified from data (exact numbers)
- 🛠️ Specific action: Not "increase sales" but "run X promotion in Y stores during Z period"
- 💰 Expected revenue gain: $X (conservative estimate)
- ⚡ Effort required: Low / Medium
- 🎯 Confidence: [High/Medium/Low] — based on [evidence from data]

## 2. 📈 MEDIUM TERM — This Quarter (1-3 Months)
For each strategy:
- 📊 Data evidence supporting this opportunity
- 🛠️ Specific implementation steps
- 💰 Revenue impact: $X gain over 3 months
- ⚠️ Risk: What could go wrong?
- 🎯 Confidence: [High/Medium/Low]

## 3. 🌟 HIGH IMPACT OPPORTUNITIES
The 3 biggest untapped revenue sources:
1. **Opportunity**: [specific description]
   - Evidence from data: [exact numbers]
   - Estimated annual revenue potential: $X
   - What's needed to capture it?

2. **Opportunity**: [specific description]
   - Evidence: [exact numbers]
   - Potential: $X annually

3. **Opportunity**: [specific description]
   - Evidence: [exact numbers]
   - Potential: $X annually

## 4. 🗑️ STOP DOING — Value Destroyers
Activities/units destroying profitability:
- What to stop: specific unit or activity
- Current cost/loss: $X per period
- What to do instead
- Net gain from stopping: $X

## 5. 💼 12-WEEK REVENUE PROJECTION
If ALL recommendations are implemented:
- Conservative scenario: +$X (X% increase)
- Base scenario: +$X (X% increase)
- Optimistic scenario: +$X (X% increase)
- 🎯 Projection Confidence: [High/Medium/Low]
- Key assumption: [main variable that drives the range]

---
Every suggestion must be specific, numbered, and financially grounded.
Numbers must come from the data. Label confidence for every major claim.
""",
        },
    },

    "ar": {
        # ── General ──────────────────────────────────────
        "app_title":        "📊 وكيل تحليل المبيعات",
        "app_subtitle":     "ارفع أي بيانات مبيعات ← احصل على تحليل فوري وتوقعات",
        "built_with":       "مبني بـ Claude AI + Statsmodels",
        "language_label":   "🌐 اللغة",

        # ── Sidebar ───────────────────────────────────────
        "settings":         "⚙️ الإعدادات",
        "upload_data":      "📁 رفع البيانات",
        "upload_hint":      "ملف CSV أو Excel",
        "map_columns":      "🗂️ تحديد الأعمدة",
        "date_warning":     "⚠️ تأكد أن عمود التاريخ يحتوي على تواريخ فعلية",
        "date_col":         "📅 عمود التاريخ",
        "sales_col":        "💰 عمود المبيعات",
        "analyze_btn":      "🚀 تحليل",
        "upload_prompt":    "👆 ارفع ملفاً للبدء",
        "company_name":     "🏢 اسم الشركة (اختياري)",
        "company_placeholder": "مثال: شركة الفا",

        # ── Tabs ──────────────────────────────────────────
        "tab_overview":     "📊 نظرة عامة",
        "tab_charts":       "📈 الرسوم البيانية",
        "tab_forecast":     "🔮 التوقعات",
        "tab_agent":        "🤖 الذكاء الاصطناعي",

        # ── Tab 1 ─────────────────────────────────────────
        "data_summary":     "📋 ملخص البيانات",
        "total_records":    "إجمالي السجلات",
        "total_sales":      "إجمالي المبيعات",
        "avg_period":       "متوسط الفترة",
        "best_period":      "أفضل فترة",
        "ai_analysis":      "🤖 تحليل الذكاء الاصطناعي",
        "choose_analysis":  "اختر نوع التحليل:",
        "analysis_types": [
            "📋 الملخص التنفيذي",
            "📊 تحليل الأداء",
            "🔴 اكتشاف المشاكل",
            "💡 اقتراحات تحسين الأرباح",
        ],
        "btn_generate":     "توليد",
        "download_txt":     "📥 تنزيل كنص",
        "download_pdf":     "📥 تنزيل تقرير PDF",
        "download_pdf_now": "📄 تنزيل PDF الآن",
        "cleaning_report":  "🧹 تقرير تنظيف البيانات",
        "data_preview":     "👀 معاينة البيانات",
        "performance_by":   "🏪 الأداء حسب",
        "generating_pdf":   "جاري إنشاء PDF...",
        "generating_ai":    "جاري توليد التحليل...",

        # ── Tab 2 ─────────────────────────────────────────
        "sales_trend":      "📈 اتجاه المبيعات",
        "monthly_sales":    "📅 مبيعات الفترة",
        "sales_by":         "🏪 المبيعات حسب",
        "correlation":      "🔗 الارتباط بالمبيعات",
        "period_avg":       "متوسط 4 فترات",

        # ── Tab 3 ─────────────────────────────────────────
        "forecast_title":   "🔮 توقعات المبيعات",
        "next_4":           "الـ 4 فترات القادمة",
        "next_8":           "الـ 8 فترات القادمة",
        "next_12":          "الـ 12 فترة القادمة",
        "historical":       "تاريخي",
        "forecast_label":   "التوقع",
        "peak_info":        "📅 فترة الذروة:",

        # ── Tab 4 ─────────────────────────────────────────
        "agent_title":      "🤖 اسأل الذكاء الاصطناعي",
        "agent_caption":    "اسأل أي شيء عن بياناتك بالعربية أو الإنجليزية أو الفرنسية",
        "chat_placeholder": "اسأل عن بيانات مبيعاتك...",
        "thinking":         "جاري التفكير...",
        "initial_analysis": "🔍 جاري توليد التحليل الأولي...",

        # ── Landing ───────────────────────────────────────
        "step1": "📁 **الخطوة 1**\nارفع ملف CSV أو Excel",
        "step2": "🗂️ **الخطوة 2**\nحدد أعمدة التاريخ والمبيعات",
        "step3": "🚀 **الخطوة 3**\nاضغط تحليل واستكشف!",
        "what_it_does": "✨ ماذا تفعل هذه الأداة:",
        "feature1": "- 📊 تنظيف بيانات ذكي\n- 📈 رسوم اتجاه المبيعات\n- 🏪 مقارنة المتاجر والفروع\n- 🔗 تحليل العوامل الخارجية",
        "feature2": "- 🔮 توقعات بالذكاء الاصطناعي\n- 🤖 تحليل عميق\n- 💰 تقدير الأثر المالي\n- 🎯 قرارات واضحة وقابلة للتنفيذ",

        # ── PDF ───────────────────────────────────────────
        "pdf_title":        "تقرير تحليل المبيعات",
        "pdf_generated":    "تاريخ الإنشاء",
        "pdf_key_metrics":  "📊 المؤشرات الرئيسية",
        "pdf_metric":       "المؤشر",
        "pdf_value":        "القيمة",
        "pdf_date_range":   "نطاق التاريخ",
        "pdf_avg_period":   "متوسط الفترة",
        "pdf_best_period":  "أفضل فترة",
        "pdf_trend":        "📈 اتجاه المبيعات",
        "pdf_forecast":     "🔮 ملخص التوقعات",
        "pdf_period":       "الفترة",
        "pdf_expected":     "المبيعات المتوقعة",
        "pdf_peak_week":    "فترة الذروة",
        "pdf_peak_sales":   "مبيعات الذروة",
        "pdf_ai_section":   "🤖 تحليل الذكاء الاصطناعي",

        # ── PDF Sections (ar) ────────────────────────────────
        "pdf_section_toc_title":       "جدول المحتويات",
        "pdf_section_toc_subtitle":    "هيكل التقرير",
        "pdf_section_kpi_dashboard":   "لوحة مؤشرات الأداء التنفيذية",
        "pdf_section_exec_summary":    "الملخص التنفيذي",
        "pdf_section_data_quality":    "تقييم جودة البيانات",
        "pdf_section_key_findings":    "النتائج الرئيسية",
        "pdf_section_sales_overview":  "نظرة عامة على أداء المبيعات",
        "pdf_section_trend_analysis":  "تحليل الاتجاهات",
        "pdf_section_segment":         "أداء القطاعات وبطاقة النتائج",
        "pdf_section_statistical":     "التحقق الإحصائي والارتباطات",
        "pdf_section_forecast":        "توقعات الإيرادات والسيناريوهات",
        "pdf_section_risk":            "مصفوفة تقييم المخاطر",
        "pdf_section_growth":          "تقييم فرص النمو",
        "pdf_section_recommendations":  "التوصيات الاستراتيجية",
        "pdf_section_appendix":        "ملحق البيانات والمنهجية",
        "pdf_section_advanced_viz":    "التحليلات المرئية المتقدمة",

        # ── PDF Exec Summary (ar) ────────────────────────────
        "pdf_exec_situation":          "الموقف \u2014 أين نحن",
        "pdf_exec_complication":       "التعقيد \u2014 المشكلة الجوهرية",
        "pdf_exec_resolution":         "الحل \u2014 الإجراءات الموصى بها",
        "pdf_exec_stakes":             "المخاطر \u2014 الأثر المالي",
        "pdf_exec_insight_highlights": "أبرز الرؤى",
        "pdf_exec_performance_analysis": "تحليل الأداء",

        # ── PDF KPIs (ar) ────────────────────────────────────
        "pdf_kpi_total_revenue":       "إجمالي الإيرادات",
        "pdf_kpi_12p_forecast":        "توقعات 12 فترة (أساسي)",
        "pdf_kpi_revenue_growth":      "نمو الإيرادات",
        "pdf_kpi_avg_per_period":      "متوسط الفترة",
        "pdf_kpi_best_group":          "أفضل مجموعة",
        "pdf_kpi_worst_group":         "أسوأ مجموعة",
        "pdf_kpi_forecast_confidence": "ثقة التوقعات",
        "pdf_kpi_revenue_volatility":  "تقلب الإيرادات",
        "pdf_kpi_peak_performance":    "أداء الذروة",
        "pdf_kpi_12p_forecast_short":  "توقعات 12 فترة",
        "pdf_kpi_data_quality":        "جودة البيانات",
        "pdf_kpi_top_risk":            "أهم مخاطر الأعمال",

        # ── PDF Table Headers (ar) ───────────────────────────
        "pdf_th_metric":               "مقياس الجودة",
        "pdf_th_value":                "القيمة",
        "pdf_th_status":               "الحالة",
        "pdf_th_notes":                "ملاحظات",
        "pdf_th_num":                  "#",
        "pdf_th_finding":              "النتيجة",
        "pdf_th_confidence":           "الثقة",
        "pdf_th_evidence":             "الدليل",
        "pdf_th_biz_implication":      "الأثر التجاري",
        "pdf_th_group":                "المجموعة",
        "pdf_th_total_revenue":        "إجمالي الإيرادات",
        "pdf_th_avg_period":           "المتوسط / الفترة",
        "pdf_th_share":                "الحصة",
        "pdf_th_rev_score":            "درجة الإيراد",
        "pdf_th_efficiency":           "الكفاءة",
        "pdf_th_growth_pot":           "إمكانات النمو",
        "pdf_th_risk_score":           "درجة المخاطرة",
        "pdf_th_overall":              "الإجمالي",
        "pdf_th_grade":                "التقييم",
        "pdf_th_variable":             "المتغير",
        "pdf_th_pearson_r":            "بيرسون r",
        "pdf_th_pvalue":               "القيمة الاحتمالية",
        "pdf_th_sample_n":             "العينة (ن)",
        "pdf_th_strength":             "القوة",
        "pdf_th_significance":         "الدلالة",
        "pdf_th_metric_fc":            "المقياس",
        "pdf_th_value_fc":             "القيمة",
        "pdf_th_interpretation":       "التفسير",
        "pdf_th_risk":                 "المخاطرة",
        "pdf_th_probability":          "الاحتمال",
        "pdf_th_impact":               "الأثر",
        "pdf_th_severity":             "الخطورة",
        "pdf_th_mitigation":           "التخفيف الموصى به",
        "pdf_th_opportunity":          "الفرصة",
        "pdf_th_est_impact":           "الأثر المقدر",
        "pdf_th_effort":               "الجهد",
        "pdf_th_basis":                "الأساس",
        "pdf_th_parameter":            "المعامل",
        "pdf_th_initiative":           "المبادرة",
        "pdf_th_description":          "الوصف",
        "pdf_th_conf_short":           "الثقة",
        "pdf_th_issue":                "المشكلة المكتشفة",
        "pdf_th_impact_level":          "مستوى الأثر",
        "pdf_th_action_taken":         "الإجراء المتخذ",

        # ── PDF Rec Labels (ar) ──────────────────────────────
        "pdf_rec_priority":    "الأولوية",
        "pdf_rec_impact":      "الأثر التجاري",
        "pdf_rec_confidence":  "الثقة",
        "pdf_rec_roi":         "العائد المتوقع",
        "pdf_rec_cost":        "تكلفة التنفيذ المقدرة",
        "pdf_rec_timeline":    "الجدول الزمني",
        "pdf_rec_owner":       "صاحب القرار",
        "pdf_rec_resources":   "الموارد المطلوبة",
        "pdf_rec_metric":      "مؤشر النجاح",
        "pdf_rec_risks":       "المخاطر الرئيسية",
        "pdf_rec_deps":        "التبعيات",
        "pdf_rec_hyp":         "الفرضيات (للتحقق)",
        "pdf_rec_first":       "أول إجراء (48 ساعة)",

        # ── PDF Methodology (ar) ─────────────────────────────
        "pdf_methodology_doc":          "توثيق المنهجية",
        "pdf_method_data_cleaning":     "تنظيف البيانات",
        "pdf_method_missing_values":    "معالجة القيم المفقودة",
        "pdf_method_outliers":          "معالجة القيم الشاذة",
        "pdf_method_aggregation":       "منطق التجميع",
        "pdf_method_forecast":          "منهجية التوقعات",
        "pdf_method_forecast_accuracy": "التحقق من دقة التوقعات (BUG FIX #1)",
        "pdf_method_statistical":       "الطرق الإحصائية",
        "pdf_method_financial":         "التقديرات المالية",

        # ── PDF Other (ar) ───────────────────────────────────
        "pdf_footer":           "تقرير تحليل أعمال سري",
        "pdf_qa_report":        "تقرير ضمان الجودة",
        "pdf_action_plan":      "خطة العمل ذات الأولوية",
        "pdf_cover_classification": "التصنيف",

        # ── UI Additional (ar) ───────────────────────────────
        "ui_advanced_settings": "⚙️ الإعدادات المتقدمة",
        "ui_forecast_periods":  "فترات التوقع",
        "ui_analysis_type":     "نوع التحليل",
        "ui_running_pipeline":  "⚙️ جاري تشغيل pipeline...",
        "ui_scenario_planning": "📊 تخطيط السيناريوهات",
        "ui_bear_case":         "السيناريو المتحفظ",
        "ui_base_case":         "السيناريو الأساسي",
        "ui_bull_case":         "السيناريو المتفائل",
        "ui_trend_continuation":"استمرار الاتجاه",
        "ui_forecast_chart":    "📈 رسم التوقعات",
        "ui_leading_indicators":"🎯 المؤشرات الرائدة",
        "ui_target":            "الهدف:",
        "ui_alert":             "التنبيه:",
        "ui_action":            "الإجراء:",
        "ui_data_quality":      "🧹 جودة البيانات",
        "ui_download_report":   "📄 تنزيل التقرير",
        "ui_clear_chat":        "🗑️ مسح المحادثة",
        "ui_what_it_does":      "✨ ماذا تفعل هذه الأداة",
        "ui_powered_by":        "🚀 مدعوم بـ",
        "ui_step1_title":       "رفع البيانات",
        "ui_step1_desc":        "ملف CSV أو Excel — أي هيكل أعمدة",
        "ui_step2_title":       "تحديد الأعمدة",
        "ui_step2_desc":        "أخبرنا أي عمود هو التاريخ وأيه هو المبيعات",
        "ui_step3_title":       "احصل على النتائج",
        "ui_step3_desc":        "تحليل ذكي، رسوم بيانية، توقعات وتقرير PDF",
        "ui_peak_period":       "فترة الذروة",
        "ui_best_group":        "أفضل مجموعة",
        "ui_worst_group":       "أسوأ مجموعة",
        "ui_num_groups":        "عدد المجموعات",
        "ui_date_range":        "نطاق التاريخ",
        "ui_metric_col":        "المقياس",
        "ui_value_col":         "القيمة",
        "ui_check_col":         "الفحص",
        "ui_result_col":        "النتيجة",
        "ui_data_quality_rating":"جودة البيانات — {rating}",
        "ui_holiday_impact":    "🎉 أثر العطلات",

        # ── Landing page (ar) ─────────────────────────────
        "ui_landing_title":     "📊 وكيل تحليل المبيعات",
        "ui_landing_subtitle":  "ارفع بيانات مبيعاتك ← احصل على تحليلات وتوقعات وتقارير فورية بالذكاء الاصطناعي",
        "ui_step1_title":       "رفع البيانات",
        "ui_step1_desc":        "ملف CSV أو Excel — أي هيكل أعمدة",
        "ui_step2_title":       "تحديد الأعمدة",
        "ui_step2_desc":        "أخبرنا أي عمود للتاريخ وأي عمود للمبيعات",
        "ui_step3_title":       "عرض النتائج",
        "ui_step3_desc":        "تحليلات ذكية ورسوم بيانية وتوقعات وتقرير PDF",
        "ui_what_it_does_tool": "✨ ماذا تفعل هذه الأداة",
        "ui_feature_1":         "📊 تنظيف ذكي للبيانات والتحقق منها",
        "ui_feature_2":         "📈 تحليل اتجاهات وأنماط المبيعات",
        "ui_feature_3":         "🏪 مقارنة المجموعات والمتاجر والفروع",
        "ui_feature_4":         "🔗 ارتباط العوامل الخارجية",
        "ui_powered_by_section":"🚀 مدعوم بواسطة",
        "ui_powered_1":         "🤖 Claude AI (بروتوكول مقاومة الهلوسة)",
        "ui_powered_2":         "📊 تنبؤ Holt-Winters",
        "ui_powered_3":         "📄 تقارير PDF احترافية",
        "ui_powered_4":         "💬 محادثة تفاعلية بالذكاء الاصطناعي",

        # ── Analysis types (ar) ───────────────────────────
        "ui_analysis_exec_summary":   "ملخص تنفيذي",
        "ui_analysis_perf_analysis":  "تحليل الأداء",
        "ui_analysis_prob_detect":    "كشف المشكلات",
        "ui_analysis_profit_improve": "تحسين الأرباح",

        # ── Pipeline status (ar) ──────────────────────────
        "ui_pipeline_status":   "🔍 حالة خط الأنابيب",
        "ui_warnings_heading":  "⚠️ تحذيرات:",
        "ui_errors_heading":    "❌ أخطاء:",

        # ── Data quality labels (ar) ──────────────────────
        "ui_dq_total_records":  "إجمالي السجلات",
        "ui_dq_missing_values": "القيم المفقودة",
        "ui_dq_duplicates":     "المكررات",
        "ui_dq_outliers":       "القيم الشاذة (IQR)",

        # ── Rating / Confidence labels (ar) ───────────────
        "ui_rating_excellent":  "ممتاز",
        "ui_rating_good":       "جيد",
        "ui_rating_fair":       "مقبول",
        "ui_rating_poor":       "ضعيف",
        "ui_rating_unknown":    "غير معروف",
        "ui_conf_high":         "عالية",
        "ui_conf_medium":       "متوسطة",
        "ui_conf_low":          "منخفضة",

        # ── Forecast chart labels (ar) ────────────────────
        "ui_from_base":         "عن الأساس",
        "ui_legend_bear":       "متشائم",
        "ui_legend_bull":       "متفائل",

        # ── Default column names (ar) ─────────────────────
        "ui_date_default":      "التاريخ",
        "ui_sales_default":     "المبيعات_الأسبوعية",
        "ui_group_fallback":    "المجموعة",

        # ── Misc labels (ar) ──────────────────────────────
        "ui_na":                "غير متاح",
        "ui_currency_sym":      "$",
        "ui_currency_suffix_b":"مليار",
        "ui_currency_suffix_m":"مليون",
        "ui_currency_suffix_k":"ألف",

        # ── Status messages (ar) ──────────────────────────
        "ui_file_read_error":   "❌ فشل قراءة الملف: {error}",
        "ui_no_charts":         "لم يتم إنشاء رسوم بيانية — تحقق من Pipeline Status",
        "ui_no_forecast":       "التوقعات غير متاحة — تحقق من Pipeline Status",
        "ui_chat_before_analysis":"⚠️ يجب تحليل البيانات أولاً قبل استخدام المحادثة",
        "ui_no_dq_report":      "تقرير جودة البيانات غير متاح",
        "ui_no_ai_analysis":    "لم يتم توليد تحليل ذكي — تحقق من Pipeline Status",

        # ── Auto question ─────────────────────────────────
        "auto_question": "حلل هذه البيانات وأعطني أهم 3 insights مع توصية عملية وتقدير مالي لكل واحدة. أجب باللغة العربية.",

        # ── AI Prompts (عميقة + Confidence Score) ─────────
        "prompts": {
            "📋 الملخص التنفيذي": """
أنت مستشار تجزئة أول. اكتب ملخصاً تنفيذياً احترافياً باللغة العربية.
استخدم فقط الأرقام الموجودة في البيانات. لا تخترع أرقاماً.

---

## 1. 📊 الأداء العام
- اذكر الإيراد الإجمالي الدقيق وعدد الفترات والمتوسط لكل فترة
- هل الاتجاه نمو أم تراجع أم ثبات؟ ادعم بأرقام
- 💰 معدل الإيراد المتوقع للـ 12 فترة القادمة
- 🎯 مستوى الثقة: [عالي/متوسط/منخفض] — بناءً على [N] فترة من البيانات

## 2. 🏆 الأفضل أداءً
لكل متجر/فرع متميز:
- 📊 الإيراد الدقيق ونسبته من الإجمالي
- 🔍 لماذا يتفوق؟ (استنتج من البيانات)
- 💡 توصية: كيف نكرر نجاحه في أماكن أخرى؟
- 💰 الأثر المالي المقدر إذا طُبق: $X إيراد إضافي

## 3. ⚠️ الوحدات الضعيفة
لكل متجر/فرع ضعيف:
- 📊 الإيراد الدقيق والفجوة عن المتوسط
- 🔍 السبب الجذري: هل الضعف مستمر أم حديث؟
- 💡 القرار: تحسين (إجراء محدد) أو إعادة هيكلة (إذا كان الفجوة أكثر من 40%)
- 💰 تكلفة التقاعس مقارنة بتكلفة التحرك

## 4. 🔴 أهم 3 قرارات عاجلة
لكل قرار:
- المشكلة المحددة بأرقام دقيقة
- الإجراء الموصى به (محدد وليس عاماً)
- النتيجة المالية المتوقعة: $X ربح أو $X توفير
- الموعد: هذا الأسبوع / هذا الشهر / هذا الربع
- 🎯 مستوى الثقة: عالي / متوسط / منخفض

## 5. 💡 أهم 3 فرص نمو
مرتبة حسب الأثر المحتمل:
1. الفرصة الأكبر + $X ربح مقدر
2. الفرصة الثانية + $X ربح مقدر
3. الفرصة الثالثة + $X ربح مقدر

## 6. 🔮 توقعات 12 فترة
- نطاق الإيراد المتوقع (سيناريو منخفض/متوسط/مرتفع)
- أبرز المخاطر التي قد تخفض الإيراد
- أبرز الفرص التي قد ترفع الإيراد
- 🎯 ثقة التوقع: [عالي/متوسط/منخفض]

---
كن مباشراً. كل ادعاء يجب أن يستند إلى البيانات. الأرقام بالدولار.
""",
            "📊 تحليل الأداء": """
أنت محلل أداء تجزئة أول. قدم تحليلاً عميقاً باللغة العربية.
استخدم فقط الأرقام الموجودة في البيانات.

---

## 1. 📈 تحليل اتجاه المبيعات
- المسار الدقيق: نمو X% / تراجع X% / ثبات
- حدد 3 نقاط تحول رئيسية مع التواريخ والأثر المالي بالدولار
- ما السبب وراء كل نقطة تحول؟
- 🎯 ثقة الاتجاه: [عالي/متوسط/منخفض] — بناءً على [N] فترة

## 2. 🏪 تصنيف الوحدات
- 🟢 الفئة العليا (أفضل 20%): كل واحد مع إيراده وسبب تميزه
- 🟡 الفئة المتوسطة (60% الوسط): أيها لديه إمكانية نمو؟ قدّر $X
- 🔴 الفئة الدنيا (أضعف 20%): هل التراجع حديث أم مزمن؟
- 💰 قاعدة باريتو: كم % من الوحدات يولد 80% من الإيراد؟

## 3. 📅 الأنماط الموسمية والزمنية
- أفضل الفترات: تواريخ دقيقة وإيراد
- أسوأ الفترات: تواريخ دقيقة وإيراد
- هل هناك نمط أسبوعي/شهري/ربعي ثابت؟
- 💡 متى يجب الاستعداد بمخزون ووظفاء إضافيين؟
- 💰 فرصة إيرادية إذا استُغلت الذروات: $X مقدر

## 4. 🔗 أثر العوامل الخارجية
لكل عامل مترابط:
- قوة الارتباط واتجاهه
- الأثر المالي المقدر لكل وحدة تغيير
- 💡 إجراء محدد للاستفادة أو التخفيف
- 🎯 مستوى الثقة: [عالي/متوسط/منخفض]

## 5. 📊 بطاقة مؤشرات الأداء
| المؤشر | القيمة | مقارنة بالمتوسط | التقييم |
|--------|--------|----------------|---------|
| نمو الإيراد | X% | +/- X% | 🟢/🟡/🔴 |
| الذروة مقابل الحضيض | $X مقابل $X | النسبة | 🟢/🟡/🔴 |
| معدل الاتساق | X% | | 🟢/🟡/🔴 |

---
كل رقم يجب أن يأتي من البيانات. كن محدداً.
""",
            "🔴 اكتشاف المشاكل": """
أنت متخصص في إنقاذ الشركات. حدد المشاكل بدقة جراحية باللغة العربية.
استخدم فقط الأرقام الموجودة في البيانات.

---

## 1. 🚨 حرج — تدخل فوري مطلوب (هذا الأسبوع)
لكل مشكلة حرجة:
- 📊 الأرقام الدقيقة: الإيراد، معدل التراجع، الوحدات المتأثرة
- 🔍 السبب الجذري: ما الذي يسبب هذا فعلاً؟
- 💸 تكلفة التأخير: كل أسبوع تقاعس يكلف تقريباً $X
- 🛠️ الحل الدقيق: ليس "حسّن التسويق" بل إجراء محدد جداً
- ⏰ الموعد النهائي: تصرف خلال [X أيام]
- 🎯 مستوى الثقة: [عالي/متوسط/منخفض]

## 2. ⚠️ إشارات تحذيرية — راقب عن كثب (هذا الشهر)
لكل تحذير:
- 📊 المسار الحالي وأين يؤدي خلال 4 أسابيع إذا لم يتغير
- 🔍 المؤشرات المبكرة: ما نقاط البيانات التي تكشف هذه المشكلة؟
- 💰 الإيراد المعرض للخطر: $X
- 💡 إجراء وقائي محدد الآن
- 🎯 مستوى الثقة: [عالي/متوسط/منخفض]

## 3. 📉 ضعف أداء مزمن
الوحدات التي تعاني باستمرار:
- مدة الضعف
- الإيراد الضائع مقارنة بالمتوسط: $X
- هل التعافي واقعي؟ دليل من البيانات
- 💡 الحكم: استثمر / أعد هيكلة / أغلق
- 💰 الأثر المالي لكل خيار

## 4. 🔗 عوامل خطر خفية
- أي العوامل ترتبط سلباً بالمبيعات؟
- الأثر المالي المقدر إذا ساء العامل بنسبة 10%
- 💡 استراتيجية تحوط: كيف نقلل هذا الاعتماد؟

## 5. 🛠️ قائمة الأولويات
مرتبة حسب الإلحاحية × الأثر المالي:
1. أصلح [X] ← يوفر/يكسب $X ← افعل بحلول [تاريخ]
2. أصلح [Y] ← يوفر/يكسب $X ← افعل بحلول [تاريخ]
3. أصلح [Z] ← يوفر/يكسب $X ← افعل بحلول [تاريخ]

---
كن صريحاً. كل مشكلة تحتاج سعراً وحلاً. الأرقام من البيانات فقط.
""",
            "💡 اقتراحات تحسين الأرباح": """
أنت متخصص في تحسين الإيرادات. قدم خطة أرباح ملموسة باللغة العربية.
استخدم فقط الأرقام الموجودة في البيانات.

---

## 1. 💰 مكاسب سريعة — افعلها هذا الأسبوع (0-30 يوم)
لكل مكسب سريع:
- 📊 الفرصة المحددة من البيانات (أرقام دقيقة)
- 🛠️ الإجراء المحدد: ليس "زد المبيعات" بل خطوة واضحة جداً
- 💰 الربح المتوقع: $X (تقدير محافظ)
- ⚡ الجهد المطلوب: منخفض / متوسط
- 🎯 مستوى الثقة: [عالي/متوسط/منخفض]

## 2. 📈 استراتيجية متوسطة المدى (1-3 أشهر)
لكل استراتيجية:
- 📊 الدليل من البيانات يدعم هذه الفرصة
- 🛠️ خطوات التنفيذ المحددة
- 💰 أثر الإيراد: $X ربح خلال 3 أشهر
- ⚠️ الخطر: ما الذي قد يسوء؟
- 🎯 مستوى الثقة: [عالي/متوسط/منخفض]

## 3. 🌟 فرص عالية الأثر
أكبر 3 مصادر إيراد غير مستغلة:
1. **الفرصة**: [وصف محدد]
   - الدليل: [أرقام دقيقة]
   - الإمكانية السنوية: $X
   - ما المطلوب للاستفادة منها؟

2. **الفرصة**: [وصف محدد]
   - الدليل: [أرقام]
   - الإمكانية: $X سنوياً

3. **الفرصة**: [وصف محدد]
   - الدليل: [أرقام]
   - الإمكانية: $X سنوياً

## 4. 🗑️ توقف عن هذا — مدمرات القيمة
أنشطة/وحدات تدمر الربحية:
- ما يجب إيقافه: وحدة أو نشاط محدد
- التكلفة/الخسارة الحالية: $X لكل فترة
- البديل الأفضل
- صافي الربح من التوقف: $X

## 5. 💼 توقع إيرادات 12 فترة
إذا نُفذت جميع التوصيات:
- السيناريو المحافظ: +$X (زيادة X%)
- السيناريو الأساسي: +$X (زيادة X%)
- السيناريو المتفائل: +$X (زيادة X%)
- 🎯 ثقة التوقع: [عالي/متوسط/منخفض]
- الافتراض الرئيسي: [المتغير الأساسي]

---
كل اقتراح محدد ومرقم ومدعوم مالياً. الأرقام من البيانات فقط.
""",
        },
    },

    "fr": {
        # ── General ──────────────────────────────────────
        "app_title":        "📊 Agent d'Analyse des Ventes",
        "app_subtitle":     "Importez vos données → Obtenez une analyse instantanée",
        "built_with":       "Construit avec Claude AI + Statsmodels",
        "language_label":   "🌐 Langue",

        # ── Sidebar ───────────────────────────────────────
        "settings":         "⚙️ Paramètres",
        "upload_data":      "📁 Importer des données",
        "upload_hint":      "Fichier CSV ou Excel",
        "map_columns":      "🗂️ Mapper les colonnes",
        "date_warning":     "⚠️ Assurez-vous que la colonne Date contient des dates réelles",
        "date_col":         "📅 Colonne Date",
        "sales_col":        "💰 Colonne Ventes",
        "analyze_btn":      "🚀 Analyser",
        "upload_prompt":    "👆 Importez un fichier pour commencer",
        "company_name":     "🏢 Nom de l'entreprise (optionnel)",
        "company_placeholder": "ex. Société Dupont",

        # ── Tabs ──────────────────────────────────────────
        "tab_overview":     "📊 Vue d'ensemble",
        "tab_charts":       "📈 Graphiques",
        "tab_forecast":     "🔮 Prévisions",
        "tab_agent":        "🤖 Agent IA",

        # ── Tab 1 ─────────────────────────────────────────
        "data_summary":     "📋 Résumé des données",
        "total_records":    "Total enregistrements",
        "total_sales":      "Ventes totales",
        "avg_period":       "Moyenne par période",
        "best_period":      "Meilleure période",
        "ai_analysis":      "🤖 Analyse IA",
        "choose_analysis":  "Choisissez le type d'analyse :",
        "analysis_types": [
            "📋 Résumé exécutif",
            "📊 Analyse des performances",
            "🔴 Détection des problèmes",
            "💡 Suggestions d'amélioration des profits",
        ],
        "btn_generate":     "Générer",
        "download_txt":     "📥 Télécharger en texte",
        "download_pdf":     "📥 Télécharger le rapport PDF",
        "download_pdf_now": "📄 Télécharger PDF maintenant",
        "cleaning_report":  "🧹 Rapport de nettoyage",
        "data_preview":     "👀 Aperçu des données",
        "performance_by":   "🏪 Performance par",
        "generating_pdf":   "Génération du PDF...",
        "generating_ai":    "Génération de l'analyse...",

        # ── Tab 2 ─────────────────────────────────────────
        "sales_trend":      "📈 Tendance des ventes",
        "monthly_sales":    "📅 Ventes par période",
        "sales_by":         "🏪 Ventes par",
        "correlation":      "🔗 Corrélation avec les ventes",
        "period_avg":       "Moyenne 4 périodes",

        # ── Tab 3 ─────────────────────────────────────────
        "forecast_title":   "🔮 Prévisions des ventes",
        "next_4":           "4 prochaines périodes",
        "next_8":           "8 prochaines périodes",
        "next_12":          "12 prochaines périodes",
        "historical":       "Historique",
        "forecast_label":   "Prévision",
        "peak_info":        "📅 Période de pointe :",

        # ── Tab 4 ─────────────────────────────────────────
        "agent_title":      "🤖 Interroger l'Agent IA",
        "agent_caption":    "Posez des questions en arabe, anglais ou français",
        "chat_placeholder": "Posez une question sur vos données...",
        "thinking":         "Réflexion en cours...",
        "initial_analysis": "🔍 Génération de l'analyse initiale...",

        # ── Landing ───────────────────────────────────────
        "step1": "📁 **Étape 1**\nImportez votre fichier CSV ou Excel",
        "step2": "🗂️ **Étape 2**\nSélectionnez les colonnes date et ventes",
        "step3": "🚀 **Étape 3**\nCliquez sur Analyser et explorez !",
        "what_it_does": "✨ Ce que fait cet outil :",
        "feature1": "- 📊 Nettoyage intelligent\n- 📈 Graphiques de tendance\n- 🏪 Comparaison des magasins\n- 🔗 Analyse des facteurs externes",
        "feature2": "- 🔮 Prévisions IA\n- 🤖 Analyse approfondie\n- 💰 Impact financier estimé\n- 🎯 Décisions actionnables",

        # ── PDF ───────────────────────────────────────────
        "pdf_title":        "Rapport d'Analyse des Ventes",
        "pdf_generated":    "Généré le",
        "pdf_key_metrics":  "📊 Indicateurs clés",
        "pdf_metric":       "Indicateur",
        "pdf_value":        "Valeur",
        "pdf_date_range":   "Plage de dates",
        "pdf_avg_period":   "Moyenne par période",
        "pdf_best_period":  "Meilleure période",
        "pdf_trend":        "📈 Tendance des ventes",
        "pdf_forecast":     "🔮 Résumé des prévisions",
        "pdf_period":       "Période",
        "pdf_expected":     "Ventes prévues",
        "pdf_peak_week":    "Période de pointe",
        "pdf_peak_sales":   "Ventes de pointe",
        "pdf_ai_section":   "🤖 Analyse IA",

        # ── PDF Sections (fr) ────────────────────────────────
        "pdf_section_toc_title":       "TABLE DES MATI\u00c8RES",
        "pdf_section_toc_subtitle":    "Structure du rapport",
        "pdf_section_kpi_dashboard":   "Tableau de bord KPI ex\u00e9cutif",
        "pdf_section_exec_summary":    "R\u00e9sum\u00e9 ex\u00e9cutif",
        "pdf_section_data_quality":    "\u00c9valuation de la qualit\u00e9 des donn\u00e9es",
        "pdf_section_key_findings":    "Constats principaux",
        "pdf_section_sales_overview":  "Aper\u00e7u de la performance des ventes",
        "pdf_section_trend_analysis":  "Analyse des tendances p\u00e9riodiques",
        "pdf_section_segment":         "Performance des segments et tableau de bord",
        "pdf_section_statistical":     "Validation statistique et corr\u00e9lations",
        "pdf_section_forecast":        "Pr\u00e9visions de revenus et sc\u00e9narios",
        "pdf_section_risk":            "Matrice d'\u00e9valuation des risques",
        "pdf_section_growth":          "\u00c9valuation des opportunit\u00e9s de croissance",
        "pdf_section_recommendations":  "Recommandations strat\u00e9giques",
        "pdf_section_appendix":        "Annexe des donn\u00e9es et m\u00e9thodologie",
        "pdf_section_advanced_viz":    "Analyses visuelles avanc\u00e9es",

        # ── PDF Exec Summary (fr) ────────────────────────────
        "pdf_exec_situation":          "SITUATION \u2014 O\u00f9 nous sommes",
        "pdf_exec_complication":       "COMPLICATION \u2014 Le probl\u00e8me critique",
        "pdf_exec_resolution":         "R\u00c9SOLUTION \u2014 Actions recommand\u00e9es",
        "pdf_exec_stakes":             "ENJEUX \u2014 Impact financier",
        "pdf_exec_insight_highlights": "Points saillants",
        "pdf_exec_performance_analysis": "Analyse des performances",

        # ── PDF KPIs (fr) ────────────────────────────────────
        "pdf_kpi_total_revenue":       "Revenu total",
        "pdf_kpi_12p_forecast":        "Pr\u00e9vision 12 p\u00e9riodes (sc\u00e9nario de base)",
        "pdf_kpi_revenue_growth":      "Croissance des revenus",
        "pdf_kpi_avg_per_period":      "Moyenne par p\u00e9riode",
        "pdf_kpi_best_group":          "Meilleur groupe",
        "pdf_kpi_worst_group":         "Pire groupe",
        "pdf_kpi_forecast_confidence": "Confiance des pr\u00e9visions",
        "pdf_kpi_revenue_volatility":  "Volatilit\u00e9 des revenus",
        "pdf_kpi_peak_performance":    "Performance de pointe",
        "pdf_kpi_12p_forecast_short":  "Pr\u00e9vision 12 p\u00e9riodes",
        "pdf_kpi_data_quality":        "Qualit\u00e9 des donn\u00e9es",
        "pdf_kpi_top_risk":            "Principal risque commercial",

        # ── PDF Table Headers (fr) ───────────────────────────
        "pdf_th_metric":               "Indicateur de qualit\u00e9",
        "pdf_th_value":                "Valeur",
        "pdf_th_status":               "Statut",
        "pdf_th_notes":                "Notes",
        "pdf_th_num":                  "#",
        "pdf_th_finding":              "Constat",
        "pdf_th_confidence":           "Confiance",
        "pdf_th_evidence":             "Preuve",
        "pdf_th_biz_implication":      "Implication commerciale",
        "pdf_th_group":                "Groupe",
        "pdf_th_total_revenue":        "Revenu total",
        "pdf_th_avg_period":           "Moy. / p\u00e9riode",
        "pdf_th_share":                "Part du portefeuille",
        "pdf_th_rev_score":            "Score revenu",
        "pdf_th_efficiency":           "Efficacit\u00e9",
        "pdf_th_growth_pot":           "Potentiel de croissance",
        "pdf_th_risk_score":           "Score de risque",
        "pdf_th_overall":              "Global",
        "pdf_th_grade":                "Note",
        "pdf_th_variable":             "Variable",
        "pdf_th_pearson_r":            "Pearson r",
        "pdf_th_pvalue":               "Valeur p",
        "pdf_th_sample_n":             "\u00c9chantillon (n)",
        "pdf_th_strength":             "Force",
        "pdf_th_significance":         "Significativit\u00e9",
        "pdf_th_metric_fc":            "M\u00e9trique",
        "pdf_th_value_fc":             "Valeur",
        "pdf_th_interpretation":       "Interpr\u00e9tation",
        "pdf_th_risk":                 "Risque",
        "pdf_th_probability":          "Probabilit\u00e9",
        "pdf_th_impact":               "Impact",
        "pdf_th_severity":             "Gravit\u00e9",
        "pdf_th_mitigation":           "Att\u00e9nuation recommand\u00e9e",
        "pdf_th_opportunity":          "Opportunit\u00e9",
        "pdf_th_est_impact":           "Impact estim\u00e9",
        "pdf_th_effort":               "Effort",
        "pdf_th_basis":                "Base",
        "pdf_th_parameter":            "Param\u00e8tre",
        "pdf_th_initiative":           "Initiative",
        "pdf_th_description":          "Description",
        "pdf_th_conf_short":           "Conf.",
        "pdf_th_issue":                "Probl\u00e8me d\u00e9tect\u00e9",
        "pdf_th_impact_level":          "Niveau d'impact",
        "pdf_th_action_taken":         "Action prise",

        # ── PDF Rec Labels (fr) ──────────────────────────────
        "pdf_rec_priority":    "PRIORIT\u00c9",
        "pdf_rec_impact":      "IMPACT COMMERCIAL",
        "pdf_rec_confidence":  "CONFIANCE",
        "pdf_rec_roi":         "ROI ATTENDU",
        "pdf_rec_cost":        "CO\u00dbT D'IMPL\u00c9MENTATION ESTIM\u00c9",
        "pdf_rec_timeline":    "\u00c9CH\u00c9ANCIER",
        "pdf_rec_owner":       "PROPRI\u00c9TAIRE DE LA D\u00c9CISION",
        "pdf_rec_resources":   "RESSOURCES REQUISES",
        "pdf_rec_metric":      "KPI DE SUCC\u00c8S",
        "pdf_rec_risks":       "RISQUES CL\u00c9S",
        "pdf_rec_deps":        "D\u00c9PENDANCES",
        "pdf_rec_hyp":         "HYPOTH\u00c8SES (\u00c0 VALIDER)",
        "pdf_rec_first":       "PREMI\u00c8RE ACTION (48h)",

        # ── PDF Methodology (fr) ─────────────────────────────
        "pdf_methodology_doc":          "Documentation m\u00e9thodologique",
        "pdf_method_data_cleaning":     "Nettoyage des donn\u00e9es",
        "pdf_method_missing_values":    "Gestion des valeurs manquantes",
        "pdf_method_outliers":          "Traitement des valeurs aberrantes",
        "pdf_method_aggregation":       "Logique d'agr\u00e9gation",
        "pdf_method_forecast":          "M\u00e9thodologie de pr\u00e9vision",
        "pdf_method_forecast_accuracy": "Validation de la pr\u00e9cision des pr\u00e9visions (BUG FIX #1)",
        "pdf_method_statistical":       "M\u00e9thodes statistiques",
        "pdf_method_financial":         "Estimations financi\u00e8res",

        # ── PDF Other (fr) ───────────────────────────────────
        "pdf_footer":           "Rapport d'analyse commerciale confidentiel",
        "pdf_qa_report":        "Rapport d'assurance qualit\u00e9",
        "pdf_action_plan":      "Plan d'action prioritaire",
        "pdf_cover_classification": "Classification",

        # ── UI Additional (fr) ───────────────────────────────
        "ui_advanced_settings": "⚙️ Param\u00e8tres avanc\u00e9s",
        "ui_forecast_periods":  "P\u00e9riodes de pr\u00e9vision",
        "ui_analysis_type":     "Type d'analyse",
        "ui_running_pipeline":  "⚙️ Ex\u00e9cution du pipeline...",
        "ui_scenario_planning": "📊 Planification de sc\u00e9narios",
        "ui_bear_case":         "Sc\u00e9nario baissier",
        "ui_base_case":         "Sc\u00e9nario de base",
        "ui_bull_case":         "Sc\u00e9nario haussier",
        "ui_trend_continuation":"Poursuite de la tendance",
        "ui_forecast_chart":    "📈 Graphique des pr\u00e9visions",
        "ui_leading_indicators":"🎯 Indicateurs avanc\u00e9s",
        "ui_target":            "Objectif :",
        "ui_alert":             "Alerte :",
        "ui_action":            "Action :",
        "ui_data_quality":      "🧹 Qualit\u00e9 des donn\u00e9es",
        "ui_download_report":   "📄 T\u00e9l\u00e9charger le rapport",
        "ui_clear_chat":        "🗑️ Effacer le chat",
        "ui_what_it_does":      "✨ Ce que fait cet outil",
        "ui_powered_by":        "🚀 Propuls\u00e9 par",
        "ui_step1_title":       "Importer des donn\u00e9es",
        "ui_step1_desc":        "Fichier CSV ou Excel — toute structure",
        "ui_step2_title":       "Mapper les colonnes",
        "ui_step2_desc":        "Dites-nous quelle colonne est Date et Ventes",
        "ui_step3_title":       "Obtenez les r\u00e9sultats",
        "ui_step3_desc":        "Analyse IA, graphiques, pr\u00e9visions et rapport PDF",
        "ui_peak_period":       "P\u00e9riode de pointe",
        "ui_best_group":        "Meilleur groupe",
        "ui_worst_group":       "Pire groupe",
        "ui_num_groups":        "Nombre de groupes",
        "ui_date_range":        "Plage de dates",
        "ui_metric_col":        "Indicateur",
        "ui_value_col":         "Valeur",
        "ui_check_col":         "V\u00e9rification",
        "ui_result_col":        "R\u00e9sultat",
        "ui_data_quality_rating":"Qualit\u00e9 des donn\u00e9es — {rating}",
        "ui_holiday_impact":    "🎉 Impact des cong\u00e9s",

        # ── Landing page (fr) ─────────────────────────────
        "ui_landing_title":     "📊 Agent d'analyse des ventes",
        "ui_landing_subtitle":  "Importez vos données de vente → Obtenez instantanément analyses, prévisions et rapports IA",
        "ui_step1_title":       "Importer des données",
        "ui_step1_desc":        "Fichier CSV ou Excel — n'importe quelle structure de colonnes",
        "ui_step2_title":       "Mapper les colonnes",
        "ui_step2_desc":        "Indiquez quelle colonne est la date et laquelle sont les ventes",
        "ui_step3_title":       "Obtenir les résultats",
        "ui_step3_desc":        "Analyses IA, graphiques, prévisions et rapport PDF",
        "ui_what_it_does_tool": "✨ Ce que fait cet outil",
        "ui_feature_1":         "📊 Nettoyage et validation intelligents des données",
        "ui_feature_2":         "📈 Analyse des tendances et modèles de vente",
        "ui_feature_3":         "🏪 Comparaison des groupes/magasins/succursales",
        "ui_feature_4":         "🔗 Corrélation des facteurs externes",
        "ui_powered_by_section":"🚀 Propulsé par",
        "ui_powered_1":         "🤖 Claude AI (Protocole anti-hallucination)",
        "ui_powered_2":         "📊 Prévisions Holt-Winters",
        "ui_powered_3":         "📄 Rapports PDF professionnels",
        "ui_powered_4":         "💬 Chat interactif IA",

        # ── Analysis types (fr) ───────────────────────────
        "ui_analysis_exec_summary":   "Résumé exécutif",
        "ui_analysis_perf_analysis":  "Analyse des performances",
        "ui_analysis_prob_detect":    "Détection de problèmes",
        "ui_analysis_profit_improve": "Amélioration des profits",

        # ── Pipeline status (fr) ──────────────────────────
        "ui_pipeline_status":   "🔍 État du pipeline",
        "ui_warnings_heading":  "⚠️ Avertissements :",
        "ui_errors_heading":    "❌ Erreurs :",

        # ── Data quality labels (fr) ──────────────────────
        "ui_dq_total_records":  "Total des enregistrements",
        "ui_dq_missing_values": "Valeurs manquantes",
        "ui_dq_duplicates":     "Doublons",
        "ui_dq_outliers":       "Valeurs aberrantes (IQR)",

        # ── Rating / Confidence labels (fr) ───────────────
        "ui_rating_excellent":  "Excellent",
        "ui_rating_good":       "Bon",
        "ui_rating_fair":       "Acceptable",
        "ui_rating_poor":       "Faible",
        "ui_rating_unknown":    "Inconnu",
        "ui_conf_high":         "Élevée",
        "ui_conf_medium":       "Moyenne",
        "ui_conf_low":          "Faible",

        # ── Forecast chart labels (fr) ────────────────────
        "ui_from_base":         "de la base",
        "ui_legend_bear":       "Baissier",
        "ui_legend_bull":       "Haussier",

        # ── Default column names (fr) ─────────────────────
        "ui_date_default":      "Date",
        "ui_sales_default":     "Ventes_Hebdomadaires",
        "ui_group_fallback":    "Groupe",

        # ── Misc labels (fr) ──────────────────────────────
        "ui_na":                "N/D",
        "ui_currency_sym":      "$",
        "ui_currency_suffix_b":"Md",
        "ui_currency_suffix_m":"M",
        "ui_currency_suffix_k":"K",

        # ── Status messages (fr) ──────────────────────────
        "ui_file_read_error":   "❌ Échec de la lecture du fichier : {error}",
        "ui_no_charts":         "Aucun graphique généré — vérifiez l'état du pipeline",
        "ui_no_forecast":       "Prévisions non disponibles — vérifiez l'état du pipeline",
        "ui_chat_before_analysis":"⚠️ Vous devez d'abord analyser les données avant d'utiliser le chat",
        "ui_no_dq_report":      "Rapport de qualité des données non disponible",
        "ui_no_ai_analysis":    "Analyse IA non générée — vérifiez l'état du pipeline",

        # ── Auto question ─────────────────────────────────
        "auto_question": "Analysez ces données et donnez-moi les 3 insights les plus importants avec une recommandation concrète et un impact financier estimé pour chacun. Répondez en français.",

        # ── AI Prompts (profonds + Confidence Score) ───────
        "prompts": {
            "📋 Résumé exécutif": """
Vous êtes un consultant senior en retail. Générez un résumé exécutif professionnel en français.
Utilisez UNIQUEMENT les chiffres des données fournies. N'inventez aucun chiffre.

---

## 1. 📊 Performance globale
- Indiquez le revenu total exact, le nombre de périodes et la moyenne par période
- La tendance est-elle croissante, déclinante ou stable ? Justifiez avec des chiffres
- 💰 Taux de revenu projeté pour les 12 prochaines périodes
- 🎯 Niveau de confiance : [Élevé/Moyen/Faible] — basé sur [N] périodes de données

## 2. 🏆 Meilleurs performeurs
Pour chaque top performer :
- 📊 Revenu exact et % du total
- 🔍 Pourquoi surperforment-ils ? (déduire des données)
- 💡 Recommandation : Comment répliquer leur succès ?
- 💰 Impact estimé si répliqué : $X de revenu additionnel

## 3. ⚠️ Unités sous-performantes
Pour chaque sous-performeur :
- 📊 Revenu exact et écart vs moyenne
- 🔍 Cause racine : sous-performance constante ou récente ?
- 💡 Décision : AMÉLIORER (action spécifique) ou RESTRUCTURER (si écart > 40%)
- 💰 Coût de l'inaction vs coût de l'action

## 4. 🔴 Top 3 décisions critiques MAINTENANT
Pour chaque décision :
- Le problème spécifique avec chiffres exacts
- L'action recommandée (spécifique, pas générique)
- Résultat financier attendu : $X gain ou $X économisé
- Délai : Cette semaine / Ce mois / Ce trimestre
- 🎯 Confiance : Élevée / Moyenne / Faible

## 5. 💡 Top 3 opportunités de croissance
Classées par impact potentiel :
1. Plus grande opportunité + $X gain estimé
2. Deuxième opportunité + $X gain estimé
3. Troisième opportunité + $X gain estimé

## 6. 🔮 Perspectives 12 périodes
- Fourchette de revenu attendue (scénario bas/moyen/haut)
- Principaux risques pouvant réduire le revenu
- Principales opportunités pouvant booster le revenu
- 🎯 Confiance prévision : [Élevée/Moyenne/Faible]

---
Soyez direct. Chaque affirmation doit référencer les données. Chiffres en dollars.
""",
            "📊 Analyse des performances": """
Vous êtes un analyste performance retail senior. Fournissez une analyse approfondie en français.
Utilisez UNIQUEMENT les chiffres des données fournies.

---

## 1. 📈 Analyse de tendance
- Trajectoire exacte : croissance X% / déclin X% / stable
- Identifiez 3 points de retournement majeurs avec dates et impact en $
- Quelle est la cause de chaque retournement ?
- 🎯 Confiance tendance : [Élevée/Moyenne/Faible] — basé sur [N] périodes

## 2. 🏪 Classement des unités
- 🟢 TOP TIER (20% supérieurs) : chacun avec revenu et facteur de succès
- 🟡 MID TIER (60% du milieu) : lesquels ont un potentiel de croissance ? Estimez $X
- 🔴 BOTTOM TIER (20% inférieurs) : déclin récent ou chronique ?
- 💰 Insight Pareto : quel % d'unités génère 80% du revenu ?

## 3. 📅 Saisonnalité et patterns temporels
- Meilleures périodes : dates exactes et revenus
- Pires périodes : dates exactes et revenus
- Y a-t-il un pattern hebdomadaire/mensuel/trimestriel constant ?
- 💡 Quand faut-il préparer stock et personnel supplémentaires ?
- 💰 Opportunité si les pics sont capitalisés : $X estimé

## 4. 🔗 Impact des facteurs externes
Pour chaque facteur corrélé :
- Force et direction de la corrélation
- Impact financier estimé par unité de changement
- 💡 Action spécifique pour exploiter ou atténuer
- 🎯 Confiance : [Élevée/Moyenne/Faible]

## 5. 📊 Tableau de bord KPI
| KPI | Valeur | vs Moyenne | Note |
|-----|--------|-----------|------|
| Croissance | X% | +/- X% | 🟢/🟡/🔴 |
| Pic vs Creux | $X vs $X | ratio | 🟢/🟡/🔴 |
| Consistance | X% | | 🟢/🟡/🔴 |

---
Chaque chiffre doit venir des données. Soyez précis.
""",
            "🔴 Détection des problèmes": """
Vous êtes un spécialiste du redressement d'entreprises. Identifiez tous les problèmes en français.
Utilisez UNIQUEMENT les chiffres des données fournies.

---

## 1. 🚨 CRITIQUE — Action immédiate (Cette semaine)
Pour chaque problème critique :
- 📊 Chiffres exacts : revenu, taux de déclin, unités affectées
- 🔍 Cause racine : qu'est-ce qui cause vraiment cela ?
- 💸 Coût du retard : chaque semaine d'inaction coûte environ $X
- 🛠️ Solution exacte : pas "améliorer le marketing" mais action très spécifique
- ⏰ Délai : agir dans [X jours]
- 🎯 Confiance : [Élevée/Moyenne/Faible]

## 2. ⚠️ SIGNAUX D'ALARME — Surveiller (Ce mois)
Pour chaque alerte :
- 📊 Trajectoire actuelle et où elle mène dans 4 semaines
- 🔍 Indicateurs précoces dans les données
- 💰 Revenu à risque : $X
- 💡 Action préventive spécifique maintenant
- 🎯 Confiance : [Élevée/Moyenne/Faible]

## 3. 📉 Sous-performance chronique
- Durée de la sous-performance
- Revenu perdu vs moyenne : $X
- La reprise est-elle réaliste ? Preuve dans les données
- 💡 Verdict : Investir / Restructurer / Fermer
- 💰 Impact financier de chaque option

## 4. 🔗 Facteurs de risque cachés
- Quels facteurs corrèlent négativement avec les ventes ?
- Impact estimé si le facteur se dégrade de 10%
- 💡 Stratégie de couverture pour réduire cette dépendance

## 5. 🛠️ Liste de priorités
Classée par urgence × impact financier :
1. Corriger [X] → économise/gagne $X → faire avant [date]
2. Corriger [Y] → économise/gagne $X → faire avant [date]
3. Corriger [Z] → économise/gagne $X → faire avant [date]

---
Soyez direct. Chaque problème a besoin d'un prix et d'une solution.
""",
            "💡 Suggestions d'amélioration des profits": """
Vous êtes un spécialiste de l'optimisation des revenus. Plan concret en français.
Utilisez UNIQUEMENT les chiffres des données fournies.

---

## 1. 💰 GAINS RAPIDES — Cette semaine (0-30 jours)
Pour chaque gain rapide :
- 📊 Opportunité identifiée dans les données (chiffres exacts)
- 🛠️ Action spécifique : pas "augmenter les ventes" mais étape très précise
- 💰 Gain attendu : $X (estimation conservatrice)
- ⚡ Effort requis : Faible / Moyen
- 🎯 Confiance : [Élevée/Moyenne/Faible]

## 2. 📈 STRATÉGIE MOYEN TERME (1-3 mois)
Pour chaque stratégie :
- 📊 Preuve dans les données soutenant cette opportunité
- 🛠️ Étapes d'implémentation spécifiques
- 💰 Impact revenu : $X gain sur 3 mois
- ⚠️ Risque : qu'est-ce qui pourrait mal tourner ?
- 🎯 Confiance : [Élevée/Moyenne/Faible]

## 3. 🌟 OPPORTUNITÉS À FORT IMPACT
Les 3 plus grandes sources de revenus inexploitées :
1. **Opportunité** : [description spécifique]
   - Preuve : [chiffres exacts]
   - Potentiel annuel : $X
   - Ce qu'il faut pour la saisir

2. **Opportunité** : [description spécifique]
   - Preuve : [chiffres]
   - Potentiel : $X annuel

3. **Opportunité** : [description spécifique]
   - Preuve : [chiffres]
   - Potentiel : $X annuel

## 4. 🗑️ ARRÊTEZ — Destructeurs de valeur
- Ce qu'il faut arrêter : unité ou activité spécifique
- Coût/perte actuel : $X par période
- Meilleure alternative
- Gain net de l'arrêt : $X

## 5. 💼 PROJECTION 12 PÉRIODES
Si toutes les recommandations sont implémentées :
- Scénario conservateur : +$X (augmentation X%)
- Scénario de base : +$X (augmentation X%)
- Scénario optimiste : +$X (augmentation X%)
- 🎯 Confiance projection : [Élevée/Moyenne/Faible]
- Hypothèse clé : [variable principale]

---
Chaque suggestion spécifique, numérotée et financièrement fondée.
""",
        },
    },
}


def get_text(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))


def get_translations(lang: str) -> dict:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])