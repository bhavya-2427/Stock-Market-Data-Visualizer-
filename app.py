import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# ----------------------------
# App Title
# ----------------------------
st.title("📊 Stock Market Data Visualizer Dashboard")

# ----------------------------
# Sidebar Inputs
# ----------------------------
st.sidebar.header("Stock Settings")
tickers = st.sidebar.text_input("Enter Stock Symbols (comma separated)", "AAPL, MSFT").upper().split(",")

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

show_indicators = st.sidebar.multiselect(
    "Select Indicators",
    ["20-Day MA", "50-Day MA", "RSI", "Bollinger Bands"],
    default=["20-Day MA", "50-Day MA"]
)

# ----------------------------
# Fetch Data
# ----------------------------
@st.cache_data
def load_data(ticker, start, end):
    return yf.download(ticker, start=start, end=end)

# Loop through multiple tickers
for ticker in tickers:
    st.subheader(f"📈 {ticker} Stock Data")

    data = load_data(ticker.strip(), start_date, end_date)

    if data.empty:
        st.warning(f"No data found for {ticker}")
        continue

    # ----------------------------
    # Indicators
    # ----------------------------
    if "20-Day MA" in show_indicators:
        data["MA20"] = data["Close"].rolling(20).mean()
    if "50-Day MA" in show_indicators:
        data["MA50"] = data["Close"].rolling(50).mean()
    if "RSI" in show_indicators:
        delta = data["Close"].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(14).mean()
        avg_loss = pd.Series(loss).rolling(14).mean()
        rs = avg_gain / avg_loss
        data["RSI"] = 100 - (100 / (1 + rs))
    if "Bollinger Bands" in show_indicators:
        data["MA20"] = data["Close"].rolling(20).mean()
        data["Upper"] = data["MA20"] + 2 * data["Close"].rolling(20).std()
        data["Lower"] = data["MA20"] - 2 * data["Close"].rolling(20).std()

    # ----------------------------
    # Candlestick Chart
    # ----------------------------
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data["Open"], high=data["High"],
        low=data["Low"], close=data["Close"],
        name="Candlestick"
    ))

    # Add indicators to chart
    if "20-Day MA" in show_indicators and "MA20" in data:
        fig.add_trace(go.Scatter(x=data.index, y=data["MA20"], line=dict(color="blue"), name="20-Day MA"))
    if "50-Day MA" in show_indicators and "MA50" in data:
        fig.add_trace(go.Scatter(x=data.index, y=data["MA50"], line=dict(color="red"), name="50-Day MA"))
    if "Bollinger Bands" in show_indicators and "Upper" in data:
        fig.add_trace(go.Scatter(x=data.index, y=data["Upper"], line=dict(color="green"), name="Upper Band"))
        fig.add_trace(go.Scatter(x=data.index, y=data["Lower"], line=dict(color="green"), name="Lower Band"))

    fig.update_layout(title=f"{ticker} Stock Chart", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------
    # RSI Chart (separate)
    # ----------------------------
    if "RSI" in show_indicators and "RSI" in data:
        st.subheader(f"{ticker} RSI")
        st.line_chart(data["RSI"])

    # ----------------------------
    # Data Table + Download
    # ----------------------------
    st.subheader(f"Data Table for {ticker}")
    st.dataframe(data)

    csv = data.to_csv().encode("utf-8")
    st.download_button(
        label="Download Data as CSV",
        data=csv,
        file_name=f"{ticker}_data.csv",
        mime="text/csv"
    )
