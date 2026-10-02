"""Importer: public Telegram channel preview (https://t.me/s/<channel>) -> casting calls in 'pending' (moderation) state.

* Reads ONLY the public web preview (no login, no API). Paginates with ?before=<oldest id>. Polite: 1 s between pages.
* Every post that was looked at is remembered in `imports` (dedupe by post id; deleted calls are never re-imported).
* Parsing is heuristic (regex on free-form Persian text). Anything doubtful is flagged and stays in moderation, even with auto-publish on.
* Contact info is kept exactly as the post published it; nothing is added, guessed or enriched.
* The content belongs to the channel owner. Every imported call carries a credit line + link to the original post.
"""
import re, json, html, time, logging, unicodedata, difflib, threading, argparse
import requests
import config, db, fa, logic, options as O

log = logging.getLogger("importer")
SOURCE = config.IMPORT_CHANNEL
UA = {"User-Agent": "Mozilla/5.0 (compatible; %s-importer)" % config.BOT_NAME_EN}
_lock = threading.Lock()

# ------------------------------------------------------------------ fetching / HTML
def fetch_page(before=None, channel=SOURCE, timeout=30):
    url = "https://t.me/s/%s" % channel + ("?before=%d" % before if before else "")
    r = requests.get(url, headers=UA, timeout=timeout)
    r.raise_for_status()
    return r.text

def parse_page(page_html, channel=SOURCE):
    """-> list of {id, date(ISO UTC), text, media, fwd}. Tolerant: an unexpected layout yields [] instead of an exception."""
    out = []
    for blk in page_html.split("tgme_widget_message_wrap")[1:]:
        m = re.search(r'data-post="%s/(\d+)"' % re.escape(channel), blk)
        if not m: continue
        t = re.search(r'js-message_text[^>]*>(.*?)</div>', blk, re.S)
        txt = ""
        if t:
            raw = re.sub(r"<br\s*/?>", "\n", t.group(1))
            txt = html.unescape(re.sub(r"<[^>]+>", "", raw))
        d = re.search(r'<time[^>]*datetime="([^"]+)"', blk)
        out.append({"id": int(m.group(1)), "date": d.group(1) if d else None, "text": txt.strip(),
                    "media": "photo" if "tgme_widget_message_photo_wrap" in blk else ("video" if "message_video" in blk else ""),
                    "fwd": "forwarded_from" in blk})
    return out

# ------------------------------------------------------------------ text helpers
def strip_deco(s):
    """Remove emoji/decoration symbols but keep letters, digits, punctuation and the Persian ZWNJ."""
    out = []
    for ch in s:
        if ch == "\u200c": out.append(ch); continue
        cat = unicodedata.category(ch)
        if cat in ("So", "Sk", "Cs", "Co", "Cn") or ch in "\u200d\ufe0f\u200e\u200f\u202a\u202b\u202c\u202d\u202e\ufffd\u20e3": continue
        if cat == "Cf": continue
        out.append(ch)
    return "".join(out)

FOOTER_RE = re.compile(r"(بزرگ‌?ترین کانال فراخوان|بزرگترین کانال فراخوان|فعال ?ترین و بزرگ)")
def body_lines(text):
    """Original text -> list of cleaned lines (footer/channel-promo removed, decoration kept out)."""
    lines = []
    for ln in (text or "").splitlines():
        if FOOTER_RE.search(ln): break
        ln = strip_deco(ln).replace("\u200f", "").strip()
        if re.fullmatch(r"https?://t\.me/farakhan\w*/?", ln): continue
        lines.append(ln)
    while lines and not lines[-1]: lines.pop()
    # collapse blank runs
    res = []
    for ln in lines:
        if not ln and (not res or not res[-1]): continue
        res.append(ln)
    return [l for l in res]

def clean_body(text, limit=1800):
    s = "\n".join(body_lines(text)).strip()
    return s if len(s) <= limit else s[:limit].rstrip() + "…"

