# src/translations.py
# كل نصوص الـ UI بثلاث لغات

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
        "monthly_sales":    "📅 Monthly Sales",
        "sales_by":         "🏪 Sales by",
        "correlation":      "🔗 Correlation with Sales",
        "period_avg":       "4-Period Avg",

        # ── Tab 3 ─────────────────────────────────────────
        "forecast_title":   "🔮 Sales Forecast - Next 12 Weeks",
        "next_4":           "Next 4 Weeks",
        "next_8":           "Next 8 Weeks",
        "next_12":          "Next 12 Weeks",
        "historical":       "Historical",
        "forecast_label":   "Forecast",
        "peak_info":        "📅 Peak week:",

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
        "feature2": "- 🔮 12-week forecast\n- 🤖 AI-powered insights\n- 📊 Performance analysis\n- 🔴 Problem detection & profit tips",

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
        "pdf_peak_week":    "Peak Week",
        "pdf_peak_sales":   "Peak Sales",
        "pdf_ai_section":   "🤖 AI Analysis",

        # ── AI Prompts ────────────────────────────────────
        "auto_question": "Analyze this data and give me the top 3 insights with one actionable recommendation each.",
        "prompts": {
            "📋 Executive Summary": """
Generate a professional Executive Summary:

## 1. 📊 Overall Performance
How is the business doing overall? Growth or decline?

## 2. 🏆 Top Performers
Which stores/branches are excelling and why?

## 3. ⚠️ Underperforming Units
Which stores are struggling? What are the likely causes?

## 4. 🔴 Critical Decisions Required
- IMPROVE: specific action to take
- CLOSE: if numbers suggest closure is better

## 5. 💡 Top 3 Actionable Recommendations
Ranked by potential revenue impact.

## 6. 🔮 Outlook
What should management expect next quarter?

Be direct, specific with numbers, and actionable.
""",
            "📊 Performance Analysis": """
Provide a detailed Performance Analysis:

## 1. 📈 Sales Trend Analysis
Describe the overall trajectory. Growing, declining, or flat? Key turning points?

## 2. 🏪 Store/Branch Breakdown
Rank all units. Highlight top 3, bottom 3, and highest growth potential.

## 3. 📅 Seasonal & Time Patterns
Peak periods, slow seasons, weekly patterns. How to prepare?

## 4. 📊 Key Performance Indicators
Revenue per period, growth rate, consistency. Be specific with numbers.
""",
            "🔴 Problem Detection": """
Identify all business problems:

## 1. 🚨 Critical Issues (Immediate Action Required)
Problems needing fixing this week. Specific numbers and affected units.

## 2. ⚠️ Warning Signs
Trends that could become serious. What should management watch?

## 3. 📉 Underperformance Root Causes
Internal (operations) or external (market)? Be specific.

## 4. 🔗 Hidden Correlations
External factors hurting performance? (temperature, fuel, CPI, holidays)

## 5. 🛠️ Recommended Fixes
Specific fix for each problem with expected impact.
""",
            "💡 Profit Improvement Suggestions": """
Strategic profit improvement recommendations:

## 1. 💰 Quick Wins (0-30 Days)
Actions to increase revenue immediately. Estimate potential gain.

## 2. 📈 Medium-Term Strategy (1-3 Months)
Structural changes. Which stores/periods to focus on first?

## 3. 🌟 High-Impact Opportunities
Biggest untapped potential. Underperforming stores, underserved periods.

## 4. 🗑️ Cut or Restructure
Which activities are destroying value? Fix, restructure, or close?

## 5. 🔮 Revenue Forecast Impact
Expected revenue increase in next 12 weeks if recommendations are implemented.
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
        "monthly_sales":    "📅 المبيعات الشهرية",
        "sales_by":         "🏪 المبيعات حسب",
        "correlation":      "🔗 الارتباط بالمبيعات",
        "period_avg":       "متوسط 4 فترات",

        # ── Tab 3 ─────────────────────────────────────────
        "forecast_title":   "🔮 توقعات المبيعات - 12 أسبوع قادم",
        "next_4":           "الـ 4 أسابيع القادمة",
        "next_8":           "الـ 8 أسابيع القادمة",
        "next_12":          "الـ 12 أسبوع القادم",
        "historical":       "تاريخي",
        "forecast_label":   "التوقع",
        "peak_info":        "📅 أسبوع الذروة:",

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
        "feature2": "- 🔮 توقعات 12 أسبوع\n- 🤖 رؤى بالذكاء الاصطناعي\n- 📊 تحليل الأداء\n- 🔴 كشف المشاكل ونصائح الأرباح",

        # ── PDF ───────────────────────────────────────────
        "pdf_title":        "تقرير تحليل المبيعات",
        "pdf_generated":    "تاريخ الإنشاء",
        "pdf_key_metrics":  "📊 المؤشرات الرئيسية",
        "pdf_metric":       "المؤشر",
        "pdf_value":        "القيمة",
        "pdf_date_range":   "النطاق الزمني",
        "pdf_avg_period":   "متوسط الفترة",
        "pdf_best_period":  "أفضل فترة",
        "pdf_trend":        "📈 اتجاه المبيعات",
        "pdf_forecast":     "🔮 ملخص التوقعات",
        "pdf_period":       "الفترة",
        "pdf_expected":     "المبيعات المتوقعة",
        "pdf_peak_week":    "أسبوع الذروة",
        "pdf_peak_sales":   "مبيعات الذروة",
        "pdf_ai_section":   "🤖 تحليل الذكاء الاصطناعي",

        # ── AI Prompts ────────────────────────────────────
        "auto_question": "حلل هذه البيانات وأعطني أهم 3 insights مع توصية عملية لكل واحدة.",
        "prompts": {
            "📋 الملخص التنفيذي": """
أنشئ ملخصاً تنفيذياً احترافياً باللغة العربية:

## 1. 📊 الأداء العام
كيف حال العمل؟ نمو أم تراجع؟

## 2. 🏆 الأفضل أداءً
أي المتاجر/الفروع تتفوق ولماذا؟

## 3. ⚠️ الوحدات الضعيفة
أي المتاجر تعاني؟ ما الأسباب المحتملة؟

## 4. 🔴 قرارات عاجلة مطلوبة
- تحسين: إجراء محدد
- إغلاق: إذا كانت الأرقام تستدعي ذلك

## 5. 💡 أهم 3 توصيات قابلة للتنفيذ
مرتبة حسب الأثر المالي المتوقع.

## 6. 🔮 التوقعات
ماذا يتوقع الإدارة في الربع القادم؟

كن مباشراً ومحدداً بالأرقام وقابلاً للتنفيذ.
""",
            "📊 تحليل الأداء": """
قدم تحليل أداء تفصيلياً باللغة العربية:

## 1. 📈 تحليل اتجاه المبيعات
صف المسار العام. نمو أم تراجع أم ثبات؟ نقاط التحول الرئيسية؟

## 2. 🏪 تفصيل أداء المتاجر/الفروع
رتب كل الوحدات. أبرز أفضل 3، وأضعف 3، وأعلى إمكانية نمو.

## 3. 📅 الأنماط الموسمية والزمنية
فترات الذروة، المواسم البطيئة، الأنماط الأسبوعية. كيف نستعد؟

## 4. 📊 مؤشرات الأداء الرئيسية
الإيراد لكل فترة، معدل النمو، الاتساق. كن محدداً بالأرقام.
""",
            "🔴 اكتشاف المشاكل": """
حدد جميع مشاكل العمل باللغة العربية:

## 1. 🚨 مشاكل حرجة (تحتاج تدخل فوري)
مشاكل تحتاج حل هذا الأسبوع. أرقام محددة ووحدات متأثرة.

## 2. ⚠️ إشارات تحذيرية
اتجاهات قد تصبح خطيرة. ماذا يجب أن ترصد الإدارة؟

## 3. 📉 أسباب ضعف الأداء
داخلية (عمليات) أم خارجية (سوق)؟ كن محدداً.

## 4. 🔗 ارتباطات خفية
عوامل خارجية تؤثر سلباً؟ (درجة الحرارة، الوقود، CPI، الأعياد)

## 5. 🛠️ حلول موصى بها
حل محدد لكل مشكلة مع الأثر المتوقع.
""",
            "💡 اقتراحات تحسين الأرباح": """
توصيات استراتيجية لتحسين الأرباح باللغة العربية:

## 1. 💰 مكاسب سريعة (0-30 يوم)
إجراءات لزيادة الإيراد فوراً. قدّر الربح المحتمل.

## 2. 📈 استراتيجية متوسطة المدى (1-3 أشهر)
تغييرات هيكلية. أي المتاجر/الفترات تستحق الأولوية؟

## 3. 🌟 فرص عالية الأثر
أكبر إمكانية غير مستغلة. متاجر ضعيفة بإمكانية عالية.

## 4. 🗑️ قطع أو إعادة هيكلة
أي الأنشطة تدمر القيمة؟ أصلح، أعد هيكلة، أو أغلق؟

## 5. 🔮 الأثر على إيرادات الـ 12 أسبوع القادمة
الزيادة المتوقعة في الإيرادات إذا نُفذت التوصيات.
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
        "total_records":    "Total des enregistrements",
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
        "cleaning_report":  "🧹 Rapport de nettoyage des données",
        "data_preview":     "👀 Aperçu des données",
        "performance_by":   "🏪 Performance par",
        "generating_pdf":   "Génération du PDF...",
        "generating_ai":    "Génération de l'analyse...",

        # ── Tab 2 ─────────────────────────────────────────
        "sales_trend":      "📈 Tendance des ventes",
        "monthly_sales":    "📅 Ventes mensuelles",
        "sales_by":         "🏪 Ventes par",
        "correlation":      "🔗 Corrélation avec les ventes",
        "period_avg":       "Moyenne 4 périodes",

        # ── Tab 3 ─────────────────────────────────────────
        "forecast_title":   "🔮 Prévisions des ventes - 12 semaines",
        "next_4":           "4 prochaines semaines",
        "next_8":           "8 prochaines semaines",
        "next_12":          "12 prochaines semaines",
        "historical":       "Historique",
        "forecast_label":   "Prévision",
        "peak_info":        "📅 Semaine de pointe :",

        # ── Tab 4 ─────────────────────────────────────────
        "agent_title":      "🤖 Interroger l'Agent IA",
        "agent_caption":    "Posez des questions sur vos données en arabe, anglais ou français",
        "chat_placeholder": "Posez une question sur vos données...",
        "thinking":         "Réflexion en cours...",
        "initial_analysis": "🔍 Génération de l'analyse initiale...",

        # ── Landing ───────────────────────────────────────
        "step1": "📁 **Étape 1**\nImportez votre fichier CSV ou Excel",
        "step2": "🗂️ **Étape 2**\nSélectionnez les colonnes date et ventes",
        "step3": "🚀 **Étape 3**\nCliquez sur Analyser et explorez !",
        "what_it_does": "✨ Ce que fait cet outil :",
        "feature1": "- 📊 Nettoyage intelligent des données\n- 📈 Graphiques de tendance\n- 🏪 Comparaison des magasins\n- 🔗 Analyse des facteurs externes",
        "feature2": "- 🔮 Prévisions 12 semaines\n- 🤖 Insights par IA\n- 📊 Analyse des performances\n- 🔴 Détection des problèmes",

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
        "pdf_peak_week":    "Semaine de pointe",
        "pdf_peak_sales":   "Ventes de pointe",
        "pdf_ai_section":   "🤖 Analyse IA",

        # ── AI Prompts ────────────────────────────────────
        "auto_question": "Analysez ces données et donnez-moi les 3 insights les plus importants avec une recommandation concrète pour chacun.",
        "prompts": {
            "📋 Résumé exécutif": """
Générez un résumé exécutif professionnel en français :

## 1. 📊 Performance globale
Comment se porte l'entreprise ? Croissance ou déclin ?

## 2. 🏆 Meilleurs performeurs
Quels magasins/branches excellent et pourquoi ?

## 3. ⚠️ Unités sous-performantes
Quels magasins sont en difficulté ? Causes probables ?

## 4. 🔴 Décisions critiques requises
- AMÉLIORER : action spécifique à prendre
- FERMER : si les chiffres suggèrent une fermeture

## 5. 💡 Top 3 recommandations actionnables
Classées par impact sur le chiffre d'affaires.

## 6. 🔮 Perspectives
Que doit anticiper la direction pour le prochain trimestre ?

Soyez direct, précis avec les chiffres et actionnable.
""",
            "📊 Analyse des performances": """
Fournissez une analyse détaillée des performances en français :

## 1. 📈 Analyse de la tendance des ventes
Décrivez la trajectoire globale. Croissance, déclin ou stagnation ?

## 2. 🏪 Répartition par magasin/branche
Classez toutes les unités. Mettez en avant les 3 meilleurs, 3 pires, et le plus grand potentiel.

## 3. 📅 Patterns saisonniers et temporels
Périodes de pointe, saisons creuses, patterns hebdomadaires. Comment se préparer ?

## 4. 📊 Indicateurs clés de performance
Revenus par période, taux de croissance, cohérence. Soyez précis avec les chiffres.
""",
            "🔴 Détection des problèmes": """
Identifiez tous les problèmes commerciaux en français :

## 1. 🚨 Problèmes critiques (Action immédiate requise)
Problèmes à régler cette semaine. Chiffres précis et unités concernées.

## 2. ⚠️ Signaux d'alarme
Tendances pouvant devenir sérieuses. Que doit surveiller la direction ?

## 3. 📉 Causes de sous-performance
Interne (opérations) ou externe (marché) ? Soyez précis.

## 4. 🔗 Corrélations cachées
Facteurs externes nuisant aux performances ? (température, carburant, CPI, jours fériés)

## 5. 🛠️ Corrections recommandées
Correction spécifique pour chaque problème avec impact attendu.
""",
            "💡 Suggestions d'amélioration des profits": """
Recommandations stratégiques pour améliorer les profits en français :

## 1. 💰 Gains rapides (0-30 jours)
Actions pour augmenter les revenus immédiatement. Estimez le gain potentiel.

## 2. 📈 Stratégie moyen terme (1-3 mois)
Changements structurels. Quels magasins/périodes prioriser ?

## 3. 🌟 Opportunités à fort impact
Plus grand potentiel inexploité. Magasins sous-performants à fort potentiel.

## 4. 🗑️ Couper ou restructurer
Quelles activités détruisent de la valeur ? Corriger, restructurer ou fermer ?

## 5. 🔮 Impact sur les revenus des 12 prochaines semaines
Augmentation attendue si les recommandations sont mises en œuvre.
""",
        },
    },
}


def get_text(lang: str, key: str) -> str:
    """استرجاع نص بلغة محددة مع fallback للإنجليزية"""
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))


def get_translations(lang: str) -> dict:
    """استرجاع كل ترجمات لغة محددة"""
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])