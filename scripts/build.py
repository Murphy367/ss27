#!/usr/bin/env python3
"""Build data.json for the parents' page from an SS27 board DB export.
Usage: python3 scripts/build.py <db_dir> <meta_status.json> <out data.json>
Only company / role / city / progress / dates are published. No resumes, contacts or notes."""
import json, glob, os, re, sys, datetime

db_dir, meta_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
jobs = []
for f in glob.glob(os.path.join(db_dir, "jobs", "*.json")):
    d = json.load(open(f)); d = d.get("data", d)
    jobs.append(d)
try:
    meta = json.load(open(meta_path)); meta = meta.get("data", meta)
except Exception:
    meta = {}

def clean(s):
    s = str(s or "").strip()
    return "" if s in ("（识别中）", "(识别中)") else s

def city(loc):
    loc = clean(loc)
    loc = re.split(r"[（(]", loc)[0].strip()
    loc = loc.replace(", CA", "").replace(", NY", "").replace(", NY,", "")
    return loc

STEP = {"已投递": "已投递", "在线测评": "在线测评", "面试中": "面试中", "Offer": "拿到 Offer", "已拒绝": "未通过"}
applied = []
for j in jobs:
    if j.get("status") != "applied":
        continue
    applied.append({
        "company": clean(j.get("company")) or "（公司信息补全中）",
        "title": clean(j.get("title")) or "（岗位信息补全中）",
        "city": city(j.get("location")),
        "progress": STEP.get(j.get("progress") or "已投递", "已投递"),
        "appliedAt": j.get("appliedAt") or "",
        "progressAt": j.get("progressAt") or j.get("appliedAt") or "",
    })
order = {"拿到 Offer": 0, "面试中": 1, "在线测评": 2, "已投递": 3, "未通过": 4}
applied.sort(key=lambda x: x["progressAt"] or "", reverse=True)
applied.sort(key=lambda x: order[x["progress"]])

watching = [j for j in jobs if j.get("origin") != "self" and j.get("stage") == "open"
            and j.get("status") not in ("applied", "hidden")]
upcoming = sorted({re.split(r"[（(]", clean(j.get("company")))[0].strip()
                   for j in jobs if j.get("stage") == "upcoming" and j.get("status") != "applied"})

counts = {k: sum(1 for a in applied if a["progress"] == k) for k in order}
data = {
    "updated": meta.get("lastRun") or datetime.date.today().isoformat(),
    "generatedAt": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "total": len(applied),
    "counts": counts,
    "watching": len(watching),
    "upcoming": upcoming,
    "applied": applied,
}
json.dump(data, open(out, "w"), ensure_ascii=False, indent=1)
print(f"applied={len(applied)} watching={len(watching)} upcoming={len(upcoming)}")
