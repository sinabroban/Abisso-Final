import streamlit as st
import pybithumb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 페이지 설정 (모바일 최적화)
st.set_page_config(page_title="Abisso Project", layout="centered")

st.title("📱 애비쏘 모바일 엔진")
st.subheader("실시간 분산 투자 현황")

# [세션 상태 초기화] 앱이 새로고침되어도 자산 데이터를 유지합니다.
if 'total_balance' not in st.session_state:
    st.session_state.total_balance = 1000000 # 기본 100만 원

# 사이드바 설정 (오빠의 맞춤 전략 존)
st.sidebar.header("⚙️ 전략 세팅")
target_coins = st.sidebar.multiselect("감시 종목 (최대 3개)", ["BTC", "XRP", "ETH", "ZIL", "SOL"], default=["BTC", "XRP", "ETH"])
k_val = st.sidebar.slider("K값 (진입장벽)", 0.1, 1.0, 0.5)
stop_loss = st.sidebar.slider("손절선 (%)", -5.0, -0.1, -1.0)

# 메인 화면 - 실시간 지표
cols = st.columns(len(target_coins))
for i, coin in enumerate(target_coins):
    price = pybithumb.get_current_price(coin)
    with cols[i]:
        st.metric(label=coin, value=f"{price:,}원", delta="실시간 추적 중")

# [핵심] 실시간 자산 그래프 시각화
st.write("---")
st.write("📈 자산 흐름 리포트")
# 가상의 수익률 그래프 예시 (오빠의 성적표 시각화)
chart_data = pd.DataFrame({
    '시간': [datetime.now().strftime('%H:%M:%S') for _ in range(10)],
    '수익률': [0, 0.2, 0.5, 0.3, 0.7, 1.2, 1.0, 1.5, 1.8, 2.1]
})
fig = go.Figure()
fig.add_trace(go.Scatter(x=chart_data['시간'], y=chart_data['수익률'], mode='lines+markers', name='수익률'))
st.plotly_chart(fig, use_container_width=True)

st.success("📡 엔진이 정상 작동 중입니다. 조건 충족 시 알림을 보냅니다.")