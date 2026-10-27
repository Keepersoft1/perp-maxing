import json,urllib.request,re
UA={"User-Agent":"Mozilla/5.0 perp-maxing","Accept":"application/json"}
res={}
def g(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60) as r: return json.loads(r.read())
try:
    rows=[]
    for page in (1,2):
        rows+=g(f"https://api.coingecko.com/api/v3/derivatives/exchanges?per_page=100&page={page}")
    rx=re.compile(r"variational|lighter|extended|rise|nado|entropy|arcus",re.I)
    res["coingecko_total"]=len(rows)
    res["coingecko_hits"]=[{k:r.get(k) for k in ("id","name","trade_volume_24h_btc","open_interest_btc","number_of_perpetual_pairs")} for r in rows if rx.search(r.get("name","")+" "+r.get("id",""))]
except Exception as e: res["coingecko_err"]=str(e)
try:
    d=g("https://api.llama.fi/overview/dexs?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")
    rx=re.compile(r"variational|lighter|extended|rise|nado|entropy|arcus",re.I)
    res["llama_dexs_hits"]=[(p.get("name"),p.get("slug"),p.get("category"),p.get("total24h")) for p in d.get("protocols",[]) if rx.search((p.get("name") or "")+" "+(p.get("slug") or ""))]
except Exception as e: res["llama_dexs_err"]=str(e)
json.dump(res,open("data/probe.json","w"),indent=1,default=str)
