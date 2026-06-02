import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# Premium Responsive Config
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

def plot_rrg_labeled(jdk_rs_ratio, jdk_rs_momentum, tickers, title):
    if jdk_rs_ratio.empty or jdk_rs_momentum.empty:
        fig = go.Figure()
        fig.add_annotation(text="No operational data available.", showarrow=False, font=dict(size=16))
        return fig
        
    fig = go.Figure()
    
    # Grid Padding Matrix
    all_x = jdk_rs_ratio.values.flatten()
    all_y = jdk_rs_momentum.values.flatten()
    max_pad = max(abs(all_x.max() - 100), abs(100 - all_x.min()), abs(all_y.max() - 100), abs(100 - all_y.min())) + 1.5
    
    x_range = [100 - max_pad, 100 + max_pad]
    y_range = [100 - max_pad, 100 + max_pad]
    
    # Quadrant Visual Shading
    fig.add_shape(type="rect", x0=100, y0=100, x1=100+max_pad, y1=100+max_pad, fillcolor="rgba(34,197,94,0.03)", line_width=0)
    fig.add_shape(type="rect", x0=100, y0=100-max_pad, x1=100+max_pad, y1=100, fillcolor="rgba(234,179,8,0.03)", line_width=0)
    fig.add_shape(type="rect", x0=100-max_pad, y0=100-max_pad, x1=100, y1=100, fillcolor="rgba(239,68,68,0.03)", line_width=0)
    fig.add_shape(type="rect", x0=100-max_pad, y0=100, x1=100, y1=100+max_pad, fillcolor="rgba(59,130,246,0.03)", line_width=0)
    
    # Crosshairs
    fig.add_shape(type="line", x0=100, y0=100-max_pad, x1=100, y1=100+max_pad, line=dict(color="rgba(148,163,184,0.5)", width=1.5, dash="dash"))
    fig.add_shape(type="line", x0=100-max_pad, y0=100, x1=100+max_pad, y1=100, line=dict(color="rgba(148,163,184,0.5)", width=1.5, dash="dash"))
    
    # Plotting Channels with Inline Ticker Embeds
    for col in jdk_rs_ratio.columns:
        x_vals = jdk_rs_ratio[col].values
        y_vals = jdk_rs_momentum[col].values
        
        # Line + Markers mapping
        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals,
            mode='lines+markers',
            name=tickers.get(col, col), # Top legend me full descriptive name rahega
            line=dict(width=3),
            marker=dict(
                size=[5]*(len(x_vals)-1) + [14],
                symbol=['circle']*(len(x_vals)-1) + ['triangle-up'],
                line=dict(width=1, color="white")
            ),
            hovertemplate=f"<b>{tickers.get(col,col)}</b><br>RS Ratio: %{{x:.2f}}<br>RS Momentum: %{{y:.2f}}<extra></extra>"
        ))
        
        # PERMANENT ON-LINE TICKER EMBEDDING (No collision padding)
        fig.add_annotation(
            x=x_vals[-1],
            y=y_vals[-1],
            text=f"<b>{col}</b>", # Sirf core code (XLK, XLE, XLF) line par dikhega
            showarrow=False,
            xshift=14,
            yshift=6,
            font=dict(size=12, color="#0F172A", family="Arial Black"),
            bgcolor="rgba(255, 255, 255, 0.85)",
            bordercolor="rgba(148,163,184,0.3)",
            borderpad=2,
            borderwidth=1,
            align="center"
        )
            
    # Quadrant Floating Headers
    fig.add_annotation(x=100+max_pad*0.75, y=100+max_pad*0.88, text="🟩 LEADING", font=dict(color="#16a34a", size=14, weight="bold"), showarrow=False)
    fig.add_annotation(x=100+max_pad*0.75, y=100-max_pad*0.88, text="🟨 WEAKENING", font=dict(color="#ca8a04", size=14, weight="bold"), showarrow=False)
    fig.add_annotation(x=100-max_pad*0.75, y=100-max_pad*0.88, text="🟥 LAGGING", font=dict(color="#dc2626", size=14, weight="bold"), showarrow=False)
    fig.add_annotation(x=100-max_pad*0.75, y=100+max_pad*0.88, text="🟦 IMPROVING", font=dict(color="#2563eb", size=14, weight="bold"), showarrow=False)
    
    # Viewport Geometry
    fig.update_layout(
        xaxis_title="👉 Trend Strength (RS Ratio)",
        yaxis_title="🚀 Sector Velocity (RS Momentum)",
        xaxis=dict(range=x_range, gridcolor="rgba(241,245,249,1)", zeroline=False),
        yaxis=dict(range=y_range, gridcolor="rgba(241,245,249,1)", zeroline=False),
        height=800, # Large View Setup
        margin=dict(l=20, r=30, t=30, b=20),
        plot_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# Pure Data Nodes
us_sectors = {
    'XLK': 'XLK (Technology)', 'XLY': 'XLY (Consumer Disc)', 'XLP': 'XLP (Consumer Staples)',
    'XLF': 'XLF (Financials)', 'XLV': 'XLV (Healthcare)', 'XLE': 'XLE (Energy)',
    'XLI': 'XLI (Industrials)', 'XLB': 'XLB (Materials)', 'XLU': 'XLU (Utilities)',
    'XLRE': 'XLRE (Real Estate)', 'XLC': 'XLC (Communication)'
}
us_benchmark = 'SPY'

# Sidebar Controls
st.sidebar.header("⚙️ Configuration")
tail = st.sidebar.slider("Tail Length (History)", min_value=3, max_value=15, value=5)

if st.sidebar.button("🔄 Reload Canvas", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Processing Tabs
t1, t2, t3, t4 = st.tabs(["📊 Hourly View", "📈 Daily Matrix", "📆 Weekly Rotation", "⏳ Monthly Macro"])

with t1:
    r, m = calculate_rrg(us_sectors, us_benchmark, '60m', tail_length=tail)
    st.plotly_chart(plot_rrg_labeled(r, m, us_sectors), use_container_width=True)

with t2:
    r, m = calculate_rrg(us_sectors, us_benchmark, '1d', tail_length=tail)
    st.plotly_chart(plot_rrg_labeled(r, m, us_sectors), use_container_width=True)

with t3:
    r, m = calculate_rrg(us_sectors, us_benchmark, '1wk', tail_length=tail)
    st.plotly_chart(plot_rrg_labeled(r, m, us_sectors), use_container_width=True)

with t4:
    r, m = calculate_rrg(us_sectors, us_benchmark, '1mo', tail_length=tail)
    st.plotly_chart(plot_rrg_labeled(r, m, us_sectors), use_container_width=True)
