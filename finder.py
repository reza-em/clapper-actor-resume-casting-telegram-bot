"""Resume search UI (admins; casting directors and plan holders as configured). Composable filters via buttons. Callback prefix 's:'."""
import json, logging
import config, db, fa, logic, resumes as R, options as O
import core as C
from core import tr, esc, btn, kb, grid, send, show

log = logging.getLogger("finder")
AGE_PRESETS = [(18, 25), (26, 35), (36, 45), (46, 60), (61, 99)]
H_PRESETS = [(140, 159), (160, 169), (170, 179), (180, 210)]
EXP_ORDER = O.codes(O.EXPERIENCE)

def can_search(uid):
    """(allowed, reason_key)"""
    if logic.is_admin(uid): return True, None
    u = logic.get_user(uid)
    if u.get("casting_status") == "approved" and logic.settings()["search_casting"]: return True, None
    p = logic.user_plan(uid)
    if p and int(p["views_month"]) != 0: return True, None
    if u.get("casting_status") in ("pending",): return False, "s_pending"
    return False, "s_not_allowed"

def get_filters(uid): return dict(logic.get_user(uid).get("search_filters") or {})
def set_filters(uid, f): logic.update_user(uid, search_filters=f)

def filter_summary(lang, f):
    parts = []
    if f.get("q"): parts.append("🔤 " + esc(f["q"]))
    if f.get("name"): parts.append("📛 " + esc(f["name"]))
    if f.get("city"): parts.append("🏙 " + esc(f["city"]))
    if f.get("role"): parts.append(O.label(O.ROLES, f["role"], lang))
    if f.get("skill"):
        cat, _, code = f["skill"].partition(":"); parts.append("🛠 " + O.skill_label(cat, code, lang) if cat in O.SKILL_CATS else "")
    if f.get("language"): parts.append("🗣 " + O.skill_label("language", f["language"], lang))
    if f.get("gender"): parts.append(O.label(O.GENDER, f["gender"], lang))
    if f.get("age_min") is not None or f.get("age_max") is not None:
        parts.append("🎂 %s–%s" % (C.num(lang, f.get("age_min") if f.get("age_min") is not None else "…"), C.num(lang, f.get("age_max") if f.get("age_max") is not None else "…")))
    if f.get("h_min") is not None or f.get("h_max") is not None:
        parts.append("📏 %s–%s" % (C.num(lang, f.get("h_min") if f.get("h_min") is not None else "…"), C.num(lang, f.get("h_max") if f.get("h_max") is not None else "…")))
    if f.get("exp"): parts.append(O.label(O.EXPERIENCE, f["exp"], lang))
    if f.get("featured"): parts.append("⭐")
    return " · ".join(p for p in parts if p) or tr(lang, "s_no_filters")

def panel(chat_id, uid, lang, mid=None, admin_mode=False):
    ok, why = can_search(uid)
    if not ok:
        rows = [C.contact_btns(lang), [btn(tr(lang, "b_register_casting"), "k:reg")] if why == "s_not_allowed" else [], [btn(tr(lang, "b_plans"), "m:plans")], [btn(tr(lang, "b_menu"), "m:menu")]]
        return show(chat_id, mid, tr(lang, why), kb([r for r in rows if r]))
    f = get_filters(uid)
    total = R.search(f, admin=logic.is_admin(uid), per=1)[3]
    rows = [[btn(tr(lang, "sb_q"), "s:ask:q"), btn(tr(lang, "sb_name"), "s:ask:name")],
            [btn(tr(lang, "sb_city"), "s:m:city"), btn(tr(lang, "sb_role"), "s:m:role")],
            [btn(tr(lang, "sb_skill"), "s:m:skill"), btn(tr(lang, "sb_lang"), "s:m:language")],
            [btn(tr(lang, "sb_gender"), "s:m:gender"), btn(tr(lang, "sb_exp"), "s:m:exp")],
            [btn(tr(lang, "sb_age"), "s:m:age"), btn(tr(lang, "sb_height"), "s:m:h")],
            [btn(tr(lang, "sb_featured_on") if f.get("featured") else tr(lang, "sb_featured"), "s:feat")],
            [btn(tr(lang, "sb_show", n=C.num(lang, total)), "s:r:1")],
            [btn(tr(lang, "sb_clear"), "s:clr"), btn(tr(lang, "b_menu"), "m:menu")]]
    show(chat_id, mid, tr(lang, "s_panel", f=filter_summary(lang, f), n=C.num(lang, total)), kb(rows))