# ------------------------------------------------------------------ classification
CAST_HEAD = re.compile(r"(جذب|فراخوان|انتخاب بازیگر|تست بازیگری|آخرین فرصت انتخاب|بازیگر (?:خانم|آقا|فرم)|پرفورمر|نیاز به)")
WORKSHOP_HEAD = re.compile(r"(نمایشگاه|کارگاه|ورک ?شاپ|مستر ?کلاس|دوره|آموزش|ثبت ?نام|کلاس|تور |پذیرش|مسابقه|بلیت|تخفیف|اجاره|پکیچ|پست پروداکشن|دفتر پیش تولید|استودیو عکاسی)")
AD_BODY = re.compile(r"(مشاوره رایگان|صفر تا صد|اجاره تجهیزات|خدمات تخصصی|ساخت فیلمت|لینک (?:کانال|گروه)|سنجاق شده|پذیرش دانشجو|ثبت ?نام ورودی|لاغری|حجم ?دهی|استخاره|تبلیغات خود را|بلیت مهمان|کانال ها و گروه ها)")
ART_WORDS = re.compile(r"(بازیگر|تئاتر|نمایش|فیلم|سریال|تیزر|مستند|کلیپ|سینما|عوامل|مجری|گریم|تدوین|فیلمبردار|تصویربردار|کارگردان|نویسنده|صدا|نوازنده|مدل|منشی صحنه|پرفورمر|اجرا)")
COURSE_WORDS = re.compile(r"(کارگاه|دوره|شهریه|هزینه ثبت|کلاس|آموزشگاه|هنرجو)")

GENERIC_HEAD = re.compile(r"^(فراخوان )?همکار[يی]( در)?( شهر)?\s*[:：]?\s*(تهران|کرج|حومه|[،, ])*$")
def header(lines):
    """Headline of the call: the first line that names the hiring ('جذب …' / 'فراخوان …' / 'بازیگر …').
    Generic first lines («فراخوان همکاری در شهر تهران», «لطفا اطلاع رسانی کنید», «( فیلم سینمایی )») are skipped."""
    first = ""
    for ln in lines[:10]:
        t = ln.strip(" .-–—_•·")
        if len(t) < 6: continue
        if re.match(r"^(لطفا اطلاع|اطلاعیه|سلام)", t) or GENERIC_HEAD.match(t): continue
        if not first: first = t
        if len(t) <= 90 and CAST_HEAD.search(t) and not re.match(r"^(\(|\[)", t): return t
    return first

def classify(post):
    """-> (kind, reason): kind 'call' or 'noise'."""
    text = post.get("text") or ""
    lines = body_lines(text)
    body = "\n".join(lines)
    if len(body) < 80: return "noise", "short/no text"
    h = header(lines)
    if AD_BODY.search(body) and not re.search(r"(جذب|دعوت به همکاری)", h): return "noise", "channel ad/info"
    cast_h = bool(CAST_HEAD.search(h)) or (bool(re.search(r"(بازیگر|عوامل)", h)) and bool(re.search(r"دعوت به همکاری", body)))
    if WORKSHOP_HEAD.search(h) and not re.search(r"جذب", h): return "noise", "workshop/course/ad"
    l0 = next((l for l in lines if l.strip()), "")
    if WORKSHOP_HEAD.search(l0) and not re.search(r"جذب", l0): return "noise", "workshop/course/ad"
    first = " ".join(l for l in lines[:6] if l)
    if re.search(r"(کارگاه|ورک ?شاپ|مستر ?کلاس|شهریه)", first) and not re.search(r"(جذب|دعوت به همکاری)", body): return "noise", "workshop/course/ad"
    if re.search(r"(کارگاه|ورک ?شاپ|مستر ?کلاس|ثبت ?نام|دوره)", first) and not re.search(r"جذب", first): return "noise", "workshop/course/ad"
    if not cast_h: return "noise", "not a casting headline"
    if not ART_WORDS.search(body): return "noise", "off-topic"
    return "call", ""

