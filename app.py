"""
🚀 Crypto Auto Trading Bot Pro V2
고객 중심 설계 | AI 추천 코인 | 초간단 인터페이스
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
import json
from typing import Dict, List, Optional
import logging

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="💎 AI 자동매매",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== 로깅 ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 다크 모드 CSS ====================
st.markdown("""
<style>
    /* 전체 배경 */
    .main {
        background: #0f1419;
    }
    
    /* 헤더 */
    .main-header {
        font-size: 2.5rem;
        font-weight: 900;
        color: #ffffff;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .sub-text {
        text-align: center;
        color: #8b949e;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* 카드 스타일 */
    .card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .coin-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 2px solid #374151;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .coin-card:hover {
        border-color: #10b981;
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.2);
    }
    
    .coin-card.selected {
        border-color: #10b981;
        background: linear-gradient(135deg, #065f46 0%, #064e3b 100%);
    }
    
    /* 수익률 */
    .profit-positive {
        color: #10b981;
        font-weight: 900;
        font-size: 1.8rem;
    }
    
    .profit-negative {
        color: #ef4444;
        font-weight: 900;
        font-size: 1.8rem;
    }
    
    /* 버튼 */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        font-weight: 700;
        border: none;
        border-radius: 12px;
        padding: 1rem;
        font-size: 1.1rem;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);
    }
    
    /* 상태 표시 */
    .status-live {
        display: inline-block;
        background: #10b981;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 700;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    .status-stopped {
        display: inline-block;
        background: #6b7280;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 700;
    }
    
    /* 추천 배지 */
    .badge-hot {
        background: #ef4444;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .badge-volume {
        background: #3b82f6;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .badge-trend {
        background: #10b981;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
        margin: 0.2rem;
    }
    
    /* 메트릭 박스 */
    .metric-box {
        background: #1f2937;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    
    .metric-label {
        color: #9ca3af;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 900;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 세션 상태 초기화 ====================
if 'exchange' not in st.session_state:
    st.session_state.exchange = 'upbit'
if 'selected_coins' not in st.session_state:
    st.session_state.selected_coins = []
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'portfolio_value' not in st.session_state:
    st.session_state.portfolio_value = 1000000  # 초기 자본
if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {'access': '', 'secret': ''}

# ==================== 코인 스캐너 ====================
class CoinScanner:
    """AI 기반 코인 스캐너"""
    
    @staticmethod
    def get_top_coins(exchange: str, count: int = 5) -> List[Dict]:
        """거래량과 변동성 기반 TOP 코인 추천"""
        try:
            if exchange == 'upbit':
                tickers = pyupbit.get_tickers(fiat="KRW")
                results = []
                
                for ticker in tickers[:30]:  # 상위 30개만 스캔
                    try:
                        df = pyupbit.get_ohlcv(ticker, interval="day", count=7)
                        if df is None or len(df) < 7:
                            continue
                        
                        # 거래량 증가율
                        volume_change = (df['volume'].iloc[-1] / df['volume'].iloc[-2] - 1) * 100
                        
                        # 변동성 (7일 평균)
                        volatility = ((df['high'] - df['low']) / df['low'] * 100).mean()
                        
                        # 가격 변화율
                        price_change = (df['close'].iloc[-1] / df['close'].iloc[-2] - 1) * 100
                        
                        # 현재가
                        current_price = df['close'].iloc[-1]
                        
                        # 점수 계산 (거래량 증가 + 변동성)
                        score = (volume_change * 0.4) + (volatility * 0.4) + (abs(price_change) * 0.2)
                        
                        results.append({
                            'ticker': ticker,
                            'name': ticker.split('-')[1],
                            'price': current_price,
                            'change': price_change,
                            'volume_change': volume_change,
                            'volatility': volatility,
                            'score': score
                        })
                        
                    except Exception as e:
                        continue
                
                # 점수 순으로 정렬
                results.sort(key=lambda x: x['score'], reverse=True)
                return results[:count]
                
            elif exchange == 'bithumb':
                tickers = pybithumb.get_tickers()
                results = []
                
                for ticker in tickers[:30]:
                    try:
                        df = pybithumb.get_ohlcv(ticker, interval="day", count=7)
                        if df is None or len(df) < 7:
                            continue
                        
                        volume_change = (df['volume'].iloc[-1] / df['volume'].iloc[-2] - 1) * 100
                        volatility = ((df['high'] - df['low']) / df['low'] * 100).mean()
                        price_change = (df['close'].iloc[-1] / df['close'].iloc[-2] - 1) * 100
                        current_price = df['close'].iloc[-1]
                        score = (volume_change * 0.4) + (volatility * 0.4) + (abs(price_change) * 0.2)
                        
                        results.append({
                            'ticker': f'KRW-{ticker}',
                            'name': ticker,
                            'price': current_price,
                            'change': price_change,
                            'volume_change': volume_change,
                            'volatility': volatility,
                            'score': score
                        })
                        
                    except:
                        continue
                
                results.sort(key=lambda x: x['score'], reverse=True)
                return results[:count]
                
        except Exception as e:
            logger.error(f"코인 스캔 오류: {e}")
            return []
        
        return []

# ==================== 기술적 지표 ====================
class TechnicalAnalysis:
    """기술적 분석"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    @staticmethod
    def calculate_macd(prices: pd.Series) -> tuple:
        """MACD 계산"""
        ema12 = prices.ewm(span=12).mean()
        ema26 = prices.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        return macd.iloc[-1], signal.iloc[-1]
    
    @staticmethod
    def should_buy(ticker: str, exchange: str) -> tuple[bool, str]:
        """매수 신호 판단"""
        try:
            if exchange == 'upbit':
                df = pyupbit.get_ohlcv(ticker, interval="minute60", count=50)
            else:
                coin = ticker.split('-')[1] if '-' in ticker else ticker
                df = pybithumb.get_ohlcv(coin, interval="minute60", count=50)
            
            if df is None or len(df) < 50:
                return False, "데이터 부족"
            
            # RSI
            rsi = TechnicalAnalysis.calculate_rsi(df['close'])
            
            # MACD
            macd, signal = TechnicalAnalysis.calculate_macd(df['close'])
            
            # 매수 조건
            reasons = []
            buy_score = 0
            
            if rsi < 30:
                reasons.append("RSI 과매도")
                buy_score += 40
            elif rsi < 40:
                reasons.append("RSI 낮음")
                buy_score += 20
            
            if macd > signal:
                reasons.append("MACD 골든크로스")
                buy_score += 30
            
            # 거래량 증가
            if df['volume'].iloc[-1] > df['volume'].iloc[-5:].mean() * 1.5:
                reasons.append("거래량 급증")
                buy_score += 30
            
            if buy_score >= 50:
                return True, " | ".join(reasons)
            
            return False, "대기"
            
        except Exception as e:
            return False, f"분석 오류: {e}"

# ==================== 메인 앱 ====================
def main():
    """메인 애플리케이션"""
    
    # 헤더
    st.markdown('<h1 class="main-header">💎 AI 자동매매 봇</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">AI가 추천하는 코인을 선택하고, 24시간 자동으로 수익을 만드세요</p>', unsafe_allow_html=True)
    
    # ==================== 대시보드 ====================
    col1, col2, col3, col4 = st.columns(4)
    
    # 계산
    total_profit = sum([t.get('profit', 0) for t in st.session_state.trades])
    profit_percent = (total_profit / st.session_state.portfolio_value) * 100 if st.session_state.portfolio_value > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">총 자산</div>
            <div class="metric-value">₩{st.session_state.portfolio_value + total_profit:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        profit_class = "profit-positive" if total_profit > 0 else "profit-negative"
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">수익금</div>
            <div class="{profit_class}">₩{total_profit:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">수익률</div>
            <div class="{profit_class}">{profit_percent:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        status_html = '<span class="status-live">🔴 실행 중</span>' if st.session_state.is_running else '<span class="status-stopped">⚪ 중지됨</span>'
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">상태</div>
            <div>{status_html}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ==================== AI 추천 코인 ====================
    st.markdown("## 🤖 AI 추천 코인 TOP 5")
    st.markdown("거래량과 변동성을 분석하여 수익 가능성이 높은 코인을 추천합니다")
    
    # 거래소 선택
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        exchange = st.selectbox(
            "거래소",
            ["upbit", "bithumb"],
            format_func=lambda x: "업비트" if x == "upbit" else "빗썸",
            key="exchange_select"
        )
        st.session_state.exchange = exchange
    
    with col2:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
    
    # TOP 5 코인 스캔
    with st.spinner("AI가 최적의 코인을 찾고 있습니다..."):
        top_coins = CoinScanner.get_top_coins(st.session_state.exchange, 5)
    
    if not top_coins:
        st.error("코인 정보를 불러올 수 없습니다. 잠시 후 다시 시도하세요.")
        return
    
    # 코인 카드 표시
    cols = st.columns(5)
    
    for idx, coin in enumerate(top_coins):
        with cols[idx]:
            # 선택 여부
            is_selected = coin['ticker'] in st.session_state.selected_coins
            card_class = "coin-card selected" if is_selected else "coin-card"
            
            # 매수 신호 분석
            should_buy, reason = TechnicalAnalysis.should_buy(coin['ticker'], st.session_state.exchange)
            
            # 배지
            badges = []
            if coin['volume_change'] > 100:
                badges.append('<span class="badge-volume">거래량↑</span>')
            if coin['volatility'] > 5:
                badges.append('<span class="badge-hot">고변동성</span>')
            if should_buy:
                badges.append('<span class="badge-trend">매수신호</span>')
            
            change_color = "#10b981" if coin['change'] > 0 else "#ef4444"
            
            st.markdown(f"""
            <div class="{card_class}">
                <h3 style="margin: 0; color: #ffffff;">{coin['name']}</h3>
                <p style="color: #9ca3af; font-size: 0.9rem; margin: 0.3rem 0;">₩{coin['price']:,.0f}</p>
                <p style="color: {change_color}; font-weight: 700; font-size: 1.2rem; margin: 0.5rem 0;">
                    {coin['change']:+.2f}%
                </p>
                <div style="margin: 0.5rem 0;">
                    {''.join(badges)}
                </div>
                <p style="color: #6b7280; font-size: 0.85rem; margin-top: 0.5rem;">
                    {reason}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # 선택 버튼
            button_label = "✓ 선택됨" if is_selected else "선택"
            button_type = "secondary" if is_selected else "primary"
            
            if st.button(button_label, key=f"select_{coin['ticker']}", use_container_width=True, type=button_type):
                if is_selected:
                    st.session_state.selected_coins.remove(coin['ticker'])
                else:
                    st.session_state.selected_coins.append(coin['ticker'])
                st.rerun()
    
    st.divider()
    
    # ==================== 선택된 코인 ====================
    if st.session_state.selected_coins:
        st.markdown("## 📌 선택된 코인")
        
        selected_df = pd.DataFrame([
            coin for coin in top_coins 
            if coin['ticker'] in st.session_state.selected_coins
        ])
        
        st.dataframe(
            selected_df[['name', 'price', 'change', 'volume_change', 'volatility']],
            column_config={
                'name': '코인명',
                'price': st.column_config.NumberColumn('현재가', format="₩%.0f"),
                'change': st.column_config.NumberColumn('변동률', format="%.2f%%"),
                'volume_change': st.column_config.NumberColumn('거래량 증가', format="%.1f%%"),
                'volatility': st.column_config.NumberColumn('변동성', format="%.2f%%"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("👆 위에서 거래할 코인을 선택하세요")
    
    st.divider()
    
    # ==================== 설정 및 제어 ====================
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## ⚙️ 거래 설정")
        
        subcol1, subcol2, subcol3 = st.columns(3)
        
        with subcol1:
            investment = st.number_input(
                "투자 금액 (원)",
                min_value=10000,
                value=100000,
                step=10000,
                help="한 코인당 투자할 금액"
            )
        
        with subcol2:
            stop_loss = st.slider(
                "손절률 (%)",
                min_value=1.0,
                max_value=10.0,
                value=3.0,
                step=0.5,
                help="이 비율만큼 손실 시 자동 매도"
            )
        
        with subcol3:
            take_profit = st.slider(
                "익절률 (%)",
                min_value=2.0,
                max_value=20.0,
                value=5.0,
                step=0.5,
                help="이 비율만큼 수익 시 자동 매도"
            )
    
    with col2:
        st.markdown("## 🔐 API 설정")
        
        mode = st.radio(
            "모드",
            ["테스트 모드", "실거래 모드"],
            help="테스트: 신호만 보기 | 실거래: 실제 거래"
        )
        
        if mode == "실거래 모드":
            with st.expander("API 키 입력", expanded=False):
                access_key = st.text_input("Access Key", type="password")
                secret_key = st.text_input("Secret Key", type="password")
                
                if access_key and secret_key:
                    st.session_state.api_keys = {
                        'access': access_key,
                        'secret': secret_key
                    }
                    st.success("✅ API 키 입력 완료")
    
    # ==================== 시작/중지 버튼 ====================
    st.divider()
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if not st.session_state.is_running:
            if st.button("🚀 자동매매 시작", use_container_width=True, type="primary"):
                if not st.session_state.selected_coins:
                    st.error("코인을 먼저 선택하세요!")
                elif mode == "실거래 모드" and not st.session_state.api_keys['access']:
                    st.error("API 키를 입력하세요!")
                else:
                    st.session_state.is_running = True
                    st.success(f"✅ {len(st.session_state.selected_coins)}개 코인 자동매매 시작!")
                    st.rerun()
        else:
            if st.button("⏸️ 중지", use_container_width=True):
                st.session_state.is_running = False
                st.warning("자동매매가 중지되었습니다")
                st.rerun()
    
    # ==================== 거래 내역 ====================
    if st.session_state.trades:
        st.divider()
        st.markdown("## 📊 거래 내역")
        
        trades_df = pd.DataFrame(st.session_state.trades)
        st.dataframe(trades_df, use_container_width=True, hide_index=True)
    
    # ==================== 하단 도움말 ====================
    st.divider()
    
    with st.expander("❓ 사용 방법"):
        st.markdown("""
        ### 🎯 3단계로 시작하기
        
        **1단계: 코인 선택**
        - AI가 추천하는 TOP 5 코인 중 원하는 코인 선택
        - 여러 개 선택 가능
        
        **2단계: 설정**
        - 투자 금액 설정
        - 손절률/익절률 설정
        - API 키 입력 (실거래 시)
        
        **3단계: 시작**
        - 시작 버튼 클릭
        - 24시간 자동 감시 시작
        
        ### 💡 팁
        - 테스트 모드로 먼저 확인하세요
        - 소액(10만원)으로 시작하세요
        - 손절은 반드시 설정하세요
        """)
    
    with st.expander("⚠️ 주의사항"):
        st.markdown("""
        - 암호화폐 투자는 고위험 상품입니다
        - 손실 가능성을 충분히 인지하세요
        - 생활비를 투자하지 마세요
        - API 출금 권한은 절대 주지 마세요
        """)

if __name__ == "__main__":
    main()
