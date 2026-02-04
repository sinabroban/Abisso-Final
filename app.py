import streamlit as st
import pybithumb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 설정 (다크 모드 및 레이아웃)
st.set_page_config(page_title="Abisso Premium Engine", layout="wide")

# 커스텀 CSS: 블랙 & 골드 테마 적용
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #4b5563; }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 ABISSO Premium Asset Engine")
st.markdown("---")

# 2. 사이드바: 오빠의 자산 정보 입력
st.sidebar.header("💰 나의 투자 설정")
my_coin = st.sidebar.selectbox("보유 종목", ["BTC", "XRP", "ETH"])
avg_price = st.sidebar.number_input("나의 평단가 (원)", value=0, step=100)
my_quantity = st.sidebar.number_input("보유 수량", value=0.0, format="%.4f")

# 3. 실시간 데이터 계산
curr_price = pybithumb.get_current_price(my_coin)
if avg_price > 0 and my_quantity > 0:
    total_buy = avg_price * my_quantity
    total_now = curr_price * my_quantity
    profit_rate = ((curr_price - avg_price) / avg_price) * 100
    profit_krw = total_now - total_buy
else:
    profit_rate = 0.0
    profit_krw = 0

# 4. 상단 메트릭 배치
col1, col2, col3 = st.columns(3)
col1.metric("현재가", f"{curr_price:,} 원", f"{my_coin}")
col2.metric("실시간 수익률", f"{profit_rate:.2f}%", f"{profit_krw:+,} 원")
col3.metric("평가 금액", f"{total_now:,} 원")

# 5. 전문가용 캔들스틱 차트 (가상 데이터)
st.write("### 📊 마켓 분석 리포트")
df = pybithumb.get_ohlcv(my_coin, interval="minute1").tail(30)
fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['open'], high=df['high'],
                low=df['low'], close=df['close'])])
fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

st.sidebar.success("엔진 최적화 완료")
