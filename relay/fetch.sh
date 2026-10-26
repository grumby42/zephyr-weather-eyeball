#!/usr/bin/env bash
# Zephyr relay: pull official aviationweather.gov products server-side (the browser cannot: CORS) and publish
# data/latest.json for the app. Every product is fetched independently; failures are recorded, not fatal.
set -u
CFG=relay/config.json; OUT=data/latest.json; UA="zephyr-weather-eyeball-relay (github.com/grumby42/zephyr-weather-eyeball)"
ST=$(jq -r '.stations|join(",")' $CFG); PS=$(jq -r '.pirep_station' $CFG); PNM=$(jq -r '.pirep_nm' $CFG); PAGE=$(jq -r '.pirep_age_h' $CFG); REG=$(jq -r '.fb_region' $CFG); MH=$(jq -r '.metar_hours' $CFG)
B=https://aviationweather.gov/api/data
declare -A URLS=(
  [metar]="$B/metar?ids=$ST&format=json&hours=$MH"
  [taf]="$B/taf?ids=$ST&format=json"
  [pirep]="$B/pirep?id=$PS&distance=$PNM&age=$PAGE&format=raw"
  [gairmet]="$B/gairmet?format=json"
  [airsigmet]="$B/airsigmet?format=json"
  [windtemp]="$B/windtemp?region=$REG&level=low&fcst=06"
)
TMP=$(mktemp -d); NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "{\"generated\":\"$NOW\",\"stations\":$(jq -c '.stations' $CFG),\"pirep_station\":\"$PS\",\"pirep_nm\":$PNM,\"fb_region\":\"$REG\",\"products\":{" > $TMP/out.json
first=1
for k in metar taf pirep gairmet airsigmet windtemp; do
  u="${URLS[$k]}"; code=$(curl -sS -m 40 -A "$UA" -o "$TMP/$k.body" -w "%{http_code}" "$u" 2>"$TMP/$k.err" || echo "000")
  [ $first -eq 1 ] || echo "," >> $TMP/out.json; first=0
  if [ "$code" = "200" ] && [ -s "$TMP/$k.body" ]; then
    if jq -e . "$TMP/$k.body" >/dev/null 2>&1; then body=$(jq -c . "$TMP/$k.body"); kind=json; else body=$(jq -Rs . "$TMP/$k.body"); kind=text; fi
    echo "\"$k\":{\"ok\":true,\"kind\":\"$kind\",\"http\":$code,\"fetched\":\"$NOW\",\"url\":$(jq -Rn --arg u "$u" '$u'),\"body\":$body}" >> $TMP/out.json
  else
    echo "\"$k\":{\"ok\":false,\"http\":\"$code\",\"fetched\":\"$NOW\",\"url\":$(jq -Rn --arg u "$u" '$u'),\"error\":$(jq -Rs . "$TMP/$k.err")}" >> $TMP/out.json
  fi
done
echo "}}" >> $TMP/out.json
jq . $TMP/out.json > $OUT && echo "wrote $OUT ($(wc -c < $OUT) bytes)"
