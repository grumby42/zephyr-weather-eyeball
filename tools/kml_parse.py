import re,sys,json,math,datetime as dt
src=sys.argv[1]; s=open(src,encoding='utf-8').read()
whens=re.findall(r'<when>([^<]+)</when>',s); coords=re.findall(r'<gx:coord>([^<]+)</gx:coord>',s)
arrays=re.findall(r'<gx:SimpleArrayData name="(\w+)">(.*?)</gx:SimpleArrayData>',s,re.S)
A={n:[float(x) for x in re.findall(r'<gx:value>([^<]+)</gx:value>',b)] for n,b in arrays}
pts=[]
for w,c in zip(whens,coords):
    lon,lat,alt=map(float,c.split()); t=dt.datetime.fromisoformat(w.replace("Z","+00:00")); pts.append([t,lat,lon,alt])
print("points",len(pts),"speed",len(A.get("speed",[])),"heading",len(A.get("heading",[])))
alts=[p[3] for p in pts]; import statistics
# altitude anomaly scan: compare each point to the median of +-20 neighbours
bad=[]
for i in range(len(pts)):
    win=alts[max(0,i-20):i]+alts[i+1:i+21]; med=statistics.median(win)
    if abs(alts[i]-med)>120: bad.append(i)
# group runs
runs=[]; 
for i in bad:
    if runs and i==runs[-1][1]+1: runs[-1][1]=i
    else: runs.append([i,i])
print("anomalous points",len(bad),"runs",[(a,b,pts[a][0].strftime('%H:%M:%S'),round(alts[a]*3.28084),round(statistics.median(alts[max(0,a-20):a])*3.28084)) for a,b in runs])
imax=max(range(len(alts)),key=lambda i:alts[i]); print("peak",round(alts[imax]*3.28084),"ft MSL at",pts[imax][0].strftime('%H:%M:%SZ'))
json.dump({"pts":[[p[0].isoformat(),p[1],p[2],p[3]] for p in pts],"speed":A.get("speed",[]),"heading":A.get("heading",[]),"runs":runs},open(sys.argv[2],"w"))
