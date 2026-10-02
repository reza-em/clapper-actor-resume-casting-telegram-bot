"""Resume data layer: validation, CRUD on normalized tables, photo media, card rendering, search."""
import os, re, json, hashlib, logging
import config, db, fa, options as O, logic
from db import tx, q, q1, val, ex

log = logging.getLogger("resumes")

SCALARS = ["full_name_fa", "stage_name", "gender", "birth_year", "city", "height_cm", "weight_kg", "hair_color", "eye_color",
           "skin_tone", "experience_level", "skills_extra", "education", "awards", "phone", "telegram_username", "email",
           "instagram", "portfolio_links", "availability", "travel", "expected_fee", "bio", "demo_reel_url"]
REQUIRED = ["full_name_fa", "gender", "birth_year", "city", "roles"]     # 'roles' = at least one role

def rid_str(rid): return "R%06d" % int(rid)

# ---------------- validation (text steps) ----------------
URL_RE = re.compile(r"^https?://[^\s]{4,300}$", re.I)
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

def city_canon(text):
    t = fa.norm(text)
    for cfa, cen in O.CITIES:
        if t in (fa.norm(cfa), fa.norm(cen)): return cfa
    return fa.clean(text, 40)

def validate(field, text):
    """-> (value, None) or (None, error_key)."""
    t = fa.clean(text, 3000)
    if field in ("full_name_fa", "stage_name"):
        if len(t) < 2 or len(t) > 60 or URL_RE.match(t) or re.fullmatch(r"[\d\s]+", fa.digits(t)): return None, "err_name"
        return t, None
    if field == "birth_year":
        n = fa.digits(t).strip()
        if not re.fullmatch(r"\d{4}", n): return None, "err_year"
        y = fa.birth_to_gregorian(int(n), db.this_year())
        return (y, None) if y else (None, "err_year")
    if field == "city":
        if len(t) < 2 or len(t) > 40: return None, "err_city"
        return city_canon(t), None
    if field == "height_cm":
        n = fa.digits(t).strip().replace("cm", "").strip()
        return (int(n), None) if re.fullmatch(r"\d{3}", n) and 100 <= int(n) <= 230 else (None, "err_height")
    if field == "weight_kg":
        n = fa.digits(t).strip().lower().replace("kg", "").strip()
        return (int(n), None) if re.fullmatch(r"\d{2,3}", n) and 25 <= int(n) <= 250 else (None, "err_weight")
    if field == "phone":
        p = re.sub(r"[\s\-()]", "", fa.digits(t))
        return (p, None) if re.fullmatch(r"\+?\d{10,15}", p) else (None, "err_phone")
    if field == "telegram_username":
        u = logic.clean_username(t)
        return (u, None) if u else (None, "err_tg")
    if field == "email":
        return (t.lower(), None) if EMAIL_RE.match(t) and len(t) <= 120 else (None, "err_email")
    if field == "instagram":
        u = t
        m = re.search(r"instagram\.com/([A-Za-z0-9._]+)", u)
        if m: u = m.group(1)
        u = u.lstrip("@").strip().lower()
        return (u, None) if re.fullmatch(r"[a-z0-9._]{1,30}", u) else (None, "err_insta")
    if field == "portfolio_links":
        links = [x for x in re.split(r"[\s,،]+", t) if x]
        if not links or len(links) > 5 or any(not URL_RE.match(x) for x in links): return None, "err_links"
        return json.dumps(links), None
    if field == "demo_reel_url":
        return (t, None) if URL_RE.match(t) else (None, "err_url")
    if field == "expected_fee":
        return (t[:80], None) if t else (None, "err_empty")
    if field in ("education", "awards", "skills_extra"):
        return (fa.clean(text, 500), None) if t else (None, "err_empty")
    if field == "bio":
        return (fa.clean(text, 500), None) if len(t) >= 3 else (None, "err_empty")
    if field == "work_title":
        return (t[:80], None) if len(t) >= 2 else (None, "err_empty")
    if field == "work_role":
        return (t[:60], None) if len(t) >= 2 else (None, "err_empty")
    if field == "work_year":
        n = fa.digits(t).strip()
        if re.fullmatch(r"\d{4}", n):
            y = int(n)
            if 1300 <= y <= 1500: y += 621
            if 1900 <= y <= db.this_year() + 1: return y, None
        return None, "err_year2"
    if field == "work_company":
        return (t[:80], None) if len(t) >= 2 else (None, "err_empty")
    return None, "err_empty"

