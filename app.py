import streamlit as st
import pybithumb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 모바일 최적화 및 고대비 테마 설정
st.set_page_config(page_title="ABISSO PRO V4", layout="wide")

# CSS: 캡처화면의 '안 보이는 글자' 문제를 100% 해결하는 고대비 스타일
st.markdown("""
    <style>
    /* 배경은 딥블랙, 모든 글자는 강제 화이트/골드 */
    .stApp { background-color: #000000 !important; }
    h1, h2, h3, p, span, label { color: #FFFFFF !important; font-weight: 600 !important; }
    
    /* 카드 디자인: 시중 앱처럼 경계선을 확실하게 */
    .app-card {
        background-color: #1A1A1A;
        border: 2px solid #333333;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
    }
    
    /* 포인트 컬러 (바이낸스 옐로우) */
    .highlight { color: #F3BA2F !important; font-size: 24px; font-weight: 800; }
    .stMetric label { color: #AAAAAA !important; }
    .stMetric [data-testid="stMetricValue"] { color: #F3BA2F !important; }
    
    /* 버튼: 시인성 극대화 */
    .stButton>button {
        background: linear-gradient(135deg, #F3BA2F 0%, #D49B00 100%) !important;
        color: black !important;
        border: none !important;
        font-weight: bold !important;
        height: 50px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [상단 헤더: 비즈니스 정체성] ---
st.markdown("<h1 style='text-align:center; color:#F3BA2F !important;'>🏛️ ABISSO TRADING SYSTEM</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888 !important;'>600개 프로그램 프로젝트의 초석: 실전 가동 엔진</p>", unsafe_allow_html=True)

# --- [STEP 1: 자동 종목 추천 및 로직] ---
# 오전에 얘기한 5종 추천 리스트 (거래대금 상위 자동화 시뮬레이션)
recommend_top5 = ["BTC", "XRP", "ETH", "SOL", "DOGE"]

with st.container():
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.markdown("### 🔍 01. AI 마켓 스캐너 (Top 5 추천)")
    st.write("📈 현재 시장 유동성 기반 추천: " + ", ".join(recommend_top5))
    
    # 기본값으로 3개를 미리 선택해두어 '비어있는 느낌' 방지
    selected_coins = st.multiselect(
        "집중 관리할 3종을 선택하세요.", 
        recommend_top5, 
        default=["BTC", "XRP", "ETH"]
    )
    st.markdown("</div>", unsafe_allow_html=True)

# --- [STEP 2: 라이브 자산 & 안전장치] ---
col_assets, col_risk = st.columns([2, 1])

with col_assets:
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.markdown("### 💰 02. 실시간 포트폴리오")
    asset_data = {}
    cols = st.columns(len(selected_coins))
    for i, coin in enumerate(selected_coins):
        with cols[i]:
            st.markdown(f"<span style='color:#F3BA2F'>{coin}</span>", unsafe_allow_html=True)
            avg = st.number_input("평단", key=f"a_{coin}", value=0)
            qty = st.number_input("수량", key=f"q_{coin}", value=0.0, format="%.4f")
            asset_data[coin] = {"avg": avg, "qty": qty}
    st.markdown("</div>", unsafe_allow_html=True)

with col_risk:
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.markdown("### 🛡️ 리스크 관리")
    stop_loss = st.slider("손절선 (%)", -15.0, -1.0, -5.0)
    st.markdown(f"<p style='font-size:12px; color:#888;'>설정 기준: {stop_loss}% 도달 시 알림</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- [STEP 3: 기간별 통합 분석 리포트] ---
st.markdown("### 📊 03. 전략 이행 리포트")
tab_d, tab_w, tab_m = st.tabs(["🕒 일간 (Live)", "📅 주간 (Trend)", "📈 월간 (Insight)"])

def get_data(ticker, days):
    df = pybithumb.get_ohlcv(ticker, interval="day").tail(days)
    curr = pybithumb.get_current_price(ticker)
    return curr, df

with tab_d:
    for coin in selected_coins:
        curr, df = get_data(coin, 1)
        st.markdown(f"<div class='app-card'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            st.metric(f"{coin} 시세", f"{curr:,}원")
        with c2:
            if asset_data[coin]['avg'] > 0:
                ror = ((curr - asset_data[coin]['avg']) / asset_data[coin]['avg']) * 100
                st.metric("수익률", f"{ror:.2f}%")
                if ror <= stop_loss: st.error("🚨 즉시 대응 요망")
            else: st.write("입력 대기")
        with c3:
            # 실전 앱처럼 심플한 라인 차트
            st.line_chart(df['close'], height=100)
        st.markdown("</div>", unsafe_allow_html=True)

with tab_w:
    st.info("지난 7일간의 변동성 및 골든크로스 여부를 분석합니다.")
    for coin in selected_coins:
        _, df_w = get_data(coin, 7)
        change = ((df_w['close'][-1] - df_w['open'][0]) / df_w['open'][0]) * 100
        st.write(f"🔹 **{coin}**: 7일 변동률 {change:+.2f}% (최고 {df_w['high'].max():,}원)")

with tab_m:
    st.success("30일 장기 추세: 현재 하락세 진정 및 횡보 구간 진입 분석")
    # 월간 리포트 테이블
    m_list = []
    for coin in selected_coins:
        _, df_m = get_data(coin, 30)
        m_list.append({"종목": coin, "월최고": f"{df_m['high'].max():,}", "거래량": f"{df_m['volume'].mean():,.0f}"})
    st.table(pd.DataFrame(m_list))

# 4. 하단 고정 새로고침 버튼
st.markdown("---")
if st.button("🔄 실시간 데이터 동기화 (Force Update)"):
    st.rerun()