# ------------------------------------------------------------------ field extraction
GENDER_PAT = [("خانم", r"(خانم|دختر|زن\b|بانو)"), ("آقا", r"(آقا|اقا|پسر|مرد\b)"), ("کودک", r"(کودک|بچه)")]
ROLE_PAT = [
    ("actor", r"(بازیگر|پرفورمر|کمدین|نقش اول|نقش\s?های|بدلکار|گوینده|صداپیشه|بازی)"),
    ("director", r"(کارگردان|گروه کارگردانی)"),
    ("cinematographer", r"(فیلم ?بردار|تصویر ?بردار|دستیار تصویر|مدیر فیلمبرداری)"),
    ("editor", r"(تدوین)"),
    ("sound", r"(صدا ?بردار|صدا ?گذار|اپراتور (?:نور و )?صدا|دستیار صدا|طراح (?:و دستیار )?صدا|افکت)"),
    ("makeup", r"(گریم)"),
    ("costume", r"(طراح لباس|صحنه و لباس|لباس)"),
    ("set_design", r"(طراح (?:و دستیار )?صحنه|طراحی صحنه|صحنه و لباس)"),
    ("lighting", r"(نور ?پرداز|طراح (?:و دستیار )?نور|اپراتور نور|دستیار نور|نورپردازی)"),
    ("writer", r"(فیلمنامه ?نویس|نمایشنامه ?نویس|نویسنده|ایده ?پرداز)"),
    ("producer", r"(تهیه ?کننده|سرمایه ?گذار|اسپانسر|مدیر تولید)"),
    ("assistant", r"(دستیار|منشی صحنه|مدیر صحنه|مدیر اجرایی|کارآموز|مدیر برنامه|روابط عمومی)"),
]
CREDIT_LINE = re.compile(r"^\s*(کارگردان(?:ان)?|نویسنده|نویسندگی و کارگردانی|تهیه ?کننده|مجری طرح|سرپرست پروژه|انتخاب بازیگر|مدیر تولید|مشاور[^:：]*|طراح و کارگردان|دستیار کارگردان)\s*[:：]\s*\S+")
CITY_EXTRA = ["لاهیجان", "لواسان", "رشت", "البرز", "گیلان", "اراک", "زنجان", "ارومیه", "بوشهر", "گرگان", "قزوین", "اردبیل", "سنندج", "ایلام", "بیرجند", "بجنورد"]
MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
MONTH_RE = "|".join(sorted(MONTHS, key=len, reverse=True))

def detect_type(text, h):
    probes = [("theatre", r"(تئاتر|نمایش|اجرا ?خوانی|کنسرت نمایش|صحنه)"), ("series", r"(سریال)"), ("short", r"(فیلم ?کوتاه)"),
              ("documentary", r"(مستند)"), ("music_video", r"(موزیک ?ویدیو|موزیک ویدئو)"),
              ("commercial", r"(تیزر|تبلیغ|کلیپ|دوربین مخفی|محتوای تصویری|محتوا)"), ("film", r"(فیلم ?سینمایی|فیلم ?بلند|فیلم نیمه ?بلند|فیلم|سینما)")]
    for scope in (h, text[:700]):
        best = None
        for code, pat in probes:
            m = re.search(pat, scope)
            if m and (best is None or m.start() < best[0]): best = (m.start(), code)
        if best: return best[1]
    return "other"

def detect_roles(lines):
    cand = [l for l in lines if not CREDIT_LINE.match(l)]
    # drop trailing contact/deadline sections: only the part before "ارسال" matters for roles
    cut = []
    for l in cand:
        if re.match(r"^(ارسال|جهت ارتباط|هماهنگی|مهلت|تماس)", l.strip()): break
        cut.append(l)
    blob = "\n".join(cut)
    roles = []
    for code, pat in ROLE_PAT:
        if re.search(pat, blob): roles.append(code)
    if "director" in roles and not re.search(r"(جذب|از)[^\n]{0,40}کارگردان|کارگردان[^\n]{0,20}(خانم|آقا|مسلط)|^\s*[\d۰-۹]+\s*[_\-.)]\s*کارگردان|گروه کارگردانی", blob, re.M):
        roles.remove("director")
    if "assistant" in roles and "director" in roles and not re.search(r"دستیار", blob): pass
    return roles or ["other"]

def detect_gender(text):
    t = text[:900]; got = [name for name, pat in GENDER_PAT if re.search(pat, t)]
    if "خانم" in got and "آقا" in got: return "خانم و آقا" + (" و کودک" if "کودک" in got else "")
    return " و ".join(got)

