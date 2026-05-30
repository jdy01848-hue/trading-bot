import requests
import json
import time
from datetime import datetime

TOKEN = "8793823731:AAG1TKA6-6SZzqc03aAV3UWnOWgrPpgZFSA"
CHAT_ID = "5902098963"
TD_KEY = "6e9a8257a2d04b80b56b022707232bff"

def send(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text},
            timeout=10)
    except:
        pass

def get_price():
    try:
        r = requests.get(
            "https://api.twelvedata.com/price",
            params={"symbol":"XAU/USD","apikey":TD_KEY},
            timeout=10)
        return float(r.json()['price'])
    except:
        return None

def get_trend_score():
    """يحسب قوة الترند الحالي"""
    try:
        r = requests.get(
            "https://api.twelvedata.com/time_series",
            params={"symbol":"XAU/USD","interval":"15min",
                    "outputsize":20,"apikey":TD_KEY},
            timeout=15)
        data = r.json()
        if 'values' not in data:
            return 50
        closes = [float(x['close']) for x in reversed(data['values'])]
        # RSI بسيط
        deltas = [closes[i]-closes[i-1] for i in range(1,len(closes))]
        gains  = [d if d>0 else 0 for d in deltas[-14:]]
        losses = [-d if d<0 else 0 for d in deltas[-14:]]
        avg_g  = sum(gains)/14
        avg_l  = sum(losses)/14
        if avg_l == 0: return 100
        rs  = avg_g/avg_l
        rsi = 100 - (100/(1+rs))
        return round(rsi, 2)
    except:
        return 50

def save_signal(direction, entry, sl, tp1, tp2, tp3, confidence):
    trade = {
        "direction":  direction,
        "entry":      entry,
        "sl":         sl,
        "tp1":        tp1,
        "tp2":        tp2,
        "tp3":        tp3,
        "confidence": confidence,
        "tp1_hit":    False,
        "tp2_hit":    False,
        "tp3_hit":    False,
        "active":     True,
        "time":       datetime.now().strftime('%Y-%m-%d %H:%M'),
        "max_profit": 0,
        "smart_exit": False
    }
    with open("active_trade.json","w") as f:
        json.dump(trade, f, ensure_ascii=False)
    print(f"✅ صفقة مسجلة للمراقبة: {direction} @ {entry}")

