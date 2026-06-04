from datetime import datetime

def load_data():
    trades, results = [], []
    try:
        with open("journal.txt","r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 5:
                    trades.append({"time":parts[0],"signal":parts[1],"price":parts[2],"confidence":parts[3]})
    except: pass
    try:
        with open("results.txt","r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    results.append({"time":parts[0],"direction":parts[1],"entry":parts[2],"result":parts[-2] if len(parts)>=5 else parts[-1]})
    except: pass
    return trades, results

def analyze_by_session(results):
    sessions = {"آسيا (0-8)":{"wins":0,"losses":0},"لندن (8-13)":{"wins":0,"losses":0},"تداخل (13-17)":{"wins":0,"losses":0},"نيويورك (17-22)":{"wins":0,"losses":0}}
    for r in results:
        try:
            hour = int(r['time'].split(" ")[1].split(":")[0])
            if 0<=hour<8: s="آسيا (0-8)"
            elif 8<=hour<13: s="لندن (8-13)"
            elif 13<=hour<17: s="تداخل (13-17)"
            else: s="نيويورك (17-22)"
            if "WIN" in r['result'] or "TP" in r['result']: sessions[s]["wins"]+=1
            elif "LOSS" in r['result']: sessions[s]["losses"]+=1
        except: pass
    return sessions

def generate_report():
    trades, results = load_data()
    total  = len(results)
    wins   = sum(1 for r in results if "WIN" in r.get('result','') or "TP" in r.get('result',''))
    losses = sum(1 for r in results if "LOSS" in r.get('result',''))
    rate   = round((wins/total)*100,1) if total>0 else 0
    msg = f"""📊 التحليل التاريخي
━━━━━━━━━━━━━━━━
📈 إجمالي : {total}
✅ رابحة  : {wins}
❌ خاسرة  : {losses}
🎯 Win Rate: {rate}%
━━━━━━━━━━━━━━━━
📅 أفضل الجلسات:\n"""
    sessions = analyze_by_session(results)
    for session, data in sessions.items():
        t = data['wins']+data['losses']
        r = round((data['wins']/t)*100,1) if t>0 else 0
        msg += f"  {session}: {r}% ({t} صفقة)\n"
    msg += f"━━━━━━━━━━━━━━━━\n📝 إجمالي الإشارات: {len(trades)}\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    return msg

print("✅ Analytics Engine جاهز")
