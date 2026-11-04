#!/usr/bin/env python3
"""Build a published-content inventory from each site's own sitemap.

One row per live URL, counted once, enriched with title, dates, categories and tags
from the WordPress REST API where a site leaves it open, or from the page's own HTML
where it does not. Optional extras:

* match the rows against an old hand-kept list (to find what it was missing, and
  which of its rows no longer exist);
* find which people in a relationship registry are named in no page title;
* flag titles that still use a retired name (a rename worklist).

The sitemap is the source of truth for "what is published". The outputs are a
generated copy: never edit them by hand; fix the page on the site and run again.

Usage:
  python3 published_inventory.py --config inventory-config.json --out library \
      [--registry registry.json] [--old-lists DIR]
  python3 published_inventory.py --config inventory-config.json --out library --retag-only

Config (JSON; every key optional except "sites"):
  {"sites": ["example.com"],
   "brand_suffixes": ["Example Co"],          # stripped from the end of titles
   "rename_pattern": "oldname",               # regex; titles that match go to the rename worklist
   "rename_file": "rename-worklist.csv",
   "user_agent": "...",                       # sent with every request
   "people": {"owner_entity_id": "jane-doe",  # the registry's own subject, skipped
              "real_sources": ["crm", "notes"],   # sources that mean a real relationship
              "exclude_entity_ids": ["ai-agent"]},  # records that are not people (e.g. AI agents)
   "topics": [["Topic name", "regex"], ...],  # replaces the built-in example topics
   "stages": [["Produce", "regex"], ...]}

--old-lists DIR holds JSON exports of the old per-site lists in the Sheets API
values format ({"values": [[No., Title, URL, Date, Status], ...]}) named <site>.json.

Standard library only. Read-only against the sites. Safe to re-run.
"""
import argparse, csv, datetime, html, json, os, re, sys, time, urllib.error, urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
DEFAULT_UA = ("Mozilla/5.0 (compatible; ContentLibraryInventory/1.0; "
              "+https://github.com/dennisyu/local-service-spotlight-skills)")
CONFIG = {"sites": [], "brand_suffixes": [], "rename_pattern": "", "rename_file": "rename-worklist.csv",
          "user_agent": DEFAULT_UA, "people": {"owner_entity_id": "", "real_sources": [], "exclude_entity_ids": []}}

# ---------- pure helpers (unit-tested) ----------
def norm(url):
    """host+path, lowercase, no scheme/www/query/trailing slash. None for drafts/admin."""
    if not url:
        return None
    m = re.match(r"https?://(www\.)?([^/?#]+)(/[^?#]*)?(\?[^#]*)?", url.strip(), re.I)
    if not m:
        return None
    path, query = m.group(3) or "/", m.group(4) or ""
    if "preview=true" in query or "/wp-admin" in path or path.endswith("post.php"):
        return None
    path = re.sub(r"/+$", "", path) or "/"
    return (m.group(2).lower() + path).lower()

def slug(url):
    parts = re.sub(r"[?#].*", "", url or "").rstrip("/").split("/")
    return parts[-1].lower() if len(parts) > 3 else "/"

def clean_title(t, suffixes=None):
    t = html.unescape(re.sub(r"\s+", " ", t or "")).strip()
    suffixes = CONFIG["brand_suffixes"] if suffixes is None else suffixes
    if suffixes:
        alt = "|".join(re.escape(s) for s in suffixes)
        t = re.sub(r"\s*[|–-]\s*(%s)\s*$" % alt, "", t)
    return t.strip()