def detect_ages(text):
    t = fa.digits(text); rng = []
    for m in re.finditer(r"(?<!\d)(\d{1,2})\s*(?:تا|الی|الا|-|–|_)\s*(\d{1,2})(?!\d)\s*(ساله|سال|سنین)?", t):
        a, b, unit = int(m.group(1)), int(m.group(2)), m.group(3)
        tail = t[m.end():m.end() + 14]; head = t[max(0, m.start() - 12):m.start()]
        if re.match(r"\s*(میلیون|هزار|تومان|درصد|ساعت|جلسه|مهر|آبان|آذر|دی|بهمن|اسفند|فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور)", tail): continue
        if not (unit or re.search(r"(سن|سنین)", head + tail)): continue
        if 1 <= a <= b <= 90: rng.append((a, b))
    if not rng: return ""
    lo, hi = min(a for a, _ in rng), max(b for _, b in rng)
    return "%d تا %d سال" % (lo, hi)

def detect_fee(lines):
    for l in lines:
        if re.search(r"(دستمزد|حق ?الزحمه|رایگان|میلیون|تومان|هدیه|درصدی|بدون دستمزد|قرارداد|قرار داد)", l) and len(l) < 140 and not re.search(r"(مشاوره|شماره|آموزش|ورک)", l):
            if re.search(r"(آموزش داده|ورک ?شاپ|کارگاه)", l) and not re.search(r"دستمزد", l): continue
            s = re.sub(r"[«»\[\]()]", "", l).strip(" :-")
            if re.search(r"(دستمزد|حق ?الزحمه|رایگان|قرارداد|قرار داد|هدیه|درصدی)", s) or re.search(r"\d.*(میلیون|تومان)", fa.digits(s)): return s[:90]
    return ""

def detect_city(h, text):
    names = [c for c, _ in O.CITIES] + CITY_EXTRA
    for scope in (h, text[:600]):
        best = None
        for c in names:
            m = re.search(r"(?<![\w‌])%s(?![\w‌])" % re.escape(c), scope)
            if m and (best is None or m.start() < best[0]): best = (m.start(), c)
        if best: return best[1]
    return None

def jalali_year_of(iso):
    s = fa.iso_to_jalali_str(iso or "")
    return (int(s[:4]), int(s[5:7])) if s else (1405, 1)

DL_PREFIX = re.compile(r"^\s*[-–]?\s*(?:آخرین )?مهلت(?: فراخوان| ارسال(?: رزومه| درخواست| آثار)?| ثبت ?نام)?\s*[:：]?\s*")

def detect_deadline(lines, post_iso):
    """-> (text, iso_date or None). 'text' is the published wording."""
    for i, l in enumerate(lines):
        if not re.search(r"مهلت", l): continue
        txt = re.sub(r"[«»\[\]]", "", l).strip()
        if not re.search(MONTH_RE, txt) and i + 1 < len(lines) and re.search(MONTH_RE, lines[i + 1]) and len(lines[i + 1]) < 60:
            txt = txt.rstrip(" :") + " " + lines[i + 1].strip()
        t = fa.digits(txt)
        m = re.search(r"(?:(\d{1,2})\s*)?(%s)(?:\s*ماه)?(?:\s*(\d{4}))?" % MONTH_RE, t)
        shown = DL_PREFIX.sub("", txt).strip(" :-–") or txt
        if not m: return shown[:60], None
        day, mon, yr = m.group(1), MONTHS.index(m.group(2)) + 1, m.group(3)
        py, pm = jalali_year_of(post_iso)
        y = int(yr) if yr else (py + 1 if mon < pm - 3 else py)
        d = int(day) if day and not (len(day) == 4) else (31 if mon <= 6 else (30 if mon <= 11 else 29))
        d = min(d, 31 if mon <= 6 else (30 if mon <= 11 else 29))
        try:
            gy, gm, gd = fa.jalali_to_gregorian(y, mon, d)
            return shown[:60], "%04d-%02d-%02d" % (gy, gm, gd)
        except Exception:
            return shown[:60], None
    return "", None

