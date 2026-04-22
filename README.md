# ACC102 Mini Assignment: Track4 - Interactive Stock Analysis Tool
## Streamlit Dual Stock & Industry Benchmark Analysis
**Student ID**: 2473457
**Student Name**: Jiayu Gu
**Product Title**: Interactive Financial Analysis Tool for Dual Stock Comparison & Industry Benchmarking

---

## 1. Project Overview
This interactive web application is built with Streamlit and Python, connecting to WRDS to provide real-time financial analysis for listed companies. It supports dual-stock comparison and industry benchmarking, automatically classifies firm lifecycle stages, calculates key financial ratios and stock performance metrics, and generates clear visualisations. The tool is designed for accounting/finance students, junior analysts, and investment enthusiasts to conduct efficient fundamental analysis.

## 2. Core Functions
### 📊 Dual Stock Comparison
- Compare financial performance between two stocks (e.g., AAPL vs MSFT)
- Automatically identify lifecycle stages: Growth / Mature / Decline
- Calculate ROA, Profit Margin, OCF Margin
- Compute Annual Return, Volatility, Sharpe Ratio
- Visualise trends in revenue, net income, operating cash flow, total assets
- Show cumulative stock return comparison

### 📈 Industry Benchmark
- Automatically identify industry based on SIC code
- Compare company performance with industry averages
- Key metrics: ROA, Profit Margin, Revenue Growth
- Bar chart for company vs industry comparison
- Outlier removal for reliable industry averages

## 3. How to Run
1. Install required packages:
pip install streamlit wrds pandas matplotlib numpy openpyxl
2. Run the app:
streamlit run app.py
3. Enter your WRDS username and password in the sidebar
4. Click Connect to WRDS
5. Choose page: Dual Stock Comparison or Industry Benchmark
6. Input tickers and year range, then run analysis

## 4. Data Source
- Database: WRDS (Wharton Research Data Services)
- Compustat (funda): Annual financial data
- CRSP (msf / msfhdr): Monthly stock returns and prices
- Company: SIC code for industry classification
- Access Date: 2026-04-17
- For educational use only

## 5. Methodology
### Lifecycle Classification
- Growth: Positive operating cash flow + Negative investing cash flow
- Decline: Negative operating cash flow
- Mature: Other conditions

### Financial Ratios
- ROA = Net Income / Total Assets
- Profit Margin = Net Income / Revenue
- OCF Margin = Operating Cash Flow / Revenue

### Performance Metrics
- Annual Return = Monthly mean return × 12
- Volatility = Monthly std × √12
- Sharpe Ratio = Annual Return / Volatility

## 6. AI Use Disclosure
- Tools Used: DeepSeek, GitHub Copilot, 豆包 (Doubao)
- Purpose: Code structure, Streamlit layout, WRDS query optimisation, plot design, logic refinement
- Access Date: 2026-04-17
- Contribution: AI assisted coding efficiency and formatting. All analytical logic, lifecycle design, and project decisions are independently developed and verified by the student.

## 7. Limitations
- Requires WRDS account
- Only supports US listed companies
- Industry classification uses 1-digit SIC code
- Static visualisations only

## 8. Future Improvements
- Add interactive Plotly charts
- Support quarterly data
- More precise industry classification
- Portfolio analysis mode
- Export to Excel / PDF
