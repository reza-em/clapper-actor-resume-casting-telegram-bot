#!/usr/bin/env python3
"""Casting & crew-recruiting Telegram bot (long polling, plain requests, SQLite)."""
import os, sys, json, time, logging, fcntl, hashlib, threading
import importer, config
import core as C
if __name__ == "__main__" and not C.TOKEN:
    print(f"{config.TOKEN_ENV} is not set (export it before starting)", file=sys.stderr); sys.exit(1)
import db, logic, resumes as R, ui, wizard, finder, castings, admin
from core import tr, esc, btn, kb, send, ApiError, set_await, u_awaiting

log = logging.getLogger("bot")

# ------------------------------------------------------------------ bot profile (name / about <=120 / description <=512)
NAME = config.BOT_NAME
ABOUT = {   # <= 120 characters each (checked by tests)
    "fa": "🎬 رزومه بازیگر و عوامل تئاتر و فیلم، کستینگ و فراخوان و آگهی بازیگر. بساز، پیدا کن، پیدا شو ✨",
    "en": "🎬 Actor & crew resumes, casting calls and auditions for theatre & film. Build, search, get cast ✨",
}
DESC = {    # <= 512 characters each incl. the advertising line (checked by tests)
    "fa": f"🎬 «{config.BOT_NAME_FA}» — رزومه و کستینگ بازیگران و عوامل تئاتر و فیلم\n📝 رزومه‌ی حرفه‌ای بساز: بازیگر، کارگردان، فیلمبردار، تدوینگر، گریم، صدا، نور، طراح لباس و صحنه\n🎭 فراخوان و آگهی بازیگر و عوامل تئاتر، سینما و سریال رو ببین و با یک لمس درخواست بده\n🔍 کارگردان و تهیه‌کننده: آگهی کستینگ بذار و بازیگر مناسب رو جستجو کن\n🔒 هر وقت خواستی رزومه‌ات رو مخفی یا پاک کن\nشروع: /start 💖",
    "en": f"🎬 “{config.BOT_NAME_EN}” — resumes & casting for actors and crew in theatre and film\n📝 Build a pro resume: actor, director, cinematographer, editor, makeup, sound, lighting, costume, set design\n🎭 Browse casting calls & auditions for theatre, cinema and series and apply in one tap\n🔍 Directors & producers: post casting calls and search talent\n🔒 Hide or delete your resume any time\nStart: /start 💖",
}
AD_LINE = {"fa": "📢 تبلیغات و همکاری: @{sp}", "en": "📢 Ads & cooperation: @{sp}"}

def description(code):
    """Bot description (limit 512) = DESC + advertising line with the *current* primary support contact."""
    sp = logic.support().get("primary") or config.DEFAULT_SUPPORT_PRIMARY
    return (DESC[code] + "\n" + AD_LINE[code].format(sp=sp))[:512]

COMMANDS = {   # exactly the commands handle_message() understands (plus /cancel, /admin which are not advertised)
    "fa": [("start", "شروع 🎬"), ("resume", "رزومه من 📝"), ("search", "جستجوی رزومه 🔍"), ("calls", "آگهی‌ها و فراخوان‌ها 🎭"),
           ("plans", "پلن‌ها 💎"), ("invite", "دعوت دوستان 🎁"), ("support", "پشتیبانی 📞"), ("help", "راهنما ℹ️"), ("lang", "زبان 🌐")],
    "en": [("start", "Start 🎬"), ("resume", "My resume 📝"), ("search", "Search resumes 🔍"), ("calls", "Casting calls 🎭"),
           ("plans", "Plans 💎"), ("invite", "Invite friends 🎁"), ("support", "Support 📞"), ("help", "Help ℹ️"), ("lang", "Language 🌐")],
}

def call(*a, **k):
    return C.call(*a, **k)

