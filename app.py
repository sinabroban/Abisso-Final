import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import random

# 외부 라이브러리 안전하게 불러오기
try:
    import pyupbit
except ImportError:
    pyupbit = None

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="💎 Pro Trading v2.1",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== OLED 블랙 테마 & CSS ====================
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    
    .status-bar {
        position: fixed; top: 0; left: 0; right: 0;
        background: #111; padding: 15px; z-index: 1000;
        border-bottom: 2px solid #00ff41;
        display: flex; justify-content: space-around; text-align: center;
    }
    .status-item { flex: 1; }
    .status-label { font-size: 0.75rem; color: #888; margin-bottom: 4px; }
    .status-value { font-size: 1.1rem; font-weight: 800; }
    
    .coin-card {
        background: #111; border: 1px solid #333;
        border-radius: 10px; padding: 15px; margin-bottom: 10px;
    }
    .profit { color: #00ff41 !important; }
    .loss { color: #ff0040 !important; }
    
    .stTabs [data-baseweb="tab-list"] { background-color: #000; border-bottom: 1px solid #333; }
    .stTabs [data-baseweb="tab"] { color: #888; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #00ff41; }
</style>
""", unsafe_allow_html=True)

# ==================== 세션 초기화 ====================
if 'total_cash' not in st.session_state:
    st.session_state.total_cash = 10000000.0
if 'invested_cash' not in st.session_state:
    st.session_state.invested_cash = 0.0
if 'selected_tickers' not in st.session_state:
    st.session_state.selected_tickers = []
if 'positions' not in st.session_state:
    st.session_state.positions = {} 
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'per_trade' not in st.session_state:
    st.session_state.per_trade = 1000000.0

# ==================== 유틸리티 함수 ====================
def get_korean_name(ticker):
    names = {'BTC':'비트코인','ETH':'이더리움','XRP':'리플','ADA':'에이다','DOGE':'도지코인',
             'SOL':'솔라나','DOT':'폴카닷','MATIC':'폴리곤','AVAX':'아발란체','LINK':'체인링크'}
    return names.get(ticker, ticker)

def format_krw(val):
    if val >= 100000000: return f"{val/100000000:.2f}억"
    if val >= 10000: return f"{val/10000:.0f}만"
    return f"{val:,.0f}"

def get_current_price_safe(ticker):
    """라이브러리가 없거나 에러날 때를 대비한 안전 가격 조회 (가상 데이터 포함)"""
    if pyupbit:
        try:
            p = pyupbit.get_current_price(f"KRW-{ticker}")
            if p: return p
        except:
            pass
    
    # 라이브러리가 없거나 API 에러 시 랜덤 변동 (시뮬레이션용)
    base_prices = {'BTC': 90000000, 'ETH': 3500000, 'XRP': 800, 'SOL': 150000, 'DOGE': 200, 'ADA': 600}
    base = base_prices.get(ticker, 1000)
    variation = random.uniform(-0.01, 0.01) # -1% ~ +1% 변동
    return base * (1 + variation)

# ==================== 메인 UI ====================

# 상단 상태바
stat_placeholder = st.empty()

def update_top_bar():
    current_eval_total = 0
    for t, pos in st.session_state.positions.items():
        curr_p = get_current_price_safe(t)
        current_eval_total += curr_p * pos['qty']
            
    total_asset = (st.session_state.total_cash - st.session_state.invested_cash) + current_eval_total
    profit_amt = current_eval_total - st.session_state.invested_cash
    profit_pct = (profit_amt / st.session_state.invested_cash * 100) if st.session_state.invested_cash > 0 else 0
    
    p_color = "profit" if profit_amt >= 0 else "loss"
    
    stat_placeholder.markdown(f"""
    <div class="status-bar">
        <div class="status-item">
            <div class="status-label">총 자산</div>
            <div class="status-value">{format_krw(total_asset)}원</div>
        </div>
        <div class="status-item">
            <div class="status-label">실시간 손익</div>
            <div class="status-value {p_color}">{profit_amt:+,.0f}원 ({profit_pct:+.2f}%)</div>
        </div>
        <div class="status-item">
            <div class="status-label">보유 현금</div>
            <div class="status-value">{format_krw(st.session_state.total_cash - st.session_state.invested_cash)}원</div>
        </div>
    </div>
    <div style="margin-top: 80px;"></div>
    """, unsafe_allow_html=True)

update_top_bar()

if not pyupbit:
    st.info("💡 pyupbit 라이브러리가 없어 '가상 모드'로 작동 중입니다. 실시간 가격을 연동하려면 'pip install pyupbit'를 설치하세요.")

tab1, tab2, tab3 = st.tabs(["💰 마켓", "📊 포지션", "⚙️ 설정"])

with tab1:
    st.subheader("매수할 코인을 선택하세요")
    tickers = ["BTC", "ETH", "XRP", "SOL", "DOGE", "ADA"]
    cols = st.columns(2)
    for i, t in enumerate(tickers):
        with cols[i % 2]:
            is_selected = t in st.session_state.selected_tickers
            with st.container():
                st.markdown(f"**{t}** ({get_korean_name(t)})")
                if st.button(f"{'✅ 선택해제' if is_selected else '➕ 선택하기'}", key=f"btn_{t}", use_container_width=True):
                    if is_selected:
                        st.session_state.selected_tickers.remove(t)
                    else:
                        st.session_state.selected_tickers.append(t)
                    st.rerun()

with tab2:
    if not st.session_state.positions:
        st.info("현재 보유 중인 코인이 없습니다. '설정' 탭에서 시뮬레이션을 시작하세요.")
    else:
        for t, pos in st.session_state.positions.items():
            curr_p = get_current_price_safe(t)
            eval_amt = curr_p * pos['qty']
            pft = eval_amt - pos['inv_amt']
            pft_p = (pft / pos['inv_amt']) * 100
            p_cls = "profit" if pft >= 0 else "loss"
            
            st.markdown(f"""
            <div class="coin-card">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-size:1.1rem; font-weight:bold;">{t} / KRW</span>
                    <span class="{p_cls}" style="font-weight:bold;">{pft:+,.0f}원 ({pft_p:+.2f}%)</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:10px; font-size:0.85rem; color:#888;">
                    <span>평단가: {pos['buy_price']:,.0f}</span>
                    <span>현재가: {curr_p:,.0f}</span>
                    <span>평가금: {format_krw(eval_amt)}원</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

with tab3:
    st.session_state.total_cash = st.number_input("💵 초기 자본 설정", value=int(st.session_state.total_cash), step=1000000)
    st.session_state.per_trade = st.number_input("🎯 코인별 투자금", value=int(st.session_state.per_trade), step=100000)
    
    st.divider()
    
    if st.session_state.is_running:
        if st.button("🛑 시뮬레이션 중지", use_container_width=True, type="primary"):
            st.session_state.is_running = False
            st.session_state.positions = {} 
            st.session_state.invested_cash = 0
            st.rerun()
    else:
        if st.button("🚀 시뮬레이션 시작", use_container_width=True):
            if not st.session_state.selected_tickers:
                st.warning("먼저 마켓 탭에서 코인을 선택하세요!")
            else:
                st.session_state.invested_cash = 0
                for t in st.session_state.selected_tickers:
                    price = get_current_price_safe(t)
                    qty = st.session_state.per_trade / price
                    st.session_state.positions[t] = {
                        'buy_price': price,
                        'qty': qty,
                        'inv_amt': st.session_state.per_trade
                    }
                    st.session_state.invested_cash += st.session_state.per_trade
                st.session_state.is_running = True
                st.rerun()

# ==================== 실시간 갱신 루프 ====================
if st.session_state.is_running:
    time.sleep(1) # 1초마다 갱신
    st.rerun()
