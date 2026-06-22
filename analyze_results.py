import json

results = json.load(open('backtest_full_results.json'))
wins = [r for r in results if r['result']=='WIN']
losses = [r for r in results if r['result']=='LOSS']

print(f"📊 تحليل {len(results)} صفقة ({len(wins)} رابحة | {len(losses)} خاسرة)")
print("="*60)

def avg(lst, key):
    vals = [r[key] for r in lst if r.get(key) is not None]
    return round(sum(vals)/len(vals), 2) if vals else 0

def rate_with_condition(condition_fn, label):
    matched = [r for r in results if condition_fn(r)]
    if not matched:
        print(f"{label}: لا توجد عينة")
        return
    w = sum(1 for r in matched if r['result']=='WIN')
    rate = round((w/len(matched))*100, 1)
    print(f"{label}: {len(matched)} صفقة | دقة {rate}%")

print("\n📐 المتوسطات:")
print(f"RSI رابحة: {avg(wins,'rsi1')} | خاسرة: {avg(losses,'rsi1')}")
print(f"ADX4 رابحة: {avg(wins,'adx4')} | خاسرة: {avg(losses,'adx4')}")
print(f"ADX1 رابحة: {avg(wins,'adx1')} | خاسرة: {avg(losses,'adx1')}")
print(f"cf_buy رابحة: {avg(wins,'cf_buy')} | خاسرة: {avg(losses,'cf_buy')}")
print(f"cf_sell رابحة: {avg(wins,'cf_sell')} | خاسرة: {avg(losses,'cf_sell')}")
print(f"manip_score رابحة: {avg(wins,'manip_score')} | خاسرة: {avg(losses,'manip_score')}")

print("\n🎯 دقة حسب الشرط:")
rate_with_condition(lambda r: r['near_fib']==True, "near_fib=True")
rate_with_condition(lambda r: r['near_fib']==False, "near_fib=False")
rate_with_condition(lambda r: r['has_liq']==True, "has_liq=True")
rate_with_condition(lambda r: r['has_liq']==False, "has_liq=False")
rate_with_condition(lambda r: r['manip_score']>=50, "manip_score>=50")
rate_with_condition(lambda r: r['manip_score']<50, "manip_score<50")
rate_with_condition(lambda r: r['adx4']>=90, "adx4>=90 (إرهاق)")
rate_with_condition(lambda r: r['adx4']<90, "adx4<90")
rate_with_condition(lambda r: r['adx4']>=25 and r['adx4']<60, "adx4 بين 25-60 (صحي)")
rate_with_condition(lambda r: r['adx1']>=20 and r['adx1']<50, "adx1 بين 20-50 (صحي)")

print("\n🔀 حسب الاتجاه:")
rate_with_condition(lambda r: r['direction']=='BUY', "كل BUY")
rate_with_condition(lambda r: r['direction']=='SELL', "كل SELL")
