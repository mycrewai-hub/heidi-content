#!/usr/bin/env python3
"""
build_hub.py — turns library/manifest.json + each piece's captions.md into the static hub (index.html)
and hub/data.json (machine-readable, used by the publisher).

Run from the repo root: python3 hub/build_hub.py
No dependencies. Brand-locked: white luminous background, blue #008DFF, ink, yellow as a light touch.
"""
import json, os, re, html, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NETWORKS = [("linkedin", "LinkedIn"), ("instagram", "Instagram"), ("facebook", "Facebook"), ("tiktok", "TikTok")]
STATUS_LABEL = {"draft": "Brouillon", "ready": "Prêt", "scheduled": "Programmé", "published": "Publié", "hd-pending": "HD en attente"}

def read(p):
    with open(p, encoding="utf-8") as f: return f.read()

def parse_captions(md):
    """## linkedin ... blocks. Lines starting with # (hashtags) at the end of a block become the hashtag line."""
    out = {}
    cur = None; buf = []
    def flush():
        if cur is None: return
        text = "\n".join(buf).strip()
        tags = ""
        lines = text.split("\n")
        while lines and lines[-1].strip().startswith("#") and not lines[-1].strip().startswith("##"):
            tags = (lines.pop().strip() + " " + tags).strip()
        out[cur] = {"caption": "\n".join(lines).strip(), "hashtags": tags}
    for line in md.split("\n"):
        m = re.match(r"^##\s+(\w+)", line)
        if m:
            flush(); cur = m.group(1).lower(); buf = []
        elif cur is not None:
            buf.append(line)
    flush()
    return out

def human_size(n):
    for u in ("o", "Ko", "Mo", "Go"):
        if n < 1024: return f"{n:.0f} {u}" if u == "o" else f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} To"

