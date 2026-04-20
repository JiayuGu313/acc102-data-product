# ACC102 Mini Assignment: Python Data Product
# Track 2 – GitHub Data Analysis Project
# Student ID: 2473457
# Student Name: Jiayu.Gu
# Product Title: Single Stock Financial & Lifecycle Analysis Tool

# Import required libraries
import wrds
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

# Create output folder
os.makedirs('output', exist_ok=True)
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

print("=" * 60)
print("SINGLE STOCK DATA QUERY TOOL")
print("=" * 60)

# Connect to WRDS
try:
    db = wrds.Connection()
    print("✅ Successfully connected to WRDS")
except Exception as e:
    print(f"❌ Connection failed: {e}")

# Data Query & Analysis Functions
def get_company_financials(db, ticker, start_year, end_year):
    sql = f"""
    SELECT gvkey, tic, fyear, datadate, sale, at, ib, oancf, invch, fincf
    FROM comp.funda
    WHERE tic = '{ticker}'
    AND fyear BETWEEN {start_year} AND {end_year}
    AND indfmt = 'INDL' AND datafmt = 'STD' AND consol = 'C'
    ORDER BY fyear
    """
    data = db.raw_sql(sql)
    print(f"📊 Retrieved {len(data)} years of financial data for {ticker}")
    return data

def get_stock_returns(db, ticker, start_year, end_year):
    sql = f"""
    SELECT a.date, a.ret, a.prc, a.vol
    FROM crsp.msf AS a
    LEFT JOIN crsp.msfhdr AS b ON a.permno = b.permno
    WHERE b.htsymbol = '{ticker}'
    AND a.date >= '{start_year}-01-01'
    AND a.date <= '{end_year}-12-31'
    ORDER BY a.date
    """
    data = db.raw_sql(sql)
    print(f"📈 Retrieved {len(data)} months of return data")
    return data

def get_yearly_price(returns):
    if returns.empty:
        return pd.Series(dtype=float)
    returns['year'] = pd.to_datetime(returns['date']).dt.year
    yearly_price = returns.groupby('year')['prc'].last()
    return yearly_price

def calculate_lifecycle(row):
    def get_sign(value):
        return '+' if value > 0 else '-' if value < 0 else '0'
    o = get_sign(row['oancf'])
    i = get_sign(row['invch'])
    f = get_sign(row['fincf'])
    if o == '+' and i == '-' and f == '+': return 'Introduction'
    elif o == '+' and i == '-' and f == '-': return 'Growth'
    elif o == '-' and i == '+': return 'Decline'
    elif (o == '-' and i == '-') or (o == '+' and i == '+'): return 'Shake-out'
    else: return 'Mature'

def calculate_metrics(returns):
    if returns.empty or len(returns) < 12:
        return None
    mean_return = returns['ret'].mean()
    annual_return = mean_return * 12
    annual_vol = returns['ret'].std() * (12 ** 0.5)
    sharpe = annual_return / annual_vol if annual_vol != 0 else 0
    cumulative = (1 + returns['ret']).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    win_rate = (returns['ret'] > 0).sum() / len(returns)
    return {
        'Annual Return': f"{annual_return:.2%}",
        'Annual Volatility': f"{annual_vol:.2%}",
        'Sharpe Ratio': f"{sharpe:.2f}",
        'Max Drawdown': f"{max_drawdown:.2%}",
        'Win Rate': f"{win_rate:.2%}"
    }

def generate_clean_table(financials, yearly_price, ticker):
    table = financials[['fyear', 'sale', 'at', 'ib', 'oancf', 'invch', 'fincf', 'lifecycle']].copy()
    table['year_end_price'] = table['fyear'].map(yearly_price)
    table.columns = [
        'Year', 'Revenue(MM)', 'Assets(MM)', 'NetIncome(MM)',
        'OperatingCF(MM)', 'InvestingCF(MM)', 'FinancingCF(MM)',
        'Lifecycle', 'YearEndPrice(USD)'
    ]
    numeric_cols = ['Revenue(MM)', 'Assets(MM)', 'NetIncome(MM)',
                    'OperatingCF(MM)', 'InvestingCF(MM)', 'FinancingCF(MM)', 'YearEndPrice(USD)']
    for col in numeric_cols:
        table[col] = table[col].round(2)
    return table

