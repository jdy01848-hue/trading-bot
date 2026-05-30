import requests

TD_KEY = "6e9a8257a2d04b80b56b022707232bff"

def calc_atr_volume(highs, lows, closes, period=14):
    """
    يستخدم ATR كبديل للحجم للذهب
    ATR مرتفع = زخم وحجم عالي
    ATR منخفض = سوق خامل
    """
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i]-lows[i],
                 abs(highs[i]-closes[i-1]),
                 abs(lows[i]-closes[i-1]))
        trs.append(tr)

    if not trs:
        return 1.0, []

    atr_now = sum(trs[-period:]) / period
    atr_old = sum(trs[-period*2:-period]) / period if len(trs) >= period*2 else atr_now
    atr_ratio = round(atr_now / atr_old, 2) if atr_old > 0 else 1.0

    signals = []
    score = 0

    if atr_ratio >= 1.5:
        signals.append(f"🔥 زخم عالي جداً (ATR {atr_ratio}x)")
        score += 40
    elif atr_ratio >= 1.2:
        signals.append(f"📈 زخم مرتفع (ATR {atr_ratio}x)")
        score += 25
    elif atr_ratio >= 0.9:
        signals.append(f"📊 زخم طبيعي (ATR {atr_ratio}x)")
        score += 15
    else:
        signals.append(f"😴 زخم منخفض (ATR {atr_ratio}x)")
        score -= 10

    # ATR Expansion = بداية حركة قوية
    if atr_ratio >= 2.0:
        signals.append("⚡ توسع ATR — حركة قوية قادمة!")
        score += 20

    # ATR Compression = ضغط قبل انفجار
    if atr_ratio <= 0.6:
        signals.append("🔵 ضغط ATR — استعداد للانفجار")
        score += 15

    return atr_ratio, signals, min(score, 100)

def get_volume_data(interval="1h", outputsize=50):
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": "XAU/USD", "interval": interval,
              "outputsize": outputsize, "apikey": TD_KEY}
    r = requests.get(url, params=params, timeout=15)
    data = r.json()
    if 'values' not in data:
        return [], [], [], []
    values = list(reversed(data['values']))
    closes  = [float(x['close'])  for x in values]
    highs   = [float(x['high'])   for x in values]
    lows    = [float(x['low'])    for x in values]
    volumes = [float(x.get('volume', 0)) for x in values]
    return closes, highs, lows, volumes

def analyze_volume(closes, volumes, highs, lows):
    if not volumes or max(volumes) == 0:
        return {
            "signal": "UNKNOWN",
            "strength": 0,
            "vol_ratio": 1.0,
            "messages": ["⚠️ بيانات الحجم غير متاحة"]
        }

    signals  = []
    score    = 0

    # متوسط الحجم
    avg_vol   = sum(volumes[-20:]) / 20
    last_vol  = volumes[-1]
    vol_ratio = round(last_vol / avg_vol, 2) if avg_vol > 0 else 1

    # 1. حجم مرتفع = اهتمام مؤسسي
    if vol_ratio >= 2.0:
        signals.append(f"🔥 حجم عالي جداً ({vol_ratio}x) — مؤسسات تتحرك")
        score += 40
    elif vol_ratio >= 1.5:
        signals.append(f"📈 حجم مرتفع ({vol_ratio}x) — اهتمام قوي")
        score += 25
    elif vol_ratio >= 1.2:
        signals.append(f"📊 حجم فوق المتوسط ({vol_ratio}x)")
        score += 15
    elif vol_ratio < 0.7:
        signals.append(f"😴 حجم منخفض ({vol_ratio}x) — سوق خامل")
        score -= 20

    # 2. Volume Climax — نهاية الترند
    if vol_ratio >= 3.0:
        signals.append("⚠️ Volume Climax — قد يكون نهاية الحركة")
        score -= 15

    # 3. حجم متصاعد مع السعر = ترند قوي
    price_up  = closes[-1] > closes[-5]
    vol_up    = volumes[-1] > volumes[-5]
    if price_up and vol_up:
        signals.append("✅ حجم يؤكد الصعود")
        score += 20
    elif not price_up and vol_up:
        signals.append("✅ حجم يؤكد الهبوط")
        score += 20

    # 4. Divergence — حركة بدون حجم = وهمية
    price_move = abs(closes[-1] - closes[-5])
    atr_est    = sum([highs[i]-lows[i] for i in range(-5,-1)]) / 4
    if price_move > atr_est * 1.5 and vol_ratio < 0.8:
        signals.append("⚠️ حركة قوية بحجم ضعيف — قد تكون وهمية!")
        score -= 25

    # تقييم نهائي
    score = max(min(score, 100), 0)
    if score >= 60:
        signal = "STRONG"
    elif score >= 35:
        signal = "MODERATE"
    else:
        signal = "WEAK"

    return {
        "signal":   signal,
        "strength": score,
        "vol_ratio": vol_ratio,
        "messages": signals
    }

def get_volume_summary(closes, highs, lows):
    try:
        atr_ratio, signals, score = calc_atr_volume(highs, lows, closes)
        msg = " | ".join(signals[:2]) if signals else "📊 زخم طبيعي"
        return msg, score, atr_ratio
    except:
        return "⚠️ خطأ في الزخم", 0, 1.0

print("✅ Volume Engine جاهز")

# اختبار
if __name__ == "__main__":
    test_closes = [4500+i for i in range(50)]
    test_highs  = [x+10 for x in test_closes]
    test_lows   = [x-10 for x in test_closes]
    msg, strength, ratio = get_volume_summary(test_closes, test_highs, test_lows)
    print(f"الحجم: {msg}")
    print(f"القوة: {strength}%")
    print(f"النسبة: {ratio}x")
