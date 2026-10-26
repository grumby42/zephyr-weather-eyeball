import csv,re,sys,math,datetime as dt
from zoneinfo import ZoneInfo
src=sys.argv[1]; out=sys.argv[2]
TZ=ZoneInfo("America/Indiana/Indianapolis"); LAT,LON=39.8345,-85.8970  # KMQJ Indianapolis Regional
def vis_sm(toks):
    for i,t in enumerate(toks):
        m=re.match(r'^(M)?(\d+)?(?:\s)?(\d)/(\d)SM$',t)
        if t.endswith("SM"):
            s=t[:-2]; neg=s.startswith("M"); s=s.lstrip("M")
            if "/" in s:
                a,b=s.split("/"); v=int(a)/int(b)
                if i>0 and re.fullmatch(r'\d+',toks[i-1]): v+=int(toks[i-1])
            else:
                try: v=float(s)
                except: continue
            return v-0.01 if neg else v
    return None
def ceiling(toks):
    c=None
    for t in toks:
        m=re.match(r'^(BKN|OVC|VV)(\d{3})',t)
        if m:
            h=int(m.group(2))*100
            if c is None or h<c: c=h
    return c
def cat(ceil,vis):
    if ceil is None and vis is None: return None
    c=ceil if ceil is not None else 99999; v=vis if vis is not None else 99
    if c<500 or v<1: return "LIFR"
    if c<1000 or v<3: return "IFR"
    if c<=3000 or v<=5: return "MVFR"
    return "VFR"
def solar(date):  # NOAA sunrise/sunset in UTC for LAT/LON
    n=date.toordinal()-dt.date(2000,1,1).toordinal()+0.5
    def ev(rise):
        lw=-LON; t=n-lw/360
        M=(357.5291+0.98560028*t)%360; C=1.9148*math.sin(math.radians(M))+0.02*math.sin(math.radians(2*M))+0.0003*math.sin(math.radians(3*M))
        L=(M+C+180+102.9372)%360; Jt=2451545+t+0.0053*math.sin(math.radians(M))-0.0069*math.sin(math.radians(2*L))
        d=math.degrees(math.asin(math.sin(math.radians(L))*math.sin(math.radians(23.4397))))
        cosw=(math.sin(math.radians(-0.833))-math.sin(math.radians(LAT))*math.sin(math.radians(d)))/(math.cos(math.radians(LAT))*math.cos(math.radians(d)))
        w=math.degrees(math.acos(max(-1,min(1,cosw)))); J=Jt+(w if not rise else -w)/360
        return dt.datetime(2000,1,1,12,tzinfo=dt.timezone.utc)+dt.timedelta(days=J-2451545)
    return ev(True),ev(False)
rows=[]
with open(src,newline='') as f:
    for r in csv.DictReader(f):
        m=r["metar"].split(); 
        if not m or m[0]!="KMQJ": continue
        t=dt.datetime.strptime(r["valid"],"%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)
        toks=m[2:]; v=vis_sm(toks); c=ceiling(toks); k=cat(c,v)
        rows.append((t,v,c,k,"SPECI" if (len(m)>3 and "RMK" in m and False) else "",r["metar"]))
rows.sort(key=lambda x:x[0])
# per-ob csv
with open(out+"/KMQJ-obs-classified.csv","w",newline='') as f:
    w=csv.writer(f); w.writerow(["utc","local","vis_sm","ceiling_ft","category","metar"])
    for t,v,c,k,sp,raw in rows: w.writerow([t.strftime("%Y-%m-%d %H:%MZ"),t.astimezone(TZ).strftime("%Y-%m-%d %H:%M"),"" if v is None else round(v,2),"" if c is None else c,k or "",raw])
# daily rollup: daylight (sunrise..sunset local) windows of continuous VFR; an ob holds until the next ob
from collections import defaultdict
days=defaultdict(list)
for i,(t,v,c,k,sp,raw) in enumerate(rows):
    t2=rows[i+1][0] if i+1<len(rows) else t+dt.timedelta(minutes=20)
    days[t.astimezone(TZ).date()].append((t,min(t2,t+dt.timedelta(hours=2)),k))
with open(out+"/KMQJ-daily-vfr.csv","w",newline='') as f:
    w=csv.writer(f); w.writerow(["date_local","weekday","sunrise_local","sunset_local","obs","daylight_vfr_pct","daylight_mvfr_pct","daylight_ifr_lifr_pct","all_day_vfr","longest_daylight_vfr_window_local","longest_vfr_window_h","vfr_windows_ge_2h"])
    for d in sorted(days):
        sr,ss=solar(d); segs=days[d]; day_s=sr; day_e=ss
        tot={"VFR":0,"MVFR":0,"IFR":0,"LIFR":0}; wins=[]; cur=None
        for a,b,k in segs:
            a2=max(a,day_s); b2=min(b,day_e)
            if b2<=a2: continue
            if k: tot[k]+=(b2-a2).total_seconds()
            if k=="VFR":
                if cur and (a2-cur[1]).total_seconds()<=1800: cur[1]=b2
                else:
                    if cur: wins.append(cur)
                    cur=[a2,b2]
            else:
                if cur: wins.append(cur); cur=None
        if cur: wins.append(cur)
        T=sum(tot.values()) or 1; best=max(wins,key=lambda w:(w[1]-w[0]).total_seconds()) if wins else None
        allvfr=all(k=="VFR" for a,b,k in segs if k)
        w.writerow([d.isoformat(),d.strftime("%a"),sr.astimezone(TZ).strftime("%H:%M"),ss.astimezone(TZ).strftime("%H:%M"),len(segs),round(100*tot["VFR"]/T),round(100*tot["MVFR"]/T),round(100*(tot["IFR"]+tot["LIFR"])/T),"Y" if allvfr else "",(best[0].astimezone(TZ).strftime("%H:%M")+"-"+best[1].astimezone(TZ).strftime("%H:%M")) if best else "",round((best[1]-best[0]).total_seconds()/3600,1) if best else 0,sum(1 for a,b in wins if (b-a).total_seconds()>=7200)])
n=len(rows); from collections import Counter; C=Counter(k for *_,k,sp,raw in rows)
print("obs",n,"first",rows[0][0],"last",rows[-1][0]); print("category share (all obs):",{k:round(100*C[k]/n,1) for k in ("VFR","MVFR","IFR","LIFR")},"unclassified",C[None])
