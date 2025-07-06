import streamlit as st
from binance.client import Client
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- Binance client
client = Client()

# --- Page setup
st.set_page_config(page_title="UHAAT Predictor", layout="centered", page_icon="📊")
st.markdown("<h1 style='text-align:center; color:#00c1ff;'>📊 UHAAT Crypto Predictor</h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;'>Live candlestick forecasting powered by Binance</div>", unsafe_allow_html=True)
st.markdown("---")

# --- Symbol dropdown
def get_binance_symbols():
    info = client.get_exchange_info()
    symbols = [s['symbol'] for s in info['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
    clean = [s for s in symbols if all(x not in s for x in ['UP', 'DOWN', 'BULL', 'BEAR'])]
    return sorted(clean)

symbols = get_binance_symbols()
selected = st.selectbox("🪙 Choose a crypto pair", symbols)

# --- Interval & history slider
interval = st.selectbox("⏱️ Select interval", ['1m','5m','15m','30m','1h','4h','1d'], index=4)
hours = st.slider("📅 Lookback period (hours)", min_value=6, max_value=168, value=48)

# --- Download OHLC data
def get_binance_ohlc(symbol, interval, hours):
    end = datetime.utcnow()
    start = end - timedelta(hours=hours)
    klines = client.get_historical_klines(
        symbol, interval,
        start.strftime('%d %b %Y %H:%M:%S'),
        end.strftime('%d %b %Y %H:%M:%S')
    )
    df_raw = pd.DataFrame(klines, columns=[
        'Time','Open','High','Low','Close','Volume','Close_time',
        'Quote_volume','Trades','Taker_base','Taker_quote','Ignore'
    ])
    df_raw['Time'] = pd.to_datetime(df_raw['Time'], unit='ms')
    df_numeric = df_raw[['Open','High','Low','Close']].astype(float)
    df_final = pd.concat([df_raw['Time'], df_numeric], axis=1).set_index('Time')
    return df_final

df = get_binance_ohlc(selected, interval, hours)

if df.empty:
    st.error("⚠️ No data available. Try another pair or interval.")
else:
    # --- Candle classification & ATR
    df['Candle'] = np.where(df['Close'] > df['Open'], 'Bullish',
                    np.where(df['Close'] < df['Open'], 'Bearish', 'Doji'))
    df['H-L'] = df['High'] - df['Low']
    df['H-C'] = abs(df['High'] - df['Close'].shift())
    df['L-C'] = abs(df['Low'] - df['Close'].shift())
    df['TR'] = df[['H-L', 'H-C', 'L-C']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=14).mean()

    # --- Prediction logic
    majority = df['Candle'].value_counts().idxmax()
    latest = df.iloc[-1]
    close_price = float(latest['Close'])
    atr_val = float(latest['ATR']) if not np.isnan(latest['ATR']) else 0.0
    target_price = close_price + atr_val if majority == 'Bullish' else close_price - atr_val

    # --- Confidence estimation
    total_candles = len(df)
    dominant_count = df['Candle'].value_counts().get(majority, 0)
    confidence_pct = (dominant_count / total_candles) * 100

    # --- Forecast panel
    st.markdown("### 🔮 Forecast Summary")
    st.markdown(f"🕯️ Dominant Candle: **{majority}**")
    st.markdown(f"💰 Latest Close: **${close_price:,.7f}**")
    st.markdown(f"🎯 Target Price: **${target_price:,.7f}**")
    st.markdown(f"📐 ATR Volatility: **${atr_val:,.7f}**")
    st.markdown(f"📊 Prediction Confidence: **{confidence_pct:.2f}%**")

    # --- Forecast chart
    fig, ax = plt.subplots(figsize=(10, 4))
    df['Close'].plot(ax=ax, label="Close Price", color='blue', linewidth=1.5)
    ax.axhline(y=target_price,
               color='green' if majority == 'Bullish' else 'red',
               linestyle='--',
               label=f'Target: ${target_price:,.7f}')
    ax.set_title(f'{selected} Forecast with ATR Target')
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # --- CSV export
    st.download_button(
        "📥 Export OHLC Data",
        data=df.to_csv().encode("utf-8"),
        file_name=f"{selected}_ohlc.csv",
        mime="text/csv"
    )

    # --- Expandable raw table
    with st.expander("🧾 Raw OHLC Data Table"):
        st.dataframe(df.tail(30)[['Open', 'High', 'Low', 'Close', 'Candle', 'ATR']])

# --- Footer
st.markdown("---")
st.caption("UHAAT Solutions · Built by Abdullah · Binance-Powered Forecasts Done Right ")
