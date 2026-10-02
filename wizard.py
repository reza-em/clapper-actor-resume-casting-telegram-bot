"""Resume wizard: ONE simple question at a time, progress indicator, back/skip on every step, tap-buttons where possible,
progress saved automatically (resumes.wiz_step). Callback prefix 'w:'."""
import logging
import config, db, fa, logic, resumes as R, options as O
import core as C
from core import tr, esc, btn, kb, grid, send, show

log = logging.getLogger("wizard")

# (field, kind). Steps 1..ESSENTIAL are the basics; after them the user may jump to the preview any time.
STEPS = [
    ("full_name_fa", "text"), ("stage_name", "text"), ("gender", "choice"), ("birth_year", "text"), ("city", "city"),
    ("roles", "roles"), ("experience_level", "choice"), ("photos", "photos"), ("phone", "text"),
    ("telegram_username", "tg"), ("email", "text"), ("instagram", "text"), ("height_cm", "text"), ("weight_kg", "text"),
    ("hair_color", "choice"), ("eye_color", "choice"), ("skin_tone", "choice"), ("skills", "skills"), ("history", "history"),
    ("education", "text"), ("awards", "text"), ("portfolio_links", "text"), ("demo_reel_url", "text"),
    ("availability", "choice"), ("travel", "choice"), ("expected_fee", "text"), ("bio", "text"),
]
N = len(STEPS)
ESSENTIAL = 9
IDX = {f: i + 1 for i, (f, _) in enumerate(STEPS)}
CHOICES = {"gender": O.GENDER, "experience_level": O.EXPERIENCE, "hair_color": O.HAIR, "eye_color": O.EYES,
           "skin_tone": O.SKIN, "availability": O.AVAILABILITY, "travel": O.TRAVEL}
PER_ROW = {"gender": 3, "experience_level": 2, "hair_color": 3, "eye_color": 3, "skin_tone": 3, "availability": 2, "travel": 1}

def lbl_of(lang, field):
    return tr(lang, "lbl_" + field)

# ---------------- entry points ----------------
def open_from_menu(chat_id, uid, lang, mid=None):
    """Main-menu button «ساخت رزومه / رزومه من»."""
    u = logic.get_user(uid)
    if not u.get("consent_at"):
        show(chat_id, mid, tr(lang, "consent"), kb([[btn(tr(lang, "b_agree"), "w:agree")], [btn(tr(lang, "b_no_agree"), "m:menu")]])); return
    r = R.ensure(uid)
    if r["status"] == "complete":
        my_resume(chat_id, uid, lang, mid); return
    if r["wiz_step"] and r["wiz_step"] > 1:
        show(chat_id, mid, tr(lang, "w_continue", n=C.num(lang, r["wiz_step"]), total=C.num(lang, N)),
             kb([[btn(tr(lang, "b_continue"), f"w:go:{r['wiz_step']}")], [btn(tr(lang, "b_restart"), "w:go:1")],
                 [btn(tr(lang, "b_preview"), "w:pv")] if not R.missing_required(r["id"]) else [],
                 [btn(tr(lang, "b_menu"), "m:menu")]]))
        return
    go(chat_id, uid, lang, 1, mid)

def go(chat_id, uid, lang, n, mid=None, edit=False):
    r = R.ensure(uid)
    n = min(max(1, int(n)), N)
    R.set_step(r["id"], n)
    C.set_await(uid, "wiz", {"edit": bool(edit)})
    field, kind = STEPS[n - 1]
    r = R.get(r["id"])
    text = header(lang, n, edit) + tr(lang, "q_" + field) + "\n\n💡 " + tr(lang, "ex_" + field)
    cur = current_value(r, field, lang)
    if cur: text += "\n\n" + tr(lang, "w_now", v=esc(cur))
    if kind == "photos":
        text += "\n\n" + tr(lang, "w_photo_count", n=C.num(lang, len(R.media_of(r["id"]))), max=C.num(lang, config.MAX_PHOTOS))
    rows = kind_rows(r, field, kind, lang, n)
    rows += nav_rows(r, field, kind, lang, n, edit, bool(cur))
    show(chat_id, mid, text, kb(rows))

