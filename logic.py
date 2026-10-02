"""Business logic (no Telegram calls): users, admins, settings, support/FAQ, plans, quotas, ads, referrals, stats."""
import json, time, copy, re
import config, db
from db import tx, q, q1, val, ex

DEFAULT_SETTINGS = {
    "free_views_month": 5,      # full resume views per month for casting/paid searchers without a plan
    "free_apps_month": 5,       # applications to casting calls per month for actors
    "free_posts_month": 2,      # casting calls per month for casting accounts
    "search_casting": True,     # approved casting accounts may use search
    "casting_approval": False,  # admin must approve casting accounts
    "ref_enabled": True, "ref_bonus": 3, "ref_invitee_bonus": 1,   # bonus = extra credits (each credit = 1 extra action)
    "ads_enabled": True, "ad_every": 6,
    "export_extra_admins": False,
    "import_auto_publish": False,   # imported (channel) calls: False = every one waits for admin approval
}
NUM_SETTINGS = ("free_views_month", "free_apps_month", "free_posts_month", "ref_bonus", "ref_invitee_bonus", "ad_every")
BOOL_SETTINGS = ("search_casting", "casting_approval", "ref_enabled", "ads_enabled", "export_extra_admins", "import_auto_publish")
MAX_PLANS = 10
MAX_ADS = 30
ACTIVE_WINDOW = 7 * 86400
UNLIMITED = -1

def now(): return db.now()
def fmt_date(ts): return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))

# ---------------- settings ----------------
def settings():
    s = dict(DEFAULT_SETTINGS); s.update(db.meta_get("settings", {}) or {}); return s

def set_setting(key, value):
    with tx():
        s = db.meta_get("settings", {}) or {}
        if key in NUM_SETTINGS: s[key] = int(value)
        elif key in BOOL_SETTINGS: s[key] = bool(value)
        else: raise KeyError(key)
        db.meta_set("settings", s)

def toggle_setting(key):
    with tx():
        v = not settings()[key]; set_setting(key, v); return v

# ---------------- users ----------------
def _row_user(r):
    if not r: return {}
    for k in ("await_data", "search_filters"):
        try: r[k] = json.loads(r[k]) if r.get(k) else ({} if k == "await_data" else {})
        except Exception: r[k] = {}
    return r

def get_user(uid):
    return _row_user(q1("SELECT * FROM users WHERE id=?", (int(uid),)))

def update_user(uid, **kw):
    if not kw: return
    for k in ("await_data", "search_filters"):
        if k in kw and kw[k] is not None and not isinstance(kw[k], str):
            kw[k] = json.dumps(kw[k], ensure_ascii=False)
    cols = ", ".join(f"{k}=?" for k in kw)
    ex(f"UPDATE users SET {cols} WHERE id=?", (*kw.values(), int(uid)))

def touch_user(tg):
    """Register/refresh a Telegram user. Returns (is_new, user)."""
    uid = int(tg["id"])
    name = " ".join(x for x in [tg.get("first_name"), tg.get("last_name")] if x)[:64]
    un = (tg.get("username") or "").lower() or None
    with tx():
        is_new = q1("SELECT id FROM users WHERE id=?", (uid,)) is None
        if is_new:
            ex("INSERT INTO users(id, first_seen) VALUES(?,?)", (uid, db.now_iso()))
        ex("UPDATE users SET username=?, name=?, language_code=COALESCE(?, language_code), last_seen=? WHERE id=?",
           (un, name, tg.get("language_code"), db.now_iso(), uid))
    return is_new, get_user(uid)

def owner_id():
    return db.meta_get("owner_id")

def bind_owner_if_needed(tg):
    """Owner numeric id is pre-set from config; if it was ever cleared, the first message from @OWNER_USERNAME binds it."""
    if (tg.get("username") or "").lower() != config.OWNER_USERNAME.lower():
        return False
    with tx():
        if db.meta_get("owner_id"): return False
        db.meta_set("owner_id", int(tg["id"])); return True

def is_owner(uid):
    o = owner_id(); return o is not None and int(uid) == int(o)

def is_admin(uid):
    if is_owner(uid): return True
    return bool(val("SELECT is_admin FROM users WHERE id=?", (int(uid),), 0))

def list_admins():
    return [r["id"] for r in q("SELECT id FROM users WHERE is_admin=1 ORDER BY id")]

def add_admin(uid):
    with tx():
        if is_owner(uid) or not q1("SELECT id FROM users WHERE id=?", (int(uid),)): return False
        ex("UPDATE users SET is_admin=1 WHERE id=?", (int(uid),)); return True

