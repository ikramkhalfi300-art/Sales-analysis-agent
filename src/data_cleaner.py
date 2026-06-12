import pandas as pd
import numpy as np


def clean_data(df, date_col='Date', sales_col='Weekly_Sales'):
    """
    تنظيف البيانات بمنطق نسب الـ nulls:
      < 5%  → ملأ بالمتوسط / الأكثر تكراراً
      5-20% → احذف الصفوف
      > 20% → احذف العمود كله
    """
    report = []
    original_rows = len(df)

    df = df.copy()
    df.columns = df.columns.str.strip()
    date_col = date_col.strip()
    sales_col = sales_col.strip()
    report.append("✅ Column names cleaned")

    # ── التاريخ ──────────────────────────────────────────
    try:
        formats = [
            '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d',
            '%d-%m-%Y', '%m-%d-%Y', '%Y/%m/%d',
            '%d.%m.%Y', '%m.%d.%Y'
        ]
        parsed = None
        for fmt in formats:
            try:
                candidate = pd.to_datetime(df[date_col], format=fmt, errors='coerce')
                if candidate.notna().sum() > len(df) * 0.8:
                    parsed = candidate
                    break
            except Exception:
                continue
        if parsed is None:
            parsed = pd.to_datetime(df[date_col], errors='coerce')
        df[date_col] = parsed

        bad_dates = df[date_col].isna().sum()
        if bad_dates > 0:
            df = df.dropna(subset=[date_col])
            report.append(f"⚠️ Dropped {bad_dates} rows with invalid dates")
        else:
            report.append("✅ Dates parsed correctly")
    except Exception as e:
        report.append(f"❌ Date parsing failed: {e}")

    # ── المبيعات السالبة ─────────────────────────────────
    if sales_col in df.columns:
        negative = (df[sales_col] < 0).sum()
        if negative > 0:
            df = df[df[sales_col] >= 0]
            report.append(f"⚠️ Removed {negative} rows with negative sales")

        zero_sales = (df[sales_col] == 0).sum()
        if zero_sales > 0:
            report.append(f"ℹ️ Found {zero_sales} rows with zero sales (kept)")

    # ── Duplicates ───────────────────────────────────────
    dupes = df.duplicated().sum()
    if dupes > 0:
        df = df.drop_duplicates()
        report.append(f"⚠️ Removed {dupes} duplicate rows")
    else:
        report.append("✅ No duplicates found")

    # ── Nulls بمنطق النسب ────────────────────────────────
    total_rows = len(df)
    null_counts = df.isnull().sum()
    total_nulls = null_counts.sum()
    cols_to_drop = []
    rows_to_drop_mask = pd.Series([False] * total_rows, index=df.index)

    if total_nulls == 0:
        report.append("✅ No null values found")
    else:
        for col, count in null_counts.items():
            if count == 0:
                continue
            pct = count / total_rows

            if pct < 0.05:
                # أقل من 5% → ملأ
                if pd.api.types.is_numeric_dtype(df[col]):
                    fill_val = df[col].mean()
                    df[col] = df[col].fillna(fill_val)
                    report.append(
                        f"✅ '{col}': {pct*100:.1f}% nulls → filled with mean ({fill_val:.2f})"
                    )
                else:
                    fill_val = df[col].mode()[0] if not df[col].mode().empty else 'Unknown'
                    df[col] = df[col].fillna(fill_val)
                    report.append(
                        f"✅ '{col}': {pct*100:.1f}% nulls → filled with most frequent ('{fill_val}')"
                    )

            elif pct <= 0.20:
                # 5-20% → احذف الصفوف
                null_rows = df[col].isna()
                rows_to_drop_mask = rows_to_drop_mask | null_rows
                report.append(
                    f"⚠️ '{col}': {pct*100:.1f}% nulls → will drop {null_rows.sum()} rows"
                )

            else:
                # أكثر من 20% → احذف العمود
                cols_to_drop.append(col)
                report.append(
                    f"🗑️ '{col}': {pct*100:.1f}% nulls → dropping entire column"
                )

    if rows_to_drop_mask.any():
        dropped_rows = int(rows_to_drop_mask.sum())
        df = df[~rows_to_drop_mask]
        report.append(f"⚠️ Dropped {dropped_rows} rows due to 5-20% null columns")

    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        report.append(f"🗑️ Dropped columns: {cols_to_drop}")

    # ── Outliers (تسجيل فقط) ─────────────────────────────
    if sales_col in df.columns:
        Q1 = df[sales_col].quantile(0.25)
        Q3 = df[sales_col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = ((df[sales_col] < Q1 - 3*IQR) | (df[sales_col] > Q3 + 3*IQR)).sum()
        if outliers > 0:
            report.append(
                f"ℹ️ Found {outliers} outliers in {sales_col} (kept - review manually)"
            )

    # ── ترتيب ────────────────────────────────────────────
    if 'Store' in df.columns:
        df = df.sort_values(['Store', date_col]).reset_index(drop=True)
    else:
        df = df.sort_values(date_col).reset_index(drop=True)

    final_rows = len(df)
    dropped = original_rows - final_rows
    report.append(f"\n📊 Summary: {original_rows:,} → {final_rows:,} rows ({dropped} dropped)")

    return df, report


def print_report(report):
    print("\n" + "="*45)
    print("   🧹 Data Cleaning Report")
    print("="*45)
    for line in report:
        print(f"  {line}")
    print("="*45 + "\n")