def header(lang, n, edit):
    if edit: return tr(lang, "w_edit_head") + "\n\n"
    bar = "▓" * round(10 * n / N) + "░" * (10 - round(10 * n / N))
    return tr(lang, "w_progress", n=C.num(lang, n), total=C.num(lang, N), bar=bar) + "\n\n"

def nav_rows(r, field, kind, lang, n, edit, has_value):
    rows = []
    if edit:
        row = [btn(tr(lang, "b_back_resume"), "w:pv")]
        if has_value and kind in ("text", "tg", "city") and field not in R.REQUIRED: row.append(btn(tr(lang, "b_clear"), "w:clr"))
        rows.append(row); return rows
    nav = []
    if n > 1: nav.append(btn(tr(lang, "b_back"), "w:bk"))
    nav.append(btn(tr(lang, "b_next") if kind in ("roles", "photos", "skills", "history") else tr(lang, "b_skip"), "w:nx"))
    rows.append(nav)
    if not R.missing_required(r["id"]):
        rows.append([btn(tr(lang, "b_preview"), "w:pv")])
    return rows

def current_value(r, field, lang):
    v = r.get(field) if field in r else None
    if field in CHOICES and v: return O.plain(O.label(CHOICES[field], v, lang))
    if field == "roles":
        return ("، " if lang == "fa" else ", ").join(O.plain(O.label(O.ROLES, x, lang)) for x in R.roles_of(r["id"]))
    if field == "portfolio_links" and v:
        try:
            import json; return "  ".join(json.loads(v))
        except Exception: return str(v)
    if field in ("birth_year", "height_cm", "weight_kg") and v: return C.num(lang, v)
    if field in ("photos", "skills", "history"): return ""
    return str(v) if v else ""

def kind_rows(r, field, kind, lang, n):
    rows = []
    if kind == "choice":
        lst = CHOICES[field]; cur = r.get(field)
        bs = [btn(("✅ " if c == cur else "") + (fa_ if lang == "fa" else en_), f"w:c:{i}") for i, (c, fa_, en_) in enumerate(lst)]
        rows += grid(bs, PER_ROW.get(field, 2))
    elif kind == "city":
        bs = [btn((cf if lang == "fa" else ce), f"w:ct:{i}") for i, (cf, ce) in enumerate(O.CITIES[:12])]
        rows += grid(bs, 3)
        rows.append([btn(tr(lang, "b_other_city"), "w:cto")])
    elif kind == "roles":
        cur = set(R.roles_of(r["id"]))
        rows += grid([btn(("✅ " if c in cur else "") + (fa_ if lang == "fa" else en_), f"w:r:{i}") for i, (c, fa_, en_) in enumerate(O.ROLES)], 2)
    elif kind == "tg":
        u = logic.get_user(r["user_id"])
        if u.get("username"): rows.append([btn(tr(lang, "b_use_my_tg", u=u["username"]), "w:tgme")])
    elif kind == "skills":
        sk = set(R.skills_of(r["id"]))
        for i, cat in enumerate(O.SKILL_CAT_ORDER):
            k = sum(1 for c, _ in sk if c == cat)
            rows.append([btn(O.skill_cat_label(cat, lang) + (f"  ✅ {C.num(lang, k)}" if k else ""), f"w:sk:{i}")])
    elif kind == "history":
        for h in R.history_of(r["id"]):
            rows.append([btn(("🎞 %s %s" % (h["title"], h["year"] or ""))[:40], f"w:he:{h['id']}"), btn("🗑", f"w:hd:{h['id']}")])
        rows.append([btn(tr(lang, "b_add_work"), "w:ha")])
    elif kind == "photos":
        for m in R.media_of(r["id"]):
            rows.append([btn(tr(lang, "b_del_photo", n=C.num(lang, m["seq"])), f"w:pd:{m['id']}")])
    return rows

