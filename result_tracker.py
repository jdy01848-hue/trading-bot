import requests
import sys
from datetime import datetime

TOKEN = "8793823731:AAG1TKA6-6SZzqc03aAV3UWnOWgrPpgZFSA"
CHAT_ID = "5902098963"

def send(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except:
        pass

def save_result(result, notes=""):
    try:
        with open("journal.txt", "r") as f:
            lines = f.readlines()
        if not lines:
            print("لا توجد اشارات")
            return
        last = lines[-1].strip().split("|")
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        with open("results.txt", "a") as f:
            f.write(f"{now}|{result}|{notes}\n")
        wins = sum(1 for l in open("results.txt") if "WIN" in l)
        losses = sum(1 for l in open("results.txt") if "LOSS" in l)
        total = wins + losses
        rate = round((wins/total)*100, 1) if total > 0 else 0
        emoji = "✅" if result == "WIN" else "❌"
        msg = f"{emoji} {result}\nاجمالي: {total} | ربح: {wins} | خسارة: {losses} | دقة: {rate}%"
        send(msg)
        print(msg)
    except Exception as e:
        print(f"خطأ: {e}")

def show_stats():
    try:
        lines = open("results.txt").readlines()
        wins = sum(1 for l in lines if "WIN" in l)
        losses = sum(1 for l in lines if "LOSS" in l)
        total = wins + losses
        rate = round((wins/total)*100, 1) if total > 0 else 0
        msg = f"📊 الاحصائيات\nاجمالي: {total} | ربح: {wins} | خسارة: {losses} | دقة: {rate}%"
        send(msg)
        print(msg)
    except:
        print("لا توجد نتائج بعد")

cmd = sys.argv[1].upper() if len(sys.argv) > 1 else ""
if cmd == "WIN":
    save_result("WIN", sys.argv[2] if len(sys.argv) > 2 else "")
elif cmd == "LOSS":
    save_result("LOSS", sys.argv[2] if len(sys.argv) > 2 else "")
elif cmd == "STATS":
    show_stats()
else:
    print("استخدم: win | loss | stats")
