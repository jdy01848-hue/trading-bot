import requests
import time
import json
from datetime import datetime

TOKEN = "8793823731:AAG1TKA6-6SZzqc03aAV3UWnOWgrPpgZFSA"
CHAT_ID = "5902098963"
TD_KEY = "6e9a8257a2d04b80b56b022707232bff"

def send(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except:
        pass

def get_price():
    try:
        r = requests.get(
            "https://api.twelvedata.com/price",
            params={"symbol": "XAU/USD", "apikey": TD_KEY},
            timeout=10
        )
        return float(r.json()['price'])
    except:
        return None

def save_active_trade(direction, entry, sl, tp1, tp2, tp3):
    trade = {
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "tp1_hit": False,
        "tp2_hit": False,
        "tp3_hit": False,
        "time": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "active": True
    }
    with open("active_trade.json", "w") as f:
        json.dump(trade, f)
    print(f"✅ صفقة مسجلة: {direction} @ {entry}")

def check_trade():
    try:
        with open("active_trade.json", "r") as f:
            trade = json.load(f)
    except:
        return

    if not trade.get("active"):
        return

    price = get_price()
    if not price:
        return

    direction = trade['direction']
    entry     = trade['entry']
    sl        = trade['sl']
    tp1       = trade['tp1']
    tp2       = trade['tp2']
    tp3       = trade['tp3']

    # حساب الربح/الخسارة الحالي
    if direction == "BUY":
        pnl = round((price - entry) * 100, 2)
        
        # ضرب SL
        if price <= sl:
            result = round((sl - entry) * 100, 2)
            send(f"❌ SL ضُرب!\nالخسارة: ${abs(result)}\nالدخول: {entry} | الخروج: {price}")
            _close_trade("LOSS", price)
            return

        # وصول TP1
        if not trade['tp1_hit'] and price >= tp1:
            trade['tp1_hit'] = True
            send(f"🥇 TP1 وصل! +{round((tp1-entry)*100,2)}$\nأغلق 40% وحرك SL للدخول")
            with open("active_trade.json", "w") as f:
                json.dump(trade, f)

        # وصول TP2
        if trade['tp1_hit'] and not trade['tp2_hit'] and price >= tp2:
            trade['tp2_hit'] = True
            send(f"🥈 TP2 وصل! +{round((tp2-entry)*100,2)}$\nأغلق 40% إضافية")
            with open("active_trade.json", "w") as f:
                json.dump(trade, f)

        # وصول TP3
        if trade['tp2_hit'] and price >= tp3:
            result = round((tp3 - entry) * 100, 2)
            send(f"🥉 TP3 وصل! 🎉\nربح كامل: +${result}\nالدخول: {entry} | الخروج: {tp3}")
            _close_trade("WIN", price)

    elif direction == "SELL":
        pnl = round((entry - price) * 100, 2)

        # ضرب SL
        if price >= sl:
            result = round((entry - sl) * 100, 2)
            send(f"❌ SL ضُرب!\nالخسارة: ${abs(result)}\nالدخول: {entry} | الخروج: {price}")
            _close_trade("LOSS", price)
            return

        # وصول TP1
        if not trade['tp1_hit'] and price <= tp1:
            trade['tp1_hit'] = True
            send(f"🥇 TP1 وصل! +{round((entry-tp1)*100,2)}$\nأغلق 40% وحرك SL للدخول")
            with open("active_trade.json", "w") as f:
                json.dump(trade, f)

        # وصول TP2
        if trade['tp1_hit'] and not trade['tp2_hit'] and price <= tp2:
            trade['tp2_hit'] = True
            send(f"🥈 TP2 وصل! +{round((entry-tp2)*100,2)}$\nأغلق 40% إضافية")
            with open("active_trade.json", "w") as f:
                json.dump(trade, f)

        # وصول TP3
        if trade['tp2_hit'] and price <= tp3:
            result = round((entry - tp3) * 100, 2)
            send(f"🥉 TP3 وصل! 🎉\nربح كامل: +${result}\nالدخول: {entry} | الخروج: {tp3}")
            _close_trade("WIN", price)

def _close_trade(result, exit_price):
    try:
        with open("active_trade.json", "r") as f:
            trade = json.load(f)
        trade['active'] = False
        trade['result'] = result
        trade['exit_price'] = exit_price
        trade['exit_time'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        with open("active_trade.json", "w") as f:
            json.dump(trade, f)

        # تسجيل في results.txt
        with open("results.txt", "a") as f:
            f.write(f"{trade['exit_time']}|{trade['direction']}|{trade['entry']}|{exit_price}|{result}\n")

        # إحصائيات
        lines = open("results.txt").readlines()
        wins   = sum(1 for l in lines if "WIN" in l)
        losses = sum(1 for l in lines if "LOSS" in l)
        total  = wins + losses
        rate   = round((wins/total)*100, 1) if total > 0 else 0
        send(f"📊 إحصائيات:\nإجمالي: {total} | ✅ {wins} | ❌ {losses} | دقة: {rate}%")
    except Exception as e:
        print(f"خطأ: {e}")

print("✅ Price Monitor جاهز")

if __name__ == "__main__":
    print("🔍 مراقبة السعر كل دقيقة...")
    while True:
        check_trade()
        time.sleep(60)
