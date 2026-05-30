def detect_candle_patterns(opens, highs, lows, closes, atr):
    """
    يكتشف أنماط الشموع اليابانية المهمة
    """
    patterns = []
    
    if len(closes) < 3:
        return patterns
    
    # آخر 3 شموع
    o1, h1, l1, c1 = opens[-3], highs[-3], lows[-3], closes[-3]
    o2, h2, l2, c2 = opens[-2], highs[-2], lows[-2], closes[-2]
    o3, h3, l3, c3 = opens[-1], highs[-1], lows[-1], closes[-1]
    
    body3 = abs(c3 - o3)
    body2 = abs(c2 - o2)
    body1 = abs(c1 - o1)
    
    upper_wick3 = h3 - max(c3, o3)
    lower_wick3 = min(c3, o3) - l3
    candle_range3 = h3 - l3

    # ─── صاعدة ───

    # Pin Bar صاعد (Hammer)
    if (lower_wick3 >= body3 * 2 and
        upper_wick3 <= body3 * 0.5 and
        candle_range3 > atr * 0.3):
        patterns.append(("🔨 Hammer صاعد", "BUY", 85))

    # Bullish Engulfing
    if (c2 < o2 and c3 > o3 and
        c3 > o2 and o3 < c2 and
        body3 > body2):
        patterns.append(("📈 Engulfing صاعد", "BUY", 80))

    # Morning Star
    if (c1 < o1 and
        body2 < atr * 0.3 and
        c3 > o3 and c3 > (o1 + c1) / 2):
        patterns.append(("⭐ Morning Star", "BUY", 75))

    # Bullish Doji
    if (body3 < atr * 0.1 and
        candle_range3 > atr * 0.4):
        patterns.append(("➕ Doji — تردد", "NEUTRAL", 50))

    # Tweezer Bottom
    if (abs(l2 - l3) < atr * 0.1 and
        c2 < o2 and c3 > o3):
        patterns.append(("🔧 Tweezer Bottom صاعد", "BUY", 70))

    # ─── هابطة ───

    # Shooting Star (Pin Bar هابط)
    if (upper_wick3 >= body3 * 2 and
        lower_wick3 <= body3 * 0.5 and
        candle_range3 > atr * 0.3):
        patterns.append(("💫 Shooting Star هابط", "SELL", 85))

    # Bearish Engulfing
    if (c2 > o2 and c3 < o3 and
        c3 < o2 and o3 > c2 and
        body3 > body2):
        patterns.append(("📉 Engulfing هابط", "SELL", 80))

    # Evening Star
    if (c1 > o1 and
        body2 < atr * 0.3 and
        c3 < o3 and c3 < (o1 + c1) / 2):
        patterns.append(("🌟 Evening Star", "SELL", 75))

    # Tweezer Top
    if (abs(h2 - h3) < atr * 0.1 and
        c2 > o2 and c3 < o3):
        patterns.append(("🔧 Tweezer Top هابط", "SELL", 70))

    return patterns


def candle_signal(opens, highs, lows, closes, atr):
    patterns = detect_candle_patterns(opens, highs, lows, closes, atr)
    
    if not patterns:
        return "⚪ لا نمط واضح", "NEUTRAL", 0
    
    # أقوى نمط
    best = max(patterns, key=lambda x: x[2])
    name, direction, strength = best
    
    all_names = " | ".join([p[0] for p in patterns])
    return all_names, direction, strength


print("✅ Candle Patterns جاهز")