# Example topics for a marketing and local-service business. Replace with "topics" in the config.
TOPICS = [
    ("AI agents & automation", r"\b(ai|agent|agents|claude|chatgpt|codex|grok|gpt|llm|qwen|kimi|automation|automate|skill pack|skill file|mcp)\b"),
    ("Content Factory & repurposing", r"content factory|repurpos|one[- ]minute video|transcri|descript|\bclips?\b|\bshorts\b|podcast|video"),
    ("Personal brand & Knowledge Panel", r"personal brand|knowledge panel|knowledge graph|\bentity\b|e-?e-?a-?t|authority|brand audit|grokipedia|wikipedia"),
    ("SEO & AI search", r"\bseo\b|search|\brank|backlink|link building|internal link|sitemap|schema|\baeo\b|google business|\bgbp\b|\bmaps\b|local seo"),
    ("Paid ads & Dollar a Day", r"dollar a day|\$1 ?a day|facebook ads?|meta ads?|advertis|\bads?\b|\bppc\b|google ads|\bboost|targeting|retarget|campaign"),
    ("Local service businesses", r"roof|hvac|plumb|\bpest|landscap|paint|gutter|fence|concrete|pressure wash|contractor|home service|local service|remodel|garage door|softwash|appliance|\blawn"),
    ("Agency, hiring & team", r"agency|agencies|\bhir(e|ing)\b|\bva\b|virtual assistant|\bteam\b|employee|manag|basecamp|communicat|\bclients?\b|outsourc|delegat|operator"),
    ("People & relationship stories", r"spotlight|awesome people|interview|\bstory\b|journey|\bmeet\b|founder|lessons from"),
    ("Entrepreneurship & career", r"entrepreneur|startup|young (adult|people|entrepreneur)|college|career|\bjobs?\b|equity|\bexit\b|acquisition|dealcon|business growth"),
    ("Analytics & MAA", r"\bmaa\b|metrics|analytics|\bga4\b|analysis|dashboard|\bkpi|measur|tracking|\breport"),
    ("Frameworks & methods", r"nine triangles|9 triangles|\bgct\b|social amplification|\bsae\b|seo tree|topic wheel|money tree|learn,? do,? teach|definitive article|meta article|task library|\bsop\b|checklist"),
    ("Speaking & events", r"\bspeak|keynote|conference|summit|\bevent|workshop|webinar|\bstage\b|digimarcon|namm"),
    ("Life, travel & mindset", r"travel|\bmiles\b|life lesson|mindset|\bfaith\b|\bhealth\b|running|marathon|\bhike|family|birthday"),
]
TRIANGLES = [
    # Names and order follow the accepted operational reference in this repository:
    # skills/nine-triangles/references/canonical-framework.md. Legacy aliases
    # (ACC for AEC, ABP for SBP) are matched so older pages are found.
    ("Specialist·Business·Partner (SBP)", r"\bsbp\b|\babp\b|specialist,? business,? (and )?partner|analyst,? business,? (and )?partner"),
    ("Audience·Engagement·Conversion (AEC)", r"\baec\b|#?\bacc\b|audience,? engagement,? (and )?conversion|awareness,? consideration,? (and )?conversion"),
    ("Goals·Content·Targeting (GCT)", r"\bgct\b|goals,? content,? (and )?targeting"),
    ("Metrics·Analysis·Action (MAA)", r"\bmaa\b|metrics,? analysis"),
    ("Do·Delegate·Delete (DDD)", r"do,? delegate,? (and )?delete|\bddd\b"),
    ("Communicate·Iterate·Delegate (CID)", r"communicate,? iterate|\bcid\b"),
    ("Learn·Do·Teach (LDT)", r"learn,? do,? (and )?teach|\bldt\b"),
    ("Content·Checklist·Software (CCS)", r"\bccs\b|content,? checklists?,? (and )?software"),
    ("Marketing·Operations·Finance (MOF)", r"\bmof\b|marketing,? operations,? (and )?finance"),
    ("Nine Triangles (overview)", r"nine triangles|9 triangles"),
]
# The four Content Factory stages are locked: Produce -> Process -> Post -> Promote.
STAGES = [
    ("Produce", r"\brecord|\bfilm|capture|interview|one[- ]minute video|phone video|camera"),
    ("Process", r"transcri|\bedit|repurpos|descript|\bclip|turn(ed)? .* into"),
    ("Post", r"publish|\bposting\b|\bblog\b|youtube|linkedin|website"),
    ("Promote", r"dollar a day|\bboost|\bads?\b|amplif|promot"),
]

def dedupe_sitemap(rows):
    """Collapse sitemap rows to one per URL.

    SEO plugins such as Rank Math list a page that embeds a video in a video sitemap
    as well, so a post can appear as both "post" and "video". Keep the content kind,
    flag has_video, and count genuine repeats of the same kind (a sitemap defect).
    Returns a list of (kind, url, lastmod, has_video, repeats) in first-seen order.
    """
    order, info = [], {}
    for kind, url, lastmod in rows:
        n = norm(url) or url
        if n not in info:
            order.append(n)
            info[n] = {"kind": None, "url": url, "lastmod": lastmod, "video": False, "seen": Counter()}
        i = info[n]
        i["seen"][kind] += 1
        if kind == "video":
            i["video"] = True
        elif i["kind"] is None:
            i["kind"], i["url"] = kind, url
        if lastmod > i["lastmod"]:
            i["lastmod"] = lastmod
    out = []
    for n in order:
        i = info[n]
        kind = i["kind"] or "video"
        repeats = max([c for k, c in i["seen"].items() if k != "video"] or [i["seen"].get("video", 1)])
        out.append((kind, i["url"], i["lastmod"], i["video"], repeats))
    return out

