import streamlit as st
import pybithumb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 화면 설정 (여백 제거 및 모바일 뷰 최적화)
st.set_page_config(page_title="ABISSO PRO", layout="wide")

# 2. [핵심] 상업용 앱 느낌을 내기 위한 CSS 강제 주입
# 스트림릿의 못생긴 기본 디자인을 다 가리고 커스텀 디자인을 입힙니다.
st.markdown("""
    <style>
    /* 전체 배경 블랙 */
    .stApp { background-color: #000000 !important; }
    
    /* 상단 헤더 숨기기 (앱처럼 보이게) */
    header { visibility: hidden; }
    
    /* 입력칸 스타일링 */
    .stSelectbox div[data-baseweb="select"] {
        background-color: #1E1E1E !important;
        border: 1px solid #333 !important;
        color: white !important;
    }
    .stNumberInput input {
        background-color: #1E1E1E !important;
        color: #00FF88 !important; /* 형광 그린 텍스트 */
        font-weight: bold;
        border-radius: 8px;
    }
    
    /* 메트릭 카드 디자인 (앱 위젯 느낌) */
    div[data-testid="stMetric"] {
        background-color: #111111;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricLabel"] { color: #888 !important; font-size: 0.8rem !important; }
    div[data-testid="stMetricValue"] { color: #fff !important; font-size: 1.5rem !important; }
    
    /* 버튼 스타일 (진짜 앱 버튼처럼) */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #00C6FF 0%, #0072FF 100%);
        color: white;
        border: none;
        padding: 12px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 16px;
        box-shadow: 0 4px 15px rgba(0, 114, 255, 0.4);
    }
    .stButton>button:active { transform: scale(0.98); }
    </style>
    """, unsafe_allow_html=True)

# 3. 로직 처리 (실용성)
# 오빠의 자산 상태와 목표가를 계산합니다.
target_coin = "BTC" # 기본값
current_p = pybithumb.get_current_price(target_coin)
yesterday = pybithumb.get_ohlcv(target_coin).iloc[-2]
target_p = yesterday['close'] + (yesterday['high'] - yesterday['low']) * 0.5
volatility = (yesterday['high'] - yesterday['low']) / yesterday['open'] * 100

# 4. UI 구성: 상단 타이틀 바 (앱 헤더)
st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #333; margin-bottom: 20px;'>
        <div style='font-size: 20px; font-weight: bold; color: white;'>ABISSO <span style='color: #0072FF; font-size: 12px;'>PRO</span></div>
        <div style='font-size: 12px; color: #666;'>{datetime.now().strftime('%H:%M')} 기준</div>
    </div>
    """, unsafe_allow_html=True)

# 5. 자산 입력 섹션 (카드 UI)
st.markdown("<div style='color: #888; font-size: 14px; margin-bottom: 5px;'>MY ASSETS</div>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    my_avg = st.number_input("평단가(KRW)", value=0)
with c2:
    my_qty = st.number_input("보유수량(BTC)", value=0.0, format="%.4f")

# 6. 메인 대시보드 (핵심 정보 시각화)
st.markdown("<br>", unsafe_allow_html=True)
col_main1, col_main2 = st.columns(2)

with col_main1:
    # 수익률 카드
    if my_avg > 0 and my_qty > 0:
        profit_pct = ((current_p - my_avg) / my_avg) * 100
        color = "#FF4B4B" if profit_pct < 0 else "#00FF88" # 마이너스면 빨강, 플러스면 형광초록
        st.metric("수익률", f"{profit_pct:.2f}%")
    else:
        st.metric("수익률", "0.00%")

with col_main2:
    # 현재가 카드
    st.metric(f"{target_coin} 현재가", f"{current_p:,}")

# 7. 트레이딩 신호 (실용적 기능)
signal_color = "#00FF88" if current_p >= target_p else "#444"
signal_text = "매수 체결 구간 진입" if current_p >= target_p else "진입 대기 중..."

st.markdown(f"""
    <div style='background-color: #161616; padding: 20px; border-radius: 12px; margin-top: 10px; border: 1px solid #333;'>
        <div style='color: #888; font-size: 12px;'>TRADING SIGNAL</div>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-top: 10px;'>
            <div style='font-size: 18px; color: white; font-weight: bold;'>{signal_text}</div>
            <div style='width: 15px; height: 15px; background-color: {signal_color}; border-radius: 50%; box-shadow: 0 0 10px {signal_color};'></div>
        </div>
        <div style='margin-top: 10px; font-size: 12px; color: #666;'>
            목표 돌파가: <span style='color: #ccc;'>{target_p:,.0f}원</span> <br>
            전일 변동성: <span style='color: #ccc;'>{volatility:.1f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 8. 차트 (최소화된 깔끔한 디자인)
st.markdown("<br>", unsafe_allow_html=True)
df = pybithumb.get_ohlcv(target_coin, interval="minute1").tail(30)
fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
fig.update_layout(
    template="plotly_dark", 
    paper_bgcolor='rgba(0,0,0,0)', 
    plot_bgcolor='rgba(0,0,0,0)', 
    margin=dict(l=0, r=0, t=0, b=0),
    height=250,
    xaxis_rangeslider_visible=False
)
st.plotly_chart(fig, use_container_width=True)

# 9. 하단 액션 버튼
if st.button("⚡ 엔진 데이터 새로고침"):
    st.rerun()
