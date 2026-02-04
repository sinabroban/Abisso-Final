import streamlit as st
import pybithumb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 및 친절한 테마 설정
st.set_page_config(page_title="Abisso Guide", layout="centered") # 집중을 위해 중앙 정렬

# CSS: 가독성과 친절함을 위한 스타일
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #E0E0E0; }
    .guide-box {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00C6FF;
        margin-bottom: 20px;
    }
    .step-header { color: #00C6FF; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
    .stButton>button {
        background: #00C6FF; color: black; font-weight: bold; width: 100%; padding: 15px;
    }
    div[data-testid="stExpander"] { background-color: #222; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💁‍♂️ ABISSO 이지 트레이딩")
st.write("반갑습니다. 처음 오셨나요? 아래 순서대로만 따라오시면 자동으로 분석해 드립니다.")

# --- [Step 1: 종목 선택 및 추천] ---
st.markdown("<div class='guide-box'>", unsafe_allow_html=True)
st.markdown("<div class='step-header'>STEP 1. 어떤 코인을 볼까요?</div>", unsafe_allow_html=True)
st.write("가장 변동성이 좋고 거래량이 많은 대장주들입니다. 하나를 골라보세요.")

selected_coin = st.selectbox("분석할 코인 선택", ["BTC (비트코인)", "ETH (이더리움)", "XRP (리플)", "SOL (솔라나)"])
coin_ticker = selected_coin.split(" ")[0] # 코드만 추출

# (오전 논의 내용: 추천 코멘트)
curr_p = pybithumb.get_current_price(coin_ticker)
st.caption(f"💡 현재 {coin_ticker}는 **{curr_p:,}원**에 거래되고 있습니다.")
st.markdown("</div>", unsafe_allow_html=True)

# --- [Step 2: 자산 입력 (설명 포함)] ---
st.markdown("<div class='guide-box'>", unsafe_allow_html=True)
st.markdown("<div class='step-header'>STEP 2. 현재 자산 상황을 알려주세요</div>", unsafe_allow_html=True)
st.write("정확한 수익률 계산을 위해 필요합니다. (저장되지 않으니 안심하세요!)")

col_input1, col_input2 = st.columns(2)
with col_input1:
    my_avg = st.number_input("내가 산 평균 가격 (원)", value=0, help="거래소 앱의 '평단가'를 입력하세요.")
with col_input2:
    my_qty = st.number_input("보유하고 있는 개수", value=0.0, format="%.4f", help="보유 수량을 정확히 적어주세요.")

if my_avg > 0 and my_qty > 0:
    profit = (curr_p - my_avg) * my_qty
    profit_pct = ((curr_p - my_avg) / my_avg) * 100
    color = "red" if profit > 0 else "blue"
    st.info(f"📊 오빠님의 현재 성적표: **{profit_pct:.2f}%** ({profit:,.0f}원)")
st.markdown("</div>", unsafe_allow_html=True)

# --- [Step 3: 전략 및 추천 (친절한 설명)] ---
st.markdown("<div class='guide-box'>", unsafe_allow_html=True)
st.markdown("<div class='step-header'>STEP 3. AI 매매 전략 추천</div>", unsafe_allow_html=True)

# 전략 설명 (K값에 대한 친절한 해설)
with st.expander("❓ '변동성 돌파 전략'이 뭔가요? (클릭)"):
    st.write("""
    어제 가격의 움직임 폭을 계산해서, 오늘 상승세가 확실할 때만 탑승하는 안전한 전략입니다.
    - **K값**은 '진입 장벽'입니다. 
    - 0.5가 가장 무난하며, 숫자가 클수록 더 안전할 때만 들어갑니다.
    """)

k_val = st.slider("안전성 조절 (K값)", 0.3, 1.0, 0.5, help="왼쪽으로 갈수록 공격적, 오른쪽으로 갈수록 보수적입니다.")

# 로직 계산
df = pybithumb.get_ohlcv(coin_ticker)
yesterday = df.iloc[-2]
range_val = yesterday['high'] - yesterday['low']
target_price = yesterday['close'] + (range_val * k_val)

st.write("---")
st.write(f"🤖 **{coin_ticker} 분석 결과 리포트**")

c1, c2 = st.columns(2)
c1.metric("오늘의 매수 목표가", f"{target_price:,.0f}원", delta="이 가격을 넘어야 상승장입니다")
c2.metric("현재 가격", f"{curr_p:,.0f}원")

# 명확한 행동 지침 (Call to Action)
if curr_p >= target_price:
    st.success(f"🚀 **[매수 추천]** 현재 가격이 목표가를 돌파했습니다! 상승 추세입니다.")
else:
    gap = target_price - curr_p
    st.warning(f"⏳ **[관망 추천]** 아직 상승세가 부족합니다. **{gap:,.0f}원** 더 오르면 그때 들어가세요.")

st.markdown("</div>", unsafe_allow_html=True)

# --- [하단: 차트 및 새로고침] ---
st.subheader("📉 실시간 차트 확인")
chart_df = pybithumb.get_ohlcv(coin_ticker, interval="minute1").tail(30)
fig = go.Figure(data=[go.Candlestick(x=chart_df.index, open=chart_df['open'], high=chart_df['high'], low=chart_df['low'], close=chart_df['close'])])
fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)

if st.button("🔄 최신 분석으로 새로고침"):
    st.rerun()
