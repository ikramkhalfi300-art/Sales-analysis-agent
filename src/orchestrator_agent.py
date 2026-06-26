"""
orchestrator_agent.py — المدير التنفيذي للنظام
================================================
المسؤولية الوحيدة: تنسيق العمل بين جميع الـ agents
لا يحلل، لا يحسب، لا يرسم — فقط يوجّه ويتحقق

Pipeline:
    1. DataAgent       → تحميل وتنظيف البيانات
    2. AnalysisAgent   → حساب المقاييس الإحصائية
    3. ForecastAgent   → التوقعات المستقبلية
    4. VisualAgent     → إنشاء الرسوم البيانية
    5. ReportAgent     → توليد التقرير النهائي

الـ SharedContext هو الذاكرة المشتركة بين كل الـ agents
"""

import os
import uuid
import traceback
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

import streamlit as st
from anthropic import Anthropic


# ════════════════════════════════════════════════
# 1. CLIENT SETUP
# ════════════════════════════════════════════════
def _get_client() -> Anthropic:
    api_key = None
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        pass
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("❌ ANTHROPIC_API_KEY غير موجود في secrets أو environment variables")
    return Anthropic(api_key=api_key)


# ════════════════════════════════════════════════
# 2. SHARED CONTEXT — الذاكرة المشتركة بين الـ agents
# ════════════════════════════════════════════════
@dataclass
class AgentStatus:
    """حالة كل agent بعد التنفيذ"""
    name: str
    success: bool
    duration_sec: float = 0.0
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class SharedContext:
    """
    الحاوية المركزية لكل البيانات التي تنتقل بين الـ agents.
    كل agent يقرأ منها ويكتب فيها — لا يوجد تمرير مباشر بين agents.
    """
    # ── معرّف الجلسة ────────────────────────────
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # ── إعدادات المستخدم ─────────────────────────
    lang: str = "en"
    company_name: str = ""
    date_col: str = "Date"
    sales_col: str = "Weekly_Sales"
    forecast_weeks: int = 12
    has_qa_errors: bool = False

    # ── مخرجات DataAgent ────────────────────────
    df: Any = None                    # DataFrame نظيف
    data_quality_report: dict = field(default_factory=dict)
    summary: dict = field(default_factory=dict)
    group_col: Optional[str] = None

    # ── مخرجات AnalysisAgent ────────────────────
    store_df: Any = None              # DataFrame أداء المجموعات
    monthly_df: Any = None            # DataFrame شهري
    yearly_df: Any = None             # DataFrame سنوي
    holiday_df: Any = None            # DataFrame مقارنة الأعياد
    corr_series: Any = None           # Series الارتباطات
    kpi_data: dict = field(default_factory=dict)

    # ── مخرجات ForecastAgent ────────────────────
    forecast_df: Any = None           # DataFrame التوقعات الكاملة
    prophet_data: Any = None          # البيانات التاريخية المجمّعة
    forecast_summary: dict = field(default_factory=dict)

    # ── مخرجات VisualAgent ──────────────────────
    chart_paths: List[str] = field(default_factory=list)

    # ── مخرجات ReportAgent ──────────────────────
    ai_analysis_text: Optional[str] = None
    pdf_bytes: Optional[bytes] = None
    pdf_path: Optional[str] = None

    # ── حالة Pipeline ───────────────────────────
    agent_statuses: List[AgentStatus] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    pipeline_complete: bool = False

    def add_error(self, msg: str):
        self.errors.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def add_warning(self, msg: str):
        self.warnings.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def record_agent(self, status: AgentStatus):
        self.agent_statuses.append(status)

    def is_healthy(self) -> bool:
        """هل الـ pipeline يعمل بدون أخطاء فادحة؟"""
        return len(self.errors) == 0

    def get_pipeline_report(self) -> str:
        """تقرير نصي عن حالة كل agent"""
        lines = [f"Pipeline Report — Session {self.session_id}"]
        lines.append("=" * 50)
        for s in self.agent_statuses:
            icon = "✅" if s.success else "❌"
            lines.append(f"{icon} {s.name:<25} ({s.duration_sec:.2f}s)")
            if s.error:
                lines.append(f"   └─ ERROR: {s.error}")
            for w in s.warnings:
                lines.append(f"   └─ ⚠️  {w}")
        if self.errors:
            lines.append("\nFATAL ERRORS:")
            for e in self.errors:
                lines.append(f"  • {e}")
        if self.warnings:
            lines.append("\nWARNINGS:")
            for w in self.warnings:
                lines.append(f"  • {w}")
        lines.append(f"\nStatus: {'✅ COMPLETE' if self.pipeline_complete else '❌ INCOMPLETE'}")
        return "\n".join(lines)


# ════════════════════════════════════════════════
# 3. BASE AGENT — الكلاس الأساسي لكل agent
# ════════════════════════════════════════════════
class BaseAgent:
    """
    كل agent يرث من هذا الكلاس.
    يوفر: logging، timing، error handling موحد.
    """
    name: str = "BaseAgent"

    def run(self, ctx: SharedContext) -> SharedContext:
        """
        الطريقة الرئيسية — يستدعيها الـ Orchestrator فقط.
        لا تستدع agent من agent آخر مباشرة.
        """
        import time
        start = time.time()
        status = AgentStatus(name=self.name, success=False)
        try:
            ctx = self._execute(ctx)
            status.success = True
            status.warnings = self._collect_warnings(ctx)
        except Exception as e:
            error_msg = f"{self.name} failed: {str(e)}"
            status.error = error_msg
            ctx.add_error(error_msg)
            # Log full traceback for debugging
            if os.getenv("DEBUG_AGENTS"):
                print(f"\n{'='*60}")
                print(f"DEBUG — {self.name} TRACEBACK:")
                print(traceback.format_exc())
                print('='*60)
        finally:
            status.duration_sec = round(time.time() - start, 2)
            ctx.record_agent(status)
        return ctx

    def _execute(self, ctx: SharedContext) -> SharedContext:
        """كل agent يـ override هذه الطريقة فقط"""
        raise NotImplementedError(f"{self.name}._execute() غير مُنفَّذ")

    def _collect_warnings(self, ctx: SharedContext) -> List[str]:
        """اجمع آخر تحذيرات من الـ context بعد التنفيذ"""
        return []


