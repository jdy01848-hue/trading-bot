"""
Backtesting حقيقي - يستخدم نفس محركات النظام الفعلية:
Confluence + Order Blocks + BOS/CHoCH + Candle Patterns +
Session Manipulation + Volume + Fibonacci + Liquidity
"""
import requests
import json
import time
import sys

TD_KEY = "6e9a8257a2d04b80b56b022707232bff"

sys.path.insert(0, '.')
from confluence import calc_confluence
from order_blocks import ob_signal
from bos_choch import detect_bos_choch
from candle_patterns import candle_signal
from session_manipulation import get_manipulation_summary

def get_historical_data(interval="1h", outputsize=5000):
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol":"XAU/USD","interval":interval,
              "outputsize":outputsize,"apikey":TD_KEY}
    r = requests.get(url, params=params, timeout=30)
    data = r.json()
    if 'values' not in data:
        raise ValueError(f"خطأ: {data.get('message','unknown')}")
    return list(reversed(data['values']))

def calc_rsi(closes, period=14):
    if len(closes) < period+3: return 50
    closes = closes[:-1]
    deltas = [closes[i]-closes[i-1] for i in range(1,len(closes))]
    gains  = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    avg_g  = sum(gains)/period
    avg_l  = sum(losses)/period
    if avg_l == 0: return 100
    return round(100-(100/(1+avg_g/avg_l)), 2)

def calc_adx(highs, lows, closes, period=14):
    if len(closes) < period+2:
        return 0, 0, 0
    trs, plus_dms, minus_dms = [], [], []
    for i in range(1, len(closes)):
        tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        plus_dm  = highs[i]-highs[i-1] if highs[i]-highs[i-1] > lows[i-1]-lows[i] else 0
        minus_dm = lows[i-1]-lows[i] if lows[i-1]-lows[i] > highs[i]-highs[i-1] else 0
        trs.append(tr)
        plus_dms.append(max(plus_dm, 0))
        minus_dms.append(max(minus_dm, 0))
    atr_s    = sum(trs[-period:]) / period
    plus_di  = 100*(sum(plus_dms[-period:])/period)/atr_s if atr_s else 0
    minus_di = 100*(sum(minus_dms[-period:])/period)/atr_s if atr_s else 0
    dx = 100*abs(plus_di-minus_di)/(plus_di+minus_di) if (plus_di+minus_di) else 0
    return round(dx,2), round(plus_di,2), round(minus_di,2)

def calc_atr(highs, lows, closes, period=14):
    if len(closes) < 2: return 0
    trs = []
    for i in range(1, len(closes)):
        trs.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])))
    return round(sum(trs[-period:])/min(period,len(trs)), 2)

def get_market_state(adx, plus_di, minus_di):
    if adx >= 90: return "EXTREME"
    if plus_di > minus_di:
        return "UP" if adx >= 25 else "WEAK_UP"
    else:
        return "DOWN" if adx >= 25 else "WEAK_DOWN"

def calc_fib_proximity(price, highs, lows):
    swing_high = max(highs[-50:]) if len(highs) >= 50 else max(highs)
    swing_low  = min(lows[-50:])  if len(lows)  >= 50 else min(lows)
    diff = swing_high - swing_low
    if diff == 0:
        return False
    levels = [swing_low + diff*r for r in [0.236,0.382,0.5,0.618,0.786]]
    closest = min(levels, key=lambda l: abs(l-price))
    return abs(closest-price) <= (diff*0.01)

def calc_liquidity(highs, lows):
    if len(highs) < 20: return False
    recent_highs = highs[-20:]
    recent_lows  = lows[-20:]
    high_range = max(recent_highs) - min(recent_highs)
    low_range  = max(recent_lows) - min(recent_lows)
    avg_price  = sum(recent_highs)/len(recent_highs)
    return (high_range/avg_price < 0.003) or (low_range/avg_price < 0.003)

def simulate_trade(direction, entry, atr, adx, future_prices):
    if adx >= 40: sl_mult, tp_mult = 2.0, 5.0
    elif adx >= 25: sl_mult, tp_mult = 1.5, 3.5
    else: sl_mult, tp_mult = 1.0, 2.5
    if direction == "BUY":
        sl = entry - sl_mult*atr; tp = entry + tp_mult*atr
        for p in future_prices:
            if p <= sl: return "LOSS", round(entry-sl,2)
            if p >= tp: return "WIN", round(tp-entry,2)
    else:
        sl = entry + sl_mult*atr; tp = entry - tp_mult*atr
        for p in future_prices:
            if p >= sl: return "LOSS", round(sl-entry,2)
            if p <= tp: return "WIN", round(entry-tp,2)
    return "TIMEOUT", 0

