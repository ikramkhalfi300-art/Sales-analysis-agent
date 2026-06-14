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