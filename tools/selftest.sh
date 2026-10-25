#!/usr/bin/env bash
# Zephyr self-test: syntax, structure, headless smoke, populated-panel screenshots. Run from the repo root.
set -e
F=${1:-zephyr-weather-eyeball.html}
node -e "const s=require('fs').readFileSync('$F','utf8');const m=[...s.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)].filter(x=>!/src=/i.test(x[1])).map(x=>x[2]).sort((a,b)=>b.length-a.length)[0];require('fs').writeFileSync('/tmp/zephyr-main.js',m);const st=[...s.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/g)].map(x=>x[1]).join('');console.log('div',(s.match(/<div/g)||[]).length,(s.match(/<\/div>/g)||[]).length,'| braces',(st.match(/{/g)||[]).length,(st.match(/}/g)||[]).length,'| doctype',/^<!doctype html>/i.test(s));"
node --check /tmp/zephyr-main.js && echo "node --check: PASS"
node tools/smoke.js "$(realpath "$F")"
node tools/shots.js "$(realpath "$F")" /tmp/zephyr-shots 420 && echo "screenshots in /tmp/zephyr-shots"
