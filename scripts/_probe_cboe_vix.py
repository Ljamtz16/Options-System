import urllib.request,re
u="https://www.cboe.com/delayed_quotes/vix/quote_table"
s=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=20).read().decode("utf-8","ignore")
for pat in [r'https?[^"\']+\.csv[^"\']*',r'quote[^"\']+api[^"\']*',r'download[^"\']+csv']:
    xs=re.findall(pat,s,re.I)
    print("PAT",pat,"N",len(xs))
    for x in xs[:20]:print(x[:500])
