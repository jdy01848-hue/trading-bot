import json

results = json.load(open('backtest_full_results.json'))

filtered = [r for r in results if r['has_liq']==True and r['manip_score']<50 and 25<=r['adx4']<60]

w = sum(1 for r in filtered if r['result']=='WIN')
l = sum(1 for r in filtered if r['result']=='LOSS')
total = w+l
rate = round((w/total)*100,1) if total>0 else 0
profit = sum(r['profit'] for r in filtered if r['result']=='WIN') - sum(r['profit'] for r in filtered if r['result']=='LOSS')

print(f"📊 الشرط المُحسَّن: has_liq=True + manip_score<50 + adx4(25-60)")
print(f"عدد الصفقات: {total} (رابحة {w} | خاسرة {l})")
print(f"Win Rate: {rate}%")
print(f"صافي الربح: {round(profit,2)} نقطة")
