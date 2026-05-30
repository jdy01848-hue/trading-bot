import requests
import time

TD_KEY = "6e9a8257a2d04b80b56b022707232bff"

def get_session_data():
    """يجلب بيانات الجلسات الثلاث"""
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": "XAU/USD", "interval": "1h",
              "outputsize": 50, "apikey": TD_KEY}
    r = requests.get(url, params=params, timeout=15)
    data = r.json()
    if 'values' not in data:
        return None
    return list(reversed(data['values']))

def detect_session_manipulation(highs, lows, closes, hour_utc):
    """
    يكتشف فخاخ المؤسسات بين الجلسات
    """
    signals = []
    score   = 0
    manipulation_type = None

    if len(highs) < 20:
        return "لا بيانات كافية", 0, None

    # قمم وقيعان آسيا (0-8 UTC = أول 8 شموع)
    asia_highs = highs[:8]
    asia_lows  = lows[:8]
    asia_high  = max(asia_highs) if asia_highs else 0
    asia_low   = min(asia_lows)  if asia_lows  else 0

    # السعر الحالي
    current = closes[-1]
    prev    = closes[-2] if len(closes) > 1 else current

    # 1. London Liquidity Grab
    # لندن تكسر قمة آسيا ثم ترجع
    if 8 <= hour_utc <= 12:
        if prev > asia_high and current < asia_high:
            signals.append("🎯 London Sweep صاعد — كسر قمة آسيا ثم انعكاس!")
            signals.append("⚡ فرصة SELL قوية — المؤسسات اصطادت الوقفات فوق")
            score += 80
            manipulation_type = "SELL_AFTER_SWEEP"

        elif prev < asia_low and current > asia_low:
            signals.append("🎯 London Sweep هابط — كسر قاع آسيا ثم انعكاس!")
            signals.append("⚡ فرصة BUY قوية — المؤسسات اصطادت الوقفات تحت")
            score += 80
            manipulation_type = "BUY_AFTER_SWEEP"

    # 2. New York Reversal
    # نيويورك تعكس اتجاه لندن
    if 13 <= hour_utc <= 16:
        london_move = closes[-4] - closes[-8] if len(closes) >= 8 else 0
        ny_move     = closes[-1] - closes[-4] if len(closes) >= 4 else 0

        if london_move > 0 and ny_move < -london_move * 0.5:
            signals.append("🔄 NY يعكس لندن — SELL محتمل")
            score += 50
            manipulation_type = "NY_REVERSAL_SELL"

        elif london_move < 0 and ny_move > abs(london_move) * 0.5:
            signals.append("🔄 NY يعكس لندن — BUY محتمل")
            score += 50
            manipulation_type = "NY_REVERSAL_BUY"

    # 3. Stop Hunt Detection
    # حركة سريعة ثم رجوع
    recent_range = max(highs[-5:]) - min(lows[-5:])
    last_candle  = abs(closes[-1] - closes[-2]) if len(closes) > 1 else 0

    if last_candle > recent_range * 0.6:
        signals.append("⚠️ حركة عنيفة مفاجئة — احذر Stop Hunt")
        score += 20

    # 4. False Breakout
    resistance = max(highs[-20:])
    support    = min(lows[-20:])

    if closes[-2] > resistance and closes[-1] < resistance:
        signals.append("🚨 Fake Breakout صاعد — كسر وهمي للمقاومة!")
        score += 60
        manipulation_type = manipulation_type or "FAKE_BREAK_SELL"

    elif closes[-2] < support and closes[-1] > support:
        signals.append("🚨 Fake Breakout هابط — كسر وهمي للدعم!")
        score += 60
        manipulation_type = manipulation_type or "FAKE_BREAK_BUY"

    score = min(score, 100)

    if not signals:
        signals.append("✅ لا تلاعب مكتشف")

    return " | ".join(signals[:2]), score, manipulation_type

def get_manipulation_summary(highs, lows, closes, hour_utc):
    try:
        msg, score, mtype = detect_session_manipulation(
            highs, lows, closes, hour_utc)
        return msg, score, mtype
    except Exception as e:
        return "✅ لا تلاعب", 0, None

print("✅ Session Manipulation Engine جاهز")

if __name__ == "__main__":
    test_closes = [4500+i*0.5 for i in range(30)]
    test_highs  = [x+15 for x in test_closes]
    test_lows   = [x-15 for x in test_closes]
    msg, score, mtype = get_manipulation_summary(
        test_highs, test_lows, test_closes, 10)
    print(f"النتيجة: {msg}")
    print(f"Score: {score}%")
    print(f"النوع: {mtype}")
