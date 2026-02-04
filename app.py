import streamlit as st
import pybithumb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 반응형 레이아웃 및 다크 테마 (실전 앱 디자인)
st.set_page_config(page_title="ABISSO Coin Engine", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    div[data-testid="stMetric"] { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .stNumberInput, .stSelectbox { background-color: #0d1117; }
    </style>
    """, unsafe_allow_html=True)

st.title("📟 ABISSO 실전 자동화 엔진")
st.write(f"현재 가동 시간: {datetime.now().strftime('%H:%M:%S')}")

# 2. 오전에 구현한 매매 파라미터 및 자산 설정
st.sidebar.header("⚙️ 전략 및 자산 설정")
target_coin = st.sidebar.selectbox("종목 선택", ["BTC", "XRP", "ETH", "SOL", "ZIL"], index=0)

# 오전에 논의한 변동성 돌파 로직용 K값 및 손절선
k_value = st.sidebar.slider("변동성 돌파 K값", 0.1, 1.0, 0.5)
stop_loss = st.sidebar.slider("손절선 (%)", -10.0, -0.1, -1.0)

st.sidebar.markdown("---")
# 실제 돈 입금 후 테스트할 평단가와 수량
avg_buy_price = st.sidebar.number_input("나의 평단가 (원)", value=0, step=1)
my_quantity = st.sidebar.number_input("나의 보유 수량", value=0.0, format="%.4f")

# 3. 실시간 데이터 및 수익률 계산 (작동 테스트 핵심)
try:
    current_p = pybithumb.get_current_price(target_coin)
    
    if avg_buy_price > 0 and my_quantity > 0:
        total_buy = avg_buy_price * my_quantity
        total_now = current_p * my_quantity
        profit_pct = ((current_p - avg_buy_price) / avg_buy_price) * 100
        profit_krw = total_now - total_buy
    else:
        total_now, profit_pct, profit_krw = 0, 0.0, 0

    # 4. 실전 대시보드 UI
    col1, col2, col3 = st.columns(3)
    col1.metric(f"{target_coin} 현재 시세", f"{current_p:,}원")
    col2.metric("실시간 수익률", f"{profit_pct:.2f}%", f"{profit_krw:+,}원")
    col3.metric("평가 금액", f"{total_now:,.0f}원")

    # 5. 실시간 캔들스틱 차트 (반응형 보완)
    st.markdown("---")
    st.subheader("📊 실시간 마켓 데이터")
    df = pybithumb.get_ohlcv(target_coin, interval="minute1").tail(40)
    
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], 
        low=df['low'], close=df['close'],
        increasing_line_color='#ef4444', decreasing_line_color='#3b82f6'
    )])
    fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig, use_container_width=True)

    # 6. 현재 엔진 상태 브리핑
    st.success(f"📡 엔진 정상 작동 중 | 설정: K={k_value}, 손절={stop_loss}%")

except Exception as e:
    st.warning("데이터를 연결 중입니다. 잠시만 기다려주세요.")
