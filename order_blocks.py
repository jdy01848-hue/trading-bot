def detect_order_blocks(prices, highs, lows, atr, lookback=100):
    result = {"bullish_ob": None, "bearish_ob": None}
    if len(prices) < 20:
        return result

    p = prices[-lookback:] if len(prices) > lookback else prices
    h = highs[-lookback:] if len(highs) > lookback else highs
    l = lows[-lookback:] if len(lows) > lookback else lows
    n = len(p)

    # Bullish OB: شمعة هابطة قبل حركة صاعدة قوية
    for i in range(n-3, 10, -1):
        if p[i] < p[i-1]:  # شمعة هابطة
            future_high = max(p[i+1:min(i+10, n)])
            move_up = future_high - p[i]
            if move_up > atr * 1.0:  # خففنا الشرط
                result["bullish_ob"] = (round(l[i], 2), round(h[i], 2))
                break

    # Bearish OB: شمعة صاعدة قبل حركة هابطة قوية
    for i in range(n-3, 10, -1):
        if p[i] > p[i-1]:  # شمعة صاعدة
            future_low = min(p[i+1:min(i+10, n)])
            move_down = p[i] - future_low
            if move_down > atr * 1.0:  # خففنا الشرط
                result["bearish_ob"] = (round(l[i], 2), round(h[i], 2))
                break

    return result

def ob_signal(prices, highs, lows, atr):
    obs = detect_order_blocks(prices, highs, lows, atr)
    price = prices[-1]
    signals = []

    if obs["bullish_ob"]:
        ob_low, ob_high = obs["bullish_ob"]
        if ob_low <= price <= ob_high:
            signals.append(f"🟢 داخل Bullish OB ({ob_low}-{ob_high})")
        elif abs(price - ob_high) < atr * 1.5:
            signals.append(f"🟢 قرب Bullish OB ({ob_low}-{ob_high})")

    if obs["bearish_ob"]:
        ob_low, ob_high = obs["bearish_ob"]
        if ob_low <= price <= ob_high:
            signals.append(f"🔴 داخل Bearish OB ({ob_low}-{ob_high})")
        elif abs(price - ob_low) < atr * 1.5:
            signals.append(f"🔴 قرب Bearish OB ({ob_low}-{ob_high})")

    return signals, obs

print("✅ Order Blocks جاهز")
