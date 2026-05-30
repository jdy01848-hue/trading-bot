def calc_confluence(s4, s1, s15, adx4, adx1, adx15,
                    r4, r1, r15, bos_text, ob_text,
                    near_fib, has_liq, is_pullback,
                    session_score, news_impact):
    
    buy_score  = 0
    sell_score = 0
    reasons_buy  = []
    reasons_sell = []

    # BOS — وزن 30
    if "BOS UP" in bos_text:
        buy_score += 30
        reasons_buy.append("كسر هيكل صاعد ✅ +30")
    elif "BOS DOWN" in bos_text:
        sell_score += 30
        reasons_sell.append("كسر هيكل هابط ✅ +30")

    # CHoCH — وزن 20
    if "CHoCH BULLISH" in bos_text:
        buy_score += 20
        reasons_buy.append("تغيير هيكل صاعد ✅ +20")
    elif "CHoCH BEARISH" in bos_text:
        sell_score += 20
        reasons_sell.append("تغيير هيكل هابط ✅ +20")

    # Order Block — وزن 20
    if "Bullish OB" in ob_text:
        buy_score += 20
        reasons_buy.append("Order Block صاعد ✅ +20")
    elif "Bearish OB" in ob_text:
        sell_score += 20
        reasons_sell.append("Order Block هابط ✅ +20")

    # Liquidity Sweep — وزن 15
    if has_liq:
        if "BUY" in bos_text or "Bullish" in ob_text:
            buy_score += 15
            reasons_buy.append("سيولة مكتشفة ✅ +15")
        else:
            sell_score += 15
            reasons_sell.append("سيولة مكتشفة ✅ +15")

    # ADX — وزن 10
    if adx4 >= 25:
        if "UP" in s4:
            buy_score += 10
            reasons_buy.append("ترند قوي 4H ✅ +10")
        elif "DOWN" in s4:
            sell_score += 10
            reasons_sell.append("ترند قوي 4H ✅ +10")

    # Session — وزن 10
    if session_score >= 7:
        buy_score  += 10
        sell_score += 10
        reasons_buy.append("جلسة قوية ✅ +10")
        reasons_sell.append("جلسة قوية ✅ +10")

    # Fibonacci — وزن 8
    if near_fib:
        buy_score  += 8
        sell_score += 8
        reasons_buy.append("فيبوناتشي قريب ✅ +8")
        reasons_sell.append("فيبوناتشي قريب ✅ +8")

    # RSI — وزن 5
    if r1 < 35:
        buy_score += 5
        reasons_buy.append("RSI oversold ✅ +5")
    elif r1 > 65:
        sell_score += 5
        reasons_sell.append("RSI overbought ✅ +5")

    # Pullback penalty
    if is_pullback:
        sell_score += 10
        reasons_sell.append("Pullback هابط ⚠️ +10")

    # News penalty
    if news_impact >= 6:
        buy_score  = max(0, buy_score  - 20)
        sell_score = max(0, sell_score - 20)

    # القرار
    total = max(buy_score, sell_score, 1)
    if buy_score > sell_score and buy_score >= 40:
        direction = "BUY"
        confidence = min(round((buy_score / 118) * 100), 95)
        top_reasons = reasons_buy[:3]
    elif sell_score > buy_score and sell_score >= 40:
        direction = "SELL"
        confidence = min(round((sell_score / 118) * 100), 95)
        top_reasons = reasons_sell[:3]
    else:
        direction = "WAIT"
        confidence = 0
        top_reasons = ["لا توافق كافٍ بين المؤشرات"]

    return direction, confidence, buy_score, sell_score, top_reasons

print("✅ Confluence Engine جاهز")
