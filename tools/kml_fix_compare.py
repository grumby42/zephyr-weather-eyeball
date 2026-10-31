import json,sys,math,statistics,csv,re,datetime as dt
SP=sys.argv[1]; d=json.load(open(SP+"/kml/track.json")); P=d["pts"]; N=len(P)
T=[dt.datetime.fromisoformat(p[0]) for p in P]; lat=[p[1] for p in P]; lon=[p[2] for p in P]; alt=[p[3] for p in P]
# --- repair: (1) stuck-value plateaus: constant altitude (<0.5 m change) for >=5 consecutive fixes that sit >=100 m
# away from the good value just before the run; (2) isolated spikes: a point >100 m from BOTH neighbours while the
# neighbours agree with each other within 60 m. Everything else is trusted (the peak is real).
bad=[False]*N
i=0
while i<N:
    j=i
    while j+1<N and abs(alt[j+1]-alt[i])<0.5: j+=1
    if j-i+1>=5:
        before=alt[i-1] if i>0 else None; after=alt[j+1] if j+1<N else None
        ref=before if before is not None else after
        if ref is not None and abs(alt[i]-ref)>100:
            for k in range(i,j+1): bad[k]=True
    i=j+1
i=1
while i<N-1:  # short glitch runs (1-4 fixes) that jump >100 m away from both sides while the sides agree within 60 m
    if not bad[i]:
        j=i
        while j+1<N-1 and abs(alt[j+1]-alt[i])<0.5 and j-i<3: j+=1
        if abs(alt[i]-alt[i-1])>100 and abs(alt[j]-alt[j+1])>100 and abs(alt[j+1]-alt[i-1])<60:
            for k in range(i,j+1): bad[k]=True
        i=j+1
    else: i+=1
# plateaus are often bracketed by 1-2 transition points that are also wrong: extend a run while the point is >100 m from the far-side good value
for _ in range(3):
    for i in range(1,N-1):
        if bad[i] and not bad[i-1] and i-2>=0 and abs(alt[i-1]-alt[i-2])>100: bad[i-1]=True
        if bad[i] and not bad[i+1] and i+2<N and abs(alt[i+1]-alt[i+2])>100: bad[i+1]=True
fixed=alt[:]; runs=[]; i=0
while i<N:
    if bad[i]:
        j=i
        while j+1<N and bad[j+1]: j+=1
        a=i-1; b=j+1
        while a>=0 and bad[a]: a-=1
        while b<N and bad[b]: b+=1
        if a>=0 and b<N:
            for k in range(i,j+1):
                f=(T[k]-T[a]).total_seconds()/((T[b]-T[a]).total_seconds() or 1); fixed[k]=alt[a]+f*(alt[b]-alt[a])
        runs.append((i,j,T[i].strftime("%H:%M:%S"),T[j].strftime("%H:%M:%S"),round(alt[i]*3.28084),round(fixed[i]*3.28084),round(fixed[j]*3.28084)))
        i=j+1
    else: i+=1
print("repaired runs:"); [print("  ",r) for r in runs]
# --- cleaned KML
src=open(SP+"/kml/flight.kml",encoding="utf-8").read()
coords=re.findall(r'<gx:coord>([^<]+)</gx:coord>',src); assert len(coords)==N
out=src; k=0
def repl(m):
    global k; lo,la,_=m.group(1).split(); s=f"<gx:coord>{lo} {la} {fixed[k]:.4f}</gx:coord>"; k+=1; return s
out=re.sub(r'<gx:coord>([^<]+)</gx:coord>',repl,out)
out=out.replace("<name>Flight Oct 31, 2026</name>","<name>Flight Oct 31, 2026 (altitude repaired)</name>")
open(sys.argv[2]+"/flight_2026-10-31_repaired.kml","w",encoding="utf-8").write(out)
# --- comparison with the 12Z forecast hodograph (AGL ft, from deg, kt)
FC=[(0,21,2),(300,118,8),(500,125,15),(1000,135,23),(1500,146,26),(2000,158,23),(2500,170,19),(3000,182,15),(3500,187,13),(4000,195,11),(4500,207,9),(5000,220,7),(5500,236,7),(6000,254,7)]
def fc_uv(agl):
    agl=max(0,min(6000,agl))
    for i in range(len(FC)-1):
        a,b=FC[i],FC[i+1]
        if a[0]<=agl<=b[0]:
            f=(agl-a[0])/(b[0]-a[0]); 
            def uv(x): r=math.radians(x[1]); return (-x[2]*math.sin(r),-x[2]*math.cos(r))
            ua,va=uv(a); ub,vb=uv(b); return (ua+f*(ub-ua), va+f*(vb-va))
    r=math.radians(FC[-1][1]); return (-FC[-1][2]*math.sin(r),-FC[-1][2]*math.cos(r))