def setup_profile():
    """setMyName / setMyDescription / setMyShortDescription / setMyCommands for default + fa + en (skipped when unchanged)."""
    sig = hashlib.sha256(json.dumps([NAME, ABOUT, description("fa"), description("en"), COMMANDS], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if db.meta_get("profile_sha") == sig:
        log.info("bot profile already up to date"); return True
    ok = True
    for code in (None, "fa", "en"):
        extra = {"language_code": code} if code else {}
        k = code or "en"
        steps = [("setMyName", {"name": NAME}), ("setMyShortDescription", {"short_description": ABOUT[k]}),
                 ("setMyDescription", {"description": description(k)}),
                 ("setMyCommands", {"commands": json.dumps([{"command": c, "description": d} for c, d in COMMANDS[k]], ensure_ascii=False)})]
        for m, d in steps:
            try: call(m, dict(d, **extra))
            except ApiError as e:
                ok = False; log.warning("%s(%s) failed: %s", m, code or "default", C.safe(e)[:100])
    if ok: db.meta_set("profile_sha", sig)
    log.info("bot profile set (ok=%s)", ok)
    return ok

# ------------------------------------------------------------------ gates
def allowed(chat_id, uid, lang):
    if logic.is_banned(uid) and not logic.is_admin(uid):
        send(chat_id, tr(lang, "banned")); return False
    return True

def _bind(tg, chat_id):
    if logic.bind_owner_if_needed(tg):
        log.info("owner bound to numeric id %s", tg["id"])
        send(chat_id, tr(C.user_lang(tg["id"], tg), "a_bound", uid=tg["id"]))

# slash-command shortcuts -> the same screens as the menu buttons
SHORTCUTS = {"/menu": "menu", "/resume": "resume", "/search": "search", "/calls": "calls", "/plans": "plans", "/invite": "invite",
             "/support": "support", "/help": "help", "/lang": "lang", "/about": "about", "/me": "me", "/faq": "faq"}

# ------------------------------------------------------------------ messages
ADMIN_AW_PREFIXES = ("a_", "fq_", "ad_")

def handle_message(msg):
    if "from" not in msg or msg["from"].get("is_bot") or msg["chat"].get("type") != "private":
        return
    chat_id = msg["chat"]["id"]; tg = msg["from"]; uid = tg["id"]
    is_new, _ = logic.touch_user(tg)
    _bind(tg, chat_id)
    lang = C.user_lang(uid, tg)
    text = (msg.get("text") or "").strip()
    aw, awd = u_awaiting(uid)
    is_admin = logic.is_admin(uid)

    if text.startswith("/"):
        parts = text.split(None, 1); cmd = parts[0].split("@")[0].lower(); arg = parts[1].strip() if len(parts) > 1 else ""
        if cmd == "/start":
            if not allowed(chat_id, uid, lang): return
            if is_new and arg.startswith("ref_") and arg[4:].isdigit():
                r = logic.try_referral(uid, int(arg[4:]))
                if r:
                    log.info("referral: %s invited %s", arg[4:], uid)
                    send(int(arg[4:]), tr(C.user_lang(int(arg[4:])), "ref_joined_referrer", bonus=C.num(C.user_lang(int(arg[4:])), r["bonus"])))
                    if r["invitee_bonus"] > 0: send(chat_id, tr(lang, "ref_joined_invitee", bonus=C.num(lang, r["invitee_bonus"])))
            set_await(uid, None)
            ui.send_welcome(chat_id, lang, uid); return
        if cmd == "/cancel":
            set_await(uid, None); ui.show_menu(chat_id, lang, uid); return
        if cmd == "/admin" and is_admin:
            set_await(uid, None); admin.home(chat_id, None, lang, uid); return
        if not allowed(chat_id, uid, lang): return
        if cmd in SHORTCUTS:
            set_await(uid, None); route_menu(SHORTCUTS[cmd], chat_id, uid, lang, None); return
        send(chat_id, tr(lang, "unknown_cmd"), ui.main_menu(lang, uid)); return

    if not allowed(chat_id, uid, lang): return
    if aw and aw.startswith(ADMIN_AW_PREFIXES) and is_admin:
        if admin.text(msg, uid, lang, aw, awd): return
    if aw == "wiz":
        if text: wizard.on_text(msg, uid, lang, awd)
        elif msg.get("photo") or msg.get("document"): wizard.on_photo(msg, uid, lang, awd)
        else: send(chat_id, tr(lang, "w_send_photo"))
        return
    if aw == "s_text" and text:
        finder.on_text(msg, uid, lang, awd.get("kind")); return
    if aw in ("k_regname", "k_new") and text:
        if castings.on_text(msg, uid, lang, aw, awd): return
    ui.show_menu(chat_id, lang, uid)

# ------------------------------------------------------------------ callbacks
def handle_callback(cq):
    cid = cq["id"]; data = cq.get("data") or ""
    try: call("answerCallbackQuery", {"callback_query_id": cid})
    except ApiError as e: log.warning("answerCallbackQuery: %s", C.safe(e)[:80])
    m = cq.get("message")
    if not m: return
    chat_id = m["chat"]["id"]; mid = m.get("message_id"); uid = cq["from"]["id"]
    if data == "a:noop": return
    logic.touch_user(cq["from"]); _bind(cq["from"], chat_id)
    lang = C.user_lang(uid, cq["from"]); is_admin = logic.is_admin(uid)
    if data.startswith("l:"):
        code = data[2:]
        if code not in ("fa", "en"): return
        logic.update_user(uid, lang=code)
        ui.show_menu(chat_id, code, uid, mid)
        return
    if not allowed(chat_id, uid, lang): return
    if data.startswith("a:"):
        if not is_admin:
            log.warning("non-admin %s tried admin callback", uid); return
        admin.callback(data, chat_id, mid, uid, lang); return
    if data[:2] in ("w:", "s:", "k:"):
        mod = {"w:": wizard, "s:": finder, "k:": castings}[data[:2]]
        try: mod.callback(data, chat_id, mid, uid, lang)
        except (ValueError, IndexError, KeyError):        # stale/malformed button data: ignore quietly
            log.warning("bad callback data: %s", data[:30])
        return
    if data.startswith("ad:"):
        try: aid = int(data[3:])
        except ValueError: return
        ad = logic.ad_count(aid, "clicks")
        if ad and ad.get("url"):
            send(chat_id, tr(lang, "ad_click_msg", url=esc(ad["url"])), kb([[btn(ad.get("btn") or tr(lang, "b_ad_open"), url=ad["url"])]]))
        return
    if not data.startswith("m:"): return
    p = data.split(":"); op = p[1]
    if op != "resume": set_await(uid, None)          # leaving the wizard/filters: next text is not swallowed (progress is saved)
    route_menu(op, chat_id, uid, lang, mid, p)

def route_menu(op, chat_id, uid, lang, mid, p=None):
    p = p or ["m", op]
    if op == "menu": ui.show_menu(chat_id, lang, uid, mid)
    elif op == "resume": wizard.open_from_menu(chat_id, uid, lang, mid) if not (R.get_by_user(uid) or {}).get("status") == "complete" else wizard.my_resume(chat_id, uid, lang, mid)
    elif op == "search": finder.panel(chat_id, uid, lang, mid)
    elif op == "calls": castings.menu(chat_id, uid, lang, mid)
    elif op == "support": ui.show_support(chat_id, lang, uid, mid)
    elif op == "more": ui.more_menu(chat_id, lang, uid, mid)
    elif op == "lang": show_lang(chat_id, mid, lang)
    elif op == "plans": ui.show_plans(chat_id, uid, lang, mid)
    elif op == "me": ui.show_me(chat_id, uid, lang, mid)
    elif op == "invite": ui.show_invite(chat_id, uid, lang, mid)
    elif op == "faq": ui.show_faq(chat_id, lang, uid, mid, int(p[2]) if len(p) > 2 and p[2].isdigit() else None)
    elif op == "help": ui.show_help(chat_id, lang, uid, mid)
    elif op == "about": ui.show_about(chat_id, lang, uid, mid)
    elif op == "deldata": ui.delete_data_ask(chat_id, lang, uid, mid)
    elif op == "deldata_ok": ui.delete_data_do(chat_id, lang, uid, mid)

def show_lang(chat_id, mid, lang):
    C.show(chat_id, mid, tr(lang, "pick_lang"), ui.lang_menu())

def handle_update(up):
    try:
        if up.get("message"): handle_message(up["message"])
        elif up.get("callback_query"): handle_callback(up["callback_query"])
    except Exception as e:
        log.exception("handler error: %s", C.safe(e))
        try:
            chat = (up.get("message") or up.get("callback_query", {}).get("message") or {}).get("chat", {})
            if chat.get("id"): send(chat["id"], C.T["fa"]["unexpected"] + "\n" + C.T["en"]["unexpected"], html=False)
        except Exception:
            pass

def single_instance():
    fd = open(os.path.join(C.BASE, "bot.lock"), "a+")
    try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another instance is already running", file=sys.stderr); sys.exit(0)
    fd.seek(0); fd.truncate(); fd.write(str(os.getpid())); fd.flush()
    return fd

C.profile_hook = lambda: threading.Thread(target=setup_profile, daemon=True).start()

def main():
    _lock = single_instance()
    C.setup_logging()
    db.init()
    me = call("getMe")
    C.BOT_USERNAME = me["username"]; C.BOT_ID = me["id"]
    log.info("%s started: @%s", config.BOT_NAME, C.BOT_USERNAME)
    threading.Thread(target=lambda: R.backfill_media(C.download_file), daemon=True).start()
    setup_profile()
    if os.environ.get("CAST_IMPORT", "1") != "0":
        importer.start_periodic(notify=admin.imp_notify)        # every config.IMPORT_INTERVAL s; only new posts; new calls wait for approval
    try:
        wh = call("getWebhookInfo")
        if wh.get("url"):
            log.info("Webhook was set; deleting to use long polling"); call("deleteWebhook")
    except ApiError as e:
        log.warning("webhook check: %s", C.safe(e)[:80])
    offset = None
    while True:
        try:
            params = {"timeout": 30, "allowed_updates": json.dumps(["message", "callback_query"])}
            if offset: params["offset"] = offset
            updates = call("getUpdates", params, timeout=45)
        except ApiError as e:
            log.warning("getUpdates: %s", C.safe(e)[:100]); time.sleep(5); continue
        for up in updates:
            offset = up["update_id"] + 1
            handle_update(up)

if __name__ == "__main__":
    main()