def remove_admin(uid):
    with tx():
        n = ex("UPDATE users SET is_admin=0 WHERE id=? AND is_admin=1", (int(uid),)).rowcount; return n > 0

def set_owner(new_uid):
    with tx():
        db.meta_set("owner_id", int(new_uid))
        ex("UPDATE users SET is_admin=0 WHERE id=?", (int(new_uid),))

def is_banned(uid):
    return bool(val("SELECT banned FROM users WHERE id=?", (int(uid),), 0))

def set_banned(uid, flag):
    ex("UPDATE users SET banned=? WHERE id=?", (1 if flag else 0, int(uid)))

def find_user(qs):
    """Exact lookup by numeric id or @username -> id or None."""
    qs = (qs or "").strip()
    if qs.lstrip("-").isdigit():
        return int(qs) if q1("SELECT id FROM users WHERE id=?", (int(qs),)) else None
    qs = qs.lstrip("@").lower()
    if not qs: return None
    r = q1("SELECT id FROM users WHERE username=?", (qs,))
    return r["id"] if r else None

def search_users(qs, limit=30):
    """Numeric id, @username or name substring."""
    qs = (qs or "").strip()
    if not qs: return []
    if qs.lstrip("-").isdigit():
        return q("SELECT * FROM users WHERE id=?", (int(qs),))
    like = "%" + qs.lstrip("@").lower().replace("%", "").replace("_", "\\_") + "%"
    return q("SELECT * FROM users WHERE lower(username) LIKE ? ESCAPE '\\' OR lower(name) LIKE ? ESCAPE '\\' "
             "OR lower(COALESCE(casting_name,'')) LIKE ? ESCAPE '\\' ORDER BY last_seen DESC LIMIT ?", (like, like, like, limit))

def users_page(page, per=8):
    total = val("SELECT COUNT(*) FROM users", (), 0)
    pages = max(1, (total + per - 1) // per); page = min(max(1, page), pages)
    rows = q("SELECT * FROM users ORDER BY last_seen DESC, id DESC LIMIT ? OFFSET ?", (per, (page - 1) * per))
    return rows, page, pages, total

USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{4,31}$")
def clean_username(s):
    s = (s or "").strip()
    for pre in ("https://t.me/", "http://t.me/", "t.me/", "@"):
        if s.lower().startswith(pre): s = s[len(pre):]
    return s if USERNAME_RE.match(s) else None

# ---------------- support / faq ----------------
def support():
    d = {"primary": config.DEFAULT_SUPPORT_PRIMARY, "backup": ""}
    d.update(db.meta_get("support", {}) or {}); return d

def set_support(slot, name):
    with tx():
        if slot == "primary" and not name: return False
        s = support(); s[slot] = name or ""; db.meta_set("support", s); return True

DEFAULT_FAQ = [
    {"q_fa": "رزومه‌ام را چطور بسازم؟", "a_fa": "از منوی اصلی «📝 ساخت رزومه» را بزن و مرحله‌به‌مرحله جواب بده. هر مرحله را می‌توانی رد کنی یا برگردی؛ پیشرفتت خودکار ذخیره می‌شود.",
     "q_en": "How do I build my resume?", "a_en": "Tap “📝 Build resume” in the main menu and answer step by step. You can skip or go back on any step; progress is saved automatically."},
    {"q_fa": "چه کسانی رزومه‌ام را می‌بینند؟", "a_fa": "فقط کارگردان‌ها و تهیه‌کننده‌هایی که در ربات ثبت‌نام کرده‌اند (و مدیران). هر وقت خواستی از «رزومه من» آن را مخفی کن.",
     "q_en": "Who can see my resume?", "a_en": "Only registered casting directors / producers (and admins). You can hide it any time from “My resume”."},
    {"q_fa": "چطور اطلاعاتم را پاک کنم؟", "a_fa": "«⚙️ بیشتر ← 🗑 حذف اطلاعات من» را بزن؛ رزومه، عکس‌ها و اطلاعات شخصی‌ات کامل پاک می‌شود.",
     "q_en": "How do I delete my data?", "a_en": "Tap “⚙️ More → 🗑 Delete my data”; your resume, photos and personal data are erased completely."},
    {"q_fa": "پلن پولی چطور فعال می‌شود؟", "a_fa": "پرداخت بیرون از ربات و با هماهنگی پشتیبانی انجام می‌شود؛ ربات هیچ شماره کارت یا رسیدی نمی‌گیرد. بعد از هماهنگی، ادمین پلن را برایت فعال می‌کند.",
     "q_en": "How do I get a paid plan?", "a_en": "Payment is arranged outside the bot with support; the bot never collects card numbers or receipts. After that an admin activates the plan for you."},
    {"q_fa": "من کارگردان/تهیه‌کننده‌ام؛ چطور آگهی بدهم؟", "a_fa": "«🎭 آگهی‌ها ← 🎬 من کارگردان/تولید هستم» را بزن، ثبت‌نام کن و بعد آگهی جدید بساز.",
     "q_en": "I'm a director/producer; how do I post a call?", "a_en": "Tap “🎭 Calls → 🎬 I'm a director/producer”, register, then create a new call."},
]

def faq():
    f = db.meta_get("faq")
    return copy.deepcopy(DEFAULT_FAQ) if f is None else f

def faq_save(items):
    db.meta_set("faq", items)

def faq_add(q_fa, a_fa, q_en="", a_en=""):
    with tx():
        f = faq()
        if len(f) >= 30: return False
        f.append({"q_fa": q_fa[:200], "a_fa": a_fa[:1500], "q_en": (q_en or q_fa)[:200], "a_en": (a_en or a_fa)[:1500]})
        faq_save(f); return True

def faq_update(i, **kw):
    with tx():
        f = faq()
        if not 0 <= i < len(f): return False
        for k, v in kw.items():
            if k in ("q_fa", "a_fa", "q_en", "a_en"): f[i][k] = str(v)[:200 if k[0] == "q" else 1500]
        faq_save(f); return True

def faq_delete(i):
    with tx():
        f = faq()
        if not 0 <= i < len(f): return False
        f.pop(i); faq_save(f); return True

# ---------------- plans (display-only; granted manually) ----------------
def plans():
    return q("SELECT * FROM plans ORDER BY position, id")

def get_plan(pid):
    return q1("SELECT * FROM plans WHERE id=?", (int(pid),))

def plan_ready(p):
    return bool((p.get("price") or "").strip())

def add_plan(title, price, duration="", features="", popular=False, views=0, apps=0, posts=0, days=30):
    with tx():
        if val("SELECT COUNT(*) FROM plans") >= MAX_PLANS: return None
        pos = val("SELECT COALESCE(MAX(position),0)+1 FROM plans")
        return ex("INSERT INTO plans(position,title,price,duration,features,popular,views_month,apps_month,posts_month,days) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (pos, title.strip()[:60], price.strip()[:120], duration.strip()[:40], features.strip()[:300], 1 if popular else 0,
                   int(views), int(apps), int(posts), int(days))).lastrowid

