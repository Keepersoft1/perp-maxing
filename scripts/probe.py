import json,urllib.request
API="https://api.llama.fi";UA={"User-Agent":"perp-maxing","Accept":"application/json"}
res={}
def t(path):
    try:
        with urllib.request.urlopen(urllib.request.Request(API+path,headers=UA),timeout=60) as r:
            d=json.loads(r.read());res[path]={"ok":True,"keys":list(d.keys())[:30] if isinstance(d,dict) else type(d).__name__,
              "sample":{k:d[k] for k in list(d)[:0]} if isinstance(d,dict) else None}
            return d
    except Exception as e: res[path]={"ok":False,"err":str(e)}
oi=t("/overview/open-interest?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")
if oi:
    row=[p for p in oi["protocols"] if p.get("slug")=="variational"][0]
    res["oi_row_variational"]={k:v for k,v in row.items() if not isinstance(v,(list,dict))}
for p in ["/summary/open-interest/variational","/summary/open-interest/variational?dataType=openInterestAtEnd",
          "/summary/dexs/variational?dataType=dailyVolume","/summary/derivatives/variational",
          "/overview/dexs?excludeTotalDataChart=true","/protocol/variational","/summary/fees/variational?dataType=dailyFees"]:
    d=t(p)
    if d and isinstance(d,dict):
        res[p]["scalars"]={k:v for k,v in d.items() if isinstance(v,(int,float,str)) and len(str(v))<80}
        ch=d.get("totalDataChart")
        if ch: res[p]["chart_len"]=len(ch);res[p]["chart_tail"]=ch[-3:]
json.dump(res,open("data/probe.json","w"),indent=1,default=str)
