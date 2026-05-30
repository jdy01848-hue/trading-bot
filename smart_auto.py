import requests
from bos_choch import detect_bos_choch, find_swing_points
from order_blocks import ob_signal
from ai_model import ai_boost, train_from_results
from auto_tracker import save_trade
from ai_analyst import get_ai_analysis
from narrative import build_narrative
from confluence import calc_confluence
from candle_patterns import candle_signal
from telegram_bot import listener_thread, send_trade_buttons
from price_monitor import save_active_trade, check_trade
from volume_engine import get_volume_summary
from session_manipulation import get_manipulation_summary
import time
import threading
from auto_tracker import check_trade

def run_tracker():
    while True:
        try:
            check_trade()
        except:
            pass
        time.sleep(60)

tracker_thread = threading.Thread(target=run_tracker, daemon=True)
tracker_thread.start()
from datetime import datetime, timezone

TOKEN = "8793823731:AAG1TKA6-6SZzqc03aAV3UWnOWgrPpgZFSA"
CHAT_ID = "5902098963"
TD_KEY = "6e9a8257a2d04b80b56b022707232bff"
NEWS_KEY = "9233c3106a144d7ebfce54e081f46603"
BALANCE = 30
RISK_PERCENT = 1
last_report_date = ""
last_signal = ""

def send(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except:
        print("خطأ في الإرسال")

def calc_position_size(balance, risk_percent, entry, sl):
    risk_amount = balance * (risk_percent / 100)
    sl_distance = abs(entry - sl)
    if sl_distance == 0:
        return 0.01
    lots = round(risk_amount / (sl_distance * 100), 4)
    return max(lots, 0.01)

def calc_sl_tp(direction, price, atr, adx):
    if adx >= 40:
        sl_mult = 2.0
        tp_mult = 5.0
    elif adx >= 25:
        sl_mult = 1.5
        tp_mult = 3.5
    else:
        sl_mult = 1.0
        tp_mult = 2.5
    if direction == "BUY":
        sl = round(price - sl_mult * atr, 2)
        tp = round(price + tp_mult * atr, 2)
    else:
        sl = round(price + sl_mult * atr, 2)
        tp = round(price - tp_mult * atr, 2)
    rr = round(abs(price-tp)/abs(price-sl), 2) if abs(price-sl) > 0 else 0
    return sl, tp, rr

def get_data(interval, outputsize=100):
    TD_KEY = "6e9a8257a2d04b80b56b022707232bff"
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": "XAU/USD", "interval": interval,
              "outputsize": outputsize, "apikey": TD_KEY}
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=15)
            data = r.json()
            if 'values' not in data:
                raise ValueError(f"خطأ API: {data.get('message','unknown')}")
            closes = [float(x['close']) for x in reversed(data['values'])]
            highs  = [float(x['high'])  for x in reversed(data['values'])]
            lows   = [float(x['low'])   for x in reversed(data['values'])]
            opens  = [float(x['open'])  for x in reversed(data['values'])]
            return closes, highs, lows, opens
        except Exception as e:
            if attempt == 2:
                raise ValueError(f"فشل جلب البيانات: {e}")
            time.sleep(5)


def calc_rsi(closes, period=14):
    # إصلاح RSI - نستخدم آخر شمعة مكتملة فقط
    if len(closes) < period + 1:
        return 50
    closes = closes[:-1]  # نحذف الشمعة الأخيرة غير المكتملة
    deltas = [closes[i]-closes[i-1] for i in range(1, len(closes))]
    gains  = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calc_macd(closes):
    def ema(data, period):
        k = 2 / (period + 1)
        e = data[0]
        for p in data[1:]:
            e = p * k + e * (1 - k)
        return e
    macd = ema(closes, 12) - ema(closes, 26)
    signal = ema(closes[-9:], 9)
    return round(macd, 4), round(signal, 4)

def calc_atr(highs, lows, closes, period=14):
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i]-lows[i],
                 abs(highs[i]-closes[i-1]),
                 abs(lows[i]-closes[i-1]))
        trs.append(tr)
    return round(sum(trs[-period:]) / period, 2)

def calc_ma(closes, period):
    return round(sum(closes[-period:]) / period, 2)

def calc_adx(highs, lows, closes, period=14):
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
    plus_di  = 100 * (sum(plus_dms[-period:]) / period) / atr_s if atr_s else 0
    minus_di = 100 * (sum(minus_dms[-period:]) / period) / atr_s if atr_s else 0
    dx = 100 * abs(plus_di-minus_di) / (plus_di+minus_di) if (plus_di+minus_di) else 0
    return round(dx, 2), round(plus_di, 2), round(minus_di, 2)

def trend_strength(adx):
    if adx >= 90:   return "⚠️ OVEREXTENDED"
    elif adx >= 40: return "💪 EXTREME"
    elif adx >= 25: return "⚡ STRONG"
    elif adx >= 20: return "📊 DEVELOPING"
    else:           return "😴 WEAK"

def exhaustion_check(adx, rsi, direction):
    # Exhaustion Detection
    reasons = []
    is_exhausted = False
    if adx > 90:
        reasons.append("ترند مبالغ فيه ⚠️")
        is_exhausted = True
    if direction == "UP" and rsi > 85:
        reasons.append("RSI مرتفع جداً ⚠️")
        is_exhausted = True
    if direction == "DOWN" and rsi < 15:
        reasons.append("RSI منخفض جداً ⚠️")
        is_exhausted = True
    if adx > 70 and direction == "UP" and rsi < 20:
        reasons.append("إرهاق السوق ⚠️")
        is_exhausted = True
    return is_exhausted, reasons