def update_plan(pid, **kw):
    lim = {"title": 60, "price": 120, "duration": 40, "features": 300}
    ints = ("views_month", "apps_month", "posts_month", "days")
    with tx():
        if not get_plan(pid): return False
        for k, v in kw.items():
            if k in lim: ex(f"UPDATE plans SET {k}=? WHERE id=?", (str(v).strip()[:lim[k]], int(pid)))
            elif k in ints: ex(f"UPDATE plans SET {k}=? WHERE id=?", (int(v), int(pid)))
            elif k == "popular": ex("UPDATE plans SET popular=? WHERE id=?", (1 if v else 0, int(pid)))
        return True

def toggle_popular(pid):
    with tx():
        p = get_plan(pid)
        if not p: return None
        ex("UPDATE plans SET popular=? WHERE id=?", (0 if p["popular"] else 1, int(pid))); return not p["popular"]

def move_plan(pid, delta):
    with tx():
        ps = plans(); i = next((i for i, p in enumerate(ps) if p["id"] == int(pid)), None)
        if i is None: return False
        j = i + int(delta)
        if j < 0 or j >= len(ps): return False
        ps[i], ps[j] = ps[j], ps[i]
        for n, p in enumerate(ps): ex("UPDATE plans SET position=? WHERE id=?", (n, p["id"]))
        return True

def remove_plan(pid):
    with tx():
        n = ex("DELETE FROM plans WHERE id=?", (int(pid),)).rowcount
        ex("UPDATE users SET plan_id=NULL, plan_until=0 WHERE plan_id=?", (int(pid),)); return n > 0

def grant_plan(uid, pid):
    """Manual grant (payment happened outside the bot). Returns plan_until (epoch, -1 = no expiry) or None."""
    with tx():
        p = get_plan(pid)
        if not p or not get_user(uid): return None
        until = -1 if int(p["days"]) <= 0 else now() + int(p["days"]) * 86400
        ex("UPDATE users SET plan_id=?, plan_until=? WHERE id=?", (int(pid), until, int(uid))); return until