# ---------------- CRUD ----------------
def get_by_user(uid):
    return q1("SELECT * FROM resumes WHERE user_id=?", (int(uid),))

def get(rid):
    return q1("SELECT * FROM resumes WHERE id=?", (int(rid),))

def ensure(uid):
    with tx():
        r = get_by_user(uid)
        if r: return r
        t = db.now_iso()
        ex("INSERT INTO resumes(user_id, created_at, updated_at) VALUES(?,?,?)", (int(uid), t, t))
        return get_by_user(uid)

def set_field(rid, field, value):
    if field not in SCALARS: raise KeyError(field)
    with tx():
        ex(f"UPDATE resumes SET {field}=?, updated_at=? WHERE id=?", (value, db.now_iso(), int(rid)))
        reindex(rid)

def clear_field(rid, field):
    set_field(rid, field, None)

def set_step(rid, step):
    ex("UPDATE resumes SET wiz_step=? WHERE id=?", (int(step), int(rid)))

def roles_of(rid): return [r["role"] for r in q("SELECT role FROM roles WHERE resume_id=? ORDER BY rowid", (int(rid),))]
def skills_of(rid): return [(r["category"], r["code"]) for r in q("SELECT category, code FROM skills WHERE resume_id=? ORDER BY rowid", (int(rid),))]
def history_of(rid): return q("SELECT * FROM work_history WHERE resume_id=? ORDER BY position, id", (int(rid),))
def media_of(rid): return q("SELECT * FROM media WHERE resume_id=? ORDER BY seq", (int(rid),))

def toggle_role(rid, role):
    if role not in O.codes(O.ROLES): return None
    with tx():
        if q1("SELECT 1 FROM roles WHERE resume_id=? AND role=?", (int(rid), role)):
            ex("DELETE FROM roles WHERE resume_id=? AND role=?", (int(rid), role)); on = False
        else:
            ex("INSERT INTO roles(resume_id, role) VALUES(?,?)", (int(rid), role)); on = True
        ex("UPDATE resumes SET updated_at=? WHERE id=?", (db.now_iso(), int(rid))); reindex(rid); return on

def toggle_skill(rid, cat, code):
    if cat not in O.SKILL_CATS or code not in O.codes(O.SKILL_CATS[cat][2]): return None
    with tx():
        if q1("SELECT 1 FROM skills WHERE resume_id=? AND category=? AND code=?", (int(rid), cat, code)):
            ex("DELETE FROM skills WHERE resume_id=? AND category=? AND code=?", (int(rid), cat, code)); on = False
        else:
            ex("INSERT INTO skills(resume_id, category, code) VALUES(?,?,?)", (int(rid), cat, code)); on = True
        ex("UPDATE resumes SET updated_at=? WHERE id=?", (db.now_iso(), int(rid))); reindex(rid); return on

def add_history(rid, title, work_type, role, year, company=None):
    with tx():
        if val("SELECT COUNT(*) FROM work_history WHERE resume_id=?", (int(rid),)) >= 30: return None
        pos = val("SELECT COALESCE(MAX(position),0)+1 FROM work_history WHERE resume_id=?", (int(rid),))
        hid = ex("INSERT INTO work_history(resume_id, position, title, work_type, role, year, director_company) VALUES(?,?,?,?,?,?,?)",
                 (int(rid), pos, title, work_type if work_type in O.codes(O.WORK_TYPES) else "other", role, year, company)).lastrowid
        ex("UPDATE resumes SET updated_at=? WHERE id=?", (db.now_iso(), int(rid))); reindex(rid); return hid

def update_history(hid, rid, **kw):
    ok = {"title", "work_type", "role", "year", "director_company"}
    with tx():
        for k, v in kw.items():
            if k in ok: ex(f"UPDATE work_history SET {k}=? WHERE id=? AND resume_id=?", (v, int(hid), int(rid)))
        reindex(rid)