# ---------------- skills sub-screen ----------------
def skills_cat(chat_id, uid, lang, mid, ci):
    cat = O.SKILL_CAT_ORDER[ci]; r = R.ensure(uid)
    cur = set(R.skills_of(r["id"]))
    items = O.SKILL_CATS[cat][2]
    bs = [btn(("✅ " if (cat, c) in cur else "") + (fa_ if lang == "fa" else en_), f"w:st:{ci}:{i}") for i, (c, fa_, en_) in enumerate(items)]
    rows = grid(bs, 2) + [[btn(tr(lang, "b_back_cats"), "w:skm")]]
    show(chat_id, mid, tr(lang, "w_skill_cat", cat=O.skill_cat_label(cat, lang)), kb(rows))

# ---------------- history sub-flow ----------------
H_STAGES = ["title", "type", "role", "year", "company"]

def hist_prompt(chat_id, uid, lang, mid, h):
    st = h["stage"]; editing = bool(h.get("hid"))
    text = tr(lang, "wh_head", n=C.num(lang, H_STAGES.index(st) + 1), total=C.num(lang, len(H_STAGES))) + "\n\n" + tr(lang, "wh_q_" + st) + "\n\n💡 " + tr(lang, "wh_ex_" + st)
    rows = []
    if st == "type":
        rows += grid([btn(fa_ if lang == "fa" else en_, f"w:ht:{i}") for i, (c, fa_, en_) in enumerate(O.WORK_TYPES)], 2)
    if st in ("role", "year", "company") or (editing and st in ("title", "type")):
        rows.append([btn(tr(lang, "b_skip"), "w:hs")])
    rows.append([btn(tr(lang, "b_cancel"), "w:hc")])
    show(chat_id, mid, text, kb(rows))

def hist_start(chat_id, uid, lang, mid, hid=None):
    r = R.ensure(uid); vals = {}
    if hid:
        hh = next((x for x in R.history_of(r["id"]) if x["id"] == int(hid)), None)
        if not hh: return go(chat_id, uid, lang, IDX["history"], mid)
        vals = {"title": hh["title"], "type": hh["work_type"], "role": hh["role"], "year": hh["year"], "company": hh["director_company"]}
    elif len(R.history_of(r["id"])) >= 30:
        send(chat_id, tr(lang, "w_too_many")); return
    d = C.u_awaiting(uid)[1]; d["h"] = {"stage": "title", "hid": int(hid) if hid else None, "vals": vals}
    C.set_await(uid, "wiz", d); hist_prompt(chat_id, uid, lang, mid, d["h"])

def hist_advance(chat_id, uid, lang, mid, d, value=None, skip=False):
    h = d["h"]; st = h["stage"]
    if not skip:
        h["vals"][st] = value
    i = H_STAGES.index(st)
    if i + 1 < len(H_STAGES):
        h["stage"] = H_STAGES[i + 1]; C.set_await(uid, "wiz", d); hist_prompt(chat_id, uid, lang, mid, h); return
    r = R.ensure(uid); v = h["vals"]
    if h.get("hid"):
        R.update_history(h["hid"], r["id"], title=v.get("title"), work_type=v.get("type") or "other", role=v.get("role"),
                         year=v.get("year"), director_company=v.get("company"))
    else:
        R.add_history(r["id"], v.get("title"), v.get("type") or "other", v.get("role"), v.get("year"), v.get("company"))
    d.pop("h", None); C.set_await(uid, "wiz", d)
    send(chat_id, tr(lang, "w_work_saved"))
    go(chat_id, uid, lang, IDX["history"], None, d.get("edit"))

