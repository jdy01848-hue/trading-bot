import requests

GEMINI_KEY = "AIzaSyDUxF6ErP21SV_RlOeZghzZqRq8_ruldJw"

def get_ai_analysis(price, atr, s4, s1, s15, adx4, adx1, adx15,
                    r4, r1, r15, structure, decision, score,
                    news_msg, session, fib_text, bos_text, ob_text):
    try:
        prompt = f"""أنت محلل تداول احترافي متخصص في الذهب XAUUSD. اكتب بالعربية الفصحى فقط بدون أي كلمة إنجليزية.

البيانات:
السعر: {price} | ATR: {atr} | الجلسة: {session}
4H: {s4} | ADX: {adx4} | RSI: {r4}
1H: {s1} | ADX: {adx1} | RSI: {r1}
15M: {s15} | ADX: {adx15} | RSI: {r15}
الهيكل: {structure} | فيبوناتشي: {fib_text}
BOS/CHoCH: {bos_text} | OB: {ob_text}
الأخبار: {news_msg} | القرار: {decision} | Score: {score}%

اكتب تحليلاً من 4 جمل فقط: ما يحدث الآن، لماذا القرار منطقي، وماذا تراقب."""

        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20
        )
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        raise Exception(str(e))

print("✅ AI Analyst (Gemini) جاهز")