def submenu(chat_id, uid, lang, mid, kind):
    f = get_filters(uid); rows = []
    if kind == "city":
        rows += grid([btn(("✅ " if f.get("city") == cf else "") + (cf if lang == "fa" else ce), f"s:v:city:{i}") for i, (cf, ce) in enumerate(O.CITIES)], 3)
        rows.append([btn(tr(lang, "b_other_city"), "s:ask:city")])
    elif kind == "role":
        rows += grid([btn(("✅ " if f.get("role") == c else "") + (a if lang == "fa" else b), f"s:v:role:{i}") for i, (c, a, b) in enumerate(O.ROLES)], 2)
    elif kind == "gender":
        rows += grid([btn(("✅ " if f.get("gender") == c else "") + (a if lang == "fa" else b), f"s:v:gender:{i}") for i, (c, a, b) in enumerate(O.GENDER)], 3)
    elif kind == "exp":
        rows += grid([btn(("✅ " if f.get("exp") == c else "") + (a if lang == "fa" else b), f"s:v:exp:{i}") for i, (c, a, b) in enumerate(O.EXPERIENCE)], 2)
    elif kind == "language":
        items = O.SKILL_CATS["language"][2]
        rows += grid([btn(("✅ " if f.get("language") == c else "") + (a if lang == "fa" else b), f"s:v:language:{i}") for i, (c, a, b) in enumerate(items)], 3)
    elif kind == "skill":
        for ci, cat in enumerate(O.SKILL_CAT_ORDER):
            if cat != "language": rows.append([btn(O.skill_cat_label(cat, lang), f"s:sk:{ci}")])
    elif kind == "age":
        rows += grid([btn("%s–%s" % (C.num(lang, a), C.num(lang, b)), f"s:v:age:{i}") for i, (a, b) in enumerate(AGE_PRESETS)], 3)
        rows.append([btn(tr(lang, "b_custom_range"), "s:ask:age")])
    elif kind == "h":
        rows += grid([btn("%s–%s" % (C.num(lang, a), C.num(lang, b)), f"s:v:h:{i}") for i, (a, b) in enumerate(H_PRESETS)], 2)
        rows.append([btn(tr(lang, "b_custom_range"), "s:ask:h")])
    rows.append([btn(tr(lang, "b_any"), f"s:x:{kind}"), btn(tr(lang, "b_back"), "s:p")])
    show(chat_id, mid, tr(lang, "s_pick_" + kind), kb(rows))

def skill_cat(chat_id, uid, lang, mid, ci):
    cat = O.SKILL_CAT_ORDER[ci]; f = get_filters(uid)
    rows = grid([btn(("✅ " if f.get("skill") == f"{cat}:{c}" else "") + (a if lang == "fa" else b), f"s:v:skill:{ci}.{i}") for i, (c, a, b) in enumerate(O.SKILL_CATS[cat][2])], 2)
    rows.append([btn(tr(lang, "b_back"), "s:m:skill")])
    show(chat_id, mid, O.skill_cat_label(cat, lang), kb(rows))

def apply_value(uid, kind, a):
    f = get_filters(uid)
    if kind == "city": f["city"] = O.CITIES[int(a)][0]
    elif kind == "role": f["role"] = O.ROLES[int(a)][0]
    elif kind == "gender": f["gender"] = O.GENDER[int(a)][0]
    elif kind == "exp": f["exp"] = O.EXPERIENCE[int(a)][0]
    elif kind == "language": f["language"] = O.SKILL_CATS["language"][2][int(a)][0]
    elif kind == "skill":
        ci, i = a.split("."); cat = O.SKILL_CAT_ORDER[int(ci)]; f["skill"] = f"{cat}:{O.SKILL_CATS[cat][2][int(i)][0]}"
    elif kind == "age": f["age_min"], f["age_max"] = AGE_PRESETS[int(a)]
    elif kind == "h": f["h_min"], f["h_max"] = H_PRESETS[int(a)]
    set_filters(uid, f)

def clear_value(uid, kind):
    f = get_filters(uid)
    for k in {"age": ("age_min", "age_max"), "h": ("h_min", "h_max")}.get(kind, (kind,)): f.pop(k, None)
    set_filters(uid, f)

def parse_range(t, lo, hi):
    t = fa.digits(t).replace("–", "-").replace("تا", "-").replace(" ", "")
    import re
    m = re.fullmatch(r"(\d{1,3})-(\d{1,3})", t)
    if not m: return None
    a, b = int(m.group(1)), int(m.group(2))
    if a > b: a, b = b, a
    return (a, b) if lo <= a and b <= hi else None

def on_text(msg, uid, lang, kind):
    """Awaiting-text replies for the filter panel."""
    chat_id = msg["chat"]["id"]; t = (msg.get("text") or "").strip(); f = get_filters(uid)
    if not t: return True
    if kind in ("q", "name"):
        f[kind] = fa.clean(t, 60)
    elif kind == "city":
        f["city"] = R.city_canon(t)
    elif kind in ("age", "h"):
        rg = parse_range(t, 5, 99) if kind == "age" else parse_range(t, 100, 230)
        if not rg: send(chat_id, tr(lang, "s_bad_range")); return True
        f["age_min" if kind == "age" else "h_min"], f["age_max" if kind == "age" else "h_max"] = rg
    set_filters(uid, f); C.set_await(uid, None); panel(chat_id, uid, lang); return True

