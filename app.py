import streamlit as st
import wrds
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# --------------------------
# Page config
# --------------------------
st.set_page_config(page_title="Stock Analysis Tool", layout="wide")

# --------------------------
# SIDEBAR NAVIGATION
# --------------------------
with st.sidebar:
    st.title("🔍 Navigation")

    if "page" not in st.session_state:
        st.session_state.page = "Dual Stock"

    if st.button("📊 Dual Stock Comparison", use_container_width=True):
        st.session_state.page = "Dual Stock"

    if st.button("📈 Industry Benchmark", use_container_width=True):
        st.session_state.page = "Industry Benchmark"

    st.divider()

    st.header("WRDS Connection")
    wrds_username = st.text_input("WRDS Username", placeholder="Enter your WRDS username")
    wrds_password = st.text_input("WRDS Password", type="password", placeholder="Enter your WRDS password")

    if st.button("Connect to WRDS", use_container_width=True):
        try:
            db = wrds.Connection(wrds_username=wrds_username, wrds_password=wrds_password)
            st.session_state["db"] = db
            st.success("✅ Connected")
        except Exception as e:
            st.error("❌ Connection failed")
            st.session_state["db"] = None

db = st.session_state.get("db", None)

# --------------------------
# Get Industry Name
# --------------------------
def get_industry_name_from_sic(db, ticker):
    try:
        gvkey_df = db.raw_sql(f"SELECT gvkey FROM comp.funda WHERE tic='{ticker}' LIMIT 1")
        if gvkey_df.empty:
            return "Industry"
        gvkey = gvkey_df.iloc[0,0]

        sic_df = db.raw_sql(f"SELECT sic FROM comp.company WHERE gvkey='{gvkey}'")
        if sic_df.empty or pd.isna(sic_df.iloc[0,0]):
            return "Industry"
        
        sic = int(sic_df.iloc[0,0])
        sic1 = str(sic)[0]

        sic_map = {
            "0": "Agriculture",
            "1": "Mining",
            "2": "Construction",
            "3": "Manufacturing",
            "4": "Transportation",
            "5": "Wholesale & Retail",
            "6": "Finance",
            "7": "Services",
            "8": "Services",
            "9": "Public Administration"
        }
        return sic_map.get(sic1, "Industry")
    except:
        return "Industry"

# --------------------------
# Shared Functions
# --------------------------
def get_year_range(db, ticker):
    if db is None:
        return 2010, 2025
    sql = f"""
    SELECT MIN(fyear) as min_year, MAX(fyear) as max_year
    FROM comp.funda
    WHERE tic = '{ticker}'
    AND indfmt = 'INDL' AND datafmt = 'STD' AND consol = 'C'
    """
    df = db.raw_sql(sql)
    if df.empty:
        return 2010, 2025
    min_year = int(df.iloc[0]['min_year'])
    max_year = int(df.iloc[0]['max_year'])
    return min_year, max_year

def get_company_financials(db, ticker, start_year, end_year):
    if db is None:
        return pd.DataFrame()
    sql = f"""
    SELECT gvkey, tic, fyear, datadate, sale, at, ib, oancf, invch
    FROM comp.funda
    WHERE tic = '{ticker}'
    AND fyear BETWEEN {start_year} AND {end_year}
    AND indfmt = 'INDL' AND datafmt = 'STD' AND consol = 'C'
    AND sale > 10
    ORDER BY fyear
    """
    data = db.raw_sql(sql)
    return data.fillna(0)

def get_stock_returns(db, ticker, start_year, end_year):
    if db is None:
        return pd.DataFrame()
    sql = f"""
    SELECT a.date, a.ret, a.prc
    FROM crsp.msf a
    JOIN crsp.msfhdr b ON a.permno = b.permno
    WHERE b.htsymbol = '{ticker}'
    AND a.date >= '{start_year}-01-01'
    AND a.date <= '{end_year}-12-31'
    ORDER BY a.date
    """
    return db.raw_sql(sql).fillna(0)

def assign_lifecycle(df):
    if df.empty:
        return df
    stages = []
    for _, row in df.iterrows():
        o = row['oancf']
        inv = row['invch']
        if o > 0 and inv < 0:
            stages.append("Growth")
        elif o < 0:
            stages.append("Decline")
        else:
            stages.append("Mature")
    df['lifecycle'] = stages
    return df

def compute_ratios(df):
    df = df.copy()
    df['Profit_Margin'] = np.where(df['sale'] != 0, df['ib'] / df['sale'], 0)
    df['ROA'] = np.where(df['at'] != 0, df['ib'] / df['at'], 0)
    df['OCF_Margin'] = np.where(df['sale'] != 0, df['oancf'] / df['sale'], 0)
    return df

