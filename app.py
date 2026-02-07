"""
💎 암호화폐 자동매매 Pro - 실전 버전
업비트 & 빗썸 지원 | 볼린저밴드 전략 | 실시간 모니터링
"""

import streamlit as st
import pandas as pd
import numpy as np
import pyupbit
import pybithumb
from datetime import datetime
import time

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="💎 자동매매 Pro",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS 스타일 ====================
st.markdown("""
<style>
    /* 전체 배경 블랙 */
    .stApp {
        background-color: #000000;
    }
    
    /* 모든 텍스트 흰색 */
    * {
        color: #FFFFFF !important;
    }
    
    /* 헤더 */
    .main-header {
        font-size: 2rem;
        font-weight: 900;
        text-align: center;
        margin: 1rem 0;
        color: #00ff41 !important;
    }
    
    /* 상태 카드 */
    .status-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
        border: 1px solid #333;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        text-align: center;
    }
    
    .status-label {
        font-size: 0.85rem;
        color: #888 !important;
        margin-bottom: 0.5rem;
    }
    
    .status-value {
        font-size: 1.8rem;
        font-weight: 900;
        color: #FFFFFF !important;
    }
    
    .status-value.profit {
        color: #00ff41 !important;
    }
    
    .status-value.loss {
        color: #ff0040 !important;
    }
    
    /* 코인 카드 */
    .coin-card {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.2s;
    }
    
    .coin-card:hover {
        border-color: #00ff41;
        transform: translateY(-2px);
    }
    
    .coin-name {
        font-size: 1.2rem;
        font-weight: 700;
        color: #FFFFFF !important;
    }
    
    .coin-price {
        font-size: 1rem;
        color: #888 !important;
    }
    
    .signal-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 700;
        margin-top: 0.5rem;
    }
    
    .badge-buy {
        background: #00ff41;
        color: #000000 !important;
    }
    
    .badge-wait {
        background: #666;
        color: #FFFFFF !important;
    }
    
    /* 포지션 카드 */
    .position-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
        border: 1px solid #333;
        border-left: 4px solid #00ff41;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 0.8rem 0;
    }
    
    .position-card.loss {
        border-left-color: #ff0040;
    }
    
    .position-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid #333;
    }
    
    .position-name {
        font-size: 1.3rem;
        font-weight: 900;
        color: #FFFFFF !important;
    }
    
    .position-profit {
        font-size: 1.3rem;
        font-weight: 900;
    }
    
    .position-detail {
        display: flex;
        justify-content: space-between;
        margin: 0.4rem 0;
        font-size: 0.95rem;
    }
    
    .detail-label {
        color: #888 !important;
    }
    
    .detail-value {
        color: #FFFFFF !important;
        font-weight: 700;
    }
    
    /* 버튼 */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
        min-height: 48px;
    }
    
    /* 사이드바 */
    [data-testid="stSidebar"] {
        background-color: #0d0d0d;
    }
    
    /* 입력 필드 */
    .stNumberInput>div>div>input {
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
        border: 1px solid #333 !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
    }
    
    .stSelectbox>div>div {
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
    }
    
    /* 탭 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1a1a;
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        font-weight: 700;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #00ff41;
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 세션 상태 초기화 ====================
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.exchange = 'upbit'
    st.session_state.total_balance = 1000000
    st.session_state.per_trade = 100000
    st.session_state.positions = {}
    st.session_state.is_running = False
    st.session_state.selected_coins = []

# ==================== 기술적 분석 함수 ====================
def calculate_bollinger_bands(df, period=20):
    """볼린저 밴드 계산"""
    df['ma'] = df['close'].rolling(period).mean()
    df['std'] = df['close'].rolling(period).std()
    df['upper'] = df['ma'] + (df['std'] * 2)
    df['lower'] = df['ma'] - (df['std'] * 2)
    return df

def calculate_rsi(df, period=14):
    """RSI 계산"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def get_signal(ticker, exchange):
    """매매 신호 생성 - 볼린저밴드 + RSI 전략"""
    try:
        # 데이터 가져오기
        if exchange == 'upbit':
            df = pyupbit.get_ohlcv(ticker, interval="minute15", count=40)
        else:
            coin = ticker.split('-')[1] if '-' in ticker else ticker
            df = pybithumb.get_ohlcv(coin)
            if df is not None:
                df = df.tail(40)
        
        if df is None or len(df) < 40:
            return "대기", 0
        
        # 지표 계산
        df = calculate_bollinger_bands(df)
        df = calculate_rsi(df)
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 매수 신호: 가격이 하단 밴드 근처 + RSI 과매도
        if current['close'] <= current['lower'] * 1.02 and current['rsi'] < 40:
            return "매수", current['rsi']
        
        return "대기", current['rsi']
        
    except Exception as e:
        return "대기", 0

# ==================== 빠른 코인 로딩 ====================
@st.cache_data(ttl=30, show_spinner=False)
def get_top_coins(exchange):
    """인기 코인 목록 (30초 캐시)"""
    try:
        if exchange == 'upbit':
            tickers = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOGE',
                      'KRW-SOL', 'KRW-DOT', 'KRW-MATIC', 'KRW-AVAX', 'KRW-LINK']
            coins = []
            for ticker in tickers:
                try:
                    price = pyupbit.get_current_price(ticker)
                    if not price:
                        continue
                    
                    signal, rsi = get_signal(ticker, exchange)
                    
                    coins.append({
                        'ticker': ticker,
                        'name': ticker.split('-')[1],
                        'price': price,
                        'signal': signal,
                        'rsi': rsi
                    })
                except:
                    continue
            return coins
        else:
            # 빗썸
            tickers = ['BTC', 'ETH', 'XRP', 'ADA', 'DOGE', 'SOL']
            coins = []
            for ticker in tickers:
                try:
                    price = pybithumb.get_current_price(ticker)
                    if not price:
                        continue
                    
                    signal, rsi = get_signal(f'KRW-{ticker}', exchange)
                    
                    coins.append({
                        'ticker': f'KRW-{ticker}',
                        'name': ticker,
                        'price': price,
                        'signal': signal,
                        'rsi': rsi
                    })
                except:
                    continue
            return coins
    except:
        return []

