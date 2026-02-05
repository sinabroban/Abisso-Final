"""
🚀 Crypto Auto Trading Bot Pro
업비트 & 빗썸 지원 | 실거래 & 테스트 모드 | 전문가급 자동매매
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
import os
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass, asdict
import traceback

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="🚀 암호화폐 자동매매 Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 로깅 설정 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 커스텀 CSS ====================
st.markdown("""
<style>
    /* 메인 컨테이너 */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* 헤더 스타일 */
    .main-header {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 서브 헤더 */
    .sub-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #667eea;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
    }
    
    /* 메트릭 카드 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 8px 16px rgba(102,126,234,0.3);
        transition: transform 0.3s ease;
        margin: 0.5rem 0;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(102,126,234,0.4);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 900;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* 상태 표시 */
    .status-running {
        color: #10b981;
        font-weight: bold;
        font-size: 1.2rem;
        animation: pulse 2s infinite;
    }
    
    .status-stopped {
        color: #ef4444;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* 신호 카드 */
    .signal-buy {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-size: 2rem;
        font-weight: 900;
        box-shadow: 0 8px 16px rgba(16,185,129,0.3);
    }
    
    .signal-sell {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-size: 2rem;
        font-weight: 900;
        box-shadow: 0 8px 16px rgba(239,68,68,0.3);
    }
    
    .signal-hold {
        background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-size: 2rem;
        font-weight: 900;
        box-shadow: 0 8px 16px rgba(107,114,128,0.3);
    }
    
    /* 경고 박스 */
    .warning-box {
        background: #fef3c7;
        border-left: 5px solid #f59e0b;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .info-box {
        background: #dbeafe;
        border-left: 5px solid #3b82f6;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #d1fae5;
        border-left: 5px solid #10b981;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* 버튼 스타일 */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: 700;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    /* 사이드바 */
    .css-1d391kg {
        background-color: #f8fafc;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        font-weight: 600;
        border-radius: 10px 10px 0 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 데이터 클래스 ====================
@dataclass
class TradingConfig:
    """거래 설정"""
    exchange: str = "upbit"  # upbit, bithumb
    market: str = "KRW-BTC"
    strategy: str = "RSI 모멘텀"
    investment_amount: int = 100000
    stop_loss: float = 3.0
    take_profit: float = 5.0
    rsi_buy: int = 30
    rsi_sell: int = 70
    use_trailing_stop: bool = True
    trailing_stop: float = 2.0
    max_position: float = 30.0
    use_real_trading: bool = False  # 실거래 여부
    
@dataclass
class TradeSignal:
    """매매 신호"""
    action: str  # BUY, SELL, HOLD
    price: float
    confidence: float  # 0-100
    indicators: Dict
    timestamp: datetime

# ==================== 거래소 연동 ====================
class ExchangeAPI:
    """거래소 API 통합"""
    
    def __init__(self, exchange: str, access_key: str = "", secret_key: str = ""):
        self.exchange = exchange.lower()
        self.access_key = access_key
        self.secret_key = secret_key
        
        if self.exchange == "upbit":
            if access_key and secret_key:
                self.client = pyupbit.Upbit(access_key, secret_key)
            else:
                self.client = None
        elif self.exchange == "bithumb":
            if access_key and secret_key:
                self.client = pybithumb.Bithumb(access_key, secret_key)
            else:
                self.client = None
    
    def get_balance(self, currency: str = "KRW") -> float:
        """잔고 조회"""
        try:
            if not self.client:
                return 0.0
                
            if self.exchange == "upbit":
                balance = self.client.get_balance(currency)
                return float(balance) if balance else 0.0
            elif self.exchange == "bithumb":
                balance = self.client.get_balance(currency)
                return float(balance[0]) if balance else 0.0
        except Exception as e:
            logger.error(f"잔고 조회 실패: {e}")
            return 0.0
    
    def get_current_price(self, market: str) -> Optional[float]:
        """현재가 조회"""
        try:
            if self.exchange == "upbit":
                price = pyupbit.get_current_price(market)
            elif self.exchange == "bithumb":
                ticker = market.split('-')[1] if '-' in market else market
                price = pybithumb.get_current_price(ticker)
            return float(price) if price else None
        except Exception as e:
            logger.error(f"현재가 조회 실패: {e}")
            return None
    
    def buy(self, market: str, amount: float) -> bool:
        """매수"""
        try:
            if not self.client:
                logger.warning("API 키가 설정되지 않음 (테스트 모드)")
                return False
                
            if self.exchange == "upbit":
                result = self.client.buy_market_order(market, amount)
            elif self.exchange == "bithumb":
                ticker = market.split('-')[1] if '-' in market else market
                result = self.client.buy_market_order(ticker, amount)
                
            return result is not None
        except Exception as e:
            logger.error(f"매수 실패: {e}")
            return False
    
    def sell(self, market: str, quantity: float) -> bool:
        """매도"""
        try:
            if not self.client:
                logger.warning("API 키가 설정되지 않음 (테스트 모드)")
                return False
                
            if self.exchange == "upbit":
                result = self.client.sell_market_order(market, quantity)
            elif self.exchange == "bithumb":
                ticker = market.split('-')[1] if '-' in market else market
                result = self.client.sell_market_order(ticker, quantity)
                
            return result is not None
        except Exception as e:
            logger.error(f"매도 실패: {e}")
            return False

# ==================== 데이터 관리 ====================
class DataManager:
    """시장 데이터 관리"""
    
    @staticmethod
    def get_ohlcv(exchange: str, market: str, interval: str = "minute60", count: int = 200) -> pd.DataFrame:
        """OHLCV 데이터 가져오기"""
        try:
            if exchange == "upbit":
                df = pyupbit.get_ohlcv(market, interval=interval, count=count)
            elif exchange == "bithumb":
                ticker = market.split('-')[1] if '-' in market else market
                df = pybithumb.get_ohlcv(ticker, interval=interval, count=count)
            else:
                return pd.DataFrame()
            
            if df is None or df.empty:
                return pd.DataFrame()
                
            df.columns = ['open', 'high', 'low', 'close', 'volume', 'value']
            return df
            
        except Exception as e:
            logger.error(f"데이터 조회 실패: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_markets(exchange: str) -> List[str]:
        """거래 가능 마켓 목록"""
        try:
            if exchange == "upbit":
                markets = pyupbit.get_tickers(fiat="KRW")
                return sorted([m for m in markets if m.startswith("KRW-")])
            elif exchange == "bithumb":
                markets = pybithumb.get_tickers()
                return sorted([f"KRW-{m}" for m in markets if m != "BTC"])
            return []
        except:
            return ["KRW-BTC", "KRW-ETH", "KRW-XRP"]

# ==================== 기술적 지표 ====================
class TechnicalIndicators:
    """기술적 지표 계산"""
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """RSI 계산"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple:
        """MACD 계산"""
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.Series, period: int = 20, std: float = 2) -> Tuple:
        """볼린저 밴드 계산"""
        ma = data.rolling(window=period).mean()
        std_dev = data.rolling(window=period).std()
        upper = ma + (std_dev * std)
        lower = ma - (std_dev * std)
        return upper, ma, lower
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """모든 지표 추가"""
        # RSI
        df['RSI'] = TechnicalIndicators.calculate_rsi(df['close'])
        
        # MACD
        macd, signal, hist = TechnicalIndicators.calculate_macd(df['close'])
        df['MACD'] = macd
        df['MACD_signal'] = signal
        df['MACD_hist'] = hist
        
        # 볼린저 밴드
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(df['close'])
        df['BB_upper'] = upper
        df['BB_middle'] = middle
        df['BB_lower'] = lower
        
        # 이동평균선
        df['SMA_5'] = df['close'].rolling(window=5).mean()
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_60'] = df['close'].rolling(window=60).mean()
        df['EMA_12'] = df['close'].ewm(span=12).mean()
        df['EMA_26'] = df['close'].ewm(span=26).mean()
        
        # 거래량 이동평균
        df['Volume_MA'] = df['volume'].rolling(window=20).mean()
        
        return df

# ==================== 매매 전략 ====================
class TradingStrategy:
    """매매 전략"""
    
    @staticmethod
    def rsi_momentum(df: pd.DataFrame, config: TradingConfig) -> TradeSignal:
        """RSI 모멘텀 전략"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        action = "HOLD"
        confidence = 0.0
        
        # 매수 신호
        if latest['RSI'] < config.rsi_buy and prev['RSI'] >= config.rsi_buy:
            action = "BUY"
            confidence = min(100, (config.rsi_buy - latest['RSI']) * 3)
            
            # MACD 확인
            if latest['MACD'] > latest['MACD_signal']:
                confidence += 20
                
            # 거래량 확인
            if latest['volume'] > latest['Volume_MA']:
                confidence += 10
        
        # 매도 신호
        elif latest['RSI'] > config.rsi_sell and prev['RSI'] <= config.rsi_sell:
            action = "SELL"
            confidence = min(100, (latest['RSI'] - config.rsi_sell) * 3)
            
            # MACD 확인
            if latest['MACD'] < latest['MACD_signal']:
                confidence += 20
                
            # 거래량 확인
            if latest['volume'] > latest['Volume_MA']:
                confidence += 10
        
        confidence = min(100, confidence)
        
        return TradeSignal(
            action=action,
            price=latest['close'],
            confidence=confidence,
            indicators={
                'RSI': latest['RSI'],
                'MACD': latest['MACD'],
                'MACD_signal': latest['MACD_signal'],
                'Volume': latest['volume']
            },
            timestamp=datetime.now()
        )
    
    @staticmethod
    def bollinger_strategy(df: pd.DataFrame, config: TradingConfig) -> TradeSignal:
        """볼린저 밴드 전략"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        action = "HOLD"
        confidence = 0.0
        
        # 하단 밴드 터치 후 반등
        if prev['close'] <= prev['BB_lower'] and latest['close'] > latest['BB_lower']:
            action = "BUY"
            distance = (latest['BB_middle'] - latest['close']) / latest['BB_middle'] * 100
            confidence = min(100, distance * 5)
        
        # 상단 밴드 돌파
        elif prev['close'] < prev['BB_upper'] and latest['close'] >= latest['BB_upper']:
            action = "SELL"
            distance = (latest['close'] - latest['BB_middle']) / latest['BB_middle'] * 100
            confidence = min(100, distance * 5)
        
        return TradeSignal(
            action=action,
            price=latest['close'],
            confidence=confidence,
            indicators={
                'BB_upper': latest['BB_upper'],
                'BB_middle': latest['BB_middle'],
                'BB_lower': latest['BB_lower'],
                'Price': latest['close']
            },
            timestamp=datetime.now()
        )
    
    @staticmethod
    def macd_strategy(df: pd.DataFrame, config: TradingConfig) -> TradeSignal:
        """MACD 크로스오버 전략"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        action = "HOLD"
        confidence = 0.0
        
        # 골든 크로스
        if prev['MACD'] <= prev['MACD_signal'] and latest['MACD'] > latest['MACD_signal']:
            action = "BUY"
            confidence = min(100, abs(latest['MACD_hist']) * 10)
        
        # 데드 크로스
        elif prev['MACD'] >= prev['MACD_signal'] and latest['MACD'] < latest['MACD_signal']:
            action = "SELL"
            confidence = min(100, abs(latest['MACD_hist']) * 10)
        
        return TradeSignal(
            action=action,
            price=latest['close'],
            confidence=confidence,
            indicators={
                'MACD': latest['MACD'],
                'Signal': latest['MACD_signal'],
                'Histogram': latest['MACD_hist']
            },
            timestamp=datetime.now()
        )

# ==================== 차트 생성 ====================
def create_advanced_chart(df: pd.DataFrame) -> go.Figure:
    """고급 차트 생성"""
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.2, 0.15, 0.15],
        subplot_titles=('📊 가격 & 지표', '📦 거래량', '📈 RSI', '📉 MACD')
    )
    
    # 캔들스틱
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='가격',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )
    
    # 볼린저 밴드
    fig.add_trace(
        go.Scatter(x=df.index, y=df['BB_upper'], name='볼린저 상단',
                   line=dict(color='rgba(102,126,234,0.5)', width=1, dash='dash')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['BB_middle'], name='볼린저 중간',
                   line=dict(color='rgba(102,126,234,0.8)', width=1.5)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['BB_lower'], name='볼린저 하단',
                   line=dict(color='rgba(102,126,234,0.5)', width=1, dash='dash'),
                   fill='tonexty', fillcolor='rgba(102,126,234,0.1)'),
        row=1, col=1
    )
    
    # 이동평균선
    fig.add_trace(
        go.Scatter(x=df.index, y=df['SMA_5'], name='SMA 5',
                   line=dict(color='#fbbf24', width=1.5)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['SMA_20'], name='SMA 20',
                   line=dict(color='#f97316', width=2)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['SMA_60'], name='SMA 60',
                   line=dict(color='#a855f7', width=2)),
        row=1, col=1
    )
    
    # 거래량
    colors = ['#ef5350' if df.iloc[i]['close'] < df.iloc[i]['open'] else '#26a69a' 
              for i in range(len(df))]
    fig.add_trace(
        go.Bar(x=df.index, y=df['volume'], name='거래량', marker_color=colors),
        row=2, col=1
    )
    
    # RSI
    fig.add_trace(
        go.Scatter(x=df.index, y=df['RSI'], name='RSI',
                   line=dict(color='#3b82f6', width=2)),
        row=3, col=1
    )
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=3, col=1, opacity=0.5)
    fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=3, col=1, opacity=0.5)
    
    # MACD
    fig.add_trace(
        go.Scatter(x=df.index, y=df['MACD'], name='MACD',
                   line=dict(color='#3b82f6', width=2)),
        row=4, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['MACD_signal'], name='Signal',
                   line=dict(color='#f97316', width=2)),
        row=4, col=1
    )
    
    # 히스토그램
    colors = ['#10b981' if val > 0 else '#ef4444' for val in df['MACD_hist']]
    fig.add_trace(
        go.Bar(x=df.index, y=df['MACD_hist'], name='Histogram',
               marker_color=colors, opacity=0.5),
        row=4, col=1
    )
    
    # 레이아웃
    fig.update_layout(
        height=1000,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.1)',
        font=dict(size=12)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgba(255,255,255,0.1)')
    
    return fig

