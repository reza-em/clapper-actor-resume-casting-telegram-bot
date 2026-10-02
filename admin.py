"""Admin panel (owner + extra admins). Callback prefix 'a:'. Text replies handled through awaiting states."""
import os, re, json, time, shutil, tempfile, threading, logging
import config, db, logic, resumes as R, exporter, options as O, finder, importer, castings
import core as C
import ui
from core import tr, esc, btn, kb, grid, show, send, parse_int, who_label, uname_of, set_await

log = logging.getLogger("admin")
# what extra (non-owner) admins may do
EXTRA_OPS = {"home", "noop", "stats", "ul", "u", "us", "msg", "bn", "ubn", "gc", "ugp", "urp", "uc", "rs", "rid", "rh", "rf", "rd", "rdy",
             "cap", "crj", "cl", "cf", "ch", "cd", "cdy", "pcl", "vr", "imp", "impl", "impa", "impx", "impxy", "impe", "impf", "impaa", "impaay", "imph", "imps"}
EXTRA_AWAIT = {"a_usearch", "a_msg", "a_num", "a_rid", "a_impedit"}

def back_row(lang, to="a:home"): return [btn(tr(lang, "a_back"), to)]

def home(chat_id, mid, lang, uid=None):
    st = logic.stats()
    badge = f" ({C.num(lang, st['casting_pending'])})" if st["casting_pending"] else ""
    rows = [[btn(tr(lang, "a_b_stats"), "a:stats"), btn(tr(lang, "a_b_users"), "a:ul:1")],
            [btn(tr(lang, "a_b_resumes"), "a:rs"), btn(tr(lang, "a_b_calls") + badge, "a:pcl")],
            [btn(tr(lang, "a_b_import") + (f" ({C.num(lang, st['imp_pending'])})" if st["imp_pending"] else ""), "a:imp")]]
    if uid is None or logic.is_owner(uid):
        rows += [[btn(tr(lang, "a_b_export"), "a:exp"), btn(tr(lang, "a_b_bc"), "a:bc")],
                 [btn(tr(lang, "a_b_prices"), "a:pp"), btn(tr(lang, "a_b_ads"), "a:ads")],
                 [btn(tr(lang, "a_b_limits"), "a:set"), btn(tr(lang, "a_b_ref"), "a:ref")],
                 [btn(tr(lang, "a_b_faq"), "a:fq"), btn(tr(lang, "a_b_support"), "a:su")],
                 [btn(tr(lang, "a_b_admins"), "a:ad")]]
    elif logic.settings()["export_extra_admins"]:
        rows.append([btn(tr(lang, "a_b_export"), "a:exp")])
    rows.append([btn(tr(lang, "b_menu"), "m:menu")])
    show(chat_id, mid, tr(lang, "a_title"), kb(rows))

def stats(chat_id, mid, lang):
    s = logic.stats()
    show(chat_id, mid, tr(lang, "a_stats", **{k: C.num(lang, v) for k, v in s.items()}), kb([back_row(lang)]))

# ---------------- users ----------------
def user_line(u):
    return f"{'🚫 ' if u.get('banned') else ''}{'👑 ' if logic.is_admin(u['id']) else ''}{u.get('name') or u['id']} {uname_of(u)}".strip()[:44]

def users_list(chat_id, mid, lang, page):
    rows_, page, pages, total = logic.users_page(page)
    rows = [[btn(user_line(u), f"a:u:{u['id']}")] for u in rows_]
    nav = []
    if page > 1: nav.append(btn("⬅️", f"a:ul:{page-1}"))
    if page < pages: nav.append(btn("➡️", f"a:ul:{page+1}"))
    if nav: rows.append(nav)
    rows.append([btn(tr(lang, "a_b_usearch"), "a:us")]); rows.append(back_row(lang))
    show(chat_id, mid, tr(lang, "a_users", page=C.num(lang, page), pages=C.num(lang, pages), total=C.num(lang, total)), kb(rows))

def user_card(chat_id, mid, lang, uid, viewer):
    u = logic.get_user(uid)
    if not u: send(chat_id, tr(lang, "a_not_found")); return
    r = R.get_by_user(uid)
    p = logic.user_plan(uid)
    role = tr(lang, "role_owner") if logic.is_owner(uid) else (tr(lang, "role_admin") if logic.is_admin(uid) else tr(lang, "role_user"))
    txt = tr(lang, "a_user", who=esc(who_label(uid)), role=role,
             resume=(tr(lang, "rs_complete") if r["status"] == "complete" else tr(lang, "rs_draft")) if r else tr(lang, "rs_none"),
             casting=tr(lang, "cs_" + (u.get("casting_status") or "none")),
             plan=(esc(p["title"]) + " → " + (tr(lang, "me_no_expiry") if logic.plan_until(uid) == -1 else logic.fmt_date(logic.plan_until(uid)))) if p else tr(lang, "a_no_plan"),
             credits=C.num(lang, u.get("credits", 0)), refs=C.num(lang, u.get("ref_count", 0)),
             ban=tr(lang, "a_ban_yes" if u.get("banned") else "a_ban_no"), seen=(u.get("last_seen") or "")[:16].replace("T", " "))
    rows = [[btn(tr(lang, "a_b_msg"), f"a:msg:{uid}")]]
    if r: rows.append([btn(tr(lang, "a_b_view_resume"), f"a:vr:{r['id']}")])
    rows.append([btn(tr(lang, "a_b_grant"), f"a:gc:{uid}"), btn(tr(lang, "a_b_credits"), f"a:uc:{uid}")])
    if not logic.is_owner(uid) and not (logic.is_admin(uid) and not logic.is_owner(viewer)):
        rows.append([btn(tr(lang, "a_b_unban1" if u.get("banned") else "a_b_ban1"), f"a:{'ubn' if u.get('banned') else 'bn'}:{uid}")])
    if u.get("casting_status") == "pending":
        rows.append([btn(tr(lang, "b_approve"), f"a:cap:{uid}"), btn(tr(lang, "b_reject"), f"a:crj:{uid}")])
    if logic.is_owner(viewer) and not logic.is_owner(uid):
        rows.append([btn(tr(lang, "a_b_demote") if logic.is_admin(uid) else tr(lang, "a_b_promote"), f"a:{'adx' if logic.is_admin(uid) else 'adp'}:{uid}")])
    rows.append(back_row(lang, "a:ul:1"))
    show(chat_id, mid, txt, kb(rows))

def search_users_reply(chat_id, lang, qs):
    res = logic.search_users(qs)
    if not res: send(chat_id, tr(lang, "a_not_found")); return
    send(chat_id, tr(lang, "a_found", n=C.num(lang, len(res))), kb([[btn(user_line(u), f"a:u:{u['id']}")] for u in res[:20]] + [back_row(lang)]))

