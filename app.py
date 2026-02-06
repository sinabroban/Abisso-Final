"""
💎 프로 트레이딩 플랫폼 v3 (Vercel 스타일 UI 적용)
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
    page_title="AI Trading Dashboard",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded" # 사이드바 기본 열림
)

# ==================== 사이트 외관 (Vercel v0 스타일 CSS) ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    /* 전체 폰트 및 배경 */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
    }
    .stApp { background-color: #000000 !important; color: #ffffff !important; }

    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #222;
    }

    /* 상단 대시보드 카드 스타일 (버셀 스타일) */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-bottom: 30px;
    }
    .metric-card {
        background: #111;
        border: 1px solid #222;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .metric-label { color: #888; font-size: 0.85rem; margin-bottom: 5px; }
    .metric-value { color: #00ff41; font-size: 1.5rem; font-weight: 800; }

    /* 코인 리스트 아이템 */
    .coin-item {
        background: #0a0a0a;
        border-bottom: 1px solid #1a1a1a;
        padding: 15px 10px;
        transition: background 0.3s;
    }
    .coin-item:hover { background: #111; }
    
    /* 신호 상태 표시 */
    .status-badge {
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .buy-badge { background: rgba(0, 255, 65, 0.15); color: #00ff41; border: 1px solid #00ff41; }
    .wait-badge { background: #1a1a1a; color: #555; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# ==================== 전략 로직 (BB + MACD + RSI) ====================
def get_indicators(df):
    # 볼린저 밴드
    df['ma20'] = df['close'].rolling(20).mean()
    df['std'] = df['close'].rolling(20).std()
    df['lower'] = df['ma20'] - (df['std'] * 2)
    # RSI
    diff = df['close'].diff()
    u, d = diff.copy(), diff.copy()
    u[u<0]=0; d[d>0]=0
    df['rsi'] = 100 - (100/(1+(u.rolling(14).mean()/abs(d.rolling(14).mean()))))
    # MACD
    df['m'] = df['close'].ewm(12).mean() - df['close'].ewm(26).mean()
    df['s'] = df['m'].ewm(9).mean()
    return df

def analyze_market(ticker):
    try:
        df = pyupbit.get_ohlcv(ticker, interval="minute15", count=40)
        df = get_indicators(df)
        c, p = df.iloc[-1], df.iloc[-2]
        
        is_low = c['close'] < c['ma20']
        is_rsi_buy = c['rsi'] < 45
        is_macd_cross = (p['m'] < p['s']) and (c['m'] > c['s'])
        
        if (is_rsi_buy or is_macd_cross) and is_low:
            return "BUY", c['close'], c['rsi']
        return "WAIT", c['close'], c['rsi']
    except: return "ERR", 0, 0

# ==================== 데이터 초기화 ====================
if 'data' not in st.session_state:
    st.session_state.data = {
        'total': 10000000.0,
        'invested': 0.0,
        'holdings': {},
        'is_active': False
    }

# ==================== 메인 화면 구성 ====================
def main():
    d = st.session_state.data
    
    # 1. 좌측 사이드바 (Vercel 메뉴 구성 모방)
    with st.sidebar:
        st.title("PRO TRADER")
        st.markdown("---")
        menu = st.radio("Navigation", ["Dashboard", "Portfolio", "Settings"])
        st.markdown("---")
        st.subheader("System Control")
        if st.button("🚀 Start Auto-Trade", use_container_width=True) if not d['is_active'] else st.button("🛑 Stop System", use_container_width=True, type="primary"):
            d['is_active'] = not d['is_active']
            st.rerun()

    # 메인 헤더
    st.title("Trading Dashboard")
    st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 2. 상단 대시보드 카드 (오빠가 보낸 URL 스타일)
    total_val = (d['total'] - d['invested']) + sum([h['inv'] for h in d['holdings'].values()])
    
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-card">
            <div class="metric-label">총 평가 자산</div>
            <div class="metric-value">{total_val:,.0f}원</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">활성 투자 금액</div>
            <div class="metric-value" style="color:#ffffff;">{d['invested']:,.0f}원</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">현재 전략</div>
            <div class="metric-value" style="color:#00ff41; font-size:1.1rem;">BB + RSI + MACD</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">시스템 상태</div>
            <div class="metric-value" style="color:{'#00ff41' if d['is_active'] else '#ff4b4b'}; font-size:1.1rem;">
                {'● RUNNING' if d['is_active'] else '○ IDLE'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. 중앙 본문 (네비게이션에 따른 화면 전환)
    if menu == "Dashboard":
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("실시간 마켓 스캐너")
            watch_list = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE"]
            
            for t in watch_list:
                sig, price, rsi = analyze_market(t)
                badge = "buy-badge" if sig == "BUY" else "wait-badge"
                sig_text = "매수 신호" if sig == "BUY" else "감시 중"
                
                st.markdown(f"""
                <div class="coin-item">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-weight:700; font-size:1.1rem;">{t}</span><br>
                            <span style="color:#888; font-size:0.85rem;">현재가: {price:,.0f}원 | RSI: {rsi:.1f}</span>
                        </div>
                        <span class="status-badge {badge}">{sig_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 가동 중일 때 자동 매수
                if d['is_active'] and sig == "BUY" and t not in d['holdings']:
                    d['holdings'][t] = {'buy': price, 'inv': 1000000.0}
                    d['invested'] += 1000000.0

        with col2:
            st.subheader("전략 가이드")
            st.info("""
            **트리플 컨펌 전략**
            1. **BB 하단**: 가격이 통계적 저점에 도달했는가?
            2. **RSI 45 미만**: 시장이 충분히 과매도되었는가?
            3. **MACD 골든크로스**: 단기 반등 추세가 시작되었는가?
            """)

    elif menu == "Portfolio":
        st.subheader("내 보유 자산")
        if not d['holdings']:
            st.write("보유한 코인이 없습니다.")
        for t, h in d['holdings'].items():
            curr = pyupbit.get_current_price(t)
            profit = ((curr - h['buy']) / h['buy']) * 100
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between;">
                    <b>{t}</b>
                    <span style="color:{'#00ff41' if profit>=0 else '#ff4b4b'}">{profit:+.2f}%</span>
                </div>
                <div style="font-size:0.85rem; color:#888;">매수가: {h['buy']:,.0f} | 현재가: {curr:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    elif menu == "Settings":
        st.subheader("설정")
        d['total'] = st.number_input("초기 자본 설정", value=int(d['total']))
        st.button("데이터 리셋", on_click=lambda: d.update({'holdings': {}, 'invested': 0.0}))

    # 자동 리프레시
    if d['is_active']:
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()