# ---------------- text / photo input ----------------
def _finish_step(chat_id, uid, lang, n, d, msg_key="w_saved"):
    """After a value was stored: confirm briefly and move on."""
    send(chat_id, tr(lang, msg_key))
    if d.get("edit"): my_resume_or_preview(chat_id, uid, lang)
    elif n >= N: preview(chat_id, uid, lang)
    else: go(chat_id, uid, lang, n + 1)

def on_text(msg, uid, lang, data):
    chat_id = msg["chat"]["id"]; t = (msg.get("text") or "").strip()
    r = R.ensure(uid); n = r["wiz_step"] or 1
    if not t: return on_photo(msg, uid, lang, data) if (msg.get("photo") or msg.get("document")) else True
    if data.get("h"):                                           # inside the add-work sub-flow
        h = data["h"]; st = h["stage"]
        if st == "type":
            send(chat_id, tr(lang, "w_use_buttons")); return True
        field = {"title": "work_title", "role": "work_role", "year": "work_year", "company": "work_company"}[st]
        v, err = R.validate(field, t)
        if err: send(chat_id, tr(lang, err)); return True
        hist_advance(chat_id, uid, lang, None, data, v); return True
    field, kind = STEPS[n - 1]
    if kind in ("choice", "roles", "photos", "history"):
        send(chat_id, tr(lang, "w_use_buttons" if kind != "photos" else "w_send_photo")); return True
    if kind == "skills":
        cur = R.get(r["id"])["skills_extra"]
        v, err = R.validate("skills_extra", t)
        if err: send(chat_id, tr(lang, err)); return True
        R.set_field(r["id"], "skills_extra", ((cur + "، ") if cur else "") + v)
        send(chat_id, tr(lang, "w_skill_added")); go(chat_id, uid, lang, n, None, data.get("edit")); return True
    v, err = R.validate("city" if kind == "city" else field, t)
    if err: send(chat_id, tr(lang, err)); return True
    R.set_field(r["id"], field, v)
    _finish_step(chat_id, uid, lang, n, data); return True

def on_photo(msg, uid, lang, data):
    chat_id = msg["chat"]["id"]; r = R.ensure(uid); n = r["wiz_step"] or 1
    if STEPS[n - 1][0] != "photos":
        send(chat_id, tr(lang, "w_photo_not_now")); return True
    if msg.get("photo"):
        p = msg["photo"][-1]; fid, uq = p["file_id"], p.get("file_unique_id")
    elif (msg.get("document") or {}).get("mime_type", "").startswith("image/"):
        d_ = msg["document"]; fid, uq = d_["file_id"], d_.get("file_unique_id")
    else:
        send(chat_id, tr(lang, "w_send_photo")); return True
    m = R.add_photo(r["id"], fid, uq, downloader=C.download_file)
    if m is None: send(chat_id, tr(lang, "w_photo_max", max=C.num(lang, config.MAX_PHOTOS)))
    elif m == "dup": send(chat_id, tr(lang, "w_photo_dup"))
    else:
        send(chat_id, tr(lang, "w_photo_ok", n=C.num(lang, m["seq"])), kb([[btn(tr(lang, "b_next"), "w:nx")]]))
    return True