def market_state(highs, lows, closes):
    adx, plus_di, minus_di = calc_adx(highs, lows, closes)
    atr     = calc_atr(highs, lows, closes)
    atr_old = calc_atr(highs[:-5], lows[:-5], closes[:-5])
    strength = trend_strength(adx)
    if atr > atr_old * 2.0 and atr > 35:
        return "⚡ VOLATILE", "BLOCK", adx, strength
    elif adx >= 40:
        return ("📈 EXTREME UP","TREND",adx,strength) if plus_di>minus_di else ("📉 EXTREME DOWN","TREND",adx,strength)
    elif adx >= 25:
        return ("📈 TRENDING UP","TREND",adx,strength) if plus_di>minus_di else ("📉 TRENDING DOWN","TREND",adx,strength)
    elif adx < 20:
        return "↔️ RANGING","RANGE",adx,strength
    else:
        return "🔄 WEAK TREND","WEAK",adx,strength

def smart_structure(highs, lows, adx, plus_di, minus_di):
    if adx >= 25:
        return ("📈 Uptrend (ADX)","BULLISH") if plus_di>minus_di else ("📉 Downtrend (ADX)","BEARISH")
    rh, rl = highs[-10:], lows[-10:]
    hh = rh[-1] > max(rh[:-1])
    hl = rl[-1] > min(rl[:-1])
    ll = rl[-1] < min(rl[:-1])
    lh = rh[-1] < max(rh[:-1])
    if hh and hl:   return "📈 Uptrend (HH/HL)","BULLISH"
    elif ll and lh: return "📉 Downtrend (LL/LH)","BEARISH"
    else:           return "↔️ Ranging","NEUTRAL"

def detect_pullback(bias_4h, bias_15m):
    if bias_4h == "BEARISH" and bias_15m == "BULLISH":
        return True, "⚠️ Pullback صاعد داخل ترند هابط"
    elif bias_4h == "BULLISH" and bias_15m == "BEARISH":
        return True, "⚠️ Pullback هابط داخل ترند صاعد"
    return False, ""

def smart_rsi_signal(rsi, adx, trend):
    if adx >= 25:
        if rsi < 32 and trend == "UP":    return "BUY"
        elif rsi > 68 and trend == "DOWN": return "SELL"
        else: return "NEUTRAL"
    else:
        if rsi < 35:   return "BUY"
        elif rsi > 65: return "SELL"
        else: return "NEUTRAL"

def is_kill_zone(hour_utc, minute_utc=0):
    """
    Kill Zones — أفضل أوقات الدخول
    لندن: 10:00-11:00 UTC
    نيويورك: 13:00-14:00 UTC
    تداخل: 12:00-13:00 UTC
    """
    # لندن Kill Zone
    if 10 <= hour_utc < 11:
        return True, "🔥 Kill Zone لندن"
    # نيويورك Kill Zone
    if 13 <= hour_utc < 14:
        return True, "🔥 Kill Zone نيويورك"
    # تداخل
    if 12 <= hour_utc < 13:
        return True, "🔥 Kill Zone تداخل"
    return False, ""

def get_session(hour_utc):
    if 13 <= hour_utc <= 17:
        return "🔥 تداخل لندن/نيويورك", 10
    elif 8 <= hour_utc <= 13:
        return "✅ جلسة لندن", 7
    elif 17 <= hour_utc <= 22:
        return "✅ جلسة نيويورك", 7
    elif 0 <= hour_utc < 8:
        return "😴 جلسة آسيا", 2
    else:
        return "😴 جلسة آسيا", 2

def build_reason_engine(direction, adx, rsi, bias_4h, bias_1h,
                        is_pullback, is_exhausted, exhaustion_reasons,
                        news_impact, hour_utc, score):
    reasons = []
    blocks  = []

    # أسباب الإيجاب
    if adx >= 40:   reasons.append("ترند عنيف✅")
    elif adx >= 25: reasons.append("ترند قوي✅")

    if direction == "BUY":
        if bias_4h == "BULLISH": reasons.append("هيكل صاعد✅")
        if rsi < 35: reasons.append("RSI ذروة بيع✅")
    elif direction == "SELL":
        if bias_4h == "BEARISH": reasons.append("هيكل هابط✅")
        if rsi > 65: reasons.append("RSI ذروة شراء✅")

    if news_impact <= 3: reasons.append("أخبار آمنة✅")

    # أسباب المنع
    if is_exhausted:
        blocks.extend(exhaustion_reasons)
    if is_pullback:
        blocks.append("Pullback عكسي⚠️")
    if hour_utc < 8:
        blocks.append("جلسة آسيا ضعيفة⚠️")
    if adx > 90:
        blocks.append("ترند مبالغ فيه⚠️")
    if news_impact >= 7:
        blocks.append("أخبار خطرة⛔")

    return reasons, blocks

