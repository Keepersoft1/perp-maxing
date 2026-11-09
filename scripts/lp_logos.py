import urllib.request,re,os,json,datetime
os.makedirs("data/lp3",exist_ok=True)
r=urllib.request.Request("https://mainnet.elysiumeco.xyz/",headers={"User-Agent":"Mozilla/5.0 Chrome/130"})
h=urllib.request.urlopen(r,timeout=40).read().decode("utf-8","ignore")
open("data/lp3/tracker.html","w").write(h)
t=re.sub(r'<[^>]+>',' ',h); t=re.sub(r'\s+',' ',t)
out={"fetched":datetime.datetime.utcnow().isoformat()}
out["rows"]=re.findall(r'([A-Za-z0-9.\- ]{2,25}?) (?:Launchpad|Token launch)[^$]{0,80}?Volume 7d (\$[\d.,]+[KMB]?) Wallets 7d ([\d,]+)',t)
i=t.find("Network Details"); out["network"]=t[i:i+1500]
out["header"]=t[:3000]
json.dump(out,open("data/lp3/stats.json","w"),indent=1)
