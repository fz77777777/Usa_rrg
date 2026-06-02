import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# Premium Responsive Dashboard Configuration
st.set_page_config(
    page_title="US Market Sector RRG Pro", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark UI Accent & Padding Optimization
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    h1 { font-weight: 800; color: #0F172A; letter-spacing: -1px; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; padding: 10px 20px; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 Institutional Sector Rotation (RRG Dashboard)")
st.caption("⚡ Direct Ticker-on-Line Asset Engine | Benchmark: SPY (S&P 500)")

def calculate_rrg(tickers, benchmark, interval, window=14, tail_length=5):
    if interval == '60m':
        period = '1mo'
    elif interval == '1d':
        period = '1y'
    elif interval == '1wk':
        period = '2y'
    else:
        period = 'max'

    all_tickers = list(tickers.keys()) + [benchmark]
    data = yf.download(all_tickers, period=period, interval=interval, progress=False)
    
    if data.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    if 'Close' in data.columns:
        data = data['Close']
        
    data = data.ffill().bfill()
    valid_tickers = [t for t in tickers.keys() if t in data.columns and not data[t].isna().all()]
    
    if not valid_tickers or benchmark not in data.columns:
        return pd.DataFrame(), pd.DataFrame()
    
    rs_ratios = pd.DataFrame()
    for t in valid_tickers:
        rs_ratios[t] = (data[t] / data[benchmark]) * 100
        
    if rs_ratios.shape[0] < (window * 2):
        return pd.DataFrame(), pd.DataFrame()
        
    rs_ratio_smoothed = rs_ratios.ewm(span=window, adjust=False).mean()
    mean_rs = rs_ratio_smoothed.rolling(window=window).mean()
    std_rs = rs_ratio_smoothed.rolling(window=window).std()
    jdk_rs_ratio = 100 + ((rs_ratio_smoothed - mean_rs) / std_rs) * 10
    
    rs_momentum = rs_ratio_smoothed.pct_change(periods=window) * 100
    rs_mom_smoothed = rs_momentum.ewm(span=window, adjust=False).mean()
    mean_mom = rs_mom_smoothed.rolling(window=window).mean()
    std_mom = rs_mom_smoothed.rolling(window=window).std()
    jdk_rs_momentum = 100 + ((rs_mom_smoothed - mean_mom) / std_mom) * 10
    
    return jdk_rs_ratio.dropna().tail(tail_length), jdk_rs_momentum.dropna().tail(tail_length)

def plot_rrg_labeled(jdk_rs_ratio, jdk_rs_momentum, tickers):
    # CRITICAL CRASH GUARD: Agar data empty hai, toh yahan se turant safe exit karo
    if jdk_rs_ratio.empty or jdk_rs_momentum.empty or len(jdk_rs_ratio.columns) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="⚠️ US Market Data Currently Unavailable.<br>Please click 'Reload Canvas' or wait for live feed.", 
            showarrow=False, 
            font=dict(size=16, color="#64748B")
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='white',
            height=400
        )
        return fig
        
    fig = go.Figure()
    
    # Grid Padding Matrix
    all_x = jdk_rs_ratio.values.flatten()
    all_y = jdk_rs_momentum.values.flatten()
    
    # Extra safety for handling non-numeric/empty slices
    if len(all_x) == 0 or len(all_y) == 0:
        max_pad = 5.0
    else:
        max_pad = max(abs(all_x.max() - 100), abs(100 - all_x.min()), abs(all_y.max() - 100), abs(100 - all_y.min())) + 1.5
    
    x_range = [100 - max_pad, 100 + max_pad]
    y_range = [100 - max_pad, 100 + max_pad]
    
    # Quadrant Visual Shading
    fig.add_shape(type="rect", x
