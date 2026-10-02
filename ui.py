"""User-facing screens: main menu (max 5 big buttons), 'more', plans, account, invite, FAQ, about, support, data deletion, ads."""
import os, re, hashlib, logging
from urllib.parse import quote
import config, db, logic, resumes as R
import core as C
from core import tr, esc, btn, kb, grid, send, show

log = logging.getLogger("ui")

def main_menu(lang, uid=None):
    has_resume = bool(uid) and (R.get_by_user(uid) or {}).get("status") == "complete"
    rows = [[btn(tr(lang, "b_my_resume") if has_resume else tr(lang, "b_build"), "m:resume")],
            [btn(tr(lang, "b_search"), "m:search")],
            [btn(tr(lang, "b_calls"), "m:calls")],
            [btn(tr(lang, "b_support"), "m:support")],
            [btn(tr(lang, "b_more"), "m:more"), btn(tr(lang, "b_other_lang"), "m:lang")]]
    if uid and logic.is_admin(uid):
        rows.append([btn(tr(lang, "b_admin"), "a:home")])
    return kb(rows)

def lang_menu():
    return kb([[btn("🇮🇷 فارسی", "l:fa"), btn("🇬🇧 English", "l:en")]])

def sponsor_line(lang, uid):
    ad = logic.sponsor_ad(uid)
    if not ad: return "", None
    logic.ad_count(ad["id"], "views")
    txt = "\n\n" + tr(lang, "sponsor_label") + " " + esc(ad["fa"] if lang == "fa" else ad["en"])
    return txt, ad

def show_menu(chat_id, lang, uid, mid=None):
    C.set_await(uid, None)
    extra, ad = sponsor_line(lang, uid)
    m = main_menu(lang, uid)
    if ad and ad.get("url"):
        import json
        rows = json.loads(m)["inline_keyboard"]; rows.insert(len(rows) - (2 if logic.is_admin(uid) else 1), [ad_button(ad, lang)]); m = kb(rows)
    show(chat_id, mid, tr(lang, "menu_title") + extra, m)

LOGO = os.path.join(config.BASE, "assets", "logo.jpg")

def _logo_sha():
    try:
        with open(LOGO, "rb") as f: return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None

def send_welcome(chat_id, lang, uid):
    """Welcome text as a photo caption (logo file_id cached in the DB; changing the file invalidates the cache)."""
    text = tr(lang, "welcome", name=esc(config.BOT_NAME_FA if lang == "fa" else config.BOT_NAME_EN))
    markup = main_menu(lang, uid); sha = _logo_sha()
    if not sha:
        send(chat_id, text, markup); return
    logo = db.meta_get("logo") or {}
    fid = logo.get("file_id") if logo.get("sha") == sha else None
    data = {"chat_id": chat_id, "caption": text, "parse_mode": "HTML", "reply_markup": markup}
    if fid:
        try: C.call("sendPhoto", dict(data, photo=fid)); return
        except C.ApiError as e: log.warning("cached logo file_id rejected (%s); re-uploading", C.safe(e)[:60])
    try:
        with open(LOGO, "rb") as f:
            res = C.call("sendPhoto", data, files={"photo": ("logo.jpg", f, "image/jpeg")}, timeout=90)
        new = ((res or {}).get("photo") or [{}])[-1].get("file_id")
        if new: db.meta_set("logo", {"sha": sha, "file_id": new})
    except C.ApiError as e:
        log.warning("logo send failed: %s", C.safe(e)[:80]); send(chat_id, text, markup)

# ---------------- more / help / about ----------------
def more_menu(chat_id, lang, uid, mid=None):
    rows = [[btn(tr(lang, "b_plans"), "m:plans"), btn(tr(lang, "b_me"), "m:me")],
            [btn(tr(lang, "b_invite"), "m:invite"), btn(tr(lang, "b_faq"), "m:faq")],
            [btn(tr(lang, "b_help"), "m:help"), btn(tr(lang, "b_about"), "m:about")],
            [btn(tr(lang, "b_delete_data"), "m:deldata")],
            [btn(tr(lang, "b_menu"), "m:menu")]]
    show(chat_id, mid, tr(lang, "more_title"), kb(rows))

def about_text(lang):
    return tr(lang, "about", name=esc(config.BOT_NAME), sp=esc(logic.support()["primary"]))

def show_about(chat_id, lang, uid, mid=None):
    show(chat_id, mid, about_text(lang), kb([[btn(tr(lang, "b_back"), "m:more")]]))

def show_help(chat_id, lang, uid, mid=None):
    show(chat_id, mid, tr(lang, "help"), kb([[btn(tr(lang, "b_back"), "m:more")]]))