# ---------------- results ----------------
def results(chat_id, uid, lang, mid, page):
    ok, why = can_search(uid)
    if not ok: return panel(chat_id, uid, lang, mid)
    admin = logic.is_admin(uid); f = get_filters(uid)
    rows_, page, pages, total = R.search(f, admin=admin, page=page)
    if mid: C.delete_msg(chat_id, mid)
    if not rows_:
        send(chat_id, tr(lang, "s_none"), kb([[btn(tr(lang, "b_change_filters"), "s:p")], [btn(tr(lang, "b_menu"), "m:menu")]])); return
    send(chat_id, tr(lang, "s_results_head", n=C.num(lang, total), p=C.num(lang, page), pages=C.num(lang, pages)))
    for r in rows_:
        text = R.card(r, lang, full=False, admin_tags=admin)
        rows = [[btn(tr(lang, "b_full_resume"), f"s:v1:{r['id']}")]]
        if admin: rows += admin_row(lang, r)
        fid = R.primary_file_id(r["id"])
        if fid: C.send_photo(chat_id, fid, text, kb(rows))
        else: send(chat_id, text, kb(rows))
    nav = []
    if page > 1: nav.append(btn("⬅️", f"s:r:{page - 1}"))
    nav.append(btn(f"{C.num(lang, page)}/{C.num(lang, pages)}", "a:noop"))
    if page < pages: nav.append(btn("➡️", f"s:r:{page + 1}"))
    send(chat_id, tr(lang, "s_page_foot"), kb([nav, [btn(tr(lang, "b_change_filters"), "s:p"), btn(tr(lang, "b_menu"), "m:menu")]]))

def admin_row(lang, r):
    return [[btn(tr(lang, "b_unhide") if r["admin_hidden"] else tr(lang, "b_hide_admin"), f"a:rh:{r['id']}"),
             btn(tr(lang, "b_unfeature") if r["featured"] else tr(lang, "b_feature"), f"a:rf:{r['id']}")],
            [btn(tr(lang, "b_del_admin"), f"a:rd:{r['id']}")]]

def view_full(chat_id, uid, lang, rid):
    """Full resume card. Counts against the monthly view quota once per resume per month (admins free)."""
    r = R.get(rid)
    ok, why = can_search(uid)
    if not r or not ok: return
    admin = logic.is_admin(uid)
    if not admin and not R.is_listed(r): send(chat_id, tr(lang, "s_gone")); return
    with db.tx():
        seen = db.q1("SELECT 1 FROM views WHERE viewer_id=? AND resume_id=? AND period=?", (uid, rid, db.period()))
        if not admin and not seen:
            if not logic.try_spend(uid, "views"):
                pass_ = False
            else:
                db.ex("INSERT INTO views(viewer_id, resume_id, period, created_at) VALUES(?,?,?,?)", (uid, rid, db.period(), db.now_iso())); pass_ = True
        else:
            pass_ = True
    if not pass_:
        return __import__("ui").upgrade_prompt(chat_id, uid, lang, "views")
    fid = R.primary_file_id(rid)
    if fid: C.send_photo(chat_id, fid, "🎭 <b>%s</b>" % esc(R.display_name(r)))
    for m in R.media_of(rid)[1:4]:
        C.send_photo(chat_id, m["telegram_file_id"])
    rows = admin_row(lang, r) if admin else []
    send(chat_id, R.card(r, lang, full=True, contact=True, admin_tags=admin), kb(rows + [[btn(tr(lang, "b_back_search"), "s:p")]]))
    __import__("ui").maybe_ad(chat_id, uid, lang)

# ---------------- callbacks ----------------
def callback(data, chat_id, mid, uid, lang):
    p = data.split(":"); op = p[1] if len(p) > 1 else ""; a = p[2] if len(p) > 2 else ""; b = p[3] if len(p) > 3 else ""
    if op == "p": return panel(chat_id, uid, lang, mid)
    ok, _ = can_search(uid)
    if not ok: return panel(chat_id, uid, lang, mid)
    if op == "ask":
        C.set_await(uid, "s_text", {"kind": a}); send(chat_id, tr(lang, "s_ask_" + a))
    elif op == "m": submenu(chat_id, uid, lang, mid, a)
    elif op == "sk": skill_cat(chat_id, uid, lang, mid, int(a))
    elif op == "v":
        apply_value(uid, a, b); panel(chat_id, uid, lang, mid)
    elif op == "x": clear_value(uid, a); panel(chat_id, uid, lang, mid)
    elif op == "feat":
        f = get_filters(uid); f["featured"] = not f.get("featured"); set_filters(uid, f); panel(chat_id, uid, lang, mid)
    elif op == "clr": set_filters(uid, {}); panel(chat_id, uid, lang, mid)
    elif op == "r": results(chat_id, uid, lang, mid, int(a) if a.isdigit() else 1)
    elif op == "v1": view_full(chat_id, uid, lang, int(a))