def quality_score(direction, adx_4h, adx_1h, bias_4h, bias_1h,
                  rsi_1h, rsi_15m, macd_1h, macd_sig_1h,
                  news_impact, is_pullback, hour_utc, is_exhausted):
    score, details = 0, []

    if adx_4h >= 90:   score += 10;  details.append("ترند مبالغ⚠️")
    elif adx_4h >= 40: score += 25;  details.append("ترند عنيف✅")
    elif adx_4h >= 25: score += 18;  details.append("ترند قوي✅")
    elif adx_4h >= 20: score += 10;  details.append("ترند ضعيف⚠️")

    if direction == "BUY":
        if bias_4h=="BULLISH" and bias_1h=="BULLISH": score+=20; details.append("هيكل✅")
        elif bias_4h=="BULLISH": score+=10; details.append("هيكل 4H✅")
        if rsi_1h < 35:   score+=15; details.append("RSI قوي✅")
        elif rsi_1h < 45: score+=8;  details.append("RSI⚠️")
        if macd_1h > macd_sig_1h: score+=10; details.append("MACD✅")
    elif direction == "SELL":
        if bias_4h=="BEARISH" and bias_1h=="BEARISH": score+=20; details.append("هيكل✅")
        elif bias_4h=="BEARISH": score+=10; details.append("هيكل 4H✅")
        if rsi_1h > 65:   score+=15; details.append("RSI قوي✅")
        elif rsi_1h > 55: score+=8;  details.append("RSI⚠️")
        if macd_1h < macd_sig_1h: score+=10; details.append("MACD✅")

    if news_impact <= 2:   score+=15; details.append("أخبار آمنة✅")
    elif news_impact <= 5: score+=7;  details.append("أخبار⚠️")

    _, session_pts = get_session(hour_utc)
    score += session_pts
    if session_pts >= 10: details.append("جلسة ممتازة✅")
    elif session_pts >= 7: details.append("جلسة جيدة✅")

    if is_pullback:   score = int(score * 0.7); details.append("Pullback⚠️")
    if is_exhausted:  score = int(score * 0.5); details.append("إرهاق⚠️")

    confidence = min(round(score), 100)
    if confidence >= 80:   grade = "🔥 ممتاز"
    elif confidence >= 65: grade = "✅ جيد"
    elif confidence >= 50: grade = "⚠️ مقبول"
    else:                  grade = "❌ ضعيف"

    return confidence, grade, details

def calc_support_resistance(highs, lows, lookback=20):
    return round(min(lows[-lookback:]), 2), round(max(highs[-lookback:]), 2)

def classify_news(title):
    t = title.lower()
    high = ["cpi","nfp","fomc","fed rate","interest rate","inflation",
            "unemployment","gdp","war","attack","crisis","emergency","sanctions","collapse"]
    med  = ["fed","powell","treasury","dollar","gold","federal reserve","rate","economy"]
    for w in high:
        if w in t: return 10, "🔴 خبر عالي التأثير"
    for w in med:
        if w in t: return 5,  "🟡 خبر متوسط التأثير"
    return 1, "🟢 خبر منخفض التأثير"

def check_news():
    try:
        url = "https://newsapi.org/v2/everything"
        params = {"q": "gold XAU Federal Reserve inflation interest rate",
                  "language": "en", "sortBy": "publishedAt",
                  "pageSize": 5, "apiKey": NEWS_KEY}
        articles = requests.get(url, params=params, timeout=10).json().get('articles', [])
        max_impact, top_msg = 0, "✅ لا أخبار مؤثرة"
        for a in articles[:5]:
            impact, msg = classify_news(a.get('title',''))
            if impact > max_impact:
                max_impact = impact
                top_msg = f"{msg}: {a.get('title','')[:35]}..."
        return max_impact >= 7, max_impact, top_msg
    except:
        return False, 0, "✅ لا أخبار"

def save_journal(signal, price, confidence, sl, tp, lots, reasons):
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        line = f"{now}|{signal}|{price}|{confidence}%|SL:{sl}|TP:{tp}|Lots:{lots}|{','.join(reasons[:2])}\n"
        with open("journal.txt", "a") as f:
            f.write(line)
    except:
        pass

def send_daily_report():
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        with open("journal.txt", "r") as f:
            lines = f.readlines()
        today_trades = [l for l in lines if today in l]
        total = len(today_trades)
        buy   = sum(1 for l in today_trades if "BUY" in l)
        sell  = sum(1 for l in today_trades if "SELL" in l)
        scores = []
        for l in today_trades:
            try: scores.append(int(l.split("|")[3].replace("%","").strip()))
            except: pass
        avg_score = round(sum(scores)/len(scores), 1) if scores else 0
        report = f"📋 التقرير اليومي {today}\n━━━━━━━━━━━━━━━━\n📊 {total} إشارة | 🟢 {buy} | 🔴 {sell}\n🤖 متوسط الثقة: {avg_score}%"
        send(report)
    except:
        send("📋 لا توجد إشارات اليوم")

def calc_fibonacci(highs, lows, direction):
    """
    يحسب مستويات فيبوناتشي تلقائياً
    """
    if direction == "DOWN":
        swing_high = max(highs[-50:])
        swing_low  = min(lows[-10:])
    else:
        swing_low  = min(lows[-50:])
        swing_high = max(highs[-10:])

    diff = swing_high - swing_low

    levels = {
        "0.236": round(swing_high - diff * 0.236, 2),
        "0.382": round(swing_high - diff * 0.382, 2),
        "0.500": round(swing_high - diff * 0.500, 2),
        "0.618": round(swing_high - diff * 0.618, 2),
        "0.786": round(swing_high - diff * 0.786, 2),
    }

    return levels, round(swing_high, 2), round(swing_low, 2)