def revoke_plan(uid):
    ex("UPDATE users SET plan_id=NULL, plan_until=0 WHERE id=?", (int(uid),))

def add_credits(uid, n):
    ex("UPDATE users SET credits=MAX(0, credits+?) WHERE id=?", (int(n), int(uid)))

def user_plan(uid):
    """Active plan row for the user or None."""
    u = q1("SELECT plan_id, plan_until FROM users WHERE id=?", (int(uid),))
    if not u or not u["plan_id"]: return None
    if u["plan_until"] != -1 and u["plan_until"] <= now(): return None
    return get_plan(u["plan_id"])

def plan_until(uid):
    return val("SELECT plan_until FROM users WHERE id=?", (int(uid),), 0)

# ---------------- quotas ----------------
KINDS = ("views", "apps", "posts")

def _usage(uid, kind, per=None):
    per = per or db.period()
    if kind == "views": return val("SELECT COUNT(*) FROM views WHERE viewer_id=? AND period=?", (int(uid), per), 0)
    if kind == "apps": return val("SELECT COUNT(*) FROM applications WHERE user_id=? AND period=?", (int(uid), per), 0)
    return val("SELECT COUNT(*) FROM calls WHERE user_id=? AND period=?", (int(uid), per), 0)

def quota(uid, kind):
    s = settings(); free = int(s[f"free_{kind}_month"])
    if is_admin(uid):
        return {"kind": kind, "limit": UNLIMITED, "used": _usage(uid, kind), "left": None, "unlimited": True, "admin": True}
    p = user_plan(uid); pl = int(p[f"{kind}_month"]) if p else 0
    if free < 0 or pl < 0: lim = UNLIMITED
    else: lim = max(free, pl)
    used = _usage(uid, kind)
    return {"kind": kind, "limit": lim, "used": used, "left": None if lim < 0 else max(0, lim - used),
            "unlimited": lim < 0, "admin": False}

def try_spend(uid, kind):
    """True if the action may proceed (spending a credit when the monthly quota is used up).
    Call inside the same tx() as the row insert that counts the usage."""
    with tx():
        qt = quota(uid, kind)
        if qt["unlimited"] or qt["left"] > 0: return True
        if val("SELECT credits FROM users WHERE id=?", (int(uid),), 0) > 0:
            add_credits(uid, -1); return True
        return False

def is_premium(uid):
    return is_admin(uid) or user_plan(uid) is not None

# ---------------- referrals ----------------
def try_referral(new_uid, referrer_uid):
    with tx():
        s = settings()
        if not s["ref_enabled"] or int(new_uid) == int(referrer_uid): return None
        me, ref = get_user(new_uid), get_user(referrer_uid)
        if not me or not ref or me.get("referred_by") or val("SELECT COUNT(*) FROM resumes WHERE user_id=?", (int(new_uid),), 0):
            return None
        rb, ib = int(s["ref_bonus"]), int(s["ref_invitee_bonus"])
        ex("UPDATE users SET referred_by=?, credits=credits+? WHERE id=?", (int(referrer_uid), ib, int(new_uid)))
        ex("UPDATE users SET credits=credits+?, ref_count=ref_count+1, ref_earned=ref_earned+? WHERE id=?", (rb, rb, int(referrer_uid)))
        return {"bonus": rb, "invitee_bonus": ib}

def top_referrers(n=5):
    return q("SELECT * FROM users WHERE ref_count>0 ORDER BY ref_count DESC LIMIT ?", (n,))

# ---------------- ads ----------------
AD_LIM = {"fa": 900, "en": 900, "url": 300, "btn": 40}
def ads(): return q("SELECT * FROM ads ORDER BY id")
def get_ad(aid): return q1("SELECT * FROM ads WHERE id=?", (int(aid),))

def add_ad(fa, en, photo=None, url="", btn="", slot="feed"):
    with tx():
        if val("SELECT COUNT(*) FROM ads") >= MAX_ADS: return None
        return ex("INSERT INTO ads(fa,en,photo,url,btn,slot,created_at) VALUES(?,?,?,?,?,?,?)",
                  (fa[:900], (en or fa)[:900], photo, url[:300], (btn or "🔗 باز کردن / Open")[:40],
                   slot if slot in ("feed", "sponsor") else "feed", db.now_iso())).lastrowid

