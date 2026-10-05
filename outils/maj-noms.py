#!/usr/bin/env python3
"""Fetch station names and brands for Vienne and its neighbours into www/noms.json.

A station's département is the first two digits of its id, zero-padded to 8 digits.
OpenStreetMap is only used for stations the official site has no name for.
"""
import html, json, math, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "www", "noms.json")
# Vienne, Deux-Sèvres, Maine-et-Loire, Indre-et-Loire, Indre, Haute-Vienne, Charente
DEPARTEMENTS = {"86", "79", "49", "37", "36", "87", "16"}
EXPORT = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-instantane-v2/exports/json"
PDV = "https://www.prix-carburants.gouv.fr/map/recuperer_infos_pdv/{}"
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
OSM_MAX_M = 150
PAUSE_S = 0.5
UA = "carburants/1.0 (+https://carburants.matthv.com/)"


def log(*args):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *args, flush=True)


def get(url, timeout=20, **headers):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def stations():
    q = urllib.parse.urlencode({"select": "id,geom"})
    rows = json.loads(get(f"{EXPORT}?{q}", timeout=120))
    return {str(r["id"]): r["geom"] for r in rows
            if r.get("geom") and str(r["id"]).zfill(8)[:2] in DEPARTEMENTS}


def name_and_brand(pdv_id):
    text = html.unescape(re.sub(r"<[^>]+>", "\n", get(PDV.format(pdv_id), **{"X-Requested-With": "XMLHttpRequest"})))
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 2 or re.match(r"^\d{5}\b", lines[1]):
        return None
    return {"nom": lines[0], "marque": lines[1]}


def osm_fuel(live):
    lats = [g["lat"] for g in live.values()]
    lons = [g["lon"] for g in live.values()]
    bbox = f"{min(lats) - .01},{min(lons) - .01},{max(lats) + .01},{max(lons) + .01}"
    query = f'[out:json][timeout:120];nwr["amenity"="fuel"]({bbox});out tags center;'
    for attempt in range(3):
        for url in OVERPASS:
            try:
                req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": query}).encode(), headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=180) as r:
                    return json.load(r)["elements"]
            except Exception as e:
                log(f"overpass {url}: {e}")
        time.sleep(30)
    return []


def osm_match(pdv_id, geom, elements):
    def dist(e):
        lat, lon = e.get("lat") or e["center"]["lat"], e.get("lon") or e["center"]["lon"]
        dy = math.radians(lat - geom["lat"])
        dx = math.radians(lon - geom["lon"]) * math.cos(math.radians(geom["lat"]))
        return 6371000 * math.hypot(dx, dy)
    by_ref = [e for e in elements if e["tags"].get("ref:FR:prix-carburants") == pdv_id]
    near = sorted((e for e in elements if dist(e) <= OSM_MAX_M), key=dist)
    for e in by_ref + near:
        t = e["tags"]
        if t.get("name") or t.get("brand"):
            return {"nom": t.get("name") or t["brand"], "marque": t.get("brand", ""), "source": "osm"}
    return None


def main():
    try:
        old = json.load(open(OUT))
    except (OSError, ValueError):
        old = {}
    live = stations()
    log(f"{len(live)} stations in the selected départements")

    names, kept, missing = {}, 0, []
    for pdv_id in live:
        try:
            info = name_and_brand(pdv_id)
        except Exception as e:
            info = None
            log(f"{pdv_id}: {e}")
        if info:
            names[pdv_id] = info
        elif pdv_id in old:
            names[pdv_id] = old[pdv_id]
            kept += 1
        else:
            missing.append(pdv_id)
        time.sleep(PAUSE_S)

    from_osm = 0
    if missing:
        elements = osm_fuel(live)
        for pdv_id in missing:
            info = osm_match(pdv_id, live[pdv_id], elements)
            if info:
                names[pdv_id] = info
                from_osm += 1

    tmp = OUT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(names, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    os.chmod(tmp, 0o664)
    os.replace(tmp, OUT)
    log(f"{len(names)}/{len(live)} named, {from_osm} via OpenStreetMap, "
        f"{kept} kept from the previous file, {len(missing) - from_osm} without a name")


if __name__ == "__main__":
    sys.exit(main())