def get_nearest_fib(price, fib_levels, atr):
    """
    يجد أقرب مستوى فيبوناتشي للسعر الحالي
    """
    nearest = None
    min_dist = float('inf')
    for level, value in fib_levels.items():
        dist = abs(price - value)
        if dist < min_dist:
            min_dist = dist
            nearest = (level, value)

    near = min_dist < atr * 1.5
    return nearest, round(min_dist, 2), near

def liquidity_engine(highs, lows, closes, atr):
    """
    يكتشف مناطق السيولة المخفية
    Equal Highs/Lows + Stop Hunt
    """
    signals = []
    score = 0

    # Equal Highs - سيولة فوق
    recent_highs = highs[-20:]
    max_high = max(recent_highs)
    equal_highs = sum(1 for h in recent_highs if abs(h - max_high) < atr * 0.3)
    if equal_highs >= 2:
        signals.append(f"🔴 سيولة فوق {round(max_high,1)} (Equal Highs)")
        score += 30

    # Equal Lows - سيولة تحت
    recent_lows = lows[-20:]
    min_low = min(recent_lows)
    equal_lows = sum(1 for l in recent_lows if abs(l - min_low) < atr * 0.3)
    if equal_lows >= 2:
        signals.append(f"🟢 سيولة تحت {round(min_low,1)} (Equal Lows)")
        score += 30

    # Stop Hunt Detection
    price = closes[-1]
    prev_high = max(highs[-5:-1])
    prev_low  = min(lows[-5:-1])

    if highs[-1] > prev_high and closes[-1] < prev_high:
        signals.append("⚡ Stop Hunt صاعد — كسر وهمي فوق!")
        score += 40

    if lows[-1] < prev_low and closes[-1] > prev_low:
        signals.append("⚡ Stop Hunt هابط — كسر وهمي تحت!")
        score += 40

    # Liquidity Grab
    near_high = abs(price - max_high) < atr * 0.5
    near_low  = abs(price - min_low) < atr * 0.5

    if near_high:
        signals.append(f"⚠️ السعر قرب سيولة فوق ({round(max_high,1)})")
        score += 20
    if near_low:
        signals.append(f"⚠️ السعر قرب سيولة تحت ({round(min_low,1)})")
        score += 20

    has_liquidity = score >= 30
    return has_liquidity, score, signals, round(max_high,1), round(min_low,1)

def detect_compression(closes, highs, lows, atr_current):
    """
    يكتشف مرحلة الضغط قبل الانفجار
    """
    # ATR Compression
    atr_old = sum([max(highs[i]-lows[i], abs(highs[i]-closes[i-1]),
                  abs(lows[i]-closes[i-1])) for i in range(-20,-5)]) / 15
    atr_new = sum([max(highs[i]-lows[i], abs(highs[i]-closes[i-1]),
                  abs(lows[i]-closes[i-1])) for i in range(-5,-1)]) / 4

    atr_ratio = round(atr_new / atr_old, 2) if atr_old > 0 else 1

    # Range Compression
    recent_high = max(highs[-10:])
    recent_low  = min(lows[-10:])
    range_size  = recent_high - recent_low

    signals = []
    score = 0

    if atr_ratio < 0.7:
        signals.append("ATR ينخفض — ضغط قوي 🔵")
        score += 40
    elif atr_ratio < 0.85:
        signals.append("ATR يتراجع — ضغط متوسط 🔵")
        score += 20

    if range_size < atr_current * 2:
        signals.append("نطاق ضيق — استعداد 🔵")
        score += 30

    is_compressing = score >= 40
    return is_compressing, score, signals, atr_ratio

def get_positive_triggers(s4, s1, s15, adx4, adx1, adx15,
                          rsi_1h, hour_utc, is_compressing):
    triggers = []

    if adx4 >= 25:
        triggers.append("ترند رئيسي واضح ✅")
    if adx1 >= 20 and adx1 > adx15:
        triggers.append("زخم يتطور على 1H ✅")
    if adx15 >= 20:
        triggers.append("زخم يتطور على 15M ✅")
    if 13 <= hour_utc <= 17:
        triggers.append("جلسة تداخل مثالية 🔥")
    elif 8 <= hour_utc <= 22:
        triggers.append("جلسة جيدة ✅")
    if is_compressing:
        triggers.append("السوق يستعد للانفجار 🔵")
    if 35 <= rsi_1h <= 65:
        triggers.append("RSI في المنطقة المثالية ✅")

    return triggers

def calc_pullback_engine(closes, highs, lows, bias_4h, rsi_1h, adx4):
    """
    يكتشف متى ينتهي الـ Pullback ويبدأ الدخول
    """
    ma20 = sum(closes[-20:]) / 20
    ma50 = sum(closes[-50:]) / 50
    price = closes[-1]

    signals = []
    score = 0

    # السعر وصل للمتوسط المتحرك
    if bias_4h == "BEARISH":
        if price >= ma20 * 0.998:
            signals.append("السعر عند MA20 ✅")
            score += 30
        if rsi_1h >= 45 and rsi_1h <= 60:
            signals.append("RSI تعافى للمنتصف ✅")
            score += 30
        if adx4 >= 25:
            signals.append("ترند رئيسي قوي ✅")
            score += 20
        # شمعة رفض
        last_candle = closes[-1] - closes[-2]
        if last_candle < 0:
            signals.append("شمعة هبوط تأكيد ✅")
            score += 20

    elif bias_4h == "BULLISH":
        if price <= ma20 * 1.002:
            signals.append("السعر عند MA20 ✅")
            score += 30
        if rsi_1h >= 40 and rsi_1h <= 55:
            signals.append("RSI تعافى للمنتصف ✅")
            score += 30
        if adx4 >= 25:
            signals.append("ترند رئيسي قوي ✅")
            score += 20
        last_candle = closes[-1] - closes[-2]
        if last_candle > 0:
            signals.append("شمعة صعود تأكيد ✅")
            score += 20

    ready = score >= 60
    return ready, score, signals