def show_support(chat_id, lang, uid, mid=None):
    sp = logic.support()
    rows = [C.contact_btns(lang), [btn(tr(lang, "b_faq"), "m:faq")], [btn(tr(lang, "b_menu"), "m:menu")]]
    show(chat_id, mid, tr(lang, "support_text", note=C.support_note(lang)), kb(rows))

def show_faq(chat_id, lang, uid, mid=None, idx=None):
    items = logic.faq()
    if idx is None:
        rows = [[btn(("❓ " + (i_["q_fa"] if lang == "fa" else i_["q_en"]))[:60], f"m:faq:{i}")] for i, i_ in enumerate(items)]
        rows.append([btn(tr(lang, "b_menu"), "m:menu")])
        show(chat_id, mid, tr(lang, "faq_title") if items else tr(lang, "faq_none"), kb(rows)); return
    if not 0 <= idx < len(items): return show_faq(chat_id, lang, uid, mid)
    it = items[idx]
    show(chat_id, mid, "❓ <b>%s</b>\n\n%s" % (esc(it["q_fa"] if lang == "fa" else it["q_en"]), esc(it["a_fa"] if lang == "fa" else it["a_en"])),
         kb([[btn(tr(lang, "b_back"), "m:faq")], C.contact_btns(lang)]))

# ---------------- plans / account / invite ----------------
def plan_card(lang, p):
    dur = ("\n⏳ " + esc(p["duration"])) if p.get("duration") else ""
    def lim(n):
        return tr(lang, "lim_unl") if n < 0 else C.num(lang, n)
    perks = "\n".join(["👁 " + tr(lang, "pl_views", n=lim(p["views_month"])) if p["views_month"] else "",
                       "📨 " + tr(lang, "pl_apps", n=lim(p["apps_month"])) if p["apps_month"] else "",
                       "📢 " + tr(lang, "pl_posts", n=lim(p["posts_month"])) if p["posts_month"] else ""]).strip("\n")
    perks = "\n".join(x for x in perks.split("\n") if x)
    feats = [x.strip(" •-\t") for x in re.split(r"[|;\n]+", p.get("features") or "") if x.strip(" •-\t")][:8]
    fl = ("\n" + "\n".join("✔️ " + esc(x) for x in feats)) if feats else ""
    card = tr(lang, "plans_card", title=esc(p["title"]), price=esc(p["price"]), dur=dur, perks=("\n" + perks) if perks else "", feats=fl)
    return (tr(lang, "pp_popular") + "\n" + card) if p.get("popular") else card

def free_lines(lang):
    s = logic.settings()
    def v(n): return tr(lang, "lim_unl") if n < 0 else C.num(lang, n)
    return tr(lang, "plans_free_lines", views=v(s["free_views_month"]), apps=v(s["free_apps_month"]), posts=v(s["free_posts_month"]))

def show_plans(chat_id, uid, lang, mid=None):
    ready = [p for p in logic.plans() if logic.plan_ready(p)]
    parts = [tr(lang, "plans_title"), tr(lang, "plans_free", lines=free_lines(lang))]
    parts += [plan_card(lang, p) for p in ready]
    if not ready: parts.append(tr(lang, "plans_none"))
    parts.append(tr(lang, "plans_footer", uid=uid, note=C.support_note(lang)))
    rows = [C.contact_btns(lang)]
    if logic.settings()["ref_enabled"]: rows.append([btn(tr(lang, "b_invite"), "m:invite")])
    rows.append([btn(tr(lang, "b_back"), "m:more")])
    show(chat_id, mid, "\n\n━━━━━━━━━━\n\n".join(parts), kb(rows))

def quota_line(lang, uid, kind):
    qt = logic.quota(uid, kind)
    label = tr(lang, "q_" + kind)
    if qt["unlimited"]: return f"{label}: {tr(lang, 'lim_unl')}"
    return f"{label}: {C.num(lang, qt['left'])} / {C.num(lang, qt['limit'])}"

