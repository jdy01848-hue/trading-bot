import json
import os

MODEL_FILE = "ai_weights.json"

def load_weights():
    if os.path.exists(MODEL_FILE):
        return json.load(open(MODEL_FILE))
    return {
        "adx4_high": 0, "adx4_low": 0,
        "rsi_buy": 0, "rsi_sell": 0,
        "pullback_win": 0, "pullback_loss": 0,
        "preparing_win": 0, "preparing_loss": 0,
        "total": 0
    }

def save_weights(w):
    json.dump(w, open(MODEL_FILE, "w"), indent=2)

def train_from_results():
    w = load_weights()
    if not os.path.exists("journal.txt"):
        print("لا توجد بيانات للتدريب")
        return w
    if not os.path.exists("results.txt"):
        print("لا توجد نتائج للتدريب")
        return w

    journal = open("journal.txt").readlines()
    results = open("results.txt").readlines()

    trained = 0
    for r_line in results:
        parts = r_line.strip().split("|")
        if len(parts) < 2:
            continue
        outcome = parts[1] if len(parts) > 1 else ""
        if outcome not in ["WIN", "LOSS"]:
            continue

        # ابحث عن journal مطابق
        for j_line in journal:
            j_parts = j_line.strip().split("|")
            if len(j_parts) < 4:
                continue
            decision = j_parts[3] if len(j_parts) > 3 else ""

            if "PREPARING" in decision:
                if outcome == "WIN": w["preparing_win"] += 1
                else: w["preparing_loss"] += 1
            if "PULLBACK" in decision:
                if outcome == "WIN": w["pullback_win"] += 1
                else: w["pullback_loss"] += 1

        w["total"] += 1
        trained += 1

    save_weights(w)
    print(f"✅ تدريب على {trained} صفقة")
    return w

def ai_boost(confidence, decision, adx4, rsi_1h):
    w = load_weights()
    boost = 0

    if w["total"] < 3:
        return confidence, "🤖 AI: يتعلم..."

    # PREPARING accuracy
    prep_total = w["preparing_win"] + w["preparing_loss"]
    if prep_total > 0 and "PREPARING" in decision:
        prep_rate = w["preparing_win"] / prep_total
        if prep_rate > 0.6:
            boost += 10
        elif prep_rate < 0.4:
            boost -= 10

    # PULLBACK accuracy
    pb_total = w["pullback_win"] + w["pullback_loss"]
    if pb_total > 0 and "PULLBACK" in decision:
        pb_rate = w["pullback_win"] / pb_total
        if pb_rate > 0.6:
            boost += 15
        elif pb_rate < 0.4:
            boost -= 15

    new_conf = min(95, max(5, confidence + boost))
    note = f"🤖 AI: {'+' if boost>=0 else ''}{boost}%"
    return new_conf, note

print("✅ AI Model جاهز")
