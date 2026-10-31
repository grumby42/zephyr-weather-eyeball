/* Zephyr Weather Eyeball service worker. CACHE name is stamped per build by the build script. */
const CACHE="zephyr-b356";
const SHELL=["./","./index.html","./zephyr-weather-eyeball.html","./manifest.webmanifest","./icons/icon-192.png","./icons/icon-512.png"];
const TILE_HOSTS=["server.arcgisonline.com","tilecache.rainviewer.com","raw.githubusercontent.com"];
const TILE_CACHE="zephyr-tiles-v1", TILE_MAX=600;
self.addEventListener("install",e=>{ e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())); });
self.addEventListener("activate",e=>{ e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith("zephyr-b")&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())); });
self.addEventListener("message",e=>{ if(e.data==="skipWaiting")self.skipWaiting(); });
async function trimTiles(){ const c=await caches.open(TILE_CACHE); const keys=await c.keys(); if(keys.length>TILE_MAX){ for(const k of keys.slice(0,keys.length-TILE_MAX))await c.delete(k); } }
self.addEventListener("fetch",e=>{
  const req=e.request; if(req.method!=="GET")return; const url=new URL(req.url);
  if(url.origin===self.location.origin){ // app shell: network first so a new build shows up, cache fallback for offline
    e.respondWith(fetch(req).then(r=>{ const copy=r.clone(); caches.open(CACHE).then(c=>c.put(req,copy)); return r; }).catch(()=>caches.match(req,{ignoreSearch:true}).then(r=>r||caches.match("./zephyr-weather-eyeball.html")))); return; }
  if(TILE_HOSTS.includes(url.host)){ // tiles + static data: cache first, fill from network, bounded
    e.respondWith(caches.open(TILE_CACHE).then(async c=>{ const hit=await c.match(req); if(hit)return hit; try{ const r=await fetch(req); if(r.ok){ c.put(req,r.clone()); trimTiles(); } return r; }catch(err){ return hit||Response.error(); } })); return; }
  // weather APIs: network only — the page keeps its own last-forecast cache and labels it stale
});
