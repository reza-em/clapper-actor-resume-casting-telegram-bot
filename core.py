"""Telegram plumbing: API calls, token redaction, i18n, keyboards, sending, file download, awaiting-state helpers."""
import os, sys, json, logging, re
import requests
import config, db, logic
from texts import T

TOKEN = os.environ.get(config.TOKEN_ENV, "")
API = f"https://api.telegram.org/bot{TOKEN}/"
FILE_API = f"https://api.telegram.org/file/bot{TOKEN}/"
BASE = config.BASE
BOT_USERNAME = ""
BOT_ID = 0

class RedactFilter(logging.Filter):
    def filter(self, record):
        try: msg = record.getMessage()
        except Exception: return True
        if TOKEN and TOKEN in msg:
            record.msg = msg.replace(TOKEN, "<TOKEN>"); record.args = ()
        return True

def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for h in logging.getLogger().handlers: h.addFilter(RedactFilter())
    logging.getLogger("urllib3").setLevel(logging.WARNING)

log = logging.getLogger("bot")

def safe(e):
    s = str(e)
    return s.replace(TOKEN, "<TOKEN>") if TOKEN else s

sess = requests.Session()

class ApiError(Exception):
    pass

def call(method, data=None, files=None, timeout=60):
    try:
        r = sess.post(API + method, data=data, files=files, timeout=timeout)
    except requests.RequestException as e:
        raise ApiError("network: " + type(e).__name__)
    try: j = r.json()
    except Exception: raise ApiError(f"bad response HTTP {r.status_code}")
    if not j.get("ok"): raise ApiError(j.get("description", "unknown error"))
    return j["result"]

def download_file(file_id, dest, max_bytes=config.MAX_PHOTO_BYTES):
    """Download a Telegram file to `dest` atomically. Returns byte count. Raises ApiError."""
    info = call("getFile", {"file_id": file_id}, timeout=30)
    path = info.get("file_path")
    if not path: raise ApiError("no file_path")
    if info.get("file_size") and int(info["file_size"]) > max_bytes: raise ApiError("file too big")
    try:
        r = sess.get(FILE_API + path, timeout=60)
    except requests.RequestException as e:
        raise ApiError("network: " + type(e).__name__)
    if r.status_code != 200: raise ApiError(f"download HTTP {r.status_code}")
    data = r.content
    if len(data) > max_bytes: raise ApiError("file too big")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    with open(tmp, "wb") as f: f.write(data)
    os.replace(tmp, dest)
    return len(data)

# ---------------- i18n ----------------
def tr(lang, key, **kw):
    s = T[lang][key]
    return s.format(**kw) if kw else s

def esc(t):
    return str(t if t is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

_FA_DIG = "۰۱۲۳۴۵۶۷۸۹"
def num(lang, n):
    s = str(n)
    return s.translate(str.maketrans("0123456789", _FA_DIG)) if lang == "fa" else s

def user_lang(uid, tg_user=None):
    lang = logic.get_user(uid).get("lang")
    return lang if lang in ("fa", "en") else "fa"

_DIG = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def norm_digits(s):
    return (s or "").translate(_DIG)

def parse_int(s, lo=0, hi=100000):
    s = norm_digits(s).strip()
    if not re.fullmatch(r"\d{1,9}", s): return None
    n = int(s)
    return n if lo <= n <= hi else None

# ---------------- keyboards ----------------
def kb(rows): return json.dumps({"inline_keyboard": rows})

def btn(text, data=None, url=None):
    b = {"text": text}
    if url: b["url"] = url
    else: b["callback_data"] = data
    return b

def grid(buttons, per=2):
    return [buttons[i:i + per] for i in range(0, len(buttons), per)]

def contact_btns(lang):
    sp = logic.support()
    if sp.get("backup"):
        return [btn(tr(lang, "b_support1"), url="https://t.me/" + sp["primary"]),
                btn(tr(lang, "b_support2"), url="https://t.me/" + sp["backup"])]
    return [btn(tr(lang, "b_contact"), url="https://t.me/" + sp["primary"])]

profile_hook = None

def support_note(lang):
    sp = logic.support()
    if sp.get("backup"): return tr(lang, "note_two", p=sp["primary"], b=sp["backup"])
    return tr(lang, "note_one", p=sp["primary"])

# ---------------- sending ----------------
def send(chat_id, text, markup=None, html=True, **extra):
    data = {"chat_id": chat_id, "text": text[:4096], "disable_web_page_preview": True}
    if markup: data["reply_markup"] = markup
    if html: data["parse_mode"] = "HTML"
    data.update(extra)
    try: return call("sendMessage", data)
    except ApiError as e:
        log.warning("sendMessage failed: %s", safe(e)[:100])

def show(chat_id, msg_id, text, markup=None, html=True):
    """Edit a panel message in place if possible, else send a new one."""
    if msg_id:
        data = {"chat_id": chat_id, "message_id": msg_id, "text": text[:4096], "disable_web_page_preview": True}
        if markup: data["reply_markup"] = markup
        if html: data["parse_mode"] = "HTML"
        try: return call("editMessageText", data)
        except ApiError as e:
            if "not modified" in str(e).lower(): return None
    return send(chat_id, text, markup, html)

def send_photo(chat_id, file_id, caption="", markup=None):
    data = {"chat_id": chat_id, "photo": file_id, "parse_mode": "HTML"}
    if caption: data["caption"] = caption[:1024]
    if markup: data["reply_markup"] = markup
    try: return call("sendPhoto", data)
    except ApiError as e:
        log.warning("sendPhoto failed: %s", safe(e)[:100])

def send_document(chat_id, path, caption=""):
    try:
        with open(path, "rb") as f:
            return call("sendDocument", {"chat_id": chat_id, "caption": caption[:1000]},
                        files={"document": (os.path.basename(path), f)}, timeout=300)
    except ApiError as e:
        log.warning("sendDocument failed: %s", safe(e)[:100])

def delete_msg(chat_id, msg_id):
    if not msg_id: return
    try: call("deleteMessage", {"chat_id": chat_id, "message_id": msg_id})
    except ApiError: pass

def tell_user(uid, key, **kw):
    send(uid, tr(user_lang(uid), key, **kw))

# -------- awaiting state --------
def set_await(uid, kind, data=None):
    logic.update_user(uid, awaiting=kind, await_data=(data if data is not None else None) if kind else None)

def u_awaiting(uid):
    u = logic.get_user(uid)
    return u.get("awaiting"), (u.get("await_data") or {})

def uname_of(u): return ("@" + u["username"]) if u.get("username") else ""

def who_label(uid):
    u = logic.get_user(uid)
    return f"{u.get('name') or uid} {uname_of(u)} ({uid})".replace("  ", " ")
