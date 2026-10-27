"""Decode raw METAR/SPECI strings into typed columns. Usage: metar_columns.py in.csv out.csv [out.xlsx]
Input: IEM CSV with columns station,valid,metar. Each code group lands in its own column; anything not
recognised goes to 'unparsed'. Units: wind kt, vis SM, heights ft AGL, temps C, altimeter inHg, SLP hPa."""
import csv,re,sys,datetime as dt
from zoneinfo import ZoneInfo
TZ=ZoneInfo("America/Indiana/Indianapolis")
WX_RE=re.compile(r'^([-+]|VC)?(?:(MI|PR|BC|DR|BL|SH|TS|FZ)?((?:DZ|RA|SN|SG|IC|PL|GR|GS|UP)+|BR|FG|FU|VA|DU|SA|HZ|PY|PO|SQ|FC|SS|DS)|(TS|SH|FG|BLSN|BLDU|BLSA|PO|DS|SS|FC))$')
CLD_RE=re.compile(r'^(FEW|SCT|BKN|OVC|VV|CLR|SKC|NSC|NCD)(\d{3}|///)?(CB|TCU|///)?$')
def frac(s):
    neg=s.startswith("M"); s=s.lstrip("M")
    if "/" in s:
        a,b=s.split("/"); v=int(a)/int(b)
    else: v=float(s)
    return v-0.01 if neg else v
def cat(ceil,vis):
    if ceil is None and vis is None: return ""
    c=ceil if ceil is not None else 99999; v=vis if vis is not None else 99
    if c<500 or v<1: return "LIFR"
    if c<1000 or v<3: return "IFR"
    if c<=3000 or v<=5: return "MVFR"
    return "VFR"
