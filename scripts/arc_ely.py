import json,urllib.request,datetime
def get(u):
    try:
        r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
        return json.load(urllib.request.urlopen(r,timeout=60))
    except Exception as e: return {"error":str(e)}
out={}
chains=get("https://api.llama.fi/v2/chains")
out["chain_names"]=[c.get("name") for c in chains if isinstance(c,dict) and any(k in (c.get("name") or "").lower() for k in ["arc","elys"])] if isinstance(chains,list) else chains
for ch in ["Arc","arc","Elysium","elysium"]:
    d=get(f"https://api.llama.fi/overview/dexs/{ch}?excludeTotalDataChartBreakdown=false")
    if "error" in d: out[ch]=d; continue
    tc=[[datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),v] for t,v in d.get("totalDataChart",[])]
    out[ch]={"total":tc[-60:],"protocols":[(p.get("name"),p.get("total24h"),p.get("total7d")) for p in d.get("protocols",[])][:40],
             "breakdown":[[datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),b] for t,b in d.get("totalDataChartBreakdown",[])][-60:]}
json.dump(out,open("data/arc_ely.json","w"),indent=1,default=str)