def delete_history(hid, rid):
    with tx():
        n = ex("DELETE FROM work_history WHERE id=? AND resume_id=?", (int(hid), int(rid))).rowcount
        reindex(rid); return n > 0

def missing_required(rid):
    r = get(rid); out = []
    for f in REQUIRED:
        if f == "roles":
            if not roles_of(rid): out.append(f)
        elif r.get(f) in (None, ""): out.append(f)
    return out

def publish(rid):
    with tx():
        if missing_required(rid): return False
        ex("UPDATE resumes SET status='complete', published_at=COALESCE(published_at, ?), updated_at=? WHERE id=?",
           (db.now_iso(), db.now_iso(), int(rid))); return True

def set_visibility(rid, vis):
    ex("UPDATE resumes SET visibility=? WHERE id=?", ("public" if vis == "public" else "hidden", int(rid)))

def admin_set(rid, key, flag):
    if key not in ("admin_hidden", "featured"): raise KeyError(key)
    ex(f"UPDATE resumes SET {key}=? WHERE id=?", (1 if flag else 0, int(rid)))

def is_listed(r):
    return r["status"] == "complete" and r["visibility"] == "public" and not r["admin_hidden"]

# ---------------- media ----------------
def media_dir(): return config.MEDIA_DIR if db.get_path() == config.DB_PATH else os.path.join(os.path.dirname(db.get_path()), "media")

def media_filename(rid, seq, ext="jpg"): return "%s_%02d.%s" % (rid_str(rid), seq, ext)

def add_photo(rid, file_id, unique_id, downloader=None, ext="jpg"):
    """Store a Telegram photo: file_ids in DB + file on disk (downloader(file_id, dest)->bytes). Returns media row or None (limit)."""
    with tx():
        if val("SELECT COUNT(*) FROM media WHERE resume_id=?", (int(rid),)) >= config.MAX_PHOTOS: return None
        if unique_id and q1("SELECT 1 FROM media WHERE resume_id=? AND telegram_unique_id=?", (int(rid), unique_id)): return "dup"
        seq = val("SELECT COALESCE(MAX(seq),0)+1 FROM media WHERE resume_id=?", (int(rid),))
        first = val("SELECT COUNT(*) FROM media WHERE resume_id=?", (int(rid),)) == 0
        mid = ex("INSERT INTO media(resume_id, seq, kind, telegram_file_id, telegram_unique_id, is_primary, created_at) VALUES(?,?,?,?,?,?,?)",
                 (int(rid), seq, "photo", file_id, unique_id, 1 if first else 0, db.now_iso())).lastrowid
        ex("UPDATE resumes SET updated_at=? WHERE id=?", (db.now_iso(), int(rid)))
    fetch_media(mid, downloader, ext)
    return q1("SELECT * FROM media WHERE id=?", (mid,))

def fetch_media(mid, downloader, ext="jpg"):
    """Download the file of one media row to media/<R000012_01.jpg>. Returns True on success."""
    m = q1("SELECT * FROM media WHERE id=?", (int(mid),))
    if not m or not downloader: return False
    fn = media_filename(m["resume_id"], m["seq"], ext)
    dest = os.path.join(media_dir(), fn)
    try:
        n = downloader(m["telegram_file_id"], dest)
    except Exception as e:                       # network / API trouble: keep the file_id, retry later
        log.warning("photo download failed for %s: %s", fn, type(e).__name__)
        return False
    h = hashlib.sha256(open(dest, "rb").read()).hexdigest()
    ex("UPDATE media SET local_path=?, bytes=?, sha256=? WHERE id=?", (fn, n, h, int(mid)))
    return True

def backfill_media(downloader):
    """Retry downloads of media rows whose file is missing on disk. Returns (ok, failed)."""
    ok = bad = 0
    for m in q("SELECT * FROM media"):
        if m["local_path"] and os.path.exists(os.path.join(media_dir(), m["local_path"])): continue
        if fetch_media(m["id"], downloader): ok += 1
        else: bad += 1
    return ok, bad

