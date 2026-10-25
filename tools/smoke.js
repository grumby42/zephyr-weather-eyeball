const { chromium } = require('playwright');
(async()=>{
  const file=process.argv[2]; const b=await chromium.launch(); const ctx=await b.newContext({viewport:{width:1100,height:900}}); const pg=await ctx.newPage();
  await ctx.route('**/*',r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  const errs=[], cons=[]; pg.on('pageerror',e=>errs.push("pageerror: "+String(e.message).slice(0,200))); pg.on('console',m=>{ if(m.type()==='error')cons.push(m.text().slice(0,200)); });
  await pg.goto('file://'+file); await pg.waitForTimeout(2500);
  const r=await pg.evaluate(async()=>{
    const out={renderErrs:[], modes:[], misc:[]};
    const fns=Object.getOwnPropertyNames(window).filter(k=>/^render[A-Z]/.test(k)&&typeof window[k]==="function");
    for(const f of fns){ try{ window[f](); }catch(e){ out.renderErrs.push(f+": "+e.message); } }
    out.renderCount=fns.length;
    const ms=document.querySelector("#modeSel"); if(ms){ for(const v of ["airplane","xc","balloon"]){ ms.value=v; ms.dispatchEvent(new Event("change",{bubbles:true})); await new Promise(r=>setTimeout(r,250)); out.modes.push(v+":"+document.body.className.match(/m-\w+/)); } }
    try{ minsRerenderNow(); }catch(e){ out.misc.push("minsRerenderNow: "+e.message); }
    try{ verdict(); }catch(e){ out.misc.push("verdict: "+e.message); }
    try{ buildVisualGrid(); openTileModal("decision"); const inModal=!!document.querySelector("#vModal .panel.in-modal"); closeTileModal(); const restored=!!document.querySelector('#sections>.panel[data-sect="decision"]'); out.misc.push("tileModal ok="+(inModal&&restored)); }catch(e){ out.misc.push("tileModal: "+e.message); }
    try{ p4Signals("balloon"); p4Signals("airplane"); }catch(e){ out.misc.push("p4Signals: "+e.message); }
    try{ renderSigmets(); renderMin15(); renderNwsGrid(); }catch(e){ out.misc.push("newPanels: "+e.message); }
    out.panels=document.querySelectorAll("#sections>.panel[data-sect]").length; out.nestedPanels=[...document.querySelectorAll('.panel[data-sect]')].filter(p=>p.parentElement.id!=='sections'&&p.closest('#sections')).map(p=>p.dataset.sect); out.expectedPanels=(typeof DEFAULT_ORDER!=='undefined')?DEFAULT_ORDER.length:null; out.grips=document.querySelectorAll(".panel>h2 .pgrip").length;
    return out;
  });
  await pg.waitForTimeout(800);
  console.log(JSON.stringify({file:file.split('/').pop(), ...r, pageErrors:errs, consoleErrors:cons.filter(c=>!/ERR_FAILED|Failed to fetch|net::|Failed to load resource/.test(c)).slice(0,10)},null,1));
  await b.close();
})();