# ════════════════════════════════════════════════
# 4. DATA AGENT
# ════════════════════════════════════════════════
class DataAgent(BaseAgent):
    """
    المسؤولية: تحميل البيانات وتنظيفها فقط.
    Input:  ملف CSV/Excel أو DataFrame مباشر
    Output: ctx.df نظيف + ctx.summary + ctx.data_quality_report
    """
    name = "DataAgent"

    def __init__(self, path: Optional[str] = None, dataframe=None):
        self.path = path
        self.dataframe = dataframe

    def _execute(self, ctx: SharedContext) -> SharedContext:
        from data_agent import load_data, get_summary

        # ── تحميل وتنظيف ────────────────────────
        df, report = load_data(path=self.path, dataframe=self.dataframe)
        ctx.df = df
        ctx.data_quality_report = report if isinstance(report, dict) else {"raw": str(report)}

        # ── التحقق من الأعمدة الأساسية ──────────
        if ctx.date_col not in df.columns:
            raise ValueError(
                f"عمود التاريخ '{ctx.date_col}' غير موجود. "
                f"الأعمدة المتاحة: {list(df.columns)}"
            )
        if ctx.sales_col not in df.columns:
            raise ValueError(
                f"عمود المبيعات '{ctx.sales_col}' غير موجود. "
                f"الأعمدة المتاحة: {list(df.columns)}"
            )

        # ── التحقق من الحد الأدنى للبيانات ──────
        if len(df) < 3:
            raise ValueError(
                f"البيانات غير كافية: {len(df)} صف فقط. "
                "الحد الأدنى المطلوب 3 صفوف."
            )

        # ── ملخص البيانات ────────────────────────
        ctx.summary = get_summary(df, ctx.date_col, ctx.sales_col)
        ctx.group_col = ctx.summary.get('group_col', None)

        # ── تحذيرات جودة البيانات ────────────────
        missing_pct = ctx.data_quality_report.get('missing_pct', 0)
        if missing_pct > 5:
            ctx.add_warning(
                f"DataAgent: {missing_pct:.1f}% من البيانات مفقودة — "
                "النتائج قد تكون غير دقيقة"
            )
        if ctx.data_quality_report.get('n_duplicates', 0) > 0:
            ctx.add_warning(
                f"DataAgent: {ctx.data_quality_report['n_duplicates']} صف مكرر — "
                "تم استبعادها تلقائياً"
            )

        return ctx

    def _collect_warnings(self, ctx: SharedContext) -> List[str]:
        return [w for w in ctx.warnings if w.startswith("[") and "DataAgent" in w]


# ════════════════════════════════════════════════
# 5. ANALYSIS AGENT
# ════════════════════════════════════════════════
class AnalysisAgent(BaseAgent):
    """
    المسؤولية: الحسابات الإحصائية فقط — لا توقعات، لا رسوم.
    Input:  ctx.df + ctx.date_col + ctx.sales_col + ctx.group_col
    Output: ctx.store_df + ctx.monthly_df + ctx.holiday_df +
            ctx.corr_series + ctx.kpi_data
    """
    name = "AnalysisAgent"

    def _execute(self, ctx: SharedContext) -> SharedContext:
        # ── التحقق من المدخلات ───────────────────
        if ctx.df is None:
            raise ValueError("AnalysisAgent: البيانات غير موجودة — DataAgent لم يعمل بنجاح")

        from analyzer_agent import (
            sales_by_store, monthly_sales, yearly_sales,
            holiday_vs_normal, correlation_analysis
        )

        df       = ctx.df
        date_col = ctx.date_col
        sales_col = ctx.sales_col
        group_col = ctx.group_col

        # ── أداء المجموعات (متاجر/فروع/...) ─────
        if group_col and group_col in df.columns:
            ctx.store_df = sales_by_store(df, group_col, sales_col)
        else:
            ctx.store_df = None
            ctx.add_warning("AnalysisAgent: لم يُعثر على عمود تجميع — تحليل المجموعات غير متاح")

        # ── التحليل الزمني ───────────────────────
        ctx.monthly_df = monthly_sales(df, date_col, sales_col)
        ctx.yearly_df  = yearly_sales(df, date_col, sales_col)

        # ── مقارنة الأعياد ───────────────────────
        ctx.holiday_df = holiday_vs_normal(df, sales_col)

        # ── الارتباطات ───────────────────────────
        ctx.corr_series = correlation_analysis(df, sales_col)

        # ── KPI متقدمة ───────────────────────────
        ctx.kpi_data = self._compute_kpis(df, date_col, sales_col, ctx.monthly_df)

        return ctx

    def _compute_kpis(self, df, date_col, sales_col, monthly_df) -> dict:
        """حساب مؤشرات الأداء المتقدمة"""
        import numpy as np
        import pandas as pd

        kpi = {}
        try:
            sales = df[sales_col].dropna()

            # معدل النمو شهر-على-شهر
            if monthly_df is not None and len(monthly_df) >= 2:
                vals = monthly_df['total'].tolist()
                if vals[-2] > 0:
                    kpi['mom_growth'] = round((vals[-1] - vals[-2]) / vals[-2] * 100, 2)

                # زخم النمو (فرق في معدل النمو)
                if len(vals) >= 3 and vals[-3] > 0 and vals[-2] > 0:
                    prev_growth = (vals[-2] - vals[-3]) / vals[-3] * 100
                    curr_growth = kpi.get('mom_growth', 0)
                    kpi['growth_momentum'] = round(curr_growth, 2)
                    kpi['momentum_delta']  = round(curr_growth - prev_growth, 2)

                # أفضل وأسوأ فترة
                kpi['best_period']        = str(monthly_df.loc[monthly_df['total'].idxmax(), 'month'])
                kpi['worst_period']       = str(monthly_df.loc[monthly_df['total'].idxmin(), 'month'])
                kpi['best_period_value']  = float(monthly_df['total'].max())
                kpi['worst_period_value'] = float(monthly_df['total'].min())
                kpi['avg_period_value']   = float(monthly_df['total'].mean())

            # معامل التغيير (CV)
            mean_val = float(sales.mean())
            std_val  = float(sales.std())
            kpi['cv_pct'] = round(std_val / mean_val * 100, 2) if mean_val > 0 else 0

        except Exception as e:
            kpi['computation_error'] = str(e)

        return kpi


