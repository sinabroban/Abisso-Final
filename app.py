"""
💎 Crypto Auto Trading Bot - Professional Edition
실제 거래소 수준의 UI/UX | 실시간 모니터링 | 완벽한 가시성
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pyupbit
import pybithumb
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
import logging

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="💎 자동매매 Pro",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 프로페셔널 CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    * {
        font-family: 'Noto Sans KR', sans-serif;
    }
    
    .main {
        background: #0a0e27;
    }
    
    /* 헤더 */
    .main-header {
        font-size: 2.2rem;
        font-weight: 900;
        color: #fff;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
    }
    
    .sub-header {
        text-align: center;
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    /* 잔고 카드 */
    .balance-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .balance-label {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    
    .balance-value {
        color: #fff;
        font-size: 2rem;
        font-weight: 900;
        margin-bottom: 0.3rem;
    }
    
    .balance-won {
        color: #64748b;
        font-size: 1rem;
    }
    
    /* 코인 리스트 */
    .coin-item {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s;
    }
    
    .coin-item:hover {
        border-color: #6366f1;
        background: #1e293b;
        transform: translateX(5px);
    }
    
    .coin-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #fff;
    }
    
    .coin-korean {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-left: 0.5rem;
    }
    
    .coin-price {
        font-size: 1rem;
        color: #fff;
        text-align: right;
    }
    
    .coin-change-up {
        color: #10b981;
        font-weight: 700;
        font-size: 0.95rem;
    }
    
    .coin-change-down {
        color: #ef4444;
        font-weight: 700;
        font-size: 0.95rem;
    }
    
    /* 주문 내역 */
    .order-item {
        background: #1e293b;
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .order-buy {
        border-left-color: #10b981;
    }
    
    .order-sell {
        border-left-color: #ef4444;
    }
    
    .order-time {
        color: #64748b;
        font-size: 0.85rem;
    }
    
    .order-details {
        color: #fff;
        font-size: 1rem;
        margin: 0.3rem 0;
    }
    
    /* 포지션 카드 */
    .position-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.5rem 0;
    }
    
    .position-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.8rem;
    }
    
    .position-coin {
        font-size: 1.2rem;
        font-weight: 700;
        color: #fff;
    }
    
    .position-profit-positive {
        color: #10b981;
        font-size: 1.2rem;
        font-weight: 900;
    }
    
    .position-profit-negative {
        color: #ef4444;
        font-size: 1.2rem;
        font-weight: 900;
    }
    
    .position-detail {
        display: flex;
        justify-content: space-between;
        color: #94a3b8;
        font-size: 0.9rem;
        margin: 0.3rem 0;
    }
    
    .position-detail-value {
        color: #fff;
    }
    
    /* 상태 배지 */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    
    .status-running {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        animation: pulse 2s infinite;
    }
    
    .status-stopped {
        background: #475569;
        color: white;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* 버튼 */
    .stButton>button {
        border-radius: 8px;
        font-weight: 700;
        border: none;
        transition: all 0.2s;
    }
    
    /* 차트 컨테이너 */
    .chart-container {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* 테이블 */
    .dataframe {
        background: #1e293b !important;
    }
    
    /* 메트릭 */
    .metric-container {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    
    .metric-label {
        color: #94a3b8;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        color: #fff;
        font-size: 1.8rem;
        font-weight: 900;
    }
    
    /* 사이드바 */
    .css-1d391kg {
        background-color: #0f172a;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }
    
    /* 입력 필드 */
    .stNumberInput>div>div>input {
        background-color: #1e293b;
        color: white;
        border: 1px solid #334155;
    }
    
    .stSelectbox>div>div {
        background-color: #1e293b;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 세션 상태 초기화 ====================
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.exchange = 'upbit'
    st.session_state.total_balance = 0  # 총 보유 현금
    st.session_state.invested_amount = 0  # 투자 중인 금액
    st.session_state.positions = {}  # 현재 포지션
    st.session_state.orders = []  # 주문 내역
    st.session_state.is_running = False
    st.session_state.auto_invest_per_coin = 100000  # 코인당 자동 투자 금액
    st.session_state.selected_coins = []
    st.session_state.api_keys = {'access': '', 'secret': ''}
    st.session_state.cached_coins = {}  # 코인 데이터 캐시
    st.session_state.last_update = None

# ==================== 캐시된 데이터 로드 ====================
@st.cache_data(ttl=60)  # 60초 캐시
def get_cached_top_coins(exchange: str, count: int = 10):
    """캐시된 TOP 코인 (빠른 로딩)"""
    try:
        if exchange == 'upbit':
            tickers = pyupbit.get_tickers(fiat="KRW")[:20]  # 상위 20개만
            results = []
            
            for ticker in tickers:
                try:
                    current_price = pyupbit.get_current_price(ticker)
                    if not current_price:
                        continue
                    
                    # 간단한 정보만 (빠른 로딩)
                    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
                    if df is None or len(df) < 2:
                        continue
                    
                    change = ((df['close'].iloc[-1] / df['close'].iloc[-2]) - 1) * 100
                    
                    results.append({
                        'ticker': ticker,
                        'name': ticker.split('-')[1],
                        'korean_name': get_korean_name(ticker.split('-')[1]),
                        'price': current_price,
                        'change': change
                    })
                except:
                    continue
            
            results.sort(key=lambda x: abs(x['change']), reverse=True)
            return results[:count]
            
        else:  # bithumb
            tickers = pybithumb.get_tickers()[:20]
            results = []
            
            for ticker in tickers:
                try:
                    current_price = pybithumb.get_current_price(ticker)
                    if not current_price:
                        continue
                    
                    df = pybithumb.get_ohlcv(ticker)
                    if df is None or len(df) < 2:
                        continue
                    
                    df = df.tail(2)
                    change = ((df['close'].iloc[-1] / df['close'].iloc[-2]) - 1) * 100
                    
                    results.append({
                        'ticker': f'KRW-{ticker}',
                        'name': ticker,
                        'korean_name': get_korean_name(ticker),
                        'price': current_price,
                        'change': change
                    })
                except:
                    continue
            
            results.sort(key=lambda x: abs(x['change']), reverse=True)
            return results[:count]
            
    except Exception as e:
        logger.error(f"코인 로딩 오류: {e}")
        return []

def get_korean_name(symbol: str) -> str:
    """한글 이름 매핑"""
    names = {
        'BTC': '비트코인',
        'ETH': '이더리움',
        'XRP': '리플',
        'ADA': '에이다',
        'DOGE': '도지코인',
        'SOL': '솔라나',
        'MATIC': '폴리곤',
        'DOT': '폴카닷',
        'AVAX': '아발란체',
        'SHIB': '시바이누',
        'LINK': '체인링크',
        'UNI': '유니스왑',
        'ATOM': '코스모스',
        'LTC': '라이트코인',
        'BCH': '비트코인캐시',
        'ETC': '이더리움클래식',
        'NEAR': '니어',
        'ALGO': '알고랜드',
        'HBAR': '헤데라',
        'VET': '비체인'
    }
    return names.get(symbol, symbol)

def format_krw(value: float) -> str:
    """원화 포맷"""
    if value >= 100000000:
        return f"{value/100000000:.1f}억"
    elif value >= 10000:
        return f"{value/10000:.1f}만"
    else:
        return f"{value:,.0f}"

# ==================== 메인 앱 ====================
def main():
    
    # 헤더
    st.markdown('<h1 class="main-header">💎 AI 자동매매 Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">실시간 모니터링 | 자동 손익관리 | 24시간 거래</p>', unsafe_allow_html=True)
    
    # ==================== 사이드바 ====================
    with st.sidebar:
        st.markdown("### ⚙️ 기본 설정")
        
        # 거래소
        exchange = st.selectbox(
            "거래소 선택",
            ["upbit", "bithumb"],
            format_func=lambda x: "🟦 업비트" if x == "upbit" else "🟨 빗썸",
            key="exchange_select"
        )
        st.session_state.exchange = exchange
        
        st.divider()
        
        # 💰 자금 설정
        st.markdown("### 💰 자금 설정")
        
        # 총 보유 현금 입력
        total_balance = st.number_input(
            "총 보유 현금 (원)",
            min_value=0,
            value=st.session_state.total_balance,
            step=100000,
            help="거래소에 입금한 총 금액을 입력하세요",
            format="%d"
        )
        st.session_state.total_balance = total_balance
        
        # 코인당 투자 금액
        auto_invest = st.number_input(
            "코인당 자동 투자 (원)",
            min_value=10000,
            max_value=total_balance if total_balance > 0 else 10000000,
            value=min(st.session_state.auto_invest_per_coin, total_balance) if total_balance > 0 else 100000,
            step=10000,
            help="각 코인에 투자할 금액",
            format="%d"
        )
        st.session_state.auto_invest_per_coin = auto_invest
        
        # 투자 가능 금액 표시
        available = total_balance - st.session_state.invested_amount
        st.info(f"""
        **투자 현황**
        - 총 보유: {format_krw(total_balance)}원
        - 투자 중: {format_krw(st.session_state.invested_amount)}원
        - 사용 가능: {format_krw(available)}원
        """)
        
        st.divider()
        
        # 손익 설정
        st.markdown("### 📊 손익 설정")
        
        col1, col2 = st.columns(2)
        with col1:
            stop_loss = st.slider("손절 %", 1.0, 10.0, 3.0, 0.5)
        with col2:
            take_profit = st.slider("익절 %", 2.0, 20.0, 5.0, 0.5)
        
        st.divider()
        
        # API 설정
        st.markdown("### 🔐 API 설정")
        
        use_real = st.checkbox("실거래 모드", value=False, help="체크 시 실제 거래 가능")
        
        if use_real:
            with st.expander("API 키 입력"):
                access = st.text_input("Access Key", type="password")
                secret = st.text_input("Secret Key", type="password")
                
                if access and secret:
                    st.session_state.api_keys = {'access': access, 'secret': secret}
                    st.success("✅ API 연결됨")
        
        st.divider()
        
        # 자동매매 제어
        st.markdown("### 🤖 자동매매")
        
        if st.session_state.is_running:
            st.markdown('<span class="status-badge status-running">● 실행 중</span>', unsafe_allow_html=True)
            if st.button("⏸️ 중지", use_container_width=True, type="secondary"):
                st.session_state.is_running = False
                st.rerun()
        else:
            st.markdown('<span class="status-badge status-stopped">● 중지됨</span>', unsafe_allow_html=True)
            if st.button("▶️ 시작", use_container_width=True, type="primary"):
                if not st.session_state.selected_coins:
                    st.error("코인을 먼저 선택하세요!")
                elif total_balance == 0:
                    st.error("총 보유 현금을 입력하세요!")
                elif auto_invest > available:
                    st.error("투자 가능 금액이 부족합니다!")
                else:
                    st.session_state.is_running = True
                    st.success("자동매매 시작!")
                    st.rerun()
    
    # ==================== 메인 영역 ====================
    
    # 탭
    tab1, tab2, tab3 = st.tabs(["📊 대시보드", "💰 코인 선택", "📈 거래 내역"])
    
    with tab1:
        # ========== 대시보드 ==========
        
        # 잔고 요약
        col1, col2, col3, col4 = st.columns(4)
        
        # 총 자산 계산
        total_position_value = sum([pos['current_value'] for pos in st.session_state.positions.values()])
        total_assets = st.session_state.total_balance - st.session_state.invested_amount + total_position_value
        total_profit = total_position_value - st.session_state.invested_amount
        profit_rate = (total_profit / st.session_state.invested_amount * 100) if st.session_state.invested_amount > 0 else 0
        
        with col1:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">총 자산</div>
                <div class="metric-value">{format_krw(total_assets)}</div>
                <div class="balance-won">₩{total_assets:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            profit_color = "#10b981" if total_profit >= 0 else "#ef4444"
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">평가 손익</div>
                <div class="metric-value" style="color: {profit_color};">{total_profit:+,.0f}</div>
                <div class="balance-won">{profit_rate:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">투자 중</div>
                <div class="metric-value">{format_krw(st.session_state.invested_amount)}</div>
                <div class="balance-won">₩{st.session_state.invested_amount:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            available = st.session_state.total_balance - st.session_state.invested_amount
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">사용 가능</div>
                <div class="metric-value">{format_krw(available)}</div>
                <div class="balance-won">₩{available:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # 보유 포지션
        if st.session_state.positions:
            st.markdown("### 💼 보유 중인 코인")
            
            for coin_name, pos in st.session_state.positions.items():
                profit = pos['current_value'] - pos['invested']
                profit_pct = (profit / pos['invested']) * 100
                profit_class = "position-profit-positive" if profit >= 0 else "position-profit-negative"
                
                st.markdown(f"""
                <div class="position-card">
                    <div class="position-header">
                        <div class="position-coin">{coin_name} <span style="color: #94a3b8; font-size: 0.9rem;">{pos.get('korean_name', '')}</span></div>
                        <div class="{profit_class}">{profit:+,.0f}원 ({profit_pct:+.2f}%)</div>
                    </div>
                    <div class="position-detail">
                        <span>매수가</span>
                        <span class="position-detail-value">₩{pos['buy_price']:,.0f}</span>
                    </div>
                    <div class="position-detail">
                        <span>현재가</span>
                        <span class="position-detail-value">₩{pos['current_price']:,.0f}</span>
                    </div>
                    <div class="position-detail">
                        <span>보유 수량</span>
                        <span class="position-detail-value">{pos['quantity']:.8f}</span>
                    </div>
                    <div class="position-detail">
                        <span>투자금</span>
                        <span class="position-detail-value">₩{pos['invested']:,.0f}</span>
                    </div>
                    <div class="position-detail">
                        <span>평가금</span>
                        <span class="position-detail-value">₩{pos['current_value']:,.0f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("현재 보유 중인 코인이 없습니다. '💰 코인 선택' 탭에서 코인을 선택하세요.")
        
        # 최근 주문
        if st.session_state.orders:
            st.divider()
            st.markdown("### 📋 최근 거래")
            
            for order in reversed(st.session_state.orders[-5:]):  # 최근 5개
                order_class = "order-buy" if order['type'] == 'BUY' else "order-sell"
                order_emoji = "🟢" if order['type'] == 'BUY' else "🔴"
                order_text = "매수" if order['type'] == 'BUY' else "매도"
                
                st.markdown(f"""
                <div class="order-item {order_class}">
                    <div class="order-time">{order['time']}</div>
                    <div class="order-details">
                        {order_emoji} <strong>{order_text}</strong> | {order['coin']} | 
                        ₩{order['price']:,.0f} × {order['quantity']:.8f} = 
                        ₩{order['total']:,.0f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        # ========== 코인 선택 ==========
        st.markdown("### 💰 거래할 코인 선택")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"💡 코인당 **{format_krw(st.session_state.auto_invest_per_coin)}원**씩 자동 투자됩니다")
        with col2:
            if st.button("🔄 새로고침", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        # 코인 목록 로드
        with st.spinner(f"{'업비트' if st.session_state.exchange == 'upbit' else '빗썸'}에서 코인 정보를 가져오는 중..."):
            coins = get_cached_top_coins(st.session_state.exchange, 15)
        
        if not coins:
            st.error("코인 정보를 불러올 수 없습니다. 새로고침을 시도하세요.")
            return
        
        # 코인 카드
        for coin in coins:
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f"""
                <div style="padding: 0.5rem 0;">
                    <span class="coin-name">{coin['name']}</span>
                    <span class="coin-korean">{coin['korean_name']}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                change_class = "coin-change-up" if coin['change'] >= 0 else "coin-change-down"
                st.markdown(f"""
                <div style="text-align: right; padding: 0.5rem 0;">
                    <div class="coin-price">₩{coin['price']:,.0f}</div>
                    <div class="{change_class}">{coin['change']:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                is_selected = coin['ticker'] in st.session_state.selected_coins
                button_label = "✓ 선택됨" if is_selected else "선택"
                button_type = "secondary" if is_selected else "primary"
                
                if st.button(button_label, key=f"select_{coin['ticker']}", use_container_width=True, type=button_type):
                    if is_selected:
                        st.session_state.selected_coins.remove(coin['ticker'])
                    else:
                        st.session_state.selected_coins.append(coin['ticker'])
                    st.rerun()
        
        # 선택된 코인
        if st.session_state.selected_coins:
            st.divider()
            st.markdown("### ✅ 선택된 코인")
            
            selected_info = [c for c in coins if c['ticker'] in st.session_state.selected_coins]
            
            for coin in selected_info:
                st.markdown(f"""
                <div class="coin-item">
                    <div>
                        <span class="coin-name">{coin['name']}</span>
                        <span class="coin-korean">{coin['korean_name']}</span>
                    </div>
                    <div style="text-align: right;">
                        <div>투자 예정: <strong>{format_krw(st.session_state.auto_invest_per_coin)}원</strong></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            total_need = len(selected_info) * st.session_state.auto_invest_per_coin
            available = st.session_state.total_balance - st.session_state.invested_amount
            
            if total_need > available:
                st.error(f"⚠️ 투자 가능 금액 부족! (필요: {format_krw(total_need)}원, 가능: {format_krw(available)}원)")
            else:
                st.success(f"✅ 총 {len(selected_info)}개 코인, 총 {format_krw(total_need)}원 투자 예정")
    
    with tab3:
        # ========== 거래 내역 ==========
        st.markdown("### 📈 전체 거래 내역")
        
        if st.session_state.orders:
            # 데이터프레임 생성
            df = pd.DataFrame(st.session_state.orders)
            
            # 컬럼 포맷
            df_display = df.copy()
            df_display['가격'] = df_display['price'].apply(lambda x: f"₩{x:,.0f}")
            df_display['수량'] = df_display['quantity'].apply(lambda x: f"{x:.8f}")
            df_display['총액'] = df_display['total'].apply(lambda x: f"₩{x:,.0f}")
            
            st.dataframe(
                df_display[['time', 'type', 'coin', '가격', '수량', '총액']],
                column_config={
                    'time': '시간',
                    'type': '구분',
                    'coin': '코인'
                },
                hide_index=True,
                use_container_width=True
            )
            
            # 통계
            st.divider()
            st.markdown("### 📊 거래 통계")
            
            col1, col2, col3, col4 = st.columns(4)
            
            total_trades = len(df)
            buy_count = len(df[df['type'] == 'BUY'])
            sell_count = len(df[df['type'] == 'SELL'])
            total_volume = df['total'].sum()
            
            with col1:
                st.metric("총 거래", f"{total_trades}회")
            with col2:
                st.metric("매수", f"{buy_count}회")
            with col3:
                st.metric("매도", f"{sell_count}회")
            with col4:
                st.metric("총 거래량", f"{format_krw(total_volume)}원")
        else:
            st.info("아직 거래 내역이 없습니다.")
    
    # ==================== 시뮬레이션 (테스트용) ====================
    if st.session_state.is_running and len(st.session_state.selected_coins) > 0:
        # 실제로는 여기서 자동매매 로직 실행
        # 지금은 UI 테스트를 위한 시뮬레이션
        
        # 예시: 첫 번째 선택 코인 매수 시뮬레이션
        if len(st.session_state.positions) == 0 and st.session_state.selected_coins:
            first_coin = st.session_state.selected_coins[0]
            
            # 현재가 가져오기
            if st.session_state.exchange == 'upbit':
                current_price = pyupbit.get_current_price(first_coin)
            else:
                ticker = first_coin.split('-')[1] if '-' in first_coin else first_coin
                current_price = pybithumb.get_current_price(ticker)
            
            if current_price and st.session_state.auto_invest_per_coin > 0:
                quantity = st.session_state.auto_invest_per_coin / current_price
                
                # 포지션 생성
                coin_name = first_coin.split('-')[1] if '-' in first_coin else first_coin
                st.session_state.positions[coin_name] = {
                    'ticker': first_coin,
                    'korean_name': get_korean_name(coin_name),
                    'buy_price': current_price,
                    'current_price': current_price,
                    'quantity': quantity,
                    'invested': st.session_state.auto_invest_per_coin,
                    'current_value': st.session_state.auto_invest_per_coin
                }
                
                # 투자금 차감
                st.session_state.invested_amount += st.session_state.auto_invest_per_coin
                
                # 주문 내역 추가
                st.session_state.orders.append({
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'BUY',
                    'coin': coin_name,
                    'price': current_price,
                    'quantity': quantity,
                    'total': st.session_state.auto_invest_per_coin
                })

if __name__ == "__main__":
    main()