def send_recommendation(direction, price, sl, adx, confidence, rsi, reasons):
    try:
        from recommendation import generate_recommendation
        msg = generate_recommendation(
            direction=direction, price=price, sl=sl,
            atr=0, adx=adx, confidence=confidence,
            rsi=rsi, reasons=reasons)
        send(msg)
    except Exception as e:
        print(f"خطأ توصية: {e}")

def analyze_tf(interval, outputsize=100):
    closes, highs, lows = get_data(interval, outputsize)
    rsi        = calc_rsi(closes)  # مصلح
    ma20       = calc_ma(closes, 20)
    ma50       = calc_ma(closes, 50)
    macd, msig = calc_macd(closes)
    atr        = calc_atr(highs, lows, closes)
    support, resistance = calc_support_resistance(highs, lows)
    state, state_type, adx, strength = market_state(highs, lows, closes)
    adx_val, plus_di, minus_di = calc_adx(highs, lows, closes)
    structure, bias = smart_structure(highs, lows, adx_val, plus_di, minus_di)
    trend = "UP" if ma20 > ma50 else "DOWN"
    price = closes[-1]
    rsi_sig = smart_rsi_signal(rsi, adx_val, trend)

    # Exhaustion Check
    is_exhausted, exh_reasons = exhaustion_check(adx_val, rsi, trend)

    if state_type == "BLOCK":
        sig = "BLOCK"
    elif is_exhausted:
        sig = "EXHAUSTED"
    elif rsi_sig in ["BUY","SELL"]:
        sig = rsi_sig
    elif adx_val >= 40 and bias == "BEARISH" and trend == "DOWN":
        sig = "SELL"
    elif adx_val >= 40 and bias == "BULLISH" and trend == "UP":
        sig = "BUY"
    else:
        sig = "NEUTRAL"

    return sig, rsi, trend, macd, msig, atr, support, resistance, structure, bias, state, state_type, adx, strength, is_exhausted, exh_reasons

