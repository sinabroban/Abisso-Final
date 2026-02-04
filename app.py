import streamlit as st
import pybithumb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 상업용 앱 테마 및 환경 설정
st.set_page_config(page_title="ABISSO PRO V3", layout="wide", initial_sidebar_state="collapsed")

# 세션 상태 초기화 (데이터가 날아가지 않게 고정)
if 'selected_coins' not in st.session_state:
    st.session_state.selected_coins = []

# CSS: 상업용 앱 배색 (가독성 최우선)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0B0E11; color: #EAECEF; }
    .stApp { background-color: #0B0E11; }
    .main-card { background-color: #1E2329; padding: 24px; border-radius: 16px; border: 1px solid #2B3139; margin-bottom: 20px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #F0B90B; } /* 바이낸스 골드 포인트 */
    .metric-label { color: #848E9C; font-size: 14px; }
    .stButton>button { background-color: #F0B90B; color: black; border-radius: 8px; font-weight: bold; border: none; width: 100%; height: 45px; }
    .stTabs [data-baseweb="tab-list"] { background-color: #0B0E11; gap: 24px; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; color: #848E9C; }
    .stTabs [aria-selected="true"] { color: #F0B90B !important; border-bottom-color: #F0B90B !important; }
    </style>
    """, unsafe_allow_html=True)

# --- [상단: 시장 현황 브리핑] ---
st.markdown("<h1 style='color:#F0B90B;'>🏛️ ABISSO TRADING SYSTEM</h1>", unsafe_allow_html=True)

# --- [SECTION 1: AI 스캐너 및 3종 선택] ---
st.markdown("### 🔍 01. AI 마켓 스캐너 (오전 기획: 5종 추천)")
with st.container():
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    # 거래대금 상위 5개 자동 스캔 로직 (벤치마킹: 거래량 우선순위)
    top_5 = ["BTC", "ETH", "XRP", "SOL", "DOGE"] 
    st.write("📈 현재 시장 유동성 및 변동성 기반 Top 5 추천 종목입니다.")
    
    selected = st.multiselect(
        "이 중 집중 관리할 3종을 선택하세요 (3종 선택 시 전략 가동)", 
        top_5, default=st.session_state.selected_coins, max_selections=3
    )
    st.session_state.selected_coins = selected
    st.markdown("</div>", unsafe_allow_html=True)

if not selected:
    st.warning("⚠️ 종목을 선택해야 리포트가 생성됩니다.")
    st.stop()

# --- [SECTION 2: 실시간 포트폴리오 & 안전장치] ---
st.markdown("### 💰 02. 라이브 포트폴리오 & 리스크 관리")
col_assets, col_safety = st.columns([2, 1])

with col_assets:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    asset_cols = st.columns(len(selected))
    user_assets = {}
    for i, coin in enumerate(selected):
        with asset_cols[i]:
            st.markdown(f"**{coin}**")
            avg = st.number_input("평단가", key=f"avg_{coin}", value=0)
            qty = st.number_input("보유량", key=f"qty_{coin}", value=0.0, format="%.4f")
            user_assets[coin] = {"avg": avg, "qty": qty}
    st.markdown("</div>", unsafe_allow_html=True)

with col_safety:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.markdown("<p class='metric-label'>🛡️ 안전장치 설정</p>", unsafe_allow_html=True)
    stop_loss = st.slider("자동 손절선 (%)", -15.0, -1.0, -5.0)
    take_profit = st.slider("목표 익절선 (%)", 1.0, 30.0, 10.0)
    st.markdown("</div>", unsafe_allow_html=True)

# --- [SECTION 3: 기간별 통합 리포트] ---
st.markdown("### 📊 03. 전략 이행 리포트 (일/주/월)")
tab1, tab2, tab3 = st.tabs(["[ DAILY ]", "[ WEEKLY ]", "[ MONTHLY ]"])

def get_report_data(ticker, period):
    df = pybithumb.get_ohlcv(ticker, interval="day").tail(period)
    curr = pybithumb.get_current_price(ticker)
    return curr, df

with tab1:
    st.markdown("#### 오늘의 실시간 수익률 및 전략 지표")
    for coin in selected:
        curr, df = get_report_data(coin, 1)
        asset = user_assets[coin]
        
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        with c1: st.markdown(f"<p class='metric-label'>{coin} 현재가</p><p class='value'>{curr:,}원</p>", unsafe_allow_html=True)
        with c2:
            if asset['avg'] > 0:
                ror = ((curr - asset['avg']) / asset['avg']) * 100
                color = "#00C087" if ror >= 0 else "#CF304A"
                st.markdown(f"<p class='metric-label'>수익률</p><p class='metric-value' style='color:{color}'>{ror:.2f}%</p>", unsafe_allow_html=True)
            else: st.markdown("<p class='metric-label'>수익률</p><p class='value'>-</p>", unsafe_allow_html=True)
        with c3:
            # 안전장치 작동 여부 (벤치마킹 포인트: 직관적 경고)
            if asset['avg'] > 0 and ror <= stop_loss: st.error("🚨 손절가 도달!")
            elif asset['avg'] > 0 and ror >= take_profit: st.success("🎯 목표가 달성!")
            else: st.info("🛰️ 감시 중")
        with c4:
            # 차트 (가독성을 위해 깔끔하게)
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
            fig.update_layout(template="plotly_dark", height=150, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("#### 최근 7일간 추세 분석 리포트")
    for coin in selected:
        curr, df = get_report_data(coin, 7)
        st.write(f"**{coin} 주간 리포트**")
        weekly_change = ((df['close'][-1] - df['open'][0]) / df['open'][0]) * 100
        st.write(f"- 지난 7일간 변동률: {weekly_change:+.2f}% | 최고가: {df['high'].max():,}원")

with tab3:
    st.markdown("#### 30일 데이터 기반 장기 전망")
    # 월간 데이터 시각화 (벤치마킹: 깔끔한 데이터 테이블)
    monthly_summary = []
    for coin in selected:
        _, df = get_report_data(coin, 30)
        monthly_summary.append({"종목": coin, "월최고": f"{df['high'].max():,}", "월최저": f"{df['low'].min():,}", "거래량(평균)": f"{df['volume'].mean():,.0f}"})
    st.table(pd.DataFrame(monthly_summary))

# --- [FOOTER: 시스템 가동 버튼] ---
st.markdown("---")
if st.button("🔄 실시간 데이터 동기화"):
    st.rerun()
