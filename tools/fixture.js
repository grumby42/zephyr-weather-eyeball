// synthetic Open-Meteo hourly fixture: 72 h from today 00Z, every variable fetchOM requests
function makeFixture(){
  const LV=[1000,975,950,925,900,850,800,750,700], GH={1000:110,975:320,950:540,925:760,900:990,850:1460,800:1950,750:2470,700:3010};
  const t0=new Date(); t0.setUTCHours(0,0,0,0); const N=72, time=[]; for(let i=0;i<N;i++){const d=new Date(t0.getTime()+i*3600000); time.push(d.toISOString().slice(0,16));}
  const H={time}; const s=(a,p,ph,off)=>Array.from({length:N},(_,i)=>off+a*Math.sin((i/p)*2*Math.PI+ph));
  const sfc=s(4,24,0,6).map((v,i)=>Math.max(1,v+(i%24>=14&&i%24<=22?4:0)));
  H.wind_speed_10m=sfc; H.wind_direction_10m=s(30,48,0,250); H.wind_gusts_10m=sfc.map(v=>v*1.6+2);
  H.wind_speed_80m=sfc.map(v=>v+3); H.wind_direction_80m=s(30,48,0.2,255); H.wind_speed_120m=sfc.map(v=>v+4); H.wind_direction_120m=s(30,48,0.3,258); H.wind_speed_180m=sfc.map(v=>v+5); H.wind_direction_180m=s(30,48,0.4,262);
  H.temperature_2m=s(7,24,-Math.PI/2,16); H.dew_point_2m=H.temperature_2m.map(v=>v-5); H.relative_humidity_2m=H.temperature_2m.map(()=>72);
  H.surface_pressure=s(2,36,0,985); H.boundary_layer_height=s(600,24,-Math.PI/2,700).map(v=>Math.max(80,v));
  H.cape=s(600,24,-Math.PI/2,700).map(v=>Math.max(0,v)); H.convective_inhibition=H.cape.map(c=>-(60-c/20)); H.visibility=H.time.map(()=>24000);
  H.precipitation=H.time.map((_,i)=>i%30===20?0.4:0); H.precipitation_probability=H.time.map((_,i)=>i%30>=18&&i%30<=22?40:8);
  H.cloud_cover=s(30,30,0,45).map(v=>Math.max(0,v)); H.cloud_cover_low=H.cloud_cover.map(v=>v*0.5); H.cloud_cover_mid=H.cloud_cover.map(v=>v*0.3); H.cloud_cover_high=H.cloud_cover.map(v=>v*0.6);
  H.weather_code=H.time.map((_,i)=>i%30===20?61:i%7===0?2:1); H.is_day=H.time.map(t=>{const h=+t.slice(11,13); return (h>=11&&h<=22)?1:0;});
  H.lifted_index=H.cape.map(c=>2-c/300); H.total_column_integrated_water_vapour=s(6,36,0,22);
  LV.forEach((l,k)=>{ H[`wind_speed_${l}hPa`]=sfc.map(v=>v+2+k*2.2); H[`wind_direction_${l}hPa`]=s(25,48,0.1*k,250+k*6); H[`geopotential_height_${l}hPa`]=H.time.map(()=>GH[l]); H[`cloud_cover_${l}hPa`]=H.cloud_cover.map(v=>Math.max(0,v-10+k*3)); H[`temperature_${l}hPa`]=H.temperature_2m.map(v=>v-(GH[l]-250)/1000*6.5+(k===1?1.5:0)); });
  return H;
}
module.exports={makeFixture};
