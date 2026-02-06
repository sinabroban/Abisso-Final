"""
💎 Professional Crypto Trading Platform v3
Core Strategy: Bollinger Bands + MACD + RSI Triple Filter
"""

import streamlit as st
import pandas as pd
import numpy as np
import pyupbit
import pybithumb
from datetime import datetime
import time

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="💎 Pro Trading Pro",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== OLED 블랙 테마 & CSS ====================
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .status-bar {
        position: fixed; top: 0; left: 0; right: 0;
        background: #0a0a0a; padding: 1rem; z-index: 1000;
        border-bottom: 2px solid #00ff41;
    }
    .status-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; max-width: 1400px; margin: 0 auto; }
    .status-label { font-size: 0.7rem; color: #888; }
    .status-value { font-size: 1.1rem; font-weight: 800; color: #00ff41; }
    .main-content { margin-top: 100px; }
    .coin-card { background: #111; border: 1px solid #333; border-radius: 10px; padding: 15px; margin-bottom: 10px; }
    .signal-buy { color: #00ff41; font-weight: bold; border: 1px solid #00ff41; padding: 2px 5px; border-radius: 4px; }
    .signal-wait { color: #666; border: 1px solid #333; padding: 2px 5px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ==================== 기술적 분석 엔진 (3박자 전략) ====================
def calculate_indicators(df):
    # 1. Bollinger Bands (20, 2)
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['std'] = df['close'].rolling(window=20).std()
    df['upper'] = df['ma20'] + (df['std'] * 2)
    df['lower'] = df['ma20'] - (df['std'] * 2)
    
    # 2. RSI (14)
    delta = df['close'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    avg_gain = up.rolling(window=14).mean()
    avg_loss = abs(down.rolling(window=14).mean())
    df['rsi'] = 100 - (100 / (1 + (avg_gain / avg_loss)))
    
    # 3. MACD (12, 26, 9)
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    return df

def get_signal(ticker, exchange):
    try:
        if exchange == 'upbit':
            df = pyupbit.get_ohlcv(ticker, interval="minute15", count=50)
        else:
            df = pybithumb.get_ohlcv(ticker.split('-')[1], interval="24h").tail(50)
            
        if df is None or len(df) < 30: return "ERROR", 0, 0, 0
        
        df = calculate_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 전략 기준 정의
        is_rsi_low = curr['rsi'] < 45  # 과매도권 진입 확인
        is_macd_cross = (prev['macd'] < prev['macd_signal']) and (curr['macd'] > curr['macd_signal']) # 골든크로스
        is_below_ma = curr['close'] < curr['ma20'] # 가격이 중심선 아래 (반등 여력)
        
        if (is_rsi_low or is_macd_cross) and is_below_ma:
            return "BUY", curr['close'], curr['rsi'], curr['macd']
        return "WAIT", curr['close'], curr['rsi'], curr['macd']
    except:
        return "ERROR", 0, 0, 0

# ==================== 세션 상태 관리 ====================
if 'init' not in st.session_state:
    st.session_state.total = 10000000.0
    st.session_state.invested = 0.0
    st.session_state.positions = {}
    st.session_state.running = False
    st.session_state.per_trade = 1000000.0

# ==================== 메인 UI ====================
def main():
    # 상단 상태바
    total_eval = sum([p['val'] for p in st.session_state.positions.values()])
    total_asset = (st.session_state.total - st.session_state.invested) + total_eval
    
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-grid">
            <div class="status-item"><div class="status-label">TOTAL ASSET</div><div class="status-value">{total_asset:,.0f}원</div></div>
            <div class="status-item"><div class="status-label">INVESTED</div><div class="status-value">{st.session_state.invested:,.0f}원</div></div>
            <div class="status-item"><div class="status-label">ALGO</div><div class="status-value">BB+MACD+RSI</div></div>
            <div class="status-item"><div class="status-label">STATUS</div><div class="status-value">{"RUNNING" if st.session_state.running else "IDLE"}</div></div>
        </div>
    </div>
    <div class="main-content"></div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 STRATEGY SCAN", "📊 PORTFOLIO", "⚙️ CONFIG"])

    with tab1:
        st.subheader("Real-time 15m Signal Watchlist")
        watch_list = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE"]
        
        for t in watch_list:
            sig, price, rsi, macd = get_signal(t, 'upbit')
            sig_ui = f"<span class='signal-buy'>BUY</span>" if sig == "BUY" else f"<span class='signal-wait'>WAIT</span>"
            
            col1, col2, col3, col4 = st.columns([1.5, 2, 2, 1.5])
            col1.markdown(f"**{t}**")
            col2.write(f"Price: {price:,.0f}")
            col3.write(f"RSI: {rsi:.1f}")
            col4.markdown(sig_ui, unsafe_allow_html=True)
            
            # 자동 매수 트리거
            if st.session_state.running and sig == "BUY" and t not in st.session_state.positions:
                qty = st.session_state.per_trade / price
                st.session_state.positions[t] = {
                    'buy': price, 'qty': qty, 'inv': st.session_state.per_trade, 'val': st.session_state.per_trade
                }
                st.session_state.invested += st.session_state.per_trade
            st.divider()

    with tab2:
        if not st.session_state.positions:
            st.info("Searching for opportunities based on 3-indicator strategy...")
        for t, p in st.session_state.positions.items():
            curr_p = pyupbit.get_current_price(t)
            val = curr_p * p['qty']
            pft = val - p['inv']
            pft_p = (pft / p['inv']) * 100
            p_color = "#00ff41" if pft >= 0 else "#ff0040"
            
            st.markdown(f"""
            <div class="coin-card">
                <div style="display:flex; justify-content:space-between;">
                    <b>{t}</b>
                    <span style="color:{p_color}; font-weight:bold;">{pft_p:+.2f}% ({pft:+,.0f}원)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.session_state.total = st.number_input("Seed Money (KRW)", value=int(st.session_state.total))
        st.session_state.per_trade = st.number_input("Per Trade (KRW)", value=int(st.session_state.per_trade))
        
        if st.session_state.running:
            if st.button("🛑 STOP ALGO", use_container_width=True, type="primary"):
                st.session_state.running = False
                st.rerun()
        else:
            if st.button("🚀 START ALGO", use_container_width=True):
                st.session_state.running = True
                st.rerun()

    if st.session_state.running:
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()