# ════════════════════════════════════════════════
# 6. FORECAST AGENT
# ════════════════════════════════════════════════
class ForecastAgent(BaseAgent):
    """
    المسؤولية: توقعات المبيعات فقط.
    Input:  ctx.df + ctx.date_col + ctx.sales_col + ctx.forecast_weeks
    Output: ctx.forecast_df + ctx.prophet_data + ctx.forecast_summary
    """
    name = "ForecastAgent"

    def _execute(self, ctx: SharedContext) -> SharedContext:
        if ctx.df is None:
            raise ValueError("ForecastAgent: البيانات غير موجودة")

        from forecaster_agent import train_and_forecast, get_forecast_summary

        # ── تدريب النموذج والتوقع ────────────────
        forecast_df, historical = train_and_forecast(
            df           = ctx.df,
            weeks        = ctx.forecast_weeks,
            date_col     = ctx.date_col,
            sales_col    = ctx.sales_col,
            has_qa_errors= ctx.has_qa_errors,
        )

        ctx.forecast_df   = forecast_df
        ctx.prophet_data  = historical

        # ── ملخص التوقعات ────────────────────────
        group_col_avg = None
        if ctx.store_df is not None and len(ctx.store_df) > 0:
            try:
                group_col_avg = float(
                    ctx.store_df.loc[ctx.store_df['total'].idxmax(), 'avg_weekly']
                )
            except Exception:
                pass

        ctx.forecast_summary = get_forecast_summary(
            forecast      = forecast_df,
            prophet_data  = historical,
            group_col_avg = group_col_avg,
        )

        # ── تحذيرات التوقع ───────────────────────
        sanity = ctx.forecast_summary.get('sanity_check', {})
        if not sanity.get('passed', True):
            for w in sanity.get('warnings', []):
                ctx.add_warning(f"ForecastAgent: {w}")

        conf = ctx.forecast_summary.get('confidence_level', 'Medium')
        if conf == 'Low':
            ctx.add_warning(
                "ForecastAgent: ثقة التوقع منخفضة — "
                "البيانات غير كافية لتوقع موثوق"
            )

        return ctx


