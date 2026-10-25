const { chromium } = require('playwright'); const {makeFixture}=require('./fixture.js'); const fs=require('fs');
(async()=>{ const file=process.argv[2], outDir=process.argv[3], width=+(process.argv[4]||420); fs.mkdirSync(outDir,{recursive:true});
  const b=await chromium.launch(); const ctx=await b.newContext({viewport:{width,height:900},deviceScaleFactor:1}); const pg=await ctx.newPage();
  await ctx.route('**/*',r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  const errs=[]; pg.on('pageerror',e=>errs.push(String(e.message).slice(0,200)));
  await pg.goto('file://'+file); await pg.waitForTimeout(1200);
  const H=makeFixture(); const when=H.time[15];
  const r=await pg.evaluate(({H,when})=>{ document.querySelector("#lat").value="40.105"; document.querySelector("#lon").value="-86.043"; document.querySelector("#when").value=when;
    try{ applyForecast(H,250,"",when,{}); }catch(e){ return "applyForecast: "+e.message; }
    try{ minsRerenderNow(); }catch(e){} try{ loadDriftMap(); }catch(e){}
    document.querySelectorAll("#sections>.panel[data-sect]").forEach(p=>{ try{setColl(p,false);}catch(e){} });
    return "ok"; },{H,when});
  await pg.waitForTimeout(1500);
  const ids=await pg.evaluate(()=>[...document.querySelectorAll('#sections>.panel[data-sect]')].filter(p=>getComputedStyle(p).display!=='none').map(p=>p.dataset.sect));
  for(const id of ids){ const el=await pg.$(`#sections>.panel[data-sect="${id}"]`); try{ await el.screenshot({path:`${outDir}/${id}.png`}); }catch(e){ errs.push(id+": "+e.message.slice(0,80)); } }
  console.log(JSON.stringify({applied:r,panels:ids.length,errs:errs.slice(0,8)})); await b.close(); })();