CHANNEL_HANDLES = re.compile(r"^(farakhan\w*|modeling\w*|sanat_modeling\w*)$", re.I)
def extract_contacts(text):
    """Contacts exactly as published: Telegram @ids, WhatsApp links, phone numbers, Instagram ids/links."""
    lines = (text or "").splitlines()
    out = {"tg": [], "wa": [], "phone": [], "ig": []}
    def add(k, v):
        if v and v not in out[k]: out[k].append(v)
    for ln in lines:
        if FOOTER_RE.search(ln): break
        ln_d = fa.digits(ln); is_ig = bool(re.search(r"(اینستا|instagram|\big\b)", ln_d, re.I))
        for m in re.finditer(r"wa\.me/(\+?\d{8,15}|qr/[A-Za-z0-9]{6,40})", ln_d): add("wa", m.group(1).lstrip("+") if m.group(1)[0] != "q" else m.group(1))
        for m in re.finditer(r"(?:instagram\.com|instagr\.am)/([A-Za-z0-9_.]{2,40})", ln_d, re.I): add("ig", m.group(1).strip("."))
        for m in re.finditer(r"(?<![\w@./])@([A-Za-z][A-Za-z0-9_]{4,31})(?![\w@])", ln_d):
            h = m.group(1)
            if CHANNEL_HANDLES.match(h): continue
            add("ig" if is_ig else "tg", h)
        for m in re.finditer(r"(?<![\d/])(\+\d{10,14}|09\d{9})(?!\d)", ln_d): add("phone", m.group(1))
    # a phone that is also the WhatsApp link number is the same contact: keep wa + a phone line only once
    wa_digits = {re.sub(r"\D", "", w)[-10:] for w in out["wa"] if w[0] != "q"}
    out["phone"] = [p for p in out["phone"] if re.sub(r"\D", "", p)[-10:] not in wa_digits or True]
    return out

def contact_keys(c):
    ks = set(h.lower() for h in c.get("tg", [])) | {re.sub(r"\D", "", p)[-10:] for p in c.get("phone", [])}
    ks |= {re.sub(r"\D", "", w)[-10:] for w in c.get("wa", []) if w[:1] != "q"}
    return ks

def fingerprint(text):
    lines = body_lines(text); keep = []
    for l in lines:
        if re.search(r"(مهلت|@|wa\.me|https?://|\+?\d{10,})", l): continue
        keep.append(l)
    s = fa.norm(" ".join(keep)); s = re.sub(r"[\d]+", "#", s); s = re.sub(r"[^\w\s#]", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:700]

def project_name(text):
    """Project/show name if the post gives one: «…» quotes, or a parenthesised name after the headline (not a city / fee / genre)."""
    ls = body_lines(text)
    body = "\n".join(ls)[:600]
    skip = re.compile(r"(دستمزد|رایگان|تهران|کرج|مشهد|اصفهان|شیراز|تبریز|خانم|آقا|فوری|ژانر|زوج|کودک|سینمایی|تلویزیونی|اینستاگرام|ساله)")
    m = re.search(r"[«“\"]\s*([^»”\"\n]{3,40}?)\s*[»”\"]", body)
    if m and not skip.search(m.group(1)): return m.group(1).strip()
    for ln in ls[1:8]:
        m = re.search(r"\(\s*([^()\n]{3,30}?)\s*\)\s*$", ln)
        if m and not skip.search(m.group(1)) and not re.search(r"[\d@]", m.group(1)): return m.group(1).strip()
    return None

BLOCKING_FLAGS = ("no_contact", "roles_unclear", "maybe_course")   # these keep a call in moderation even when auto-publish is on

def parse(post):
    """post dict (from parse_page) -> call dict, or None when it is not a casting call. Never raises on odd text."""
    kind, why = classify(post)
    if kind != "call": return None
    text = post["text"]; lines = body_lines(text); h = header(lines)
    title = fa.clean(re.sub(r"\s+", " ", re.sub(r"\(\s*([^()]*?)\s*\)", r"(\1)", h)), 100)
    pn = project_name(text)
    if pn and pn not in title and len(title) + len(pn) < 96: title = f"{title} — {pn}"
    contacts = extract_contacts(text)
    dl_text, dl_iso = detect_deadline(lines, post.get("date"))
    flags = []
    if not (contacts["tg"] or contacts["wa"] or contacts["phone"] or contacts["ig"]): flags.append("no_contact")
    roles = detect_roles(lines)
    if roles == ["other"]: flags.append("roles_unclear")
    city = detect_city(h, "\n".join(lines))
    if not city: flags.append("no_city")
    body = "\n".join(lines)
    if COURSE_WORDS.search(body) and not re.search(r"(دستمزد|دعوت به همکاری)", body): flags.append("maybe_course")
    blocking = [f for f in flags if f in BLOCKING_FLAGS]
    return {"title": title, "blocking": blocking, "project_type": detect_type("\n".join(lines), h), "roles": roles, "city": city,
            "gender_text": detect_gender("\n".join(lines)), "age_text": detect_ages(body), "fee_text": detect_fee(lines),
            "deadline_text": dl_text, "deadline_iso": dl_iso, "contacts": contacts, "flags": flags,
            "details": clean_body(text), "date_text": dl_text or None, "date_iso": dl_iso}

