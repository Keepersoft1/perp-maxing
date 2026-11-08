import json,urllib.request,re,os
os.makedirs("data/lp2",exist_ok=True)
def get(u,b=False):
    r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36"})
    d=urllib.request.urlopen(r,timeout=30).read()
    return d if b else d.decode("utf-8","ignore")
log={}
try:
    b=get("https://elysiom.trade/boot.js?v=14exafgp7n"); open("data/lp2/boot.js","w").write(b)
    for m in set(re.findall(r'["\'](/[A-Za-z0-9_./-]+\.js[^"\']*)["\']',b)):
        try: open("data/lp2/"+re.sub(r'\W','_',m)[:60]+".js","w").write(get("https://elysiom.trade"+m))
        except Exception as e: log[m]=str(e)
except Exception as e: log["boot"]=str(e)
slugs="montra ascend kleos boxa elyspump obol volta rons stockium arkhampad eleos elyxa quoted mesa elyra liquidfi styxn torusfi apogee hookium elysianpad elevate arena arka stonkspad elysrocket elixirpad hesperia fullfun nectar perpme tartarus boursely akafun hips pangea stands wormpad o1 zyora launchcraft asphodel clanker signalfam elyne chainzy supercolony olympad ronspad corepad pumpfun".split()
for s in slugs:
    for ext in ["jpg","png","webp","svg"]:
        try:
            d=get(f"https://mainnet.elysiumeco.xyz/logos/{s}.{ext}",True)
            if len(d)>500 and not d[:20].lower().startswith(b"<!doctype"):
                open(f"data/lp2/{s}.{ext}","wb").write(d); log[s]=ext; break
        except Exception as e: pass
json.dump(log,open("data/lp2/log.json","w"),indent=1)
