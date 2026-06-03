def generate_recommendation(direction, price, sl, atr, adx, confidence, rsi, reasons):
    
    # حساب المسافة الكاملة
    sl_distance = abs(price - sl)
    
    # 3 أهداف بناءً على RR
    if direction == "BUY":
        tp1 = round(price + sl_distance * 1.0, 2)  # RR 1:1
        tp2 = round(price + sl_distance * 2.0, 2)  # RR 1:2
        tp3 = round(price + sl_distance * 3.0, 2)  # RR 1:3
        arrow = "📈"
    else:
        tp1 = round(price - sl_distance * 1.0, 2)  # RR 1:1
        tp2 = round(price - sl_distance * 2.0, 2)  # RR 1:2
        tp3 = round(price - sl_distance * 3.0, 2)  # RR 1:3
        arrow = "📉"

    # نقاط كل هدف
    pts1 = round(abs(price - tp1), 1)
    pts2 = round(abs(price - tp2), 1)
    pts3 = round(abs(price - tp3), 1)
    sl_pts = round(sl_distance, 1)

    # قوة الإشارة
    if confidence >= 80:
        strength = "🔥 قوية جداً"
        risk_advice = "يمكن الدخول بثقة"
    elif confidence >= 65:
        strength = "✅ جيدة"
        risk_advice = "دخول مع إدارة مخاطرة"
    else:
        strength = "⚠️ متوسطة"
        risk_advice = "انتظر تأكيداً أقوى"

    # توزيع الربح
    msg = f"""
╔══════════════════════╗
      🎯 توصية تداول
      XAUUSD {arrow}
╚══════════════════════╝

📍 الاتجاه  : {'🟢 شراء BUY' if direction=='BUY' else '🔴 بيع SELL'}
💰 السعر   : {price}
━━━━━━━━━━━━━━━━━━━━━━

🛑 وقف الخسارة
   SL: {sl} ({sl_pts} نقطة)

━━━━━━━━━━━━━━━━━━━━━━
🎯 الأهداف:

   🥇 TP1: {tp1}
      +{pts1} نقطة | RR 1:1
      → أغلق 40% من الصفقة

   🥈 TP2: {tp2}
      +{pts2} نقطة | RR 1:2
      → أغلق 40% من الصفقة

   🥉 TP3: {tp3}
      +{pts3} نقطة | RR 1:3
      → أغلق 20% المتبقية

━━━━━━━━━━━━━━━━━━━━━━
📊 تفاصيل التحليل:
   ADX    : {adx} ({('💪 ترند عنيف' if adx>=40 else '⚡ ترند قوي' if adx>=25 else '😴 ضعيف')})
   RSI    : {rsi}
   الثقة : {confidence}% {strength}

💡 الأسباب:
   {chr(10).join(['• '+r for r in reasons[:4]])}

━━━━━━━━━━━━━━━━━━━━━━
⚠️  إدارة المخاطرة:
   • خاطر 1% فقط من رأس المال
   • {risk_advice}
   • بعد TP1 → حرك SL للدخول

━━━━━━━━━━━━━━━━━━━━━━
🤖 نظام التداول الآلي v3.2"""

    return msg

# اختبار