def show_me(chat_id, uid, lang, mid=None):
    u = logic.get_user(uid); r = R.get_by_user(uid)
    lines = [tr(lang, "me_head")]
    if logic.is_admin(uid): lines.append(tr(lang, "me_admin"))
    p = logic.user_plan(uid)
    if p:
        until = logic.plan_until(uid)
        lines.append(tr(lang, "me_plan", title=esc(p["title"]), until=tr(lang, "me_no_expiry") if until == -1 else logic.fmt_date(until)))
    else:
        lines.append(tr(lang, "me_free"))
    lines.append(tr(lang, "me_resume", s=tr(lang, "rs_complete") if r and r["status"] == "complete" else (tr(lang, "rs_draft") if r else tr(lang, "rs_none"))))
    if u.get("casting_status") == "approved" or logic.is_admin(uid):
        lines += [quota_line(lang, uid, "views"), quota_line(lang, uid, "posts")]
    if r and r["status"] == "complete" or not u.get("casting_status") in ("approved",):
        lines.append(quota_line(lang, uid, "apps"))
    lines.append(tr(lang, "me_credits", n=C.num(lang, u.get("credits", 0))))
    lines.append(tr(lang, "me_ref", n=C.num(lang, u.get("ref_count", 0)), b=C.num(lang, u.get("ref_earned", 0))))
    lines.append(tr(lang, "me_id", uid=uid))
    show(chat_id, mid, "\n".join(lines), kb([[btn(tr(lang, "b_plans"), "m:plans"), btn(tr(lang, "b_invite"), "m:invite")], C.contact_btns(lang), [btn(tr(lang, "b_back"), "m:more")]]))

def upgrade_prompt(chat_id, uid, lang, kind):
    """Monthly free quota (and credits) used up -> plans + numeric id + contact buttons."""
    rows = [C.contact_btns(lang), [btn(tr(lang, "b_plans"), "m:plans")]]
    if logic.settings()["ref_enabled"]: rows.append([btn(tr(lang, "b_invite"), "m:invite")])
    rows.append([btn(tr(lang, "b_menu"), "m:menu")])
    send(chat_id, tr(lang, "quota_out_" + kind, uid=uid, note=C.support_note(lang)), kb(rows))

def invite_share_url(link, body):
    return "https://t.me/share/url?url=" + quote(link, safe="") + "&text=" + quote(body, safe="")

def show_invite(chat_id, uid, lang, mid=None):
    s = logic.settings(); u = logic.get_user(uid)
    if not s["ref_enabled"]:
        return show(chat_id, mid, tr(lang, "invite_off"), kb([[btn(tr(lang, "b_back"), "m:more")]]))
    link = f"https://t.me/{C.BOT_USERNAME}?start=ref_{uid}"
    inv = tr(lang, "invite_invitee_line", b=C.num(lang, s["ref_invitee_bonus"])) if s["ref_invitee_bonus"] > 0 else ""
    body = tr(lang, "invite_share_text")
    show(chat_id, mid, tr(lang, "invite_text", link=link, bonus=C.num(lang, s["ref_bonus"]), invitee_line=inv,
                          n=C.num(lang, u.get("ref_count", 0)), earned=C.num(lang, u.get("ref_earned", 0))),
         kb([[btn(tr(lang, "b_share"), url=invite_share_url(link, body))], [btn(tr(lang, "b_back"), "m:more")]]))

# ---------------- delete my data ----------------
def delete_data_ask(chat_id, lang, uid, mid=None):
    show(chat_id, mid, tr(lang, "deldata_ask"), kb([[btn(tr(lang, "yes_delete"), "m:deldata_ok"), btn(tr(lang, "no"), "m:more")]]))

def delete_data_do(chat_id, lang, uid, mid=None):
    R.delete_user_data(uid)
    show(chat_id, mid, tr(lang, "deldata_done"), kb([[btn(tr(lang, "b_start_again"), "m:menu")]]))

# ---------------- ads ----------------
def ad_button(ad, lang):
    label = ad.get("btn") or tr(lang, "b_ad_open")
    return btn(label, f"ad:{ad['id']}") if ad.get("track") else btn(label, url=ad["url"])

def ad_markup(ad, lang):
    return kb([[ad_button(ad, lang)]]) if ad.get("url") else None

def send_ad(chat_id, ad, lang, count_view=True):
    text = tr(lang, "ad_label") + "\n" + esc(ad["fa"] if lang == "fa" else ad["en"])
    markup = ad_markup(ad, lang)
    try:
        if ad.get("photo"):
            data = {"chat_id": chat_id, "photo": ad["photo"], "caption": text[:1024], "parse_mode": "HTML"}
            if markup: data["reply_markup"] = markup
            r = C.call("sendPhoto", data)
        else:
            r = C.send(chat_id, text, markup)
    except C.ApiError as e:
        log.warning("ad send failed: %s", C.safe(e)[:80]); return None
    if r is not None and count_view: logic.ad_count(ad["id"], "views")
    return r

def maybe_ad(chat_id, uid, lang):
    """Count one user action and show a feed ad when due (never for premium users/admins)."""
    logic.note_action(uid)
    ad = logic.ad_due(uid)
    if ad: send_ad(chat_id, ad, lang)