# ════════════════════════════════════════════════
# 7. VISUAL AGENT
# ════════════════════════════════════════════════
class VisualAgent(BaseAgent):
    """
    المسؤولية: إنشاء الرسوم البيانية وحفظها فقط.
    Input:  ctx.df + ctx.store_df + ctx.monthly_df + ctx.forecast_df
    Output: ctx.chart_paths (قائمة بمسارات الملفات)
    """
    name = "VisualAgent"

    def _execute(self, ctx: SharedContext) -> SharedContext:
        if ctx.df is None:
            raise ValueError("VisualAgent: البيانات غير موجودة")

        from visualizer_agent import (
            plot_sales_trend, plot_store_comparison,
            plot_monthly_trend, plot_holiday_impact,
            plot_correlations, plot_forecast
        )
        import os
        os.makedirs('outputs', exist_ok=True)

        charts = []

        # ── 1. منحنى المبيعات ────────────────────
        try:
            # visualizer_agent يحفظ في outputs/ مباشرة
            # نمرر البيانات الصحيحة بناءً على الأعمدة المتاحة
            df_viz = ctx.df.copy()
            # توحيد أسماء الأعمدة للـ visualizer
            df_viz = df_viz.rename(columns={
                ctx.date_col:  'Date',
                ctx.sales_col: 'Weekly_Sales'
            })
            plot_sales_trend(df_viz)
            if os.path.exists('outputs/01_sales_trend.png'):
                charts.append('outputs/01_sales_trend.png')
        except Exception as e:
            ctx.add_warning(f"VisualAgent: فشل رسم منحنى المبيعات — {e}")

        # ── 2. مقارنة المجموعات ──────────────────
        if ctx.store_df is not None:
            try:
                store_viz = ctx.store_df.copy()
                if ctx.group_col and ctx.group_col != 'Store':
                    store_viz = store_viz.rename(columns={ctx.group_col: 'Store'})
                plot_store_comparison(store_viz)
                if os.path.exists('outputs/02_store_comparison.png'):
                    charts.append('outputs/02_store_comparison.png')
            except Exception as e:
                ctx.add_warning(f"VisualAgent: فشل رسم مقارنة المجموعات — {e}")

        # ── 3. المبيعات الشهرية ──────────────────
        if ctx.monthly_df is not None and len(ctx.monthly_df) > 0:
            try:
                plot_monthly_trend(ctx.monthly_df)
                if os.path.exists('outputs/03_monthly_trend.png'):
                    charts.append('outputs/03_monthly_trend.png')
            except Exception as e:
                ctx.add_warning(f"VisualAgent: فشل رسم المبيعات الشهرية — {e}")

        # ── 4. تأثير الأعياد ─────────────────────
        if ctx.holiday_df is not None:
            try:
                plot_holiday_impact(ctx.holiday_df)
                if os.path.exists('outputs/04_holiday_impact.png'):
                    charts.append('outputs/04_holiday_impact.png')
            except Exception as e:
                ctx.add_warning(f"VisualAgent: فشل رسم تأثير الأعياد — {e}")

        # ── 5. الارتباطات ────────────────────────
        if ctx.corr_series is not None and len(ctx.corr_series) > 0:
            try:
                plot_correlations(ctx.corr_series)
                if os.path.exists('outputs/05_correlations.png'):
                    charts.append('outputs/05_correlations.png')
            except Exception as e:
                ctx.add_warning(f"VisualAgent: فشل رسم الارتباطات — {e}")

        # ── 6. التوقعات ──────────────────────────
        if ctx.forecast_df is not None and ctx.prophet_data is not None:
            try:
                plot_forecast(ctx.forecast_df, ctx.prophet_data)
                if os.path.exists('outputs/06_forecast.png'):
                    charts.append('outputs/06_forecast.png')
            except Exception as e:
                ctx.add_warning(f"VisualAgent: فشل رسم التوقعات — {e}")

        ctx.chart_paths = charts

        if not charts:
            ctx.add_warning("VisualAgent: لم يتم إنشاء أي رسم بياني")

        return ctx


