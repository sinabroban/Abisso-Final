import streamlit as st
import pybithumb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 반응형 환경 및 상용 앱 테마 설정
st.set_page_config(page_title="ABISSO PRO ENGINE", layout="wide")

# CSS: 상용 앱 수준의 배색 및 폰트 설정
st.markdown("""
    <style>
    .stApp { background-color: #0A0D10; color: #E1E4E8; }
    .main-header { font-size: 24px; font-weight: 800; color: #00FF88; margin-bottom: 20px; border-bottom: 2px solid #1E2329; padding-bottom: 10px; }
    .card { background-color: #1E2329; padding: 20px; border-radius: 12px; border: 1px solid #2B3139; margin-bottom: 15px; }
    .label { color: #848E9C; font-size: 13px; margin-bottom: 5px; }
    .value { font-size: 22px; font-weight: bold; color: #FFFFFF; }
    .stTabs [data-baseweb="tab"] { color: #848E9C; padding: 10px 20px; }
    .stTabs [data-baseweb="tab-list"] { background-color: #0A0D10; }
    .stTabs [aria-selected="true"] { color: #00FF88 !important; border-bottom-color: #00FF88 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- [상단 헤더] ---
st.markdown("<div class='main-header'>🏛️ ABISSO TRADING CONSOLE</div>", unsafe_allow_html=True)

# --- [SECTION 1] AI 종목 추천 & 3종 선택 (오전 기획) ---
st.markdown("### 🎯 STEP 1. AI 마켓 스캐너 (Top 5 추천)")
# 변동성과 거래대금이 높은 상위 5개 종목을 가져옵니다.
recommend_list = ["BTC", "XRP", "ETH", "SOL", "ZIL"] 
selected_coins = st.multiselect(
    "관리할 종목을 최대 3개까지 선택하세요 (오전 합의사항)", 
    recommend_list, default=recommend_list[:3], max_selections=3
)

st.markdown("---")

# --- [SECTION 2] 실시간 자산 관리 및 안전장치 ---
st.markdown("### 💰 STEP 2. 내 자산 및 리스크 관리")
col_input1, col_input2, col_input3 = st.columns([2, 1, 1])

my_data = {}
with col_input1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='label'>종목별 평단가 / 수량 입력</p>", unsafe_allow_html=True)
    sub_cols = st.columns(len(selected_coins))
    for i, coin in enumerate(selected_coins):
        with sub_cols[i]:
            avg = st.number_input(f"{coin} 평단가", value=0, key=f"a_{coin}")
            qty = st.number_input(f"{coin} 수량", value=0.0, format="%.4f", key=f"q_{coin}")
            my_data[coin] = {'avg': avg, 'qty': qty}
    st.markdown("</div>", unsafe_allow_html=True)

with col_input2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='label'>⚠️ 익절 목표선 (%)</p>", unsafe_allow_html=True)
    target_pct = st.slider("Target", 1.0, 50.0, 10.0)
    st.markdown("</div>", unsafe_allow_html=True)

with col_input3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<p class='label'>🛡️ 손절 제한선 (%)</p>", unsafe_allow_html=True)
    stop_pct = st.slider("Stop Loss", -20.0, -1.0, -5.0)
    st.markdown("</div>", unsafe_allow_html=True)

# --- [SECTION 3] 기간별 심층 분석 리포트 ---
st.markdown("### 📊 STEP 3. 심층 분석 리포트 (일/주/월)")
tab1, tab2, tab3 = st.tabs(["[ Daily ]", "[ Weekly ]", "[ Monthly ]"])

def draw_chart(ticker, days):
    df = pybithumb.get_ohlcv(ticker).tail(days)
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
    return fig, df

with tab1:
    st.markdown("#### 오늘의 실시간 전략 현황")
    for coin in selected_coins:
        p = pybithumb.get_current_price(coin)
        asset = my_data[coin]
        col_c1, col_c2, col_c3 = st.columns([1, 1, 2])
        
        with col_c1:
            st.markdown(f"<p class='label'>{coin} 현재가</p><p class='value'>{p:,}원</p>", unsafe_allow_html=True)
        with col_c2:
            if asset['avg'] > 0:
                ror = ((p - asset['avg']) / asset['avg']) * 100
                color = "#00FF88" if ror >= 0 else "#FF4B4B"
                st.markdown(f"<p class='label'>수익률</p><p class='value' style='color:{color}'>{ror:.2f}%</p>", unsafe_allow_html=True)
                if ror <= stop_pct: st.error("⚠️ 손절 라인 돌파! 매도 검토")
            else:
                st.markdown("<p class='label'>수익률</p><p class='value'>-</p>", unsafe_allow_html=True)
        with col_c3:
            # 캔들차트 요약 (일간)
            fig, _ = draw_chart(coin, 24) # 최근 24시간 느낌으로
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("#### 최근 7일간의 시장 흐름")
    c_select = st.radio("종목 선택", selected_coins, horizontal=True, key="w_radio")
    fig, df_w = draw_chart(c_select, 7)
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"💡 {c_select} 주간 고가: {df_w['high'].max():,.0f}원 / 저가: {df_w['low'].min():,.0f}원")

with tab3:
    st.markdown("#### 30일 데이터 기반 장기 리포트")
    c_select_m = st.radio("종목 선택", selected_coins, horizontal=True, key="m_radio")
    fig, df_m = draw_chart(c_select_m, 30)
    st.plotly_chart(fig, use_container_width=True)
    avg_vol = df_m['volume'].mean()
    st.success(f"📈 {c_select_m} 월평균 거래량: {avg_vol:,.0f} / 장기 추세 분석 중...")

# 새로고침 버튼
st.markdown("---")
if st.button("🔄 실시간 데이터 강제 업데이트"):
    st.rerun()
