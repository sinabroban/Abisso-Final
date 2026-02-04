import streamlit as st
import pybithumb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# 1. 앱 설정 및 모바일 최적화 레이아웃
st.set_page_config(page_title="ABISSO PRO ENGINE", layout="centered")

# CSS: 실제 금융 앱처럼 묵직하고 깔끔한 디자인
st.markdown("""
    <style>
    .stApp { background-color: #050505; }
    .main-card { background-color: #1a1a1a; padding: 20px; border-radius: 15px; border-left: 5px solid #FFD700; }
    div[data-testid="stMetric"] { background-color: #111; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 ABISSO 실전 자산 엔진")

# 2. 자산 입력 섹션 (세션 상태 유지)
with st.expander("💰 나의 실전 자산 설정", expanded=True):
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        avg_price = st.number_input("평단가 (원)", value=0, step=1, help="실제 매수한 평균 단가를 입력하세요.")
    with col_in2:
        amount = st.number_input("보유수량", value=0.0, format="%.4f")
    
    target_coin = st.selectbox("추적 종목", ["BTC", "XRP", "ETH", "SOL"], index=0)

# 3. 실시간 데이터 호출 (안전 로직 적용)
def get_safe_price(ticker):
    try:
        p = pybithumb.get_current_price(ticker)
        return p if p is not None else 0
    except:
        return 0

curr_p = get_safe_price(target_coin)

# 4. 실전 수익 계산
if avg_price > 0 and amount > 0:
    buy_total = avg_price * amount
    now_total = curr_p * amount
    profit_pct = ((curr_p - avg_price) / avg_price) * 100
    profit_krw = now_total - buy_total
else:
    now_total, profit_pct, profit_krw = 0, 0.0, 0

# 5. 메인 대시보드
st.markdown(f"### {target_coin} 투자 현황")
c1, c2 = st.columns(2)
c1.metric("현재가", f"{curr_p:,}원")
c2.metric("수익률", f"{profit_pct:.2f}%", f"{profit_krw:+,}원")

st.metric("총 평가금액", f"{now_total:,.0f}원")

# 6. 실시간 차트 (데이터 로딩 최적화)
st.write("---")
st.write("📈 실시간 흐름분석")
try:
    df = pybithumb.get_ohlcv(target_coin, interval="minute1").tail(30)
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
    fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
except:
    st.info("데이터를 불러오는 중입니다... 잠시만 기다려주세요.")

# 7. 하단 안내 (비즈니스 모드)
st.caption("본 앱은 실전 테스트용이며, 모든 데이터는 빗썸 시세를 기준으로 합니다.")