# ---------------- callbacks ----------------
def callback(data, chat_id, mid, uid, lang):
    p = data.split(":"); op = p[1] if len(p) > 1 else ""; a = p[2] if len(p) > 2 else ""; b = p[3] if len(p) > 3 else ""
    if op == "agree":
        logic.update_user(uid, consent_at=db.now_iso())
        send(chat_id, tr(lang, "consent_ok")); return open_from_menu(chat_id, uid, lang, None)
    if not logic.get_user(uid).get("consent_at"):
        return open_from_menu(chat_id, uid, lang, mid)
    r = R.ensure(uid); n = r["wiz_step"] or 1
    d = C.u_awaiting(uid)[1] if C.u_awaiting(uid)[0] == "wiz" else {}
    edit = bool(d.get("edit"))
    if op == "go": return go(chat_id, uid, lang, int(a), mid, edit=(b == "e"))
    if op == "pv": return my_resume_or_preview(chat_id, uid, lang, mid)
    if op == "bk": return go(chat_id, uid, lang, n - 1, mid)
    if op == "nx":
        if edit: return my_resume_or_preview(chat_id, uid, lang, mid)
        if n >= N: return preview(chat_id, uid, lang, mid)
        return go(chat_id, uid, lang, n + 1, mid)
    if op == "clr":
        field = STEPS[n - 1][0]
        if field in R.SCALARS and field not in R.REQUIRED: R.clear_field(r["id"], field)
        return my_resume_or_preview(chat_id, uid, lang, mid)
    if op == "em": return edit_menu(chat_id, uid, lang, mid)
    if op == "e": return go(chat_id, uid, lang, int(a), mid, edit=True)
    field, kind = STEPS[n - 1]
    if op == "c" and kind == "choice":
        lst = CHOICES[field]; i = int(a)
        if 0 <= i < len(lst):
            R.set_field(r["id"], field, lst[i][0])
            return after_pick(chat_id, uid, lang, mid, n, edit)
    elif op == "ct" and kind == "city":
        i = int(a)
        if 0 <= i < len(O.CITIES): R.set_field(r["id"], "city", O.CITIES[i][0]); return after_pick(chat_id, uid, lang, mid, n, edit)
    elif op == "cto": send(chat_id, tr(lang, "w_type_city"))
    elif op == "r" and kind == "roles":
        i = int(a)
        if 0 <= i < len(O.ROLES): R.toggle_role(r["id"], O.ROLES[i][0]); go(chat_id, uid, lang, n, mid, edit)
    elif op == "tgme" and kind == "tg":
        un = logic.get_user(uid).get("username")
        if un: R.set_field(r["id"], "telegram_username", un); return after_pick(chat_id, uid, lang, mid, n, edit)
    elif op == "sk" and kind == "skills": skills_cat(chat_id, uid, lang, mid, int(a))
    elif op == "skm": go(chat_id, uid, lang, n, mid, edit)
    elif op == "st" and kind == "skills":
        ci, i = int(a), int(b); cat = O.SKILL_CAT_ORDER[ci]
        R.toggle_skill(r["id"], cat, O.SKILL_CATS[cat][2][i][0]); skills_cat(chat_id, uid, lang, mid, ci)
    elif op == "pd" and kind == "photos":
        R.delete_photo(r["id"], int(a)); go(chat_id, uid, lang, n, mid, edit)
    elif kind == "history" and op in ("ha", "he", "hd", "ht", "hs", "hc"):
        if op == "ha": hist_start(chat_id, uid, lang, mid)
        elif op == "he": hist_start(chat_id, uid, lang, mid, int(a))
        elif op == "hd": R.delete_history(int(a), r["id"]); go(chat_id, uid, lang, n, mid, edit)
        elif op == "hc": d.pop("h", None); C.set_await(uid, "wiz", d); go(chat_id, uid, lang, n, mid, edit)
        elif d.get("h"):
            if op == "ht":
                i = int(a)
                if 0 <= i < len(O.WORK_TYPES) and d["h"]["stage"] == "type": hist_advance(chat_id, uid, lang, mid, d, O.WORK_TYPES[i][0])
            elif op == "hs": hist_advance(chat_id, uid, lang, mid, d, skip=True)
    elif op == "ok": confirm(chat_id, uid, lang, mid)
    elif op == "vis": R.set_visibility(r["id"], "hidden" if r["visibility"] == "public" else "public"); my_resume(chat_id, uid, lang, mid)
    elif op == "del": show(chat_id, mid, tr(lang, "del_resume_confirm"), kb([[btn(tr(lang, "yes"), "w:delok"), btn(tr(lang, "no"), "w:pv")]]))
    elif op == "delok":
        R.delete_resume(r["id"]); C.set_await(uid, None); show(chat_id, mid, tr(lang, "del_resume_done"), kb([[btn(tr(lang, "b_menu"), "m:menu")]]))

