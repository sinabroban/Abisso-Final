"""
💎 Professional Crypto Trading Platform
Commercial-Grade | Real-time | High Performance
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
    page_title="💎 Pro Trading",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== OLED 블랙 테마 ====================
st.markdown("""
<style>
    .main, .stApp, [data-testid="stAppViewContainer"] {
        background-color: #000000 !important;
    }
    
    * { color: #FFFFFF !important; }
    
    .status-bar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #1a1a1a;
        padding: 1rem;
        z-index: 999;
        border-bottom: 2px solid #00ff41;
    }
    
    .status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .status-item {
        text-align: center;
    }
    
    .status-label {
        font-size: 0.7rem;
        color: #888 !important;
    }
    
    .status-value {
        font-size: 1.2rem;
        font-weight: 900;
    }
    
    .profit { color: #00ff41 !important; }
    .loss { color: #ff0040 !important; }
    
    .main-content {
        margin-top: 100px;
    }
    
    .coin-card {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .coin-card.selected {
        border: 2px solid #00ff41;
        background: #002200;
    }
    
    .position-card {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.8rem 0;
    }
    
    .stButton>button {
        width: 100%;
        min-height: 45px;
        border-radius: 6px;
        font-weight: 700;
    }
    
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        margin: 0.2rem;
    }
    
    .badge-buy { background: #00ff41; color: #000 !important; }
    .badge-sell { background: #ff0040; color: #fff !important; }
    .badge-neutral { background: #666; }
    
    @media (max-width: 768px) {
        .status-grid { grid-template-columns: repeat(2, 1fr); }
        .status-value { font-size: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# ==================== 세션 상태 ====================
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.exchange = 'upbit'
    st.session_state.total = 10000000
    st.session_state.invested = 0
    st.session_state.positions = {}
    st.session_state.selected = []
    st.session_state.running = False
    st.session_state.per_trade = 100000
    st.session_state.logs = []

# ==================== 캐시 ====================
@st.cache_data(ttl=30, show_spinner=False)
def get_coins(exchange):
    try:
        if exchange == 'upbit':
            tickers = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOGE', 
                      'KRW-SOL', 'KRW-DOT', 'KRW-MATIC', 'KRW-AVAX', 'KRW-LINK']
            coins = []
            for t in tickers:
                try:
                    p = pyupbit.get_current_price(t)
                    if not p: continue
                    df = pyupbit.get_ohlcv(t, interval="day", count=2)
                    if df is None or len(df) < 2: continue
                    ch = ((df['close'].iloc[-1] / df['close'].iloc[-2]) - 1) * 100
                    coins.append({
                        'ticker': t,
                        'name': t.split('-')[1],
                        'korean': get_korean(t.split('-')[1]),
                        'price': p,
                        'change': ch
                    })
                except: continue
            return coins
        else:
            tickers = ['BTC', 'ETH', 'XRP', 'ADA', 'DOGE', 'SOL']
            coins = []
            for t in tickers:
                try:
                    p = pybithumb.get_current_price(t)
                    if not p: continue
                    df = pybithumb.get_ohlcv(t)
                    if df is None or len(df) < 2: continue
                    df = df.tail(2)
                    ch = ((df['close'].iloc[-1] / df['close'].iloc[-2]) - 1) * 100
                    coins.append({
                        'ticker': f'KRW-{t}',
                        'name': t,
                        'korean': get_korean(t),
                        'price': p,
                        'change': ch
                    })
                except: continue
            return coins
    except:
        return []

def get_korean(s):
    n = {'BTC':'비트코인','ETH':'이더리움','XRP':'리플','ADA':'에이다','DOGE':'도지코인',
         'SOL':'솔라나','DOT':'폴카닷','MATIC':'폴리곤','AVAX':'아발란체','LINK':'체인링크'}
    return n.get(s, s)

def fmt(v):
    if v >= 1e8: return f"{v/1e8:.1f}억"
    if v >= 1e4: return f"{v/1e4:.0f}만"
    return f"{v:,.0f}"

# ==================== 메인 ====================
def main():
    # 상태바
    total_val = st.session_state.total - st.session_state.invested + sum([p['val'] for p in st.session_state.positions.values()])
    total_pft = sum([p['pft'] for p in st.session_state.positions.values()])
    pft_pct = (total_pft / st.session_state.invested * 100) if st.session_state.invested > 0 else 0
    avail = st.session_state.total - st.session_state.invested
    
    pft_cls = "profit" if total_pft >= 0 else "loss"
    
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-grid">
            <div class="status-item">
                <div class="status-label">총자산</div>
                <div class="status-value">{fmt(total_val)}원</div>
            </div>
            <div class="status-item">
                <div class="status-label">손익</div>
                <div class="status-value {pft_cls}">{total_pft:+,.0f}원</div>
                <div class="status-label">{pft_pct:+.2f}%</div>
            </div>
            <div class="status-item">
                <div class="status-label">투자중</div>
                <div class="status-value">{fmt(st.session_state.invested)}원</div>
            </div>
            <div class="status-item">
                <div class="status-label">사용가능</div>
                <div class="status-value">{fmt(avail)}원</div>
            </div>
        </div>
    </div>
    <div class="main-content"></div>
    """, unsafe_allow_html=True)
    
    # 탭
    t1, t2, t3 = st.tabs(["💰 코인선택", "📊 포지션", "⚙️ 설정"])
    
    with t1:
        col1, col2, col3 = st.columns([2,2,1])
        with col1:
            ex = st.selectbox("거래소", ["upbit","bithumb"], 
                             format_func=lambda x: "🟦 업비트" if x=="upbit" else "🟨 빗썸",
                             label_visibility="collapsed")
            st.session_state.exchange = ex
        with col2:
            st.info(f"코인당 **{fmt(st.session_state.per_trade)}원** 투자")
        with col3:
            if st.button("🔄"): 
                st.cache_data.clear()
                st.rerun()
        
        coins = get_coins(st.session_state.exchange)
        if not coins:
            st.error("데이터를 불러올 수 없습니다")
            return
        
        for c in coins:
            sel = c['ticker'] in st.session_state.selected
            cls = "coin-card selected" if sel else "coin-card"
            ch_cls = "profit" if c['change'] >= 0 else "loss"
            
            col1, col2, col3 = st.columns([3,2,1])
            with col1:
                st.markdown(f"""
                <div style="padding:0.5rem 0;">
                    <strong>{c['name']}</strong> <span style="color:#888;font-size:0.8rem;">{c['korean']}</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="text-align:right;padding:0.5rem 0;">
                    <div>₩{c['price']:,.0f}</div>
                    <div class="{ch_cls}">{c['change']:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                if st.button("✓" if sel else "선택", key=f"s_{c['ticker']}", use_container_width=True):
                    if sel:
                        st.session_state.selected.remove(c['ticker'])
                    else:
                        st.session_state.selected.append(c['ticker'])
                    st.rerun()
        
        if st.session_state.selected:
            st.success(f"✅ {len(st.session_state.selected)}개 선택 (필요: {fmt(len(st.session_state.selected)*st.session_state.per_trade)}원)")
    
    with t2:
        if st.session_state.positions:
            for name, p in st.session_state.positions.items():
                pft_cls = "profit" if p['pft'] >= 0 else "loss"
                pft_pct = (p['pft'] / p['inv']) * 100
                
                st.markdown(f"""
                <div class="position-card">
                    <div style="display:flex;justify-content:space-between;margin-bottom:0.8rem;">
                        <strong>{name} {p['kor']}</strong>
                        <span class="{pft_cls}" style="font-weight:900;">{p['pft']:+,.0f}원 ({pft_pct:+.2f}%)</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin:0.3rem 0;">
                        <span style="color:#888;">매수가</span>
                        <span>₩{p['buy']:,.0f}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin:0.3rem 0;">
                        <span style="color:#888;">현재가</span>
                        <span>₩{p['now']:,.0f}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin:0.3rem 0;">
                        <span style="color:#888;">평가금</span>
                        <span>₩{p['val']:,.0f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("포지션 없음")
    
    with t3:
        st.number_input("💰 총 보유 현금", 0, 100000000, st.session_state.total, 100000, 
                       key="tot", on_change=lambda: setattr(st.session_state, 'total', st.session_state.tot))
        
        st.number_input("💵 코인당 투자", 10000, 10000000, st.session_state.per_trade, 10000,
                       key="per", on_change=lambda: setattr(st.session_state, 'per_trade', st.session_state.per))
        
        st.divider()
        
        if st.session_state.running:
            if st.button("⏸️ 중지", use_container_width=True):
                st.session_state.running = False
                st.rerun()
        else:
            if st.button("▶️ 시작", use_container_width=True, type="primary"):
                if not st.session_state.selected:
                    st.error("코인 선택 필요")
                else:
                    st.session_state.running = True
                    
                    # 시뮬: 첫 코인 매수
                    if st.session_state.selected and not st.session_state.positions:
                        t = st.session_state.selected[0]
                        try:
                            if st.session_state.exchange == 'upbit':
                                p = pyupbit.get_current_price(t)
                            else:
                                p = pybithumb.get_current_price(t.split('-')[1])
                            
                            if p:
                                q = st.session_state.per_trade / p
                                n = t.split('-')[1]
                                st.session_state.positions[n] = {
                                    'ticker': t,
                                    'kor': get_korean(n),
                                    'buy': p,
                                    'now': p,
                                    'qty': q,
                                    'inv': st.session_state.per_trade,
                                    'val': st.session_state.per_trade,
                                    'pft': 0
                                }
                                st.session_state.invested += st.session_state.per_trade
                        except: pass
                    
                    st.rerun()

if __name__ == "__main__":
    main()
