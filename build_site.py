"""Build the GitHub Pages site from the games in ../outputs.

Makes: index.html (home page), maze_game.html + word_game.html (copies with a Home button
and offline support), sw.js (keeps an offline copy on the phone), manifest.webmanifest, icons.
The originals in ../outputs are never changed.

Usage:  python build_site.py            (keeps the player name)
        python build_site.py --name ""  (no name shown: "Great job!" instead of "Great job, Lucas!")
Run it again after changing a game; the offline copy on phones updates on their next visit.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "outputs"
GAMES = [("maze_game.html", "Maze Adventure", "🦌", "Help Sven find the star"),
         ("word_game.html", "Word Builder", "🔤", "Spell the picture")]

ap = argparse.ArgumentParser()
ap.add_argument("--name", default=None, help='player name to show; "" hides it (default: keep the games\' own)')
args = ap.parse_args()

HEAD_EXTRA = """<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Kids Games">
<meta name="theme-color" content="#ff7b54">
"""
SW_REGISTER = """<script>
if ("serviceWorker" in navigator) { window.addEventListener("load", function () { navigator.serviceWorker.register("sw.js"); }); }
</script>
"""
HOME_BUTTON = """<a id="home-link" href="./" aria-label="Back to games">🏠</a>
<style>
  #home-link { position: fixed; left: calc(10px + env(safe-area-inset-left)); bottom: calc(10px + env(safe-area-inset-bottom));
    z-index: 60; width: 44px; height: 44px; border-radius: 50%; background: rgba(255,255,255,0.85);
    box-shadow: 0 2px 8px rgba(0,0,0,0.15); display: flex; align-items: center; justify-content: center;
    font-size: 22px; text-decoration: none; }
</style>
"""


def set_name(html: str, name: str | None) -> str:
    if name is None:
        return html
    html = re.sub(r'const PLAYER_NAME = "[^"]*";', f'const PLAYER_NAME = {json.dumps(name)};', html)
    if name == "":
        # Overlays say "Great Job, Lucas!" in plain HTML too.
        html = re.sub(r"Great Job, [A-Za-z]+!", "Great Job!", html)
    return html


def game_page(src_name: str) -> str:
    html = (SRC / src_name).read_text(encoding="utf-8")
    html = set_name(html, args.name)
    i = html.index("\n", html.index("<meta charset")) + 1
    html = html[:i] + HEAD_EXTRA + html[i:]
    j = html.rindex("</body>")
    return html[:j] + HOME_BUTTON + SW_REGISTER + html[j:]


def index_page() -> str:
    who = args.name if args.name is not None else re.search(r'const PLAYER_NAME = "([^"]*)";', (SRC / GAMES[0][0]).read_text(encoding="utf-8")).group(1)
    title = f"{who}'s Games" if who else "Kids Games"
    cards = "\n".join(
        f'    <a class="card" href="{f}"><span class="big">{emoji}</span><span class="name">{name}</span><span class="sub">{sub}</span></a>'
        for f, name, emoji, sub in GAMES)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
{HEAD_EXTRA}<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
  html, body {{ height: 100%; }}
  body {{ font-family: "Comic Sans MS", "Chalkboard SE", "Marker Felt", "Segoe UI", sans-serif;
    background: linear-gradient(160deg, #fef9f0, #fdf2e3); color: #3a3a3a;
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 24px;
    padding: calc(16px + env(safe-area-inset-top)) 16px calc(16px + env(safe-area-inset-bottom)); }}
  h1 {{ font-size: clamp(30px, 9vmin, 56px); color: #ff7b54; text-align: center; }}
  .games {{ display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; width: 100%; }}
  .card {{ flex: 1 1 240px; max-width: 340px; background: #fff; border-radius: 28px; padding: 22px 16px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.10); text-decoration: none; color: inherit;
    display: flex; flex-direction: column; align-items: center; gap: 6px; }}
  .card:active {{ transform: scale(0.97); }}
  .big {{ font-size: clamp(56px, 18vmin, 96px); line-height: 1.1; }}
  .name {{ font-size: clamp(22px, 6vmin, 30px); font-weight: bold; }}
  .sub {{ font-size: clamp(14px, 4vmin, 18px); color: #888; }}
  @media (orientation: landscape) and (max-height: 500px) {{ body {{ gap: 12px; }} .card {{ padding: 12px; }} }}
</style>
</head>
<body>
  <h1>{title}</h1>
  <div class="games">
{cards}
  </div>
{SW_REGISTER}</body>
</html>
"""


def icon(size: int) -> Image.Image:
    # Orange rounded square with a big white star and a small teal maze path.
    s = size
    img = Image.new("RGB", (s, s), "#ff7b54")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([s * .08, s * .08, s * .92, s * .92], radius=s * .18, fill="#ff9a6e")
    import math
    cx, cy, r1, r2 = s / 2, s * .47, s * .30, s * .13
    pts = [(cx + (r1 if k % 2 == 0 else r2) * math.sin(math.pi * k / 5), cy - (r1 if k % 2 == 0 else r2) * math.cos(math.pi * k / 5)) for k in range(10)]
    d.polygon(pts, fill="#ffffff")
    w = max(2, int(s * .045))
    path = [(s * .2, s * .82), (s * .4, s * .82), (s * .4, s * .72), (s * .6, s * .72), (s * .6, s * .82), (s * .8, s * .82)]
    d.line(path, fill="#4ecdc4", width=w, joint="curve")
    return img


written = []
for f, *_ in GAMES:
    (HERE / f).write_text(game_page(f), encoding="utf-8"); written.append(f)
(HERE / "index.html").write_text(index_page(), encoding="utf-8"); written.append("index.html")
for size in (180, 192, 512):
    icon(size).save(HERE / f"icon-{size}.png"); written.append(f"icon-{size}.png")
manifest = {
    "name": "Kids Games", "short_name": "Kids Games", "start_url": "./", "scope": "./", "display": "standalone",
    "background_color": "#fef9f0", "theme_color": "#ff7b54",
    "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}],
}
(HERE / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2), encoding="utf-8"); written.append("manifest.webmanifest")

# Offline helper. Its version is a hash of every site file, so any change makes phones refresh their copy.
files = ["./"] + [f"./{n}" for n in written]
digest = hashlib.sha256(b"".join((HERE / n).read_bytes() for n in written)).hexdigest()[:12]
sw = f"""// Generated by build_site.py -- keeps an offline copy of the games on the phone.
const CACHE = "kids-games-{digest}";
const FILES = {json.dumps(files)};
self.addEventListener("install", e => {{
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
}});
self.addEventListener("activate", e => {{
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
}});
self.addEventListener("fetch", e => {{
  if (e.request.method !== "GET") return;
  e.respondWith(caches.match(e.request, {{ ignoreSearch: true }})
    .then(hit => hit || fetch(e.request).catch(() => caches.match("./index.html"))));
}});
"""
(HERE / "sw.js").write_text(sw, encoding="utf-8")
(HERE / ".nojekyll").write_text("", encoding="utf-8")
print("built", ", ".join(written + ["sw.js", ".nojekyll"]), f"(version {digest})")