# ------------------------------------------------------------------ store
def source_url(post_id): return "https://t.me/%s/%d" % (SOURCE, post_id)

def _owner():
    return logic.owner_id() or config.OWNER_ID

def _ensure_owner_user():
    """calls.user_id is a FK to users; imported calls belong to the owner account (no new fake user rows)."""
    oid = _owner()
    if not db.q1("SELECT 1 FROM users WHERE id=?", (oid,)):
        db.ex("INSERT INTO users(id,first_seen,last_seen,lang) VALUES(?,?,?,'fa')", (oid, db.now_iso(), db.now_iso()))
    return oid

def similar_known(fp, contacts):
    """Existing/rejected imported call that is the same call re-posted? -> imports row or None."""
    keys = contact_keys(contacts)
    best = None
    for r in db.q("SELECT * FROM imports WHERE source=? AND kind IN ('call','rejected') AND fingerprint IS NOT NULL ORDER BY post_id DESC LIMIT 400", (SOURCE,)):
        ratio = difflib.SequenceMatcher(None, fp, r["fingerprint"]).ratio()
        rk = set(json.loads(r.get("reason") or "[]")) if (r.get("reason") or "").startswith("[") else set()
        same_contact = bool(keys and rk and (keys & rk))
        if (ratio >= 0.80 and same_contact) or ratio >= 0.95:
            if best is None or ratio > best[0]: best = (ratio, r)
    return best[1] if best else None

