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

# ==================== OLED 블랙 테마 & UI 최적화 ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Noto Sans KR', sans-serif;
    }
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    
    /* 상단 고정 상태바 - 오빠가 준 URL 대시보드 느낌 재현 */
    .status-bar {
        position: fixed; top: 0; left: 0; right: 0;
        background: #0a0a0a; padding: 1.2rem; z-index: 1000;
        border-bottom: 2px solid #00ff41;
        box-shadow: 0 4px 20px rgba(0, 255, 65, 0.1);
    }
    .status-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; max-width: 1400px; margin: 0 auto; }
    .status-label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .status-value { font-size: 1.3rem; font-weight: 800; color: #00ff41; }
    
    .main-content { margin-top: 120px; }
    
    /* 카드 디자인 개선 */
    .coin-card { 
        background: linear-gradient(145deg, #111111, #0a0a0a);
        border: 1px solid #222222; 
        border-radius: 15px; 
        padding: 24px; 
        margin-bottom: 20px;
    }
    .indicator-pill {
        display: inline-block;
        font-size: 0.7rem;
        padding: 3px 10px;
        border-radius: 20px;
        margin-right: 8px;
        background: rgba(255, 255, 255, 0.05);
    }
    .signal-buy { color: #00ff41; font-weight: bold; border: 1px solid #00ff41; padding: 5px 15px; border-radius: 8px; }
    .signal-wait { color: #444; border: 1px solid #222; padding: 5px 15px; border-radius: 8px; }
    
    /* 전략 가이드 박스 */
    .guide-box {
        background: #0a0a0a;
        border-left: 4px solid #00ff41;
        padding: 15px;
        margin-bottom: 25px;
        border-radius: 0 10px 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 전략 엔진 ====================
def calculate_indicators(df):
    # 볼린저 밴드
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['std'] = df['close'].rolling(window=20).std()
    df['lower'] = df['ma20'] - (df['std'] * 2)
    # RSI
    delta = df['close'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0; down[down > 0] = 0
    df['rsi'] = 100 - (100 / (1 + (up.rolling(14).mean() / abs(down.rolling(14).mean()))))
    # MACD
    df['macd'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    df['macd_s'] = df['macd'].ewm(span=9).mean()
    return df

def fetch_signal(ticker):
    try:
        df = pyupbit.get_ohlcv(ticker, interval="minute15", count=50)
        if df is None: return "ERR", 0, 0, {}
        df = calculate_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        stats = {
            'rsi': curr['rsi'],
            'is_low': curr['close'] < curr['ma20'],
            'cross': (prev['macd'] < prev['macd_s']) and (curr['macd'] > curr['macd_s'])
        }
        
        # 전략: RSI가 낮거나(침체) MACD 골든크로스가 발생했는데, 가격이 밴드 하단일 때
        if (stats['rsi'] < 45 or stats['cross']) and stats['is_low']:
            return "BUY", curr['close'], curr['rsi'], stats
        return "WAIT", curr['close'], curr['rsi'], stats
    except: return "ERR", 0, 0, {}

# ==================== 세션 초기화 ====================
if 'state' not in st.session_state:
    st.session_state.state = {
        'total': 10000000.0,
        'inv': 0.0,
        'pos': {},
        'run': False,
        'per': 1000000.0
    }

# ==================== 메인 화면 ====================
def main():
    s = st.session_state.state
    eval_val = sum([p['inv'] for p in s['pos'].values()]) # 간소화된 평가
    total_val = (s['total'] - s['inv']) + eval_val

    # 상단 대시보드 (오빠가 만든 사이트 스타일 적용)
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-grid">
            <div class="status-item"><div class="status-label">Total Balance</div><div class="status-value">{total_val:,.0f}원</div></div>
            <div class="status-item"><div class="status-label">Active Investment</div><div class="status-value">{s['inv']:,.0f}원</div></div>
            <div class="status-item"><div class="status-label">Strategy Mode</div><div class="status-value">Triple-Signal</div></div>
            <div class="status-item"><div class="status-label">System Status</div><div class="status-value" style="color:{'#00ff41' if s['run'] else '#ff0040'}">{'RUNNING' if s['run'] else 'IDLE'}</div></div>
        </div>
    </div>
    <div class="main-content"></div>
    """, unsafe_allow_html=True)

    # 1. 전략 가이드 섹션 (앱을 켜면 바로 알 수 있게)
    with st.expander("💡 이 자동매매 앱은 어떻게 작동하나요?", expanded=not s['run']):
        st.markdown("""
        <div class="guide-box">
            <b>1단계: 시장 스캔</b> - 업비트 주요 코인의 15분봉 데이터를 실시간으로 읽어옵니다.<br>
            <b>2단계: 3박자 필터링</b><br>
            - 📈 <b>RSI</b>: 지수가 45 미만으로 떨어져 가격이 저렴해졌는지 확인합니다.<br>
            - 📉 <b>볼린저 밴드</b>: 현재 가격이 20일 평균선 아래에 있는지(저점) 확인합니다.<br>
            - ⚡ <b>MACD</b>: 단기 추세가 위로 꺾이는 '골든크로스' 시점을 포착합니다.<br>
            <b>3단계: 자동 주문</b> - 위 조건들이 충족되면 설정한 금액만큼 즉시 매수합니다.
        </div>
        """, unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["🎯 시장 모니터링", "📂 보유 자산", "⚙️ 시스템 설정"])

    with t1:
        st.subheader("실시간 시그널 스캐너")
        coins = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE"]
        for c in coins:
            sig, price, rsi, stats = fetch_signal(c)
            with st.container():
                col1, col2, col3 = st.columns([1.5, 3, 1.5])
                col1.markdown(f"**{c}**\n\n{price:,.0f}원")
                
                # 지표 상태 시각화
                rsi_c = "#00ff41" if rsi < 45 else "#444"
                bb_c = "#00ff41" if stats.get('is_low') else "#444"
                mc_c = "#00ff41" if stats.get('cross') else "#444"
                
                col2.markdown(f"""
                    <span class="indicator-pill" style="border:1px solid {rsi_c}; color:{rsi_c}">RSI: {rsi:.1f}</span>
                    <span class="indicator-pill" style="border:1px solid {bb_c}; color:{bb_c}">밴드하단: {'YES' if stats.get('is_low') else 'NO'}</span>
                    <span class="indicator-pill" style="border:1px solid {mc_c}; color:{mc_c}">MACD: {'CROSS' if stats.get('cross') else 'WAIT'}</span>
                """, unsafe_allow_html=True)
                
                if sig == "BUY":
                    col3.markdown("<span class='signal-buy'>매수 신호</span>", unsafe_allow_html=True)
                    if s['run'] and c not in s['pos']:
                        s['pos'][c] = {'buy': price, 'inv': s['per']}
                        s['inv'] += s['per']
                else:
                    col3.markdown("<span class='signal-wait'>감시중</span>", unsafe_allow_html=True)
            st.divider()

    with t2:
        if not s['pos']: st.info("보유 중인 종목이 없습니다.")
        for t, p in s['pos'].items():
            st.markdown(f"<div class='coin-card'><b>{t}</b><br>매수가: {p['buy']:,.0f}원 | 투자금: {p['inv']:,.0f}원</div>", unsafe_allow_html=True)

    with t3:
        s['total'] = st.number_input("총 자산(원)", value=int(s['total']))
        s['per'] = st.number_input("회당 투자금(원)", value=int(s['per']))
        if st.button("🚀 시스템 가동" if not s['run'] else "🛑 시스템 정지", use_container_width=True):
            s['run'] = not s['run']
            st.rerun()

    if s['run']:
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()