def calculate_metrics(returns):
    if returns.empty or len(returns) < 12:
        return {}
    ret = returns['ret']
    ann_ret = ret.mean() * 12
    vol = ret.std() * np.sqrt(12) or 1
    sharpe = ann_ret / vol if vol != 0 else 0
    return {
        'Annual Return': f"{ann_ret:.2%}",
        'Volatility': f"{vol:.2%}",
        'Sharpe Ratio': f"{sharpe:.2f}",
    }

def plot_comparison(fin1, fin2, ticker1, ticker2):
    fig, ax = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(f'Comparison: {ticker1} vs {ticker2}', fontsize=16, weight='bold')

    ax[0,0].plot(fin1['fyear'], fin1['sale'], 'o-', label=ticker1)
    ax[0,0].plot(fin2['fyear'], fin2['sale'], 'o-', label=ticker2)
    ax[0,0].set_title('Revenue')
    ax[0,0].legend()
    ax[0,0].grid(alpha=0.3)

    ax[0,1].plot(fin1['fyear'], fin1['ib'], 'o-', label=ticker1)
    ax[0,1].plot(fin2['fyear'], fin2['ib'], 'o-', label=ticker2)
    ax[0,1].set_title('Net Income')
    ax[0,1].legend()
    ax[0,1].grid(alpha=0.3)

    ax[1,0].plot(fin1['fyear'], fin1['oancf'], 'o-', label=ticker1)
    ax[1,0].plot(fin2['fyear'], fin2['oancf'], 'o-', label=ticker2)
    ax[1,0].set_title('Operating Cash Flow')
    ax[1,0].legend()
    ax[1,0].grid(alpha=0.3)

    ax[1,1].plot(fin1['fyear'], fin1['at'], 'o-', label=ticker1)
    ax[1,1].plot(fin2['fyear'], fin2['at'], 'o-', label=ticker2)
    ax[1,1].set_title('Total Assets')
    ax[1,1].legend()
    ax[1,1].grid(alpha=0.3)
    plt.tight_layout()
    return fig

def plot_cum_return(ret1, ret2, t1, t2):
    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot((1 + ret1['ret']).cumprod(), label=t1)
    ax.plot((1 + ret2['ret']).cumprod(), label=t2)
    ax.set_title("Cumulative Stock Return")
    ax.legend()
    ax.grid(alpha=0.3)
    return fig

# --------------------------
# Industry averages without outliers
# --------------------------
def get_industry_averages(db, ticker, sy, ey):
    try:
        gvkey_df = db.raw_sql(f"SELECT gvkey FROM comp.funda WHERE tic='{ticker}' LIMIT 1")
        if gvkey_df.empty:
            return 6.0, 8.0, 5.0
        gvkey = gvkey_df.iloc[0,0]

        sic_df = db.raw_sql(f"SELECT sic FROM comp.company WHERE gvkey='{gvkey}'")
        if sic_df.empty or pd.isna(sic_df.iloc[0,0]):
            return 6.0, 8.0, 5.0

        sic = str(int(sic_df.iloc[0,0]))[:1]

        sql = f"""
        WITH ind AS (
            SELECT
                gvkey,
                fyear,
                ib,
                at,
                sale,
                (sale - LAG(sale) OVER (PARTITION BY gvkey ORDER BY fyear))
                / NULLIF(LAG(sale) OVER (PARTITION BY gvkey ORDER BY fyear), 0) * 100 AS growth
            FROM comp.funda
            WHERE indfmt='INDL' AND datafmt='STD'
              AND sale > 100
              AND at > 100
              AND ib BETWEEN -1e10 AND 1e10
        )
        SELECT
            AVG(ib / NULLIF(at,0))*100 AS roa,
            AVG(ib / NULLIF(sale,0))*100 AS pm,
            AVG(growth) AS growth
        FROM ind i
        JOIN comp.company c ON i.gvkey = c.gvkey
        WHERE SUBSTRING(CAST(c.sic AS TEXT),1,1) = '{sic}'
        AND i.fyear BETWEEN {sy} AND {ey}
        AND ABS(ib / NULLIF(sale, 0)) < 5
        AND ABS(ib / NULLIF(at, 0)) < 1
        """
        df = db.raw_sql(sql)
        roa = df.iloc[0,0]
        pm = df.iloc[0,1]
        growth = df.iloc[0,2]

        roa = roa if not pd.isna(roa) else 6.0
        pm = pm if not pd.isna(pm) else 8.0
        growth = growth if not pd.isna(growth) else 5.0
        return roa, pm, growth

    except:
        return 6.0, 8.0, 5.0

# Fixed title: Company name vs Industry
def plot_industry_benchmark(comp, ind, labels, company_name, industry_name):
    fig, ax = plt.subplots(figsize=(10,5))
    x = np.arange(len(labels))
    ax.bar(x-0.2, comp, 0.4, label=company_name)
    ax.bar(x+0.2, ind, 0.4, label="Industry") 
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title(f"{company_name} vs Industry")  
    ax.legend()
    ax.grid(alpha=0.3)
    return fig

