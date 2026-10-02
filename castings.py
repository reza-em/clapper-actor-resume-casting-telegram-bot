"""Casting side: casting/production accounts, casting calls, browsing, applying with a resume, applicants. Callback prefix 'k:'."""
import logging, json
import config, db, fa, logic, resumes as R, options as O
import core as C
from core import tr, esc, btn, kb, grid, send, show

log = logging.getLogger("castings")
PROJECT_TYPES = [(c, a, b) for c, a, b in O.WORK_TYPES]

def is_casting(uid):
    return logic.get_user(uid).get("casting_status") == "approved" or logic.is_admin(uid)

def call_row(cid): return db.q1("SELECT * FROM calls WHERE id=?", (int(cid),))
def call_roles(cid): return [r["role"] for r in db.q("SELECT role FROM call_roles WHERE call_id=? ORDER BY rowid", (int(cid),))]

# ---------------- menu ----------------
def menu(chat_id, uid, lang, mid=None):
    C.set_await(uid, None)
    u = logic.get_user(uid); st = u.get("casting_status", "none")
    rows = [[btn(tr(lang, "b_browse_calls"), "k:l:1")]]
    if R.get_by_user(uid):
        rows.append([btn(tr(lang, "b_my_apps"), "k:ma:1")])
    if is_casting(uid):
        rows.append([btn(tr(lang, "b_new_call"), "k:new"), btn(tr(lang, "b_my_calls"), "k:mc:1")])
    elif st == "pending":
        rows.append([btn(tr(lang, "b_pending"), "a:noop")])
    else:
        rows.append([btn(tr(lang, "b_register_casting"), "k:reg")])
    rows.append([btn(tr(lang, "b_menu"), "m:menu")])
    show(chat_id, mid, tr(lang, "k_menu"), kb(rows))

# ---------------- casting registration ----------------
def register(chat_id, uid, lang, mid=None):
    st = logic.get_user(uid).get("casting_status", "none")
    if st == "approved": return menu(chat_id, uid, lang, mid)
    if st == "pending": return show(chat_id, mid, tr(lang, "k_pending"), kb([[btn(tr(lang, "b_menu"), "m:menu")]]))
    if not logic.get_user(uid).get("consent_at"):
        return show(chat_id, mid, tr(lang, "consent"), kb([[btn(tr(lang, "b_agree_c"), "k:agree")], [btn(tr(lang, "b_no_agree"), "m:menu")]]))
    C.set_await(uid, "k_regname", {}); send(chat_id, tr(lang, "k_ask_name"))

def finish_registration(chat_id, uid, lang, name):
    need = logic.settings()["casting_approval"]
    logic.update_user(uid, casting_name=fa.clean(name, 80), casting_status="pending" if need else "approved")
    C.set_await(uid, None)
    if need:
        send(chat_id, tr(lang, "k_reg_pending"), kb([[btn(tr(lang, "b_menu"), "m:menu")]]))
        for aid in ([logic.owner_id()] + logic.list_admins()):
            if aid and aid != uid:
                send(aid, tr(C.user_lang(aid), "k_notify_admin", who=esc(C.who_label(uid)), name=esc(name)),
                     kb([[btn(tr(C.user_lang(aid), "b_approve"), f"a:cap:{uid}"), btn(tr(C.user_lang(aid), "b_reject"), f"a:crj:{uid}")]]))
    else:
        send(chat_id, tr(lang, "k_reg_ok"), kb([[btn(tr(lang, "b_new_call"), "k:new")], [btn(tr(lang, "b_menu"), "m:menu")]]))

# ---------------- new call wizard ----------------
CSTEPS = ["title", "type", "roles", "city", "date", "details", "contact"]

def new_call(chat_id, uid, lang, mid=None):
    if not is_casting(uid): return register(chat_id, uid, lang, mid)
    qt = logic.quota(uid, "posts")
    if not qt["unlimited"] and qt["left"] <= 0 and logic.get_user(uid).get("credits", 0) <= 0:
        return __import__("ui").upgrade_prompt(chat_id, uid, lang, "posts")
    step(chat_id, uid, lang, mid, "title", {"v": {"roles": []}})

