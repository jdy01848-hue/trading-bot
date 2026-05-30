import yfinance as yf

def run_backtest(symbol="GC=F", period="180d", interval="1h"):
    print("📊 جاري تحميل البيانات التاريخية...")
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    df.columns = [c[0] for c in df.columns]
    df = df.dropna()
    
    prices = list(df['Close'].astype(float))
    highs  = list(df['High'].astype(float))
    lows   = list(df['Low'].astype(float))
    print(f"✅ {len(prices)} شمعة جاهزة")
    
    trades = []
    i = 50
    
    while i < len(prices) - 30:
        atr = sum([highs[j]-lows[j] for j in range(i-14,i)]) / 14
        
        gains  = [max(prices[j]-prices[j-1],0) for j in range(i-14,i)]
        losses = [max(prices[j-1]-prices[j],0) for j in range(i-14,i)]
        avg_g  = sum(gains)/14
        avg_l  = sum(losses)/14
        rsi    = 100-(100/(1+avg_g/avg_l)) if avg_l>0 else 50

        dm_p = sum([max(highs[j]-highs[j-1],0) for j in range(i-13,i)])
        dm_m = sum([max(lows[j-1]-lows[j],0)  for j in range(i-13,i)])
        adx  = abs(dm_p-dm_m)/(dm_p+dm_m)*100 if (dm_p+dm_m)>0 else 0

        ma20 = sum(prices[i-20:i])/20
        ma50 = sum(prices[i-50:i])/50
        p    = prices[i]

        direction = None
        # BUY: ترند صاعد + RSI مناسب + ADX قوي + فوق MA
        if (p > ma20 > ma50 and
            30 < rsi < 60 and
            adx > 20 and
            p > prices[i-3]):
            direction = "BUY"
        # SELL: ترند هابط + RSI مناسب + ADX قوي + تحت MA
        elif (p < ma20 < ma50 and
              40 < rsi < 70 and
              adx > 20 and
              p < prices[i-3]):
            direction = "SELL"

        if direction:
            sl = round(p - atr*1.5,2) if direction=="BUY" else round(p+atr*1.5,2)
            tp = round(p + atr*3.0,2) if direction=="BUY" else round(p-atr*3.0,2)
            
            result = "OPEN"
            for j in range(i+1, min(i+72, len(prices))):
                if direction == "BUY":
                    if lows[j]  <= sl: result="LOSS"; break
                    if highs[j] >= tp: result="WIN";  break
                else:
                    if highs[j] >= sl: result="LOSS"; break
                    if lows[j]  <= tp: result="WIN";  break

            if result != "OPEN":
                trades.append({"dir":direction,"entry":p,"result":result})
            i += 15
        else:
            i += 1

    wins   = sum(1 for t in trades if t["result"]=="WIN")
    losses = sum(1 for t in trades if t["result"]=="LOSS")
    total  = wins + losses

    if total == 0:
        print("❌ لا توجد صفقات كافية")
        return

    rate = round((wins/total)*100,1)
    print(f"""
📈 نتائج Backtest ({period} | {interval})
━━━━━━━━━━━━━━━━
📊 إجمالي : {total}
✅ رابحة  : {wins}
❌ خاسرة  : {losses}
🎯 Win Rate: {rate}%
RR: 1:2 (SL=1.5 ATR | TP=3 ATR)
━━━━━━━━━━━━━━━━
{'✅ النظام مربح!' if rate>=55 else '⚠️ يحتاج تحسين' if rate>=45 else '❌ يحتاج مراجعة'}
""")

run_backtest()