def build():
    manifest = json.loads(read(os.path.join(ROOT, "library", "manifest.json")))
    base = manifest["site"]["base_url"].rstrip("/")
    pieces = []
    for p in manifest["pieces"]:
        pdir = os.path.join(ROOT, p["dir"])
        caps = parse_captions(read(os.path.join(pdir, "captions.md"))) if os.path.exists(os.path.join(pdir, "captions.md")) else {}
        nets = {}
        for key, label in NETWORKS:
            spec = p.get("networks", {}).get(key)
            if not spec: continue
            files = []
            for rel in spec.get("files", []):
                fp = os.path.join(pdir, rel)
                if not os.path.exists(fp):
                    print(f"WARN missing file {fp}"); continue
                files.append({"path": f"{p['dir']}/{rel}", "url": f"{base}/{p['dir']}/{rel}", "name": os.path.basename(rel),
                              "bytes": os.path.getsize(fp), "size": human_size(os.path.getsize(fp)),
                              "kind": "video" if rel.lower().endswith((".mp4", ".mov", ".webm")) else "pdf" if rel.lower().endswith(".pdf") else "image"})
            nets[key] = {"label": label, "format": spec.get("format", ""), "files": files,
                         "caption": caps.get(key, {}).get("caption", ""), "hashtags": caps.get(key, {}).get("hashtags", ""),
                         "status": spec.get("status", p.get("status", "draft"))}
        pieces.append({"id": p["id"], "type": p.get("type", ""), "title": p["title"], "date": p.get("date", ""),
                       "status": p.get("status", "draft"), "note": p.get("note", ""),
                       "cover": f"{p['dir']}/{p['cover']}" if p.get("cover") else "", "networks": nets})
    data = {"generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "base_url": base, "pieces": pieces}
    with open(os.path.join(ROOT, "hub", "data.json"), "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f: f.write(render(manifest["site"], data))
    print(f"hub: {len(pieces)} pieces, index.html + hub/data.json written")

def render(site, data):
    j = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    title = html.escape(site.get("title", "Heidi Content Hub"))
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="robots" content="noindex">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Onest:wght@500;600;700;800&family=Geist+Mono:wght@500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#ffffff;--ink:#0c0f14;--ink2:#171b26;--gray:#3a424d;--gray2:#6c7682;--blue:#008dff;--blue-d:#0070d6;--light:#b3f0ff;--ice:#edf9ff;--ice-line:#cfe9ff;--yellow:#ffe310;--r:18px;
--font:"Onest",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"Geist Mono",ui-monospace,SFMono-Regular,Menlo,monospace}}
*{{box-sizing:border-box}}
html{{color-scheme:light}}
body{{margin:0;font:16px/1.45 var(--font);color:var(--ink);background:var(--bg) radial-gradient(900px 520px at 100% -10%,rgba(179,240,255,.75),transparent 60%),radial-gradient(700px 480px at -10% 110%,rgba(0,141,255,.14),transparent 60%);background-attachment:fixed;min-height:100%}}
.wrap{{max-width:980px;margin:0 auto;padding-block:20px 60px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
header{{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:12px;margin-bottom:18px}}
h1{{font-weight:800;font-size:clamp(28px,6vw,40px);letter-spacing:-.03em;margin:0;line-height:1}}
h1 span{{color:var(--blue)}}
.meta{{font:500 12px/1.2 var(--mono);color:var(--blue-d);background:var(--ice);border:1px solid var(--ice-line);border-radius:999px;padding:8px 12px;letter-spacing:.02em}}
.filters{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 22px}}
.chip{{font:600 14px/1 var(--font);padding:10px 14px;border-radius:999px;border:1.5px solid var(--ice-line);background:#fff;color:var(--ink2);cursor:pointer}}
.chip[aria-pressed="true"]{{background:var(--blue);border-color:var(--blue);color:#fff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}}
.card{{background:#fff;border:1px solid var(--ice-line);border-radius:var(--r);overflow:hidden;box-shadow:0 14px 40px -24px rgba(0,112,214,.35);display:flex;flex-direction:column;min-width:0}}
.cover{{position:relative;aspect-ratio:4/5;background:var(--ice);overflow:hidden}}
.cover img,.cover video{{width:100%;height:100%;object-fit:cover;display:block}}
.badge{{position:absolute;right:12px;bottom:12px;font:500 11px/1 var(--mono);background:rgba(255,255,255,.92);color:var(--blue-d);border-radius:999px;padding:7px 10px;letter-spacing:.03em}}
.badge.s-ready,.badge.s-published{{color:#0a7a3b}}
.badge.s-hd-pending,.badge.s-draft{{color:#8a6d00}}
.body{{padding:14px 14px 16px;display:flex;flex-direction:column;gap:12px}}
.title{{font-weight:800;font-size:18px;letter-spacing:-.02em;line-height:1.15;text-wrap:balance;margin:0}}
.sub{{color:var(--gray2);font-size:13px;margin:0}}
.tabs{{display:flex;gap:6px;flex-wrap:wrap}}
.tab{{font:600 13px/1 var(--font);padding:8px 11px;border-radius:999px;border:1.5px solid var(--ice-line);background:#fff;color:var(--ink2);cursor:pointer}}
.tab[aria-selected="true"]{{background:var(--ink);border-color:var(--ink);color:#fff}}
.panel{{display:flex;flex-direction:column;gap:10px}}
.fmt{{font:500 12px/1.3 var(--mono);color:var(--gray2)}}
.files{{display:flex;flex-direction:column;gap:6px}}
.file{{display:flex;align-items:center;justify-content:space-between;gap:8px;border:1px solid var(--ice-line);border-radius:12px;padding:8px 10px;background:var(--ice)}}
.file .n{{font-size:13px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.file .n small{{color:var(--gray2);font-family:var(--mono);font-size:11px;margin-left:6px}}
.btns{{display:flex;gap:6px;flex-shrink:0}}
.btn{{font:700 13px/1 var(--font);padding:9px 12px;border-radius:999px;border:0;cursor:pointer;background:var(--blue);color:#fff;text-decoration:none;display:inline-flex;align-items:center;gap:6px}}
.btn.ghost{{background:#fff;color:var(--blue-d);border:1.5px solid var(--ice-line)}}
.btn:focus-visible,.chip:focus-visible,.tab:focus-visible{{outline:3px solid var(--light);outline-offset:2px}}
.cap{{position:relative}}
.cap textarea{{width:100%;min-height:140px;resize:vertical;font:500 14px/1.45 var(--font);color:var(--ink);border:1.5px solid var(--ice-line);border-radius:12px;padding:10px 12px;background:#fff;display:block}}
.cap .row{{display:flex;justify-content:flex-end;margin-top:8px}}
.vid{{width:100%;border-radius:12px;background:#000;max-height:420px}}
.cap .tags{{font:500 13px/1.4 var(--mono);color:var(--blue-d);margin:6px 0 0;word-break:break-word}}
.toast{{position:fixed;left:50%;bottom:calc(20px + env(safe-area-inset-bottom,0px));transform:translateX(-50%) translateY(20px);background:var(--ink);color:#fff;font:600 14px/1 var(--font);padding:12px 16px;border-radius:999px;opacity:0;transition:.2s;pointer-events:none}}
.toast.on{{opacity:1;transform:translateX(-50%)}}
.empty{{color:var(--gray2);padding:40px 0;text-align:center}}
.yellow{{background:linear-gradient(transparent 62%,var(--yellow) 62%,var(--yellow) 88%,transparent 88%)}}
footer{{margin-top:36px;color:var(--gray2);font:500 12px/1.5 var(--mono)}}
@media (prefers-reduced-motion:reduce){{.toast{{transition:none}}}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div><h1>Heidi <span>Content Hub</span></h1><p class="sub" style="margin-top:8px">Chaque pièce, par réseau, au bon format. Copie la caption, télécharge, publie.</p></div>
  <div class="meta" id="meta"></div>
</header>
<div class="filters" id="filters" role="group" aria-label="Filtrer par réseau"></div>
<div class="grid" id="grid"></div>
<div class="empty" id="empty" hidden>Rien pour ce filtre.</div>
<footer>Fichiers servis depuis ce dépôt. URL publique de chaque fichier = bouton "URL" (à coller dans l'outil de publication).</footer>
</div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>
const DATA = {j};
const NET = {{linkedin:"LinkedIn",instagram:"Instagram",facebook:"Facebook",tiktok:"TikTok"}};
const STATUS = {json.dumps(STATUS_LABEL, ensure_ascii=False)};
let filter = "all";
try {{ filter = localStorage.getItem("hub.filter") || "all"; }} catch (e) {{}}
const $ = (s, r=document) => r.querySelector(s);
function toast(msg) {{ const t = $("#toast"); t.textContent = msg; t.classList.add("on"); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("on"), 1600); }}
async function copy(text, label) {{
  try {{ await navigator.clipboard.writeText(text); toast(label + " copié"); }}
  catch (e) {{ const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select(); try {{ document.execCommand("copy"); toast(label + " copié"); }} catch (e2) {{ toast("Copie impossible, sélectionne le texte"); }} ta.remove(); }}
}}
function esc(s) {{ return String(s).replace(/[&<>"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c])); }}
function renderFilters() {{
  const f = $("#filters"); f.innerHTML = "";
  [["all","Tous"],...Object.entries(NET)].forEach(([k,l]) => {{
    const b = document.createElement("button"); b.className = "chip"; b.textContent = l; b.setAttribute("aria-pressed", String(filter===k));
    b.onclick = () => {{ filter = k; try {{ localStorage.setItem("hub.filter", k); }} catch(e) {{}} renderFilters(); renderGrid(); }}; f.appendChild(b);
  }});
}}
function panel(p, key) {{
  const n = p.networks[key]; if (!n) return "";
  const vids = n.files.filter(f => f.kind === "video").map(f => `<video class="vid" controls preload="metadata" playsinline src="${{esc(f.path)}}"></video>`).join("");
  const files = vids + n.files.map(f => `<div class="file"><div class="n">${{esc(f.name)}}<small>${{esc(f.size)}}</small></div><div class="btns"><a class="btn" href="${{esc(f.path)}}" download>Télécharger</a><button class="btn ghost" data-copy="${{esc(f.url)}}" data-label="URL">URL</button></div></div>`).join("");
  const full = n.caption + (n.hashtags ? "\\n\\n" + n.hashtags : "");
  return `<div class="panel" data-net="${{key}}">
    <div class="fmt">${{esc(n.format || "")}}</div>
    <div class="files">${{files || '<div class="fmt">Aucun fichier encore.</div>'}}</div>
    ${{n.caption ? `<div class="cap"><textarea readonly aria-label="Caption ${{esc(n.label)}}">${{esc(n.caption)}}</textarea>${{n.hashtags ? `<p class="tags">${{esc(n.hashtags)}}</p>` : ""}}<div class="row"><button class="btn" data-copy="${{esc(full)}}" data-label="Caption + hashtags">Copier caption + hashtags</button></div></div>` : ""}}
  </div>`;
}}
function card(p) {{
  const keys = Object.keys(p.networks).filter(k => filter === "all" || k === filter);
  const first = keys.includes(filter) ? filter : keys[0];
  const cover = p.cover ? (p.cover.match(/\\.(mp4|webm|mov)$/i) ? `<video src="${{esc(p.cover)}}" muted playsinline preload="metadata"></video>` : `<img src="${{esc(p.cover)}}" alt="" loading="lazy">`) : "";
  const el = document.createElement("article"); el.className = "card";
  el.innerHTML = `<div class="cover">${{cover}}<span class="badge s-${{esc(p.status)}}">${{esc(STATUS[p.status] || p.status)}}</span></div>
  <div class="body"><h2 class="title">${{esc(p.title)}}</h2><p class="sub">${{esc(p.type)}}${{p.date ? " · " + esc(p.date) : ""}}${{p.note ? " · " + esc(p.note) : ""}}</p>
  <div class="tabs" role="tablist">${{keys.map(k => `<button class="tab" role="tab" data-k="${{k}}" aria-selected="${{k===first}}">${{NET[k]}}</button>`).join("")}}</div>
  <div class="panels">${{first ? panel(p, first) : ""}}</div></div>`;
  el.querySelectorAll(".tab").forEach(t => t.onclick = () => {{ el.querySelectorAll(".tab").forEach(x => x.setAttribute("aria-selected", String(x===t))); $(".panels", el).innerHTML = panel(p, t.dataset.k); }});
  return el;
}}
function renderGrid() {{
  const g = $("#grid"); g.innerHTML = "";
  const list = DATA.pieces.filter(p => filter === "all" || p.networks[filter]);
  list.forEach(p => g.appendChild(card(p)));
  $("#empty").hidden = list.length > 0;
}}
document.addEventListener("click", e => {{ const b = e.target.closest("[data-copy]"); if (b) copy(b.dataset.copy, b.dataset.label || "Texte"); }});
$("#meta").textContent = DATA.pieces.length + " pièce" + (DATA.pieces.length > 1 ? "s" : "") + " · mis à jour " + DATA.generated;
renderFilters(); renderGrid();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