def step(chat_id, uid, lang, mid, st, d):
    d["st"] = st; C.set_await(uid, "k_new", d)
    i = CSTEPS.index(st) + 1
    text = tr(lang, "kc_head", n=C.num(lang, i), total=C.num(lang, len(CSTEPS))) + "\n\n" + tr(lang, "kq_" + st) + "\n\n💡 " + tr(lang, "kex_" + st)
    rows = []
    if st == "type": rows += grid([btn(a if lang == "fa" else b, f"k:t:{n}") for n, (c, a, b) in enumerate(PROJECT_TYPES)], 2)
    elif st == "roles":
        cur = set(d["v"]["roles"])
        rows += grid([btn(("✅ " if c in cur else "") + (a if lang == "fa" else b), f"k:r:{n}") for n, (c, a, b) in enumerate(O.ROLES)], 2)
        rows.append([btn(tr(lang, "b_next"), "k:nx")])
    elif st == "city":
        rows += grid([btn(cf if lang == "fa" else ce, f"k:c:{n}") for n, (cf, ce) in enumerate(O.CITIES[:12])], 3)
    elif st == "contact":
        u = logic.get_user(uid)
        if u.get("username"): rows.append([btn(tr(lang, "b_use_my_tg", u=u["username"]), "k:cme")])
    nav = []
    if i > 1: nav.append(btn(tr(lang, "b_back"), "k:bk"))
    if st in ("date", "details"): nav.append(btn(tr(lang, "b_skip"), "k:sk"))
    if nav: rows.append(nav)
    rows.append([btn(tr(lang, "b_cancel"), "k:cx")])
    show(chat_id, mid, text, kb(rows))

def _advance(chat_id, uid, lang, mid, d):
    i = CSTEPS.index(d["st"])
    if i + 1 >= len(CSTEPS): return preview(chat_id, uid, lang, d)
    step(chat_id, uid, lang, mid, CSTEPS[i + 1], d)

def is_imported(c): return bool(c.get("source"))

def imported_text(c, roles, lang, full=True, admin=False):
    """Imported (channel) call: parsed summary + the post text as published + credit line with link to the source post."""
    t = ["🎬 <b>%s</b>%s" % (esc(c["title"]), " ⭐" if c.get("featured") else "")]
    t.append("📌 " + O.plain(O.label(O.WORK_TYPES, c["project_type"], lang)) + (" · 🏙 " + esc(c["city"]) if c["city"] else ""))
    if roles: t.append("🎭 " + ("، " if lang == "fa" else ", ").join(O.plain(O.label(O.ROLES, x, lang)) for x in roles))
    meta = [tr(lang, k, v=esc(c[f])) for k, f in (("imp_gender", "gender_text"), ("imp_age", "age_text"), ("imp_fee", "fee_text"), ("imp_deadline", "deadline_text")) if c.get(f)]
    t += meta
    if full and c.get("details"): t.append("\n" + esc(c["details"]))
    if c.get("source_date"): t.append(tr(lang, "imp_posted", v=esc(fa.iso_to_jalali_str(c["source_date"]) if lang == "fa" else c["source_date"][:10])))
    t.append("\n" + tr(lang, "imp_credit", ch=esc(c["source"]), url=esc(c["source_url"])))
    if admin:
        try: fl = json.loads(c.get("flags") or "[]")
        except Exception: fl = []
        if fl: t.append(tr(lang, "a_imp_flags", f=("، " if lang == "fa" else ", ").join(tr(lang, "flag_" + f) for f in fl if ("flag_" + f) in C.T["fa"])))
    t.append("🆔 <code>C%06d</code>" % c["id"])
    return "\n".join(t)

def has_contact(c):
    try: ct = json.loads(c.get("contacts") or "{}")
    except Exception: return False
    return any(ct.get(k) for k in ("tg", "wa", "phone", "ig"))