def delete_photo(rid, mid):
    with tx():
        m = q1("SELECT * FROM media WHERE id=? AND resume_id=?", (int(mid), int(rid)))
        if not m: return False
        ex("DELETE FROM media WHERE id=?", (int(mid),))
        if m["local_path"]:
            try: os.remove(os.path.join(media_dir(), m["local_path"]))
            except OSError: pass
        if m["is_primary"]:
            nxt = q1("SELECT id FROM media WHERE resume_id=? ORDER BY seq LIMIT 1", (int(rid),))
            if nxt: ex("UPDATE media SET is_primary=1 WHERE id=?", (nxt["id"],))
        return True

def primary_file_id(rid):
    m = q1("SELECT telegram_file_id FROM media WHERE resume_id=? ORDER BY is_primary DESC, seq LIMIT 1", (int(rid),))
    return m["telegram_file_id"] if m else None

def delete_all_media_files(rid):
    for m in media_of(rid):
        if m["local_path"]:
            try: os.remove(os.path.join(media_dir(), m["local_path"]))
            except OSError: pass

# ---------------- search index ----------------
def reindex(rid):
    r = get(rid)
    if not r: return
    parts = [r["full_name_fa"], r["stage_name"], r["city"], r["skills_extra"], r["bio"], r["education"], r["awards"]]
    for role in roles_of(rid):
        parts += [O.plain(O.label(O.ROLES, role, "fa")), O.plain(O.label(O.ROLES, role, "en"))]
    for cat, code in skills_of(rid):
        parts += [O.skill_label(cat, code, "fa"), O.skill_label(cat, code, "en")]
    for h in history_of(rid):
        parts += [h["title"], h["role"], h["director_company"]]
    ex("UPDATE resumes SET search_text=?, name_norm=?, city_norm=? WHERE id=?",
       (fa.norm(" ".join(str(p) for p in parts if p)), fa.norm(" ".join(x for x in [r["full_name_fa"], r["stage_name"]] if x)),
        fa.norm(r["city"] or ""), int(rid)))

# ---------------- search ----------------
FILTER_KEYS = ("q", "name", "city", "role", "skill", "gender", "age_min", "age_max", "h_min", "h_max", "language", "exp", "featured")

def _like(tok):
    return "%" + tok.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"

