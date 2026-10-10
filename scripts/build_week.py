"""Builds 7 days x 5 satellite puzzles. Usage: python scripts/build_week.py [start-date]"""
import json, math, random, sys, pathlib, datetime as dt, urllib.parse, urllib.request
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, IMGS = ROOT / "data", ROOT / "images"
ZOOM_KM = [40, 32, 26, 20, 14]   # puzzle 1 is zoomed out (easier), puzzle 5 zoomed in (harder)
POOL = """Paris|France|Europe|48.86|2.35
New York|USA|North America|40.71|-74.01
Dubai|UAE|Asia|25.2|55.27
Sydney|Australia|Oceania|-33.87|151.21
Seattle|USA|North America|47.61|-122.33
Rio de Janeiro|Brazil|South America|-22.91|-43.17
Cairo|Egypt|Africa|30.04|31.24
London|UK|Europe|51.51|-0.13
Tokyo|Japan|Asia|35.68|139.69
Toronto|Canada|North America|43.65|-79.38
San Francisco|USA|North America|37.77|-122.42
Singapore|Singapore|Asia|1.35|103.82
Moscow|Russia|Europe|55.76|37.62
Barcelona|Spain|Europe|41.39|2.17
Istanbul|Turkey|Europe & Asia|41.01|28.98
Shanghai|China|Asia|31.23|121.47
Chicago|USA|North America|41.88|-87.63
Kuala Lumpur|Malaysia|Asia|3.14|101.69
Hong Kong|China|Asia|22.32|114.17
Cape Town|South Africa|Africa|-33.92|18.42
Berlin|Germany|Europe|52.52|13.4
Madrid|Spain|Europe|40.42|-3.7
Rome|Italy|Europe|41.9|12.5
Amsterdam|Netherlands|Europe|52.37|4.9
Lisbon|Portugal|Europe|38.72|-9.14
Athens|Greece|Europe|37.98|23.73
Venice|Italy|Europe|45.44|12.33
Mumbai|India|Asia|19.08|72.88
Delhi|India|Asia|28.61|77.21
Beijing|China|Asia|39.9|116.4
Seoul|South Korea|Asia|37.57|126.98
Bangkok|Thailand|Asia|13.76|100.5
Taipei|Taiwan|Asia|25.03|121.57
Jakarta|Indonesia|Asia|-6.2|106.85
Los Angeles|USA|North America|34.05|-118.24
Miami|USA|North America|25.76|-80.19
Houston|USA|North America|29.76|-95.37
Las Vegas|USA|North America|36.17|-115.14
Washington DC|USA|North America|38.9|-77.04
Vancouver|Canada|North America|49.28|-123.12
Mexico City|Mexico|North America|19.43|-99.13
Buenos Aires|Argentina|South America|-34.6|-58.38
São Paulo|Brazil|South America|-23.55|-46.63
Lima|Peru|South America|-12.05|-77.04
Lagos|Nigeria|Africa|6.52|3.38
Johannesburg|South Africa|Africa|-26.2|28.05
Nairobi|Kenya|Africa|-1.29|36.82
Melbourne|Australia|Oceania|-37.81|144.96
Auckland|New Zealand|Oceania|-36.85|174.76""".splitlines()
CITIES = [(n, c, k, float(a), float(b)) for n, c, k, a, b in (l.split("|") for l in POOL)]

def fetch(lat, lon, km, path):
    dlat = km / 111.0 / 2
    dlon = km / (111.0 * math.cos(math.radians(lat))) / 2
    q = urllib.parse.urlencode(dict(service="WMS", request="GetMap", version="1.1.1",
        layers="s2cloudless-2020", styles="", format="image/jpeg", srs="EPSG:4326",
        bbox=f"{lon-dlon},{lat-dlat},{lon+dlon},{lat+dlat}", width=640, height=640))
    req = urllib.request.Request("https://tiles.maps.eox.at/wms?" + q, headers={"User-Agent": "aerial-game/1.0"})
    data = urllib.request.urlopen(req, timeout=90).read()
    if data[:2] != b"\xff\xd8":
        raise RuntimeError(f"Not a JPEG: {data[:200]!r}")
    path.write_bytes(data)

def load(p, default):
    return json.loads(p.read_text()) if p.exists() else default

cur = load(DATA / "current.json", {"days": {}})
hist = load(DATA / "history.json", {})
today = dt.date.today()
last = max((dt.date.fromisoformat(d) for d in cur["days"]), default=today - dt.timedelta(days=1))
start = max(today, last + dt.timedelta(days=1)) if len(sys.argv) < 2 else dt.date.fromisoformat(sys.argv[1])
rnd = random.Random(start.toordinal())
order = sorted(CITIES, key=lambda c: (hist.get(c[0], ""), rnd.random()))  # least recently used first
picks = order[:35]; rnd.shuffle(picks)

for d in range(7):
    day = (start + dt.timedelta(days=d)).isoformat(); entries = []
    for i, (n, c, k, lat, lon) in enumerate(picks[d*5:d*5+5]):
        jl, jo = rnd.uniform(-.01, .01), rnd.uniform(-.01, .01)   # shift the crop ~1 km so it isn't dead-centre
        f = f"images/{day}-{i}.jpg"
        fetch(lat + jl, lon + jo, ZOOM_KM[i], ROOT / f)
        entries.append({"n": n, "img": f}); hist[n] = day
    cur["days"][day] = entries
    print("built", day, [e["n"] for e in entries])

keep = (today - dt.timedelta(days=14)).isoformat()   # prune old days and their images
for d in [d for d in cur["days"] if d < keep]:
    for e in cur["days"].pop(d): (ROOT / e["img"]).unlink(missing_ok=True)
(DATA / "current.json").write_text(json.dumps(cur, indent=1))
(DATA / "history.json").write_text(json.dumps(hist, indent=1))
(DATA / "cities.json").write_text(json.dumps([list(c) for c in CITIES], ensure_ascii=False))