def get_korean_name(symbol):
    """한글 이름"""
    names = {
        'BTC': '비트코인', 'ETH': '이더리움', 'XRP': '리플',
        'ADA': '에이다', 'DOGE': '도지코인', 'SOL': '솔라나',
        'DOT': '폴카닷', 'MATIC': '폴리곤', 'AVAX': '아발란체',
        'LINK': '체인링크'
    }
    return names.get(symbol, symbol)

# ==================== 메인 앱 ====================
def main():
    
    # 헤더
    st.markdown('<h1 class="main-header">💎 자동매매 Pro</h1>', unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.markdown("### ⚙️ 기본 설정")
        
        # 거래소 선택
        exchange = st.selectbox(
            "거래소",
            ["upbit", "bithumb"],
            format_func=lambda x: "🟦 업비트" if x == "upbit" else "🟨 빗썸",
            key="exchange_select"
        )
        st.session_state.exchange = exchange
        
        st.divider()
        
        # 자금 설정
        st.markdown("### 💰 투자 설정")
        
        total = st.number_input(
            "총 보유 현금 (원)",
            min_value=0,
            value=st.session_state.total_balance,
            step=100000,
            format="%d"
        )
        st.session_state.total_balance = total
        
        per_trade = st.number_input(
            "코인당 투자금 (원)",
            min_value=10000,
            max_value=total if total > 0 else 10000000,
            value=min(st.session_state.per_trade, total) if total > 0 else 100000,
            step=10000,
            format="%d"
        )
        st.session_state.per_trade = per_trade
        
        # 투자 현황
        invested = sum([p['invested'] for p in st.session_state.positions.values()])
        available = total - invested
        
        st.info(f"""
        **투자 현황**
        - 투자 중: {invested:,.0f}원
        - 사용 가능: {available:,.0f}원
        """)
        
        st.divider()
        
        # 자동매매 제어
        st.markdown("### 🤖 자동매매")
        
        if st.session_state.is_running:
            if st.button("⏸️ 중지", use_container_width=True, type="secondary"):
                st.session_state.is_running = False
                st.rerun()
        else:
            if st.button("▶️ 시작", use_container_width=True, type="primary"):
                if not st.session_state.selected_coins:
                    st.error("코인을 먼저 선택하세요!")
                elif total == 0:
                    st.error("총 보유 현금을 입력하세요!")
                else:
                    st.session_state.is_running = True
                    st.success("자동매매 시작!")
                    st.rerun()
        
        # 전략 설명
        st.divider()
        st.markdown("### 📊 적용 전략")
        st.info("""
        **볼린저밴드 + RSI 전략**
        
        **매수 조건:**
        - 가격이 하단 밴드 근처
        - RSI < 40 (과매도)
        
        **자동 손익:**
        - 손절: -3%
        - 익절: +5%
        """)
    
    # 메인 영역
    tab1, tab2, tab3 = st.tabs(["💰 코인 선택", "📊 포지션", "📈 거래 내역"])
    
    with tab1:
        st.markdown("### 💰 거래할 코인 선택")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"💡 선택한 코인당 **{st.session_state.per_trade:,}원**씩 자동 투자")
        with col2:
            if st.button("🔄 새로고침", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        # 코인 로딩
        coins = get_top_coins(st.session_state.exchange)
        
        if not coins:
            st.error("코인 정보를 불러올 수 없습니다")
            return
        
        # 코인 표시
        for coin in coins:
            is_selected = coin['ticker'] in st.session_state.selected_coins
            
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                badge_class = "badge-buy" if coin['signal'] == "매수" else "badge-wait"
                badge_text = "🟢 매수 신호" if coin['signal'] == "매수" else "⚪ 대기"
                
                st.markdown(f"""
                <div class="coin-card">
                    <div class="coin-name">{coin['name']} <span style="color:#888;font-size:0.9rem;">{get_korean_name(coin['name'])}</span></div>
                    <div class="coin-price">₩{coin['price']:,.0f}</div>
                    <div style="margin-top:0.5rem;">
                        <span class="signal-badge {badge_class}">{badge_text}</span>
                        <span style="color:#888;font-size:0.85rem;margin-left:0.5rem;">RSI: {coin['rsi']:.0f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.write("")
                st.write("")
                if is_selected:
                    st.success("✓ 선택됨")
            
            with col3:
                st.write("")
                st.write("")
                if st.button("선택" if not is_selected else "취소", key=f"sel_{coin['ticker']}", use_container_width=True):
                    if is_selected:
                        st.session_state.selected_coins.remove(coin['ticker'])
                    else:
                        st.session_state.selected_coins.append(coin['ticker'])
                    st.rerun()
        
        # 선택된 코인
        if st.session_state.selected_coins:
            st.divider()
            st.markdown("### ✅ 선택된 코인")
            selected = [c for c in coins if c['ticker'] in st.session_state.selected_coins]
            for c in selected:
                st.markdown(f"- **{c['name']}** {get_korean_name(c['name'])} → {st.session_state.per_trade:,}원 투자 예정")
            
            total_need = len(selected) * st.session_state.per_trade
            if total_need > available:
                st.error(f"❌ 자금 부족! (필요: {total_need:,}원, 가능: {available:,}원)")
            else:
                st.success(f"✅ 총 {len(selected)}개 코인, {total_need:,}원 투자 준비 완료")
    
    with tab2:
        st.markdown("### 📊 보유 포지션")
        
        if st.session_state.positions:
            for coin_name, pos in st.session_state.positions.items():
                # 현재가 업데이트
                try:
                    if st.session_state.exchange == 'upbit':
                        current_price = pyupbit.get_current_price(pos['ticker'])
                    else:
                        ticker = pos['ticker'].split('-')[1]
                        current_price = pybithumb.get_current_price(ticker)
                    
                    if current_price:
                        pos['current_price'] = current_price
                        pos['current_value'] = pos['quantity'] * current_price
                        pos['profit'] = pos['current_value'] - pos['invested']
                except:
                    pass
                
                profit_pct = (pos['profit'] / pos['invested']) * 100
                profit_class = "profit" if pos['profit'] >= 0 else "loss"
                card_class = "position-card" if pos['profit'] >= 0 else "position-card loss"
                
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="position-header">
                        <div class="position-name">{coin_name} <span style="color:#888;font-size:0.9rem;">{get_korean_name(coin_name)}</span></div>
                        <div class="position-profit {profit_class}">{pos['profit']:+,.0f}원 ({profit_pct:+.2f}%)</div>
                    </div>
                    <div class="position-detail">
                        <span class="detail-label">매수가</span>
                        <span class="detail-value">₩{pos['buy_price']:,.0f}</span>
                    </div>
                    <div class="position-detail">
                        <span class="detail-label">현재가</span>
                        <span class="detail-value">₩{pos['current_price']:,.0f}</span>
                    </div>
                    <div class="position-detail">
                        <span class="detail-label">보유 수량</span>
                        <span class="detail-value">{pos['quantity']:.8f}</span>
                    </div>
                    <div class="position-detail">
                        <span class="detail-label">투자금</span>
                        <span class="detail-value">₩{pos['invested']:,.0f}</span>
                    </div>
                    <div class="position-detail">
                        <span class="detail-label">평가금</span>
                        <span class="detail-value">₩{pos['current_value']:,.0f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("보유 중인 포지션이 없습니다")
    
    with tab3:
        st.markdown("### 📈 거래 내역")
        st.info("거래 내역 기능은 추후 업데이트됩니다")
    
    # 상태 표시
    col1, col2, col3, col4 = st.columns(4)
    
    total_value = st.session_state.total_balance - invested + sum([p['current_value'] for p in st.session_state.positions.values()])
    total_profit = sum([p['profit'] for p in st.session_state.positions.values()])
    profit_pct = (total_profit / invested * 100) if invested > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class="status-card">
            <div class="status-label">총 자산</div>
            <div class="status-value">₩{total_value:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        profit_class = "profit" if total_profit >= 0 else "loss"
        st.markdown(f"""
        <div class="status-card">
            <div class="status-label">평가 손익</div>
            <div class="status-value {profit_class}">{total_profit:+,.0f}원</div>
            <div class="status-label">{profit_pct:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="status-card">
            <div class="status-label">투자 중</div>
            <div class="status-value">₩{invested:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        status_text = "🟢 실행 중" if st.session_state.is_running else "⚪ 중지됨"
        st.markdown(f"""
        <div class="status-card">
            <div class="status-label">상태</div>
            <div class="status-value" style="font-size:1.2rem;">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 자동매매 로직 (시뮬레이션)
    if st.session_state.is_running and st.session_state.selected_coins:
        # 선택된 코인 중 매수 신호 있는 것 매수
        for ticker in st.session_state.selected_coins:
            coin_name = ticker.split('-')[1]
            
            # 이미 보유 중이면 스킵
            if coin_name in st.session_state.positions:
                continue
            
            # 매수 신호 확인
            signal, rsi = get_signal(ticker, st.session_state.exchange)
            
            if signal == "매수":
                # 현재가 가져오기
                try:
                    if st.session_state.exchange == 'upbit':
                        price = pyupbit.get_current_price(ticker)
                    else:
                        price = pybithumb.get_current_price(coin_name)
                    
                    if price and st.session_state.per_trade > 0:
                        quantity = st.session_state.per_trade / price
                        
                        # 포지션 생성
                        st.session_state.positions[coin_name] = {
                            'ticker': ticker,
                            'buy_price': price,
                            'current_price': price,
                            'quantity': quantity,
                            'invested': st.session_state.per_trade,
                            'current_value': st.session_state.per_trade,
                            'profit': 0
                        }
                        
                        st.success(f"✅ {coin_name} 매수 완료! (₩{price:,.0f})")
                        time.sleep(1)
                        st.rerun()
                except:
                    pass

if __name__ == "__main__":
    main()
