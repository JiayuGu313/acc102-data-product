# ACC102 Mini Assignment: Python Data Analysis Project
# Track 2 – GitHub Data Analysis Project
# Student ID: 2473457
# Student Name: Jiayu Gu
# Title: Single Stock Financial & Lifecycle Analysis Tool

import wrds
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def main():
    os.makedirs('output', exist_ok=True)
    plt.rcParams['axes.unicode_minus'] = False

    # ------------------------------------------------------------------------------
    # 🔥 WRDS Connection
    # ------------------------------------------------------------------------------
    print("=" * 60)
    print("Connecting to WRDS...")
    print("=" * 60)

    try:
        db = wrds.Connection(wrds_username="YOUR_WRDS_USERNAME")
        print("✅ WRDS connected successfully!")
    except Exception as e:
        print(f"❌ WRDS connection failed: {e}")
        print("Please check your username/password!")
        db = None

    # ------------------------------------------------------------------------------
    # Data Fetching
    # ------------------------------------------------------------------------------
    def get_company_financials(ticker, start_year, end_year):
        if db is None:
            return pd.DataFrame({
                'fyear': [], 'sale': [], 'at': [], 'ib': [],
                'oancf': [], 'invch': [], 'fincf': []
            })

        sql = f"""
        SELECT gvkey, tic, fyear, datadate, sale, at, ib, oancf, invch, fincf
        FROM comp.funda
        WHERE tic = '{ticker}'
        AND fyear BETWEEN {start_year} AND {end_year}
        AND indfmt = 'INDL' AND datafmt = 'STD' AND consol = 'C'
        ORDER BY fyear
        """
        data = db.raw_sql(sql)
        return data.fillna(0)

    def get_stock_returns(ticker, start_year, end_year):
        if db is None:
            return pd.DataFrame({'date': [], 'ret': [], 'prc': [], 'vol': []})

        sql = f"""
        SELECT a.date, a.ret, a.prc, a.vol
        FROM crsp.msf a
        JOIN crsp.msfhdr b ON a.permno = b.permno
        WHERE b.htsymbol = '{ticker}'
        AND a.date >= '{start_year}-01-01'
        AND a.date <= '{end_year}-12-31'
        ORDER BY a.date
        """
        data = db.raw_sql(sql)
        return data.fillna(0)

    # ------------------------------------------------------------------------------
    # Lifecycle Classification
    # ------------------------------------------------------------------------------
    def assign_lifecycle(df):
        if df.empty:
            return df

        stages = []
        for _, row in df.iterrows():
            o = row['oancf']
            i = row['invch']
            f = row['fincf']

            if o > 0 and i < 0 and f > 0:
                stages.append('Introduction')
            elif o > 0 and i < 0 and f < 0:
                stages.append('Growth')
            elif o < 0 and i > 0:
                stages.append('Decline')
            elif (o < 0 and i < 0) or (o > 0 and i > 0):
                stages.append('Shake-out')
            else:
                stages.append('Mature')
        df['lifecycle'] = stages
        return df

    # ------------------------------------------------------------------------------
    # Performance Metrics
    # ------------------------------------------------------------------------------
    def calculate_metrics(returns):
        if returns.empty or len(returns) < 12:
            return {}

        ret = returns['ret']
        ann_ret = ret.mean() * 12
        vol = ret.std() * np.sqrt(12) or 1
        sharpe = ann_ret / vol
        cum = (1 + ret).cumprod()
        max_dd = ((cum / cum.expanding().max()) - 1).min()
        win_rate = (ret > 0).mean()

        return {
            'Annual Return': f"{ann_ret:.2%}",
            'Annual Volatility': f"{vol:.2%}",
            'Sharpe Ratio': f"{sharpe:.2f}",
            'Max Drawdown': f"{max_dd:.2%}",
            'Win Rate': f"{win_rate:.2%}"
        }

    # ------------------------------------------------------------------------------
    # Enhanced Plotting with FULL English Labels, Titles, Axes
    # ------------------------------------------------------------------------------
    def plot_financial(fin, ticker):
        if fin.empty:
            return

        fig, ax = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle(f'Financial Performance of {ticker}', fontsize=16, fontweight='bold')

        # Revenue
        ax[0,0].plot(fin['fyear'], fin['sale'], 'o-', color='#1f77b4', linewidth=2, markersize=6)
        ax[0,0].set_title('Total Revenue', fontsize=12, fontweight='bold')
        ax[0,0].set_xlabel('Fiscal Year')
        ax[0,0].set_ylabel('Revenue (USD)')
        ax[0,0].grid(alpha=0.3)

        # Total Assets
        ax[0,1].plot(fin['fyear'], fin['at'], 'o-', color='#ff7f0e', linewidth=2, markersize=6)
        ax[0,1].set_title('Total Assets', fontsize=12, fontweight='bold')
        ax[0,1].set_xlabel('Fiscal Year')
        ax[0,1].set_ylabel('Assets (USD)')
        ax[0,1].grid(alpha=0.3)

        # Net Income
        ax[1,0].plot(fin['fyear'], fin['ib'], 'o-', color='#2ca02c', linewidth=2, markersize=6)
        ax[1,0].axhline(0, color='red', linestyle='--', linewidth=1.5)
        ax[1,0].set_title('Net Income', fontsize=12, fontweight='bold')
        ax[1,0].set_xlabel('Fiscal Year')
        ax[1,0].set_ylabel('Net Income (USD)')
        ax[1,0].grid(alpha=0.3)

        # Cash Flows
        ax[1,1].plot(fin['fyear'], fin['oancf'], 'o-', label='Operating Cash Flow', linewidth=2)
        ax[1,1].plot(fin['fyear'], fin['invch'], 'o-', label='Investing Cash Flow', linewidth=2)
        ax[1,1].plot(fin['fyear'], fin['fincf'], 'o-', label='Financing Cash Flow', linewidth=2)
        ax[1,1].set_title('Cash Flow Components', fontsize=12, fontweight='bold')
        ax[1,1].set_xlabel('Fiscal Year')
        ax[1,1].set_ylabel('Cash Flow (USD)')
        ax[1,1].legend()
        ax[1,1].grid(alpha=0.3)

        plt.tight_layout()
        plt.show()

    def plot_stock(returns, ticker):
        if returns.empty:
            return

        fig, ax = plt.subplots(2, 1, figsize=(14, 8))
        fig.suptitle(f'Stock Performance of {ticker}', fontsize=16, fontweight='bold')

        # Monthly Returns
        ax[0].bar(range(len(returns)), returns['ret'], color='#1f77b4', alpha=0.7)
        ax[0].set_title('Monthly Stock Returns', fontsize=12, fontweight='bold')
        ax[0].set_xlabel('Month Index')
        ax[0].set_ylabel('Monthly Return')
        ax[0].axhline(0, color='red', linestyle='--')
        ax[0].grid(alpha=0.3)

        # Cumulative Returns
        ax[1].plot((1 + returns['ret']).cumprod(), color='#ff7f0e', linewidth=2.5)
        ax[1].set_title('Cumulative Return', fontsize=12, fontweight='bold')
        ax[1].set_xlabel('Month Index')
        ax[1].set_ylabel('Cumulative Value')
        ax[1].grid(alpha=0.3)

        plt.tight_layout()
        plt.show()

    # ------------------------------------------------------------------------------
    # Main Program Execution
    # ------------------------------------------------------------------------------
    if db is None:
        print("❌ Cannot run without WRDS connection!")
        return

    ticker = input("Stock Ticker: ").upper()
    sy = int(input("Start Year: "))
    ey = int(input("End Year: "))

    fin = get_company_financials(ticker, sy, ey)
    if fin.empty:
        print("❌ No financial data found.")
        return

    fin = assign_lifecycle(fin)
    ret = get_stock_returns(ticker, sy, ey)
    metrics = calculate_metrics(ret)

    print("\n=== Lifecycle Stages ===")
    for _, r in fin.iterrows():
        print(f"{r.fyear}: {r.lifecycle}")

    print("\n=== Performance Metrics ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    plot_financial(fin, ticker)
    plot_stock(ret, ticker)

    # Close DB connection
    if db is not None:
        db.close()
        print("\n🔌 WRDS connection closed")

if __name__ == "__main__":
    main()