ELEV_FT=alt[0]*3.28084  # launch GPS altitude as field elevation (flat terrain; see note)
def hav(la1,lo1,la2,lo2):
    R=3440.065; p=math.pi/180; dl=(la2-la1)*p; dn=(lo2-lo1)*p; a=math.sin(dl/2)**2+math.cos(la1*p)*math.cos(la2*p)*math.sin(dn/2)**2; return 2*R*math.asin(math.sqrt(a))
def brg(la1,lo1,la2,lo2):
    p=math.pi/180; y=math.sin((lo2-lo1)*p)*math.cos(la2*p); x=math.cos(la1*p)*math.sin(la2*p)-math.sin(la1*p)*math.cos(la2*p)*math.cos((lo2-lo1)*p); return (math.degrees(math.atan2(y,x))+360)%360
rows=[]; t0=T[0]; i=0
while i<N-1:
    j=i
    while j<N-1 and (T[j+1]-T[i]).total_seconds()<60: j+=1
    if j==i: i+=1; continue
    dist=hav(lat[i],lon[i],lat[j],lon[j]); secs=(T[j]-T[i]).total_seconds(); spd=dist/secs*3600; trk=brg(lat[i],lon[i],lat[j],lon[j])
    msl=statistics.mean(fixed[i:j+1])*3.28084; agl=msl-ELEV_FT
    u,v=fc_uv(agl); fspd=math.hypot(u,v); fto=(math.degrees(math.atan2(u,v))+360)%360
    derr=((trk-fto+540)%360)-180
    rows.append({"utc":T[i].strftime("%H:%M")+"Z","min":round((T[i]-t0).total_seconds()/60),"msl_ft":round(msl),"agl_ft":round(agl),"actual_track_deg":round(trk),"actual_gs_kt":round(spd,1),"fc_to_deg":round(fto),"fc_kt":round(fspd,1),"dir_err_deg":round(derr),"spd_err_kt":round(spd-fspd,1)})
    i=j+1
with open(sys.argv[2]+"/flight_2026-10-31_forecast_vs_actual.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
# layer summary (500-ft AGL bins), ignore first/last 2 min (launch/landing manoeuvring) and slow (<4 kt) bins for direction
from collections import defaultdict
L=defaultdict(list)
for r in rows[2:-2]: L[int(r["agl_ft"]//500)*500].append(r)
print("\nlayer  n  actual gs  fc kt  spd err   actual trk  fc to   dir err(mean|abs)")
for k in sorted(L):
    rs=L[k]; sp=statistics.mean(r["actual_gs_kt"] for r in rs); fs=statistics.mean(r["fc_kt"] for r in rs)
    rd=[r for r in rs if r["actual_gs_kt"]>=4]; de=[r["dir_err_deg"] for r in rd]
    cm=lambda xs:(math.degrees(math.atan2(sum(math.sin(math.radians(x)) for x in xs),sum(math.cos(math.radians(x)) for x in xs)))+360)%360 if xs else float('nan')
    print(f"{k:>5}-{k+499:<5} {len(rs):>2}   {sp:5.1f}     {fs:5.1f}   {sp-fs:+5.1f}      {cm([r['actual_track_deg'] for r in rd]):5.0f}     {cm([r['fc_to_deg'] for r in rd]):5.0f}    {statistics.mean(de) if de else float('nan'):+4.0f} | {statistics.mean(abs(x) for x in de) if de else float('nan'):3.0f}")
allr=rows[2:-2]; print("\noverall: mean |dir err|",round(statistics.mean(abs(r["dir_err_deg"]) for r in allr if r["actual_gs_kt"]>=4)),"deg; mean spd err",round(statistics.mean(r["spd_err_kt"] for r in allr),1),"kt; mean |spd err|",round(statistics.mean(abs(r["spd_err_kt"]) for r in allr),1),"kt")
print("launch",lat[0],lon[0],"land",lat[-1],lon[-1],"crow",round(hav(lat[0],lon[0],lat[-1],lon[-1]),1),"nm brg",round(brg(lat[0],lon[0],lat[-1],lon[-1])),"max repaired alt",round(max(fixed)*3.28084),"ft MSL")
json.dump({"rows":rows,"fixed_ft":[round(x*3.28084) for x in fixed],"t":[t.strftime("%H:%M:%S") for t in T],"spd":[s*1.944 for s in d["speed"]]},open(SP+"/kml/cmp.json","w"))
