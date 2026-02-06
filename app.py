"""
💎 프로 트레이딩 플랫폼 v3 (Vercel 스타일 UI 개선판)
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
    page_title="AI 트레이딩 대시보드",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 사이트 외관 (가독성 강화 UI) ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    /* 전체 폰트 및 배경 */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
    }
    .stApp { background-color: #000000 !important; color: #ffffff !important; }

    /* 사이드바 가독성 개선 (글자색 명확하게) */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #222;
    }
    [data-testid="stSidebar"] .stMarkdown p {
        color: #ffffff !important; /* 사이드바 텍스트 흰색으로 강제 */
        font-weight: 500;
    }
    [data-testid="stSidebarNav"] { color: white !important; }
    
    /* 사이드바 라디오 버튼 글자색 수정 */
    div[data-testid="stSidebarUserContent"] .st-emotion-cache-16idsys p {
        color: #eeeeee !important;
        font-size: 1rem !important;
    }

    /* 대시보드 카드 스타일 */
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
    .metric-label { color: #aaaaaa; font-size: 0.9rem; margin-bottom: 8px; font-weight: 400; }
    .metric-value { color: #00ff41; font-size: 1.6rem; font-weight: 800; }

    /* 코인 리스트 아이템 */
    .coin-item {
        background: #0a0a0a;
        border-bottom: 1px solid #1a1a1a;
        padding: 15px 10px;
    }
    
    /* 신호 상태 표시 */
    .status-badge {
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .buy-badge { background: rgba(0, 255, 65, 0.2); color: #00ff41; border: 1px solid #00ff41; }
    .wait-badge { background: #1a1a1a; color: #888888; border: 1px solid #333; }
    
    /* 전략 가이드 박스 가독성 수정 (배경과 대비) */
    .guide-box {
        background: #161b22; /* 살짝 더 밝은 다크블루 계열 */
        border: 1px solid #30363d;
        padding: 20px;
        border-radius: 12px;
        color: #e6edf3 !important;
    }
    .guide-title {
        color: #58a6ff;
        font-weight: 700;
        margin-bottom: 10px;
        font-size: 1.1rem;
    }
    .guide-text {
        color: #c9d1d9 !important;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 전략 로직 (BB + MACD + RSI) ====================
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
    
    # 1. 좌측 사이드바 (한글화 및 색상 개선)
    with st.sidebar:
        st.markdown("<h1 style='color:white;'>전문 트레이더</h1>", unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("메뉴 이동", ["거래소 대시보드", "내 포트폴리오", "시스템 설정"])
        st.markdown("---")
        st.subheader("시스템 제어")
        btn_label = "🛑 시스템 정지" if d['is_active'] else "🚀 자동매매 시작"
        if st.button(btn_label, use_container_width=True, type="primary" if d['is_active'] else "secondary"):
            d['is_active'] = not d['is_active']
            st.rerun()

    # 메인 헤더 (한글화)
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
                badge = "buy-badge" if sig == "매수" else "wait-badge"
                sig_text = "매수 신호" if sig == "매수" else "감시 중"
                
                st.markdown(f"""
                <div class="coin-item">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-weight:700; font-size:1.1rem; color:white;">{t}</span><br>
                            <span style="color:#888; font-size:0.85rem;">현재가: {price:,.0f}원 | RSI: {rsi:.1f}</span>
                        </div>
                        <span class="status-badge {badge}">{sig_text}</span>
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