def direct_buttons(c, lang):
    """URL buttons built ONLY from contacts published in the post (telegram id / whatsapp)."""
    try: ct = json.loads(c.get("contacts") or "{}")
    except Exception: ct = {}
    rows = []
    for h in (ct.get("tg") or [])[:2]: rows.append([btn(tr(lang, "b_direct_tg", h=h), url="https://t.me/" + h)])
    for w in (ct.get("wa") or [])[:1]:
        if w[:1] != "q": rows.append([btn(tr(lang, "b_direct_wa"), url="https://wa.me/" + w)])
    if c.get("source_url"): rows.append([btn(tr(lang, "b_src_post"), url=c["source_url"])])
    return rows

def call_text(c, roles, lang, full=True, applicants=None):
    if is_imported(c): return imported_text(c, roles, lang, full)
    t = ["🎬 <b>%s</b>%s" % (esc(c["title"]), " ⭐" if c.get("featured") else "")]
    t.append("📌 " + O.plain(O.label(O.WORK_TYPES, c["project_type"], lang)) + (" · 🏙 " + esc(c["city"]) if c["city"] else ""))
    if roles: t.append("🎭 " + ("، " if lang == "fa" else ", ").join(O.plain(O.label(O.ROLES, x, lang)) for x in roles))
    if c.get("date_text"): t.append("📅 " + esc(c["date_text"]))
    if c.get("details") and full: t.append("\n📝 " + esc(c["details"]))
    if full and c.get("contact"): t.append("\n📞 " + esc(c["contact"]))
    if applicants is not None: t.append(tr(lang, "kc_applicants", n=C.num(lang, applicants)))
    t.append("🆔 <code>C%06d</code>" % c["id"])
    return "\n".join(t)

def preview(chat_id, uid, lang, d):
    v = d["v"]; c = {"id": 0, "title": v.get("title", ""), "project_type": v.get("type", "other"), "city": v.get("city"),
                     "date_text": v.get("date_text"), "details": v.get("details"), "contact": v.get("contact"), "featured": 0}
    d["st"] = "confirm"; C.set_await(uid, "k_new", d)
    send(chat_id, tr(lang, "kc_preview") + "\n\n" + call_text(c, v["roles"], lang),
         kb([[btn(tr(lang, "b_publish"), "k:pub")], [btn(tr(lang, "b_back"), "k:bk"), btn(tr(lang, "b_cancel"), "k:cx")]]))

def publish(chat_id, uid, lang, d):
    v = d["v"]
    with db.tx():
        if not logic.try_spend(uid, "posts"):
            C.set_await(uid, None); return __import__("ui").upgrade_prompt(chat_id, uid, lang, "posts")
        cid = db.ex("INSERT INTO calls(user_id,title,project_type,city,date_text,date_iso,details,contact,status,period,created_at) VALUES(?,?,?,?,?,?,?,?,'open',?,?)",
                    (uid, v["title"], v.get("type", "other"), v.get("city"), v.get("date_text"), v.get("date_iso"), v.get("details"),
                     v.get("contact"), db.period(), db.now_iso())).lastrowid
        for r_ in v["roles"]: db.ex("INSERT INTO call_roles(call_id, role) VALUES(?,?)", (cid, r_))
    C.set_await(uid, None)
    send(chat_id, tr(lang, "kc_published"), kb([[btn(tr(lang, "b_my_calls"), "k:mc:1")], [btn(tr(lang, "b_menu"), "m:menu")]]))
    return cid

