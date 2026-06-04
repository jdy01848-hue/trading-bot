import requests
import json
from datetime import datetime

TOKEN = "8793823731:AAG1TKA6-6SZzqc03aAV3UWnOWgrPpgZFSA"
CHAT_ID = "5902098963"
TD_KEY = "6e9a8257a2d04b80b56b022707232bff"

def get_current_price():
    try:
        r = requests.get(
            "https://api.twelvedata.com/price",
            params={"symbol":"XAU/USD","apikey":TD_KEY},
            timeout=10)
        return float(r.json()['price'])
    except:
        return None

def send_with_buttons(text, trade_id):
    """يرسل رسالة مع أزرار التسجيل"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🥇 TP1 وصل", "callback_data": f"tp1_{trade_id}"},
                    {"text": "🥈 TP2 وصل", "callback_data": f"tp2_{trade_id}"}
                ],
                [
                    {"text": "🥉 TP3 وصل", "callback_data": f"tp3_{trade_id}"},
                    {"text": "❌ ضرب SL", "callback_data": f"sl_{trade_id}"}
                ],
                [
                    {"text": "🚪 أغلقت يدوي", "callback_data": f"manual_{trade_id}"}
                ]
            ]
        }
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "reply_markup": keyboard
        }, timeout=10)
    except Exception as e:
        print(f"خطأ في الإرسال: {e}")

def handle_button(callback_data):
    """يعالج ضغط الأزرار"""
    try:
        parts = callback_data.split('_')
        action = parts[0]
        trade_id = '_'.join(parts[1:])

        # جلب بيانات الصفقة
        try:
            with open("active_trade.json","r") as f:
                trade = json.load(f)
        except:
            send_msg("❌ لا توجد صفقة نشطة")
            return

        entry    = float(trade.get('entry', 0))
        sl       = float(trade.get('sl', 0))
        tp1      = float(trade.get('tp1', 0))
        tp2      = float(trade.get('tp2', 0))
        tp3      = float(trade.get('tp3', 0))
        direction = trade.get('direction', 'SELL')

        if action == 'tp1':
            profit = calc_profit(direction, entry, tp1)
            msg = f"""🥇 الهدف الأول تحقق! ✅
━━━━━━━━━━━━━━━━
💰 ربح: +${profit}
📈 من {entry} إلى {tp1}
━━━━━━━━━━━━━━━━
💡 أغلق 40% من الصفقة
🔒 حرك SL إلى {entry}"""
            send_msg(msg)
            log_result("TP1", profit, trade)

        elif action == 'tp2':
            profit = calc_profit(direction, entry, tp2)
            msg = f"""🥈 الهدف الثاني تحقق! ✅
━━━━━━━━━━━━━━━━
💰 ربح: +${profit}
📈 من {entry} إلى {tp2}
━━━━━━━━━━━━━━━━
💡 أغلق 40% إضافية"""
            send_msg(msg)
            log_result("TP2", profit, trade)

        elif action == 'tp3':
            profit = calc_profit(direction, entry, tp3)
            msg = f"""🥉 الهدف الثالث تحقق! 🎉
━━━━━━━━━━━━━━━━
💰 ربح كامل: +${profit}
━━━━━━━━━━━━━━━━
🏆 صفقة ناجحة بالكامل!"""
            send_msg(msg)
            log_result("WIN", profit, trade)
            close_trade(trade, "WIN", tp3)

        elif action == 'sl':
            loss = calc_profit(direction, entry, sl)
            msg = f"""❌ وقف الخسارة ضُرب
━━━━━━━━━━━━━━━━
📉 خسارة: ${abs(loss)}
━━━━━━━━━━━━━━━━
💪 الخسارة جزء من التداول
انتظر الإشارة القادمة"""
            send_msg(msg)
            log_result("LOSS", loss, trade)
            close_trade(trade, "LOSS", sl)

        elif action == 'manual':
            price = get_current_price()
            if price:
                profit = calc_profit(direction, entry, price)
                emoji = "✅" if profit > 0 else "❌"
                result = "ربح" if profit > 0 else "خسارة"
                msg = f"""{emoji} إغلاق يدوي
━━━━━━━━━━━━━━━━
💰 السعر الحالي: {price}
📊 الدخول: {entry}
━━━━━━━━━━━━━━━━
{'💰' if profit > 0 else '📉'} {result}: ${abs(profit)}
━━━━━━━━━━━━━━━━"""

                # أضف مقارنة بالأهداف
                if direction == "SELL":
                    if price <= tp3: msg += "\n🥉 كان يمكن الوصول لـ TP3!"
                    elif price <= tp2: msg += "\n🥈 كان يمكن الوصول لـ TP2!"
                    elif price <= tp1: msg += "\n🥇 وصلت لـ TP1 على الأقل!"
                else:
                    if price >= tp3: msg += "\n🥉 كان يمكن الوصول لـ TP3!"
                    elif price >= tp2: msg += "\n🥈 كان يمكن الوصول لـ TP2!"
                    elif price >= tp1: msg += "\n🥇 وصلت لـ TP1 على الأقل!"

                send_msg(msg)
                result_type = "WIN" if profit > 0 else "LOSS"
                log_result(result_type, profit, trade)
                close_trade(trade, result_type, price)
            else:
                send_msg("⚠️ لم أستطع جلب السعر الحالي")

    except Exception as e:
        send_msg(f"⚠️ خطأ: {e}")

def calc_profit(direction, entry, exit_price):
    if direction == "BUY":
        return round((exit_price - entry), 2)
    else:
        return round((entry - exit_price), 2)

def log_result(result_type, profit, trade):
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        with open("results.txt","a") as f:
            f.write(f"{now}|{trade.get('direction')}|{trade.get('entry')}|{result_type}|{profit}\n")

        lines = open("results.txt").readlines()
        wins   = sum(1 for l in lines if "WIN" in l or "TP" in l)
        losses = sum(1 for l in lines if "LOSS" in l)
        total  = wins + losses
        rate   = round((wins/total)*100,1) if total>0 else 0
        send_msg(f"📊 إجمالي: {total} | ✅ {wins} | ❌ {losses} | دقة: {rate}%")
    except:
        pass

def close_trade(trade, result, exit_price):
    try:
        trade['active'] = False
        trade['result'] = result
        trade['exit_price'] = exit_price
        trade['exit_time'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        with open("active_trade.json","w") as f:
            json.dump(trade, f, ensure_ascii=False)
    except:
        pass

def send_msg(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text},
            timeout=10)
    except:
        pass

def listen_buttons():
    """يستمع لضغطات الأزرار"""
    offset = 0
    while True:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35)
            updates = r.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                if "callback_query" in update:
                    cb = update["callback_query"]
                    handle_button(cb["data"])
                    # تأكيد استلام الضغطة
                    requests.post(
                        f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery",
                        data={"callback_query_id": cb["id"]},
                        timeout=5)
        except:
            pass

print("✅ Trade Buttons جاهز")

if __name__ == "__main__":
    print("🎯 بدء الاستماع للأزرار...")
    listen_buttons()
