import streamlit as st
import pybithumb
import pandas as pd
import plotly.graph_objects as go
import time

# 1. 앱 기본 설정
st.set_page_config(page_title="ABISSO PRO ANALYZER", layout="wide")

# 스타일링: 가독성 높고 친절한 UI
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .big-font { font-size: 20px !important; font-weight: bold; color: #00C6FF; }
    div[data-testid="stMetric"] { background-color: #1A1C24; padding: 15px; border-radius: 10px; border-left: 5px solid #00C6FF; }
    .report-box { background-color: #262730; padding: 20px; border-radius: 10px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 ABISSO 포트폴리오 매니지먼트")
st.caption("오전 기획 반영: 5종 추천 / 3종 선택 / 기간별 리포트 / 안전장치")

# --- [STEP 1] AI 추천 5선 및 사용자 선택 (3개) ---
st.markdown("### 1️⃣ 오늘의 AI 추천 Top 5 (변동성 기반)")

# (가상 로직: 실제로는 복잡한 알고리즘이 들어가지만, 작동 확인을 위해 대장주 5개 선정)
recommendations = ["BTC", "ETH", "XRP", "SOL", "ETC"]
st.info(f"💡 시스템이 분석한 추천 종목: {', '.join(recommendations)}")

# 3개 선택 기능
selected_coins = st.multiselect(
    "위 추천 종목 중 집중 관리할 3개를 선택하세요.",
    recommendations,
    default=recommendations[:3], # 기본 3개 선택
    max_selections=3
)

if len(selected_coins) < 1:
    st.error("최소 1개 이상의 코인을 선택해주세요.")
    st.stop()

# --- [STEP 2] 자산 입력 & 안전장치 ---
st.markdown("### 2️⃣ 포트폴리오 구성 & 안전장치")

col_params, col_safety = st.columns([2, 1])

# 자산 입력 (선택한 3개 코인에 대해서만 입력창 생성)
my_assets = {}
with col_params:
    st.write("보유 자산 입력")
    cols = st.columns(len(selected_coins))
    for idx, coin in enumerate(selected_coins):
        with cols[idx]:
            st.markdown(f"**{coin} 설정**")
            avg = st.number_input(f"{coin} 평단가", value=0, key=f"p_{coin}")
            qty = st.number_input(f"{coin} 수량", value=0.0, format="%.4f", key=f"q_{coin}")
            my_assets[coin] = {'avg': avg, 'qty': qty}

# 안전장치 설정
with col_safety:
    st.write("🛡️ 안전장치 (Safety Lock)")
    stop_loss = st.slider("손절 제한선 (%)", -20.0, -1.0, -5.0, help="이 수익률 아래로 떨어지면 강력 경고가 뜹니다.")
    target_profit = st.slider("익절 목표선 (%)", 1.0, 50.0, 10.0)

# --- [STEP 3] 기간별 분석 리포트 (일간/주간/월간) ---
st.markdown("---")
st.markdown("### 3️⃣ 심층 분석 리포트")

# 탭 구성 (오빠가 원하신 기능)
tab_daily, tab_weekly, tab_monthly = st.tabs(["📅 일간 분석 (Daily)", "📊 주간 흐름 (Weekly)", "📈 월간 전망 (Monthly)"])

# 데이터 로딩 및 공통 함수
def get_market_data(ticker):
    try:
        curr = pybithumb.get_current_price(ticker)
        df = pybithumb.get_ohlcv(ticker)
        return curr, df
    except:
        return 0, None

# 1. 일간 분석 탭
with tab_daily:
    st.markdown("#### ⚡ 실시간 시세 및 오늘의 전략")
    
    # 3개 코인 나란히 보여주기
    d_cols = st.columns(3)
    for i, coin in enumerate(selected_coins):
        curr_p, df = get_market_data(coin)
        asset = my_assets[coin]
        
        # 수익률 계산
        if asset['avg'] > 0:
            ror = ((curr_p - asset['avg']) / asset['avg']) * 100
            val = (curr_p - asset['avg']) * asset['qty']
        else:
            ror, val = 0, 0
            
        with d_cols[i]:
            st.markdown(f"<div class='report-box'>", unsafe_allow_html=True)
            st.markdown(f"**{coin}**")
            st.metric("현재가", f"{curr_p:,}원")
            
            # 안전장치 가동 로직
            if ror <= stop_loss and asset['avg'] > 0:
                st.error(f"🚨 경고: 손절선({stop_loss}%) 터치!")
            elif ror >= target_profit:
                st.success(f"🎉 축하: 목표달성({target_profit}%)")
            else:
                st.metric("내 수익률", f"{ror:.2f}%", f"{val:,.0f}원")
            st.markdown("</div>", unsafe_allow_html=True)

# 2. 주간 흐름 탭
with tab_weekly:
    st.markdown("#### 🌊 최근 7일간의 추세 분석")
    coin_select = st.radio("차트 볼 종목 선택", selected_coins, horizontal=True)
    
    curr_p, df = get_market_data(coin_select)
    if df is not None:
        df_week = df.tail(7)
        fig = go.Figure(data=[go.Candlestick(x=df_week.index, open=df_week['open'], high=df_week['high'], low=df_week['low'], close=df_week['close'])])
        fig.update_layout(title=f"{coin_select} 주간 차트", template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        week_change = (df_week['close'][-1] - df_week['open'][0]) / df_week['open'][0] * 100
        st.info(f"이번 주 {coin_select} 변동률: **{week_change:+.2f}%**")

# 3. 월간 전망 탭
with tab_monthly:
    st.markdown("#### 🔭 장기 관점 및 월간 리포트")
    st.write("지난 30일간의 데이터를 기반으로 한 장기 추세입니다.")
    
    col_m1, col_m2 = st.columns([1, 1])
    # 간단한 테이블 리포트 생성
    report_data = []
    for coin in selected_coins:
        _, df = get_market_data(coin)
        if df is not None:
            month_high = df.tail(30)['high'].max()
            month_low = df.tail(30)['low'].min()
            report_data.append([coin, f"{month_high:,}원", f"{month_low:,}원"])
    
    df_report = pd.DataFrame(report_data, columns=["종목", "월 최고가", "월 최저가"])
    st.table(df_report)
    st.caption("※ 이 데이터는 과거 30일 기준이며, 미래 수익을 보장하지 않습니다.")

# 새로고침 버튼
if st.button("🔄 전체 데이터 업데이트"):
    st.rerun()