# Visualisation Functions
def plot_financial_trends(financials, ticker, start_year, end_year):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(f'{ticker} Financial Trends ({start_year}-{end_year})', fontsize=16, fontweight='bold')
    
    axes[0,0].plot(financials['fyear'], financials['sale'], 'o-', color='blue')
    axes[0,0].set_title('Revenue Trend')
    axes[0,0].grid(alpha=0.3)
    
    axes[0,1].plot(financials['fyear'], financials['at'], 'o-', color='green')
    axes[0,1].set_title('Assets Trend')
    axes[0,1].grid(alpha=0.3)
    
    axes[1,0].plot(financials['fyear'], financials['ib'], 'o-', color='orange')
    axes[1,0].axhline(0, color='red', linestyle='--')
    axes[1,0].set_title('Net Income Trend')
    axes[1,0].grid(alpha=0.3)
    
    axes[1,1].plot(financials['fyear'], financials['oancf'], 'o-', label='Operating CF')
    axes[1,1].plot(financials['fyear'], financials['invch'], 's-', label='Investing CF')
    axes[1,1].plot(financials['fyear'], financials['fincf'], '^-', label='Financing CF')
    axes[1,1].legend()
    axes[1,1].set_title('Cash Flow Components')
    axes[1,1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'output/{ticker}_financial_trends.png', dpi=150)
    plt.show()

def plot_stock_performance(returns, ticker, start_year, end_year):
    if returns.empty:
        print("⚠️ No return data to plot")
        return
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle(f'{ticker} Stock Performance ({start_year}-{end_year})', fontsize=16, fontweight='bold')
    
    axes[0].bar(range(len(returns)), returns['ret'], alpha=0.7)
    axes[0].axhline(0, color='red', linestyle='--')
    axes[0].set_title('Monthly Returns')
    axes[0].grid(alpha=0.3)
    
    cumulative = (1 + returns['ret']).cumprod()
    axes[1].plot(range(len(cumulative)), cumulative, 'o-', linewidth=2)
    axes[1].axhline(1, color='red', linestyle='--')
    axes[1].set_title('Cumulative Return')
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'output/{ticker}_stock_performance.png', dpi=150)
    plt.show()

# Export Functions
def export_to_excel(financials, returns, metrics, ticker):
    output_file = f'output/{ticker}_report.xlsx'
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        financials.to_excel(writer, sheet_name='Financial Data', index=False)
        if not returns.empty:
            returns.to_excel(writer, sheet_name='Monthly Returns', index=False)
        if metrics:
            pd.DataFrame([metrics]).to_excel(writer, sheet_name='Performance Metrics', index=False)
        financials[['fyear','lifecycle']].to_excel(writer, sheet_name='Lifecycle', index=False)
    print(f"📁 Exported: {output_file}")

def export_clean_table(table, ticker):
    output_file = f'output/{ticker}_clean_table.xlsx'
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        table.to_excel(writer, sheet_name='Clean Data Table', index=False)
    print(f"📁 Exported: {output_file}")

# Main Execution
def main():
    print("\nPlease input query parameters")
    ticker = input("Stock Ticker (e.g., AAPL): ").upper().strip()
    start_year = int(input("Start Year: "))
    end_year = int(input("End Year: "))

    financials = get_company_financials(db, ticker, start_year, end_year)
    if financials.empty:
        print("❌ No financial data found")
        return

    financials['lifecycle'] = financials.apply(calculate_lifecycle, axis=1)
    print("\n📌 Lifecycle Stages:")
    for _, row in financials.iterrows():
        print(f"   {row['fyear']}: {row['lifecycle']}")

    returns = get_stock_returns(db, ticker, start_year, end_year)
    yearly_price = get_yearly_price(returns)
    clean_table = generate_clean_table(financials, yearly_price, ticker)

    metrics = calculate_metrics(returns)
    if metrics:
        print("\n📊 Performance Metrics:")
        for k, v in metrics.items():
            print(f"   {k}: {v}")

    plot_financial_trends(financials, ticker, start_year, end_year)
    plot_stock_performance(returns, ticker, start_year, end_year)
    export_to_excel(financials, returns, metrics, ticker)
    export_clean_table(clean_table, ticker)

    print("\n✅ Analysis completed successfully!")

if __name__ == "__main__":
    main()

# Close WRDS connection
db.close()
print("\n🔌 WRDS connection closed")

# AI Use Disclosure
# - Tools Used: DeepSeek, GitHub Copilot, 豆包 (Doubao)
# - Purpose: Code structure suggestions, function writing, plot formatting, notebook organisation, and explanation of financial analysis logic.
# - Access Date: 2026-04-17
# - Contribution: AI tools assisted with code optimisation, visualisation, and document structuring. All analytical logic, lifecycle design, project decisions, and financial interpretation are independently designed and verified by the student.