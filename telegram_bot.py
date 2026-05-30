import requests
import threading
import os

TOKEN = "8793823731:AAG1TKA6-6SZzqc03aAV3UWnOWgrPpgZFSA"
CHAT_ID = "5902098963"

def send(chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": chat_id, "text": text},
            timeout=10
        )
    except:
        pass

def send_trade_buttons(chat_id, direction, price, sl, tp):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": f"هل نفذت الصفقة؟ {direction} @ {price} | SL: {sl} | TP: {tp}",
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "✅ نفّذت", "callback_data": f"executed_{direction}_{price}_{sl}_{tp}"},
                    {"text": "❌ لم أنفّذ", "callback_data": "not_executed"}
                ]]
            }
        },
        timeout=10
    )

def handle_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    data = callback["data"]
    msg_id = callback["message"]["message_id"]

    if data == "not_executed":
        requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery",
            json={"callback_query_id": callback["id"], "text": "تم الإلغاء"}, timeout=10)

    elif data.startswith("executed_"):
        parts = data.split("_")
        direction = parts[1]
        price = parts[2]
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "ما نتيجة الصفقة؟",
                "reply_markup": {
                    "inline_keyboard": [[
                        {"text": "🏆 WIN - وصل TP", "callback_data": "result_win"},
                        {"text": "💸 LOSS - ضرب SL", "callback_data": "result_loss"}
                    ],[
                        {"text": "🔄 لا تزال مفتوحة", "callback_data": "result_open"}
                    ]]
                }
            },
            timeout=10
        )

    elif data == "result_win":
        import subprocess
        subprocess.run(["python", "result_tracker.py", "win"])
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": "✅ تم تسجيل WIN! 🏆"}, timeout=10)

    elif data == "result_loss":
        import subprocess
        subprocess.run(["python", "result_tracker.py", "loss"])
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": "💸 تم تسجيل LOSS"}, timeout=10)

    elif data == "result_open":
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": "🔄 سيتابع البوت الصفقة تلقائياً"}, timeout=10)

def handle_command(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text == "/now":
        send(chat_id, "🔍 جاري التحليل الفوري...")
        os.system("timeout 90 python smart_auto.py &")

    elif text == "/stats":
        try:
            lines = open("results.txt").readlines()
            wins   = sum(1 for l in lines if "WIN" in l)
            losses = sum(1 for l in lines if "LOSS" in l)
            total  = wins + losses
            rate   = round((wins/total)*100, 1) if total > 0 else 0
            send(chat_id, f"""📊 الإحصائيات
━━━━━━━━━━━━━━━━
📈 إجمالي : {total}
✅ رابحة  : {wins}
❌ خاسرة  : {losses}
🎯 دقة    : {rate}%""")
        except:
            send(chat_id, "لا توجد نتائج بعد")

    elif text == "/status":
        send(chat_id, """✅ البوت يعمل
🤖 النظام v7.0
⏱ كل 15 دقيقة""")

    elif text == "/start" or text == "القائمة الرئيسية 🏠":
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "🥇 مرحباً! اختر أمراً:",
                "reply_markup": {
                    "keyboard": [
                        [{"text": "📊 تحليل فوري"}, {"text": "📈 إحصائيات"}],
                        [{"text": "✅ حالة البوت"}, {"text": "القائمة الرئيسية 🏠"}]
                    ],
                    "resize_keyboard": True,
                    "persistent": True
                }
            },
            timeout=10
        )
    elif text == "📊 تحليل فوري":
        handle_command({"chat": {"id": chat_id}, "text": "/now"})
    elif text == "📈 إحصائيات":
        handle_command({"chat": {"id": chat_id}, "text": "/stats"})
    elif text == "✅ حالة البوت":
        handle_command({"chat": {"id": chat_id}, "text": "/status"})

def run_listener():
    offset = 0
    while True:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            updates = r.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                if "message" in update:
                    handle_command(update["message"])
                if "callback_query" in update:
                    handle_callback(update["callback_query"])
        except:
            pass

print("✅ Telegram Commands جاهز")
listener_thread = threading.Thread(target=run_listener, daemon=True)
listener_thread.start()
