import json,urllib.request,re,os,html
os.makedirs("data/lp",exist_ok=True)
def get(u,b=False):
    r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36"})
    d=urllib.request.urlopen(r,timeout=40).read()
    return d if b else d.decode("utf-8","ignore")
log={}
for site in ["https://elysiom.trade/","https://mainnet.elysiumeco.xyz/"]:
    try:
        h=get(site); open("data/lp/"+site.split("//")[1].split("/")[0]+".html","w").write(h)
        imgs=re.findall(r'<img[^>]+>',h); log[site]=imgs[:300]
        # also js bundles
        js=re.findall(r'src="([^"]+\.js)"',h); log[site+"_js"]=js
        for j in js[:8]:
            u=j if j.startswith("http") else site.rstrip("/")+"/"+j.lstrip("/")
            try:
                t=get(u); open("data/lp/"+re.sub(r'\W','_',u)[-60:]+".js","w").write(t)
            except Exception as e: log[u]=str(e)
    except Exception as e: log[site]=str(e)
handles={"montra":"MontraXYZ","ascend":"AscendLaunch","kleos":"TheKleos_","elyspump":"ElysiumPump","boxa":"Boxa_Elysium","obol":"obolworld","stockium":"Stockium","rons":"ronspadfun","eleos":"eleosfun","elyxa":"elyxa_trade","pumpfun":"pumpdotfun","volta":"VoltaElysium","quoted":"quotedfun","mesa":"mesa_fun","arkhampad":"ArkhamPad","elyra":"elyra_xyz"}
for k,h in handles.items():
    for src in [f"https://unavatar.io/x/{h}?fallback=false",f"https://unavatar.io/twitter/{h}?fallback=false"]:
        try:
            d=get(src,True); open(f"data/lp/av_{k}.img","wb").write(d); log["av_"+k]=len(d); break
        except Exception as e: log["av_"+k]=str(e)
json.dump(log,open("data/lp/log.json","w"),indent=1)
