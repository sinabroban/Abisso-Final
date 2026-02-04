import streamlit as st
import pybithumb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 설정 (반응형/전체 화면)
st.set_page_config(page_title="ABISSO REAL-TIME", layout="wide")

# CSS: 화면 중앙 집중형 디자인
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    .stNumberInput input { background-color: #1a1a1a !important; color: gold !important; font-size: 20px !important; }
    div[data-testid="stMetric"] { background-color: #111; border: 2px solid #333; padding: 20px; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📟 ABISSO 실전 가동 엔진")

# 2. 화면 상단 - 바로 숫자 넣는 곳 (사이드바 아님!)
st.subheader("💰 나의 자산 설정 (여기에 숫자를 입력하세요)")
c_in1, c_in2, c_in3 = st.columns(3)

with c_in1:
    target_coin = st.selectbox("종목 선택", ["BTC", "XRP", "ETH", "SOL"], index=0)
with c_in2:
    avg_price = st.number_input("나의 평단가 (원)", value=0, step=1)
with c_in3:
    hold_qty = st.number_input("보유 수량", value=0.0, format="%.4f")

# 3. 실시간 시세 호출 및 로직
try:
    # 실시간 시세 (강제 새로고침용 타임스탬프)
    current_p = pybithumb.get_current_price(target_coin)
    
    # 변동성 돌파 목표가 계산
    df_h = pybithumb.get_ohlcv(target_coin)
    yesterday = df_h.iloc[-2]
    target_p = yesterday['close'] + (yesterday['high'] - yesterday['low']) * 0.5

    # 4. 메인 대시보드 - 실시간 변동 내용
    st.markdown("---")
    st.subheader("📡 실시간 변동 리포트")
    m1, m2, m3 = st.columns(3)

    with m1:
        st.metric("실시간 시세", f"{current_p:,} 원")
    with m2:
        if avg_price > 0 and hold_qty > 0:
            profit_rate = ((current_p - avg_price) / avg_price) * 100
            profit_krw = (current_p - avg_price) * hold_qty
            st.metric("수익률", f"{profit_rate:.2f}%", f"{profit_krw:+,} 원")
        else:
            st.metric("수익률", "입력 대기", "0 원")
    with m3:
        st.metric("목표 돌파가", f"{target_p:,.0f} 원")

    # 5. 하단 - 실시간 캔들 차트
    st.markdown("---")
    df_chart = pybithumb.get_ohlcv(target_coin, interval="minute1").tail(30)
    fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['open'], high=df_chart['high'], low=df_chart['low'], close=df_chart['close'])])
    fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error("데이터 연결 중... 잠시만 기다려주세요.")

# 1초마다 자동 새로고침을 유도하는 트리거
if st.button('🔄 시세 지금 바로 업데이트'):
    st.rerun()
