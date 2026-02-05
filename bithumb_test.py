import pybithumb
import time
from datetime import datetime
import sys

# [1단계: 시장 스캔]
def get_top_tickers():
    print("🔍 [Abisso Guard] 안전장치가 강화된 엔진을 가동합니다...")
    try:
        tickers = pybithumb.get_tickers()
        top_list = []
        for ticker in tickers[:15]:
            df = pybithumb.get_ohlcv(ticker)
            if df is not None:
                volume = df['volume'].iloc[-1] * df['close'].iloc[-1]
                top_list.append((ticker, volume))
        top_list.sort(key=lambda x: x[1], reverse=True)
        return top_list[:5]
    except:
        return [("BTC", 0), ("XRP", 0), ("ETH", 0)]

# 성적표 기록 함수 (기존과 동일)
def save_log(coin, side, price, profit=0, balance=0):
    with open("abisso_safety_report.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {coin:6} | {side:4} | 가격:{price:>10,} | 수익:{profit:>6.2f}% | 잔고:{balance:>10,.0f}\n")

recommendations = get_top_tickers()
print("\n🔥 [실시간 추천] TOP 5")
for i, (ticker, vol) in enumerate(recommendations):
    print(f"{i+1}위: {ticker:8} | 거래대금: {vol:,.0f}원")

# [2단계: 분산 투자 및 안전장치 설정]
try:
    choices = input("\n👉 투자할 3개 종목 선택 (예: 1, 2, 3): ")
    target_indices = [int(x.strip()) - 1 for x in choices.split(',')]
    selected_coins = [recommendations[i][0] for i in target_indices][:3]
    total_asset = float(input(f"💰 총 시작 자산(원): "))
    initial_total = total_asset
except:
    selected_coins = ["BTC", "XRP", "ETH"]; total_asset = 1000000

coin_data = {}
for coin in selected_coins:
    print(f"\n⚙️ [{coin}] 맞춤 설정 및 안전장치")
    k = float(input(f" - K값 (기본 0.5): ") or 0.5)
    stop = float(input(f" - 손절선% (기본 -1.0): ") or -1.0)
    profit = float(input(f" - 익절시작% (기본 1.0): ") or 1.0)
    # [추가] 최저가 방어선 설정
    current_p = pybithumb.get_current_price(coin)
    emergency_price = float(input(f" - 최저 방어선가 (현재 {current_p:,}원): ") or (current_p * 0.9))
    
    df = pybithumb.get_ohlcv(coin)
    coin_data[coin] = {
        'avg_vol': df['volume'].iloc[-6:-1].mean(),
        'virtual_coin_count': 0, 'buy_price': 0, 'highest_price': 0,
        'current_seed': total_asset / len(selected_coins),
        'k': k, 'stop_loss': stop, 'take_profit': profit,
        'emergency_price': emergency_price # 안전 스위치 가격
    }

print(f"\n🚀 애비쏘 가드 시스템 가동!")
print("-" * 65)

# [3단계: 실시간 루프]
start_time = datetime.now()
trade_count = 0

try:
    while True:
        for coin, data in coin_data.items():
            current_price = pybithumb.get_current_price(coin)
            if current_price is None: continue

            # 🚨 [안전장치] 최저 방어선 돌파 시 강제 종료
            if current_price <= data['emergency_price']:
                print(f"\n⚠️⚠️ [비상 정지] {coin} 가격이 방어선({data['emergency_price']:,}원)을 이탈했습니다!")
                if data['virtual_coin_count'] > 0:
                    settled_amount = (data['virtual_coin_count'] * current_price) * (1 - 0.0025)
                    data['current_seed'] = settled_amount
                    print(f"📢 {coin} 전량 긴급 매도 처리 완료.")
                    save_log(coin, "EMERGENCY_SELL", current_price, 0, settled_amount)
                
                print("🛑 리스크 관리를 위해 전체 시스템을 종료합니다.")
                raise KeyboardInterrupt # 리포트 출력 후 종료되도록 유도

            df_now = pybithumb.get_ohlcv(coin)
            if df_now is None: continue
            yesterday = df_now.iloc[-2]
            target_price = df_now['open'].iloc[-1] + (yesterday['high'] - yesterday['low']) * data['k']
            current_vol = df_now['volume'].iloc[-1]

            # 매수/매도 로직 (이전과 동일)
            if data['virtual_coin_count'] == 0:
                if current_price > target_price and current_vol > (data['avg_vol'] * 1.1):
                    data['buy_price'] = current_price
                    data['highest_price'] = current_price
                    data['virtual_coin_count'] = (data['current_seed'] * (1 - 0.0025)) / current_price
                    print(f"\n✅ [매수] {coin:6} | 진입가: {current_price:,}원")
                    save_log(coin, "BUY", current_price, 0, data['current_seed'])

            elif data['virtual_coin_count'] > 0:
                if current_price > data['highest_price']: data['highest_price'] = current_price
                profit_rate = ((current_price - data['buy_price']) / data['buy_price']) * 100
                drop_from_high = ((data['highest_price'] - current_price) / data['highest_price']) * 100

                if profit_rate <= data['stop_loss'] or (profit_rate >= data['take_profit'] and drop_from_high >= 0.3):
                    settled_amount = (data['virtual_coin_count'] * current_price) * (1 - 0.0025)
                    data['current_seed'] = settled_amount
                    trade_count += 1
                    status = "익절" if profit_rate > 0 else "손절"
                    print(f"\n🔔 [{status}] {coin:6} | 수익: {profit_rate:.2f}% | 잔고: {settled_amount:,.0f}원")
                    save_log(coin, "SELL", current_price, profit_rate, settled_amount)
                    data['virtual_coin_count'] = 0

            print(f"[{coin:4}: {current_price:>10,.0f}]", end='  |  ')
        print(end='\r')
        time.sleep(1)

except KeyboardInterrupt:
    current_total = sum(d['current_seed'] for d in coin_data.values())
    net_profit = ((current_total / initial_total) - 1) * 100
    print(f"\n\n📊 [최종 영업 보고] 거래:{trade_count}회 | 수익률:{net_profit:.2f}% | 종료시간:{datetime.now()}")
    sys.exit()