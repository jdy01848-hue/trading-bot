import requests
import json
from datetime import datetime

TD_KEY = "6e9a8257a2d04b80b56b022707232bff"                               

def get_historical_data(interval="1h", outputsize=500):
    url = "https://api.twelvedata.com/time_series"                            
    params = {"symbol":"XAU/USD","interval":interval,"outputsize":outputsize,"apikey":TD_KEY}
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
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        trs.append(tr)
    return round(sum(trs[-period:])/period, 2)

def find_order_blocks(highs, lows, closes, window=5):
    bullish_ob = min(lows[-window:])
    bearish_ob = max(highs[-window:])
    return bullish_ob, bearish_ob

def ai_analyst_filter(direction, rsi, adx, open_p, close_p, high_p, low_p):
    """محاكي الـ AI Analyst لفحص السلوك السعري الشمعي (Price Action)"""
    body = abs(close_p - open_p)
    total_range = high_p - low_p if (high_p - low_p) > 0 else 0.1
    
    if direction == "BUY":
        # الـ AI يفضل الشموع الارتدادية (ذيل سفلي طويل مثل المطرقة Pinbar) أو شمعة خضراء قوية
        lower_wick = min(open_p, close_p) - low_p
        if lower_wick > (body * 1.2) or close_p > open_p:
            return "CONFIRMED"
    elif direction == "SELL":
        # الـ AI يفضل ذيل علوي طويل أو شمعة حمراء هابطة قوية
        upper_wick = high_p - max(open_p, close_p)
        if upper_wick > (body * 1.2) or close_p < open_p:
            return "CONFIRMED"
            
    return "REJECTED"

def simulate_trade(direction, entry, atr, adx, future_candles):
    if adx >= 40:
        sl_mult, tp_mult = 2.0, 5.0
    elif adx >= 25:
        sl_mult, tp_mult = 1.5, 3.5
    else:
        sl_mult, tp_mult = 1.0, 2.5

    if direction == "BUY":
        sl = entry - sl_mult * atr
        tp = entry + tp_mult * atr
        for idx, candle in enumerate(future_candles):
            if float(candle['low']) <= sl: return "LOSS", round((entry-sl), 2), idx + 1
            if float(candle['high']) >= tp: return "WIN",  round((tp-entry), 2), idx + 1
    else:
        sl = entry + sl_mult * atr
        tp = entry - tp_mult * atr
        for idx, candle in enumerate(future_candles):
            if float(candle['high']) >= sl: return "LOSS", round((sl-entry), 2), idx + 1
            if float(candle['low']) <= tp: return "WIN",  round((entry-tp), 2), idx + 1

    return "TIMEOUT", 0, len(future_candles)

def run_backtest():
    print("🔄 جلب البيانات وتشغيل الـ AI Analyst...")
    data_1h = get_historical_data("1h", 500)
    data_4h = get_historical_data("4h", 200)

    closes_4h = [float(x['close']) for x in data_4h]
    highs_4h  = [float(x['high'])  for x in data_4h]
    lows_4h   = [float(x['low'])   for x in data_4h]

    closes_1h = [float(x['close']) for x in data_1h]
    highs_1h  = [float(x['high'])  for x in data_1h]
    lows_1h   = [float(x['low'])   for x in data_1h]
    opens_1h  = [float(x['open'])  for x in data_1h]

    results = []
    wins = losses = timeouts = 0
    total_profit = 0
    ai_rejections = 0

    i = 50
    while i < len(closes_1h) - 50:
        try:
            c1h = closes_1h[max(0,i-100):i]
            h1h = highs_1h[max(0,i-100):i]
            l1h = lows_1h[max(0,i-100):i]

            rsi = calc_rsi(c1h)
            atr = calc_atr(h1h, l1h, c1h)
            adx, plus_di, minus_di = calc_adx(h1h, l1h, c1h)
            bull_ob, bear_ob = find_order_blocks(h1h, l1h, c1h)

            j = min(i//2, len(closes_4h)-1)
            c4h = closes_4h[max(0,j-50):j]
            h4h = highs_4h[max(0,j-50):j]
            l4h = lows_4h[max(0,j-50):j]
            adx4, plus4, minus4 = calc_adx(h4h, l4h, c4h)

            price = closes_1h[i]
            future_candles = data_1h[i:i+50]

            direction = None
            if adx4 >= 25 and plus4 > minus4 and rsi < 45 and adx >= 20 and price <= (bull_ob * 1.002):
                direction = "BUY"
            elif adx4 >= 25 and minus4 > plus4 and rsi > 55 and adx >= 20 and price >= (bear_ob * 0.998):
                direction = "SELL"

            if direction:
                # فلترة ذكية إضافية بواسطة الـ AI
                ai_status = ai_analyst_filter(direction, rsi, adx, opens_1h[i], closes_1h[i], highs_1h[i], lows_1h[i])
                
                if ai_status == "CONFIRMED":
                    result, profit, candles_held = simulate_trade(direction, price, atr, adx4, future_candles)
                    results.append({"direction": direction, "price": price, "result": result, "profit": profit})
                    if result == "WIN":
                        wins += 1
                        total_profit += profit
                    elif result == "LOSS":
                        losses += 1
                        total_profit -= profit
                    else:
                        timeouts += 1
                    i += max(1, candles_held)
                else:
                    ai_rejections += 1
                    i += 2  # الـ AI رفض الصفقة، نتخطى ونبحث عن فرصة أفضل
            else:
                i += 2
        except:
            i += 2

    total = wins + losses
    rate  = round((wins/total)*100, 1) if total > 0 else 0

    report = f"""
📊 نتائج الباك تيست النهائي (Order Blocks + AI Analyst)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 إجمالي الصفقات المقبولة : {total}
✅ رابحة                    : {wins}
❌ خاسرة                    : {losses}
⏳ Timeout                  : {timeouts}
🛡️ صفقات خطيرة منعها الـ AI  : {ai_rejections}
🎯 Win Rate                 : {rate}%
💰 صافي الربح              : {round(total_profit, 2)} نقطة
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(report)
    return rate, results

if __name__ == "__main__":
    run_backtest()