def on_text(msg, uid, lang, aw, d):
    chat_id = msg["chat"]["id"]; t = (msg.get("text") or "").strip()
    if not t: return True
    if aw == "k_regname":
        if len(t) < 2: send(chat_id, tr(lang, "err_name")); return True
        finish_registration(chat_id, uid, lang, t); return True
    if aw == "k_new":
        st = d.get("st"); v = d["v"]
        if st == "title":
            if len(t) < 3: send(chat_id, tr(lang, "err_empty")); return True
            v["title"] = fa.clean(t, 100)
        elif st == "city":
            if not 2 <= len(t) <= 40: send(chat_id, tr(lang, "err_city")); return True
            v["city"] = R.city_canon(t)
        elif st == "date":
            iso = fa.parse_date(t)
            v["date_text"] = fa.clean(t, 60); v["date_iso"] = iso
        elif st == "details": v["details"] = fa.clean(t, 1200)
        elif st == "contact":
            if len(t) < 3: send(chat_id, tr(lang, "err_empty")); return True
            v["contact"] = fa.clean(t, 120)
        else: send(chat_id, tr(lang, "w_use_buttons")); return True
        _advance(chat_id, uid, lang, None, d); return True
    return False

# ---------------- browsing ----------------
def list_calls(chat_id, uid, lang, mid, page, mine=False):
    per = config.PAGE_SIZE
    where = "user_id=? AND source IS NULL" if mine else "status='open'"
    args = (uid,) if mine else ()
    total = db.val(f"SELECT COUNT(*) FROM calls WHERE {where}", args, 0)
    pages = max(1, (total + per - 1) // per); page = min(max(1, page), pages)
    rows_ = db.q(f"SELECT * FROM calls WHERE {where} ORDER BY featured DESC, id DESC LIMIT ? OFFSET ?", (*args, per, (page - 1) * per))
    if mid: C.delete_msg(chat_id, mid)
    if not rows_:
        send(chat_id, tr(lang, "k_none_mine" if mine else "k_none"), kb([[btn(tr(lang, "b_back"), "m:calls")]])); return
    send(chat_id, tr(lang, "k_list_head", n=C.num(lang, total), p=C.num(lang, page), pages=C.num(lang, pages)))
    mine_rows = {r["call_id"] for r in db.q("SELECT call_id FROM applications WHERE user_id=?", (uid,))}
    for c in rows_:
        roles = call_roles(c["id"])
        if mine:
            n = db.val("SELECT COUNT(*) FROM applications WHERE call_id=?", (c["id"],), 0)
            b = [[btn(tr(lang, "b_applicants", n=C.num(lang, n)), f"k:ap:{c['id']}:1")],
                 [btn(tr(lang, "b_close_call") if c["status"] == "open" else tr(lang, "b_reopen_call"), f"k:cl:{c['id']}"), btn("🗑", f"k:del:{c['id']}")]]
            send(chat_id, call_text(c, roles, lang, applicants=n) + "\n" + tr(lang, "k_status_" + c["status"]), kb(b))
        else:
            if is_imported(c):
                b = direct_buttons(c, lang)
                if not has_contact(c):                      # no contact published at all -> in-bot apply is the only way
                    b.insert(0, [btn(tr(lang, "b_applied") if c["id"] in mine_rows else tr(lang, "b_apply"), "a:noop" if c["id"] in mine_rows else f"k:ap1:{c['id']}")])
            else:
                b = [[btn(tr(lang, "b_applied") if c["id"] in mine_rows else tr(lang, "b_apply"), "a:noop" if c["id"] in mine_rows else f"k:ap1:{c['id']}")]]
            if logic.is_admin(uid):
                b.append([btn(tr(lang, "b_unfeature") if c["featured"] else tr(lang, "b_feature"), f"a:cf:{c['id']}"), btn(tr(lang, "b_hide_admin"), f"a:ch:{c['id']}"), btn("🗑", f"a:cd:{c['id']}")])
            send(chat_id, call_text(c, roles, lang), kb(b))
    nav = []
    cb = "k:mc:" if mine else "k:l:"
    if page > 1: nav.append(btn("⬅️", cb + str(page - 1)))
    nav.append(btn(f"{C.num(lang, page)}/{C.num(lang, pages)}", "a:noop"))
    if page < pages: nav.append(btn("➡️", cb + str(page + 1)))
    send(chat_id, tr(lang, "s_page_foot"), kb([nav, [btn(tr(lang, "b_back"), "m:calls")]]))

def my_applications(chat_id, uid, lang, mid, page):
    rows_ = db.q("SELECT a.*, c.title, c.status AS cstatus FROM applications a JOIN calls c ON c.id=a.call_id WHERE a.user_id=? ORDER BY a.id DESC LIMIT 15", (uid,))
    text = tr(lang, "k_my_apps_head") + "\n\n" + ("\n".join("• %s — %s" % (esc(r["title"]), tr(lang, "k_status_" + r["cstatus"])) for r in rows_) or tr(lang, "k_none_apps"))
    show(chat_id, mid, text, kb([[btn(tr(lang, "b_back"), "m:calls")]]))

def apply(chat_id, uid, lang, cid):
    c = call_row(cid)
    if not c or c["status"] != "open": send(chat_id, tr(lang, "k_closed")); return
    if is_imported(c):
        if has_contact(c):                                  # applicants contact the original poster directly
            send(chat_id, tr(lang, "imp_contact_direct"), kb(direct_buttons(c, lang))); return
    elif c["user_id"] == uid: send(chat_id, tr(lang, "k_own_call")); return
    r = R.get_by_user(uid)
    if not r or r["status"] != "complete":
        send(chat_id, tr(lang, "k_need_resume"), kb([[btn(tr(lang, "b_build"), "m:resume")], [btn(tr(lang, "b_menu"), "m:menu")]])); return
    with db.tx():
        if db.q1("SELECT 1 FROM applications WHERE call_id=? AND user_id=?", (cid, uid)): send(chat_id, tr(lang, "k_already")); return
        if not logic.try_spend(uid, "apps"):
            return __import__("ui").upgrade_prompt(chat_id, uid, lang, "apps")
        db.ex("INSERT INTO applications(call_id,user_id,resume_id,period,created_at) VALUES(?,?,?,?,?)", (cid, uid, r["id"], db.period(), db.now_iso()))
    send(chat_id, tr(lang, "k_applied"), kb([[btn(tr(lang, "b_browse_calls"), "k:l:1")], [btn(tr(lang, "b_menu"), "m:menu")]]))
    owner = c["user_id"]
    send(owner, tr(C.user_lang(owner), "k_new_applicant", title=esc(c["title"]), name=esc(R.display_name(r))),
         kb([[btn(tr(C.user_lang(owner), "b_applicants", n=""), f"k:ap:{cid}:1")]]))
    __import__("ui").maybe_ad(chat_id, uid, lang)

def applicants(chat_id, uid, lang, mid, cid, page):
    c = call_row(cid)
    if not c or (c["user_id"] != uid and not logic.is_admin(uid)): return
    per = config.PAGE_SIZE
    total = db.val("SELECT COUNT(*) FROM applications WHERE call_id=?", (cid,), 0)
    pages = max(1, (total + per - 1) // per); page = min(max(1, page), pages)
    rows_ = db.q("SELECT a.* FROM applications a WHERE call_id=? ORDER BY id DESC LIMIT ? OFFSET ?", (cid, per, (page - 1) * per))
    if mid: C.delete_msg(chat_id, mid)
    if not rows_: send(chat_id, tr(lang, "k_no_applicants"), kb([[btn(tr(lang, "b_back"), "k:mc:1")]])); return
    send(chat_id, tr(lang, "k_applicants_head", title=esc(c["title"]), n=C.num(lang, total), p=C.num(lang, page), pages=C.num(lang, pages)))
    for a in rows_:
        r = R.get(a["resume_id"])
        if not r: continue
        fid = R.primary_file_id(r["id"]); text = R.card(r, lang, full=True, contact=True)
        if fid: C.send_photo(chat_id, fid, "🎭 <b>%s</b>" % esc(R.display_name(r)))
        send(chat_id, text)
    nav = []
    if page > 1: nav.append(btn("⬅️", f"k:ap:{cid}:{page - 1}"))
    if page < pages: nav.append(btn("➡️", f"k:ap:{cid}:{page + 1}"))
    send(chat_id, tr(lang, "s_page_foot"), kb([nav, [btn(tr(lang, "b_back"), "k:mc:1")]] if nav else [[btn(tr(lang, "b_back"), "k:mc:1")]]))

# ---------------- callbacks ----------------
def callback(data, chat_id, mid, uid, lang):
    p = data.split(":"); op = p[1] if len(p) > 1 else ""; a = p[2] if len(p) > 2 else ""; b = p[3] if len(p) > 3 else ""
    aw, d = C.u_awaiting(uid)
    if op == "agree":
        logic.update_user(uid, consent_at=db.now_iso()); return register(chat_id, uid, lang, None)
    if op == "reg": return register(chat_id, uid, lang, mid)
    if op == "l": return list_calls(chat_id, uid, lang, mid, int(a or 1))
    if op == "ma": return my_applications(chat_id, uid, lang, mid, 1)
    if op == "ap1": return apply(chat_id, uid, lang, int(a))
    if op == "new": return new_call(chat_id, uid, lang, mid)
    if op == "mc":
        if not is_casting(uid): return register(chat_id, uid, lang, mid)
        return list_calls(chat_id, uid, lang, mid, int(a or 1), mine=True)
    if op == "ap": return applicants(chat_id, uid, lang, mid, int(a), int(b or 1))
    if op in ("cl", "del"):
        c = call_row(int(a))
        if not c or (c["user_id"] != uid and not logic.is_admin(uid)): return
        if op == "cl":
            db.ex("UPDATE calls SET status=? WHERE id=?", ("closed" if c["status"] == "open" else "open", c["id"]))
            return list_calls(chat_id, uid, lang, mid, 1, mine=True)
        if b == "y":
            db.ex("DELETE FROM calls WHERE id=?", (c["id"],)); return list_calls(chat_id, uid, lang, mid, 1, mine=True)
        return show(chat_id, mid, tr(lang, "k_del_confirm"), kb([[btn(tr(lang, "yes"), f"k:del:{c['id']}:y"), btn(tr(lang, "no"), "k:mc:1")]]))
    # wizard ops
    if aw != "k_new":
        if op in ("t", "r", "c", "nx", "bk", "sk", "cme", "pub", "cx"): return menu(chat_id, uid, lang, mid)
        return
    v = d.setdefault("v", {"roles": []}); st = d.get("st")
    if op == "cx": C.set_await(uid, None); return menu(chat_id, uid, lang, mid)
    if op == "bk":
        i = CSTEPS.index(st) if st in CSTEPS else len(CSTEPS)
        return step(chat_id, uid, lang, mid, CSTEPS[max(0, i - 1)], d)
    if op == "t" and st == "type":
        n = int(a)
        if 0 <= n < len(PROJECT_TYPES): v["type"] = PROJECT_TYPES[n][0]; return _advance(chat_id, uid, lang, mid, d)
    elif op == "r" and st == "roles":
        n = int(a); code = O.ROLES[n][0]
        v["roles"] = [x for x in v["roles"] if x != code] if code in v["roles"] else v["roles"] + [code]
        return step(chat_id, uid, lang, mid, "roles", d)
    elif op == "nx" and st == "roles":
        if not v["roles"]: send(chat_id, tr(lang, "kc_need_role")); return
        return _advance(chat_id, uid, lang, mid, d)
    elif op == "c" and st == "city":
        v["city"] = O.CITIES[int(a)][0]; return _advance(chat_id, uid, lang, mid, d)
    elif op == "sk" and st in ("date", "details"): return _advance(chat_id, uid, lang, mid, d)
    elif op == "cme" and st == "contact":
        un = logic.get_user(uid).get("username")
        if un: v["contact"] = "@" + un; return _advance(chat_id, uid, lang, mid, d)
    elif op == "pub" and st == "confirm":
        return publish(chat_id, uid, lang, d)
