import requests
import json
import time
from datetime import datetime

TD_KEY = "6e9a8257a2d04b80b56b022707232bff"

def get_historical_data(interval="1h", outputsize=500):
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol":"XAU/USD","interval":interval,
              "outputsize":outputsize,"apikey":TD_KEY}
    r = requests.get(url, params=params, timeout=30)
    data = r.json()
    if 'values' not in data:
        raise ValueError(f"خطأ: {data.get('message','unknown')}")
    values = list(reversed(data['values']))
    return values

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
        tr = max(highs[i]-lows[i],
                 abs(highs[i]-closes[i-1]),
                 abs(lows[i]-closes[i-1]))
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
    if len(closes) < 2:
        return 0
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i]-lows[i],
                 abs(highs[i]-closes[i-1]),
                 abs(lows[i]-closes[i-1]))
        trs.append(tr)
    return round(sum(trs[-period:])/min(period,len(trs)), 2)

def simulate_trade(direction, entry, atr, adx, future_prices):
    if adx >= 40:
        sl_mult, tp_mult = 2.0, 5.0
    elif adx >= 25:
        sl_mult, tp_mult = 1.5, 3.5
    else:
        sl_mult, tp_mult = 1.0, 2.5

    if direction == "BUY":
        sl = entry - sl_mult * atr
        tp = entry + tp_mult * atr
        for p in future_prices:
            if p <= sl: return "LOSS", round((entry-sl), 2)
            if p >= tp: return "WIN",  round((tp-entry), 2)
    else:
        sl = entry + sl_mult * atr
        tp = entry - tp_mult * atr
        for p in future_prices:
            if p >= sl: return "LOSS", round((sl-entry), 2)
            if p <= tp: return "WIN",  round((entry-tp), 2)

    return "TIMEOUT", 0

def run_backtest():
    print("🔄 جلب البيانات التاريخية...")
    data_1h = get_historical_data("1h", 5000)
    time.sleep(8)
    data_4h = get_historical_data("4h", 1500)

    closes_4h = [float(x['close']) for x in data_4h]
    highs_4h  = [float(x['high'])  for x in data_4h]
    lows_4h   = [float(x['low'])   for x in data_4h]

    closes_1h = [float(x['close']) for x in data_1h]
    highs_1h  = [float(x['high'])  for x in data_1h]
    lows_1h   = [float(x['low'])   for x in data_1h]

    print(f"✅ البيانات جاهزة: {len(closes_1h)} شمعة 1H, {len(closes_4h)} شمعة 4H")

    results = []
    wins = losses = timeouts = 0
    total_profit = 0

    for i in range(60, len(closes_1h)-60, 10):
        try:
            c1h = closes_1h[max(0,i-60):i]
            h1h = highs_1h[max(0,i-60):i]
            l1h = lows_1h[max(0,i-60):i]

            rsi = calc_rsi(c1h)
            atr = calc_atr(h1h, l1h, c1h)
            adx1, plus1, minus1 = calc_adx(h1h, l1h, c1h)

            j = min(i//4, len(closes_4h)-1)
            c4h = closes_4h[max(0,j-50):j+1]
            h4h = highs_4h[max(0,j-50):j+1]
            l4h = lows_4h[max(0,j-50):j+1]
            adx4, plus4, minus4 = calc_adx(h4h, l4h, c4h)

            price = closes_1h[i]
            future = closes_1h[i+1:i+60]
            if len(future) < 10:
                continue

            direction = None
            if adx4>=25 and plus4>minus4 and adx1>=20 and plus1>minus1 and rsi<30:
                direction = "BUY"
            elif adx4>=25 and minus4>plus4 and adx1>=20 and minus1>plus1 and rsi>70:
                direction = "SELL"

            if direction and atr > 0:
                result, profit = simulate_trade(direction, price, atr, max(adx4,adx1), future)
                results.append({
                    "direction": direction,
                    "price": price,
                    "result": result,
                    "profit": profit,
                    "rsi": rsi,
                    "adx4": adx4,
                    "adx1": adx1
                })
                if result == "WIN":
                    wins += 1
                    total_profit += profit
                elif result == "LOSS":
                    losses += 1
                    total_profit -= profit
                else:
                    timeouts += 1

        except Exception:
            pass

    total = wins + losses
    rate  = round((wins/total)*100, 1) if total > 0 else 0

    report = f"""
📊 نتائج Backtesting (بيانات تاريخية حقيقية)
━━━━━━━━━━━━━━━━
📈 إجمالي الصفقات : {total}
✅ رابحة          : {wins}
❌ خاسرة          : {losses}
⏳ Timeout        : {timeouts}
🎯 Win Rate       : {rate}%
💰 صافي الربح    : {round(total_profit, 2)} نقطة
━━━━━━━━━━━━━━━━
"""

    win_adx  = [r['adx4'] for r in results if r['result']=='WIN']
    loss_adx = [r['adx4'] for r in results if r['result']=='LOSS']
    win_rsi  = [r['rsi'] for r in results if r['result']=='WIN']
    loss_rsi = [r['rsi'] for r in results if r['result']=='LOSS']

    if win_adx:
        report += f"📊 ADX(4H) متوسط الرابحة : {round(sum(win_adx)/len(win_adx),1)}\n"
    if loss_adx:
        report += f"📊 ADX(4H) متوسط الخاسرة : {round(sum(loss_adx)/len(loss_adx),1)}\n"
    if win_rsi:
        report += f"📊 RSI متوسط الرابحة     : {round(sum(win_rsi)/len(win_rsi),1)}\n"
    if loss_rsi:
        report += f"📊 RSI متوسط الخاسرة     : {round(sum(loss_rsi)/len(loss_rsi),1)}\n"

    buy_results  = [r for r in results if r['direction']=='BUY']
    sell_results = [r for r in results if r['direction']=='SELL']
    buy_wins  = sum(1 for r in buy_results if r['result']=='WIN')
    sell_wins = sum(1 for r in sell_results if r['result']=='WIN')

    report += "━━━━━━━━━━━━━━━━\n"
    if buy_results:
        bw_rate = round((buy_wins/len(buy_results))*100,1)
        report += f"🟢 BUY:  {len(buy_results)} صفقة | دقة {bw_rate}%\n"
    if sell_results:
        sw_rate = round((sell_wins/len(sell_results))*100,1)
        report += f"🔴 SELL: {len(sell_results)} صفقة | دقة {sw_rate}%\n"

    with open("backtest_results.json","w") as f:
        json.dump(results, f, ensure_ascii=False)

    report += f"\n✅ تم حفظ {len(results)} صفقة في backtest_results.json"
    print(report)
    return rate, results, report

print("✅ Backtesting Engine جاهز")

if __name__ == "__main__":
    rate, results, report = run_backtest()
