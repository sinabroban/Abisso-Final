"""
💎 프로 트레이딩 플랫폼 v3 (한글판)
핵심 전략: 볼린저 밴드 + MACD + RSI 트리플 필터
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
    page_title="💎 AI 자동매매 프로",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== OLED 블랙 테마 & 한국어 맞춤 CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Noto Sans KR', sans-serif;
    }
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .status-bar {
        position: fixed; top: 0; left: 0; right: 0;
        background: #0a0a0a; padding: 1rem; z-index: 1000;
        border-bottom: 2px solid #00ff41;
    }
    .status-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; max-width: 1400px; margin: 0 auto; }
    .status-label { font-size: 0.8rem; color: #888; margin-bottom: 4px; }
    .status-value { font-size: 1.2rem; font-weight: 800; color: #00ff41; }
    .main-content { margin-top: 110px; }
    .coin-card { 
        background: #111111; 
        border: 1px solid #333333; 
        border-radius: 12px; 
        padding: 20px; 
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .signal-buy { 
        background-color: rgba(0, 255, 65, 0.2);
        color: #00ff41; 
        font-weight: bold; 
        border: 1px solid #00ff41; 
        padding: 5px 12px; 
        border-radius: 8px;
        animation: blink 2s infinite;
    }
    @keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
    .signal-wait { color: #666; border: 1px solid #333; padding: 5px 12px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ==================== 기술적 분석 엔진 (3박자 전략) ====================
def calculate_indicators(df):
    # 1. 볼린저 밴드 (20, 2)
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
            
        if df is None or len(df) < 30: return "데이터오류", 0, 0, 0
        
        df = calculate_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # --- 매수 전략 조건 ---
        # 1. RSI 45 미만 (과매도 구간에서 반등 준비)
        is_rsi_low = curr['rsi'] < 45  
        # 2. MACD 골든크로스 (추세 전환 확인)
        is_macd_cross = (prev['macd'] < prev['macd_signal']) and (curr['macd'] > curr['macd_signal'])
        # 3. 현재가가 볼린저 밴드 중심선(ma20) 아래 (저점 매수 유리)
        is_below_ma = curr['close'] < curr['ma20'] 
        
        if (is_rsi_low or is_macd_cross) and is_below_ma:
            return "매수신호", curr['close'], curr['rsi'], curr['macd']
        return "대기중", curr['close'], curr['rsi'], curr['macd']
    except:
        return "에러", 0, 0, 0

# ==================== 세션 상태 관리 ====================
if 'init' not in st.session_state:
    st.session_state.total = 10000000.0 # 기본 1,000만원
    st.session_state.invested = 0.0
    st.session_state.positions = {}
    st.session_state.running = False
    st.session_state.per_trade = 1000000.0 # 종목당 100만원

# ==================== 메인 UI ====================
def main():
    # 상단 고정 상태바
    total_eval = sum([p['val'] for p in st.session_state.positions.values()])
    total_asset = (st.session_state.total - st.session_state.invested) + total_eval
    
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-grid">
            <div class="status-item"><div class="status-label">총 자산 평가액</div><div class="status-value">{total_asset:,.0f}원</div></div>
            <div class="status-item"><div class="status-label">현재 투자금</div><div class="status-value">{st.session_state.invested:,.0f}원</div></div>
            <div class="status-item"><div class="status-label">적용 기법</div><div class="status-value">BB+MACD+RSI</div></div>
            <div class="status-item"><div class="status-label">시스템 상태</div><div class="status-value">{"가동중" if st.session_state.running else "정지됨"}</div></div>
        </div>
    </div>
    <div class="main-content"></div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 실시간 전략 감시", "📊 내 포트폴리오", "⚙️ 매매 설정"])

    with tab1:
        st.subheader("실시간 15분봉 시그널 스캐너")
        watch_list = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE", "KRW-ADA"]
        
        for t in watch_list:
            sig, price, rsi, macd = get_signal(t, 'upbit')
            sig_ui = f"<span class='signal-buy'>매수 신호</span>" if sig == "매수신호" else f"<span class='signal-wait'>조건 대기</span>"
            
            col1, col2, col3, col4 = st.columns([1.5, 2, 2, 1.5])
            col1.markdown(f"**{t}**")
            col2.write(f"현재가: {price:,.0f}원")
            col3.write(f"RSI 지수: {rsi:.1f}")
            col4.markdown(sig_ui, unsafe_allow_html=True)
            
            # 자동 매수 실행 (시스템 가동 시)
            if st.session_state.running and sig == "매수신호" and t not in st.session_state.positions:
                qty = st.session_state.per_trade / price
                st.session_state.positions[t] = {
                    'buy': price, 'qty': qty, 'inv': st.session_state.per_trade, 'val': st.session_state.per_trade
                }
                st.session_state.invested += st.session_state.per_trade
            st.divider()

    with tab2:
        if not st.session_state.positions:
            st.info("현재 보유 중인 종목이 없습니다. 알고리즘이 기회를 찾고 있어요!")
        for t, p in st.session_state.positions.items():
            curr_p = pyupbit.get_current_price(t)
            val = curr_p * p['qty']
            pft = val - p['inv']
            pft_p = (pft / p['inv']) * 100
            p_color = "#00ff41" if pft >= 0 else "#ff0040"
            
            st.markdown(f"""
            <div class="coin-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-size:1.2rem; font-weight:bold;">{t}</span>
                        <div style="font-size:0.8rem; color:#888;">수량: {p['qty']:.4f} / 평단: {p['buy']:,.0f}원</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:{p_color}; font-size:1.3rem; font-weight:bold;">{pft_p:+.2f}%</div>
                        <div style="color:{p_color}; font-size:0.9rem;">{pft:+,.0f}원</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.subheader("매매 환경 설정")
        st.session_state.total = st.number_input("운용 가능 총자산 (원)", value=int(st.session_state.total), step=1000000)
        st.session_state.per_trade = st.number_input("종목당 투자 금액 (원)", value=int(st.session_state.per_trade), step=100000)
        
        st.divider()
        if st.session_state.running:
            if st.button("🛑 자동매매 시스템 종료", use_container_width=True, type="primary"):
                st.session_state.running = False
                st.rerun()
        else:
            if st.button("🚀 자동매매 시스템 시작", use_container_width=True):
                st.session_state.running = True
                st.rerun()

    if st.session_state.running:
        time.sleep(5) # 5초마다 데이터 갱신
        st.rerun()

if __name__ == "__main__":
    main()