def grant_choice(chat_id, mid, lang, t):
    rows = []
    for p in logic.plans():
        rows.append([btn(tr(lang, "a_grant_plan", title=p["title"])[:55], f"a:ugp:{t}:{p['id']}")])
    if logic.user_plan(t): rows.append([btn(tr(lang, "a_b_revoke"), f"a:urp:{t}")])
    rows.append([btn(tr(lang, "a_b_credits"), f"a:uc:{t}")]); rows.append(back_row(lang, f"a:u:{t}"))
    show(chat_id, mid, tr(lang, "a_grant_choice", who=esc(who_label(t))) if logic.plans() else tr(lang, "a_grant_choice", who=esc(who_label(t))) + "\n" + tr(lang, "pp_none"), kb(rows))

# ---------------- resumes ----------------
def resume_admin(chat_id, lang, rid, viewer):
    r = R.get(rid)
    if not r: send(chat_id, tr(lang, "a_not_found")); return
    fid = R.primary_file_id(rid)
    if fid: C.send_photo(chat_id, fid, "🎭 <b>%s</b>" % esc(R.display_name(r)))
    send(chat_id, R.card(r, lang, full=True, contact=True, admin_tags=True), kb(finder.admin_row(lang, r) + [[btn(tr(lang, "a_b_view_user"), f"a:u:{r['user_id']}")]]))

# ---------------- casting calls ----------------
def pending_casting(chat_id, mid, lang):
    ps = db.q("SELECT * FROM users WHERE casting_status='pending' ORDER BY last_seen DESC LIMIT 20")
    if not ps: return show(chat_id, mid, tr(lang, "a_no_pending"), kb([back_row(lang)]))
    rows = []
    for u in ps:
        rows.append([btn(f"{u.get('casting_name') or u.get('name') or u['id']}"[:30], f"a:u:{u['id']}"), btn("✅", f"a:cap:{u['id']}"), btn("❌", f"a:crj:{u['id']}")])
    rows.append(back_row(lang)); show(chat_id, mid, tr(lang, "a_pending_head"), kb(rows))

# ---------------- imported calls (channel importer) ----------------
IMP_PER = 3

def imp_panel(chat_id, mid, lang):
    n = lambda s: db.val("SELECT COUNT(*) FROM calls WHERE source=? AND status" + s, (importer.SOURCE,), 0)
    pending = n("='pending'"); opened = n("='open'"); other = n(" IN ('closed','hidden')")
    rejected = db.val("SELECT COUNT(*) FROM imports WHERE source=? AND kind='rejected'", (importer.SOURCE,), 0)
    last = db.meta_get("import_last") or {}
    auto = logic.settings()["import_auto_publish"]
    clean = db.val("SELECT COUNT(*) FROM calls WHERE source=? AND status='pending' AND (flags IS NULL OR flags NOT LIKE '%no_contact%' AND flags NOT LIKE '%roles_unclear%' AND flags NOT LIKE '%maybe_course%')", (importer.SOURCE,), 0)
    rows = []
    if pending: rows.append([btn(tr(lang, "a_imp_review") + f" ({C.num(lang, pending)})", "a:impl:1")])
    if clean: rows.append([btn(tr(lang, "a_imp_approve_all", n=C.num(lang, clean)), "a:impaa")])
    rows.append([btn(tr(lang, "a_imp_auto", s=tr(lang, "on" if auto else "off")), "a:tg:import_auto_publish")])
    rows.append([btn(tr(lang, "a_imp_sync"), "a:imps")])
    rows.append(back_row(lang))
    show(chat_id, mid, tr(lang, "a_imp_head", ch=importer.SOURCE, pending=C.num(lang, pending), open=C.num(lang, opened), other=C.num(lang, other),
                          rejected=C.num(lang, rejected), auto=tr(lang, "on" if auto else "off"),
                          last=(logic.fmt_date(0) if False else (last.get("at", "")[:16].replace("T", " ") or tr(lang, "a_imp_never")))), kb(rows))

def imp_card_buttons(c, lang):
    cid = c["id"]
    if c["status"] == "pending":
        first = [btn(tr(lang, "b_imp_approve"), f"a:impa:{cid}")]
    else:
        first = [btn(tr(lang, "b_hide_admin") if c["status"] == "open" else tr(lang, "b_unhide"), f"a:imph:{cid}")]
    return [first, [btn(tr(lang, "b_imp_edit"), f"a:impe:{cid}"), btn("🗑", f"a:impx:{cid}")]] + castings.direct_buttons(c, lang)[-1:]