def tags_for(text, rules):
    return "; ".join(name for name, rx in rules if re.search(rx, text or "", re.I))

def apply_config(cfg):
    """Merge a config dict into CONFIG and the rule tables. Returns CONFIG."""
    global TOPICS, STAGES
    for k in ("sites", "brand_suffixes", "rename_pattern", "rename_file", "user_agent"):
        if k in cfg:
            CONFIG[k] = cfg[k]
    if "people" in cfg:
        CONFIG["people"] = {**CONFIG["people"], **cfg["people"]}
    if cfg.get("topics"):
        TOPICS = [tuple(t) for t in cfg["topics"]]
    if cfg.get("stages"):
        STAGES = [tuple(t) for t in cfg["stages"]]
    return CONFIG

# ---------- network ----------
def fetch(url, tries=3, limit=None):
    err = None
    headers = {"User-Agent": CONFIG["user_agent"]}
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as r:
                return r.status, {k.lower(): v for k, v in r.headers.items()}, (r.read(limit) if limit else r.read()), r.geturl()
        except urllib.error.HTTPError as e:
            return e.code, {}, b"", url
        except Exception as e:  # network blips
            err = e
            time.sleep(2 * (i + 1))
    return None, {}, str(err).encode(), url

def sitemap_urls(site):
    st, _, body, _ = fetch(f"https://{site}/sitemap_index.xml")
    if st != 200:
        raise RuntimeError(f"{site}: sitemap index HTTP {st}")
    root = ET.fromstring(body)
    children = [el.find("s:loc", NS).text.strip() for el in root if el.find("s:loc", NS) is not None]
    rows = []
    def one(cu):
        s, _, b, _ = fetch(cu)
        if s != 200:
            return cu, []
        try:
            r = ET.fromstring(b)
        except ET.ParseError:
            return cu, []
        out = []
        for el in r:
            loc, lm = el.find("s:loc", NS), el.find("s:lastmod", NS)
            if loc is not None and loc.text:
                out.append((loc.text.strip(), (lm.text or "").strip() if lm is not None else ""))
        return cu, out
    with ThreadPoolExecutor(6) as ex:
        for cu, items in ex.map(one, children):
            kind = re.sub(r"\d*\.xml$", "", cu.rsplit("/", 1)[-1]).replace("-sitemap", "")
            if kind == "sitemap":  # nested per-page sitemaps from page builders
                continue
            rows += [(kind, u, lm) for u, lm in items]
    return rows

def wp_rest(site):
    """Return ({norm_url: item}, categories, tags) for posts and pages; empty dicts if REST is closed."""
    def pages(kind, fields):
        base = f"https://{site}/wp-json/wp/v2/{kind}?per_page=100&_fields={fields}"
        st, h, b, _ = fetch(base + "&page=1")
        if st != 200:
            return None
        try:
            items = json.loads(b)
        except ValueError:
            return None
        total = int(h.get("x-wp-totalpages") or 0)
        p = 2
        # Some proxies drop the X-WP-TotalPages header; then keep paging until a short page.
        while (total and p <= total) or (not total and items and len(items) % 100 == 0):
            s, _, b2, _ = fetch(base + f"&page={p}")
            try:
                batch = json.loads(b2) if s == 200 else []
            except ValueError:
                batch = []
            if not batch:
                break
            items += batch
            p += 1
        return items
    posts = pages("posts", "id,link,title,date,modified,categories,tags")
    if posts is None:
        return {}, {}, {}
    pgs = pages("pages", "id,link,title,date,modified") or []
    cats = {c["id"]: html.unescape(c["name"]) for c in (pages("categories", "id,name") or [])}
    tgs = {t["id"]: html.unescape(t["name"]) for t in (pages("tags", "id,name") or [])}
    out = {}
    for items in (posts, pgs):
        for it in items:
            out[norm(it["link"])] = it
    return out, cats, tgs

def meta(b, prop):
    m = (re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]*content=["\']([^"\']*)' % re.escape(prop), b, re.I)
         or re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:property|name)=["\']%s["\']' % re.escape(prop), b, re.I))
    return html.unescape(m.group(1)).strip() if m else ""