# ════════════════════════════════════════════════
# 8. AI ANALYSIS AGENT
# ════════════════════════════════════════════════
class AIAnalysisAgent(BaseAgent):
    """
    المسؤولية: توليد النص التحليلي بالـ LLM فقط.
    Input:  ctx كامل (بعد Analysis + Forecast)
    Output: ctx.ai_analysis_text

    هذا الـ agent يعمل بـ Anti-Hallucination Protocol صارم:
    - يحصل فقط على الأرقام المحسوبة من الـ agents السابقة
    - لا يستطيع اختراع أرقام لأن الـ prompt لا يحتوي إلا على المحسوب فعلاً
    """
    name = "AIAnalysisAgent"

    def __init__(self, analysis_type: str = "executive_summary"):
        self.analysis_type = analysis_type
        self.client = _get_client()

    def _execute(self, ctx: SharedContext) -> SharedContext:
        system_prompt = self._build_system_prompt(ctx)
        user_prompt   = self._build_user_prompt(ctx)

        response = self.client.messages.create(
            model      = "claude-sonnet-4-6",
            max_tokens = 4096,
            system     = system_prompt,
            messages   = [{"role": "user", "content": user_prompt}]
        )
        ctx.ai_analysis_text = response.content[0].text
        return ctx

    def _build_system_prompt(self, ctx: SharedContext) -> str:
        """
        بناء System Prompt محكم — يمنع الهلوسة تماماً.
        الـ agent يعرف فقط ما في هذا الـ prompt.
        """
        lang_map = {
            "en": "Always respond in English.",
            "ar": "يجب أن تجيب دائماً باللغة العربية الفصحى.",
            "fr": "Répondez toujours en français.",
        }
        lang_instr   = lang_map.get(ctx.lang, lang_map["en"])
        company_line = (f"Client: {ctx.company_name}" if ctx.company_name
                        else "Client: [Not specified]")

        summary  = ctx.summary or {}
        fc       = ctx.forecast_summary or {}
        kpi      = ctx.kpi_data or {}

        # ── استخراج أرقام التوقعات ───────────────
        fc_conf     = fc.get('confidence_level', 'Medium')
        fc_model    = fc.get('model_type', 'unknown')
        fc_cv       = fc.get('cv_pct', 0)
        next_4      = fc.get('next_4_weeks',  0)
        next_12     = fc.get('next_12_weeks', 0)
        bear_12     = fc.get('bear_12_weeks', next_12 * 0.75)
        bull_12     = fc.get('bull_12_weeks', next_12 * 1.25)
        bear_spread = fc.get('bear_spread_pct', -25.0)
        bull_spread = fc.get('bull_spread_pct',  25.0)
        peak_wk     = fc.get('peak_week', 'N/A')
        peak_val    = fc.get('peak_expected_sales', 0)
        volatility  = fc.get('volatility', {}).get('level', 'Unknown')

        sanity         = fc.get('sanity_check', {'passed': True, 'warnings': []})
        sanity_passed  = sanity.get('passed', True)
        sanity_warns   = sanity.get('warnings', [])

        # ── مستوى موثوقية التوقع ─────────────────
        if not sanity_passed:
            fc_reliability = "⚠️ LOW — SANITY CHECK FAILED"
            fc_instruction = (
                "CRITICAL: أرقام التوقع فشلت في اختبار المنطقية. "
                "اذكر صراحةً أنها تقديرات اتجاهية فقط وليست توقعات موثوقة."
            )
        elif fc_conf == 'Low':
            fc_reliability = "LOW"
            fc_instruction = "أضف دائماً: '[ثقة منخفضة — للتوجيه فقط]' عند ذكر أرقام التوقع."
        elif fc_conf == 'Medium':
            fc_reliability = "MEDIUM"
            fc_instruction = "اذكر دائماً نطاق Bear/Base/Bull وليس الرقم الأساسي فقط."
        else:
            fc_reliability = "HIGH"
            fc_instruction = "أرقام التوقع موثوقة للتخطيط. اذكر النطاق عند مناقشة الميزانيات."

        # ── بناء قسم أداء المجموعات ──────────────
        group_section = "N/A — لا يوجد عمود تجميع"
        if ctx.store_df is not None and ctx.group_col:
            top5    = ctx.store_df.head(5).to_string(index=False)
            bottom5 = ctx.store_df.tail(5).to_string(index=False)
            group_section = f"TOP 5:\n{top5}\n\nBOTTOM 5:\n{bottom5}"

        # ── قسم الارتباطات ───────────────────────
        corr_section = "N/A"
        if ctx.corr_series is not None and len(ctx.corr_series) > 0:
            corr_section = ctx.corr_series.to_string()

        # ── قسم الأعياد ──────────────────────────
        holiday_section = "N/A"
        if ctx.holiday_df is not None:
            holiday_section = ctx.holiday_df.to_string(index=False)

        # ── KPI Section ───────────────────────────
        mom      = kpi.get('mom_growth')
        momentum = kpi.get('growth_momentum')
        cv_kpi   = kpi.get('cv_pct', 0)

        kpi_lines = []
        if mom is not None:
            kpi_lines.append(f"- Period-over-Period Growth: {mom:+.1f}%")
        if momentum is not None:
            kpi_lines.append(f"- Growth Momentum: {momentum:+.1f}%/period")
        if cv_kpi:
            level = 'EXTREME' if cv_kpi > 70 else 'HIGH' if cv_kpi > 40 else 'MODERATE' if cv_kpi > 20 else 'LOW'
            kpi_lines.append(f"- Revenue Volatility (CV): {cv_kpi:.1f}% → {level}")
        if kpi.get('best_period'):
            kpi_lines.append(f"- Best Period: {kpi['best_period']} (${kpi.get('best_period_value',0):,.0f})")
        if kpi.get('worst_period'):
            kpi_lines.append(f"- Worst Period: {kpi['worst_period']} (${kpi.get('worst_period_value',0):,.0f})")
        kpi_section = "\n".join(kpi_lines) if kpi_lines else "N/A"

        # ── Sanity Warnings ───────────────────────
        sanity_block = ""
        if sanity_warns:
            sanity_block = "\n⚠️ FORECAST SANITY WARNINGS:\n"
            for w in sanity_warns:
                sanity_block += f"  - {w}\n"

        return f"""You are a senior business intelligence analyst with 15+ years experience.
{lang_instr}
{company_line}

{'='*60}
ANTI-HALLUCINATION PROTOCOL — MANDATORY
{'='*60}
1. استخدم فقط الأرقام الموجودة في هذا الـ prompt — لا تخترع أي رقم.
2. إذا لم يكن الرقم في الـ prompt → قل "البيانات غير متاحة".
3. التقديرات المحسوبة منك → ضع [ESTIMATED] أمامها.
4. الأرقام من البيانات الفعلية → يمكنك تسميتها [DATA].
5. لا تذكر نسب تحسين إلا إذا حسبتها من الأرقام الموجودة هنا.
6. موثوقية التوقع: {fc_reliability}
   {fc_instruction}
7. الارتباط ≠ سببية — أضف هذا التحذير دائماً عند مناقشة الارتباطات.
8. لا تذكر أسماء منافسين أو أحداث خارجية غير موجودة في البيانات.
{'='*60}

=== بيانات الأداء الفعلية ===
- إجمالي السجلات:     {summary.get('total_records', 'N/A'):,}
- النطاق الزمني:      {summary.get('date_range', 'N/A')}
- إجمالي الإيراد:     ${summary.get('total_sales', 0):,.2f}  [DATA]
- متوسط الفترة:       ${summary.get('avg_weekly_sales', 0):,.2f}  [DATA]
- أعلى فترة:          ${summary.get('max_single_week', 0):,.2f}  [DATA]
- أدنى فترة:          ${summary.get('min_single_week', 0):,.2f}  [DATA]
- أفضل مجموعة:        {summary.get('best_group', 'N/A')}
- أسوأ مجموعة:        {summary.get('worst_group', 'N/A')}
- عدد المجموعات:      {summary.get('num_groups', 'N/A')}

=== KPI متقدمة ===
{kpi_section}

=== أداء المجموعات ===
{group_section}

=== تأثير الأعياد ===
{holiday_section}

=== الارتباطات مع المبيعات ===
{corr_section}
ملاحظة: جميع الارتباطات إحصائية فقط — لا تعني سببية.

=== التوقعات ===
النموذج المستخدم:    {fc_model}
ثقة التوقع:         {fc_conf} ({fc_reliability})
تقلب الإيراد:       {volatility} (CV = {fc_cv:.1f}%)

أرقام التوقع:
- الـ 4 فترات القادمة:    ${next_4:,.0f}
- الـ 12 فترة (Base):    ${next_12:,.0f}
- Bear Case (12f):       ${bear_12:,.0f} ({bear_spread:+.1f}%)
- Bull Case (12f):       ${bull_12:,.0f} (+{bull_spread:.1f}%)
- ذروة متوقعة:           {peak_wk} → ${peak_val:,.0f}

نطاق التخطيط: ${bear_12:,.0f} (Bear) — ${next_12:,.0f} (Base) — ${bull_12:,.0f} (Bull)
{sanity_block}
=== كيفية ذكر التوقعات في إجابتك ===
- اذكر دائماً النطاق [Bear–Base–Bull] وليس رقماً واحداً فقط.
- مثال صحيح: "التوقع الأساسي ${next_12:,.0f} لـ12 فترة [{fc_conf} confidence]،
  مع نطاق Bear/Bull ${bear_12:,.0f}–${bull_12:,.0f}."
"""

    def _build_user_prompt(self, ctx: SharedContext) -> str:
        """بناء طلب المستخدم بناءً على نوع التحليل"""
        prompts = {
            "executive_summary": (
                "اكتب ملخصاً تنفيذياً شاملاً يتضمن:\n"
                "1. الوضع الحالي (أرقام دقيقة من البيانات)\n"
                "2. أبرز 3 نتائج مع تأثيرها المالي\n"
                "3. أهم 3 قرارات عاجلة مع موعد كل منها\n"
                "4. توقعات 12 فترة مع نطاق Bear/Base/Bull\n"
                "5. الفرص والمخاطر الرئيسية\n\n"
                "القاعدة الذهبية: كل ادعاء يجب أن يكون مدعوماً برقم من البيانات."
            ),
            "performance_analysis": (
                "قدّم تحليل أداء تفصيلياً يشمل:\n"
                "1. تحليل الاتجاه مع نقاط التحول الرئيسية\n"
                "2. تصنيف المجموعات (أفضل/متوسط/أسوأ) مع الأسباب\n"
                "3. الأنماط الموسمية وفرص استغلالها\n"
                "4. تأثير العوامل الخارجية (الارتباطات)\n"
                "5. بطاقة مؤشرات الأداء KPI"
            ),
            "problem_detection": (
                "حدد جميع المشاكل بدقة جراحية:\n"
                "1. مشاكل حرجة تتطلب تدخلاً هذا الأسبوع (مع الأرقام)\n"
                "2. إشارات تحذيرية تحتاج متابعة هذا الشهر\n"
                "3. ضعف أداء مزمن مع قرار: استثمر/أعد هيكلة/أغلق\n"
                "4. عوامل خطر خفية\n"
                "5. قائمة أولويات الإصلاح مع التكلفة والعائد"
            ),
            "profit_improvement": (
                "قدّم خطة تحسين أرباح ملموسة:\n"
                "1. مكاسب سريعة (0-30 يوم) مع العائد المتوقع\n"
                "2. استراتيجيات متوسطة المدى (1-3 أشهر)\n"
                "3. أكبر 3 فرص إيراد غير مستغلة\n"
                "4. ما يجب التوقف عنه (مدمرات القيمة)\n"
                "5. توقع إيرادات 12 فترة بسيناريوهات ثلاثة"
            ),
        }
        return prompts.get(self.analysis_type, prompts["executive_summary"])


