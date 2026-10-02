"""Export resumes to CSV / JSON / photo ZIP with stable ids and ISO dates. Used by the admin button and export.py (CLI).
Private data note: exports contain personal data (phone, email...). Handle accordingly."""
import os, io, csv, json, zipfile, shutil, time, hashlib
import config, db, options as O, resumes as R
from db import q, q1

SCHEMA_VERSION = 1
LIST_SEP = " | "
CSV_COLUMNS = ["resume_id", "user_id", "telegram_username_account", "status", "visibility", "admin_hidden", "featured",
               "full_name_fa", "stage_name", "gender", "birth_year", "age", "city", "height_cm", "weight_kg", "hair_color",
               "eye_color", "skin_tone", "roles", "experience_level", "skills", "languages", "skills_extra", "education",
               "awards", "phone", "telegram_username", "email", "instagram", "portfolio_links", "availability", "travel",
               "expected_fee", "bio", "demo_reel_url", "work_history_count", "work_history_json", "photo_count",
               "photo_files", "photo_file_ids", "created_at", "updated_at", "published_at"]

def _links(r):
    try: return json.loads(r["portfolio_links"]) if r["portfolio_links"] else []
    except Exception: return []

def build(include_drafts=True):
    """Nested structure for all resumes."""
    where = "" if include_drafts else "WHERE status='complete'"
    out = []
    for r in q(f"SELECT r.*, u.username AS account_username FROM resumes r LEFT JOIN users u ON u.id=r.user_id {where} ORDER BY r.id"):
        rid = r["id"]
        skills = R.skills_of(rid)
        work = [{"id": "W%06d" % h["id"], "position": h["position"], "title": h["title"], "type": h["work_type"], "role": h["role"],
                 "year": h["year"], "director_or_company": h["director_company"]} for h in R.history_of(rid)]
        media = [{"id": "M%06d" % m["id"], "seq": m["seq"], "kind": m["kind"], "file": ("photos/" + m["local_path"]) if m["local_path"] else None,
                  "telegram_file_id": m["telegram_file_id"], "telegram_unique_id": m["telegram_unique_id"], "bytes": m["bytes"],
                  "sha256": m["sha256"], "is_primary": bool(m["is_primary"]), "created_at": m["created_at"]} for m in R.media_of(rid)]
        out.append({
            "resume_id": R.rid_str(rid), "user_id": r["user_id"], "account_username": r["account_username"],
            "status": r["status"], "visibility": r["visibility"], "admin_hidden": bool(r["admin_hidden"]), "featured": bool(r["featured"]),
            "personal": {"full_name_fa": r["full_name_fa"], "stage_name": r["stage_name"], "gender": r["gender"],
                         "birth_year": r["birth_year"], "age": R.age_of(r), "city": r["city"]},
            "appearance": {"height_cm": r["height_cm"], "weight_kg": r["weight_kg"], "hair_color": r["hair_color"],
                           "eye_color": r["eye_color"], "skin_tone": r["skin_tone"]},
            "roles": R.roles_of(rid), "experience_level": r["experience_level"],
            "skills": [{"category": c, "code": k} for c, k in skills], "skills_extra": r["skills_extra"],
            "work_history": work, "education": r["education"], "awards": r["awards"],
            "contact": {"phone": r["phone"], "telegram_username": r["telegram_username"], "email": r["email"],
                        "instagram": r["instagram"], "portfolio_links": _links(r)},
            "availability": r["availability"], "travel": r["travel"], "expected_fee": r["expected_fee"],
            "bio": r["bio"], "demo_reel_url": r["demo_reel_url"], "media": media,
            "created_at": r["created_at"], "updated_at": r["updated_at"], "published_at": r["published_at"],
        })
    return out

def csv_rows(items):
    for it in items:
        p, a, c = it["personal"], it["appearance"], it["contact"]
        langs = [s["code"] for s in it["skills"] if s["category"] == "language"]
        others = ["%s:%s" % (s["category"], s["code"]) for s in it["skills"] if s["category"] != "language"]
        yield {"resume_id": it["resume_id"], "user_id": it["user_id"], "telegram_username_account": it["account_username"] or "",
               "status": it["status"], "visibility": it["visibility"], "admin_hidden": int(it["admin_hidden"]), "featured": int(it["featured"]),
               "full_name_fa": p["full_name_fa"], "stage_name": p["stage_name"], "gender": p["gender"], "birth_year": p["birth_year"],
               "age": p["age"], "city": p["city"], "height_cm": a["height_cm"], "weight_kg": a["weight_kg"], "hair_color": a["hair_color"],
               "eye_color": a["eye_color"], "skin_tone": a["skin_tone"], "roles": LIST_SEP.join(it["roles"]),
               "experience_level": it["experience_level"], "skills": LIST_SEP.join(others), "languages": LIST_SEP.join(langs),
               "skills_extra": it["skills_extra"], "education": it["education"], "awards": it["awards"], "phone": c["phone"],
               "telegram_username": c["telegram_username"], "email": c["email"], "instagram": c["instagram"],
               "portfolio_links": LIST_SEP.join(c["portfolio_links"]), "availability": it["availability"], "travel": it["travel"],
               "expected_fee": it["expected_fee"], "bio": it["bio"], "demo_reel_url": it["demo_reel_url"],
               "work_history_count": len(it["work_history"]), "work_history_json": json.dumps(it["work_history"], ensure_ascii=False),
               "photo_count": len(it["media"]), "photo_files": LIST_SEP.join(m["file"] for m in it["media"] if m["file"]),
               "photo_file_ids": LIST_SEP.join(m["telegram_file_id"] or "" for m in it["media"]),
               "created_at": it["created_at"], "updated_at": it["updated_at"], "published_at": it["published_at"]}

