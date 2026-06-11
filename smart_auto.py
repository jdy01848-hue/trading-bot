import requests
import json
import time
from datetime import datetime

TD_KEY = "6e9a8257a2d04b80b56b022707232bff"
SYMBOL = "XAU/USD"

def get_live_data(interval="1h", outputsize=100):
    url = "https://api.twelvedata.com/time_series"                            
    params = {"symbol": SYMBOL, "interval": interval, "outputsize": outputsize, "apikey": TD_KEY}
    r = requests.get(url, params=params, timeout=30)
    data = r.json()
    if 'values' not in data:
        raise ValueError(f"خطأ في جلب البيانات الحية: {data.get('message','unknown')}")
    return list(reversed(data['values']))

def calc_rsi(closes, period=14):
    closes = closes[:-1]
    deltas = [closes[i]-closes[i-1] for i in range(1, len(closes))]
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

def find_order_blocks(highs, lows, window=5):
    bullish_ob = min(lows[-window:])
    bearish_ob = max(highs[-window:])
    return bullish_ob, bearish_ob

def ai_analyst_filter(direction, open_p, close_p, high_p, low_p):
    body = abs(close_p - open_p)
    if direction == "BUY":
        lower_wick = min(open_p, close_p) - low_p
        if lower_wick > (body * 1.2) or close_p > open_p: return "CONFIRMED"
    elif direction == "SELL":
        upper_wick = high_p - max(open_p, close_p)
        if upper_wick > (body * 1.2) or close_p < open_p: return "CONFIRMED"
    return "REJECTED"

def start_live_bot():
    print("✅ Smart Monitor جاهز")
    print("✅ Order Blocks جاهز")
    print("✅ AI Analyst (Gemini) جاهز")
    print("🚀 البوت الآن في وضع المراقبة الحية لأسواق الذهب (XAU/USD)...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    while True:
        try:
            # 1. جلب البيانات الحية الحالية
            data_1h = get_live_data("1h", 100)
            data_4h = get_live_data("4h", 50)
            
            closes_1h = [float(x['close']) for x in data_1h]
            highs_1h  = [float(x['high'])  for x in data_1h]
            lows_1h   = [float(x['low'])   for x in data_1h]
            opens_1h  = [float(x['open'])  for x in data_1h]
            
            closes_4h = [float(x['close']) for x in data_4h]
            highs_4h  = [float(x['high'])  for x in data_4h]
            lows_4h   = [float(x['low'])   for x in data_4h]
            
            # 2. حساب المؤشرات الحية للشمعة الأخيرة المغلقة
            rsi = calc_rsi(closes_1h)
            atr = calc_atr(highs_1h, lows_1h, closes_1h)
            adx, _, _ = calc_adx(highs_1h, lows_1h, closes_1h)
            bull_ob, bear_ob = find_order_blocks(highs_1h, lows_1h)
            
            adx4, plus4, minus4 = calc_adx(highs_4h, lows_4h, closes_4h)
            
            current_price = closes_1h[-1]
            current_time = data_1h[-1]['datetime']
            
            print(f"⏳ [تحديث {current_time}] السعر الحالي: {current_price} | RSI: {rsi} | ADX (4H): {adx4}", end="\r")
            
            # 3. فحص شروط الدخول الحية
            direction = None
            if adx4 >= 25 and plus4 > minus4 and rsi < 45 and adx >= 20 and current_price <= (bull_ob * 1.002):
                direction = "BUY"
            elif adx4 >= 25 and minus4 > plus4 and rsi > 55 and adx >= 20 and current_price >= (bear_ob * 0.998):
                direction = "SELL"
                
            if direction:
                # تشغيل مصفاة الـ AI الحية للشمعة الحالية
                ai_status = ai_analyst_filter(direction, opens_1h[-1], closes_1h[-1], highs_1h[-1], lows_1h[-1])
                
                if ai_status == "CONFIRMED":
                    sl_mult = 2.0 if adx4 >= 40 else (1.5 if adx4 >= 25 else 1.0)
                    tp_mult = 5.0 if adx4 >= 40 else (3.5 if adx4 >= 25 else 2.5)
                    
                    sl = current_price - (sl_mult * atr) if direction == "BUY" else current_price + (sl_mult * atr)
                    tp = current_price + (tp_mult * atr) if direction == "BUY" else current_price - (tp_mult * atr)
                    
                    print(f"\n🚨 🔥 [إشارة حيّة!] تم رصد فرصة {direction} بواسطة المحرك والـ AI!")
                    print(f"🎯 سعر الدخول الحقيقي : {current_price}")
                    print(f"🛑 وقف الخسارة (SL)  : {round(sl, 2)}")
                    print(f"💰 جني الأرباح  (TP)  : {round(tp, 2)}")
                    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    
                    # لمنع تكرار نفس الإشارة، ينام البوت لمدة ساعة كاملة حتى إغلاق الشمعة التالية
                    time.sleep(3600)
                else:
                    print(f"\n🛡️ تم رصد فرصة رياضية {direction} ولكن الـ AI Analyst رفضها لحمايتك.")
            
            # فحص كل 60 ثانية لتحديث البيانات
            time.sleep(60)
            
        except Exception as e:
            print(f"\n❌ خطأ أثناء المراقبة: {e}")
            time.sleep(10)

if __name__ == "__main__":
    start_live_bot()