# ════════════════════════════════════════════════
# 9. REPORT AGENT
# ════════════════════════════════════════════════
class ReportAgent(BaseAgent):
    """
    المسؤولية: توليد تقرير PDF فقط.
    Input:  ctx كامل (كل مخرجات الـ agents السابقة)
    Output: ctx.pdf_bytes + ctx.pdf_path
    """
    name = "ReportAgent"

    def __init__(self, output_path: str = "outputs/report.pdf"):
        self.output_path = output_path

    def _execute(self, ctx: SharedContext) -> SharedContext:
        if ctx.df is None:
            raise ValueError("ReportAgent: لا يوجد بيانات لإنشاء التقرير")

        from pdf_gen_agent import generate_pdf
        from translations import get_translations

        T = get_translations(ctx.lang)

        pdf_bytes = generate_pdf(
            df               = ctx.df,
            date_col         = ctx.date_col,
            sales_col        = ctx.sales_col,
            summary          = ctx.summary,
            store_df         = ctx.store_df,
            corr_series      = ctx.corr_series,
            forecast         = ctx.forecast_df,
            prophet_data     = ctx.prophet_data,
            forecast_summary = ctx.forecast_summary,
            monthly_df       = ctx.monthly_df,
            group_col        = ctx.group_col,
            company_name     = ctx.company_name,
            T                = T,
            ai_result        = ctx.ai_analysis_text,
            ai_type          = "executive_summary",
            lang             = ctx.lang,
            system_prompt    = "",
            ask_agent_fn     = None,
        )

        ctx.pdf_bytes = pdf_bytes

        # حفظ على القرص أيضاً
        import os
        os.makedirs(os.path.dirname(self.output_path) or ".", exist_ok=True)
        with open(self.output_path, 'wb') as f:
            f.write(pdf_bytes)
        ctx.pdf_path = self.output_path

        return ctx


