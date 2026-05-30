def find_swing_points(prices, highs, lows, window=5):
    swing_highs, swing_lows = [], []
    for i in range(window, len(highs)-window):
        if highs[i] == max(highs[i-window:i+window+1]):
            swing_highs.append((i, highs[i]))
    for i in range(window, len(lows)-window):
        if lows[i] == min(lows[i-window:i+window+1]):
            swing_lows.append((i, lows[i]))
    return swing_highs, swing_lows

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
