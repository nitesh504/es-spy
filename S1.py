import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import time
from datetime import datetime, timedelta
import threading
import numpy as np
import altair as alt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page configuration
st.set_page_config(
    page_title="UTY CAPITAL ES-SPY Price Tracker",
    page_icon="📈",
    layout="wide",
)

# Initialize session state variables if they don't exist
if 'es_data' not in st.session_state:
    st.session_state.es_data = pd.DataFrame()
if 'spy_data' not in st.session_state:
    st.session_state.spy_data = pd.DataFrame()
if 'ratio_data' not in st.session_state:
    st.session_state.ratio_data = []
if 'timestamps' not in st.session_state:
    st.session_state.timestamps = []
if 'current_ratio' not in st.session_state:
    st.session_state.current_ratio = 10.0
if 'last_update' not in st.session_state:
    st.session_state.last_update = "Not updated yet"
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'es_change_pct' not in st.session_state:
    st.session_state.es_change_pct = 0.0
if 'spy_change_pct' not in st.session_state:
    st.session_state.spy_change_pct = 0.0
if 'ratio_change_pct' not in st.session_state:
    st.session_state.ratio_change_pct = 0.0

# Function to fetch data
def fetch_data():
    try:
        # Fetch ES data
        es_ticker = yf.Ticker("ES=F")
        es_data = es_ticker.history(period="1d", interval="1m")
        
        # Fetch SPY data
        spy_ticker = yf.Ticker("SPY")
        spy_data = spy_ticker.history(period="1d", interval="1m")
        
        if not es_data.empty and not spy_data.empty:
            # Get latest prices
            es_price = es_data["Close"].iloc[-1]
            spy_price = spy_data["Close"].iloc[-1]
            ratio = es_price / spy_price
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Update current ratio (for calculator)
            st.session_state.current_ratio = ratio
            
            # Store data
            st.session_state.es_data = pd.concat([st.session_state.es_data, es_data])
            st.session_state.spy_data = pd.concat([st.session_state.spy_data, spy_data])
            st.session_state.timestamps.append(timestamp)
            st.session_state.ratio_data.append(ratio)
            
            # Calculate changes
            if len(st.session_state.es_data) > 1:
                es_change = es_price - st.session_state.es_data["Close"].iloc[-2]
                st.session_state.es_change_pct = (es_change / st.session_state.es_data["Close"].iloc[-2]) * 100
            
            if len(st.session_state.spy_data) > 1:
                spy_change = spy_price - st.session_state.spy_data["Close"].iloc[-2]
                st.session_state.spy_change_pct = (spy_change / st.session_state.spy_data["Close"].iloc[-2]) * 100
            
            if len(st.session_state.ratio_data) > 1:
                ratio_change = ratio - st.session_state.ratio_data[-2]
                st.session_state.ratio_change_pct = (ratio_change / st.session_state.ratio_data[-2]) * 100
            
            # Limit data to last 100 points
            if len(st.session_state.timestamps) > 100:
                st.session_state.timestamps = st.session_state.timestamps[-100:]
                st.session_state.ratio_data = st.session_state.ratio_data[-100:]
            
            # Update last update time
            st.session_state.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return True
        else:
            return False
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return False

# Function to clear data
def clear_data():
    st.session_state.es_data = pd.DataFrame()
    st.session_state.spy_data = pd.DataFrame()
    st.session_state.ratio_data = []
    st.session_state.timestamps = []
    st.session_state.last_update = "Data cleared"
    st.session_state.es_change_pct = 0.0
    st.session_state.spy_change_pct = 0.0
    st.session_state.ratio_change_pct = 0.0