# ════════════════════════════════════════════════
# 10. CHAT AGENT — للمحادثة التفاعلية
# ════════════════════════════════════════════════
class ChatAgent(BaseAgent):
    """
    المسؤولية: الإجابة على أسئلة المستخدم في الوقت الفعلي.
    يستخدم ctx كـ context ثابت + تاريخ المحادثة.
    """
    name = "ChatAgent"

    def __init__(self, question: str, history: Optional[list] = None, stream: bool = False):
        self.question = question
        self.history  = history or []
        self.stream   = stream
        self.client   = _get_client()

    def _execute(self, ctx: SharedContext) -> SharedContext:
        # ChatAgent لا يعدّل الـ ctx — فقط يستخدمه
        raise NotImplementedError("استخدم ask() أو stream() مباشرة")

    def ask(self, ctx: SharedContext) -> tuple:
        """إجابة كاملة — تُرجع (النص، تاريخ المحادثة)"""
        system = self._build_chat_system(ctx)
        messages = self.history.copy()
        messages.append({"role": "user", "content": self.question})

        response = self.client.messages.create(
            model      = "claude-sonnet-4-6",
            max_tokens = 4096,
            system     = system,
            messages   = messages,
        )
        answer = response.content[0].text
        messages.append({"role": "assistant", "content": answer})
        return answer, messages

    def stream_response(self, ctx: SharedContext):
        """Streaming — يولد النص كلمة كلمة"""
        system = self._build_chat_system(ctx)
        messages = self.history.copy()
        messages.append({"role": "user", "content": self.question})

        with self.client.messages.stream(
            model      = "claude-sonnet-4-6",
            max_tokens = 4096,
            system     = system,
            messages   = messages,
        ) as stream_obj:
            for text in stream_obj.text_stream:
                yield text

    def _build_chat_system(self, ctx: SharedContext) -> str:
        """
        System prompt مضغوط للمحادثة — يحتوي فقط على الأرقام الجوهرية.
        أقصر من system prompt التقرير لتوفير tokens في المحادثة.
        """
        lang_map = {
            "en": "Always respond in English.",
            "ar": "أجب دائماً بالعربية الفصحى.",
            "fr": "Répondez toujours en français.",
        }
        summary = ctx.summary or {}
        fc      = ctx.forecast_summary or {}

        next_12 = fc.get('next_12_weeks', 0)
        bear_12 = fc.get('bear_12_weeks', next_12 * 0.75)
        bull_12 = fc.get('bull_12_weeks', next_12 * 1.25)
        fc_conf = fc.get('confidence_level', 'Medium')

        group_summary = ""
        if ctx.store_df is not None and ctx.group_col:
            top3 = ctx.store_df.head(3)[ctx.group_col].tolist()
            group_summary = f"أفضل 3 مجموعات: {top3}"

        return f"""أنت محلل أعمال خبير تجيب على أسئلة حول بيانات المبيعات.
{lang_map.get(ctx.lang, lang_map['en'])}
{'Client: ' + ctx.company_name if ctx.company_name else ''}

RULES:
- استخدم فقط الأرقام التالية — لا تخترع أرقاماً.
- إذا لم يكن الرقم هنا → قل "البيانات غير متاحة في هذا السياق".
- الارتباطات ≠ سببية.

DATA SNAPSHOT:
- إجمالي الإيراد: ${summary.get('total_sales', 0):,.0f}
- متوسط الفترة:   ${summary.get('avg_weekly_sales', 0):,.0f}
- النطاق الزمني:  {summary.get('date_range', 'N/A')}
- أفضل مجموعة:   {summary.get('best_group', 'N/A')}
- أسوأ مجموعة:   {summary.get('worst_group', 'N/A')}
{group_summary}

FORECAST (12 فترة):
- Base: ${next_12:,.0f} | Bear: ${bear_12:,.0f} | Bull: ${bull_12:,.0f}
- ثقة التوقع: {fc_conf}
"""


