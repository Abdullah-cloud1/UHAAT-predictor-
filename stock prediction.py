import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="centered", page_title="CandleTrend Forecast")

st.title("📈 CandleTrend Forecast – Stocks & Crypto")
st.caption("Get market direction + target from historical price action")

# 🧭 Sidebar Inputs
st.sidebar.header("Select Market")
symbol = st.sidebar.text_input("🔤 Symbol (e.g. AAPL, BTC-USD)", "AAPL").upper()
interval = st.sidebar.selectbox("⏱️ Interval", ['1m', '5m', '15m', '1h', '1d'], index=1)
period = st.sidebar.selectbox("📆 Period", ['1d', '5d', '1mo', '3mo'], index=1)

# 🔄 Fetch Data
with st.spinner("📡 Downloading data..."):
    data = yf.download(symbol, interval=interval, period=period, auto_adjust=True)
    data.dropna(inplace=True)

if data.empty:
    st.error("❌ No data found. Check your symbol or timeframe.")
    st.stop()

# 📊 Logic
data['candle_type'] = np.where(data['Close'] > data['Open'], 'Bullish',
                        np.where(data['Close'] < data['Open'], 'Bearish', 'Doji'))

bullish = (data['candle_type'] == 'Bullish').sum()
bearish = (data['candle_type'] == 'Bearish').sum()
data['range'] = data['High'] - data['Low']
atr = float(data['range'].rolling(14).mean().iloc[-1])
current_price = float(data['Close'].iloc[-1])
prediction = "📈 Bullish" if bullish > bearish else "📉 Bearish"
target = round(current_price + atr, 2) if "Bullish" in prediction else round(current_price - atr, 2)
confidence = round(abs(bullish - bearish) / (bullish + bearish + 1e-6), 2)

# 🧾 Output
col1, col2 = st.columns(2)
with col1:
    st.metric("💵 Current Price", f"${current_price:.8f}")
    st.metric("🎯 Target", f"${target:.8f}")
with col2:
    st.metric("🔮 Prediction", prediction)
    st.metric("📌 Confidence", f"{confidence*100:.2f}%")

st.write(f"🟢 Bullish candles: {bullish}  🔴 Bearish candles: {bearish}")

# 📈 Chart
fig, ax = plt.subplots(figsize=(10, 4))
data['Close'].plot(ax=ax, label="Close", color='blue', linewidth=1.5)
ax.axhline(y=target, color='green' if 'Bullish' in prediction else 'red',
           linestyle='--', label=f'Target: ${target}')
ax.set_title(f'{symbol} Forecast')
ax.legend()
ax.grid(True)
st.pyplot(fig)

st.caption("Powered by Yahoo Finance · Built by UHAAT Solutions® ")