def analyze(is_hourly=True):
    global last_signal, last_report_date
    try:
        now_utc   = datetime.now(timezone.utc)
        local_now = datetime.now()

        if local_now.hour == 8 and local_now.strftime('%Y-%m-%d') != last_report_date:
            send_daily_report()
            last_report_date = local_now.strftime('%Y-%m-%d')

        hour_utc = now_utc.hour
        weekday  = now_utc.weekday()
        # السوق يفتح الأحد مساءً (UTC 21:00)
        if weekday == 6:  # الأحد
            pass  # السوق مفتوح
        elif weekday == 5:  # السبت
            print("🔴 عطلة"); return

        time_msg, session_score = get_session(hour_utc)
        in_kill_zone, kz_msg = is_kill_zone(hour_utc)
        if in_kill_zone:
            session_score = min(session_score + 5, 15)

        s4,  r4,  t4,  m4,  ms4,  atr4,  sup4,  res4,  str4,  b4,  st4,  stype4,  adx4,  str4_,  exh4,  exhr4  = analyze_tf("4h")
        time.sleep(12)
        s1,  r1,  t1,  m1,  ms1,  atr1,  sup1,  res1,  str1,  b1,  st1,  stype1,  adx1,  str1_,  exh1,  exhr1  = analyze_tf("1h")
        time.sleep(12)
        s15, r15, t15, m15, ms15, atr15, sup15, res15, str15, b15, st15, stype15, adx15, str15_, exh15, exhr15 = analyze_tf("15min")

        price_data, _, _ = get_data("5min", 2)
        # السعر اللحظي الدقيق
        try:
            td_live = requests.get("https://api.twelvedata.com/price",
                params={"symbol":"XAU/USD","apikey":"6e9a8257a2d04b80b56b022707232bff"},
                timeout=10).json()
            if 'price' in td_live:
                df_live.columns = [c[0] for c in df_live.columns]
                price = round(float(df_live["Close"].iloc[-1]), 2)
            else:
                price = round(float(price_data[-1]), 2)
        except:
            price = round(float(price_data[-1]), 2)

        is_pullback, pullback_msg = detect_pullback(b4, b15)
        news_danger, news_impact, news_msg = check_news()

        bos_text = "⚪ BOS/CHoCH: لا يوجد\n"

        signals      = [s4, s1, s15]
        buy_count    = signals.count("BUY")
        sell_count   = signals.count("SELL")
        block_count  = signals.count("BLOCK")
        exh_count    = signals.count("EXHAUSTED")
        atr = atr1
        sl = tp = lots = 0
        confidence = 0
        grade = "❌"
        reasons = []
        blocks = []

        # Reason Engine
        direction_check = "BUY" if buy_count >= sell_count else "SELL"
        is_exhausted_main = exh4 or exh1
        exh_reasons_main = exhr4 + exhr1

        pos_reasons, neg_blocks = build_reason_engine(
            direction_check, adx4, r1, b4, b1,
            is_pullback, is_exhausted_main, exh_reasons_main,
            news_impact, hour_utc, 0)

        # Fibonacci Engine
        fib_data, fib_highs, fib_lows = get_data("4h", 60)
        fib_direction = "DOWN" if b4 == "BEARISH" else "UP"
        fib_levels, fib_high, fib_low = calc_fibonacci(fib_highs, fib_lows, fib_direction)
        nearest_fib, fib_dist, near_fib = get_nearest_fib(price_data[-1], fib_levels, atr1)

        # Session Manipulation
        manip_msg, manip_score, manip_type = get_manipulation_summary(
            highs1, lows1, closes1, hour_utc)

        # Volume Engine
        vol_msg, vol_score, vol_ratio = get_volume_summary(closes1, highs1, lows1)

        # Liquidity Engine
        liq_data, liq_highs, liq_lows = get_data("1h", 50)
        has_liq, liq_score, liq_signals, liq_high, liq_low = liquidity_engine(
            liq_highs, liq_lows, liq_data, atr1)

        # Compression Detection
        price_list, highs_list, lows_list = get_data("1h", 30)
        bos_r = detect_bos_choch(price_list, highs_list, lows_list)
        ob_signals, obs = ob_signal(price_list, highs_list, lows_list, atr1)
        ob_text = " | ".join(ob_signals) if ob_signals else "⚪ لا OB قريب"
        # كشف أنماط الشموع
        try:
            closes_c, highs_c, lows_c, opens_1h = get_data("1h", 30)
            candle_text, candle_dir, candle_strength = candle_signal(opens_1h, highs_list, lows_list, price_list, atr1)
        except:
            candle_text, candle_dir, candle_strength = "⚪ لا نمط واضح", "NEUTRAL", 0

        # Candle يرفع Confluence
        if candle_dir == "BUY":
            cf_buy += candle_strength // 5
        elif candle_dir == "SELL":
            cf_sell += candle_strength // 5

        cf_dir, cf_conf, cf_buy, cf_sell, cf_reasons = calc_confluence(
            s4, s1, s15, adx4, adx1, adx15,
            r4, r1, r15, bos_text, ob_text,
            near_fib, has_liq, is_pullback,
            session_score, news_impact)
        bos_text = ""
        if bos_r["BOS"]:
            d, l = bos_r["BOS"]
            arrow = "📈" if d == "UP" else "📉"
            bos_text += f"{arrow} BOS {d}: {l}\n"
        if bos_r["CHoCH"]:
            d, l = bos_r["CHoCH"]
            arrow = "🔄📈" if d == "BULLISH" else "🔄📉"
            bos_text += f"{arrow} CHoCH {d}: {l}\n"
        if not bos_text:
            bos_text = "⚪ BOS/CHoCH: لا يوجد\n"
        is_compressing, comp_score, comp_signals, atr_ratio = detect_compression(
            price_list, highs_list, lows_list, atr1)

        # Positive Triggers
        pos_triggers = get_positive_triggers(
            s4, s1, s15, adx4, adx1, adx15,
            r1, hour_utc, is_compressing)

        # البونص يُحسب بعد quality_score
        bonus = 0
        if near_fib: bonus += 10
        if has_liq:  bonus += 10
        cf_bonus = 0
        if cf_buy > cf_sell and cf_buy >= 40:
            cf_bonus = min(round(cf_buy * 0.3), 25)
        elif cf_sell > cf_buy and cf_sell >= 40:
            cf_bonus = min(round(cf_sell * 0.3), 25)

        if news_danger:
            final = "⛔ NO TRADE"
            detail = "أخبار خطرة"
            blocks = ["أخبار عالية التأثير⛔"]
        elif block_count >= 2:
            final = "⛔ NO TRADE"
            detail = "سوق متقلب جداً"
            blocks = ["تقلب عالي⛔"]
        elif exh_count >= 2 or is_exhausted_main:
            # Pullback Engine
            pb_ready, pb_score, pb_signals = calc_pullback_engine(
                price_data, [], [], b4, r1, adx4)
            if pb_ready:
                final = "🔄 PULLBACK ENTRY"
                detail = "Pullback انتهى — فرصة دخول! " + " | ".join(pb_signals[:2])
            else:
                final = "⏳ WAIT"
                detail = "انتظر Pullback " + str(pb_score) + "% | " + (" | ".join(pb_signals[:2]) if pb_signals else "السوق مرهق")
            blocks = exh_reasons_main
        elif buy_count >= 2 and "DOWN" not in st4 and "EXTREME DOWN" not in st4 and r1 < 65 and session_score >= 7:
            confidence, grade, reasons = quality_score(
                "BUY", adx4, adx1, b4, b1, r1, r15,
                m1, ms1, news_impact, is_pullback,
                hour_utc, is_exhausted_main)
            confidence = min(confidence + bonus + cf_bonus, 100)
            sl, tp, rr = calc_sl_tp("BUY", price, atr, adx4)
            lots = calc_position_size(BALANCE, RISK_PERCENT, price, sl)
            risk_usd = round(BALANCE*RISK_PERCENT/100, 2)
            if confidence >= 80:
                final = "🟢 BUY قوي 🔥"
                detail = f"""🛑 SL: {sl}
🥇 TP1: {round(price + abs(price-tp)*0.4, 2) if "BUY" in final else round(price - abs(price-tp)*0.4, 2)} → أغلق 40%
🥈 TP2: {round(price + abs(price-tp)*0.7, 2) if "BUY" in final else round(price - abs(price-tp)*0.7, 2)} → أغلق 40%
🥉 TP3: {tp} → أغلق 20%
⚠️ بعد TP1 → حرك SL للدخول
💼 حجم: {lots} | خطر: ${risk_usd}"""
            elif confidence >= 65:
                final = "🟢 BUY جيد"
                detail = f"""🛑 SL: {sl}
🥇 TP1: {round(price + abs(price-tp)*0.4, 2) if "BUY" in final else round(price - abs(price-tp)*0.4, 2)} → أغلق 40%
🥈 TP2: {round(price + abs(price-tp)*0.7, 2) if "BUY" in final else round(price - abs(price-tp)*0.7, 2)} → أغلق 40%
🥉 TP3: {tp} → أغلق 20%
⚠️ بعد TP1 → حرك SL للدخول
💼 حجم: {lots} | خطر: ${risk_usd}"""
            elif confidence >= 50:
                final = "🟡 BUY مقبول"
                detail = f"SL: {sl} | TP: {tp} | راقب"
            else:
                final = "⚪ NO TRADE"
                detail = f"جودة منخفضة ({confidence}%)"
                sl = tp = 0
        elif sell_count >= 2 and session_score >= 7 and r1 > 35:
            confidence, grade, reasons = quality_score(
                "SELL", adx4, adx1, b4, b1, r1, r15,
                m1, ms1, news_impact, is_pullback,
                hour_utc, is_exhausted_main)
            sl, tp, rr = calc_sl_tp("SELL", price, atr, adx4)
            lots = calc_position_size(BALANCE, RISK_PERCENT, price, sl)
            risk_usd = round(BALANCE*RISK_PERCENT/100, 2)
            if confidence >= 80:
                final = "🔴 SELL قوي 🔥"
                detail = f"""🛑 SL: {sl}
🥇 TP1: {round(price + abs(price-tp)*0.4, 2) if "BUY" in final else round(price - abs(price-tp)*0.4, 2)} → أغلق 40%
🥈 TP2: {round(price + abs(price-tp)*0.7, 2) if "BUY" in final else round(price - abs(price-tp)*0.7, 2)} → أغلق 40%
🥉 TP3: {tp} → أغلق 20%
⚠️ بعد TP1 → حرك SL للدخول
💼 حجم: {lots} | خطر: ${risk_usd}"""
            elif confidence >= 65:
                final = "🔴 SELL جيد"
                detail = f"""🛑 SL: {sl}
🥇 TP1: {round(price + abs(price-tp)*0.4, 2) if "BUY" in final else round(price - abs(price-tp)*0.4, 2)} → أغلق 40%
🥈 TP2: {round(price + abs(price-tp)*0.7, 2) if "BUY" in final else round(price - abs(price-tp)*0.7, 2)} → أغلق 40%
🥉 TP3: {tp} → أغلق 20%
⚠️ بعد TP1 → حرك SL للدخول
💼 حجم: {lots} | خطر: ${risk_usd}"""
            elif confidence >= 50:
                final = "🟡 SELL مقبول"
                detail = f"SL: {sl} | TP: {tp} | راقب"
            else:
                final = "⚪ NO TRADE"
                detail = f"جودة منخفضة ({confidence}%)"
                sl = tp = 0
        else:
            confidence, grade, reasons = quality_score(
                "BUY", adx4, adx1, b4, b1, r1, r15,
                m1, ms1, news_impact, is_pullback,
                hour_utc, is_exhausted_main)
            confidence = min(confidence + bonus + cf_bonus, 100)
            if is_compressing and adx4 >= 25:
                final = "🔵 PREPARING"
                detail = "السوق يستعد — " + " | ".join(comp_signals[:2])
            else:
                final = "⚪ NO TRADE"
                detail = " | ".join(neg_blocks) if neg_blocks else "الإطارات غير متوافقة"

        # تحديث grade بعد البونص
        if confidence >= 80:   grade = "🔥 ممتاز"
        elif confidence >= 65: grade = "✅ جيد"
        elif confidence >= 50: grade = "⚠️ مقبول"
        else:                  grade = "❌ ضعيف"

        confidence, ai_note = ai_boost(confidence, final, adx4, r1)
        if sl != 0:
            save_journal(final, price, confidence, sl, tp, lots, reasons)
            import os
            if "BUY" in final and not os.path.exists("active_trade.json"):
                save_trade("BUY", price, sl, tp)
                send_trade_buttons(CHAT_ID, "BUY", price, sl, tp)
            elif "SELL" in final and not os.path.exists("active_trade.json"):
                save_trade("SELL", price, sl, tp)
                send_trade_buttons(CHAT_ID, "SELL", price, sl, tp)

        is_strong     = "🔥" in final
        is_new_signal = final != last_signal
        if is_strong and is_new_signal:
            send(f"🚨 تنبيه!\n{final}\n💰 {price}\n📊 {confidence}%\n📌 {detail}")
            last_signal = final

        # Market Quality vs Entry Quality
        def calc_market_quality(adx4, bias_4h, bias_1h, news_impact):
            mq = 0
            if adx4 >= 40: mq += 35
            elif adx4 >= 25: mq += 25
            if bias_4h in ["BULLISH","BEARISH"]: mq += 25
            if bias_1h in ["BULLISH","BEARISH"]: mq += 20
            if news_impact <= 3: mq += 20
            return min(mq, 100)

        def calc_entry_quality(rsi, hour_utc, is_exhausted, is_pullback, adx4):
            eq = 50
            if is_exhausted: eq -= 30
            if is_pullback: eq -= 20
            if hour_utc < 8: eq -= 15
            if adx4 > 90: eq -= 20
            if 13 <= hour_utc <= 17: eq += 20
            elif 8 <= hour_utc <= 22: eq += 10
            return max(min(eq, 100), 0)

        mq = calc_market_quality(adx4, b4, b1, news_impact)
        eq = calc_entry_quality(r1, hour_utc, is_exhausted_main, is_pullback, adx4)

        stars = "⭐" * min(int(confidence/20), 5)
        reasons_text  = " | ".join(reasons[:3])  if reasons  else "تحليل جارٍ"
        blocks_text   = " | ".join(neg_blocks[:2]) if neg_blocks else "لا موانع"
        pullback_line = f"\n⚠️ {pullback_msg}" if is_pullback else ""
        exh_line      = f"\n⚠️ إرهاق: {' | '.join(exh_reasons_main[:2])}" if is_exhausted_main else ""

        narrative = build_narrative(
            s4, s1, s15, adx4, adx1, adx15,
            r4, r1, r15, str4, str1, str15,
            final, bos_text, ob_text, near_fib,
            is_pullback, news_danger, session_score,
            confidence)
        msg = f"""🥇 XAUUSD | {price}
⏰ {time_msg} | 🕐 {local_now.strftime('%H:%M')}
━━━━━━━━━━━━━━━━
💰 السعر: {price} | ATR: {atr}
🔴 مقاومة: {res1} | 🟢 دعم: {sup1}
💧 سيولة ↑{liq_high} | ↓{liq_low}
📐 فيبوناتشي {nearest_fib[0] if nearest_fib else "N/A"} → {nearest_fib[1] if nearest_fib else "N/A"} {"✅ قريب" if near_fib else ""}
━━━━━━━━━━━━━━━━
4H  {st4} | ADX:{adx4} {str4_} | RSI:{r4}
1H  {st1} | ADX:{adx1} {str1_} | RSI:{r1}
15M {st15} | ADX:{adx15} {str15_} | RSI:{r15}
━━━━━━━━━━━━━━━━
{bos_text}🔲 OB: {ob_text}
🎭 تلاعب: {manip_msg}
📊 زخم: {vol_msg}
🕯 {candle_text} | 📰 {news_msg}
━━━━━━━━━━━━━━━━
🔀 BUY: {cf_buy} | SELL: {cf_sell}
🤖 Score: {confidence}% {grade}
━━━━━━━━━━━━━━━━
🎯 {final}
🧠 {detail}
━━━━━━━━━━━━━━━━
📝 {narrative}
━━━━━━━━━━━━━━━━"""

        if is_hourly:
            try:
                ai_analysis = get_ai_analysis(
                price, atr, s4, s1, s15, adx4, adx1, adx15,
                r4, r1, r15, str4, final, confidence,
                news_msg, time_msg, 
                str(nearest_fib) if nearest_fib else "N/A",
                bos_text, ob_text)
            except:
                ai_analysis = narrative
            msg += f"""
"""
            print(msg)
            send(msg)
            if sl != 0 and confidence >= 65:
                direction_str = "BUY" if "BUY" in final else "SELL"
                send_recommendation(direction_str, price, sl, adx4, confidence, r1, reasons)
        else:
            print(f"✅ {final} | {confidence}% | {local_now.strftime('%H:%M')}")

    except Exception as e:
        print(f"خطأ: {e}")
        send(f"⚠️ خطأ: {str(e)}")

