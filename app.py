import streamlit as st
import pybithumb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 설정 및 다크 테마
st.set_page_config(page_title="ABISSO PREMIUM", layout="wide")

# 배경색 및 폰트 스타일 제어 (블랙 & 골드 포인트)
st.markdown("""
    <style>
    .main { background-color: #000000; color: #E5E7EB; }
    div[data-testid="stMetricValue"] { color: #F3F4F6; font-size: 24px; font-weight: bold; }
    div[data-testid="stMetricDelta"] { font-size: 16px; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #374151; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 ABISSO ASSET ENGINE")
st.caption(f"접속 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 2. 사이드바: 오빠의 실질적인 자산 설정
st.sidebar.header("📊 MY PORTFOLIO")
target_coin = st.sidebar.selectbox("종목 선택", ["BTC", "XRP", "ETH", "SOL", "ZIL"], index=0)
avg_buy_price = st.sidebar.number_input("나의 매수 평단가 (원)", value=0, step=100)
my_holdings = st.sidebar.number_input("내가 가진 수량", value=0.0, format="%.4f")

# 3. 데이터 로드 및 에러 방지 로직
try:
    current_price = pybithumb.get_current_price(target_coin)
    
    # 수익률 및 평가손익 계산
    if avg_buy_price > 0 and my_holdings > 0:
        total_buy = avg_buy_price * my_holdings
        total_now = current_price * my_holdings
        profit_percent = ((current_price - avg_buy_price) / avg_buy_price) * 100
        profit_amount = total_now - total_buy
    else:
        total_now, profit_percent, profit_amount = 0, 0.0, 0

    # 4. 상단 대시보드 (디자인 보완)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("현재 시세", f"{current_price:,} 원", f"{target_coin}")
    with col2:
        color = "normal" if profit_percent >= 0 else "inverse"
        st.metric("실시간 수익률", f"{profit_percent:.2f}%", f"{profit_amount:+,} 원", delta_color=color)
    with col3:
        st.metric("총 평가금액", f"{total_now:,.0f} 원")

    # 5. 그래프 보완 (엉성하지 않은 캔들스틱 차트)
    st.write("---")
    st.markdown("### 📈 마켓 트렌드 리포트")
    df = pybithumb.get_ohlcv(target_coin, interval="minute1").tail(40)
    
    if df is not None:
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['open'], high=df['high'],
            low=df['low'], close=df['close'],
            increasing_line_color= '#ef4444', decreasing_line_color= '#3b82f6'
        )])
        fig.update_layout(
            template="plotly_dark", 
            margin=dict(l=10, r=10, t=10, b=10),
            height=350,
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("차트 데이터를 불러오는 중입니다...")

except Exception as e:
    st.error(f"데이터 연결 중 잠시 지연이 발생했습니다. 1~2초 후 새로고침 해주세요! (사유: {e})")

st.sidebar.write("---")
st.sidebar.info("Abisso 비즈니스 엔진 최적화 모드 가동 중")
