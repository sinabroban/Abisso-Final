"""
💎 AI 자동매매 Pro - Commercial Edition
Bloomberg-Style | Advanced Risk Management | Telegram Alerts
"""

import streamlit as st
import pandas as pd
import numpy as np
import pyupbit
import pybithumb
from datetime import datetime
import time
import requests

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="💎 AI Trading Pro",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Bloomberg Style CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700;900&display=swap');
    
    * { font-family: 'Noto Sans KR', sans-serif; }
    
    .stApp { background-color: #0a0e27; }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, #00ff41 0%, #00b8ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 1rem 0 2rem 0;
    }
    
    .premium-container {
        background: linear-gradient(135deg, #1a1f3a 0%, #0f1228 100%);
        border: 1px solid rgba(0, 255, 65, 0.2);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 24px rgba(0, 255, 65, 0.1);
    }
    
    .coin-card {
        background: linear-gradient(135deg, #1a1f3a 0%, #0f1228 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .coin-card:hover {
        border-color: #00ff41;
        box-shadow: 0 8px 24px rgba(0, 255, 65, 0.2);
        transform: translateY(-3px);
    }
    
    .position-card {
        background: linear-gradient(135deg, #1a1f3a 0%, #0f1228 100%);
        border: 1px solid rgba(0, 255, 65, 0.3);
        border-left: 4px solid #00ff41;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 6px 20px rgba(0, 255, 65, 0.15);
    }
    
    .position-card.loss {
        border-left-color: #ff4b4b;
        border-color: rgba(255, 75, 75, 0.3);
        box-shadow: 0 6px 20px rgba(255, 75, 75, 0.15);
    }
    
    .mdd-warning {
        color: #ff4b4b;
        font-size: 1.5rem;
        font-weight: 900;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #00ff41 0%, #00b830 100%);
        color: #000000;
        font-weight: 900;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0, 255, 65, 0.4);
    }
    
    div[data-testid="stButton"] button[kind="secondary"] {
        background: linear-gradient(135deg, #ff4b4b 0%, #cc0000 100%);
        color: #ffffff;
        font-weight: 900;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(255, 75, 75, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ==================== 세션 상태 ====================
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.exchange = 'upbit'
    st.session_state.total = 1000000
    st.session_state.per_trade = 100000
    st.session_state.positions = {}
    st.session_state.running = False
    st.session_state.selected = []
    st.session_state.trades = []
    st.session_state.stop_loss = 3.0
    st.session_state.take_profit = 5.0
    st.session_state.use_trailing = False
    st.session_state.trailing = 2.0
    st.session_state.strategy = "안전형"
    st.session_state.rsi_th = 30
    st.session_state.bb_mult = 2.0
    st.session_state.tg_on = False
    st.session_state.tg_token = ""
    st.session_state.tg_chat = ""

# ==================== 텔레그램 ====================
def send_tg(msg):
    if not st.session_state.tg_on or not st.session_state.tg_token or not st.session_state.tg_chat:
        return
    try:
        url = f"https://api.telegram.org/bot{st.session_state.tg_token}/sendMessage"
        requests.post(url, data={"chat_id": st.session_state.tg_chat, "text": msg, "parse_mode": "HTML"}, timeout=5)
    except:
        pass

# ==================== Retry ====================
def retry(func, n=3, d=1):
    for i in range(n):
        try:
            r = func()
            if r is not None:
                return r
        except:
            if i < n - 1:
                time.sleep(d)
    return None

# ==================== 지표 ====================
def calc_ind(df):
    df['ma'] = df['close'].rolling(20).mean()
    df['std'] = df['close'].rolling(20).std()
    df['upper'] = df['ma'] + (df['std'] * st.session_state.bb_mult)
    df['lower'] = df['ma'] - (df['std'] * st.session_state.bb_mult)
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain / loss))
    
    df['ema12'] = df['close'].ewm(12).mean()
    df['ema26'] = df['close'].ewm(26).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['sig'] = df['macd'].ewm(9).mean()
    
    return df

# ==================== 신호 ====================
def get_sig(ticker, ex):
    try:
        def load():
            if ex == 'upbit':
                return pyupbit.get_ohlcv(ticker, interval="minute15", count=40)
            else:
                df = pybithumb.get_ohlcv(ticker.split('-')[1])
                return df.tail(40) if df is not None else None
        
        df = retry(load)
        if df is None or len(df) < 40:
            return "대기", 0, ""
        
        df = calc_ind(df)
        c = df.iloc[-1]
        p = df.iloc[-2]
        
        if st.session_state.strategy == "안전형":
            if c['rsi'] <= st.session_state.rsi_th and c['close'] <= c['lower'] * 1.02:
                return "강력매수", c['rsi'], f"RSI {c['rsi']:.1f}+BB하단"
            elif c['rsi'] < 40 and c['close'] < c['ma']:
                return "매수", c['rsi'], f"RSI {c['rsi']:.1f}"
        
        elif st.session_state.strategy == "공격형":
            vol = c['volume'] > df['volume'].rolling(20).mean().iloc[-1] * 1.5
            cross = (p['macd'] <= p['sig']) and (c['macd'] > c['sig'])
            if cross and vol:
                return "강력매수", c['rsi'], "MACD+거래량"
            elif cross:
                return "매수", c['rsi'], "MACD"
        
        elif st.session_state.strategy == "사용자설정":
            if c['rsi'] < st.session_state.rsi_th:
                return "매수", c['rsi'], f"RSI {c['rsi']:.1f}"
        
        return "대기", c['rsi'], ""
    except:
        return "대기", 0, ""

# ==================== 리스크 ====================
def check_risk(pos):
    try:
        def get_p():
            if st.session_state.exchange == 'upbit':
                return pyupbit.get_current_price(pos['ticker'])
            else:
                return pybithumb.get_current_price(pos['ticker'].split('-')[1])
        
        p = retry(get_p)
        if not p:
            return False, ""
        
        pct = ((p - pos['buy']) / pos['buy']) * 100
        
        if pct <= -st.session_state.stop_loss:
            return True, f"손절 {pct:.2f}%"
        
        if pct >= st.session_state.take_profit:
            if st.session_state.use_trailing:
                if 'peak' not in pos:
                    pos['peak'] = p
                else:
                    pos['peak'] = max(pos['peak'], p)
                
                dd = ((p - pos['peak']) / pos['peak']) * 100
                
                if dd <= -st.session_state.trailing:
                    return True, f"트레일링 {pct:.2f}%"
            else:
                return True, f"익절 {pct:.2f}%"
        
        return False, ""
    except:
        return False, ""

# ==================== 코인 ====================
@st.cache_data(ttl=30, show_spinner=False)
def get_coins(ex):
    try:
        if ex == 'upbit':
            ts = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOGE', 'KRW-SOL']
        else:
            ts = ['BTC', 'ETH', 'XRP', 'ADA', 'DOGE', 'SOL']
        
        coins = []
        for t in ts:
            try:
                if ex == 'upbit':
                    p = retry(lambda: pyupbit.get_current_price(t))
                    ticker = t
                else:
                    p = retry(lambda: pybithumb.get_current_price(t))
                    ticker = f'KRW-{t}'
                
                if not p:
                    continue
                
                sig, rsi, rsn = get_sig(ticker, ex)
                
                coins.append({
                    'ticker': ticker,
                    'name': ticker.split('-')[1],
                    'price': p,
                    'signal': sig,
                    'rsi': rsi,
                    'reason': rsn
                })
            except:
                continue
        
        return coins
    except:
        return []

def kr(s):
    n = {'BTC': '비트코인', 'ETH': '이더리움', 'XRP': '리플', 'ADA': '에이다', 'DOGE': '도지코인', 'SOL': '솔라나'}
    return n.get(s, s)

# ==================== 메인 ====================
def main():
    st.markdown('<h1 class="main-header">💎 AI Trading Pro</h1>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        
        ex = st.selectbox("거래소", ["upbit", "bithumb"], format_func=lambda x: "🟦 업비트" if x == "upbit" else "🟨 빗썸")
        st.session_state.exchange = ex
        
        st.divider()
        
        st.markdown("### 💰 투자")
        st.session_state.total = st.number_input("총 보유", 0, 100000000, st.session_state.total, 100000)
        st.session_state.per_trade = st.number_input("코인당", 10000, st.session_state.total, st.session_state.per_trade, 10000)
        
        st.divider()
        
        st.markdown("### 📊 전략")
        st.session_state.strategy = st.radio("모드", ["안전형", "공격형", "사용자설정"])
        
        if st.session_state.strategy == "사용자설정":
            st.session_state.rsi_th = st.slider("RSI", 20, 40, 30)
            st.session_state.bb_mult = st.slider("BB", 1.5, 3.0, 2.0, 0.1)
        
        st.divider()
        
        st.markdown("### 🛡️ 리스크")
        st.session_state.stop_loss = st.slider("손절%", 1.0, 10.0, 3.0, 0.5)
        st.session_state.take_profit = st.slider("익절%", 2.0, 20.0, 5.0, 0.5)
        st.session_state.use_trailing = st.checkbox("트레일링")
        if st.session_state.use_trailing:
            st.session_state.trailing = st.slider("트레일링%", 0.5, 5.0, 2.0, 0.1)
        
        st.divider()
        
        st.markdown("### 📱 텔레그램")
        st.session_state.tg_on = st.checkbox("알림")
        if st.session_state.tg_on:
            st.session_state.tg_token = st.text_input("Token", type="password")
            st.session_state.tg_chat = st.text_input("ChatID")
            if st.button("테스트"):
                send_tg("🤖 테스트")
                st.success("전송!")
        
        st.divider()
        
        st.markdown("### 🤖 매매")
        if st.session_state.running:
            if st.button("⏸️ 중지", use_container_width=True, type="secondary"):
                st.session_state.running = False
                send_tg("⏸️ 중지")
                st.rerun()
        else:
            if st.button("▶️ 시작", use_container_width=True, type="primary"):
                if not st.session_state.selected:
                    st.error("코인 선택")
                else:
                    st.session_state.running = True
                    send_tg(f"🚀 시작\n{st.session_state.strategy}")
                    st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["💰 코인", "📊 포지션", "📈 분석"])
    
    with tab1:
        st.markdown("### 💰 코인 선택")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"**{st.session_state.strategy}** | {st.session_state.per_trade:,}원")
        with col2:
            if st.button("🔄"):
                st.cache_data.clear()
                st.rerun()
        
        coins = get_coins(st.session_state.exchange)
        
        for c in coins:
            sel = c['ticker'] in st.session_state.selected
            
            badge = {
                "강력매수": ("🟢 강력매수", "#00ff41"),
                "매수": ("🔵 매수", "#0088ff"),
                "대기": ("⚪ 대기", "#666")
            }
            txt, col = badge.get(c['signal'], ("⚪ 대기", "#666"))
            
            col1, col2, col3 = st.columns([4, 2, 1])
            
            with col1:
                st.markdown(f"""
                <div class="coin-card">
                    <div style="font-size:1.3rem;font-weight:700;color:#fff;">{c['name']} <span style="color:#666;font-size:0.9rem;">{kr(c['name'])}</span></div>
                    <div style="color:#999;margin:0.5rem 0;">₩{c['price']:,.0f}</div>
                    <span style="background:{col};color:{'#000' if col=='#00ff41' else '#fff'};padding:0.4rem 1rem;border-radius:20px;font-size:0.85rem;font-weight:700;">{txt}</span>
                    <div style="color:#666;font-size:0.85rem;margin-top:0.5rem;">RSI:{c['rsi']:.0f} | {c['reason']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.write("")
                st.write("")
                if sel:
                    st.success("✓")
            
            with col3:
                st.write("")
                st.write("")
                if st.button("선택" if not sel else "취소", key=f"s{c['ticker']}"):
                    if sel:
                        st.session_state.selected.remove(c['ticker'])
                    else:
                        st.session_state.selected.append(c['ticker'])
                    st.rerun()
    
    with tab2:
        st.markdown("### 📊 포지션")
        
        if st.session_state.positions:
            for name, pos in st.session_state.positions.items():
                sell, rsn = check_risk(pos)
                
                if sell and st.session_state.running:
                    pft = pos['val'] - pos['inv']
                    pft_pct = (pft / pos['inv']) * 100
                    
                    st.session_state.trades.append({
                        'time': datetime.now(),
                        'coin': name,
                        'action': 'SELL',
                        'price': pos['now'],
                        'profit': pft,
                        'pct': pft_pct,
                        'reason': rsn
                    })
                    
                    send_tg(f"🔔<b>매도</b>\n{name}\n₩{pos['now']:,.0f}\n{pft:+,.0f}원({pft_pct:+.2f}%)\n{rsn}")
                    
                    del st.session_state.positions[name]
                    st.rerun()
                
                pft_pct = (pos['pft'] / pos['inv']) * 100
                cls = "profit" if pos['pft'] >= 0 else "loss"
                card = "position-card" if pos['pft'] >= 0 else "position-card loss"
                
                st.markdown(f"""
                <div class="{card}">
                    <div style="display:flex;justify-content:space-between;margin-bottom:1rem;padding-bottom:1rem;border-bottom:1px solid rgba(255,255,255,0.1);">
                        <div style="font-size:1.4rem;font-weight:900;color:#fff;">{name} <span style="color:#666;font-size:0.9rem;">{kr(name)}</span></div>
                        <div style="font-size:1.4rem;font-weight:900;color:{'#00ff41' if pos['pft']>=0 else '#ff4b4b'};">{pos['pft']:+,.0f}원({pft_pct:+.2f}%)</div>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.8rem;">
                        <div style="display:flex;justify-content:space-between;"><span style="color:#666;">매수</span><span style="font-weight:700;">₩{pos['buy']:,.0f}</span></div>
                        <div style="display:flex;justify-content:space-between;"><span style="color:#666;">현재</span><span style="font-weight:700;">₩{pos['now']:,.0f}</span></div>
                        <div style="display:flex;justify-content:space-between;"><span style="color:#666;">수량</span><span style="font-weight:700;">{pos['qty']:.8f}</span></div>
                        <div style="display:flex;justify-content:space-between;"><span style="color:#666;">평가</span><span style="font-weight:700;">₩{pos['val']:,.0f}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("없음")
    
    with tab3:
        st.markdown("### 📈 누적수익 & MDD")
        
        if st.session_state.trades:
            df = pd.DataFrame(st.session_state.trades)
            df['cum'] = df['profit'].cumsum()
            
            st.line_chart(df.set_index('time')['cum'])
            
            total = len(df)
            wins = len(df[df['profit'] > 0])
            rate = (wins / total * 100) if total > 0 else 0
            pft = df['profit'].sum()
            
            cum = df['cum'].values
            peak = np.maximum.accumulate(cum)
            dd = (cum - peak) / peak * 100
            mdd = dd.min() if len(dd) > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("거래", f"{total}회")
            with col2:
                st.metric("승률", f"{rate:.1f}%")
            with col3:
                st.metric("손익", f"{pft:+,.0f}원")
            with col4:
                st.markdown(f'<div class="mdd-warning">MDD {mdd:.2f}%</div>', unsafe_allow_html=True)
        else:
            st.info("없음")
    
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    inv = sum([p['inv'] for p in st.session_state.positions.values()])
    val = st.session_state.total - inv + sum([p['val'] for p in st.session_state.positions.values()])
    pft = sum([p['pft'] for p in st.session_state.positions.values()])
    pct = (pft / inv * 100) if inv > 0 else 0
    
    with col1:
        st.markdown(f'<div style="background:#1a1f3a;border:1px solid #00b8ff30;border-radius:12px;padding:1.2rem;text-align:center;"><div style="font-size:0.85rem;color:#666;margin-bottom:0.5rem;">총자산</div><div style="font-size:1.8rem;font-weight:900;color:#fff;">₩{val:,.0f}</div></div>', unsafe_allow_html=True)
    
    with col2:
        c = "#00ff41" if pft >= 0 else "#ff4b4b"
        st.markdown(f'<div style="background:#1a1f3a;border:1px solid #00b8ff30;border-radius:12px;padding:1.2rem;text-align:center;"><div style="font-size:0.85rem;color:#666;margin-bottom:0.5rem;">손익</div><div style="font-size:1.8rem;font-weight:900;color:{c};">{pft:+,.0f}원</div><div style="font-size:0.85rem;color:#666;">{pct:+.2f}%</div></div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div style="background:#1a1f3a;border:1px solid #00b8ff30;border-radius:12px;padding:1.2rem;text-align:center;"><div style="font-size:0.85rem;color:#666;margin-bottom:0.5rem;">투자중</div><div style="font-size:1.8rem;font-weight:900;color:#fff;">₩{inv:,.0f}</div></div>', unsafe_allow_html=True)
    
    with col4:
        s = "🟢 실행" if st.session_state.running else "⚪ 중지"
        st.markdown(f'<div style="background:#1a1f3a;border:1px solid #00b8ff30;border-radius:12px;padding:1.2rem;text-align:center;"><div style="font-size:0.85rem;color:#666;margin-bottom:0.5rem;">상태</div><div style="font-size:1.2rem;font-weight:900;color:#fff;">{s}</div></div>', unsafe_allow_html=True)
    
    if st.session_state.running and st.session_state.selected:
        for ticker in st.session_state.selected:
            name = ticker.split('-')[1]
            
            if name in st.session_state.positions:
                continue
            
            sig, rsi, rsn = get_sig(ticker, st.session_state.exchange)
            
            if sig in ["매수", "강력매수"]:
                def gp():
                    if st.session_state.exchange == 'upbit':
                        return pyupbit.get_current_price(ticker)
                    else:
                        return pybithumb.get_current_price(name)
                
                p = retry(gp)
                
                if p and st.session_state.per_trade > 0:
                    q = st.session_state.per_trade / p
                    
                    st.session_state.positions[name] = {
                        'ticker': ticker,
                        'buy': p,
                        'now': p,
                        'qty': q,
                        'inv': st.session_state.per_trade,
                        'val': st.session_state.per_trade,
                        'pft': 0
                    }
                    
                    send_tg(f"🟢<b>매수</b>\n{name}\n₩{p:,.0f}\n{q:.8f}\n{rsn}")
                    
                    st.success(f"✅ {name} 매수!")
                    time.sleep(1)
                    st.rerun()

if __name__ == "__main__":
    main()