def store(post, parsed, auto_publish=False):
    """Insert one parsed call (status pending, or open if auto_publish and high confidence). -> call_id."""
    oid = _ensure_owner_user()
    flags = parsed["flags"]
    status = "open" if (auto_publish and not parsed.get("blocking")) else "pending"
    with db.tx():
        cid = db.ex("""INSERT INTO calls(user_id,title,project_type,city,date_text,date_iso,details,contact,status,created_at,
                       source,source_post,source_url,source_date,source_text,gender_text,age_text,fee_text,deadline_text,deadline_iso,contacts,flags)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (oid, parsed["title"], parsed["project_type"], parsed["city"], parsed["date_text"], parsed["date_iso"], parsed["details"],
                     contact_line(parsed["contacts"]), status, db.now_iso(), SOURCE, post["id"], source_url(post["id"]), post.get("date"),
                     post["text"][:4000], parsed["gender_text"], parsed["age_text"], parsed["fee_text"], parsed["deadline_text"],
                     parsed["deadline_iso"], json.dumps(parsed["contacts"], ensure_ascii=False), json.dumps(flags))).lastrowid
        for r_ in parsed["roles"]: db.ex("INSERT OR IGNORE INTO call_roles(call_id, role) VALUES(?,?)", (cid, r_))
        db.ex("INSERT OR REPLACE INTO imports(source,post_id,kind,reason,call_id,fingerprint,post_date,fetched_at) VALUES(?,?,?,?,?,?,?,?)",
              (SOURCE, post["id"], "call", json.dumps(sorted(contact_keys(parsed["contacts"]))), cid, fingerprint(post["text"]), post.get("date"), db.now_iso()))
    return cid, status

def contact_line(c):
    parts = []
    parts += ["@" + h for h in c.get("tg", [])]
    parts += [p for p in c.get("phone", [])]
    parts += ["wa.me/" + w for w in c.get("wa", [])]
    parts += ["instagram.com/" + i for i in c.get("ig", [])]
    return " ، ".join(parts)[:300]

def mark_rejected(call_id):
    """Admin deleted an imported call: remember it so the same post / a re-post is not imported again."""
    db.ex("UPDATE imports SET kind='rejected' WHERE call_id=?", (int(call_id),))

def _refresh(call, post, parsed):
    """Same call re-posted later by the channel: move the call to the newest post (not touching status/featured)."""
    db.ex("""UPDATE calls SET source_post=?, source_url=?, source_date=?, source_text=?, details=?, deadline_text=?, deadline_iso=?, date_text=?, date_iso=?,
             age_text=?, fee_text=?, gender_text=? WHERE id=?""",
          (post["id"], source_url(post["id"]), post.get("date"), post["text"][:4000], parsed["details"], parsed["deadline_text"], parsed["deadline_iso"],
           parsed["date_text"], parsed["date_iso"], parsed["age_text"], parsed["fee_text"], parsed["gender_text"], call["id"]))

def is_expired(parsed, post, today_iso):
    if parsed["deadline_iso"]: return parsed["deadline_iso"] < today_iso
    d = (post.get("date") or "")[:10]
    return bool(d) and d < db.now_iso(db.now() - config.IMPORT_MAX_AGE_DAYS * 86400)[:10]

def expire_old():
    """Imported calls whose published deadline passed -> closed (pending ones too). Returns how many."""
    today = db.now_iso()[:10]
    n = 0
    for c in db.q("SELECT id FROM calls WHERE source=? AND status IN ('open','pending') AND deadline_iso IS NOT NULL AND deadline_iso<?", (SOURCE, today)):
        db.ex("UPDATE calls SET status='closed' WHERE id=?", (c["id"],)); n += 1
    return n

# ------------------------------------------------------------------ sync
def collect(fetch, known_max, cutoff, max_pages, stats):
    """Page backwards from the newest post until we reach an already-seen id / the age limit. -> list of new posts."""
    new, before = [], None
    for _ in range(max_pages):
        try: posts = parse_page(fetch(before))
        except Exception as e:
            stats["errors"] += 1; log.warning("import fetch failed: %s", str(e)[:120]); break
        stats["pages"] += 1
        if not posts: break
        reached = False
        for p in posts:
            if p["id"] <= known_max or db.q1("SELECT 1 FROM imports WHERE source=? AND post_id=?", (SOURCE, p["id"])):
                reached = True; stats["known"] += 1; continue
            if not known_max and (p.get("date") or "9999")[:10] < cutoff: reached = True; continue
            new.append(p)
        before = min(p["id"] for p in posts)
        if reached: break
        if fetch is fetch_page: time.sleep(1.0)       # polite
    return new

def sync(max_pages=None, dry=False, fetch=None, notify=None, today_iso=None):
    """Fetch only NEW posts (ids above the newest known one; first run: back to IMPORT_MAX_AGE_DAYS), classify, parse, store.
    Returns a stats dict. `fetch(before)` is injectable for tests; dry=True stores nothing."""
    if not _lock.acquire(blocking=False): return {"skipped": "already running"}
    fetch = fetch or fetch_page; max_pages = max_pages or config.IMPORT_MAX_PAGES
    today_iso = today_iso or db.now_iso()[:10]
    st = {"pages": 0, "found": 0, "calls_parsed": 0, "imported_pending": 0, "imported_open": 0, "reposts": 0, "noise": 0,
          "expired": 0, "known": 0, "errors": 0, "new_ids": [], "noise_reasons": {}, "samples": []}
    try:
        auto = bool(logic.settings().get("import_auto_publish"))
        known_max = db.val("SELECT MAX(post_id) FROM imports WHERE source=?", (SOURCE,), 0) or 0
        cutoff = db.now_iso(db.now() - config.IMPORT_MAX_AGE_DAYS * 86400)[:10]
        new = collect(fetch, known_max, cutoff, max_pages, st)
        st["found"] = len(new)
        for p in sorted(new, key=lambda x: x["id"]):
            try:
                parsed = parse(p)
                if parsed is None:
                    st["noise"] += 1; why = classify(p)[1]; st["noise_reasons"][why] = st["noise_reasons"].get(why, 0) + 1
                    if not dry: db.ex("INSERT OR IGNORE INTO imports(source,post_id,kind,reason,post_date,fetched_at) VALUES(?,?,?,?,?,?)",
                                      (SOURCE, p["id"], "noise", why, p.get("date"), db.now_iso()))
                    continue
                st["calls_parsed"] += 1
                if len(st["samples"]) < 40: st["samples"].append((p["id"], parsed))
                if is_expired(parsed, p, today_iso):
                    st["expired"] += 1
                    if not dry: db.ex("INSERT OR IGNORE INTO imports(source,post_id,kind,reason,post_date,fetched_at) VALUES(?,?,?,?,?,?)",
                                      (SOURCE, p["id"], "noise", "expired", p.get("date"), db.now_iso()))
                    continue
                ex_ = db.q1("SELECT id FROM calls WHERE source=? AND source_post=?", (SOURCE, p["id"]))
                if ex_:                                  # call already exists for this post (imports row was lost): just re-record it
                    if not dry: db.ex("INSERT OR IGNORE INTO imports(source,post_id,kind,reason,call_id,fingerprint,post_date,fetched_at) VALUES(?,?,?,?,?,?,?,?)",
                                      (SOURCE, p["id"], "call", json.dumps(sorted(contact_keys(parsed["contacts"]))), ex_["id"], fingerprint(p["text"]), p.get("date"), db.now_iso()))
                    st["known"] += 1; continue
                fp = fingerprint(p["text"]); same = similar_known(fp, parsed["contacts"])
                if same:
                    st["reposts"] += 1
                    if not dry:
                        db.ex("INSERT OR IGNORE INTO imports(source,post_id,kind,reason,call_id,fingerprint,post_date,fetched_at) VALUES(?,?,?,?,?,?,?,?)",
                              (SOURCE, p["id"], "repost", "same as %s" % same["post_id"], same.get("call_id"), fp, p.get("date"), db.now_iso()))
                        c = db.q1("SELECT * FROM calls WHERE id=?", (same.get("call_id"),)) if same.get("call_id") else None
                        if c and same["kind"] == "call" and c["status"] in ("open", "pending") and p["id"] > (c["source_post"] or 0): _refresh(c, p, parsed)
                    continue
                if dry: st["imported_pending"] += 1; continue
                cid, status = store(p, parsed, auto_publish=auto)
                st["new_ids"].append(cid)
                st["imported_open" if status == "open" else "imported_pending"] += 1
            except Exception as e:
                st["errors"] += 1; log.exception("import: post %s failed: %s", p.get("id"), str(e)[:100])
        if not dry:
            st["expired"] += expire_old()
            db.meta_set("import_last", {"at": db.now_iso(), "found": st["found"], "pending": st["imported_pending"], "open": st["imported_open"],
                                        "errors": st["errors"]})
        if notify and st["new_ids"] and not dry:
            try: notify(st)
            except Exception as e: log.warning("import notify failed: %s", str(e)[:80])
        log.info("import sync: new_posts=%d calls=%d pending=%d open=%d reposts=%d noise=%d expired=%d errors=%d",
                 st["found"], st["calls_parsed"], st["imported_pending"], st["imported_open"], st["reposts"], st["noise"], st["expired"], st["errors"])
        return st
    finally:
        _lock.release()

def start_periodic(notify=None, interval=None, first_delay=20):
    """Background thread: sync every `interval` seconds. Failures only log; the bot never depends on it."""
    interval = interval or config.IMPORT_INTERVAL
    def loop():
        time.sleep(first_delay)
        while True:
            try: sync(notify=notify)
            except Exception as e: log.warning("periodic import failed: %s", str(e)[:100])
            time.sleep(interval)
    th = threading.Thread(target=loop, daemon=True, name="importer"); th.start(); return th

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Import casting calls from the public channel preview into the bot DB (status=pending).")
    ap.add_argument("--dry", action="store_true"); ap.add_argument("--pages", type=int, default=None)
    ap.add_argument("--db", default=None)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if a.db: db.set_path(a.db)
    db.init(); r = sync(max_pages=a.pages, dry=a.dry)
    r = dict(r); r.pop("samples", None); print(json.dumps(r, ensure_ascii=False, indent=1))