# ============================================================
# PAGE 1
# ============================================================
if st.session_state.page == "Dual Stock":
    st.title("Single Stock Financial & Lifecycle Analysis Tool")
    st.header("Dual Stock Comparison")

    col1, col2 = st.columns(2)
    with col1:
        ticker1 = st.text_input("Stock 1", "AAPL").upper()
    with col2:
        ticker2 = st.text_input("Stock 2", "MSFT").upper()

    if db:
        my1, mx1 = get_year_range(db, ticker1)
        my2, mx2 = get_year_range(db, ticker2)
    else:
        my1, mx1, my2, mx2 = 2010,2025,2010,2025

    min_year = max(my1, my2)
    max_year = min(mx1, mx2)

    sy = st.number_input("Start Year", 1950, 2030, min_year)
    ey = st.number_input("End Year", sy, 2030, max_year)

    if st.button("Run Analysis", use_container_width=True):
        if not db:
            st.error("Connect WRDS first")
            st.stop()

        f1 = get_company_financials(db, ticker1, sy, ey)
        f2 = get_company_financials(db, ticker2, sy, ey)
        r1 = get_stock_returns(db, ticker1, sy, ey)
        r2 = get_stock_returns(db, ticker2, sy, ey)

        f1 = assign_lifecycle(f1)
        f2 = assign_lifecycle(f2)
        fr1 = compute_ratios(f1)
        fr2 = compute_ratios(f2)
        m1 = calculate_metrics(r1)
        m2 = calculate_metrics(r2)

        st.subheader("Lifecycle")
        c1, c2 = st.columns(2)
        c1.dataframe(f1[['fyear','lifecycle']])
        c2.dataframe(f2[['fyear','lifecycle']])

        st.subheader("Financial Ratios")
        st.dataframe(pd.DataFrame({
            'Metric': ['ROA', 'Profit Margin', 'OCF Margin'],
            ticker1: [f"{fr1['ROA'].mean():.2%}", f"{fr1['Profit_Margin'].mean():.2%}", f"{fr1['OCF_Margin'].mean():.2%}"],
            ticker2: [f"{fr2['ROA'].mean():.2%}", f"{fr2['Profit_Margin'].mean():.2%}", f"{fr2['OCF_Margin'].mean():.2%}"]
        }))

        st.subheader("Performance Metrics")
        st.dataframe(pd.DataFrame([m1, m2], index=[ticker1, ticker2]))

        st.subheader("Financial Trends")
        st.pyplot(plot_comparison(f1, f2, ticker1, ticker2))

        st.subheader("Stock Return")
        st.pyplot(plot_cum_return(r1, r2, ticker1, ticker2))

# ============================================================
# PAGE 2
# ============================================================
if st.session_state.page == "Industry Benchmark":
    st.title("📊 Industry Benchmark")
    tgt = st.text_input("Company Ticker", "GOOGL").upper()

    if db:
        ymin, ymax = get_year_range(db, tgt)
        ind_name = get_industry_name_from_sic(db, tgt)
    else:
        ymin, ymax = 2010, 2025
        ind_name = "Industry"

    sy = st.number_input("Start Year", 1950, 2030, ymin)
    ey = st.number_input("End Year", sy, 2030, ymax)

    if st.button("Compare with Industry", use_container_width=True):
        if not db:
            st.error("Connect WRDS first")
            st.stop()

        df = get_company_financials(db, tgt, sy, ey)
        if df.empty:
            st.warning("No data")
            st.stop()

        fr = compute_ratios(df)
        c_roa = fr['ROA'].mean() * 100
        c_pm = fr['Profit_Margin'].mean() * 100

        sale_clean = df['sale'].replace(0, np.nan)
        c_growth = sale_clean.pct_change().mean() * 100
        c_growth = 0 if pd.isna(c_growth) else c_growth

        i_roa, i_pm, i_growth = get_industry_averages(db, tgt, sy, ey)

        c_roa = 0 if pd.isna(c_roa) else c_roa
        c_pm = 0 if pd.isna(c_pm) else c_pm
        i_roa = 0 if pd.isna(i_roa) else i_roa
        i_pm = 0 if pd.isna(i_pm) else i_pm
        i_growth = 0 if pd.isna(i_growth) else i_growth

        st.dataframe(pd.DataFrame({
            "Metric": ["ROA (%)", "Profit Margin (%)", "Revenue Growth (%)"],
            tgt: [round(c_roa,2), round(c_pm,2), round(c_growth,2)],
            ind_name: [round(i_roa,2), round(i_pm,2), round(i_growth,2)]
        }))

        st.pyplot(plot_industry_benchmark(
            [c_roa, c_pm, c_growth],
            [i_roa, i_pm, i_growth],
            ["ROA", "Profit Margin", "Growth"],
            tgt, ind_name
        ))