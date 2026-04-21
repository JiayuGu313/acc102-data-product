# ACC102 Mini Assignment: Python Data Product
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
    # 基础设置
    os.makedirs('output', exist_ok=True)
    plt.rcParams['axes.unicode_minus'] = False

    # ------------------------------------------------------------------------------
    # 🔥 兼容所有环境的 WRDS 连接（必须手动输入账号密码！）
    # ------------------------------------------------------------------------------
    print("=" * 60)
    print("Connecting to WRDS...")
    print("=" * 60)

    try:
        db = wrds.Connection(wrds_username="YOUR_WRDS_USERNAME")  # 必须写你的WRDS用户名
        print("✅ WRDS connected successfully!")
    except Exception as e:
        print(f"❌ WRDS connection failed: {e}")
        print("Please check your username/password!")
        db = None

    # ------------------------------------------------------------------------------
    # 数据获取（空值全部填 0）
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
    # 🔥 绝对不报错的生命周期判断
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
    # 计算指标
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
    # 绘图（修复了 .at 冲突）
    # ------------------------------------------------------------------------------
    def plot_financial(fin, ticker):
        if fin.empty:
            return

        fig, ax = plt.subplots(2, 2, figsize=(14, 8))
        ax[0,0].plot(fin['fyear'], fin['sale'], 'o-')
        ax[0,0].set_title("Revenue")
        ax[0,1].plot(fin['fyear'], fin['at'], 'o-')
        ax[0,1].set_title("Total Assets")
        ax[1,0].plot(fin['fyear'], fin['ib'], 'o-')
        ax[1,0].axhline(0, color='r')
        ax[1,0].set_title("Net Income")
        ax[1,1].plot(fin['fyear'], fin['oancf'], label='OCF')
        ax[1,1].plot(fin['fyear'], fin['invch'], label='ICF')
        ax[1,1].plot(fin['fyear'], fin['fincf'], label='FCF')
        ax[1,1].legend()
        plt.tight_layout()
        plt.show()

    def plot_stock(returns):
        if returns.empty:
            return

        fig, ax = plt.subplots(2, 1, figsize=(12, 6))
        ax[0].bar(range(len(returns)), returns['ret'])
        ax[1].plot((1 + returns['ret']).cumprod())
        plt.tight_layout()
        plt.show()

    # ------------------------------------------------------------------------------
    # 主程序执行逻辑
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
    plot_stock(ret)

    # 关闭数据库连接
    if db is not None:
        db.close()
        print("\n🔌 WRDS connection closed")

if __name__ == "__main__":
    main()