def search(filters, admin=False, page=1, per=config.PAGE_SIZE):
    """-> (rows, page, pages, total). Non-admins only see public, complete, non-hidden resumes."""
    w, a = ["r.status='complete'"], []
    if not admin: w.append("r.visibility='public' AND r.admin_hidden=0")
    f = filters or {}
    for tok in fa.norm(f.get("q") or "").split():
        w.append("r.search_text LIKE ? ESCAPE '\\'"); a.append(_like(tok))
    for tok in fa.norm(f.get("name") or "").split():
        w.append("r.name_norm LIKE ? ESCAPE '\\'"); a.append(_like(tok))
    if f.get("city"): w.append("r.city_norm=?"); a.append(fa.norm(city_canon(f["city"])))
    if f.get("role"): w.append("EXISTS(SELECT 1 FROM roles x WHERE x.resume_id=r.id AND x.role=?)"); a.append(f["role"])
    if f.get("skill"):
        cat, _, code = f["skill"].partition(":")
        w.append("EXISTS(SELECT 1 FROM skills x WHERE x.resume_id=r.id AND x.category=? AND x.code=?)"); a += [cat, code]
    if f.get("language"): w.append("EXISTS(SELECT 1 FROM skills x WHERE x.resume_id=r.id AND x.category='language' AND x.code=?)"); a.append(f["language"])
    if f.get("gender"): w.append("r.gender=?"); a.append(f["gender"])
    if f.get("exp"): w.append("r.experience_level=?"); a.append(f["exp"])
    y = db.this_year()
    if f.get("age_min") is not None: w.append("r.birth_year IS NOT NULL AND r.birth_year<=?"); a.append(y - int(f["age_min"]))
    if f.get("age_max") is not None: w.append("r.birth_year IS NOT NULL AND r.birth_year>=?"); a.append(y - int(f["age_max"]))
    if f.get("h_min") is not None: w.append("r.height_cm IS NOT NULL AND r.height_cm>=?"); a.append(int(f["h_min"]))
    if f.get("h_max") is not None: w.append("r.height_cm IS NOT NULL AND r.height_cm<=?"); a.append(int(f["h_max"]))
    if f.get("featured"): w.append("r.featured=1")
    where = " AND ".join(w)
    total = val(f"SELECT COUNT(*) FROM resumes r WHERE {where}", a, 0)
    pages = max(1, (total + per - 1) // per); page = min(max(1, page), pages)
    rows = q(f"SELECT r.* FROM resumes r WHERE {where} ORDER BY r.featured DESC, r.updated_at DESC, r.id DESC LIMIT ? OFFSET ?",
             (*a, per, (page - 1) * per))
    return rows, page, pages, total

# ---------------- rendering ----------------
def age_of(r):
    return db.this_year() - int(r["birth_year"]) if r.get("birth_year") else None

def _e(t):
    return str(t if t is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _n(lang, x):
    s = str(x)
    return fa.to_fa_digits(s) if lang == "fa" else s

def display_name(r):
    return r.get("stage_name") or r.get("full_name_fa") or ("#" + rid_str(r["id"]))

def _lbl(lst, code, lang):
    return O.plain(O.label(lst, code, lang)) if code else ""

def card(r, lang, full=True, contact=True, admin_tags=False):
    """Nicely formatted HTML resume card. compact (full=False) hides sections and never shows contact info."""
    from texts import T
    t = T[lang]; rid = r["id"]
    lines = []
    head = "⭐ " if r.get("featured") else ""
    head += "<b>%s</b>" % _e(r.get("full_name_fa") or "—")
    if r.get("stage_name"): head += " · <i>%s</i>" % _e(r["stage_name"])
    lines.append("🎭 " + head)
    bits = []
    if r.get("gender"): bits.append(_lbl(O.GENDER, r["gender"], lang))
    if age_of(r): bits.append(t["c_age"].format(n=_n(lang, age_of(r))))
    if r.get("city"):
        bits.append(_e(r["city"] if lang == "fa" else next((en for cf, en in O.CITIES if cf == r["city"]), r["city"])))
    if bits: lines.append("👤 " + " · ".join(bits))
    roles = roles_of(rid)
    if roles: lines.append("🎬 " + "، ".join(_lbl(O.ROLES, x, lang) for x in roles) if lang == "fa" else "🎬 " + ", ".join(_lbl(O.ROLES, x, lang) for x in roles))
    if r.get("experience_level"): lines.append("⭐ " + _lbl(O.EXPERIENCE, r["experience_level"], lang))
    sk = skills_of(rid)
    sep = "، " if lang == "fa" else ", "
    if not full:
        if sk: lines.append("🛠 " + sep.join(O.skill_label(c, k, lang) for c, k in sk[:6]) + (" …" if len(sk) > 6 else ""))
        hs = history_of(rid)
        if hs: lines.append("📽 " + t["c_works"].format(n=_n(lang, len(hs))))
        lines.append("🆔 <code>%s</code>" % rid_str(rid))
        if admin_tags: lines.append(_admin_tag(r, lang))
        return "\n".join(lines)
    body = []
    if r.get("height_cm") or r.get("weight_kg"):
        b = []
        if r.get("height_cm"): b.append(t["c_height"].format(n=_n(lang, r["height_cm"])))
        if r.get("weight_kg"): b.append(t["c_weight"].format(n=_n(lang, r["weight_kg"])))
        body.append("📏 " + " · ".join(b))
    look = []
    if r.get("hair_color"): look.append(t["c_hair"] + " " + _lbl(O.HAIR, r["hair_color"], lang))
    if r.get("eye_color"): look.append(t["c_eyes"] + " " + _lbl(O.EYES, r["eye_color"], lang))
    if r.get("skin_tone"): look.append(t["c_skin"] + " " + _lbl(O.SKIN, r["skin_tone"], lang))
    if look: body.append("👁 " + " · ".join(look))
    if sk:
        cats = {}
        for c, k in sk: cats.setdefault(c, []).append(O.skill_label(c, k, lang))
        for c, items in cats.items():
            body.append("%s: %s" % (O.skill_cat_label(c, lang), sep.join(items)))
    if r.get("skills_extra"): body.append("🛠 " + _e(r["skills_extra"]))
    hs = history_of(rid)
    if hs:
        body.append("\n📽 <b>%s</b>" % t["c_history"])
        for h in hs:
            bit = "• <b>%s</b> (%s)" % (_e(h["title"]), _lbl(O.WORK_TYPES, h["work_type"], lang))
            more = [x for x in [h["role"], _n(lang, h["year"]) if h["year"] else "", h["director_company"]] if x]
            if more: bit += " — " + _e(" · ".join(str(m) for m in more))
            body.append(bit)
    if r.get("education"): body.append("\n🎓 <b>%s</b>\n%s" % (t["c_education"], _e(r["education"])))
    if r.get("awards"): body.append("\n🏆 <b>%s</b>\n%s" % (t["c_awards"], _e(r["awards"])))
    ex_ = []
    if r.get("availability"): ex_.append("🗓 " + _lbl(O.AVAILABILITY, r["availability"], lang))
    if r.get("travel"): ex_.append("🧳 " + _lbl(O.TRAVEL, r["travel"], lang))
    if r.get("expected_fee"): ex_.append("💰 " + _e(r["expected_fee"]))
    if ex_: body.append("\n" + "\n".join(ex_))
    if r.get("bio"): body.append("\n📝 " + _e(r["bio"]))
    if r.get("demo_reel_url"): body.append("🎞 %s: %s" % (t["c_reel"], _e(r["demo_reel_url"])))
    try: links = json.loads(r["portfolio_links"]) if r.get("portfolio_links") else []
    except Exception: links = []
    if links: body.append("🔗 " + "\n🔗 ".join(_e(l) for l in links))
    if contact:
        c = []
        if r.get("phone"): c.append("📞 <code>%s</code>" % _e(r["phone"]))
        if r.get("telegram_username"): c.append("✈️ @%s" % _e(r["telegram_username"]))
        if r.get("email"): c.append("✉️ %s" % _e(r["email"]))
        if r.get("instagram"): c.append("📸 instagram.com/%s" % _e(r["instagram"]))
        if c: body.append("\n<b>%s</b>\n%s" % (t["c_contact"], "\n".join(c)))
    lines += body
    lines.append("\n🆔 <code>%s</code>" % rid_str(rid))
    if admin_tags: lines.append(_admin_tag(r, lang))
    return "\n".join(lines)

def _admin_tag(r, lang):
    from texts import T
    tags = []
    if r["status"] != "complete": tags.append(T[lang]["tag_draft"])
    if r["visibility"] == "hidden": tags.append(T[lang]["tag_hidden_user"])
    if r["admin_hidden"]: tags.append(T[lang]["tag_hidden_admin"])
    if r["featured"]: tags.append(T[lang]["tag_featured"])
    return " ".join(tags)

# ---------------- delete ----------------
def delete_resume(rid):
    with tx():
        delete_all_media_files(rid)
        ex("DELETE FROM resumes WHERE id=?", (int(rid),))         # cascades to work_history/skills/roles/media
        ex("DELETE FROM applications WHERE resume_id=?", (int(rid),))

def delete_user_data(uid):
    """Erase everything personal about a user. The user row is kept only as an anonymous ban/audit stub."""
    with tx():
        r = get_by_user(uid)
        if r: delete_resume(r["id"])
        ex("DELETE FROM calls WHERE user_id=? AND source IS NULL", (int(uid),))      # channel-imported calls are not the user's personal data
        ex("DELETE FROM applications WHERE user_id=?", (int(uid),))
        ex("DELETE FROM views WHERE viewer_id=?", (int(uid),))
        banned = val("SELECT banned FROM users WHERE id=?", (int(uid),), 0)
        holds_imports = val("SELECT COUNT(*) FROM calls WHERE user_id=?", (int(uid),), 0)     # FK: keep an anonymous stub row
        if banned or holds_imports:
            ex("UPDATE users SET username=NULL, name=NULL, casting_name=NULL, casting_about=NULL, casting_status='none', consent_at=NULL, awaiting=NULL, await_data=NULL, search_filters=NULL WHERE id=?", (int(uid),))
        else:
            ex("DELETE FROM users WHERE id=?", (int(uid),))