def imp_list(chat_id, mid, lang, page):
    where = "source=? AND status='pending'"
    total = db.val("SELECT COUNT(*) FROM calls WHERE " + where, (importer.SOURCE,), 0)
    pages = max(1, (total + IMP_PER - 1) // IMP_PER); page = min(max(1, page), pages)
    rows_ = db.q("SELECT * FROM calls WHERE " + where + " ORDER BY source_post DESC LIMIT ? OFFSET ?", (importer.SOURCE, IMP_PER, (page - 1) * IMP_PER))
    if mid: C.delete_msg(chat_id, mid)
    if not rows_: return send(chat_id, tr(lang, "a_imp_none"), kb([back_row(lang, "a:imp")]))
    send(chat_id, tr(lang, "a_imp_list_head", n=C.num(lang, total), p=C.num(lang, page), pages=C.num(lang, pages)))
    for c in rows_:
        send(chat_id, castings.imported_text(c, castings.call_roles(c["id"]), lang, full=True, admin=True)[:3900], kb(imp_card_buttons(c, lang)))
    nav = []
    if page > 1: nav.append(btn("⬅️", f"a:impl:{page - 1}"))
    nav.append(btn(f"{C.num(lang, page)}/{C.num(lang, pages)}", "a:noop"))
    if page < pages: nav.append(btn("➡️", f"a:impl:{page + 1}"))
    send(chat_id, tr(lang, "s_page_foot"), kb([nav, back_row(lang, "a:imp")]))

IMP_FIELDS = {"title": ("title", 100), "city": ("city", 40), "contact": ("contact", 300), "details": ("details", 3500)}

def imp_notify(stats):
    """After a periodic sync: tell the owner (+admins) that new calls wait for review. One short message per sync."""
    n = stats.get("imported_pending", 0)
    if not n: return
    for aid in ([logic.owner_id()] + logic.list_admins()):
        if aid: send(aid, tr(C.user_lang(aid), "a_imp_new", n=C.num(C.user_lang(aid), n)), kb([[btn(tr(C.user_lang(aid), "a_imp_review"), "a:impl:1")]]))

def imp_sync_job(chat_id, lang):
    send(chat_id, tr(lang, "a_imp_sync_start"))
    def job():
        st = importer.sync(notify=None)
        if st.get("skipped"): send(chat_id, tr(lang, "a_imp_sync_busy")); return
        send(chat_id, tr(lang, "a_imp_sync_done", found=C.num(lang, st["found"]), pending=C.num(lang, st["imported_pending"]), open=C.num(lang, st["imported_open"]),
                         reposts=C.num(lang, st["reposts"]), noise=C.num(lang, st["noise"]), expired=C.num(lang, st["expired"]), errors=C.num(lang, st["errors"])),
             kb([[btn(tr(lang, "a_imp_review"), "a:impl:1")], back_row(lang, "a:imp")]))
    if SYNC: job()
    else: threading.Thread(target=job, daemon=True).start()

# ---------------- settings / limits ----------------
def settings_panel(chat_id, mid, lang):
    s = logic.settings(); on = lambda k: tr(lang, "on" if s[k] else "off")
    def v(n): return tr(lang, "lim_unl") if n < 0 else C.num(lang, n)
    rows = [[btn(tr(lang, "a_s_views", n=v(s["free_views_month"])), "a:sn:free_views_month")],
            [btn(tr(lang, "a_s_apps", n=v(s["free_apps_month"])), "a:sn:free_apps_month")],
            [btn(tr(lang, "a_s_posts", n=v(s["free_posts_month"])), "a:sn:free_posts_month")],
            [btn(tr(lang, "a_s_search_casting", s=on("search_casting")), "a:tg:search_casting")],
            [btn(tr(lang, "a_s_approval", s=on("casting_approval")), "a:tg:casting_approval")],
            [btn(tr(lang, "a_s_export_extra", s=on("export_extra_admins")), "a:tg:export_extra_admins")],
            back_row(lang)]
    show(chat_id, mid, tr(lang, "a_settings"), kb(rows))

def ref_panel(chat_id, mid, lang):
    s = logic.settings()
    lines = "\n".join(f"{i+1}. {esc(u.get('name') or u['id'])} {uname_of(u)} — {C.num(lang, u['ref_count'])}" for i, u in enumerate(logic.top_referrers(5))) or tr(lang, "a_ref_none")
    show(chat_id, mid, tr(lang, "a_ref", s=tr(lang, "on" if s["ref_enabled"] else "off"), total=C.num(lang, logic.stats()["refs"]),
                          rb=C.num(lang, s["ref_bonus"]), ib=C.num(lang, s["ref_invitee_bonus"]), top=lines),
         kb([[btn(tr(lang, "a_s_reftoggle", s=tr(lang, "on" if s["ref_enabled"] else "off")), "a:tg:ref_enabled")],
             [btn(tr(lang, "a_s_rb"), "a:sn:ref_bonus"), btn(tr(lang, "a_s_ib"), "a:sn:ref_invitee_bonus")], back_row(lang)]))

# ---------------- admins / support / faq ----------------
def admins_panel(chat_id, mid, lang):
    owner = logic.owner_id()
    lines = "\n".join("• " + esc(who_label(a)) for a in logic.list_admins()) or tr(lang, "ad_none")
    rows = [[btn(tr(lang, "ad_add"), "a:ada")]]
    for a in logic.list_admins(): rows.append([btn(f"🗑 {logic.get_user(a).get('name') or a} · {a}"[:55], f"a:adx:{a}")])
    rows.append([btn(tr(lang, "ad_owner"), "a:own")]); rows.append(back_row(lang))
    show(chat_id, mid, tr(lang, "ad_menu", owner=esc(who_label(owner)) if owner else "-", lines=lines), kb(rows))

def support_panel(chat_id, mid, lang):
    sp = logic.support()
    rows = [[btn(tr(lang, "su_b_primary"), "a:sup:primary"), btn(tr(lang, "su_b_backup"), "a:sup:backup")]]
    if sp["backup"]: rows.append([btn(tr(lang, "su_b_clear"), "a:suc")])
    rows.append(back_row(lang))
    show(chat_id, mid, tr(lang, "su_menu", p=sp["primary"], b=("@" + sp["backup"]) if sp["backup"] else tr(lang, "su_none")), kb(rows))

def faq_panel(chat_id, mid, lang):
    items = logic.faq()
    rows = [[btn(f"✏️ {i+1}. {(it['q_fa'] if lang == 'fa' else it['q_en'])[:35]}", f"a:fqe:{i}")] for i, it in enumerate(items)]
    rows.append([btn(tr(lang, "fq_add"), "a:fqa")]); rows.append(back_row(lang))
    show(chat_id, mid, tr(lang, "fq_mgr", n=C.num(lang, len(items))), kb(rows))

def faq_edit(chat_id, mid, lang, i):
    items = logic.faq()
    if not 0 <= i < len(items): return faq_panel(chat_id, mid, lang)
    it = items[i]
    show(chat_id, mid, "❓ <b>%s</b>\n%s\n\n🇬🇧 <b>%s</b>\n%s" % (esc(it["q_fa"]), esc(it["a_fa"]), esc(it["q_en"]), esc(it["a_en"])),
         kb([[btn(tr(lang, "fq_qfa"), f"a:fqf:{i}:q_fa"), btn(tr(lang, "fq_afa"), f"a:fqf:{i}:a_fa")],
             [btn(tr(lang, "fq_qen"), f"a:fqf:{i}:q_en"), btn(tr(lang, "fq_aen"), f"a:fqf:{i}:a_en")],
             [btn("🗑", f"a:fqx:{i}")], back_row(lang, "a:fq")]))

# ---------------- plans ----------------
def plan_line(lang, pos, p):
    def v(n): return tr(lang, "lim_unl") if n < 0 else C.num(lang, n)
    return tr(lang, "pp_line", pos=C.num(lang, pos), star="⭐ " if p.get("popular") else "", title=esc(p["title"]), price=esc(p["price"] or "—"),
              dur=(" / " + esc(p["duration"])) if p.get("duration") else "", views=v(p["views_month"]), apps=v(p["apps_month"]),
              posts=v(p["posts_month"]), days=C.num(lang, p["days"]), hid="" if logic.plan_ready(p) else tr(lang, "pp_hidden"))

def plans_panel(chat_id, mid, lang):
    ps = logic.plans()
    lines = "\n".join(plan_line(lang, i + 1, p) for i, p in enumerate(ps)) or tr(lang, "pp_none")
    rows = []
    for i, p in enumerate(ps):
        r = [btn(f"✏️ {p['title']}"[:30], f"a:ppe:{p['id']}")]
        if i > 0: r.append(btn("⬆️", f"a:ppu:{p['id']}"))
        if i < len(ps) - 1: r.append(btn("⬇️", f"a:ppd:{p['id']}"))
        r.append(btn("🗑", f"a:ppx:{p['id']}")); rows.append(r)
    rows.append([btn(tr(lang, "pp_add"), "a:ppa")]); rows.append(back_row(lang))
    show(chat_id, mid, tr(lang, "pp_mgr", lines=lines), kb(rows))

PP_FIELDS = {"ppet": ("title", "pp_ask_title"), "ppep": ("price", "pp_ask_price"), "pped": ("duration", "pp_ask_dur"),
             "ppef": ("features", "pp_ask_feat"), "ppev": ("views_month", "pp_ask_views"), "ppea": ("apps_month", "pp_ask_apps"),
             "ppeo": ("posts_month", "pp_ask_posts"), "ppey": ("days", "pp_ask_days")}

def plan_edit(chat_id, mid, lang, pid):
    p = logic.get_plan(pid)
    if not p: return plans_panel(chat_id, mid, lang)
    rows = [[btn(tr(lang, "pp_e_title"), f"a:ppet:{pid}"), btn(tr(lang, "pp_e_price"), f"a:ppep:{pid}")],
            [btn(tr(lang, "pp_e_dur"), f"a:pped:{pid}"), btn(tr(lang, "pp_e_feat"), f"a:ppef:{pid}")],
            [btn(tr(lang, "pp_e_views"), f"a:ppev:{pid}"), btn(tr(lang, "pp_e_apps"), f"a:ppea:{pid}")],
            [btn(tr(lang, "pp_e_posts"), f"a:ppeo:{pid}"), btn(tr(lang, "pp_e_days"), f"a:ppey:{pid}")],
            [btn(tr(lang, "pp_e_unpop") if p["popular"] else tr(lang, "pp_e_pop"), f"a:ppt:{pid}")], back_row(lang, "a:pp")]
    show(chat_id, mid, tr(lang, "pp_edit", line=plan_line(lang, 0, p), feats=esc(p["features"] or "—")), kb(rows))

def parse_signed(t):
    t = C.norm_digits(t).strip()
    return int(t) if re.fullmatch(r"-?\d{1,6}", t) else None

# ---------------- ads ----------------
def ads_panel(chat_id, mid, lang):
    s = logic.settings(); items = logic.ads()
    lines = "\n".join(f"#{a['id']} {'✅' if a['enabled'] else '⛔'} {'📌' if a['slot'] == 'sponsor' else '📰'} {esc((a['fa'] or a['en'])[:40])} · 👁{C.num(lang, a['views'])} 🖱{C.num(lang, a['clicks'])}" for a in items) or tr(lang, "ads_none")
    rows = [[btn(f"✏️ #{a['id']}", f"a:ade:{a['id']}"), btn("👁", f"a:adp:{a['id']}"), btn("🗑", f"a:adx2:{a['id']}")] for a in items]
    rows.append([btn(tr(lang, "ads_add"), "a:ada2"), btn(tr(lang, "ads_toggle", s=tr(lang, "on" if s["ads_enabled"] else "off")), "a:tg:ads_enabled")])
    rows.append([btn(tr(lang, "ads_every", n=C.num(lang, s["ad_every"])), "a:sn:ad_every")])
    if items: rows.append([btn(tr(lang, "ads_bc"), "a:adb")])
    rows.append(back_row(lang))
    show(chat_id, mid, tr(lang, "ads_mgr", lines=lines), kb(rows))

def ad_edit(chat_id, mid, lang, aid):
    a = logic.get_ad(aid)
    if not a: return ads_panel(chat_id, mid, lang)
    txt = tr(lang, "ads_edit", id=a["id"], fa=esc(a["fa"]), en=esc(a["en"]), url=esc(a["url"] or "—"), btn=esc(a["btn"]), photo="✅" if a["photo"] else "—",
             views=C.num(lang, a["views"]), clicks=C.num(lang, a["clicks"]), slot=tr(lang, "slot_" + a["slot"]))
    rows = [[btn(tr(lang, "ads_e_fa"), f"a:adf:{aid}:fa"), btn(tr(lang, "ads_e_en"), f"a:adf:{aid}:en")],
            [btn(tr(lang, "ads_e_photo"), f"a:adf:{aid}:photo"), btn(tr(lang, "ads_e_url"), f"a:adf:{aid}:url")],
            [btn(tr(lang, "ads_e_btn"), f"a:adf:{aid}:btn")],
            [btn(tr(lang, "ads_e_on" if a["enabled"] else "ads_e_off"), f"a:adn:{aid}"), btn(tr(lang, "ads_e_track_on" if a["track"] else "ads_e_track_off"), f"a:adk:{aid}")],
            [btn(tr(lang, "ads_slot_btn", slot=tr(lang, "slot_" + a["slot"])), f"a:adl:{aid}")], back_row(lang, "a:ads")]
    show(chat_id, mid, txt, kb(rows))

def finish_ad(chat_id, lang, d):
    aid = logic.add_ad(d.get("fa", ""), d.get("en", ""), d.get("photo"), d.get("url", ""), d.get("btn", ""), d.get("slot", "feed"))
    send(chat_id, tr(lang, "ads_added" if aid else "pp_full", n=C.num(lang, logic.MAX_ADS))); ads_panel(chat_id, None, lang)

# ---------------- broadcast ----------------
def broadcast_job(admin_chat, lang, text, ids):
    def job():
        ok = fail = 0
        for i in ids:
            r = send(i, esc(text))
            if r: ok += 1
            else: fail += 1
            time.sleep(0.06)
        send(admin_chat, tr(lang, "a_bc_done", ok=C.num(lang, ok), fail=C.num(lang, fail)))
    if SYNC: job()
    else: threading.Thread(target=job, daemon=True).start()

SYNC = False

def ad_broadcast(admin_chat, lang, aid):
    ids = logic.ad_recipients()
    def job():
        ok = fail = 0
        for i in ids:
            a = logic.get_ad(aid)
            if a and ui.send_ad(i, a, C.user_lang(i)): ok += 1
            else: fail += 1
            time.sleep(0.06)
        send(admin_chat, tr(lang, "a_bc_done", ok=C.num(lang, ok), fail=C.num(lang, fail)))
    if SYNC: job()
    else: threading.Thread(target=job, daemon=True).start()

# ---------------- export ----------------
def do_export(chat_id, lang):
    send(chat_id, tr(lang, "exp_working"))
    def job():
        try:
            okc, badc = R.backfill_media(C.download_file)          # try to fetch photos that failed earlier
            out = tempfile.mkdtemp(prefix="castexp-")
            try:
                res = exporter.export_all(out); exporter.export_calls(out)
                send(chat_id, tr(lang, "exp_done", n=C.num(lang, res["count"]), photos=C.num(lang, len(res["photos"])), bad=C.num(lang, badc)))
                for p in [res["csv"], res["json"], os.path.join(out, "calls.json")] + res["photos"] + ([res["schema"]] if res.get("schema") else []):
                    C.send_document(chat_id, p, os.path.basename(p))
            finally:
                shutil.rmtree(out, ignore_errors=True)
        except Exception as e:
            log.exception("export failed: %s", C.safe(e)); send(chat_id, tr(lang, "exp_fail"))
    if SYNC: job()
    else: threading.Thread(target=job, daemon=True).start()

# ---------------- callbacks ----------------
def callback(data, chat_id, mid, uid, lang):
    p = data.split(":"); op = p[1] if len(p) > 1 else ""
    a = p[2] if len(p) > 2 else ""; b = p[3] if len(p) > 3 else ""
    prev = C.u_awaiting(uid)[1] or {}
    allowed = op in EXTRA_OPS or (op == "exp" and logic.settings()["export_extra_admins"])
    if not logic.is_owner(uid) and not allowed:
        send(chat_id, tr(lang, "a_denied")); return
    if op != "noop": set_await(uid, None)
    try:
        _callback(op, a, b, prev, chat_id, mid, uid, lang)
    except (ValueError, IndexError, KeyError):
        log.warning("bad admin callback: %s", data[:30])

def _callback(op, a, b, prev, chat_id, mid, uid, lang):
    if op == "noop": return
    if op == "home": home(chat_id, mid, lang, uid)
    elif op == "stats": stats(chat_id, mid, lang)
    elif op == "ul": users_list(chat_id, mid, lang, parse_int(a, 1, 10**6) or 1)
    elif op == "u": user_card(chat_id, mid, lang, int(a), uid)
    elif op == "us": set_await(uid, "a_usearch"); send(chat_id, tr(lang, "a_ask_usearch"))
    elif op == "msg": set_await(uid, "a_msg", {"target": int(a)}); send(chat_id, tr(lang, "a_ask_msg", who=esc(who_label(int(a)))))
    elif op == "gc": grant_choice(chat_id, mid, lang, int(a))
    elif op == "ugp":
        t = int(a); until = logic.grant_plan(t, int(b))
        if until is None: send(chat_id, tr(lang, "pp_gone")); return
        pl = logic.get_plan(int(b))
        show(chat_id, mid, tr(lang, "a_done_plan", title=esc(pl["title"]), who=esc(who_label(t))), kb([back_row(lang, f"a:u:{t}")]))
        C.tell_user(t, "u_plan", title=esc(pl["title"]), until=tr(C.user_lang(t), "me_no_expiry") if until == -1 else logic.fmt_date(until))
    elif op == "urp":
        t = int(a); logic.revoke_plan(t)
        show(chat_id, mid, tr(lang, "a_done_revoke", who=esc(who_label(t))), kb([back_row(lang, f"a:u:{t}")])); C.tell_user(t, "u_revoked")
    elif op == "uc": set_await(uid, "a_num", {"op": "credits", "target": int(a)}); send(chat_id, tr(lang, "a_ask_num"))
    elif op in ("bn", "ubn"):
        t = int(a)
        if logic.is_owner(t) or (logic.is_admin(t) and not logic.is_owner(uid)): return
        logic.set_banned(t, op == "bn")
        show(chat_id, mid, tr(lang, "a_done_ban" if op == "bn" else "a_done_unban", who=esc(who_label(t))), kb([back_row(lang, f"a:u:{t}")]))
    elif op == "adp":                       # promote from user card (owner only, enforced by EXTRA_OPS)
        t = int(a)
        if logic.add_admin(t):
            send(chat_id, tr(lang, "ad_added", who=esc(who_label(t)))); C.tell_user(t, "ad_notify_new")
        user_card(chat_id, mid, lang, t, uid)
    elif op == "adx":
        t = int(a)
        if logic.remove_admin(t): send(chat_id, tr(lang, "ad_removed", who=esc(who_label(t)))); C.tell_user(t, "ad_notify_removed")
        admins_panel(chat_id, mid, lang) if prev.get("from_panel", True) else None
    # resumes
    elif op == "rs": finder.panel(chat_id, uid, lang, mid, admin_mode=True)
    elif op == "rid": set_await(uid, "a_rid"); send(chat_id, tr(lang, "a_ask_rid"))
    elif op == "vr": resume_admin(chat_id, lang, int(a), uid)
    elif op == "rh":
        r = R.get(int(a))
        if r:
            R.admin_set(r["id"], "admin_hidden", not r["admin_hidden"])
            send(chat_id, tr(lang, "a_resume_hidden" if not r["admin_hidden"] else "a_resume_unhidden", id=R.rid_str(r["id"])))
    elif op == "rf":
        r = R.get(int(a))
        if r:
            R.admin_set(r["id"], "featured", not r["featured"])
            send(chat_id, tr(lang, "a_resume_unfeatured" if r["featured"] else "a_resume_featured", id=R.rid_str(r["id"])))
            if not r["featured"]: C.tell_user(r["user_id"], "u_featured")
    elif op == "rd":
        send(chat_id, tr(lang, "a_resume_del_confirm", id=R.rid_str(int(a))), kb([[btn(tr(lang, "yes"), f"a:rdy:{a}"), btn(tr(lang, "no"), "a:home")]]))
    elif op == "rdy":
        r = R.get(int(a))
        if r:
            R.delete_resume(r["id"]); send(chat_id, tr(lang, "a_resume_deleted", id=R.rid_str(r["id"]))); C.tell_user(r["user_id"], "u_resume_removed")
    # casting accounts / calls
    elif op == "pcl": pending_casting(chat_id, mid, lang)
    elif op in ("cap", "crj"):
        t = int(a); logic.update_user(t, casting_status="approved" if op == "cap" else "rejected")
        send(chat_id, tr(lang, "a_casting_done", who=esc(who_label(t)), s=tr(lang, "cs_approved" if op == "cap" else "cs_rejected")))
        C.tell_user(t, "u_casting_ok" if op == "cap" else "u_casting_no")
    elif op == "cf":
        c = db.q1("SELECT * FROM calls WHERE id=?", (int(a),))
        if c:
            db.ex("UPDATE calls SET featured=? WHERE id=?", (0 if c["featured"] else 1, c["id"]))
            send(chat_id, tr(lang, "a_call_unfeatured" if c["featured"] else "a_call_featured"))
    elif op == "ch":
        c = db.q1("SELECT * FROM calls WHERE id=?", (int(a),))
        if c: db.ex("UPDATE calls SET status=? WHERE id=?", ("open" if c["status"] == "hidden" else "hidden", c["id"])); send(chat_id, tr(lang, "a_call_toggled"))
    elif op == "cd":
        send(chat_id, tr(lang, "k_del_confirm"), kb([[btn(tr(lang, "yes"), f"a:cdy:{a}"), btn(tr(lang, "no"), "a:home")]]))
    elif op == "cdy":
        db.ex("DELETE FROM calls WHERE id=?", (int(a),)); send(chat_id, tr(lang, "a_call_deleted"))
    # imported calls
    elif op == "imp": imp_panel(chat_id, mid, lang)
    elif op == "impl": imp_list(chat_id, mid, lang, parse_int(a, 1, 10**6) or 1)
    elif op == "impa":
        c = db.q1("SELECT * FROM calls WHERE id=? AND source IS NOT NULL", (int(a),))
        if c and c["status"] == "pending":
            db.ex("UPDATE calls SET status='open' WHERE id=?", (c["id"],)); send(chat_id, tr(lang, "a_imp_approved"))
    elif op == "imph":
        c = db.q1("SELECT * FROM calls WHERE id=? AND source IS NOT NULL", (int(a),))
        if c: db.ex("UPDATE calls SET status=? WHERE id=?", ("hidden" if c["status"] == "open" else "open", c["id"])); send(chat_id, tr(lang, "a_imp_hidden"))
    elif op == "impx":
        send(chat_id, tr(lang, "k_del_confirm"), kb([[btn(tr(lang, "yes"), f"a:impxy:{a}"), btn(tr(lang, "no"), "a:imp")]]))
    elif op == "impxy":
        c = db.q1("SELECT * FROM calls WHERE id=? AND source IS NOT NULL", (int(a),))
        if c:
            importer.mark_rejected(c["id"]); db.ex("DELETE FROM calls WHERE id=?", (c["id"],)); send(chat_id, tr(lang, "a_imp_deleted"))
    elif op == "impe":
        send(chat_id, tr(lang, "a_imp_edit"), kb([[btn(tr(lang, "a_imp_f_" + k), f"a:impf:{a}:{k}") for k in ("title", "city")],
                                                   [btn(tr(lang, "a_imp_f_" + k), f"a:impf:{a}:{k}") for k in ("contact", "details")]]))
    elif op == "impf":
        if b not in IMP_FIELDS or not db.q1("SELECT 1 FROM calls WHERE id=? AND source IS NOT NULL", (int(a),)): return
        set_await(uid, "a_impedit", {"id": int(a), "f": b}); send(chat_id, tr(lang, "a_imp_ask_field"))
    elif op == "impaa":
        n = db.val("SELECT COUNT(*) FROM calls WHERE source=? AND status='pending' AND (flags IS NULL OR flags NOT LIKE '%no_contact%' AND flags NOT LIKE '%roles_unclear%' AND flags NOT LIKE '%maybe_course%')", (importer.SOURCE,), 0)
        send(chat_id, tr(lang, "a_imp_approve_all_ask", n=C.num(lang, n)), kb([[btn(tr(lang, "yes"), "a:impaay"), btn(tr(lang, "no"), "a:imp")]]))
    elif op == "impaay":
        cur = db.ex("UPDATE calls SET status='open' WHERE source=? AND status='pending' AND (flags IS NULL OR flags NOT LIKE '%no_contact%' AND flags NOT LIKE '%roles_unclear%' AND flags NOT LIKE '%maybe_course%')", (importer.SOURCE,))
        send(chat_id, tr(lang, "a_imp_approve_all_ok", n=C.num(lang, cur.rowcount)))
    elif op == "imps": imp_sync_job(chat_id, lang)
    # export / broadcast
    elif op == "exp": do_export(chat_id, lang)
    elif op == "bc":
        show(chat_id, mid, tr(lang, "a_bc_who"), kb([[btn(tr(lang, "aud_all"), "a:bca:all")], [btn(tr(lang, "aud_resume"), "a:bca:resume")],
                                                     [btn(tr(lang, "aud_casting"), "a:bca:casting")], back_row(lang)]))
    elif op == "bca":
        if a not in ("all", "resume", "casting"): return
        set_await(uid, "a_bc", {"aud": a}); send(chat_id, tr(lang, "a_bc_ask"))
    elif op == "bcy":
        pb = db.meta_get("pending_broadcast")
        if not pb: send(chat_id, tr(lang, "a_bc_none")); return
        db.meta_set("pending_broadcast", None)
        show(chat_id, mid, tr(lang, "a_bc_sending")); broadcast_job(chat_id, lang, pb["text"], logic.audience_ids(pb["aud"]))
    elif op == "bcn":
        db.meta_set("pending_broadcast", None); show(chat_id, mid, tr(lang, "a_bc_cancel"), kb([back_row(lang)]))
    # settings
    elif op == "set": settings_panel(chat_id, mid, lang)
    elif op == "sn":
        if a not in logic.NUM_SETTINGS: return
        set_await(uid, "a_setnum", {"key": a}); send(chat_id, tr(lang, "a_s_ask_num"))
    elif op == "tg":
        if a not in logic.BOOL_SETTINGS: return
        logic.toggle_setting(a)
        {"ref_enabled": ref_panel, "ads_enabled": ads_panel, "import_auto_publish": imp_panel}.get(a, settings_panel)(chat_id, mid, lang)
    elif op == "ref": ref_panel(chat_id, mid, lang)
    # admins / owner / support / faq
    elif op == "ad": admins_panel(chat_id, mid, lang)
    elif op == "ada": set_await(uid, "a_ad_add"); send(chat_id, tr(lang, "ad_ask_add"))
    elif op == "own": set_await(uid, "a_owner"); send(chat_id, tr(lang, "ad_owner_ask"))
    elif op == "ownc":
        t = int(a)
        if not logic.is_owner(uid) or t == uid: return
        logic.set_owner(t)
        send(chat_id, tr(lang, "ad_owner_done", who=esc(who_label(t))), ui.main_menu(lang, uid)); C.tell_user(t, "ad_owner_notify_new")
    elif op == "su": support_panel(chat_id, mid, lang)
    elif op == "sup":
        if a in ("primary", "backup"): set_await(uid, "a_su", {"slot": a}); send(chat_id, tr(lang, "su_ask"))
    elif op == "suc": logic.set_support("backup", ""); (C.profile_hook and C.profile_hook()); send(chat_id, tr(lang, "su_cleared")); support_panel(chat_id, None, lang)
    elif op == "fq": faq_panel(chat_id, mid, lang)
    elif op == "fqa": set_await(uid, "fq_add1", {}); send(chat_id, tr(lang, "fq_ask_q"))
    elif op == "fqe": faq_edit(chat_id, mid, lang, int(a))
    elif op == "fqf": set_await(uid, "fq_edit", {"i": int(a), "f": b}); send(chat_id, tr(lang, "fq_ask_field"))
    elif op == "fqx": logic.faq_delete(int(a)); send(chat_id, tr(lang, "fq_deleted")); faq_panel(chat_id, mid, lang)
    # plans
    elif op == "pp": plans_panel(chat_id, mid, lang)
    elif op == "ppa":
        if len(logic.plans()) >= logic.MAX_PLANS: send(chat_id, tr(lang, "pp_full", n=C.num(lang, logic.MAX_PLANS))); return
        set_await(uid, "a_pp_title", {}); send(chat_id, tr(lang, "pp_ask_title"))
    elif op == "ppx": logic.remove_plan(int(a)); send(chat_id, tr(lang, "pp_deleted")); plans_panel(chat_id, mid, lang)
    elif op in ("ppu", "ppd"): logic.move_plan(int(a), -1 if op == "ppu" else 1); plans_panel(chat_id, mid, lang)
    elif op == "ppe": plan_edit(chat_id, mid, lang, int(a))
    elif op == "ppt": logic.toggle_popular(int(a)); plan_edit(chat_id, mid, lang, int(a))
    elif op in PP_FIELDS:
        f, k = PP_FIELDS[op]; set_await(uid, "a_pp_edit", {"id": int(a), "field": f}); send(chat_id, tr(lang, k))
    elif op == "pps":
        d = dict(prev)
        if a == "dur": d["duration"] = ""; set_await(uid, "a_pp_feat", d); send(chat_id, tr(lang, "pp_ask_feat"), kb([[btn(tr(lang, "pp_skip"), "a:pps:feat")]]))
        elif a == "feat": d["features"] = ""; set_await(uid, "a_pp_views", d); send(chat_id, tr(lang, "pp_ask_views"))
    elif op == "ppp":
        d = dict(prev)
        if "title" not in d or "price" not in d: return
        pid = logic.add_plan(d["title"], d["price"], d.get("duration", ""), d.get("features", ""), a == "1", d.get("views", 0), d.get("apps", 0), d.get("posts", 0), d.get("days", 30))
        send(chat_id, tr(lang, "pp_added" if pid else "pp_full", n=C.num(lang, logic.MAX_PLANS))); plans_panel(chat_id, None, lang)
    # ads
    elif op == "ads": ads_panel(chat_id, mid, lang)
    elif op == "ada2": set_await(uid, "ad_fa", {}); send(chat_id, tr(lang, "ads_ask_fa"))
    elif op == "ade": ad_edit(chat_id, mid, lang, int(a))
    elif op == "adn": logic.toggle_ad(int(a), "enabled"); ad_edit(chat_id, mid, lang, int(a))
    elif op == "adk": logic.toggle_ad(int(a), "track"); ad_edit(chat_id, mid, lang, int(a))
    elif op == "adl": logic.toggle_ad(int(a), "slot"); ad_edit(chat_id, mid, lang, int(a))
    elif op == "adx2": logic.remove_ad(int(a)); send(chat_id, tr(lang, "ads_deleted")); ads_panel(chat_id, mid, lang)
    elif op == "adp":
        ad = logic.get_ad(int(a))
        if ad: ui.send_ad(chat_id, ad, lang, count_view=False)
    elif op == "adf":
        if b not in ("fa", "en", "photo", "url", "btn"): return
        set_await(uid, "ad_edit", {"id": int(a), "field": b})
        send(chat_id, tr(lang, {"fa": "ads_ask_fa", "en": "ads_ask_en", "photo": "ads_ask_photo", "url": "ads_ask_url", "btn": "ads_ask_btn"}[b]) + ("\n(- = حذف / clear)" if b in ("photo", "url", "btn") else ""))
    elif op == "ads_skip":
        d = dict(prev)
        nxt = {"en": ("ad_photo", "ads_ask_photo"), "photo": ("ad_url", "ads_ask_url"), "url": ("ad_btn", "ads_ask_btn"), "btn": None}[a]
        if a == "en": d["en"] = d.get("fa", "")
        if nxt:
            set_await(uid, nxt[0], d); send(chat_id, tr(lang, nxt[1]), kb([[btn(tr(lang, "pp_skip"), "a:ads_skip:" + nxt[0][3:])]]))
        else: finish_ad(chat_id, lang, d)
    elif op == "adb":
        show(chat_id, mid, tr(lang, "ads_bc_pick"), kb([[btn(f"#{x['id']} " + (x['fa'] or x['en'])[:30], f"a:adbc:{x['id']}")] for x in logic.ads()] + [back_row(lang, "a:ads")]))
    elif op == "adbc":
        show(chat_id, mid, tr(lang, "ads_bc_confirm", id=int(a), n=C.num(lang, len(logic.ad_recipients()))), kb([[btn(tr(lang, "yes"), f"a:adby:{a}"), btn(tr(lang, "no"), "a:ads")]]))
    elif op == "adby":
        if logic.get_ad(int(a)): show(chat_id, mid, tr(lang, "a_bc_sending")); ad_broadcast(chat_id, lang, int(a))

def text(msg, uid, lang, aw, data):
    """Text/photo replies while an admin awaiting-state is active. True if consumed."""
    chat_id = msg["chat"]["id"]; t = (msg.get("text") or msg.get("caption") or "").strip()
    if not logic.is_owner(uid) and aw not in EXTRA_AWAIT:
        set_await(uid, None); return False
    if aw == "a_impedit":
        f, n = IMP_FIELDS[data["f"]]; set_await(uid, None)
        if not t: return True
        v = R.city_canon(t) if f == "city" else t[:n]
        db.ex(f"UPDATE calls SET {f}=? WHERE id=? AND source IS NOT NULL", (v, data["id"]))
        send(chat_id, tr(lang, "a_imp_saved")); c = db.q1("SELECT * FROM calls WHERE id=?", (data["id"],))
        if c: send(chat_id, castings.imported_text(c, castings.call_roles(c["id"]), lang, full=True, admin=True)[:3900], kb(imp_card_buttons(c, lang)))
        return True
    if aw == "a_usearch":
        set_await(uid, None); search_users_reply(chat_id, lang, t); return True
    if aw == "a_rid":
        digits = re.sub(r"\D", "", C.norm_digits(t))
        set_await(uid, None)
        if not digits or not R.get(int(digits)): send(chat_id, tr(lang, "a_not_found")); return True
        resume_admin(chat_id, lang, int(digits), uid); return True
    if aw == "a_msg":
        if not t: return True
        tgt = data["target"]; set_await(uid, None)
        if logic.is_banned(tgt) and not logic.is_owner(uid): send(chat_id, tr(lang, "a_msg_banned")); return True
        ok = send(tgt, tr(C.user_lang(tgt), "u_msg_from_admin", text=esc(t[:3500])), kb([C.contact_btns(C.user_lang(tgt))]))
        send(chat_id, tr(lang, "a_msg_sent" if ok else "a_msg_fail", who=esc(who_label(tgt))), kb([back_row(lang, f"a:u:{tgt}")])); return True
    if aw == "a_num":
        n = parse_signed(t)
        if n is None or n == 0 or abs(n) > 100000: send(chat_id, tr(lang, "a_bad_num")); return True
        tg_ = data["target"]; set_await(uid, None); logic.add_credits(tg_, n)
        send(chat_id, tr(lang, "a_done_credits", n=C.num(lang, n), who=esc(who_label(tg_))), kb([back_row(lang, f"a:u:{tg_}")]))
        if n > 0: C.tell_user(tg_, "u_credits", n=C.num(C.user_lang(tg_), n))
        return True
    if aw == "a_setnum":
        key = data["key"]; n = parse_signed(t) if key.startswith("free_") else parse_int(t, 0 if key != "ad_every" else 1, 100000)
        if n is None or (key.startswith("free_") and (n < -1 or n > 100000)): send(chat_id, tr(lang, "a_bad_num")); return True
        logic.set_setting(key, n); set_await(uid, None); send(chat_id, tr(lang, "a_s_saved"))
        {"ad_every": ads_panel, "ref_bonus": ref_panel, "ref_invitee_bonus": ref_panel}.get(key, settings_panel)(chat_id, None, lang); return True
    if aw == "a_ad_add":
        tg_ = logic.find_user(t)
        if tg_ is None: send(chat_id, tr(lang, "a_not_found")); return True
        set_await(uid, None)
        if not logic.add_admin(tg_): send(chat_id, tr(lang, "ad_is_owner")); return True
        send(chat_id, tr(lang, "ad_added", who=esc(who_label(tg_)))); C.tell_user(tg_, "ad_notify_new"); admins_panel(chat_id, None, lang); return True
    if aw == "a_owner":
        tg_ = logic.find_user(t)
        if tg_ is None: send(chat_id, tr(lang, "a_not_found")); return True
        set_await(uid, None)
        if logic.is_owner(tg_): send(chat_id, tr(lang, "ad_owner_same")); return True
        send(chat_id, tr(lang, "ad_owner_confirm", who=esc(who_label(tg_))), kb([[btn(tr(lang, "yes"), f"a:ownc:{tg_}"), btn(tr(lang, "no"), "a:ad")]])); return True
    if aw == "a_su":
        name = logic.clean_username(t)
        if not name: send(chat_id, tr(lang, "su_bad")); return True
        logic.set_support(data["slot"], name); set_await(uid, None); (C.profile_hook and C.profile_hook()); send(chat_id, tr(lang, "su_saved")); support_panel(chat_id, None, lang); return True
    if aw == "fq_add1":
        if not t: return True
        data["q"] = t[:200]; set_await(uid, "fq_add2", data); send(chat_id, tr(lang, "fq_ask_a")); return True
    if aw == "fq_add2":
        if not t: return True
        logic.faq_add(data["q"], t[:1500]); set_await(uid, None); send(chat_id, tr(lang, "fq_saved")); faq_panel(chat_id, None, lang); return True
    if aw == "fq_edit":
        if not t: return True
        logic.faq_update(data["i"], **{data["f"]: t}); set_await(uid, None); send(chat_id, tr(lang, "fq_saved")); faq_edit(chat_id, None, lang, data["i"]); return True
    # --- plan wizard
    if aw == "a_pp_title":
        if not t: return True
        data["title"] = t[:60]; set_await(uid, "a_pp_price", data); send(chat_id, tr(lang, "pp_ask_price")); return True
    if aw == "a_pp_price":
        if not t: return True
        data["price"] = t[:120]; set_await(uid, "a_pp_dur", data); send(chat_id, tr(lang, "pp_ask_dur"), kb([[btn(tr(lang, "pp_skip"), "a:pps:dur")]])); return True
    if aw == "a_pp_dur":
        if not t: return True
        data["duration"] = t[:40]; set_await(uid, "a_pp_feat", data); send(chat_id, tr(lang, "pp_ask_feat"), kb([[btn(tr(lang, "pp_skip"), "a:pps:feat")]])); return True
    if aw == "a_pp_feat":
        if not t: return True
        data["features"] = t[:300]; set_await(uid, "a_pp_views", data); send(chat_id, tr(lang, "pp_ask_views")); return True
    for aw_, key, nxt, ask in (("a_pp_views", "views", "a_pp_apps", "pp_ask_apps"), ("a_pp_apps", "apps", "a_pp_posts", "pp_ask_posts"),
                               ("a_pp_posts", "posts", "a_pp_days", "pp_ask_days")):
        if aw == aw_:
            n = parse_signed(t)
            if n is None or n < -1: send(chat_id, tr(lang, "a_bad_num")); return True
            data[key] = n; set_await(uid, nxt, data); send(chat_id, tr(lang, ask)); return True
    if aw == "a_pp_days":
        n = parse_signed(t)
        if n is None or n < 0: send(chat_id, tr(lang, "a_bad_num")); return True
        data["days"] = n; set_await(uid, "a_pp_pop", data)
        send(chat_id, tr(lang, "pp_ask_pop"), kb([[btn(tr(lang, "yes"), "a:ppp:1"), btn(tr(lang, "no"), "a:ppp:0")]])); return True
    if aw == "a_pp_pop":
        send(chat_id, tr(lang, "pp_ask_pop"), kb([[btn(tr(lang, "yes"), "a:ppp:1"), btn(tr(lang, "no"), "a:ppp:0")]])); return True
    if aw == "a_pp_edit":
        if not t: return True
        f = data["field"]
        if f in ("views_month", "apps_month", "posts_month", "days"):
            n = parse_signed(t)
            if n is None or n < (0 if f == "days" else -1): send(chat_id, tr(lang, "a_bad_num")); return True
            val = n
        elif f in ("duration", "features"): val = "" if t == "-" else t
        else: val = t
        ok_ = logic.update_plan(data["id"], **{f: val}); set_await(uid, None)
        send(chat_id, tr(lang, "pp_saved" if ok_ else "pp_gone"))
        plan_edit(chat_id, None, lang, data["id"]) if ok_ else plans_panel(chat_id, None, lang); return True
    # --- ads wizard
    if aw == "ad_fa":
        if msg.get("photo"): data["photo"] = msg["photo"][-1]["file_id"]
        if not t: send(chat_id, tr(lang, "ads_ask_fa")); return True
        data["fa"] = t[:900]; set_await(uid, "ad_en", data); send(chat_id, tr(lang, "ads_ask_en"), kb([[btn(tr(lang, "pp_skip"), "a:ads_skip:en")]])); return True
    if aw == "ad_en":
        if not t: return True
        data["en"] = t[:900]; nxt = "ad_url" if data.get("photo") else "ad_photo"; set_await(uid, nxt, data)
        if nxt == "ad_photo": send(chat_id, tr(lang, "ads_ask_photo"), kb([[btn(tr(lang, "pp_skip"), "a:ads_skip:photo")]]))
        else: send(chat_id, tr(lang, "ads_ask_url"), kb([[btn(tr(lang, "pp_skip"), "a:ads_skip:url")]]))
        return True
    if aw == "ad_photo":
        if not msg.get("photo"): send(chat_id, tr(lang, "ads_ask_photo"), kb([[btn(tr(lang, "pp_skip"), "a:ads_skip:photo")]])); return True
        data["photo"] = msg["photo"][-1]["file_id"]; set_await(uid, "ad_url", data); send(chat_id, tr(lang, "ads_ask_url"), kb([[btn(tr(lang, "pp_skip"), "a:ads_skip:url")]])); return True
    if aw == "ad_url":
        if not re.match(r"^https?://\S+$", t): send(chat_id, tr(lang, "ads_bad_url")); return True
        data["url"] = t[:300]; set_await(uid, "ad_btn", data); send(chat_id, tr(lang, "ads_ask_btn"), kb([[btn(tr(lang, "pp_skip"), "a:ads_skip:btn")]])); return True
    if aw == "ad_btn":
        if not t: return True
        data["btn"] = t[:40]; set_await(uid, None); finish_ad(chat_id, lang, data); return True
    if aw == "ad_edit":
        f = data["field"]; aid = data["id"]
        if f == "photo":
            if msg.get("photo"): val = msg["photo"][-1]["file_id"]
            elif t == "-": val = None
            else: send(chat_id, tr(lang, "ads_ask_photo")); return True
        elif f == "url":
            if t == "-": val = ""
            elif re.match(r"^https?://\S+$", t): val = t
            else: send(chat_id, tr(lang, "ads_bad_url")); return True
        elif f == "btn": val = "" if t == "-" else t
        else:
            if not t: return True
            val = t
        logic.update_ad(aid, **{f: val}); set_await(uid, None); send(chat_id, tr(lang, "ads_saved")); ad_edit(chat_id, None, lang, aid); return True
    # --- broadcast
    if aw == "a_bc":
        if not t: return True
        db.meta_set("pending_broadcast", {"text": t[:3500], "by": uid, "aud": data.get("aud", "all")}); set_await(uid, None)
        send(chat_id, tr(lang, "a_bc_confirm", text=esc(t[:3500]), n=C.num(lang, len(logic.audience_ids(data.get("aud", "all"))))),
             kb([[btn(tr(lang, "yes"), "a:bcy"), btn(tr(lang, "no"), "a:bcn")]])); return True
    return False