# ════════════════════════════════════════════════
# 11. ORCHESTRATOR — المدير التنفيذي
# ════════════════════════════════════════════════
class OrchestratorAgent:
    """
    المدير التنفيذي الذي يشغّل كل الـ agents بالترتيب الصحيح.

    Pipeline:
        DataAgent → AnalysisAgent → ForecastAgent →
        VisualAgent → AIAnalysisAgent → ReportAgent

    المبادئ:
    - كل agent يفشل بشكل مستقل (لا يوقف الـ pipeline كله)
    - الـ SharedContext هو الوسيلة الوحيدة للتواصل بين الـ agents
    - الـ Orchestrator لا يعالج البيانات بنفسه أبداً
    """

    def __init__(
        self,
        lang: str = "en",
        company_name: str = "",
        date_col: str = "Date",
        sales_col: str = "Weekly_Sales",
        forecast_weeks: int = 12,
        analysis_type: str = "executive_summary",
        output_pdf_path: str = "outputs/report.pdf",
    ):
        self.lang             = lang
        self.company_name     = company_name
        self.date_col         = date_col
        self.sales_col        = sales_col
        self.forecast_weeks   = forecast_weeks
        self.analysis_type    = analysis_type
        self.output_pdf_path  = output_pdf_path

    def _init_context(self) -> SharedContext:
        """إنشاء SharedContext جديد بإعدادات المستخدم"""
        return SharedContext(
            lang           = self.lang,
            company_name   = self.company_name,
            date_col       = self.date_col,
            sales_col      = self.sales_col,
            forecast_weeks = self.forecast_weeks,
        )

    def run_full_pipeline(
        self,
        path: Optional[str] = None,
        dataframe=None,
        progress_callback=None,  # function(step: int, total: int, message: str)
    ) -> SharedContext:
        """
        تشغيل الـ pipeline الكامل من تحميل البيانات حتى إنشاء التقرير.

        Args:
            path:              مسار ملف CSV/Excel
            dataframe:         pandas DataFrame مباشر (من Streamlit upload)
            progress_callback: دالة لتحديث شريط التقدم في الـ UI

        Returns:
            SharedContext يحتوي على كل النتائج
        """
        ctx   = self._init_context()
        total = 6  # عدد الـ agents

        def _progress(step: int, msg: str):
            if progress_callback:
                progress_callback(step, total, msg)

        # ── Step 1: Data ─────────────────────────
        _progress(1, "⏳ تحميل وتنظيف البيانات...")
        ctx = DataAgent(path=path, dataframe=dataframe).run(ctx)
        if not ctx.is_healthy():
            ctx.add_error("Pipeline أُوقف: DataAgent فشل — البيانات غير صالحة")
            return ctx

        # ── Step 2: Analysis ─────────────────────
        _progress(2, "📊 تحليل البيانات...")
        ctx = AnalysisAgent().run(ctx)
        # Analysis ليس حرجاً — نكمل حتى لو فشل جزئياً

        # ── Step 3: Forecast ─────────────────────
        _progress(3, "🔮 حساب التوقعات...")
        ctx = ForecastAgent().run(ctx)

        # ── Step 4: Visualization ────────────────
        _progress(4, "📈 إنشاء الرسوم البيانية...")
        ctx = VisualAgent().run(ctx)

        # ── Step 5: AI Analysis ──────────────────
        _progress(5, "🤖 توليد التحليل الذكي...")
        ctx = AIAnalysisAgent(analysis_type=self.analysis_type).run(ctx)

        # ── Step 6: Report ───────────────────────
        _progress(6, "📄 إنشاء التقرير...")
        ctx = ReportAgent(output_path=self.output_pdf_path).run(ctx)

        ctx.pipeline_complete = ctx.is_healthy()
        _progress(total, "✅ اكتمل!" if ctx.pipeline_complete else "⚠️ اكتمل مع تحذيرات")

        return ctx

    def run_analysis_only(
        self,
        path: Optional[str] = None,
        dataframe=None,
        analysis_type: Optional[str] = None,
    ) -> SharedContext:
        """
        تشغيل بدون PDF — أسرع وأرخص في الـ API cost.
        مناسب للمعاينة السريعة.
        """
        ctx    = self._init_context()
        a_type = analysis_type or self.analysis_type

        ctx = DataAgent(path=path, dataframe=dataframe).run(ctx)
        if not ctx.is_healthy():
            return ctx

        ctx = AnalysisAgent().run(ctx)
        ctx = ForecastAgent().run(ctx)
        ctx = AIAnalysisAgent(analysis_type=a_type).run(ctx)

        ctx.pipeline_complete = ctx.is_healthy()
        return ctx

    def chat(
        self,
        question: str,
        ctx: SharedContext,
        history: Optional[list] = None,
        stream: bool = False,
    ):
        """
        واجهة المحادثة — يستخدم الـ ctx الموجود كـ context.

        Args:
            question: سؤال المستخدم
            ctx:      SharedContext من pipeline سابق
            history:  تاريخ المحادثة
            stream:   True للـ streaming

        Returns:
            إذا stream=False: (answer: str, history: list)
            إذا stream=True:  generator يولد النص كلمة كلمة
        """
        agent = ChatAgent(question=question, history=history, stream=stream)
        if stream:
            return agent.stream_response(ctx)
        else:
            return agent.ask(ctx)


# ════════════════════════════════════════════════
# 12. STREAMLIT HELPER — واجهة مبسطة للـ app.py
# ════════════════════════════════════════════════
def create_orchestrator(
    lang: str = "en",
    company_name: str = "",
    date_col: str = "Date",
    sales_col: str = "Weekly_Sales",
    forecast_weeks: int = 12,
) -> OrchestratorAgent:
    """
    Factory function — أبسط طريقة لإنشاء Orchestrator من الـ app.
    استخدم هذه الدالة في app.py بدلاً من الكلاس مباشرة.
    """
    return OrchestratorAgent(
        lang           = lang,
        company_name   = company_name,
        date_col       = date_col,
        sales_col      = sales_col,
        forecast_weeks = forecast_weeks,
    )


def run_pipeline_with_progress(
    orchestrator: OrchestratorAgent,
    dataframe=None,
    path: Optional[str] = None,
    streamlit_progress=None,  # st.progress() object
) -> SharedContext:
    """
    تشغيل الـ pipeline مع شريط تقدم Streamlit.
    استخدم هذه الدالة مباشرة في app.py.

    مثال الاستخدام في app.py:
    ─────────────────────────
    from orchestrator_agent import create_orchestrator, run_pipeline_with_progress

    orch = create_orchestrator(lang="ar", date_col="Date", sales_col="Sales")
    progress_bar = st.progress(0)
    ctx = run_pipeline_with_progress(orch, dataframe=df, streamlit_progress=progress_bar)

    if ctx.pdf_bytes:
        st.download_button("📥 تنزيل التقرير", ctx.pdf_bytes, "report.pdf")
    if ctx.warnings:
        for w in ctx.warnings:
            st.warning(w)
    ─────────────────────────
    """
    status_text = st.empty() if streamlit_progress else None

    def progress_callback(step: int, total: int, message: str):
        if streamlit_progress:
            streamlit_progress.progress(step / total)
        if status_text:
            status_text.text(message)

    ctx = orchestrator.run_full_pipeline(
        path              = path,
        dataframe         = dataframe,
        progress_callback = progress_callback,
    )

    if streamlit_progress:
        streamlit_progress.progress(1.0)
    if status_text:
        status_text.empty()

    return ctx