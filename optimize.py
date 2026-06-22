import requests
import json
import time

TD_KEY = "6e9a8257a2d04b80b56b022707232bff"

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

def precompute(data_1h, data_4h):
    closes_1h=[float(x['close']) for x in data_1h]
    highs_1h=[float(x['high']) for x in data_1h]
    lows_1h=[float(x['low']) for x in data_1h]
    closes_4h=[float(x['close']) for x in data_4h]
    highs_4h=[float(x['high']) for x in data_4h]
    lows_4h=[float(x['low']) for x in data_4h]

    snapshots = []
    for i in range(60, len(closes_1h)-60, 10):
        c1h=closes_1h[max(0,i-60):i]; h1h=highs_1h[max(0,i-60):i]; l1h=lows_1h[max(0,i-60):i]
        rsi = calc_rsi(c1h)
        atr = calc_atr(h1h,l1h,c1h)
        adx1,plus1,minus1 = calc_adx(h1h,l1h,c1h)
        j = min(i//4, len(closes_4h)-1)
        c4h=closes_4h[max(0,j-50):j+1]; h4h=highs_4h[max(0,j-50):j+1]; l4h=lows_4h[max(0,j-50):j+1]
        adx4,plus4,minus4 = calc_adx(h4h,l4h,c4h)
        price = closes_1h[i]
        future = closes_1h[i+1:i+60]
        if len(future) < 10 or atr <= 0:
            continue
        snapshots.append({
            "rsi":rsi,"adx4":adx4,"adx1":adx1,"plus4":plus4,"minus4":minus4,
            "plus1":plus1,"minus1":minus1,"price":price,"atr":atr,"future":future
        })
    return snapshots

def test_combo(snapshots, rsi_buy, rsi_sell, adx4_min, adx1_min):
    wins=losses=timeouts=0
    profit=0
    for s in snapshots:
        direction=None
        if s['adx4']>=adx4_min and s['plus4']>s['minus4'] and s['adx1']>=adx1_min and s['plus1']>s['minus1'] and s['rsi']<rsi_buy:
            direction="BUY"
        elif s['adx4']>=adx4_min and s['minus4']>s['plus4'] and s['adx1']>=adx1_min and s['minus1']>s['plus1'] and s['rsi']>rsi_sell:
            direction="SELL"
        if direction:
            result, p = simulate_trade(direction, s['price'], s['atr'], max(s['adx4'],s['adx1']), s['future'])
            if result=="WIN": wins+=1; profit+=p
            elif result=="LOSS": losses+=1; profit-=p
            else: timeouts+=1
    total = wins+losses
    rate = round((wins/total)*100,1) if total>0 else 0
    return total, wins, losses, rate, round(profit,2)

def run_optimization():
    print("🔄 جلب البيانات...")
    data_1h = get_historical_data("1h", 5000)
    time.sleep(8)
    data_4h = get_historical_data("4h", 1500)
    print(f"✅ {len(data_1h)} شمعة 1H, {len(data_4h)} شمعة 4H")

    print("🔄 حساب اللقطات (مرة واحدة)...")
    snapshots = precompute(data_1h, data_4h)
    print(f"✅ {len(snapshots)} لقطة جاهزة للاختبار")

    combos = []
    for rsi_buy in [25,30,35,40,45]:
        for rsi_sell in [55,60,65,70,75]:
            for adx4_min in [20,25,30]:
                for adx1_min in [15,20,25]:
                    combos.append((rsi_buy, rsi_sell, adx4_min, adx1_min))

    print(f"🔄 اختبار {len(combos)} تركيبة...")
    all_results = []
    for rsi_buy, rsi_sell, adx4_min, adx1_min in combos:
        total, wins, losses, rate, profit = test_combo(snapshots, rsi_buy, rsi_sell, adx4_min, adx1_min)
        if total >= 15:  # نتجاهل التركيبات بعينة صغيرة جداً
            all_results.append({
                "rsi_buy":rsi_buy,"rsi_sell":rsi_sell,"adx4_min":adx4_min,"adx1_min":adx1_min,
                "total":total,"wins":wins,"losses":losses,"rate":rate,"profit":profit
            })

    # ترتيب حسب صافي الربح
    all_results.sort(key=lambda x: x['profit'], reverse=True)

    print("\n📊 أفضل 10 تركيبات (مرتبة حسب صافي الربح، بعينة >= 15 صفقة):")
    print("━"*60)
    for r in all_results[:10]:
        print(f"RSI<{r['rsi_buy']}/>{r['rsi_sell']} ADX4>={r['adx4_min']} ADX1>={r['adx1_min']} | "
              f"عدد={r['total']} دقة={r['rate']}% ربح={r['profit']}")

    with open("optimization_results.json","w") as f:
        json.dump(all_results, f, ensure_ascii=False)

    return all_results

if __name__ == "__main__":
    run_optimization()