def after_pick(chat_id, uid, lang, mid, n, edit):
    if edit: return my_resume_or_preview(chat_id, uid, lang, mid)
    if n >= N: return preview(chat_id, uid, lang, mid)
    go(chat_id, uid, lang, n + 1, mid)

# ---------------- preview / my resume ----------------
def edit_menu(chat_id, uid, lang, mid):
    bs = [btn(lbl_of(lang, f), f"w:e:{i + 1}") for i, (f, _) in enumerate(STEPS)]
    show(chat_id, mid, tr(lang, "w_edit_menu"), kb(grid(bs, 2) + [[btn(tr(lang, "b_back_resume"), "w:pv")]]))

def my_resume_or_preview(chat_id, uid, lang, mid=None):
    C.set_await(uid, None)
    r = R.ensure(uid)
    return my_resume(chat_id, uid, lang, mid) if r["status"] == "complete" else preview(chat_id, uid, lang, mid)

def _send_card(chat_id, r, lang, markup, admin_tags=False, contact=True):
    fid = R.primary_file_id(r["id"])
    if fid: C.send_photo(chat_id, fid, "🎭 <b>%s</b>" % esc(R.display_name(r)))
    return send(chat_id, R.card(r, lang, full=True, contact=contact, admin_tags=admin_tags), markup)

def preview(chat_id, uid, lang, mid=None):
    C.set_await(uid, None)
    r = R.ensure(uid)
    if mid: C.delete_msg(chat_id, mid)
    miss = R.missing_required(r["id"])
    rows = []
    if miss:
        first = min(IDX[f] for f in miss)
        rows.append([btn(tr(lang, "b_fill_missing"), f"w:go:{first}")])
        note = tr(lang, "w_missing", items="، ".join(lbl_of(lang, f) for f in miss) if lang == "fa" else ", ".join(lbl_of(lang, f) for f in miss))
    else:
        rows.append([btn(tr(lang, "b_confirm"), "w:ok")]); note = ""
    rows.append([btn(tr(lang, "b_edit"), "w:em")])
    rows.append([btn(tr(lang, "b_menu"), "m:menu")])
    send(chat_id, tr(lang, "w_preview_head"))
    _send_card(chat_id, r, lang, None)
    send(chat_id, (note or tr(lang, "w_preview_ask")), kb(rows))

def confirm(chat_id, uid, lang, mid):
    r = R.ensure(uid)
    if not R.publish(r["id"]):
        return preview(chat_id, uid, lang, mid)
    logic.update_user(uid, awaiting=None)
    show(chat_id, mid, tr(lang, "w_published"), kb([[btn(tr(lang, "b_my_resume"), "m:resume")], [btn(tr(lang, "b_menu"), "m:menu")]]))

def my_resume(chat_id, uid, lang, mid=None):
    C.set_await(uid, None)
    r = R.ensure(uid)
    if r["status"] != "complete": return open_from_menu(chat_id, uid, lang, mid)
    if mid: C.delete_msg(chat_id, mid)
    vis = r["visibility"] == "public"
    rows = [[btn(tr(lang, "b_edit"), "w:em")],
            [btn(tr(lang, "b_hide") if vis else tr(lang, "b_show"), "w:vis")],
            [btn(tr(lang, "b_del_resume"), "w:del")], [btn(tr(lang, "b_menu"), "m:menu")]]
    _send_card(chat_id, r, lang, None)
    status = tr(lang, "vis_public" if vis else "vis_hidden")
    if r["admin_hidden"]: status += "\n" + tr(lang, "vis_admin_hidden")
    if r["featured"]: status += "\n" + tr(lang, "vis_featured")
    send(chat_id, tr(lang, "my_resume_foot", status=status), kb(rows))