# Apply custom styles based on dark mode
def apply_styles():
    if st.session_state.dark_mode:
        # Dark mode styles
        st.markdown("""
        <style>
        .stApp {
            background-color: #2e2e2e;
            color: white;
        }
        .price-display {
            font-size: 32px;
            font-weight: bold;
            text-align: center;
        }
        .price-label {
            font-size: 18px;
            text-align: center;
        }
        .price-change {
            font-size: 16px;
            text-align: center;
        }
        .sidebar .sidebar-content {
            background-color: #3e3e3e;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Light mode styles
        st.markdown("""
        <style>
        .price-display {
            font-size: 32px;
            font-weight: bold;
            text-align: center;
        }
        .price-label {
            font-size: 18px;
            text-align: center;
        }
        .price-change {
            font-size: 16px;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

# Create plotly chart
def create_chart():
    if len(st.session_state.timestamps) > 0 and not st.session_state.es_data.empty and not st.session_state.spy_data.empty:
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add ES price trace
        es_data = st.session_state.es_data["Close"].iloc[-len(st.session_state.timestamps):]
        fig.add_trace(
            go.Scatter(
                x=st.session_state.timestamps, 
                y=es_data, 
                name="ES",
                line=dict(color="blue", width=2)
            ),
            secondary_y=False,
        )
        
        # Add SPY price trace
        spy_data = st.session_state.spy_data["Close"].iloc[-len(st.session_state.timestamps):]
        fig.add_trace(
            go.Scatter(
                x=st.session_state.timestamps, 
                y=spy_data, 
                name="SPY",
                line=dict(color="green", width=2)
            ),
            secondary_y=False,
        )
        
        # Add ratio trace on secondary y-axis
        fig.add_trace(
            go.Scatter(
                x=st.session_state.timestamps, 
                y=st.session_state.ratio_data, 
                name="Ratio",
                line=dict(color="red", width=1.5)
            ),
            secondary_y=True,
        )
        
        # Set titles
        fig.update_layout(
            title_text="ES-SPY Price and Ratio Over Time",
            title_font_size=16,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=400,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#f5f5f5" if not st.session_state.dark_mode else "#3e3e3e",
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text="Price ($)", secondary_y=False)
        fig.update_yaxes(title_text="Ratio", secondary_y=True)
        
        # Update grid and font colors for dark mode
        if st.session_state.dark_mode:
            fig.update_layout(
                font_color="white",
                xaxis=dict(gridcolor="#555555"),
                yaxis=dict(gridcolor="#555555"),
            )
        
        return fig
    return None

# Main application
def main():
    apply_styles()
    
    # Header
    st.title("UTY CAPITAL ES-SPY Real-Time Tracker")
    
    # Control row with buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        refresh_button = st.button("Refresh Data", key="refresh")
        if refresh_button:
            with st.spinner("Fetching data..."):
                success = fetch_data()
                if success:
                    st.success("Data updated successfully!")
                else:
                    st.error("Failed to fetch data")
    
    with col2:
        clear_button = st.button("Clear Data", key="clear")
        if clear_button:
            clear_data()
            st.success("Data cleared successfully!")
    
    with col3:
        theme_toggle = st.toggle("Dark Mode", key="toggle_theme")
        if theme_toggle != st.session_state.dark_mode:
            st.session_state.dark_mode = theme_toggle
            st.rerun()  # Changed from st.experimental_rerun()
    
    with col4:
        auto_refresh = st.checkbox("Auto Refresh (5s)", value=False, key="auto_refresh")
    
    # Display last update time
    st.caption(f"Last update: {st.session_state.last_update}")
    
    # Price display section
    price_cols = st.columns(3)
    
    # ES price
    with price_cols[0]:
        st.markdown("<p class='price-label'>ES Futures</p>", unsafe_allow_html=True)
        if not st.session_state.es_data.empty:
            es_price = st.session_state.es_data["Close"].iloc[-1]
            st.markdown(f"<p class='price-display'>{es_price:.2f}</p>", unsafe_allow_html=True)
            
            color = "green" if st.session_state.es_change_pct >= 0 else "red"
            st.markdown(f"<p class='price-change' style='color:{color};'>({st.session_state.es_change_pct:+.2f}%)</p>", 
                        unsafe_allow_html=True)
        else:
            st.markdown("<p class='price-display'>--</p>", unsafe_allow_html=True)
            st.markdown("<p class='price-change'>--</p>", unsafe_allow_html=True)
    
    # SPY price
    with price_cols[1]:
        st.markdown("<p class='price-label'>SPY ETF</p>", unsafe_allow_html=True)
        if not st.session_state.spy_data.empty:
            spy_price = st.session_state.spy_data["Close"].iloc[-1]
            st.markdown(f"<p class='price-display'>{spy_price:.2f}</p>", unsafe_allow_html=True)
            
            color = "green" if st.session_state.spy_change_pct >= 0 else "red"
            st.markdown(f"<p class='price-change' style='color:{color};'>({st.session_state.spy_change_pct:+.2f}%)</p>", 
                        unsafe_allow_html=True)
        else:
            st.markdown("<p class='price-display'>--</p>", unsafe_allow_html=True)
            st.markdown("<p class='price-change'>--</p>", unsafe_allow_html=True)
    
    # Ratio
    with price_cols[2]:
        st.markdown("<p class='price-label'>ES/SPY Ratio</p>", unsafe_allow_html=True)
        if len(st.session_state.ratio_data) > 0:
            ratio = st.session_state.ratio_data[-1]
            st.markdown(f"<p class='price-display'>{ratio:.4f}</p>", unsafe_allow_html=True)
            
            color = "green" if st.session_state.ratio_change_pct >= 0 else "red"
            st.markdown(f"<p class='price-change' style='color:{color};'>({st.session_state.ratio_change_pct:+.2f}%)</p>", 
                        unsafe_allow_html=True)
        else:
            st.markdown("<p class='price-display'>--</p>", unsafe_allow_html=True)
            st.markdown("<p class='price-change'>--</p>", unsafe_allow_html=True)
    
    # Add separator
    st.markdown("---")
    
    # Chart section
    chart_fig = create_chart()
    if chart_fig:
        st.plotly_chart(chart_fig, use_container_width=True)
    else:
        st.info("No data available for chart. Please refresh to fetch data.")
    
    # Price Calculator section
    st.subheader("Price Calculator")
    
    calc_cols = st.columns(2)
    
    # Left side - ES to SPY calculator
    with calc_cols[0]:
        st.markdown("### Calculate SPY from ES")
        es_price_input = st.number_input("ES Price:", min_value=0.0, step=0.01, format="%.2f", key="es_input")
        
        if st.button("Calculate SPY", key="calc_spy"):
            if st.session_state.current_ratio > 0:
                spy_price = es_price_input / st.session_state.current_ratio
                st.success(f"Calculated SPY Price: ${spy_price:.2f}")
            else:
                st.error("Cannot calculate: Current ratio is not available")
    
    # Right side - SPY to ES calculator
    with calc_cols[1]:
        st.markdown("### Calculate ES from SPY")
        spy_price_input = st.number_input("SPY Price:", min_value=0.0, step=0.01, format="%.2f", key="spy_input")
        
        if st.button("Calculate ES", key="calc_es"):
            if st.session_state.current_ratio > 0:
                es_price = spy_price_input * st.session_state.current_ratio
                st.success(f"Calculated ES Price: ${es_price:.2f}")
            else:
                st.error("Cannot calculate: Current ratio is not available")
    
    # Custom ratio input
    st.markdown("### Custom Ratio")
    custom_ratio_cols = st.columns([2, 2, 1])
    
    with custom_ratio_cols[0]:
        use_current_ratio = st.checkbox("Use current market ratio", value=True, key="use_current")
    
    with custom_ratio_cols[1]:
        custom_ratio = st.number_input(
            "Custom Ratio:",
            min_value=0.1,
            max_value=100.0,
            value=float(st.session_state.current_ratio if st.session_state.current_ratio > 0 else 10.0),
            step=0.0001,
            format="%.4f",
            key="custom_ratio",
            disabled=use_current_ratio
        )
    
    # Status bar at the bottom
    st.markdown("---")
    status_text = "Updating every 5 seconds..." if st.session_state.auto_refresh else "Manual update mode"
    st.caption(status_text)
    
    # Auto refresh logic
    if st.session_state.auto_refresh:
        time.sleep(5)
        fetch_data()
        st.rerun()  # Changed from st.experimental_rerun()

if __name__ == "__main__":
    main()