send("🚀 النظام v7.0 | Confluence + OB + Candles + Narrative | جاهز للتداول!")
last_report_date = ""
cycle = 0
# ═══════════════════════════════
# BOS / CHoCH
# ═══════════════════════════════
def find_swing_points(prices, highs, lows, window=5):
    sh, sl = [], []
    for i in range(window, len(highs)-window):
        if highs[i] == max(highs[i-window:i+window+1]):
            sh.append((i, highs[i]))
    for i in range(window, len(lows)-window):
        if lows[i] == min(lows[i-window:i+window+1]):
            sl.append((i, lows[i]))
    return sh, sl

def detect_bos_choch(prices, highs, lows, window=5):
    result = {"BOS": None, "CHoCH": None}
    sh, sl = find_swing_points(prices, highs, lows, window)
    if len(sh) < 2 or len(sl) < 2:
        return result
    last_price = prices[-1]
    h1_i, h1 = sh[-2]; h2_i, h2 = sh[-1]
    l1_i, l1 = sl[-2]; l2_i, l2 = sl[-1]
    if last_price > h1 and h2 > h1:
        result["BOS"] = ("UP", round(float(h1), 2))
    elif last_price < l1 and l2 < l1:
        result["BOS"] = ("DOWN", round(float(l1), 2))
    if h2 > h1 and l2 < l1:
        result["CHoCH"] = ("BEARISH", round(float(l1), 2))
    elif l2 > l1 and h2 < h1:
        result["CHoCH"] = ("BULLISH", round(float(h1), 2))
    return result

while True:
    is_hourly = (cycle % 4 == 0)
    analyze(is_hourly=is_hourly)
    cycle += 1
    print(f"⏳ 15 دقيقة... (دورة {cycle})")
    time.sleep(900)


