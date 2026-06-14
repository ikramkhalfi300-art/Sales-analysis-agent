
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Decision:
    unit: str           # اسم المتجر/الفرع
    revenue: float      # الإيراد الإجمالي
    avg_period: float   # متوسط الفترة
    vs_avg_pct: float   # % فوق/تحت المتوسط الكلي
    trend: str          # Growing / Stable / Declining
    trend_pct: float    # نسبة التغيير
    problem: str        # وصف المشكلة أو نقطة القوة
    decision: str       # INVEST / MONITOR / RESTRUCTURE / CLOSE
    action: str         # إجراء محدد
    financial_impact: float   # الأثر المالي المقدر $
    urgency: str        # This Week / This Month / This Quarter
    confidence: str     # High / Medium / Low
    rating: str         # 🟢 / 🟡 / 🔴


def _calc_trend(series: pd.Series) -> tuple:
    """يحسب اتجاه المبيعات لسلسلة زمنية"""
    if len(series) < 2:
        return "Stable", 0.0
    half = max(1, len(series) // 2)
    first_half = series.iloc[:half].mean()
    second_half = series.iloc[half:].mean()
    if first_half == 0:
        return "Stable", 0.0
    pct = (second_half - first_half) / first_half * 100
    if pct > 5:
        return "Growing", round(pct, 1)
    elif pct < -5:
        return "Declining", round(pct, 1)
    return "Stable", round(pct, 1)


def generate_decisions(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    group_col: Optional[str],
    lang: str = "en"
) -> List[Decision]:
    """
    يولد قائمة قرارات لكل وحدة (متجر/فرع)
    إذا ما في group_col → يحلل الفترات الزمنية بدلاً
    """
    decisions = []
    overall_avg = df[sales_col].mean()
    overall_total = df[sales_col].sum()

    LABELS = {
        "en": {
            "growing":      "Growing consistently",
            "stable":       "Stable performance",
            "declining":    "Declining trend",
            "top":          "Top performer — drives disproportionate revenue",
            "strong":       "Strong performer — above average",
            "average":      "Average performer — room for growth",
            "weak":         "Weak performer — below average",
            "critical":     "Critical underperformer — significant revenue gap",
            "invest":       "INVEST",
            "monitor":      "MONITOR",
            "restructure":  "RESTRUCTURE",
            "close":        "EVALUATE CLOSURE",
            "act_invest":   "Replicate success model in similar locations",
            "act_monitor":  "Track monthly — set growth target of +10%",
            "act_restructure": "Review operations, staffing, and product mix",
            "act_close":    "Conduct closure feasibility analysis within 30 days",
            "this_week":    "This Week",
            "this_month":   "This Month",
            "this_quarter": "This Quarter",
        },
        "ar": {
            "growing":      "نمو مستمر",
            "stable":       "أداء مستقر",
            "declining":    "اتجاه تراجعي",
            "top":          "الأفضل أداءً — يولد إيراداً غير متناسب",
            "strong":       "أداء قوي — فوق المتوسط",
            "average":      "أداء متوسط — إمكانية نمو",
            "weak":         "أداء ضعيف — تحت المتوسط",
            "critical":     "ضعف حرج — فجوة إيرادية كبيرة",
            "invest":       "استثمر",
            "monitor":      "راقب",
            "restructure":  "أعد الهيكلة",
            "close":        "دراسة الإغلاق",
            "act_invest":   "كرر نموذج النجاح في مواقع مشابهة",
            "act_monitor":  "تتبع شهرياً — ضع هدف نمو +10%",
            "act_restructure": "راجع العمليات والكوادر ومزيج المنتجات",
            "act_close":    "دراسة جدوى الإغلاق خلال 30 يوماً",
            "this_week":    "هذا الأسبوع",
            "this_month":   "هذا الشهر",
            "this_quarter": "هذا الربع",
        },
        "fr": {
            "growing":      "Croissance constante",
            "stable":       "Performance stable",
            "declining":    "Tendance déclinante",
            "top":          "Top performer — revenu disproportionné",
            "strong":       "Fort performer — au-dessus de la moyenne",
            "average":      "Performance moyenne — potentiel de croissance",
            "weak":         "Performance faible — sous la moyenne",
            "critical":     "Sous-performance critique — écart significatif",
            "invest":       "INVESTIR",
            "monitor":      "SURVEILLER",
            "restructure":  "RESTRUCTURER",
            "close":        "ÉVALUER FERMETURE",
            "act_invest":   "Répliquer le modèle de succès dans des emplacements similaires",
            "act_monitor":  "Suivi mensuel — objectif de croissance +10%",
            "act_restructure": "Réviser les opérations, le personnel et le mix produit",
            "act_close":    "Analyse de faisabilité de fermeture dans 30 jours",
            "this_week":    "Cette semaine",
            "this_month":   "Ce mois",
            "this_quarter": "Ce trimestre",
        },
    }
    L = LABELS.get(lang, LABELS["en"])

    if group_col and group_col in df.columns:
        grouped = df.groupby(group_col)
        group_stats = grouped[sales_col].agg(['sum','mean','std','count']).reset_index()
        group_stats.columns = [group_col, 'total', 'avg', 'std', 'count']
        group_stats = group_stats.sort_values('total', ascending=False)

        overall_unit_avg = group_stats['total'].mean()

        for _, row in group_stats.iterrows():
            unit_name  = str(row[group_col])
            revenue    = float(row['total'])
            avg_period = float(row['avg'])
            vs_avg     = (revenue - overall_unit_avg) / overall_unit_avg * 100 if overall_unit_avg else 0

            # حساب الاتجاه
            unit_series = df[df[group_col] == row[group_col]].sort_values(date_col)[sales_col]
            trend, trend_pct = _calc_trend(unit_series)

            # تحديد المشكلة/القوة
            rank_pct = group_stats['total'].rank(pct=True)[group_stats[group_col] == row[group_col]].values[0]

            if rank_pct >= 0.85:
                problem  = L["top"]
                decision = L["invest"]
                action   = L["act_invest"]
                urgency  = L["this_quarter"]
                rating   = "🟢"
                impact   = revenue * 0.15  # 15% إضافي من الاستثمار
                confidence = "High"
            elif rank_pct >= 0.60:
                problem  = L["strong"]
                decision = L["monitor"]
                action   = L["act_monitor"]
                urgency  = L["this_quarter"]
                rating   = "🟢"
                impact   = revenue * 0.10
                confidence = "High"
            elif rank_pct >= 0.40:
                problem  = L["average"]
                decision = L["monitor"]
                action   = L["act_monitor"]
                urgency  = L["this_month"]
                rating   = "🟡"
                impact   = (overall_unit_avg - revenue) * 0.5
                confidence = "Medium"
            elif rank_pct >= 0.20:
                problem  = L["weak"]
                decision = L["restructure"]
                action   = L["act_restructure"]
                urgency  = L["this_month"]
                rating   = "🟡"
                impact   = overall_unit_avg - revenue
                confidence = "Medium"
            else:
                problem  = L["critical"]
                decision = L["close"] if vs_avg < -50 else L["restructure"]
                action   = L["act_close"] if vs_avg < -50 else L["act_restructure"]
                urgency  = L["this_week"]
                rating   = "🔴"
                impact   = overall_unit_avg - revenue
                confidence = "High"

            # تعديل بناءً على الاتجاه
            if trend == "Declining" and rating == "🟡":
                rating   = "🔴"
                urgency  = L["this_week"]
            elif trend == "Growing" and rating == "🟡":
                rating   = "🟢"

            decisions.append(Decision(
                unit=unit_name,
                revenue=revenue,
                avg_period=avg_period,
                vs_avg_pct=round(vs_avg, 1),
                trend=f"{trend} ({trend_pct:+.1f}%)",
                trend_pct=trend_pct,
                problem=problem,
                decision=decision,
                action=action,
                financial_impact=round(abs(impact), 0),
                urgency=urgency,
                confidence=confidence,
                rating=rating,
            ))

    return decisions


def decisions_to_df(decisions: List[Decision], lang: str = "en") -> pd.DataFrame:
    """يحوّل قائمة القرارات إلى DataFrame للعرض"""
    COLS = {
        "en": {
            "unit": "Unit", "revenue": "Total Revenue",
            "vs_avg": "vs Average", "trend": "Trend",
            "problem": "Assessment", "decision": "Decision",
            "action": "Recommended Action", "impact": "Est. Financial Impact",
            "urgency": "Urgency", "rating": "Rating",
        },
        "ar": {
            "unit": "الوحدة", "revenue": "الإيراد الكلي",
            "vs_avg": "مقابل المتوسط", "trend": "الاتجاه",
            "problem": "التقييم", "decision": "القرار",
            "action": "الإجراء الموصى به", "impact": "الأثر المالي المقدر",
            "urgency": "الإلحاحية", "rating": "التقييم",
        },
        "fr": {
            "unit": "Unité", "revenue": "Revenu Total",
            "vs_avg": "vs Moyenne", "trend": "Tendance",
            "problem": "Évaluation", "decision": "Décision",
            "action": "Action Recommandée", "impact": "Impact Financier Est.",
            "urgency": "Urgence", "rating": "Note",
        },
    }
    C = COLS.get(lang, COLS["en"])

    rows = []
    for d in decisions:
        rows.append({
            C["rating"]:   d.rating,
            C["unit"]:     d.unit,
            C["revenue"]:  f"${d.revenue:,.0f}",
            C["vs_avg"]:   f"{d.vs_avg_pct:+.1f}%",
            C["trend"]:    d.trend,
            C["problem"]:  d.problem,
            C["decision"]: d.decision,
            C["action"]:   d.action,
            C["impact"]:   f"${d.financial_impact:,.0f}",
            C["urgency"]:  d.urgency,
        })
    return pd.DataFrame(rows)


def get_summary_stats(decisions: List[Decision]) -> dict:
    """ملخص إحصائي للقرارات"""
    if not decisions:
        return {}
    invest     = sum(1 for d in decisions if "INVEST" in d.decision or "استثمر" in d.decision or "INVESTIR" in d.decision)
    monitor    = sum(1 for d in decisions if "MONITOR" in d.decision or "راقب" in d.decision or "SURVEILLER" in d.decision)
    restructure= sum(1 for d in decisions if "RESTRUCTURE" in d.decision or "هيكلة" in d.decision or "RESTRUCTURER" in d.decision)
    close      = sum(1 for d in decisions if "CLOS" in d.decision.upper() or "إغلاق" in d.decision or "FERMETURE" in d.decision)
    total_impact = sum(d.financial_impact for d in decisions)
    critical   = [d for d in decisions if d.rating == "🔴"]
    return {
        "invest": invest, "monitor": monitor,
        "restructure": restructure, "close": close,
        "total_impact": total_impact,
        "critical_count": len(critical),
        "critical_units": [d.unit for d in critical[:3]],
    }