def run_full_backtest():
    print("🔄 جلب البيانات (1H, 4H, 15M)...")
    data_1h = get_historical_data("1h", 5000)
    time.sleep(8)
    data_4h = get_historical_data("4h", 1500)
    time.sleep(8)
    data_15m = get_historical_data("15min", 5000)

    closes_1h = [float(x['close']) for x in data_1h]
    highs_1h  = [float(x['high'])  for x in data_1h]
    lows_1h   = [float(x['low'])   for x in data_1h]
    opens_1h  = [float(x['open'])  for x in data_1h]

    closes_4h = [float(x['close']) for x in data_4h]
    highs_4h  = [float(x['high'])  for x in data_4h]
    lows_4h   = [float(x['low'])   for x in data_4h]

    closes_15 = [float(x['close']) for x in data_15m]
    highs_15  = [float(x['high'])  for x in data_15m]
    lows_15   = [float(x['low'])   for x in data_15m]

    print(f"✅ {len(closes_1h)} شمعة 1H | {len(closes_4h)} شمعة 4H | {len(closes_15)} شمعة 15M")

    results = []
    wins = losses = timeouts = 0
    total_profit = 0
    errors = 0

    for i in range(100, len(closes_1h)-60, 10):
        try:
            c1h = closes_1h[max(0,i-100):i]
            h1h = highs_1h[max(0,i-100):i]
            l1h = lows_1h[max(0,i-100):i]
            o1h = opens_1h[max(0,i-100):i]

            rsi1 = calc_rsi(c1h)
            atr1 = calc_atr(h1h, l1h, c1h)
            adx1, plus1, minus1 = calc_adx(h1h, l1h, c1h)

            j = min(i//4, len(closes_4h)-1)
            c4h = closes_4h[max(0,j-60):j+1]
            h4h = highs_4h[max(0,j-60):j+1]
            l4h = lows_4h[max(0,j-60):j+1]
            adx4, plus4, minus4 = calc_adx(h4h, l4h, c4h)
            r4 = calc_rsi(c4h)

            k = min(i*4, len(closes_15)-1)
            c15 = closes_15[max(0,k-100):k+1]
            h15 = highs_15[max(0,k-100):k+1]
            l15 = lows_15[max(0,k-100):k+1]
            adx15, plus15, minus15 = calc_adx(h15, l15, c15)
            r15 = calc_rsi(c15)

            price = closes_1h[i]
            future = closes_1h[i+1:i+60]
            if len(future) < 10 or atr1 <= 0:
                continue

            st4  = get_market_state(adx4, plus4, minus4)
            st1  = get_market_state(adx1, plus1, minus1)
            st15 = get_market_state(adx15, plus15, minus15)

            bos_result = detect_bos_choch(c1h, h1h, l1h)
            bos_text = ""
            if bos_result.get("BOS"): bos_text += f"BOS_{bos_result['BOS'][0]} "
            if bos_result.get("CHoCH"): bos_text += f"CHOCH_{bos_result['CHoCH'][0]}"
            ob_signals, _ = ob_signal(c1h, h1h, l1h, atr1)
            ob_text = " | ".join(ob_signals) if ob_signals else ""
            _, candle_dir, candle_strength = candle_signal(o1h, h1h, l1h, c1h, atr1)
            manip_msg, manip_score, manip_type = get_manipulation_summary(h1h, l1h, c1h, 12)
            near_fib = calc_fib_proximity(price, h1h, l1h)
            has_liq  = calc_liquidity(h1h, l1h)

            _, _, cf_buy, cf_sell, _ = calc_confluence(
                st4, st1, st15, adx4, adx1, adx15,
                r4, rsi1, r15, bos_text, ob_text,
                near_fib, has_liq, False, 8, 0
            )

            buy_count  = sum([adx4>=25 and plus4>minus4, adx1>=20 and plus1>minus1, rsi1<45])
            sell_count = sum([adx4>=25 and minus4>plus4, adx1>=20 and minus1>plus1, rsi1>55])

            direction = None
            if buy_count >= 2 and cf_buy >= cf_sell:
                direction = "BUY"
            elif sell_count >= 2 and cf_sell >= cf_buy:
                direction = "SELL"

            if direction:
                result, profit = simulate_trade(direction, price, atr1, max(adx4,adx1), future)
                results.append({
                    "direction": direction, "price": price, "result": result, "profit": profit,
                    "rsi1": rsi1, "adx4": adx4, "adx1": adx1,
                    "cf_buy": cf_buy, "cf_sell": cf_sell,
                    "manip_score": manip_score, "near_fib": near_fib, "has_liq": has_liq
                })
                if result == "WIN": wins += 1; total_profit += profit
                elif result == "LOSS": losses += 1; total_profit -= profit
                else: timeouts += 1

        except Exception as e:
            errors += 1
            if errors <= 3:
                import traceback
                print(f"⚠️ خطأ في اللقطة {i}: {e}")
                traceback.print_exc()

    total = wins + losses
    rate  = round((wins/total)*100, 1) if total > 0 else 0

    report = f"""
📊 نتائج Backtesting الكامل (بمحركات النظام الحقيقية)
━━━━━━━━━━━━━━━━
📈 إجمالي الصفقات : {total}
✅ رابحة          : {wins}
❌ خاسرة          : {losses}
⏳ Timeout        : {timeouts}
🎯 Win Rate       : {rate}%
💰 صافي الربح    : {round(total_profit, 2)} نقطة
⚠️ أخطاء          : {errors}
━━━━━━━━━━━━━━━━
"""

    buy_results  = [r for r in results if r['direction']=='BUY']
    sell_results = [r for r in results if r['direction']=='SELL']
    buy_wins  = sum(1 for r in buy_results if r['result']=='WIN')
    sell_wins = sum(1 for r in sell_results if r['result']=='WIN')

    if buy_results:
        report += f"🟢 BUY:  {len(buy_results)} صفقة | دقة {round((buy_wins/len(buy_results))*100,1)}%\n"
    if sell_results:
        report += f"🔴 SELL: {len(sell_results)} صفقة | دقة {round((sell_wins/len(sell_results))*100,1)}%\n"

    with open("backtest_full_results.json","w") as f:
        json.dump(results, f, ensure_ascii=False)

    report += f"\n✅ تم حفظ {len(results)} صفقة في backtest_full_results.json"
    print(report)
    return rate, results

print("✅ Full Backtesting Engine جاهز")

if __name__ == "__main__":
    run_full_backtest()