def _csv_safe(v):
    """Neutralise spreadsheet formula injection (=,+,-,@ at start of free text). Digits/phones with leading + are kept."""
    if isinstance(v, str) and v and v[0] in "=@\t\r" or (isinstance(v, str) and v[:1] in "+-" and not v[1:].replace(" ", "").isdigit()):
        return "'" + v
    return v

def write_csv(items, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:          # BOM so Excel shows Persian correctly
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for row in csv_rows(items):
            w.writerow({k: ("" if v is None else _csv_safe(v)) for k, v in row.items()})

def write_json(items, path):
    doc = {"schema_version": SCHEMA_VERSION, "exported_at": db.now_iso(), "count": len(items), "enums": O.enums_export(), "resumes": items}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

def photo_files(items):
    """[(zip name, absolute path)] for photos that exist on disk."""
    md = R.media_dir(); out = []
    for it in items:
        for m in it["media"]:
            if m["file"]:
                p = os.path.join(md, os.path.basename(m["file"]))
                if os.path.exists(p): out.append((m["file"], p))
    return out

def write_photo_zips(items, out_dir, part_bytes=config.ZIP_PART_BYTES, stamp=""):
    """photos.zip (split into photos-part1.zip ... if it would exceed part_bytes). Returns list of paths (may be empty)."""
    files = photo_files(items)
    if not files: return []
    parts, cur, size = [], [], 0
    for name, p in files:
        s = os.path.getsize(p)
        if cur and size + s > part_bytes: parts.append(cur); cur, size = [], 0
        cur.append((name, p)); size += s
    parts.append(cur)
    paths = []
    for i, part in enumerate(parts, 1):
        fn = "photos%s.zip" % ("" if len(parts) == 1 else "-part%d" % i)
        path = os.path.join(out_dir, fn)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
            for name, p in part: z.write(p, name)
        paths.append(path)
    return paths

def export_all(out_dir, include_drafts=True):
    """Write resumes.csv, resumes.json, photos*.zip, SCHEMA.md copy into out_dir. Returns dict of paths."""
    os.makedirs(out_dir, exist_ok=True)
    items = build(include_drafts)
    res = {"csv": os.path.join(out_dir, "resumes.csv"), "json": os.path.join(out_dir, "resumes.json")}
    write_csv(items, res["csv"]); write_json(items, res["json"])
    res["photos"] = write_photo_zips(items, out_dir)
    schema = os.path.join(config.BASE, "SCHEMA.md")
    if os.path.exists(schema):
        shutil.copy(schema, os.path.join(out_dir, "SCHEMA.md")); res["schema"] = os.path.join(out_dir, "SCHEMA.md")
    res["count"] = len(items)
    return res

def export_calls(out_dir):
    """calls.json — casting calls + applications (optional extra for the website)."""
    calls = []
    for c in q("SELECT * FROM calls ORDER BY id"):
        calls.append({"call_id": "C%06d" % c["id"], "user_id": c["user_id"], "title": c["title"], "project_type": c["project_type"],
                      "city": c["city"], "date": c["date_iso"], "date_text": c["date_text"], "details": c["details"], "contact": c["contact"],
                      "status": c["status"], "featured": bool(c["featured"]), "created_at": c["created_at"],
                      "imported": bool(c.get("source")),
                      "source": ({"channel": "@" + c["source"], "post_url": c["source_url"], "post_date": c["source_date"], "gender": c["gender_text"],
                                  "age": c["age_text"], "fee": c["fee_text"], "deadline": c["deadline_text"], "deadline_date": c["deadline_iso"],
                                  "contacts_as_published": json.loads(c["contacts"] or "{}"), "credit": "منبع: @%s — %s" % (c["source"], c["source_url"])}
                                 if c.get("source") else None),
                      "roles": [r["role"] for r in q("SELECT role FROM call_roles WHERE call_id=?", (c["id"],))],
                      "applications": [{"resume_id": R.rid_str(a["resume_id"]), "created_at": a["created_at"]}
                                       for a in q("SELECT * FROM applications WHERE call_id=? ORDER BY id", (c["id"],))]})
    path = os.path.join(out_dir, "calls.json")
    with open(path, "w", encoding="utf-8") as f: json.dump({"schema_version": SCHEMA_VERSION, "calls": calls}, f, ensure_ascii=False, indent=2)
    return path
