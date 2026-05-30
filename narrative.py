def build_narrative(s4, s1, s15, adx4, adx1, adx15,
                    r4, r1, r15, str4, str1, str15,
                    final, bos_text, ob_text, near_fib,
                    is_pullback, news_danger, session_score,
                    confidence):

    lines = []

    # 1. وصف الوضع الحالي
    if "TRENDING UP" in s4 and "TRENDING UP" in s1:
        lines.append("الاتجاه صاعد ومتوافق على 4H و1H — بيئة مناسبة للشراء.")
    elif "TRENDING UP" in s4 and "RANGING" in s1:
        lines.append("الاتجاه الرئيسي صاعد على 4H لكن 1H في رنج — السوق يستعد.")
    elif "TRENDING UP" in s4 and "DOWN" in s15:
        lines.append("الاتجاه الرئيسي صاعد على 4H لكن 15M في تراجع — Pullback محتمل.")
    elif "TRENDING DOWN" in s4 and "TRENDING DOWN" in s1:
        lines.append("الاتجاه هابط ومتوافق على 4H و1H — بيئة مناسبة للبيع.")
    elif "RANGING" in s4 and "RANGING" in s1:
        lines.append("السوق في رنج على جميع الأطر — لا اتجاه واضح حالياً.")
    else:
        lines.append("السوق في حالة مختلطة — لا اتجاه واضح على الأطر الزمنية.")

    # 2. تحليل BOS و OB
    if "لا يوجد" in bos_text and "لا OB" in ob_text:
        lines.append("لا يوجد كسر هيكل أو Order Block قريب — تأكيد الاتجاه غائب.")
    elif "BOS UP" in bos_text:
        lines.append("كسر هيكل صاعد مؤكد — إشارة قوة للمشترين.")
    elif "BOS DOWN" in bos_text:
        lines.append("كسر هيكل هابط مؤكد — إشارة قوة للبائعين.")
    if "Bullish OB" in ob_text:
        lines.append("السعر قرب منطقة طلب قوية — احتمال ارتداد صاعد.")
    elif "Bearish OB" in ob_text:
        lines.append("السعر قرب منطقة عرض قوية — احتمال ضغط هابط.")

    # 3. فيبوناتشي
    if near_fib:
        lines.append("السعر عند مستوى فيبوناتشي — نقطة دعم أو مقاومة محتملة.")

    # 4. سبب القرار
    if "BUY" in final:
        lines.append(f"القرار شراء بثقة {confidence}% بناءً على توافق الأطر والمؤشرات.")
    elif "SELL" in final:
        lines.append(f"القرار بيع بثقة {confidence}% بناءً على توافق الأطر والمؤشرات.")
    elif "PREPARING" in final:
        lines.append("السوق يستعد للتحرك — انتظر تأكيد الاتجاه على 1H قبل الدخول.")
    elif "PULLBACK" in final:
        lines.append("Pullback انتهى — فرصة دخول مع الاتجاه الرئيسي.")
    else:
        if is_pullback:
            lines.append("15M في تراجع عكس الاتجاه الرئيسي — الدخول الآن مخاطرة عالية.")
        elif session_score < 5:
            lines.append("جلسة التداول ضعيفة — انتظر جلسة لندن أو نيويورك لإشارات أقوى.")
        else:
            lines.append(f"الأطر غير متوافقة بما يكفي — Score {confidence}% دون الحد المطلوب.")

    return "\n".join(lines)

print("✅ Narrative Engine جاهز")
