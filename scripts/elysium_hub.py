import urllib.request,re,os,json,datetime,html as H
ROOT="elysium"; SRC="https://mainnet.elysiumeco.xyz/"
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36"}
def get(u,b=False):
    d=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40).read()
    return d if b else d.decode("utf-8","ignore")
def num(s):
    s=s.replace("$","").replace(",","").strip(); m={"K":1e3,"M":1e6,"B":1e9}
    return float(s[:-1])*m[s[-1]] if s and s[-1] in m else float(s or 0)
def parse(h):
    t=re.sub(r'<script[^>]*>(.*?)</script>',lambda m:" "+m.group(1)+" ",h,flags=re.S)
    t=H.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',t)))
    o={}
    m=re.search(r'Block ([\d,]+) Transactions today ([\d,]+) Active wallets today \$([\d.,]+[KMB]?) Value in apps ([\d,]+) Tokens launched HYPE \$([\d.]+)',t)
    if m: o["today"]={"tx_today":num(m[1]),"wallets_today":num(m[2]),"value_in_apps":num(m[3]),"tokens_launched":num(m[4]),"hype":num(m[5])}
    m=re.search(r'([\d,]+) transactions since launch',t); o["tx_total"]=num(m[1]) if m else None
    i=t.find('{"New transactions"')
    if i>=0:
        dec=json.JSONDecoder(); o["series"],_=dec.raw_decode(t[i:])
    seg=t[t.find('All ',t.find('Projects')):]
    seg=seg[:seg.find('Building on Elysium')]
    pr=[]
    for m in re.finditer(r'(?:Open |projects )([A-Z][\w .\-]{1,24}?) ([^$]{0,60}?) (?:On mainnet|Partner) (Volume 7d|Sales vol\. 7d) \$([\d.,]+[KMB]?) Wallets 7d ([\d,]+) (\w+)',seg):
        pr.append({"name":m[1].strip(),"desc":m[2].strip(),"metric":m[3],"vol7d":num(m[4]),"wallets7d":num(m[5]),"cat":m[6]})
    for p in pr:
        if p["name"]=="Elysium" and p["desc"].startswith("Machines"): p["name"]="Elysium Machines"; p["desc"]=p["desc"][9:]
    o["projects"]=pr
    a=t.find('Price Market cap Vol 24h'); b=t.find('Price Market cap Vol 24h',a+10)
    tk=[]
    for m in re.finditer(r'(.{1,40}?) \$(\S+) · (\d+[smhdw]) (\S+) \$([\d.]+) \$([\d.,]+[KMB]?) \$([\d.,]+[KMB]?) Open',t[a+24:b]):
        nm=m[1].strip(); nm=nm[2:] if len(nm)>2 and nm[1]==" " else nm
        tk.append({"name":nm,"ticker":m[2],"age":m[3],"pad":m[4],"price":float(m[5]),"mcap":num(m[6]),"vol24h":num(m[7])})
    o["trending"]=tk
    m=re.search(r'All ([\d,]+) tokens',t); o["tokens_listed"]=num(m[1]) if m else None
    o["trade"]={}
    i=h.find('"tradeTpl":')
    if i>=0:
        try: o["trade"],_=json.JSONDecoder().raw_decode(H.unescape(h[i+11:]))
        except Exception: pass
    m=re.search(r'"updated":"([^"]+)"',h); o["src_updated"]=m[1] if m else None
    return o
if __name__=="__main__":
    h=get(SRC); o=parse(h)
    o["fetched"]=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    for p in o["projects"]:
        slug=re.sub(r'[^a-z0-9]','',p["name"].lower())
        f=f"{ROOT}/logos/{slug}.jpg"
        if not os.path.exists(f):
            for ext in ["jpg","png"]:
                try:
                    d=get(f"{SRC}logos/{slug}.{ext}",True)
                    if len(d)>500 and not d[:15].lower().startswith(b"<!doctype"): open(f,"wb").write(d); break
                except Exception: pass
        p["logo"]=f"logos/{slug}.jpg" if os.path.exists(f) else None
    hp=f"{ROOT}/data/history.json"
    hist=json.load(open(hp)) if os.path.exists(hp) else []
    day=o["fetched"][:10]
    snap={"t":o["fetched"],"lp_vol7d":sum(p["vol7d"] for p in o["projects"] if p["cat"]=="Launchpad"),**{k:o.get("today",{}).get(k) for k in ["value_in_apps","tokens_launched","hype"]},"tx_total":o.get("tx_total")}
    hist=[x for x in hist if x["t"][:13]!=o["fetched"][:13]]+[snap]
    json.dump(hist[-2000:],open(hp,"w"))
    json.dump(o,open(f"{ROOT}/data/hub.json","w"))
    print(json.dumps({k:(v if k not in("series","trade") else "...") for k,v in o.items()},indent=0)[:3000])
