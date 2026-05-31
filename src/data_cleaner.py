import pandas as pd

def clean_data(df, date_col='Date', sales_col='Weekly_Sales'):
    """
    تنظيف شامل لأي داتا مبيعات
    يرجع: (df_clean, report) 
    report = تقرير بكل اللي صار
    """
    report = []
    original_rows = len(df)

    # ── 1. نسخة مستقلة ──────────────────────────────
    df = df.copy()
    df.columns = [col.strip() for col in df.columns]

    date_col = date_col.strip()
    sales_col =sales_col.strip()

    # ── 2. أسماء الأعمدة ─────────────────────────────
    # أحياناً فيها مسافات زائدة أو حروف كبيرة
    df.columns = df.columns.str.strip()
    report.append("✅ Column names cleaned")

    # ── 3. التاريخ ────────────────────────────────────
    try:
        def parse_dates(series):
            formats = [
                '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d',
                '%d-%m-%Y', '%m-%d-%Y', '%Y/%m/%d',
                '%d.%m.%Y', '%m.%d.%Y'
            ]
            for fmt in formats:
                try:
                    parsed = pd.to_datetime(series, format=fmt, errors='coerce')
                    if parsed.notna().sum() > len(series) * 0.8:
                        return parsed
                except:
                    continue
            return pd.to_datetime(series, errors='coerce')

        df[date_col] = parse_dates(df[date_col])
        bad_dates = df[date_col].isna().sum()
        if bad_dates > 0:
            df = df.dropna(subset=[date_col])
            report.append(f"⚠️  Dropped {bad_dates} rows with invalid dates")
        else:
            report.append("✅ Dates parsed correctly")
    except Exception as e:
        report.append(f"❌ Date parsing failed: {e}")

    # ── 4. المبيعات السالبة أو الصفر ─────────────────
    negative = (df[sales_col] < 0).sum()
    if negative > 0:
        df = df[df[sales_col] >= 0]
        report.append(f"⚠️  Removed {negative} rows with negative sales")

    zero_sales = (df[sales_col] == 0).sum()
    if zero_sales > 0:
        report.append(f"ℹ️  Found {zero_sales} rows with zero sales (kept)")

    # ── 5. Duplicates ─────────────────────────────────
    dupes = df.duplicated().sum()
    if dupes > 0:
        df = df.drop_duplicates()
        report.append(f"⚠️  Removed {dupes} duplicate rows")
    else:
        report.append("✅ No duplicates found")

    # ── 6. Nulls ──────────────────────────────────────
    null_counts = df.isnull().sum()
    total_nulls = null_counts.sum()

    if total_nulls == 0:
        report.append("✅ No null values found")
    else:
        for col, count in null_counts.items():
            if count == 0:
                continue
            # الأعمدة الرقمية → نملأ بالمتوسط
            if df[col].dtype in ['float64', 'int64']:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                report.append(
                    f"⚠️  {col}: filled {count} nulls with median ({median_val:.2f})"
                )
            # الأعمدة النصية → نملأ بـ 'Unknown'
            else:
                df[col] = df[col].fillna('Unknown')
                report.append(f"⚠️  {col}: filled {count} nulls with 'Unknown'")

    # ── 7. Outliers (اختياري - نسجل بس مو نحذف) ──────
    Q1 = df[sales_col].quantile(0.25)
    Q3 = df[sales_col].quantile(0.75)
    IQR = Q3 - Q1
    outliers = ((df[sales_col] < Q1 - 3*IQR) | 
                (df[sales_col] > Q3 + 3*IQR)).sum()
    if outliers > 0:
        report.append(f"ℹ️  Found {outliers} outliers in {sales_col} (kept - review manually)")

    # ── 8. ترتيب ─────────────────────────────────────
    if 'Store' in df.columns:
        df = df.sort_values(['Store', date_col]).reset_index(drop=True)
    else:
        df = df.sort_values(date_col).reset_index(drop=True)

    # ── 9. تقرير نهائي ───────────────────────────────
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