def html_facts(url):
    st, _, b, final = fetch(url, limit=400000)
    t = b.decode("utf-8", "replace")
    title = re.search(r"<title[^>]*>(.*?)</title>", t, re.I | re.S)
    can = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', t, re.I)
    return {"status": str(st), "final": final, "title": meta(t, "og:title") or (title.group(1) if title else ""),
            "published": meta(t, "article:published_time")[:10], "modified": meta(t, "article:modified_time")[:10],
            "section": meta(t, "article:section"), "robots": meta(t, "robots"), "canonical": can.group(1) if can else ""}

# ---------- old lists + registry ----------
def load_old_list(list_dir, site):
    """Rows from a Sheets values export: [No., Title, URL, Date, Status]."""
    path = os.path.join(list_dir or "", f"{site}.json")
    if not list_dir or not os.path.exists(path):
        return {}, {}
    by_norm, by_slug = {}, {}
    with open(path, encoding="utf-8") as fh:
        values = json.load(fh).get("values", [])
    for r in values:
        r = [str(x) for x in r] + [""] * (5 - len(r))
        n = norm(r[2]) if r[2].startswith("http") else None
        if n:
            by_norm.setdefault(n, r)
            by_slug.setdefault(slug(r[2]), r)
    return by_norm, by_slug

def load_people(registry_path):
    """People from a registry JSON list: [{"entity_id", "type": "person", "name", "aliases", "sources", ...}]."""
    if not registry_path or not os.path.exists(registry_path):
        return []
    owner = CONFIG["people"].get("owner_entity_id") or ""
    real_sources = set(CONFIG["people"].get("real_sources") or [])
    excluded = set(CONFIG["people"].get("exclude_entity_ids") or [])  # e.g. AI agent personas stored as people
    people = []
    with open(registry_path, encoding="utf-8") as fh:
        entities = json.load(fh)
    for e in entities:
        name = (e.get("name") or "").strip().strip('"')
        if (e.get("type") != "person" or len(name.split()) < 2 or len(name) < 7
                or (owner and e.get("entity_id") == owner) or e.get("entity_id") in excluded):
            continue
        src = [s.strip() for s in re.split(r"[,;]", e.get("sources") or "") if s.strip()]
        names = {name} | {a.strip() for a in re.split(r"[;|]", e.get("aliases") or "") if len(a.strip().split()) >= 2}
        pats = [re.compile(r"(?<![\w])" + re.escape(n) + r"(?![\w])", re.I) for n in names]
        people.append({"entity_id": e["entity_id"], "name": name, "sources": src, "pats": pats,
                       "real": bool(real_sources & set(src)) if real_sources else bool(src),
                       "in_vault": e.get("in_vault", ""), "in_fleet_memory": e.get("in_fleet_memory", "")})
    return people