def update_ad(aid, **kw):
    with tx():
        if not get_ad(aid): return False
        for k, v in kw.items():
            if k in AD_LIM: ex(f"UPDATE ads SET {k}=? WHERE id=?", (str(v)[:AD_LIM[k]], int(aid)))
            elif k == "photo": ex("UPDATE ads SET photo=? WHERE id=?", (v, int(aid)))
            elif k in ("enabled", "track"): ex(f"UPDATE ads SET {k}=? WHERE id=?", (1 if v else 0, int(aid)))
            elif k == "slot" and v in ("feed", "sponsor"): ex("UPDATE ads SET slot=? WHERE id=?", (v, int(aid)))
        return True

def toggle_ad(aid, key="enabled"):
    with tx():
        a = get_ad(aid)
        if not a: return None
        if key == "slot":
            new = "sponsor" if a["slot"] == "feed" else "feed"; ex("UPDATE ads SET slot=? WHERE id=?", (new, int(aid))); return new
        new = 0 if a[key] else 1; ex(f"UPDATE ads SET {key}=? WHERE id=?", (new, int(aid))); return bool(new)

def remove_ad(aid): return ex("DELETE FROM ads WHERE id=?", (int(aid),)).rowcount > 0
def ad_count(aid, what):
    if what not in ("views", "clicks"): return None
    with tx():
        ex(f"UPDATE ads SET {what}={what}+1 WHERE id=?", (int(aid),)); return get_ad(aid)

def note_action(uid):
    ex("UPDATE users SET actions_since_ad=actions_since_ad+1 WHERE id=?", (int(uid),))

def ad_due(uid):
    """A feed ad to show after an action (non-premium only); resets the counter when it fires."""
    with tx():
        s = settings()
        if not s["ads_enabled"] or is_premium(uid): return None
        u = get_user(uid)
        if not u or u["actions_since_ad"] < max(1, int(s["ad_every"])): return None
        live = q("SELECT * FROM ads WHERE enabled=1 AND slot='feed' ORDER BY views, id")
        if not live: return None
        ex("UPDATE users SET actions_since_ad=0 WHERE id=?", (int(uid),)); return live[0]

def sponsor_ad(uid=None):
    if not settings()["ads_enabled"] or (uid is not None and is_premium(uid)): return None
    r = q("SELECT * FROM ads WHERE enabled=1 AND slot='sponsor' ORDER BY views, id LIMIT 1")
    return r[0] if r else None

def ad_recipients():
    return [r["id"] for r in q("SELECT id FROM users WHERE banned=0") if not is_premium(r["id"])]

# ---------------- audiences / stats ----------------
def audience_ids(kind="all"):
    if kind == "resume":
        rows = q("SELECT u.id FROM users u JOIN resumes r ON r.user_id=u.id WHERE u.banned=0 AND r.status='complete'")
    elif kind == "casting":
        rows = q("SELECT id FROM users WHERE banned=0 AND casting_status='approved'")
    else:
        rows = q("SELECT id FROM users WHERE banned=0")
    return [r["id"] for r in rows]

def stats():
    t = now(); iso_cut = db.now_iso(t - ACTIVE_WINDOW)
    return {
        "users": val("SELECT COUNT(*) FROM users", (), 0),
        "active": val("SELECT COUNT(*) FROM users WHERE last_seen>=?", (iso_cut,), 0),
        "banned": val("SELECT COUNT(*) FROM users WHERE banned=1", (), 0),
        "resumes": val("SELECT COUNT(*) FROM resumes WHERE status='complete'", (), 0),
        "drafts": val("SELECT COUNT(*) FROM resumes WHERE status='draft'", (), 0),
        "public": val("SELECT COUNT(*) FROM resumes WHERE status='complete' AND visibility='public' AND admin_hidden=0", (), 0),
        "featured": val("SELECT COUNT(*) FROM resumes WHERE featured=1", (), 0),
        "photos": val("SELECT COUNT(*) FROM media", (), 0),
        "casting": val("SELECT COUNT(*) FROM users WHERE casting_status='approved'", (), 0),
        "casting_pending": val("SELECT COUNT(*) FROM users WHERE casting_status='pending'", (), 0),
        "calls": val("SELECT COUNT(*) FROM calls", (), 0),
        "calls_open": val("SELECT COUNT(*) FROM calls WHERE status='open'", (), 0),
        "imp_pending": val("SELECT COUNT(*) FROM calls WHERE status='pending' AND source IS NOT NULL", (), 0),
        "apps": val("SELECT COUNT(*) FROM applications", (), 0),
        "premium": sum(1 for r in q("SELECT id FROM users WHERE plan_id IS NOT NULL") if user_plan(r["id"])),
        "refs": val("SELECT COALESCE(SUM(ref_count),0) FROM users", (), 0),
    }