COLS=["station","report_type","obs_utc","obs_local","day","time_z","auto","cor","wind_dir","wind_dir_variable","wind_kt","gust_kt","wind_var_from","wind_var_to","wind_calm","vis_sm","vis_lt","rvr","wx1","wx2","wx3","cloud1_cover","cloud1_ft","cloud1_type","cloud2_cover","cloud2_ft","cloud2_type","cloud3_cover","cloud3_ft","cloud3_type","cloud4_cover","cloud4_ft","cloud4_type","sky_clear","ceiling_ft","temp_c","dewpoint_c","altimeter_inhg","flight_category","rmk_sensor","rmk_slp_hpa","rmk_temp_c","rmk_dewpoint_c","rmk_peak_wind_dir","rmk_peak_wind_kt","rmk_peak_wind_time","rmk_wind_shift_time","rmk_wshft_frontal","rmk_precip_1h_in","rmk_precip_3h_in","rmk_precip_6h_in","rmk_precip_24h_in","rmk_ptend_code","rmk_ptend_hpa","rmk_max6h_c","rmk_min6h_c","rmk_max24h_c","rmk_min24h_c","rmk_tower_vis","rmk_sfc_vis","rmk_vis_var","rmk_lightning","rmk_tsb","rmk_tse","rmk_rab","rmk_rae","rmk_snb","rmk_sne","rmk_ceiling_var","rmk_sky_var","rmk_pressure_trend","rmk_sensor_status","rmk_maint","rmk_other","unparsed","raw"]
def decode(valid,raw):
    o={k:"" for k in COLS}; o["raw"]=raw
    toks=raw.split(); i=0; un=[]
    if toks and toks[0] in ("METAR","SPECI"): o["report_type"]=toks[0]; i+=1
    if i<len(toks) and re.fullmatch(r'[A-Z][A-Z0-9]{3}',toks[i]): o["station"]=toks[i]; i+=1
    if i<len(toks) and re.fullmatch(r'\d{6}Z',toks[i]): o["day"]=int(toks[i][:2]); o["time_z"]=toks[i][2:4]+":"+toks[i][4:6]; i+=1
    t=dt.datetime.strptime(valid,"%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc); o["obs_utc"]=t.strftime("%Y-%m-%d %H:%M"); o["obs_local"]=t.astimezone(TZ).strftime("%Y-%m-%d %H:%M")
    if not o["report_type"]: o["report_type"]="SPECI" if t.minute not in (53,54,55,56) and False else ""  # IEM strips the type; see note in report
    body=[]; rmk=[]; inr=False
    for tk in toks[i:]:
        if tk=="RMK": inr=True; continue
        (rmk if inr else body).append(tk)
    clouds=[]; wx=[]; j=0
    while j<len(body):
        tk=body[j]; j+=1
        if tk=="AUTO": o["auto"]="Y"; continue
        if tk=="COR": o["cor"]="Y"; continue
        m=re.fullmatch(r'(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?KT',tk)
        if m:
            o["wind_dir"]="" if m.group(1)=="VRB" else int(m.group(1)); o["wind_dir_variable"]="Y" if m.group(1)=="VRB" else ""; o["wind_kt"]=int(m.group(2)); o["gust_kt"]=int(m.group(3)) if m.group(3) else ""
            if m.group(1)=="000" and int(m.group(2))==0: o["wind_calm"]="Y"
            continue
        m=re.fullmatch(r'(\d{3})V(\d{3})',tk)
        if m: o["wind_var_from"]=int(m.group(1)); o["wind_var_to"]=int(m.group(2)); continue
        if re.fullmatch(r'\d{1,2}',tk) and j<len(body) and re.fullmatch(r'M?\d/\dSM',body[j]):
            v=int(tk)+frac(body[j].replace("SM","")); o["vis_sm"]=round(v,2); j+=1; continue
        m=re.fullmatch(r'(M?)(\d+(?:/\d+)?)SM',tk)
        if m: o["vis_sm"]=round(frac(m.group(1)+m.group(2)),2); o["vis_lt"]="Y" if m.group(1) else ""; continue
        if re.fullmatch(r'R\d{2}[LRC]?/[MP]?\d{4}(V[MP]?\d{4})?FT',tk): o["rvr"]=(o["rvr"]+" "+tk).strip(); continue
        m=CLD_RE.match(tk)
        if m:
            if m.group(1) in ("CLR","SKC","NSC","NCD"): o["sky_clear"]=m.group(1)
            else: clouds.append((m.group(1),int(m.group(2))*100 if m.group(2) and m.group(2)!="///" else "",m.group(3) if m.group(3) and m.group(3)!="///" else ""))
            continue
        m=re.fullmatch(r'(M?\d{2})/(M?\d{2})?',tk)
        if m: o["temp_c"]=int(m.group(1).replace("M","-")); o["dewpoint_c"]=int(m.group(2).replace("M","-")) if m.group(2) else ""; continue
        m=re.fullmatch(r'A(\d{4})',tk)
        if m: o["altimeter_inhg"]=int(m.group(1))/100; continue
        if WX_RE.match(tk): wx.append(tk); continue
        if tk in ("RMK","$","NOSIG","TEMPO","BECMG"): continue
        un.append(tk)
    for k,w in enumerate(wx[:3]): o[f"wx{k+1}"]=w
    ceil=None
    for k,(cv,h,ty) in enumerate(clouds[:4]):
        o[f"cloud{k+1}_cover"]=cv; o[f"cloud{k+1}_ft"]=h; o[f"cloud{k+1}_type"]=ty
    for cv,h,ty in clouds:
        if cv in ("BKN","OVC","VV") and h!="" and (ceil is None or h<ceil): ceil=h
    o["ceiling_ft"]=ceil if ceil is not None else ""
    o["flight_category"]=cat(ceil if ceil is not None else None, o["vis_sm"] if o["vis_sm"]!="" else None)
    # remarks
    other=[]; k=0
    def sgn(s): return (-1 if s[0]=="1" else 1)*int(s[1:])/10
    while k<len(rmk):
        tk=rmk[k]; k+=1
        if tk in ("AO1","AO2"): o["rmk_sensor"]=tk; continue
        m=re.fullmatch(r'SLP(\d{3})',tk)
        if m: v=int(m.group(1))/10; o["rmk_slp_hpa"]=round(1000+v if v<50 else 900+v,1); continue
        if tk=="SLPNO": o["rmk_slp_hpa"]="SLPNO"; continue
        m=re.fullmatch(r'T([01]\d{3})([01]\d{3})?',tk)
        if m: o["rmk_temp_c"]=sgn(m.group(1)); o["rmk_dewpoint_c"]=sgn(m.group(2)) if m.group(2) else ""; continue
        m=re.fullmatch(r'PK',tk)
        if m and k+1<len(rmk) and rmk[k]=="WND":
            mm=re.fullmatch(r'(\d{3})(\d{2,3})/(\d{2}|\d{4})',rmk[k+1]) if k+1<len(rmk) else None
            if mm: o["rmk_peak_wind_dir"]=int(mm.group(1)); o["rmk_peak_wind_kt"]=int(mm.group(2)); o["rmk_peak_wind_time"]=mm.group(3); k+=2; continue
        if tk=="WSHFT" and k<len(rmk) and re.fullmatch(r'\d{2,4}',rmk[k]): o["rmk_wind_shift_time"]=rmk[k]; k+=1; 
        if tk=="WSHFT": 
            if k<len(rmk) and rmk[k]=="FROPA": o["rmk_wshft_frontal"]="Y"; k+=1
            continue
        m=re.fullmatch(r'P(\d{4})',tk)
        if m: o["rmk_precip_1h_in"]=int(m.group(1))/100; continue
        m=re.fullmatch(r'6(\d{4})',tk)
        if m: o["rmk_precip_6h_in"]=int(m.group(1))/100; continue   # 3- or 6-hourly group (same code); column named 6h
        m=re.fullmatch(r'7(\d{4})',tk)
        if m: o["rmk_precip_24h_in"]=int(m.group(1))/100; continue
        m=re.fullmatch(r'5(\d)(\d{3})',tk)
        if m: o["rmk_ptend_code"]=int(m.group(1)); o["rmk_ptend_hpa"]=(-1 if int(m.group(1))>=5 else 1)*int(m.group(2))/10; continue
        m=re.fullmatch(r'1([01]\d{3})',tk)
        if m: o["rmk_max6h_c"]=sgn(m.group(1)); continue
        m=re.fullmatch(r'2([01]\d{3})',tk)
        if m: o["rmk_min6h_c"]=sgn(m.group(1)); continue
        m=re.fullmatch(r'4([01]\d{3})([01]\d{3})',tk)
        if m: o["rmk_max24h_c"]=sgn(m.group(1)); o["rmk_min24h_c"]=sgn(m.group(2)); continue
        if tk=="TWR" and k+1<len(rmk) and rmk[k]=="VIS": o["rmk_tower_vis"]=rmk[k+1]; k+=2; continue
        if tk=="SFC" and k+1<len(rmk) and rmk[k]=="VIS": o["rmk_sfc_vis"]=rmk[k+1]; k+=2; continue
        if tk=="VIS" and k<len(rmk):
            seg=[]
            while k<len(rmk) and re.fullmatch(r'[\d/]+(V[\d/]+)?',rmk[k]): seg.append(rmk[k]); k+=1
            if seg and any("V" in x for x in seg): o["rmk_vis_var"]=" ".join(seg); continue
            other.append("VIS"); other.extend(seg); continue
        if tk in ("PRESFR","PRESRR"): o["rmk_pressure_trend"]=tk; continue
        m=re.fullmatch(r'(FEW|SCT|BKN|OVC)(\d{3})?',tk)
        if m and k+1<len(rmk) and rmk[k]=="V" and re.fullmatch(r'(FEW|SCT|BKN|OVC)',rmk[k+1]): o["rmk_sky_var"]=(o["rmk_sky_var"]+" "+tk+" V "+rmk[k+1]).strip(); k+=2; continue
        if tk=="CIG" and k<len(rmk) and re.fullmatch(r'\d{3}V\d{3}',rmk[k]): o["rmk_ceiling_var"]=rmk[k]; k+=1; continue
        if tk in ("LTG","OCNL","FRQ","CONS","TS","TSRA","CB","TCU") or tk.startswith("LTG"):
            seg=[tk]
            while k<len(rmk) and re.fullmatch(r'(LTG[A-Z]*|DSNT|OHD|VC|ALQDS|[NSEW]{1,2}(-[NSEW]{1,2})?|-|AND|OCNL|FRQ|CONS|TS|MOV|MOVG|STNRY|THRU)',rmk[k]): seg.append(rmk[k]); k+=1
            o["rmk_lightning"]=(o["rmk_lightning"]+" "+" ".join(seg)).strip(); continue
        m=re.fullmatch(r'(TS|RA|SN|DZ|FZRA|PL|GR|SHRA|SHSN|UP|FZDZ)(B|E)(\d{2,4})((?:B|E)\d{2,4})*',tk)
        if m:
            for mm in re.finditer(r'(B|E)(\d{2,4})',tk[len(m.group(1)):]):
                key={"TS":"ts","RA":"ra","SN":"sn","SHRA":"ra","SHSN":"sn","DZ":"ra","FZRA":"ra","PL":"sn","GR":"ra","UP":"ra","FZDZ":"ra"}[m.group(1)]+("b" if mm.group(1)=="B" else "e")
                o["rmk_"+key]=(o["rmk_"+key]+" "+mm.group(2)).strip()
            continue
        if tk in ("RVRNO","PWINO","PNO","FZRANO","TSNO","VISNO","CHINO","$"): o["rmk_sensor_status"]=(o["rmk_sensor_status"]+" "+tk).strip(); continue
        if tk=="$": o["rmk_maint"]="Y"; continue
        other.append(tk)
    o["rmk_other"]=" ".join(other); o["unparsed"]=" ".join(un)
    return o
rows=[]
with open(sys.argv[1],newline='') as f:
    for r in csv.DictReader(f):
        if not r["metar"].startswith("K"): continue
        rows.append(decode(r["valid"],r["metar"]))
rows.sort(key=lambda o:o["obs_utc"])
# report type: IEM strips METAR/SPECI; infer: routine obs at the station's standard minute (:53 at KMQJ -> check mode)
from collections import Counter
mins=Counter(o["obs_utc"][-2:] for o in rows); std={m for m,c in mins.items() if c>=0.1*len(rows)}
for o in rows:
    if not o["report_type"]: o["report_type"]="ROUTINE" if o["obs_utc"][-2:] in std else "SPECI"
print("routine minutes:",sorted(std))
with open(sys.argv[2],"w",newline='') as f:
    w=csv.DictWriter(f,fieldnames=COLS); w.writeheader(); w.writerows(rows)
print("rows",len(rows),"routine minutes",sorted(std),"unparsed tokens in",sum(1 for o in rows if o["unparsed"]),"rows; rmk_other in",sum(1 for o in rows if o["rmk_other"]))
if len(sys.argv)>3:
    from openpyxl import Workbook; from openpyxl.utils import get_column_letter
    wb=Workbook(); ws=wb.active; ws.title="KMQJ obs"; ws.append(COLS)
    for o in rows: ws.append([o[c] for c in COLS])
    ws.freeze_panes="C2"; ws.auto_filter.ref=ws.dimensions
    for i,c in enumerate(COLS,1): ws.column_dimensions[get_column_letter(i)].width=min(40,max(8,len(c)+2))
    ws.column_dimensions[get_column_letter(len(COLS))].width=90
    wb.save(sys.argv[3]); print("xlsx ok")