# ---------- build ----------
def build(sites, out_dir, list_dir, registry):
    people = load_people(registry)
    rename_rx = re.compile(CONFIG["rename_pattern"], re.I) if CONFIG["rename_pattern"] else None
    inv, stats, lib_not_live = [], {}, []
    for site in sites:
        print(f"[{site}] sitemaps…", flush=True)
        raw = sitemap_urls(site)
        sm = dedupe_sitemap(raw)
        print(f"[{site}] {len(raw)} sitemap listings → {len(sm)} unique URLs", flush=True)
        rest, cats, tgs = wp_rest(site)
        print(f"[{site}] REST {'open' if rest else 'closed → reading each page'}", flush=True)
        facts = {}
        if not rest:
            urls = [u for _, u, _, _, _ in sm]
            with ThreadPoolExecutor(8) as ex:
                for u, f in zip(urls, ex.map(html_facts, urls)):
                    facts[norm(u)] = f
        by_norm, by_slug = load_old_list(list_dir, site)
        matched = set()
        for kind, url, lastmod, has_video, repeats in sm:
            n = norm(url)
            row = {"site": site, "type": kind, "url": url, "title": "", "published": "", "modified": lastmod[:10],
                   "categories": "", "tags": "", "status": "in sitemap", "library_tab": "",
                   "has_video": "Y" if has_video else "", "notes": []}
            if repeats > 1:
                row["notes"].append(f"listed {repeats}x in sitemaps")
            if n in rest:
                it = rest[n]
                row.update(title=clean_title(it["title"]["rendered"]), published=it["date"][:10],
                           modified=(it.get("modified") or lastmod)[:10], status="200",
                           categories="; ".join(cats.get(i, str(i)) for i in it.get("categories", [])),
                           tags="; ".join(tgs.get(i, str(i)) for i in it.get("tags", [])))
            if n in facts:
                f = facts[n]
                row.update(title=clean_title(f["title"]), published=f["published"], status=f["status"],
                           modified=f["modified"] or row["modified"], categories=f["section"])
                if "noindex" in f["robots"].lower(): row["notes"].append("noindex")
                if f["canonical"] and norm(f["canonical"]) != n: row["notes"].append("canonical->" + f["canonical"])
                if f["final"] and norm(f["final"]) != n: row["notes"].append("redirects->" + f["final"])
            hit = by_norm.get(n) or by_slug.get(slug(url))
            if hit:
                row["library_tab"] = "yes"
                matched.add(norm(hit[2]))
                if norm(hit[2]) != n: row["notes"].append("library has old URL " + hit[2])
                row["title"] = row["title"] or hit[1]
            text = " ".join([row["title"], row["categories"], row["tags"]])
            row["topics_v1"] = tags_for(text, TOPICS)
            row["nine_triangles_v1"] = tags_for(text, TRIANGLES)
            row["factory_stage_v1"] = tags_for(row["title"], STAGES)
            hay = row["title"] + " | " + row["tags"]
            row["people_in_title_v1"] = "; ".join(p["name"] for p in people if any(rx.search(hay) for rx in p["pats"]))
            row["notes"] = " | ".join(row["notes"])
            inv.append(row)
        live_slugs = {slug(r["url"]) for r in inv if r["site"] == site}
        for n2, r in by_norm.items():
            if n2 not in matched and slug(r[2]) not in live_slugs:
                lib_not_live.append({"site": site, "title": r[1], "url": r[2], "date": r[3], "status_in_library": r[4]})
        rows = [r for r in inv if r["site"] == site]
        stats[site] = {"live_urls": len(rows), "sitemap_listings": len(raw),
                       "with_video": sum(1 for r in rows if r["has_video"]),
                       "listed_twice_or_more": sum(1 for r in rows if "x in sitemaps" in r["notes"]),
                       "by_type": dict(Counter(r["type"] for r in rows)),
                       "in_library": sum(1 for r in rows if r["library_tab"]),
                       "missing_from_library": sum(1 for r in rows if not r["library_tab"]),
                       "non_200": sum(1 for r in rows if r["status"] not in ("200", "in sitemap")),
                       "noindex": sum("noindex" in r["notes"] for r in rows),
                       "rename_hits": sum(1 for r in rows if rename_rx and rename_rx.search(r["title"])),
                       "library_old_url": sum("library has old URL" in r["notes"] for r in rows)}
    stats["library_rows_not_live"] = dict(Counter(x["site"] for x in lib_not_live))
    stats["generated_utc"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    stats["library_matching"] = bool(list_dir)
    write_outputs(out_dir, inv, lib_not_live, people, stats, rename_rx)
    return stats

FIELDS = ["site", "type", "title", "url", "published", "modified", "categories", "tags", "status",
          "has_video", "library_tab", "topics_v1", "nine_triangles_v1", "factory_stage_v1", "people_in_title_v1", "notes"]
SLIM = ["site", "type", "title", "url", "published", "modified", "has_video", "topics_v1", "nine_triangles_v1",
        "people_in_title_v1", "library_tab", "notes"]

def short_notes(notes):
    codes = []
    if "library has old URL" in notes: codes.append("old URL in library")
    if "noindex" in notes: codes.append("noindex")
    if "canonical->" in notes: codes.append("canonical differs")
    if "redirects->" in notes: codes.append("redirects")
    m = re.search(r"listed (\d+)x in sitemaps", notes)
    if m: codes.append(f"listed {m.group(1)}x in sitemaps")
    return "; ".join(codes)

def write_outputs(out_dir, inv, lib_not_live, people, stats, rename_rx):
    os.makedirs(out_dir, exist_ok=True)
    inv.sort(key=lambda r: (r["site"], r["published"] or r["modified"] or "", r["url"]))
    with open(os.path.join(out_dir, "published-inventory.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(inv)
    with open(os.path.join(out_dir, "published-inventory-sheet.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SLIM, extrasaction="ignore"); w.writeheader()
        for r in inv:
            w.writerow({**r, "library_tab": "Y" if r["library_tab"] else "", "notes": short_notes(r["notes"])})
    with open(os.path.join(out_dir, "library-rows-not-live.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["site", "title", "url", "date", "status_in_library"]); w.writeheader(); w.writerows(lib_not_live)
    if rename_rx:
        with open(os.path.join(out_dir, CONFIG["rename_file"]), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader()
            w.writerows(r for r in inv if rename_rx.search(r["title"]))
    if people:
        cov = defaultdict(list)
        for r in inv:
            for nm in filter(None, r["people_in_title_v1"].split("; ")):
                cov[nm].append(r)
        pc = [{"entity_id": p["entity_id"], "name": p["name"], "relationship_sources": ", ".join(p["sources"]),
               "real_relationship": "Y" if p["real"] else "N", "in_vault": p["in_vault"], "in_fleet_memory": p["in_fleet_memory"],
               "pages_with_name_in_title": len(cov.get(p["name"], [])),
               "sites": "; ".join(sorted({a["site"] for a in cov.get(p["name"], [])})),
               "example_urls": " ".join(a["url"] for a in cov.get(p["name"], [])[:3])} for p in people]
        pc.sort(key=lambda x: (-x["pages_with_name_in_title"], x["name"]))
        with open(os.path.join(out_dir, "people-coverage.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(pc[0].keys())); w.writeheader(); w.writerows(pc)
        real = [p for p in pc if p["real_relationship"] == "Y"]
        stats["people"] = {"registry_people_indexed": len(pc), "real_relationships": len(real),
                           "real_with_1plus_title_page": sum(1 for p in real if p["pages_with_name_in_title"]),
                           "real_with_no_title_page": sum(1 for p in real if not p["pages_with_name_in_title"])}
    with open(os.path.join(out_dir, "inventory-stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

def retag(out_dir):
    """Recompute the v1 tag columns in existing CSVs without touching the network.

    Use after changing the topic, triangle or stage rules. The full CSV is retagged
    from its own title, categories and tags; the slim sheet CSV (which has no
    categories or tags) copies the result by URL, so both files always agree.
    People columns and counts are not recomputed here; a full run does that.
    """
    changed = Counter()
    def load(name):
        with open(os.path.join(out_dir, name), newline="", encoding="utf-8") as f:
            rd = csv.DictReader(f)
            return rd.fieldnames, list(rd)
    def save(name, fields, rows):
        with open(os.path.join(out_dir, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    fields, rows = load("published-inventory.csv")
    by_url = {}
    for r in rows:
        text = " ".join([r.get("title", ""), r.get("categories", ""), r.get("tags", "")])
        new = {"topics_v1": tags_for(text, TOPICS), "nine_triangles_v1": tags_for(text, TRIANGLES),
               "factory_stage_v1": tags_for(r.get("title", ""), STAGES)}
        for k, v in new.items():
            if k in fields and r.get(k, "") != v:
                changed["published-inventory.csv:" + k] += 1
                r[k] = v
        by_url[r["url"]] = r
    save("published-inventory.csv", fields, rows)
    slim_name = "published-inventory-sheet.csv"
    if os.path.exists(os.path.join(out_dir, slim_name)):
        sfields, srows = load(slim_name)
        for r in srows:
            src = by_url.get(r["url"])
            if not src:
                continue
            for k in ("topics_v1", "nine_triangles_v1", "factory_stage_v1"):
                if k in sfields and r.get(k, "") != src.get(k, ""):
                    changed[slim_name + ":" + k] += 1
                    r[k] = src.get(k, "")
        save(slim_name, sfields, srows)
    return dict(changed)

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", help="JSON config (see the module docstring)")
    ap.add_argument("--out", required=True, help="folder for the outputs")
    ap.add_argument("--sites", help="comma-separated; overrides the config's sites")
    ap.add_argument("--old-lists", "--sheet-exports", dest="old_lists",
                    help="folder of <site>.json exports of the old hand-kept lists")
    ap.add_argument("--registry", help="people registry JSON")
    ap.add_argument("--retag-only", action="store_true",
                    help="recompute topic/triangle/stage tags in the CSVs already in --out; no network")
    a = ap.parse_args(argv)
    if a.config:
        with open(a.config, encoding="utf-8") as fh:
            apply_config(json.load(fh))
    if a.retag_only:
        print(json.dumps(retag(a.out), indent=1))
        return 0
    sites = [s.strip() for s in (a.sites.split(",") if a.sites else CONFIG["sites"]) if s.strip()]
    if not sites:
        ap.error("no sites: pass --sites or put \"sites\" in the config")
    stats = build(sites, a.out, a.old_lists, a.registry)
    print(json.dumps(stats, indent=1))
    return 0

if __name__ == "__main__":
    sys.exit(main())
