import requests
import json
import time
import yfinance as yf
import logging
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime

TOKEN = "8793823731:AAG1TKA6-6SZzqc03aAV3UWnOWgrPpgZFSA"
CHAT_ID = "5902098963"
TRADE_FILE = "active_trade.json"

def send(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except:
        pass

def save_trade(direction, entry, sl, tp):
    trade = {
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "time": datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    json.dump(trade, open(TRADE_FILE, "w"))
    print(f"✅ صفقة مسجلة: {direction} @ {entry}")

def get_price():
    try:
        df = yf.download("GC=F", period="2d", interval="1m", progress=False)
        return float(df['Close'].iloc[-1])
    except:
        return None

def check_trade():
    try:
        trade = json.load(open(TRADE_FILE))
    except:
        return

    price = get_price()
    if not price:
        return

    direction = trade["direction"]
    entry = trade["entry"]
    sl = trade["sl"]
    tp = trade["tp"]

    hit_tp = False
    hit_sl = False

    if direction == "BUY":
        hit_tp = price >= tp
        hit_sl = price <= sl
    elif direction == "SELL":
        hit_tp = price <= tp
        hit_sl = price >= sl

    if hit_tp:
        pips = round(abs(tp - entry), 2)
        msg = f"""✅ WIN — TP وصل!
━━━━━━━━━━━━━━━━
📈 {direction} @ {entry}
🎯 TP: {tp} ✅
💰 ربح: {pips} نقطة
🕐 {datetime.now().strftime('%H:%M')}"""
        send(msg)
        print(msg)
        # سجل WIN
        import subprocess
        subprocess.run(["python", "result_tracker.py", "win"])
        import os; os.remove(TRADE_FILE)

    elif hit_sl:
        pips = round(abs(sl - entry), 2)
        msg = f"""❌ LOSS — SL وصل
━━━━━━━━━━━━━━━━
📉 {direction} @ {entry}
🛑 SL: {sl} ❌
💸 خسارة: {pips} نقطة
🕐 {datetime.now().strftime('%H:%M')}"""
        send(msg)
        print(msg)
        import subprocess
        subprocess.run(["python", "result_tracker.py", "loss"])
        import os; os.remove(TRADE_FILE)

    else:
        pips = round(price - entry if direction=="BUY" else entry - price, 2)
        status = "🟢" if pips > 0 else "🔴"
        print(f"{status} متابعة | السعر: {price} | P&L: {pips:+.2f}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 5:
        save_trade(sys.argv[1].upper(), float(sys.argv[2]),
                   float(sys.argv[3]), float(sys.argv[4]))
    else:
        print("المتابعة التلقائية...")
        while True:
            check_trade()
            time.sleep(60)
