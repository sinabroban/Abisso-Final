"""
💎 프로 트레이딩 플랫폼 v3 (가독성 및 모바일 최적화)
핵심 전략: 볼린저 밴드 + MACD + RSI 트리플 필터
"""

import streamlit as st
import pandas as pd
import numpy as np
import pyupbit
import pybithumb
from datetime import datetime
import time

# ==================== 페이지 설정 (사이드바 상태를 auto로 변경) ====================
st.set_page_config(
    page_title="AI 트레이딩 대시보드",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="auto" # 모바일에서 접히도록 auto로 설정
)

# ==================== 사이트 외관 (CSS 최종 보정) ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    /* 1. 상단 흰색 바 제거 및 전체 배경 블랙 강제 */
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
        color: white !important;
    }
    .stApp { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
    }

    /* 2. 사이드바 글자색 및 배경색 확실하게 구분 */
    [data-testid="stSidebar"] {
        background-color: #111111 !important; /* 약간 밝은 블랙으로 구분 */
        border-right: 1px solid #333;
    }
    
    /* 사이드바 모든 텍스트를 흰색으로 */
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span {
        color: #ffffff !important; 
        font-size: 1.05rem !important;
        opacity: 1 !important;
    }

    /* 사이드바 라디오 버튼(메뉴) 글자색 */
    div[data-testid="stSidebarUserContent"] .st-emotion-cache-16idsys p {
        color: #ffffff !important;
        font-weight: 500 !important;
    }

    /* 3. 대시보드 카드 디자인 */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 15px;
        margin-bottom: 30px;
    }
    .metric-card {
        background: #1a1a1a;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 12px;
    }
    .metric-label { color: #bbbbbb; font-size: 0.9rem; margin-bottom: 8px; }
    .metric-value { color: #00ff41; font-size: 1.6rem; font-weight: 800; }

    /* 4. 전략 가이드 박스 (배경 대비 강화) */
    .guide-box {
        background: #1c2128; 
        border: 1px solid #444c56;
        padding: 20px;
        border-radius: 12px;
    }
    .guide-title { color: #58a6ff; font-weight: 700; font-size: 1.1rem; margin-bottom: 10px; }
    .guide-text { color: #adbac7 !important; line-height: 1.6; }
    
    /* 코인 아이템 가독성 */
    .coin-item {
        background: #0d0d0d;
        border-bottom: 1px solid #222;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 전략 로직 ====================
def get_indicators(df):
    df['ma20'] = df['close'].rolling(20).mean()
    df['std'] = df['close'].rolling(20).std()
    df['lower'] = df['ma20'] - (df['std'] * 2)
    diff = df['close'].diff()
    u, d = diff.copy(), diff.copy()
    u[u<0]=0; d[d>0]=0
    df['rsi'] = 100 - (100/(1+(u.rolling(14).mean()/abs(d.rolling(14).mean()))))
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
            return "매수", c['close'], c['rsi']
        return "대기", c['close'], c['rsi']
    except: return "에러", 0, 0

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
    
    # 1. 좌측 사이드바
    with st.sidebar:
        st.markdown("<h2 style='color:white; margin-top:0;'>💎 전문 트레이더</h2>", unsafe_allow_html=True)
        st.write("") # 간격
        menu = st.radio("메뉴 이동", ["거래소 대시보드", "내 포트폴리오", "시스템 설정"])
        st.markdown("---")
        st.markdown("<p style='color:white;'>시스템 제어</p>", unsafe_allow_html=True)
        btn_label = "🛑 시스템 정지" if d['is_active'] else "🚀 자동매매 시작"
        if st.button(btn_label, use_container_width=True, type="primary" if d['is_active'] else "secondary"):
            d['is_active'] = not d['is_active']
            st.rerun()

    # 메인 헤더
    st.title("거래 관리 대시보드")
    st.caption(f"최근 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 2. 상단 대시보드 카드
    total_val = (d['total'] - d['invested']) + sum([h['inv'] for h in d['holdings'].values()])
    
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-card">
            <div class="metric-label">총 평가 자산</div>
            <div class="metric-value">{total_val:,.0f}원</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">투자 중인 금액</div>
            <div class="metric-value" style="color:#ffffff;">{d['invested']:,.0f}원</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">적용 전략</div>
            <div class="metric-value" style="color:#00ff41; font-size:1.1rem;">볼린저밴드 + RSI + MACD</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">시스템 상태</div>
            <div class="metric-value" style="color:{'#00ff41' if d['is_active'] else '#ff4b4b'}; font-size:1.1rem;">
                {'● 가동 중' if d['is_active'] else '○ 정지 상태'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. 중앙 본문
    if menu == "거래소 대시보드":
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("실시간 시장 분석")
            watch_list = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE"]
            
            for t in watch_list:
                sig, price, rsi = analyze_market(t)
                sig_text = "매수 신호" if sig == "매수" else "감시 중"
                badge_style = "background:rgba(0,255,65,0.2); color:#00ff41; border:1px solid #00ff41;" if sig == "매수" else "background:#1a1a1a; color:#888; border:1px solid #333;"
                
                st.markdown(f"""
                <div class="coin-item">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-weight:700; font-size:1.1rem; color:white;">{t}</span><br>
                            <span style="color:#888; font-size:0.85rem;">현재가: {price:,.0f}원 | RSI: {rsi:.1f}</span>
                        </div>
                        <span style="padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; {badge_style}">{sig_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if d['is_active'] and sig == "매수" and t not in d['holdings']:
                    d['holdings'][t] = {'buy': price, 'inv': 1000000.0}
                    d['invested'] += 1000000.0

        with col2:
            st.subheader("전략 가이드")
            st.markdown("""
            <div class="guide-box">
                <div class="guide-title">트리플 확인 전략</div>
                <div class="guide-text">
                    1. <b>볼린저밴드 하단</b>: 가격이 통계적 저점에 도달했는가?<br><br>
                    2. <b>RSI 45 미만</b>: 시장이 충분히 과매도되었는가?<br><br>
                    3. <b>MACD 골든크로스</b>: 단기 상승 추세가 시작되었는가?
                </div>
            </div>
            """, unsafe_allow_html=True)

    elif menu == "내 포트폴리오":
        st.subheader("보유 자산 상세")
        if not d['holdings']:
            st.info("현재 보유 중인 종목이 없습니다.")
        for t, h in d['holdings'].items():
            curr = pyupbit.get_current_price(t)
            profit = ((curr - h['buy']) / h['buy']) * 100
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between;">
                    <b style="color:white;">{t}</b>
                    <span style="color:{'#00ff41' if profit>=0 else '#ff4b4b'}">{profit:+.2f}%</span>
                </div>
                <div style="font-size:0.85rem; color:#888;">매수가: {h['buy']:,.0f} | 현재가: {curr:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    elif menu == "시스템 설정":
        st.subheader("운용 설정")
        d['total'] = st.number_input("시드 머니 설정 (원)", value=int(d['total']), step=1000000)
        if st.button("투자 데이터 초기화", use_container_width=True):
            d.update({'holdings': {}, 'invested': 0.0})
            st.rerun()

    # 자동 갱신
    if d['is_active']:
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()