def monitor():
    while True:
        try:
            # تحقق من وجود صفقة نشطة
            try:
                with open("active_trade.json","r") as f:
                    trade = json.load(f)
            except:
                time.sleep(60)
                continue

            if not trade.get("active"):
                time.sleep(60)
                continue

            price = get_price()
            if not price:
                time.sleep(30)
                continue

            direction = trade['direction']
            entry     = float(trade['entry'])
            sl        = float(trade['sl'])
            tp1       = float(trade['tp1'])
            tp2       = float(trade['tp2'])
            tp3       = float(trade['tp3'])

            # حساب الربح الحالي
            if direction == "BUY":
                current_pnl = round((price - entry) * 100, 2)
            else:
                current_pnl = round((entry - price) * 100, 2)

            # تحديث أعلى ربح
            if current_pnl > trade.get('max_profit', 0):
                trade['max_profit'] = current_pnl

            # ━━━━━━━━━━━━━━━━
            # BUY منطق
            # ━━━━━━━━━━━━━━━━
            if direction == "BUY":

                # ضرب SL
                if price <= sl:
                    loss = round((entry - sl) * 100, 2)
                    send(f"""❌ وقف الخسارة ضُرب!
━━━━━━━━━━━━━━━━
📉 الخسارة: ${loss}
🔴 الدخول: {entry}
🔴 الخروج: {price}
━━━━━━━━━━━━━━━━
📊 سيتم تسجيل LOSS""")
                    _close(trade, "LOSS", price, current_pnl)
                    continue

                # TP1
                if not trade['tp1_hit'] and price >= tp1:
                    trade['tp1_hit'] = True
                    profit = round((tp1-entry)*100, 2)
                    send(f"""🥇 الهدف الأول تحقق! ✅
━━━━━━━━━━━━━━━━
💰 ربح: +${profit}
📈 السعر: {price}
━━━━━━━━━━━━━━━━
💡 أغلق 40% من الصفقة
🔒 حرك SL إلى نقطة الدخول {entry}""")

                # TP2
                if trade['tp1_hit'] and not trade['tp2_hit'] and price >= tp2:
                    trade['tp2_hit'] = True
                    profit = round((tp2-entry)*100, 2)
                    send(f"""🥈 الهدف الثاني تحقق! ✅
━━━━━━━━━━━━━━━━
💰 ربح: +${profit}
📈 السعر: {price}
━━━━━━━━━━━━━━━━
💡 أغلق 40% إضافية
🔒 اترك 20% تركض""")

                # TP3
                if trade['tp2_hit'] and price >= tp3:
                    profit = round((tp3-entry)*100, 2)
                    send(f"""🥉 الهدف الثالث تحقق! 🎉
━━━━━━━━━━━━━━━━
💰 الربح الكامل: +${profit}
📈 الدخول: {entry} | الخروج: {tp3}
━━━━━━━━━━━━━━━━
🏆 صفقة ناجحة بالكامل!""")
                    _close(trade, "WIN", price, profit)
                    continue

                # ━━ الخروج الذكي ━━
                rsi = get_trend_score()

                # إذا وصل TP1 والـ RSI انعكس
                if trade['tp1_hit'] and rsi > 75:
                    send(f"""⚠️ إشارة خروج ذكي!
━━━━━━━━━━━━━━━━
📊 RSI: {rsi} (تشبع شراء)
💰 ربح حالي: +${current_pnl}
━━━━━━━━━━━━━━━━
💡 فكر في إغلاق الصفقة الآن
قبل الانعكاس المحتمل""")
                    trade['smart_exit'] = True

                # إذا تراجع الربح بعد وصول TP1
                max_p = trade.get('max_profit', 0)
                if trade['tp1_hit'] and max_p > 0 and current_pnl < max_p * 0.5:
                    send(f"""⚠️ تراجع الربح!
━━━━━━━━━━━━━━━━
📉 أعلى ربح كان: +${max_p}
📉 الربح الآن: +${current_pnl}
━━━━━━━━━━━━━━━━
💡 فكر في الخروج لحفظ الربح""")

            # ━━━━━━━━━━━━━━━━
            # SELL منطق
            # ━━━━━━━━━━━━━━━━
            elif direction == "SELL":

                # ضرب SL
                if price >= sl:
                    loss = round((sl - entry) * 100, 2)
                    send(f"""❌ وقف الخسارة ضُرب!
━━━━━━━━━━━━━━━━
📉 الخسارة: ${abs(loss)}
🔴 الدخول: {entry}
🔴 الخروج: {price}
━━━━━━━━━━━━━━━━
📊 سيتم تسجيل LOSS""")
                    _close(trade, "LOSS", price, current_pnl)
                    continue

                # TP1
                if not trade['tp1_hit'] and price <= tp1:
                    trade['tp1_hit'] = True
                    profit = round((entry-tp1)*100, 2)
                    send(f"""🥇 الهدف الأول تحقق! ✅
━━━━━━━━━━━━━━━━
💰 ربح: +${profit}
📉 السعر: {price}
━━━━━━━━━━━━━━━━
💡 أغلق 40% من الصفقة
🔒 حرك SL إلى نقطة الدخول {entry}""")

                # TP2
                if trade['tp1_hit'] and not trade['tp2_hit'] and price <= tp2:
                    trade['tp2_hit'] = True
                    profit = round((entry-tp2)*100, 2)
                    send(f"""🥈 الهدف الثاني تحقق! ✅
━━━━━━━━━━━━━━━━
💰 ربح: +${profit}
📉 السعر: {price}
━━━━━━━━━━━━━━━━
💡 أغلق 40% إضافية""")

                # TP3
                if trade['tp2_hit'] and price <= tp3:
                    profit = round((entry-tp3)*100, 2)
                    send(f"""🥉 الهدف الثالث تحقق! 🎉
━━━━━━━━━━━━━━━━
💰 الربح الكامل: +${profit}
📉 الدخول: {entry} | الخروج: {tp3}
━━━━━━━━━━━━━━━━
🏆 صفقة ناجحة بالكامل!""")
                    _close(trade, "WIN", price, profit)
                    continue

                # ━━ الخروج الذكي ━━
                rsi = get_trend_score()

                if trade['tp1_hit'] and rsi < 25:
                    send(f"""⚠️ إشارة خروج ذكي!
━━━━━━━━━━━━━━━━
📊 RSI: {rsi} (تشبع بيع)
💰 ربح حالي: +${current_pnl}
━━━━━━━━━━━━━━━━
💡 فكر في إغلاق الصفقة الآن""")

                max_p = trade.get('max_profit', 0)
                if trade['tp1_hit'] and max_p > 0 and current_pnl < max_p * 0.5:
                    send(f"""⚠️ تراجع الربح!
━━━━━━━━━━━━━━━━
📉 أعلى ربح: +${max_p}
📉 الربح الآن: +${current_pnl}
━━━━━━━━━━━━━━━━
💡 فكر في الخروج""")

            # حفظ التحديثات
            with open("active_trade.json","w") as f:
                json.dump(trade, f, ensure_ascii=False)

        except Exception as e:
            print(f"خطأ: {e}")

        time.sleep(60)

def _close(trade, result, exit_price, pnl):
    trade['active']     = False
    trade['result']     = result
    trade['exit_price'] = exit_price
    trade['exit_time']  = datetime.now().strftime('%Y-%m-%d %H:%M')
    with open("active_trade.json","w") as f:
        json.dump(trade, f, ensure_ascii=False)

    # تسجيل في results.txt
    with open("results.txt","a") as f:
        f.write(f"{trade['exit_time']}|{trade['direction']}|{trade['entry']}|{exit_price}|{result}|{pnl}\n")

    # إحصائيات
    try:
        lines  = open("results.txt").readlines()
        wins   = sum(1 for l in lines if "WIN"  in l)
        losses = sum(1 for l in lines if "LOSS" in l)
        total  = wins + losses
        rate   = round((wins/total)*100,1) if total>0 else 0
        send(f"""📊 إحصائيات محدّثة
━━━━━━━━━━━━━━━━
📈 إجمالي : {total}
✅ ربح    : {wins}
❌ خسارة  : {losses}
🎯 دقة    : {rate}%""")
    except:
        pass

print("✅ Smart Monitor جاهز")

if __name__ == "__main__":
    print("🔍 بدء المراقبة الذكية...")
    monitor()
