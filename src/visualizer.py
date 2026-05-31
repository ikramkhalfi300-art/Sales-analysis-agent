import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

os.makedirs('outputs', exist_ok=True)

# ألوان موحدة للمشروع
COLORS = {
    'primary': '#2563EB',
    'secondary': '#DC2626',
    'success': '#16A34A',
    'warning': '#D97706',
    'purple': '#7C3AED',
    'gray': '#6B7280'
}

def format_millions(x, pos):
    return f'${x/1e6:.1f}M'

def plot_sales_trend(df):
    """منحنى المبيعات الكلية أسبوعياً"""
    weekly = df.groupby('Date')['Weekly_Sales'].sum().reset_index()
    
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(weekly['Date'], weekly['Weekly_Sales'],
            color=COLORS['primary'], linewidth=1, alpha=0.6)
    
    # Moving average 4 أسابيع
    weekly['ma4'] = weekly['Weekly_Sales'].rolling(4).mean()
    ax.plot(weekly['Date'], weekly['ma4'],
            color=COLORS['secondary'], linewidth=2.5, label='4-Week Average')
    
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(format_millions))
    ax.set_title('Total Weekly Sales - All Stores', fontsize=15, fontweight='bold', pad=15)
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Sales')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    import os
    os.makedirs('outputs', exist_ok=True)
    plt.savefig('outputs/01_sales_trend.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ Saved: outputs/01_sales_trend.png")
    print("✅ 01_sales_trend.png")

def plot_store_comparison(store_df):
    """مقارنة المتاجر - أفضل 10"""
    top10 = store_df.head(10)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(
        top10['Store'].astype(str),
        top10['total'],
        color=COLORS['primary'],
        alpha=0.85,
        edgecolor='white',
        linewidth=0.5
    )
    
    # أضف الأرقام فوق الأعمدة
    for bar, val in zip(bars, top10['total']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1e6,
                f'${val/1e6:.0f}M', ha='center', va='bottom', fontsize=9)
    
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(format_millions))
    ax.set_title('Top 10 Stores by Total Sales', fontsize=15, fontweight='bold', pad=15)
    ax.set_xlabel('Store Number')
    ax.set_ylabel('Total Sales')
    ax.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('outputs/02_store_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ 02_store_comparison.png")

def plot_monthly_trend(monthly_df):
    """المبيعات الشهرية"""
    fig, ax = plt.subplots(figsize=(14, 5))
    
    months = [str(m) for m in monthly_df['month']]
    ax.bar(months, monthly_df['total'],
           color=COLORS['success'], alpha=0.8, edgecolor='white')
    
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(format_millions))
    ax.set_title('Monthly Sales - All Stores', fontsize=15, fontweight='bold', pad=15)
    ax.set_xlabel('Month')
    ax.set_ylabel('Total Sales')
    plt.xticks(rotation=45, ha='right', fontsize=8)
    ax.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('outputs/03_monthly_trend.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ 03_monthly_trend.png")

def plot_holiday_impact(holiday_df):
    """تأثير الأعياد على المبيعات"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    colors = [COLORS['primary'], COLORS['warning']]
    
    # متوسط المبيعات
    axes[0].bar(holiday_df['type'], holiday_df['avg'],
                color=colors, alpha=0.85, edgecolor='white')
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(format_millions))
    axes[0].set_title('Average Weekly Sales', fontweight='bold')
    axes[0].set_ylabel('Avg Sales')
    axes[0].grid(True, axis='y', alpha=0.3)
    
    # عدد الأسابيع
    axes[1].bar(holiday_df['type'], holiday_df['weeks'],
                color=colors, alpha=0.85, edgecolor='white')
    axes[1].set_title('Number of Weeks', fontweight='bold')
    axes[1].set_ylabel('Count')
    axes[1].grid(True, axis='y', alpha=0.3)
    
    fig.suptitle('Holiday vs Normal Weeks', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig('outputs/04_holiday_impact.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ 04_holiday_impact.png")

def plot_correlations(corr_series):
    """علاقة العوامل الخارجية بالمبيعات"""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    colors = [COLORS['success'] if v > 0 else COLORS['secondary']
              for v in corr_series.values]
    
    bars = ax.barh(corr_series.index, corr_series.values,
                   color=colors, alpha=0.85, edgecolor='white')
    
    # أضف القيم
    for bar, val in zip(bars, corr_series.values):
        ax.text(val + (0.002 if val > 0 else -0.002), bar.get_y() + bar.get_height()/2,
                f'{val:.4f}', va='center', ha='left' if val > 0 else 'right', fontsize=10)
    
    ax.axvline(x=0, color='black', linewidth=0.8)
    ax.set_title('Correlation with Weekly Sales', fontsize=15, fontweight='bold', pad=15)
    ax.set_xlabel('Correlation Coefficient')
    ax.grid(True, axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('outputs/05_correlations.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ 05_correlations.png")

def plot_forecast(forecast, historical):
    """رسم التوقعات"""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # التاريخي
    ax.plot(historical['ds'], historical['y'],
            color=COLORS['primary'], linewidth=1, label='Historical', alpha=0.7)
    
    # التوقعات
    future = forecast[forecast['ds'] > historical['ds'].max()]
    ax.plot(future['ds'], future['yhat'],
            color=COLORS['secondary'], linewidth=2.5, label='Forecast')
    ax.fill_between(future['ds'], future['yhat_lower'], future['yhat_upper'],
                    alpha=0.15, color=COLORS['secondary'], label='Confidence Interval')
    
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(format_millions))
    ax.set_title('Sales Forecast - Next 12 Weeks', fontsize=15, fontweight='bold', pad=15)
    ax.set_xlabel('Date')
    ax.set_ylabel('Weekly Sales')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('outputs/06_forecast.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ 06_forecast.png")