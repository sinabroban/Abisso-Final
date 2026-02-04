import streamlit as st
import pybithumb
import time
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# [핵심 로직] 변동성 돌파 및 자산 관리 클래스 (A4 수십 장 분량의 시작점)
class AbissoEngine:
    def __init__(self, ticker, k, sl):
        self.ticker = ticker
        self.k = k
        self.sl = sl
        
    def get_target_price(self):
        try:
            df = pybithumb.get_ohlcv(self.ticker)
            yesterday = df.iloc[-2]
            return yesterday['close'] + (yesterday['high'] - yesterday['low']) * self.k
        except: return 0

    def get_balance(self):
        # 실제 API 키 연동 시 잔고 호출 로직 (오빠의 실전 입금 대비)
        return 1000000 # 테스트용 가상 잔고

# 1. 반응형 인프라 설정
st.set_page_config(page_title="ABISSO MAIN SYSTEM", layout="wide")

# 2. 비즈니스 대시보드 레이아웃
st.title("🏛️ ABISSO 통합 비즈니스 관제 센터")

# 상단: 실시간 핵심 지표 (가장 중요한 숫자들)
head1, head2, head3, head4 = st.columns(4)

# 3. 입력 제어판 (모든 버튼과 수치 입력 집중)
with st.container():
    st.markdown("### 🛠️ 시스템 제어 및 자산 설정")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ticker = st.selectbox("집중 감시 종목", ["BTC", "XRP", "ETH", "SOL"])
    with col2:
        k_val = st.number_input("변동성 돌파 K값", value=0.5, step=0.1)
    with col3:
        avg_p = st.number_input("실제 매수 평단가", value=0)
    with col4:
        qty = st.number_input("보유 수량", value=0.0, format="%.4f")

# 4. 실시간 엔진 가동 데이터 로드
engine = AbissoEngine(ticker, k_val, 0)
curr_p = pybithumb.get_current_price(ticker)
target_p = engine.get_target_price()

# 5. 메인 디스플레이 (작동 확인 섹션)
with head1: st.metric("현재가", f"{curr_p:,}원")
with head2: st.metric("매수 목표가", f"{target_p:,.0f}원")
with head3: 
    p_rate = ((curr_p - avg_p) / avg_p * 100) if avg_p > 0 else 0
    st.metric("실시간 수익률", f"{p_rate:.2f}%")
with head4: 
    status = "🚨 진입 대기" if curr_p < target_p else "🔥 돌파! 매수 실행"
    st.metric("시스템 상태", status)

# 6. 전문가용 데이터 분석 탭 (반응형 최적화)
tab_chart, tab_log, tab_order = st.tabs(["📊 정밀 분석 차트", "📋 시스템 로그", "💸 거래 주문"])

with tab_chart:
    df = pybithumb.get_ohlcv(ticker, interval="minute1").tail(60)
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with tab_log:
    st.write("시스템 가동 이후 모든 변동 사항을 기록합니다.")
    log_data = pd.DataFrame({
        "시간": [datetime.now().strftime("%H:%M:%S")],
        "상태": [f"{ticker} 시세 추적 중..."],
        "내용": [f"현재가: {curr_p} / 목표가: {target_p}"]
    })
    st.table(log_data)

with tab_order:
    st.warning("⚠️ 실제 거래를 위해 빗썸 API Key 연결이 필요합니다.")
    st.button(f"{ticker} 시장가 매수 실행")
    st.button(f"{ticker} 전량 매도 (익절/손절)")

# 자동 새로고침 트리거
st.empty()
time.sleep(1)
if st.button('🔄 시스템 데이터 강제 갱신'):
    st.rerun()