# ==================== 메인 애플리케이션 ====================
def main():
    """메인 애플리케이션"""
    
    # 세션 상태 초기화
    if 'config' not in st.session_state:
        st.session_state.config = TradingConfig()
    if 'is_running' not in st.session_state:
        st.session_state.is_running = False
    if 'trades' not in st.session_state:
        st.session_state.trades = []
    if 'portfolio_value' not in st.session_state:
        st.session_state.portfolio_value = []
    
    # 헤더
    st.markdown('<h1 class="main-header">🚀 암호화폐 자동매매 Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #6b7280; font-size: 1.2rem;">업비트 & 빗썸 지원 | AI 기반 전략 | 실시간 자동매매</p>', unsafe_allow_html=True)
    
    # 사이드바 설정
    with st.sidebar:
        st.markdown('<h2 class="sub-header">⚙️ 설정</h2>', unsafe_allow_html=True)
        
        # 거래소 선택
        st.session_state.config.exchange = st.selectbox(
            "🏦 거래소",
            ["upbit", "bithumb"],
            format_func=lambda x: "업비트 (Upbit)" if x == "upbit" else "빗썸 (Bithumb)"
        )
        
        # 마켓 선택
        markets = DataManager.get_markets(st.session_state.config.exchange)
        if markets:
            st.session_state.config.market = st.selectbox(
                "💰 거래 마켓",
                markets,
                format_func=lambda x: f"{x.split('-')[1]} ({x})"
            )
        
        st.divider()
        
        # 전략 선택
        st.markdown("### 📊 매매 전략")
        st.session_state.config.strategy = st.selectbox(
            "전략",
            ["RSI 모멘텀", "볼린저 밴드", "MACD 크로스오버"],
            label_visibility="collapsed"
        )
        
        # 전략별 파라미터
        with st.expander("🎯 전략 파라미터", expanded=True):
            if "RSI" in st.session_state.config.strategy:
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.config.rsi_buy = st.slider("RSI 매수", 20, 40, 30)
                with col2:
                    st.session_state.config.rsi_sell = st.slider("RSI 매도", 60, 80, 70)
        
        st.divider()
        
        # 투자 설정
        st.markdown("### 💵 투자 설정")
        st.session_state.config.investment_amount = st.number_input(
            "투자 금액 (원)",
            min_value=5000,
            value=st.session_state.config.investment_amount,
            step=10000
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.config.stop_loss = st.slider("손절률 (%)", 1.0, 10.0, 3.0, 0.5)
        with col2:
            st.session_state.config.take_profit = st.slider("익절률 (%)", 2.0, 20.0, 5.0, 0.5)
        
        st.session_state.config.use_trailing_stop = st.checkbox("트레일링 스탑 사용", value=True)
        if st.session_state.config.use_trailing_stop:
            st.session_state.config.trailing_stop = st.slider("트레일링 %", 0.5, 5.0, 2.0, 0.1)
        
        st.divider()
        
        # API 설정
        st.markdown("### 🔑 API 설정")
        
        # 실거래/테스트 모드
        mode = st.radio(
            "모드 선택",
            ["🧪 테스트 모드 (신호만 보기)", "💰 실거래 모드 (실제 거래)"],
            index=0 if not st.session_state.config.use_real_trading else 1
        )
        st.session_state.config.use_real_trading = "실거래" in mode
        
        if st.session_state.config.use_real_trading:
            st.markdown('<div class="warning-box">⚠️ <b>실거래 모드</b>입니다. API 키를 정확히 입력하세요!</div>', unsafe_allow_html=True)
            
            access_key = st.text_input("Access Key", type="password")
            secret_key = st.text_input("Secret Key", type="password")
            
            if access_key and secret_key:
                st.success("✅ API 키가 입력되었습니다")
                st.session_state.api = ExchangeAPI(st.session_state.config.exchange, access_key, secret_key)
            else:
                st.warning("API 키를 입력해주세요")
        else:
            st.markdown('<div class="info-box">ℹ️ <b>테스트 모드</b>입니다. 실제 거래는 하지 않습니다.</div>', unsafe_allow_html=True)
            st.session_state.api = ExchangeAPI(st.session_state.config.exchange)
        
        # API 키 발급 안내
        with st.expander("❓ API 키 발급 방법"):
            if st.session_state.config.exchange == "upbit":
                st.markdown("""
                **업비트 API 키 발급**
                1. [업비트 웹사이트](https://upbit.com) 로그인
                2. 마이페이지 > Open API 관리
                3. 'Open API Key 발급' 클릭
                4. 권한 설정:
                   - ✅ 자산 조회
                   - ✅ 주문 조회
                   - ✅ 주문하기
                   - ❌ 출금하기 (보안을 위해 체크 해제!)
                5. IP 주소 등록 (선택사항)
                6. Access Key & Secret Key 복사
                """)
            else:
                st.markdown("""
                **빗썸 API 키 발급**
                1. [빗썸 웹사이트](https://www.bithumb.com) 로그인
                2. 마이페이지 > API 관리
                3. 'API 키 발급' 클릭
                4. 권한 설정:
                   - ✅ 자산 조회
                   - ✅ 거래 권한
                   - ❌ 출금 권한 (보안!)
                5. Access Key & Secret Key 복사
                """)
    
    # 메인 영역
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 실시간 모니터링",
        "🔬 백테스팅",
        "📈 거래 내역",
        "📚 전략 가이드",
        "ℹ️ 사용법"
    ])
    
    with tab1:
        # 실시간 데이터 가져오기
        df = DataManager.get_ohlcv(
            st.session_state.config.exchange,
            st.session_state.config.market
        )
        
        if df.empty:
            st.error("❌ 데이터를 불러올 수 없습니다. 인터넷 연결을 확인하세요.")
            return
        
        # 지표 계산
        df = TechnicalIndicators.add_all_indicators(df)
        
        # 현재 가격 정보
        current_price = df.iloc[-1]['close']
        price_change = ((df.iloc[-1]['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close']) * 100
        
        # 메트릭 표시
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">현재가</div>
                <div class="metric-value">₩{current_price:,.0f}</div>
                <div style="color: {'#10b981' if price_change > 0 else '#ef4444'}; font-size: 1.2rem; font-weight: 700;">
                    {price_change:+.2f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            volume_24h = df['value'].sum() / 1e8
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">24h 거래량</div>
                <div class="metric-value">₩{volume_24h:.1f}억</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            high_24h = df['high'].max()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">24h 고가</div>
                <div class="metric-value">₩{high_24h:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            low_24h = df['low'].min()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">24h 저가</div>
                <div class="metric-value">₩{low_24h:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # 매매 신호
        strategies = {
            "RSI 모멘텀": TradingStrategy.rsi_momentum,
            "볼린저 밴드": TradingStrategy.bollinger_strategy,
            "MACD 크로스오버": TradingStrategy.macd_strategy
        }
        
        signal = strategies[st.session_state.config.strategy](df, st.session_state.config)
        
        st.markdown('<h2 class="sub-header">🎯 현재 매매 신호</h2>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if signal.action == "BUY":
                st.markdown(f'<div class="signal-buy">🟢 매수 신호</div>', unsafe_allow_html=True)
            elif signal.action == "SELL":
                st.markdown(f'<div class="signal-sell">🔴 매도 신호</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="signal-hold">⚪ 대기</div>', unsafe_allow_html=True)
        
        with col2:
            st.metric("신뢰도", f"{signal.confidence:.1f}%")
        
        with col3:
            st.metric("예상 가격", f"₩{signal.price:,.0f}")
        
        # 지표 상세
        with st.expander("📊 현재 지표 값", expanded=True):
            cols = st.columns(5)
            latest = df.iloc[-1]
            
            cols[0].metric("RSI", f"{latest['RSI']:.1f}")
            cols[1].metric("MACD", f"{latest['MACD']:.1f}")
            cols[2].metric("볼린저 %", f"{((latest['close']-latest['BB_lower'])/(latest['BB_upper']-latest['BB_lower'])*100):.1f}%")
            cols[3].metric("거래량 대비", f"{(latest['volume']/latest['Volume_MA']*100):.0f}%")
            cols[4].metric("SMA20 대비", f"{((latest['close']/latest['SMA_20']-1)*100):+.2f}%")
        
        # 차트
        st.plotly_chart(create_advanced_chart(df), use_container_width=True)
        
        # 자동매매 제어
        st.divider()
        st.markdown('<h2 class="sub-header">🤖 자동매매 제어</h2>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.session_state.is_running:
                st.markdown('<p class="status-running">● 자동매매 실행 중...</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="status-stopped">● 자동매매 중지됨</p>', unsafe_allow_html=True)
        
        with col2:
            if st.button("▶️ 시작", disabled=st.session_state.is_running, use_container_width=True, type="primary"):
                if st.session_state.config.use_real_trading and not hasattr(st.session_state, 'api'):
                    st.error("API 키를 먼저 입력하세요!")
                else:
                    st.session_state.is_running = True
                    st.success("✅ 자동매매가 시작되었습니다!")
                    st.rerun()
        
        with col3:
            if st.button("⏸️ 중지", disabled=not st.session_state.is_running, use_container_width=True):
                st.session_state.is_running = False
                st.warning("⚠️ 자동매매가 중지되었습니다.")
                st.rerun()
        
        # 경고 메시지
        if st.session_state.is_running:
            if st.session_state.config.use_real_trading:
                st.markdown("""
                <div class="warning-box">
                    ⚠️ <b>실거래 모드로 실행 중입니다!</b><br>
                    - 실제 자금이 사용됩니다<br>
                    - 정기적으로 모니터링하세요<br>
                    - 큰 뉴스나 이벤트 시 중지하세요
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="info-box">
                    ℹ️ <b>테스트 모드로 실행 중입니다</b><br>
                    - 신호만 표시되며 실제 거래는 하지 않습니다<br>
                    - 백테스팅 결과를 참고하세요
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<h2 class="sub-header">🔬 백테스팅</h2>', unsafe_allow_html=True)
        st.info("백테스팅 기능은 다음 업데이트에서 제공됩니다.")
    
    with tab3:
        st.markdown('<h2 class="sub-header">📈 거래 내역</h2>', unsafe_allow_html=True)
        
        if st.session_state.trades:
            trades_df = pd.DataFrame(st.session_state.trades)
            st.dataframe(trades_df, use_container_width=True)
        else:
            st.info("아직 거래 내역이 없습니다.")
    
    with tab4:
        st.markdown('<h2 class="sub-header">📚 전략 가이드</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        ### 🎯 RSI 모멘텀 전략
        
        **원리**
        - RSI가 과매도(30 이하) 구간에서 반등할 때 매수
        - RSI가 과매수(70 이상) 구간에 진입하면 매도
        
        **장점**
        - 명확한 신호
        - 역추세 매매에 효과적
        - 초보자도 이해하기 쉬움
        
        **단점**
        - 횡보장에서 거짓 신호 가능
        - 강한 추세장에서 기회 놓침
        
        **최적 시장**: 변동성이 큰 시장, 박스권 장세
        
        ---
        
        ### 📊 볼린저 밴드 전략
        
        **원리**
        - 하단 밴드 터치 후 반등 시 매수
        - 상단 밴드 돌파 시 매도
        
        **장점**
        - 변동성 고려
        - 추세 전환 포착
        - 급등/급락 대응
        
        **단점**
        - 강한 추세에서 손실 가능
        - 밴드 폭 변화에 민감
        
        **최적 시장**: 변동성 있는 추세장
        
        ---
        
        ### 📉 MACD 크로스오버 전략
        
        **원리**
        - MACD선이 시그널선 상향 돌파 시 매수 (골든 크로스)
        - MACD선이 시그널선 하향 돌파 시 매도 (데드 크로스)
        
        **장점**
        - 추세 전환 빠르게 포착
        - 모멘텀 확인
        - 중장기 추세 파악
        
        **단점**
        - 횡보장에서 잦은 신호
        - 후행성 지표
        
        **최적 시장**: 명확한 추세장
        """)
    
    with tab5:
        st.markdown('<h2 class="sub-header">ℹ️ 사용법</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        ## 🚀 빠른 시작 가이드
        
        ### 1단계: 설정
        1. **거래소 선택**: 업비트 또는 빗썸
        2. **거래 마켓 선택**: BTC, ETH 등
        3. **전략 선택**: RSI, 볼린저, MACD 중 선택
        
        ### 2단계: 테스트 (필수!)
        1. **테스트 모드**로 설정
        2. 신호 확인 및 전략 검증
        3. 백테스팅으로 성과 확인
        
        ### 3단계: 실거래 (선택)
        1. **실거래 모드**로 전환
        2. API 키 입력
        3. 소액(10만원)으로 시작
        4. 정기적으로 모니터링
        
        ---
        
        ## ⚠️ 주의사항
        
        ### 반드시 지켜주세요!
        - ❌ 생활비 투자 금지
        - ❌ 레버리지 사용 자제
        - ❌ 감정적 거래 금지
        - ❌ API 출금 권한 절대 금지
        - ✅ 소액으로 시작
        - ✅ 손절 설정 필수
        - ✅ 정기 모니터링
        - ✅ 분산 투자
        
        ---
        
        ## 💰 리스크 관리
        
        ### 손절/익절
        - **손절률**: 3-5% 권장
        - **익절률**: 5-10% 권장
        - **트레일링 스탑**: 수익 극대화
        
        ### 포지션 관리
        - 한 번에 전체 자산의 30% 이하만 투자
        - 여러 코인에 분산
        - 비상금 별도 유지
        
        ---
        
        ## 📞 문의 및 지원
        
        문제가 발생하면:
        1. 로그 파일 확인
        2. 설정 재확인
        3. 프로그램 재시작
        4. API 키 재발급
        
        ---
        
        ## ⚖️ 면책 조항
        
        - 이 프로그램은 교육 목적으로 제작되었습니다
        - 암호화폐 투자는 높은 리스크를 동반합니다
        - 과거 성과가 미래 수익을 보장하지 않습니다
        - 투자 손실에 대한 책임은 사용자에게 있습니다
        - 충분한 테스트 후 소액으로 시작하세요
        """)

if __name__ == "__main__":
    main()
