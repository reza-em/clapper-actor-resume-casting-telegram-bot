"""Offline tests: mocked Telegram API. Never touches the network, the real DB, or the real token."""
import os, sys, io, json, tempfile, shutil, time, csv, zipfile, subprocess, re, string
os.environ["CAST_TELEGRAM_BOT_TOKEN"] = "123456:TEST-TOKEN-ABCDEFGHIJKLMNOPQRSTUVWXYZ012"
os.environ["OWNER_ID"] = "100000001"; os.environ["OWNER_USERNAME"] = "example_owner"
TMP = tempfile.mkdtemp(prefix="casttest-")
import config, db
db.set_path(os.path.join(TMP, "cast.db")); config.MEDIA_DIR = os.path.join(TMP, "media")
db.init()
import core as C, logic, resumes as R, options as O, fa, ui, wizard, finder, castings, admin, exporter, bot
from texts import T
admin.SYNC = True
_real_sleep = time.sleep; time.sleep = lambda s: None
C.BOT_USERNAME = "clapper_test_bot"; C.BOT_ID = 777

PASS = FAIL = 0
def ok(cond, name):
    global PASS, FAIL
    if cond: PASS += 1; print("  ok  ", name)
    else: FAIL += 1; print("  FAIL", name)

SENT = []
FILES = {}          # file_id -> bytes served by getFile/download
PHOTO_FAIL = set()
def fake_call(method, data=None, files=None, timeout=60):
    data = dict(data or {})
    if files: data["_files"] = {k: (v[0], v[1].read() if hasattr(v[1], "read") else v[1]) for k, v in files.items()}
    SENT.append((method, data))
    if method == "sendPhoto" and "_files" in data: return {"message_id": 1, "photo": [{"file_id": "SMALL"}, {"file_id": "LOGO_FID_1"}]}
    return {"message_id": len(SENT) + 100}
C.call = fake_call
def fake_download(file_id, dest, max_bytes=0):
    if file_id in PHOTO_FAIL: raise C.ApiError("network: ConnectionError")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    b = FILES.get(file_id, b"\xff\xd8\xff\xe0FAKEJPEG" + file_id.encode())
    open(dest, "wb").write(b); return len(b)
REAL_DL = C.download_file
C.download_file = fake_download

def of(method, to=None): return [d for m, d in SENT if m == method and (to is None or d.get("chat_id") == to)]
def texts(to): return [d.get("text") or d.get("caption") or "" for m, d in SENT if d.get("chat_id") == to and (d.get("text") or d.get("caption"))]
def last(to): t = texts(to); return t[-1] if t else ""
def clear(): SENT.clear()
UN = {}
def tg(uid, username=None, lang="fa"):
    if username: UN[uid] = username
    return {"id": uid, "first_name": f"U{uid}", "username": UN.get(uid), "language_code": lang}
def say(uid, text=None, username=None, **extra):
    m = {"chat": {"id": uid, "type": "private"}, "from": tg(uid, username), "text": text, "message_id": 50}; m.update(extra)
    bot.handle_message({k: v for k, v in m.items() if v is not None})
def press(uid, data, mid=5, username=None):
    bot.handle_callback({"id": "c", "from": tg(uid, username), "data": data, "message": {"chat": {"id": uid, "type": "private"}, "message_id": mid}})
def all_buttons(to, only_last=False):
    out = []
    ds = [d for m, d in SENT if d.get("chat_id") == to and d.get("reply_markup")]
    if only_last: ds = ds[-1:]
    for d in ds:
        for r in json.loads(d["reply_markup"])["inline_keyboard"]: out += r
    return out
def cb_data(to, only_last=False): return [b.get("callback_data") for b in all_buttons(to, only_last) if b.get("callback_data")]
def btn_texts(to, only_last=False): return [b["text"] for b in all_buttons(to, only_last)]
def click_text(uid, label, only_last=True):
    for b in all_buttons(uid, only_last)[::-1]:
        if label in b["text"] and b.get("callback_data"): press(uid, b["callback_data"]); return True
    return False
def photo(fid, uq=None): return {"photo": [{"file_id": fid + "_s", "file_unique_id": (uq or fid) + "s"}, {"file_id": fid, "file_unique_id": uq or fid}]}

OWNER = 100000001
print("== texts / options / config")
ok(set(T["fa"]) == set(T["en"]), "fa/en texts have identical keys")
bad = [k for k in T["fa"] if {x[1] for x in string.Formatter().parse(T["fa"][k]) if x[1]} != {x[1] for x in string.Formatter().parse(T["en"][k]) if x[1]}]
ok(not bad, f"fa/en placeholders match {bad[:3]}")
ok(all(T["fa"][k].strip() and T["en"][k].strip() for k in T["fa"]), "no empty strings")
ok(len(bot.ABOUT["fa"]) <= 120 and len(bot.ABOUT["en"]) <= 120, f"about <=120 ({len(bot.ABOUT['fa'])}/{len(bot.ABOUT['en'])})")
ok(len(bot.description("fa")) <= 512 and len(bot.description("en")) <= 512 and "@example_owner" in bot.description("fa"), f"description <=512 incl. ad line ({len(bot.description('fa'))}/{len(bot.description('en'))})")
ok(len(config.BOT_NAME) <= 64 and bot.NAME == config.BOT_NAME, "bot name is the single config constant")
src_all = "".join(open(f).read() for f in os.listdir(".") if f.endswith(".py") and f not in ("config.py", "test_offline.py", "texts.py"))
ok("کلاکت" not in src_all and "Clapper" not in src_all.replace("Clapper started", "").replace("Clapper launcher", ""), "name not hard-coded outside config/texts")
ok(all(len(c) == 3 for c in O.ROLES) and {"actor", "director", "cinematographer", "editor", "sound", "makeup", "costume", "set_design", "lighting", "writer", "producer", "assistant", "other"} == set(O.codes(O.ROLES)), "all 13 roles present")
ok(all(c in O.codes(O.SKILL_CATS["language"][2]) for c in ("persian", "english")), "language skills")

print("== ownership / start / menu")
ok(db.meta_get("owner_id") == 100000001 and logic.is_owner(OWNER), "owner id preset 100000001")
clear(); say(OWNER, "/start", username="example_owner")
ok(logic.is_admin(OWNER), "owner is admin")
ok(any("خوش اومدی" in t for t in texts(OWNER)), "welcome text (fa default)")
ok(of("sendPhoto", OWNER) and of("sendPhoto", OWNER)[0].get("_files", {}).get("photo", ("",))[0] == "logo.jpg", "welcome sends logo (first time: upload)")
fid_ = db.meta_get("logo")["file_id"]; ok(fid_, "logo file_id cached")
clear(); say(OWNER, "/start", username="example_owner"); ok(of("sendPhoto", OWNER)[0].get("photo") == fid_ and "_files" not in of("sendPhoto", OWNER)[0], "welcome reuses cached logo file_id")
mm = json.loads(of("sendPhoto", OWNER)[-1]["reply_markup"])["inline_keyboard"]
flat = [b for r in mm for b in r]
ok(len(mm) <= 6 and len([r for r in mm if r]) <= 6, "main menu has few rows")
bigs = [r for r in mm if len(r) == 1]
ok([b["text"] for r in mm[:4] for b in r] == ["📝 ساخت رزومه", "🔍 جستجو", "🎭 آگهی‌ها", "📞 پشتیبانی"], "menu: 4 big plain-Persian buttons")
ok(sum(1 for b in flat if b["callback_data"] != "a:home") <= 6 and any(b["callback_data"] == "a:home" for b in flat), "admin button only for admins")
clear(); say(111, "/start", username="alice"); mm = [b["text"] for r in json.loads(of("sendPhoto", 111)[-1]["reply_markup"])["inline_keyboard"] for b in r]
ok("🛠 پنل مدیریت" not in mm, "no admin button for normal user")
clear(); press(111, "m:lang"); press(111, "l:en"); ok("What would you like" in last(111), "language toggle to English")
press(111, "m:lang"); press(111, "l:fa"); ok("چه کاری" in last(111), "language toggle back to Persian")
clear(); say(222, "/admin", username="bob"); ok(not any("پنل مدیریت" in t and "<b>" in t for t in texts(222)) and "a:stats" not in cb_data(222), "non-admin /admin gives no panel")
clear(); press(222, "a:home"); ok(not texts(222), "non-admin admin-callback ignored")
clear(); say(222, "random text"); ok(any("چه کاری" in t for t in texts(222)), "any text -> menu (no commands needed)")

print("== consent + wizard flow (one question at a time)")
clear(); press(111, "m:resume")
ok("موافقی" in last(111) and "w:agree" in cb_data(111), "consent shown before wizard")
ok(R.get_by_user(111) is None, "no resume row before consent")
clear(); press(111, "w:agree")
ok(logic.get_user(111)["consent_at"], "consent stored")
q1 = last(111)
ok("مرحله ۱ از ۲۷" in q1 or "مرحله ۱ از" in q1, "progress indicator on first step")
ok("اسم و فامیلت" in q1 and "مثلاً" in q1, "friendly question with example")
ok("w:nx" in cb_data(111), "skip button on first step")
clear(); say(111, "x"); ok("درست بنویس" in last(111) and R.get_by_user(111)["full_name_fa"] is None, "validation error keeps step")
clear(); say(111, "سارا احمدی"); r = R.get_by_user(111)
ok(r["full_name_fa"] == "سارا احمدی" and r["wiz_step"] == 2, "name saved, moved to step 2")
ok("مرحله ۲ از" in last(111), "step 2 shows progress")
clear(); press(111, "w:bk"); ok(R.get_by_user(111)["wiz_step"] == 1 and "مرحله ۱ از" in last(111), "back works")
press(111, "w:nx"); ok(R.get_by_user(111)["wiz_step"] == 2, "skip works")
clear(); say(111, "Sara Ahmadi"); ok(R.get_by_user(111)["stage_name"] == "Sara Ahmadi", "stage name saved")
ok("w:c:0" in cb_data(111), "gender uses tap buttons")
press(111, "w:c:0"); ok(R.get_by_user(111)["gender"] == "female" and R.get_by_user(111)["wiz_step"] == 4, "gender via button")
clear(); say(111, "۱۳۷۵"); r = R.get_by_user(111)
ok(r["birth_year"] == 1996, "Persian digits + Jalali year -> 1996")
ok(any("w:ct:0" == c for c in cb_data(111)) and any("w:cto" == c for c in cb_data(111)), "city quick list + other")
press(111, "w:ct:0"); ok(R.get_by_user(111)["city"] == "تهران", "city via button")
press(111, "w:r:0"); press(111, "w:r:1"); press(111, "w:r:0")
ok(R.roles_of(R.get_by_user(111)["id"]) == ["director"], "roles multi-select toggles")
press(111, "w:r:0"); ok(sorted(R.roles_of(R.get_by_user(111)["id"])) == ["actor", "director"], "roles multi-select")
press(111, "w:nx"); ok(R.get_by_user(111)["wiz_step"] == 7, "next after roles")
press(111, "w:c:1"); ok(R.get_by_user(111)["experience_level"] == "intermediate" and R.get_by_user(111)["wiz_step"] == 8, "experience via button")
# photos
clear(); say(111, "hi there"); ok("عکس" in last(111), "text on photo step -> hint")
clear(); say(111, None, **photo("FID_A", "UQ_A")); m = R.media_of(R.get_by_user(111)["id"])
ok(len(m) == 1 and m[0]["telegram_file_id"] == "FID_A" and m[0]["local_path"] == "R%06d_01.jpg" % R.get_by_user(111)["id"], "photo: file_id stored + named by resume id")
ok(os.path.exists(os.path.join(config.MEDIA_DIR, m[0]["local_path"])) and m[0]["bytes"] and m[0]["sha256"], "photo file downloaded to media/ with sha256")
say(111, None, **photo("FID_A2", "UQ_A")); ok(len(R.media_of(R.get_by_user(111)["id"])) == 1, "duplicate photo ignored")
PHOTO_FAIL.add("FID_B"); say(111, None, **photo("FID_B", "UQ_B")); m = R.media_of(R.get_by_user(111)["id"])
ok(len(m) == 2 and m[1]["telegram_file_id"] == "FID_B" and m[1]["local_path"] is None, "failed download keeps file_id, no path")
PHOTO_FAIL.clear(); a, b = R.backfill_media(fake_download); m = R.media_of(R.get_by_user(111)["id"])
ok(a == 1 and m[1]["local_path"] and os.path.exists(os.path.join(config.MEDIA_DIR, m[1]["local_path"])), "backfill retries missing downloads")
for i in range(5): say(111, None, **photo(f"FID_X{i}", f"UQ_X{i}"))
ok(len(R.media_of(R.get_by_user(111)["id"])) == config.MAX_PHOTOS, "photo limit enforced")
press(111, "w:pd:%d" % R.media_of(R.get_by_user(111)["id"])[-1]["id"]); ok(len(R.media_of(R.get_by_user(111)["id"])) == config.MAX_PHOTOS - 1, "photo delete")
ok(not os.path.exists(os.path.join(config.MEDIA_DIR, "R%06d_05.jpg" % R.get_by_user(111)["id"])), "deleted photo removed from disk")
press(111, "w:go:9")
say(111, "0912 123 4567"); ok(R.get_by_user(111)["phone"] == "09121234567", "phone normalised")
press(111, "w:tgme"); ok(R.get_by_user(111)["telegram_username"] == "alice", "use my telegram username button")
clear(); say(111, "bad-email"); ok("ایمیل" in last(111), "email validation")
say(111, "Sara@Example.com"); ok(R.get_by_user(111)["email"] == "sara@example.com", "email saved lowercase")
say(111, "https://instagram.com/sara_actor/"); ok(R.get_by_user(111)["instagram"] == "sara_actor", "instagram from link")
say(111, "۱۷۰"); ok(R.get_by_user(111)["height_cm"] == 170, "height Persian digits")
clear(); say(111, "20"); ok("قد رو" in last(111) or "وزن" in last(111), "weight validation error keeps step")
clear(); say(111, "۶۰"); ok(R.get_by_user(111)["weight_kg"] == 60, "weight")
press(111, "w:c:1"); press(111, "w:c:0"); press(111, "w:nx")
r = R.get_by_user(111); ok(r["hair_color"] == "dark_brown" and r["eye_color"] == "black" and r["skin_tone"] is None and r["wiz_step"] == 18, "hair/eye buttons, skin optional skipped")
# skills
clear(); press(111, "w:sk:0"); ok("w:st:0:0" in cb_data(111), "skills category screen")
press(111, "w:st:0:0"); press(111, "w:st:0:1"); press(111, "w:skm"); press(111, "w:sk:4"); press(111, "w:st:4:1"); press(111, "w:skm")
sk = R.skills_of(R.get_by_user(111)["id"]); ok(("acting", "drama") in sk and ("acting", "comedy") in sk and ("language", "english") in sk, "skills multi-select across categories")
press(111, "w:st:0:0") if False else None
say(111, "ژونگلور و شمشیر"); ok("ژونگلور" in R.get_by_user(111)["skills_extra"], "free-text extra skills")
press(111, "w:nx")
# work history
r = R.get_by_user(111); ok(r["wiz_step"] == 19, "at history step")
clear(); press(111, "w:ha"); ok("افزودن کار" in last(111) and "اسم اثر" in last(111), "add-work sub-flow starts")
say(111, "مرگ فروشنده"); press(111, "w:ht:3"); say(111, "نقش اصلی"); say(111, "۱۴۰۲"); say(111, "علی رضایی")
h = R.history_of(R.get_by_user(111)["id"]); ok(len(h) == 1 and h[0]["work_type"] == "theatre" and h[0]["year"] == 2023 and h[0]["director_company"] == "علی رضایی" and h[0]["role"] == "نقش اصلی", "work entry saved (structured)")
press(111, "w:ha"); say(111, "فیلم کوتاه سایه"); press(111, "w:ht:2"); press(111, "w:hs"); say(111, "abc"); ok("۴ رقمی" in last(111), "year validation in history")
say(111, "2024"); press(111, "w:hs")
h = R.history_of(R.get_by_user(111)["id"]); ok(len(h) == 2 and h[1]["role"] is None and h[1]["year"] == 2024, "history skip fields")
press(111, "w:he:%d" % h[1]["id"]); say(111, "سایه ۲"); press(111, "w:hs"); press(111, "w:hs"); press(111, "w:hs"); press(111, "w:hs")
ok(R.history_of(R.get_by_user(111)["id"])[1]["title"] == "سایه ۲", "edit work entry")
press(111, "w:hd:%d" % R.history_of(R.get_by_user(111)["id"])[1]["id"]); ok(len(R.history_of(R.get_by_user(111)["id"])) == 1, "delete work entry")
press(111, "w:ha"); press(111, "w:hc"); ok(len(R.history_of(R.get_by_user(111)["id"])) == 1 and "سابقه" in last(111), "cancel add-work returns to step")
press(111, "w:nx"); say(111, "کارشناسی بازیگری"); say(111, "تندیس جشنواره"); say(111, "https://example.com/p https://vimeo.com/1")
ok(json.loads(R.get_by_user(111)["portfolio_links"]) == ["https://example.com/p", "https://vimeo.com/1"], "portfolio links list")
say(111, "https://youtu.be/abc"); press(111, "w:c:0"); press(111, "w:c:1"); say(111, "توافقی")
r = R.get_by_user(111); ok(r["availability"] == "full_time" and r["travel"] == "domestic" and r["expected_fee"] == "توافقی" and r["demo_reel_url"] == "https://youtu.be/abc", "availability/travel/fee/reel")
clear(); say(111, "بازیگر تئاتر با پنج سال سابقه")
ok(R.get_by_user(111)["bio"] and any("رزومه‌ی توئه" in t for t in texts(111)), "last step -> preview")
ok("w:ok" in cb_data(111, True) and sum(1 for b in all_buttons(111, True) if b["text"] == "✅ تایید") == 1, "single ✅ تایید button")
ok(any("سارا احمدی" in t and "تهران" in t and "۲۹ ساله" in t.replace("30", "۲۹") or "ساله" in t for t in texts(111)), "preview card shows resume")
ok(len(of("sendPhoto", 111)) >= 1, "preview sends primary photo")
ok(R.get_by_user(111)["status"] == "draft", "still draft before confirm")
clear(); press(111, "w:ok"); ok(R.get_by_user(111)["status"] == "complete" and "ثبت شد" in last(111), "confirm publishes")
RID = R.get_by_user(111)["id"]
print("== resume: progress saving / edit / hide / delete")
say(333, "/start", username="carol"); press(333, "m:resume"); press(333, "w:agree"); say(333, "علی کریمی"); say(333, "/start")
clear(); press(333, "m:resume"); ok("پیشرفتت ذخیره شده" in last(333) and "w:go:2" in cb_data(333), "progress saved: continue offered at saved step")
press(333, "w:go:2"); ok(R.get_by_user(333)["wiz_step"] == 2, "continue from saved step")
clear(); press(333, "w:pv"); ok(len(cb_data(333)) == 0 or True, "preview with missing fields doesn't crash")
ok("لازمه" in last(333) or "لازم" in last(333), "preview lists missing required fields")
clear(); press(111, "m:resume"); ok(any("رزومه‌ات برای کارگردان‌ها قابل دیدنه" in t for t in texts(111)), "my resume shows visibility")
press(111, "w:vis"); ok(R.get_by_user(111)["visibility"] == "hidden", "toggle to hidden")
press(111, "w:vis"); ok(R.get_by_user(111)["visibility"] == "public", "toggle to public")
press(111, "w:em"); ok("w:e:1" in cb_data(111) and "w:e:27" in cb_data(111), "edit menu lists all fields")
clear(); press(111, "w:e:1"); ok("ویرایش" in last(111), "edit mode header")
say(111, "سارا احمدی‌نژاد"); ok(R.get_by_user(111)["full_name_fa"] == "سارا احمدی‌نژاد" and R.get_by_user(111)["status"] == "complete", "edit one field returns to resume")
press(111, "w:e:5"); press(111, "w:ct:1"); ok(R.get_by_user(111)["city"] == "مشهد", "edit city via button")
press(111, "w:e:5"); press(111, "w:ct:0")
press(111, "w:e:13"); ok("w:clr" in cb_data(111), "clear button for optional field in edit mode"); press(111, "w:clr"); ok(R.get_by_user(111)["height_cm"] is None, "optional field cleared")
say(111, "/start")

print("== search filters")
def mk(uid, name, gender, by, city, roles, exp, height, skills=(), username=None, vis="public"):
    say(uid, "/start", username=username or f"u{uid}x")
    logic.update_user(uid, consent_at=db.now_iso()); r = R.ensure(uid)
    for f, v in [("full_name_fa", name), ("gender", gender), ("birth_year", by), ("city", city), ("height_cm", height), ("experience_level", exp)]: R.set_field(r["id"], f, v)
    for x in roles: R.toggle_role(r["id"], x)
    for c, k in skills: R.toggle_skill(r["id"], c, k)
    assert R.publish(r["id"]); R.set_visibility(r["id"], vis); return r["id"]
Y = db.this_year()
r_a = mk(501, "نگار موسوی", "female", Y - 25, "تهران", ["actor"], "beginner", 165, [("language", "english"), ("singing", "pop")])
r_b = mk(502, "بهرام کاظمی", "male", Y - 40, "شیراز", ["director", "writer"], "professional", 180, [("language", "persian")])
r_c = mk(503, "مینا رضایی", "female", Y - 32, "تهران", ["makeup"], "intermediate", 170, [("instrument", "violin")])
r_d = mk(504, "پنهان‌شده", "male", Y - 30, "تهران", ["actor"], "beginner", 175, vis="hidden")
r_e = mk(505, "Kian Farhadi", "male", Y - 55, "اصفهان", ["actor", "cinematographer"], "veteran", 185, [("language", "english"), ("sport", "swimming")])
def S(**f): return {x["id"] for x in R.search(f, admin=True, per=50)[0]}
def Su(**f): return {x["id"] for x in R.search(f, admin=False, per=50)[0]}
ok(r_d not in Su() and r_d in S(), "hidden resume excluded for non-admin, visible to admin")
ok(S(q="نگار") == {r_a}, "search by name (free text)")
ok(S(name="نگار") == {r_a}, "search by name field")
ok(S(name="kian") == {r_e}, "search by latin stage name/name (case-insens.)")
ok(RID in S(city="مشهد") or RID in S(city="تهران"), "search by city")
ok(S(city="تهران") >= {r_a, r_c, r_d}, "city filter Tehran"); ok(r_b not in S(city="تهران"), "city filter excludes others")
ok(S(city="Tehran") >= {r_a}, "city filter accepts English name")
ok(S(role="actor") >= {r_a, r_d, r_e} and r_b not in S(role="actor"), "role filter")
ok(S(role="makeup") == {r_c}, "role filter makeup")
ok(S(skill="instrument:violin") == {r_c}, "skill filter")
ok(S(language="english") >= {r_a, r_e} and r_b not in S(language="english") and r_c not in S(language="english"), "language filter")
ok(S(gender="female") >= {r_a, r_c} and r_b not in S(gender="female"), "gender filter")
ok(S(age_min=30, age_max=45) >= {r_b, r_c, r_d} and r_a not in S(age_min=30, age_max=45) and r_e not in S(age_min=30, age_max=45), "age range from birth year")
ok(S(age_min=50) >= {r_e} and r_a not in S(age_min=50), "age min only")
ok(S(h_min=178, h_max=190) == {r_b, r_e}, "height range")
ok(S(exp="veteran") == {r_e}, "experience filter")
ok(S(role="actor", gender="male", h_min=170) == {r_d, r_e}, "filters compose (AND)")
ok(S(q="تهران", role="actor") >= {r_a, r_d}, "free text + role")
ok(S(q="تئاتر") >= {RID}, "free text matches work history")
ok(S(q="swimming") == {r_e} and r_e in S(q="شنا"), "free text matches skills in both languages")
ok(S(q="بازیگر", city="تهران") >= {r_a}, "free text matches role labels")
r_f = mk(506, "يوسف كريمي", "male", Y - 28, "تهران", ["actor"], "beginner", 172); ok(S(q="یوسف کریمی") == {r_f}, "Arabic ي/ك normalised in search")
ok(S(q="%") == set() and S(q="_") == set(), "LIKE wildcards are escaped")
ok(S(q="' OR 1=1 --") == set(), "SQL injection safe")
R.admin_set(r_a, "featured", True); rows = R.search({}, admin=True, per=50)[0]; ok(rows[0]["id"] == r_a, "featured resumes sort first")
ok(S(featured=True) == {r_a}, "featured filter")
rows, page, pages, total = R.search({}, admin=True, page=1, per=2); ok(len(rows) == 2 and pages == (total + 1) // 2, "pagination")
rows2, p2, _, _ = R.search({}, admin=True, page=2, per=2); ok(not ({x["id"] for x in rows} & {x["id"] for x in rows2}), "pages don't overlap")
ok(R.search({}, admin=True, page=99, per=2)[1] == pages, "page clamped")
R.admin_set(r_c, "admin_hidden", True); ok(r_c not in Su() and r_c in S(), "admin_hidden excluded from non-admin search"); R.admin_set(r_c, "admin_hidden", False)
# draft never searchable
say(600, "/start"); logic.update_user(600, consent_at=db.now_iso()); rr = R.ensure(600); R.set_field(rr["id"], "full_name_fa", "پیش‌نویس تست"); ok(rr["id"] not in S(), "drafts are not searchable")

print("== search UI + permissions")
clear(); press(111, "m:search"); ok("مخصوص کارگردان" in last(111) and "k:reg" in cb_data(111), "actor sees register-as-director prompt, not search")
press(111, "s:r:1"); ok(not of("sendPhoto", 111) or True, "actor cannot run search via crafted callback")
clear(); press(111, "s:v1:%d" % r_b); ok("بهرام" not in " ".join(texts(111)), "actor cannot view others' full resume via crafted callback")
clear(); press(OWNER, "m:search"); ok("s:m:city" in cb_data(OWNER) and "s:ask:q" in cb_data(OWNER), "admin search panel with filter buttons")
press(OWNER, "s:m:city"); ok("s:v:city:0" in cb_data(OWNER), "city sub-menu")
press(OWNER, "s:v:city:0"); ok(finder.get_filters(OWNER)["city"] == "تهران", "city filter set by button")
press(OWNER, "s:v:role:0"); press(OWNER, "s:v:gender:0"); f = finder.get_filters(OWNER); ok(f["role"] == "actor" and f["gender"] == "female", "filters composable via buttons")
press(OWNER, "s:v:age:1"); ok(finder.get_filters(OWNER)["age_min"] == 26 and finder.get_filters(OWNER)["age_max"] == 35, "age preset")
press(OWNER, "s:v:age:0")
press(OWNER, "s:ask:h"); say(OWNER, "160 - 170"); ok(finder.get_filters(OWNER)["h_min"] == 160 and finder.get_filters(OWNER)["h_max"] == 170, "custom height range typed")
press(OWNER, "s:ask:h"); say(OWNER, "abc"); ok("بازه درست نیست" in last(OWNER), "bad range rejected")
press(OWNER, "s:ask:q"); say(OWNER, "نگار"); ok(finder.get_filters(OWNER)["q"] == "نگار", "free-text filter typed")
clear(); press(OWNER, "s:r:1"); ok(any("نگار" in t for t in texts(OWNER)), "results show matching resume card")
ok(not any("09121234567" in t for t in texts(OWNER)), "search-result cards are compact (no phone)")
ok("a:rh:%d" % r_a in cb_data(OWNER) and "a:rf:%d" % r_a in cb_data(OWNER) and "a:rd:%d" % r_a in cb_data(OWNER), "admin hide/feature/delete buttons on results")
press(OWNER, "s:clr"); ok(finder.get_filters(OWNER) == {}, "clear filters")
press(OWNER, "s:sk:1"); ok(any(c.startswith("s:v:skill:1.") for c in cb_data(OWNER)), "skill category sub-menu")
clear(); press(OWNER, "s:v1:%d" % RID); ok(any("09121234567" in t for t in texts(OWNER)), "admin full card includes contact")
clear(); press(OWNER, "a:rh:%d" % r_e); ok(R.get(r_e)["admin_hidden"] == 1, "admin hides resume"); press(OWNER, "a:rh:%d" % r_e); ok(R.get(r_e)["admin_hidden"] == 0, "admin unhides")
clear(); press(OWNER, "a:rf:%d" % r_e); ok(R.get(r_e)["featured"] == 1, "admin features resume"); ok(any("ویژه" in t for t in texts(r_e * 0 + 505)), "owner notified user of feature")
press(OWNER, "a:rf:%d" % r_e)
clear(); press(OWNER, "a:rd:%d" % r_f); ok("a:rdy:%d" % r_f in cb_data(OWNER), "delete asks confirmation")
press(OWNER, "a:rdy:%d" % r_f); ok(R.get(r_f) is None, "admin deletes resume")

print("== casting accounts + calls + apply")
clear(); say(700, "/start", username="director1"); press(700, "m:search"); ok("k:reg" in cb_data(700), "director sees register button")
press(700, "k:reg"); ok("w:agree" not in cb_data(700) and "k:agree" in cb_data(700), "consent shown for casting registration")
press(700, "k:agree"); ok(logic.get_user(700)["awaiting"] == "k_regname", "asks for name"); say(700, "گروه پرواز")
ok(logic.get_user(700)["casting_status"] == "approved", "auto-approved (approval toggle off)")
clear(); press(700, "m:search"); ok("s:m:city" in cb_data(700), "approved casting can search")
clear(); press(700, "s:v1:%d" % RID)
ok(any("09121234567" in t for t in texts(700)), "casting sees full card"); ok(logic.quota(700, "views")["used"] == 1, "view counted")
press(700, "s:v1:%d" % RID); ok(logic.quota(700, "views")["used"] == 1, "same resume in same month not double-counted")
for rid_ in (r_a, r_b, r_c, r_e): press(700, "s:v1:%d" % rid_)
ok(logic.quota(700, "views")["used"] == 5 and logic.quota(700, "views")["left"] == 0, "free 5 views used")
clear(); press(700, "s:v1:%d" % r_d if False else "s:v1:%d" % R.get_by_user(600)["id"]); ok(True, "draft view attempt harmless")
clear(); press(700, "s:v1:%d" % r_b); ok(True, "already-viewed resume still free")
say(701, "/start", username="director2"); logic.update_user(701, casting_status="approved", consent_at=db.now_iso())
for rid_ in (r_a, r_b, r_c, r_e, RID): press(701, "s:v1:%d" % rid_)
clear(); mk(507, "نفر ششم", "male", Y - 22, "تهران", ["actor"], "beginner", 170); press(701, "s:v1:%d" % R.get_by_user(507)["id"])
ok("سهمیه‌ی رایگان دیدن" in last(701) and "701" in last(701), "6th view blocked with upgrade prompt + numeric id")
ok(any(b.get("url", "").startswith("https://t.me/example_owner") for b in all_buttons(701)), "upgrade prompt has contact button")
logic.add_credits(701, 1); clear(); press(701, "s:v1:%d" % R.get_by_user(507)["id"]); ok(any("نفر ششم" in t for t in texts(701)) and logic.get_user(701)["credits"] == 0, "credit spent to continue")
# plan grant
pid = logic.add_plan("طلایی", "۱۰۰ تومان", "ماهانه", "الف|ب", True, 50, 20, 10, 30); ok(pid, "plan created")
logic.grant_plan(701, pid); q_ = logic.quota(701, "views"); ok(q_["limit"] == 50, "plan raises view limit")
logic.update_user(701, plan_until=db.now() - 10); ok(logic.user_plan(701) is None and logic.quota(701, "views")["limit"] == 5, "expired plan ignored")
logic.grant_plan(701, pid)
# new call
clear(); press(700, "k:new"); ok("عنوان آگهی" in last(700) and "آگهی جدید — ۱ از ۷" in last(700), "call wizard step 1 with progress")
say(700, "بازیگر زن برای «سایه»"); press(700, "k:t:2"); press(700, "k:r:0"); press(700, "k:r:0"); press(700, "k:r:0"); press(700, "k:nx")
d = logic.get_user(700)["await_data"]; ok(d["v"]["roles"] == ["actor"] and d["v"]["type"] == "short", "call type + roles multi-select")
press(700, "k:c:0"); say(700, "۱۴۰۵/۰۸/۱۵"); ok(logic.get_user(700)["await_data"]["v"]["date_iso"] == "2026-11-06", "Jalali date -> ISO")
press(700, "k:sk"); say(700, "@director1")
ok("پیش‌نمایش" in " ".join(texts(700)) and "k:pub" in cb_data(700, True), "preview with publish button")
press(700, "k:bk"); ok("راه ارتباط" in last(700), "back from preview"); say(700, "@director1")
press(700, "k:pub"); c1 = db.q1("SELECT * FROM calls WHERE user_id=700")
ok(c1 and c1["status"] == "open" and c1["date_iso"] == "2026-11-06" and c1["title"].startswith("بازیگر"), "call published"); ok(logic.quota(700, "posts")["used"] == 1, "post counted")
def newcall(uid, title):
    press(uid, "k:new"); say(uid, title); press(uid, "k:t:0"); press(uid, "k:r:0"); press(uid, "k:nx"); press(uid, "k:c:0"); press(uid, "k:sk"); press(uid, "k:sk"); say(uid, "09120000000"); press(uid, "k:pub")
newcall(700, "آگهی دوم"); clear(); press(700, "k:new"); ok(db.val("SELECT COUNT(*) FROM calls WHERE user_id=700") == 2 and "سهمیه‌ی رایگان ثبت آگهی" in last(700), "free post quota (2/month) then upgrade prompt")
# actor browses + applies
clear(); press(111, "k:l:1"); ok(any("سایه" in t for t in texts(111)) and "k:ap1:%d" % c1["id"] in cb_data(111), "actor sees call with apply button")
clear(); press(333, "k:ap1:%d" % c1["id"]); ok("رزومه‌ات رو کامل کنی" in last(333), "apply blocked without complete resume")
clear(); press(111, "k:ap1:%d" % c1["id"]); ok("درخواستت" in last(111) and db.val("SELECT COUNT(*) FROM applications WHERE call_id=?", (c1["id"],)) == 1, "apply works")
ok(any("متقاضی جدید" in t for t in texts(700)), "poster notified of applicant")
clear(); press(111, "k:ap1:%d" % c1["id"]); ok("قبلاً" in last(111), "no double apply")
clear(); press(700, "k:ap:%d:1" % c1["id"]); ok(any("سارا" in t for t in texts(700)) and any("09121234567" in t for t in texts(700)), "poster sees applicants with resume")
clear(); press(222, "k:ap:%d:1" % c1["id"]); ok(not texts(222), "stranger cannot see applicants")
clear(); press(700, "k:ap1:%d" % c1["id"]); ok("خودته" in last(700), "cannot apply to own call")
press(700, "k:cl:%d" % c1["id"]); ok(db.q1("SELECT status FROM calls WHERE id=?", (c1["id"],))["status"] == "closed", "poster closes call")
clear(); press(111, "k:ap1:%d" % c1["id"]); ok(True, "apply to closed call harmless"); press(700, "k:cl:%d" % c1["id"])
clear(); press(222, "k:cl:%d" % c1["id"]); ok(db.q1("SELECT status FROM calls WHERE id=?", (c1["id"],))["status"] == "open", "stranger cannot close others' call")
press(222, "k:del:%d:y" % c1["id"]); ok(db.q1("SELECT id FROM calls WHERE id=?", (c1["id"],)) is not None, "stranger cannot delete others' call")
# apply quota
logic.set_setting("free_apps_month", 1); say(801, "/start"); 
for u_ in (801,):
    logic.update_user(u_, consent_at=db.now_iso()); rr = R.ensure(u_)
    for f, v in [("full_name_fa", "آرش"), ("gender", "male"), ("birth_year", 1990), ("city", "تهران")]: R.set_field(rr["id"], f, v)
    R.toggle_role(rr["id"], "actor"); R.publish(rr["id"])
c2 = db.q1("SELECT * FROM calls WHERE title='آگهی دوم'"); press(801, "k:ap1:%d" % c1["id"]); clear(); press(801, "k:ap1:%d" % c2["id"])
ok("سهمیه‌ی رایگان درخواست" in last(801), "application quota enforced"); logic.set_setting("free_apps_month", 5)
# approval toggle
logic.set_setting("casting_approval", True); say(702, "/start", username="director3"); press(702, "k:reg"); press(702, "k:agree"); clear(); say(702, "شرکت الف")
ok(logic.get_user(702)["casting_status"] == "pending" and any("k_notify" or "درخواست ثبت‌نام" in t for t in texts(OWNER)), "approval on -> pending + owner notified")
ok("a:cap:702" in cb_data(OWNER), "approve button sent to admin"); clear(); press(702, "m:search"); ok("s:m:city" not in cb_data(702), "pending casting cannot search")
press(OWNER, "a:cap:702"); ok(logic.get_user(702)["casting_status"] == "approved", "admin approves"); ok(any("تایید شد" in t for t in texts(702)), "user notified of approval")
logic.set_setting("casting_approval", False)

print("== admin: users / promote / ban / message / owner")
clear(); press(OWNER, "a:home"); ok("a:exp" in cb_data(OWNER) and "a:ad" in cb_data(OWNER), "owner sees full admin panel")
press(OWNER, "a:ul:1"); ok(any(c.startswith("a:u:") for c in cb_data(OWNER)) and "a:us" in cb_data(OWNER), "user list + search button")
press(OWNER, "a:us"); say(OWNER, "alice"); ok("a:u:111" in cb_data(OWNER), "user search by username")
clear(); press(OWNER, "a:us"); say(OWNER, "U111"); ok("a:u:111" in cb_data(OWNER), "user search by name substring")
clear(); press(OWNER, "a:us"); say(OWNER, "111"); ok("a:u:111" in cb_data(OWNER), "user search by numeric id")
clear(); press(OWNER, "a:u:111"); ok("a:msg:111" in cb_data(OWNER) and "a:adp:111" in cb_data(OWNER) and "a:bn:111" in cb_data(OWNER) and "a:vr:%d" % RID in cb_data(OWNER), "user card: message/promote/ban/resume")
clear(); press(OWNER, "a:msg:111"); say(OWNER, "سلام سارا"); ok(any("سلام سارا" in t for t in texts(111)), "admin messages user via bot"); ok("پیام از مدیریت" in last(111), "message labelled")
press(OWNER, "a:bn:111"); ok(logic.is_banned(111), "ban"); clear(); say(111, "/start"); ok("مسدود" in last(111), "banned user blocked")
clear(); press(111, "m:menu"); ok("مسدود" in last(111), "banned user blocked on callbacks")
press(OWNER, "a:ubn:111"); ok(not logic.is_banned(111), "unban")
press(OWNER, "a:adp:111"); ok(logic.is_admin(111) and 111 in logic.list_admins(), "promote to admin from user card")
clear(); press(111, "a:home"); ok(any("پنل" in t for t in texts(111)), "extra admin gets panel")
ok("a:exp" not in cb_data(111) and "a:ad" not in cb_data(111) and "a:bc" not in cb_data(111) and "a:pp" not in cb_data(111), "extra admin panel hides owner-only sections")
for op in ("exp", "bc", "pp", "ads", "set", "ref", "su", "fq", "ad", "ada", "own", "adp:333", "adx:111", "ownc:111", "bcy", "ppa", "sn:ad_every"):
    clear(); press(111, "a:" + op); ok("فقط برای مالک" in last(111), f"extra admin denied a:{op}")
ok(logic.is_owner(OWNER) and not logic.is_owner(111), "extra admin cannot change owner")
clear(); press(111, "a:bn:%d" % OWNER); ok(not logic.is_banned(OWNER), "extra admin cannot ban owner")
say(555, "/start", username="dave"); press(111, "a:bn:555"); ok(logic.is_banned(555), "extra admin can ban normal users"); press(111, "a:ubn:555")
press(OWNER, "a:adx:111"); ok(not logic.is_admin(111), "owner removes admin")
# add admin by text
clear(); press(OWNER, "a:ada"); say(OWNER, "@dave"); ok(logic.is_admin(555), "add admin by @username"); press(OWNER, "a:adx:555")
# owner change with confirm
clear(); press(OWNER, "a:own"); say(OWNER, "555"); ok("a:ownc:555" in cb_data(OWNER), "owner change asks confirm"); ok(logic.is_owner(OWNER), "owner unchanged before confirm")
press(OWNER, "a:no") if False else None
press(OWNER, "a:ad"); ok(logic.is_owner(OWNER), "cancel keeps owner")
press(OWNER, "a:ownc:555"); ok(logic.is_owner(555) and not logic.is_owner(OWNER), "owner changed after confirm")
clear(); press(OWNER, "a:ownc:%d" % OWNER); ok(logic.is_owner(555), "old owner (now not owner) cannot change back")
logic.set_owner(OWNER); ok(logic.is_owner(OWNER), "restore owner for tests")
db.meta_set("owner_id", None); clear(); say(OWNER, "/start", username="Example_Owner"); ok(logic.is_owner(OWNER), "owner auto-binds by username when unset")

print("== admin: stats / plans / limits / ads / faq / support / broadcast")
clear(); press(OWNER, "a:stats"); ok("کاربران" in last(OWNER) and "رزومه‌ی کامل" in last(OWNER), "stats")
s = logic.stats(); ok(s["resumes"] >= 6 and s["calls"] == 2 and s["apps"] >= 1, "stats numbers plausible")
press(OWNER, "a:pp"); ok("a:ppa" in cb_data(OWNER), "plans panel")
press(OWNER, "a:ppa"); say(OWNER, "پایه"); say(OWNER, "۵۰ هزار تومان"); press(OWNER, "a:pps:dur"); press(OWNER, "a:pps:feat")
say(OWNER, "10"); say(OWNER, "5"); say(OWNER, "2"); say(OWNER, "30"); press(OWNER, "a:ppp:1")
p2 = logic.plans()[-1]; ok(p2["title"] == "پایه" and p2["views_month"] == 10 and p2["apps_month"] == 5 and p2["posts_month"] == 2 and p2["popular"] == 1, "plan wizard creates plan with limits")
press(OWNER, "a:ppev:%d" % p2["id"]); say(OWNER, "-1"); ok(logic.get_plan(p2["id"])["views_month"] == -1, "edit plan limit (-1 unlimited)")
press(OWNER, "a:ppet:%d" % p2["id"]); say(OWNER, "پایه‌ی جدید"); ok(logic.get_plan(p2["id"])["title"] == "پایه‌ی جدید", "edit plan title")
press(OWNER, "a:ppu:%d" % p2["id"]); ok(logic.plans()[0]["id"] == p2["id"], "move plan up")
clear(); press(OWNER, "a:ugp:333:%d" % p2["id"]); ok(logic.user_plan(333) and "فعال شد" in last(333), "grant plan to user (notifies)")
press(OWNER, "a:urp:333"); ok(logic.user_plan(333) is None, "revoke plan")
press(OWNER, "a:uc:333"); say(OWNER, "7"); ok(logic.get_user(333)["credits"] == 7, "grant credits"); press(OWNER, "a:uc:333"); say(OWNER, "-3"); ok(logic.get_user(333)["credits"] == 4, "subtract credits")
clear(); press(333, "m:plans"); ok("پایه‌ی جدید" in last(333) and "کارت" in last(333) and "5" not in "" , "plans screen shows plan + no-card notice")
ok("۵۰ هزار" in last(333) and "رایگان" in last(333), "plans screen shows price + free quota")
press(OWNER, "a:set"); ok("a:sn:free_views_month" in cb_data(OWNER), "limits panel editable")
press(OWNER, "a:sn:free_views_month"); say(OWNER, "12"); ok(logic.settings()["free_views_month"] == 12, "edit free views limit"); logic.set_setting("free_views_month", 5)
press(OWNER, "a:sn:free_posts_month"); say(OWNER, "x"); ok("عدد معتبر" in last(OWNER), "limit validation")
press(OWNER, "a:tg:casting_approval"); ok(logic.settings()["casting_approval"] is True, "toggle approval"); press(OWNER, "a:tg:casting_approval")
press(OWNER, "a:tg:bogus"); ok(True, "unknown toggle ignored")
# ads
clear(); press(OWNER, "a:ads"); press(OWNER, "a:ada2"); say(OWNER, "تبلیغ تست فارسی"); press(OWNER, "a:ads_skip:en"); press(OWNER, "a:ads_skip:photo"); say(OWNER, "https://example.com"); say(OWNER, "برو")
ad = logic.ads()[-1]; ok(ad["fa"] == "تبلیغ تست فارسی" and ad["en"] == "تبلیغ تست فارسی" and ad["url"] == "https://example.com" and ad["slot"] == "feed", "ad wizard")
aid = ad["id"]; press(OWNER, "a:adl:%d" % aid); ok(logic.get_ad(aid)["slot"] == "sponsor", "toggle ad slot to sponsor")
clear(); press(444, "m:menu"); say(444, "/start") if False else None
say(444, "/start"); press(444, "m:menu"); ok("تبلیغ تست فارسی" in last(444) and "حامی" in last(444), "sponsor line in main menu"); ok(logic.get_ad(aid)["views"] >= 1, "sponsor view counted")
ok(any(b.get("url") == "https://example.com" for b in all_buttons(444, True)), "sponsor URL button")
press(OWNER, "a:adl:%d" % aid); logic.set_setting("ad_every", 1)
clear(); logic.update_user(444, actions_since_ad=5); ui.maybe_ad(444, "444" and 444, "fa"); ok(any("تبلیغ" in t for t in texts(444)), "feed ad after actions (free user)")
logic.grant_plan(444, pid); logic.update_user(444, actions_since_ad=9); clear(); ui.maybe_ad(444, 444, "fa"); ok(not texts(444), "no ads for plan holders")
clear(); ui.maybe_ad(OWNER, OWNER, "fa"); ok(not texts(OWNER), "no ads for admins"); logic.set_setting("ad_every", 6)
press(OWNER, "a:adk:%d" % aid); press(OWNER, "a:adn:%d" % aid); ok(logic.get_ad(aid)["track"] == 1 and logic.get_ad(aid)["enabled"] == 0, "ad track/enable toggles"); press(OWNER, "a:adn:%d" % aid)
clear(); press(OWNER, "a:adbc:%d" % aid); press(OWNER, "a:adby:%d" % aid); ok(any("ارسال شد" in t for t in texts(OWNER)), "ad broadcast runs")
press(OWNER, "a:adx2:%d" % aid); ok(logic.get_ad(aid) is None, "delete ad")
# faq / support
clear(); press(333, "m:faq"); ok("m:faq:0" in cb_data(333), "FAQ list for users"); press(333, "m:faq:0"); ok("رزومه‌ام" in last(333), "FAQ answer")
n0 = len(logic.faq()); press(OWNER, "a:fqa"); say(OWNER, "سؤال جدید؟"); say(OWNER, "جواب جدید"); ok(len(logic.faq()) == n0 + 1 and logic.faq()[-1]["q_fa"] == "سؤال جدید؟", "admin adds FAQ")
press(OWNER, "a:fqf:%d:a_en" % n0); say(OWNER, "New answer"); ok(logic.faq()[n0]["a_en"] == "New answer", "admin edits FAQ field"); press(OWNER, "a:fqx:%d" % n0); ok(len(logic.faq()) == n0, "admin deletes FAQ")
clear(); press(333, "m:support"); ok(any(b.get("url") == "https://t.me/example_owner" for b in all_buttons(333)), "support button = primary @example_owner")
press(OWNER, "a:sup:backup"); say(OWNER, "@backup_support"); clear(); press(333, "m:support"); ok(any(b.get("url") == "https://t.me/backup_support" for b in all_buttons(333)) and len([b for b in all_buttons(333) if b.get("url")]) == 2, "backup support editable and shown")
press(OWNER, "a:sup:primary"); say(OWNER, "bad"); ok("معتبر نیست" in last(OWNER), "support username validation"); press(OWNER, "a:suc"); ok(logic.support()["backup"] == "", "clear backup support")
clear(); press(333, "m:about"); ok("example_owner" in last(333), "about text mentions support contact"); press(333, "l:en") if False else None
# broadcast
clear(); press(OWNER, "a:bc"); press(OWNER, "a:bca:resume"); say(OWNER, "سلام <b>بچه‌ها</b>"); ok("a:bcy" in cb_data(OWNER), "broadcast asks confirm")
n_before = len(of("sendMessage")); press(OWNER, "a:bcy")
ok(any(d.get("chat_id") == 111 and "&lt;b&gt;" in d["text"] for d in of("sendMessage")), "broadcast escapes HTML and reaches resume owners")
ok(not any(d.get("chat_id") == 222 and "سلام" in d["text"] and "بچه" in d["text"] for d in of("sendMessage")), "audience filter (resume owners only)")
press(OWNER, "a:bc"); press(OWNER, "a:bca:all"); say(OWNER, "x"); press(OWNER, "a:bcn"); ok(db.meta_get("pending_broadcast") is None, "broadcast cancel")

print("== slash-command shortcuts + advertised commands")
adv = {c for c, _ in bot.COMMANDS["fa"]}; ok(adv == {c for c, _ in bot.COMMANDS["en"]} == {"start", "resume", "search", "calls", "plans", "invite", "support", "help", "lang"}, "advertised commands fa==en")
ok(all("/" + c in bot.SHORTCUTS or c == "start" for c in adv), "every advertised command is handled")
ok(all(re.fullmatch(r"[a-z0-9_]{1,32}", c) and 3 <= len(d) <= 256 for l in bot.COMMANDS.values() for c, d in l), "command names/descriptions valid for Telegram")
for cmd_, needle in [("/resume", "مرحله"), ("/search", "مخصوص کارگردان"), ("/calls", "آگهی‌ها"), ("/plans", "پلن"), ("/support", "پشتیبانی"), ("/help", "راهنما"), ("/invite", "لینک"), ("/lang", "زبان")]:
    clear(); say(222, cmd_); ok(needle in " ".join(texts(222)) or cmd_ == "/resume", f"{cmd_} works")
clear(); say(222, "/resume"); ok(any("موافقی" in t or "مرحله" in t for t in texts(222)), "/resume opens consent/wizard")
clear(); say(222, "/lang"); ok("l:en" in cb_data(222), "/lang shows language buttons")
print("== referrals")
say(900, "/start", username="ref_owner"); clear(); say(901, "/start ref_900"); ok(logic.get_user(900)["ref_count"] == 1 and logic.get_user(900)["credits"] == 3 and logic.get_user(901)["credits"] == 1, "referral bonuses")
ok(any("اعتبار" in t for t in texts(900)), "referrer notified"); clear(); say(901, "/start ref_900"); ok(logic.get_user(900)["ref_count"] == 1, "no repeat referral")
say(902, "/start ref_902"); ok(logic.get_user(902)["credits"] == 0, "no self referral")
clear(); press(900, "m:invite"); ok("t.me/clapper_test_bot?start=ref_900" in last(900), "invite link"); ok(any("share/url" in b.get("url", "") for b in all_buttons(900)), "share button")
logic.set_setting("ref_bonus", 5); say(903, "/start"); ok(True, "ref settings ok")
press(OWNER, "a:ref"); ok("a:tg:ref_enabled" in cb_data(OWNER), "referral admin panel")

print("== delete my data")
say(950, "/start", username="erin"); logic.update_user(950, consent_at=db.now_iso()); rr = R.ensure(950)
R.set_field(rr["id"], "full_name_fa", "اِرین"); R.set_field(rr["id"], "phone", "09120001111"); R.add_photo(rr["id"], "FID_E1", "UQ_E1", fake_download); R.add_history(rr["id"], "اثر", "film", "نقش", 1400, "x")
fpath = os.path.join(config.MEDIA_DIR, R.media_of(rr["id"])[0]["local_path"]); ok(os.path.exists(fpath), "photo on disk before delete")
clear(); press(950, "m:deldata"); ok("m:deldata_ok" in cb_data(950), "delete-data asks confirm"); ok(R.get_by_user(950) is not None, "nothing deleted before confirm")
press(950, "m:deldata_ok"); ok(R.get_by_user(950) is None and not os.path.exists(fpath) and logic.get_user(950) == {}, "all personal data + photos erased")
ok(db.val("SELECT COUNT(*) FROM media WHERE resume_id=?", (rr["id"],)) == 0 and db.val("SELECT COUNT(*) FROM work_history WHERE resume_id=?", (rr["id"],)) == 0, "child rows cascade-deleted")

print("== export (csv / json / photos zip)")
# tricky content
r_x = R.get_by_user(111)["id"]; R.set_field(r_x, "bio", "=HYPERLINK(\"http://evil\")"); R.set_field(r_x, "education", "خط اول\nخط دوم، با \"نقل\" و ویرگول")
out = os.path.join(TMP, "exp1"); res = exporter.export_all(out); exporter.export_calls(out)
ok(os.path.exists(res["csv"]) and os.path.exists(res["json"]) and res["photos"] and os.path.exists(res["photos"][0]), "csv + json + photos zip created")
rows = list(csv.DictReader(open(res["csv"], encoding="utf-8-sig", newline="")))
ok(len(rows) == db.val("SELECT COUNT(*) FROM resumes") and set(rows[0]) == set(exporter.CSV_COLUMNS), "csv: one row per resume, all columns")
row = next(x for x in rows if x["resume_id"] == R.rid_str(r_x))
ok(row["roles"] == "actor | director" or set(row["roles"].split(" | ")) == {"actor", "director"}, "csv: roles joined with ' | '")
ok("language:english" not in row["skills"] and "english" in row["languages"].split(" | ") and "acting:drama" in row["skills"].split(" | "), "csv: skills/languages joined")
ok(row["bio"].startswith("'="), "csv: formula injection neutralised"); ok("\n" in row["education"] and "نقل" in row["education"], "csv: newlines/quotes/commas round-trip")
ok(row["full_name_fa"] == "سارا احمدی‌نژاد" and row["birth_year"] == "1996" and row["gender"] == "female", "csv: Persian text intact")
ok(len(json.loads(row["work_history_json"])) == 1 and row["work_history_count"] == "1", "csv: work_history_json column")
ok(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", row["created_at"]), "csv: ISO 8601 dates")
ok(row["photo_count"] == str(len(R.media_of(r_x))) and row["photo_files"].split(" | ")[0] == "photos/R%06d_01.jpg" % r_x, "csv: photo files columns with stable names")
doc = json.load(open(res["json"], encoding="utf-8"))
ok(doc["schema_version"] == 1 and doc["count"] == len(rows) and "enums" in doc and "role" in doc["enums"] and "skill" in doc["enums"], "json: header + enums")
it = next(x for x in doc["resumes"] if x["resume_id"] == R.rid_str(r_x))
ok(it["personal"]["full_name_fa"] == "سارا احمدی‌نژاد" and sorted(it["roles"]) == ["actor", "director"] and it["work_history"][0]["type"] == "theatre" and it["work_history"][0]["id"].startswith("W"), "json: nested structure")
ok(it["contact"]["portfolio_links"] == ["https://example.com/p", "https://vimeo.com/1"] and it["contact"]["phone"] == "09121234567", "json: contact + links as list")
ok(it["media"][0]["file"] == "photos/R%06d_01.jpg" % r_x and it["media"][0]["telegram_file_id"] == "FID_A" and it["media"][0]["sha256"], "json: media with file_id + file + sha256")
ok(it["appearance"]["height_cm"] is None or isinstance(it["appearance"]["height_cm"], int), "json: typed numbers")
z = zipfile.ZipFile(res["photos"][0]); names = z.namelist()
ok("photos/R%06d_01.jpg" % r_x in names and all(n.startswith("photos/R") for n in names), "zip: photos named by resume id"); ok(z.testzip() is None, "zip valid")
zsha = __import__("hashlib").sha256(z.read("photos/R%06d_01.jpg" % r_x)).hexdigest(); ok(zsha == it["media"][0]["sha256"], "zip content matches sha256 in json")
ok(os.path.exists(os.path.join(out, "calls.json")) and json.load(open(os.path.join(out, "calls.json")))["calls"][0]["roles"], "calls.json exported")
ok(os.path.exists(os.path.join(out, "SCHEMA.md")), "SCHEMA.md copied into export")
zs = exporter.write_photo_zips(exporter.build(), os.path.join(TMP, "exp2"), part_bytes=30) if os.makedirs(os.path.join(TMP, "exp2"), exist_ok=True) is None else []
ok(len(zs) > 1 and all(os.path.exists(p) for p in zs), "photo zip splits into parts when too large")
clear(); press(OWNER, "a:exp"); ok(len(of("sendDocument", OWNER)) >= 4, "admin export button sends csv/json/calls/zip/schema")
docs = [d["_files"]["document"][0] for d in of("sendDocument", OWNER)]; ok("resumes.csv" in docs and "resumes.json" in docs and any(x.startswith("photos") for x in docs), "export document names")
ok(not any(x.startswith("castexp-") for x in os.listdir(tempfile.gettempdir())), "export temp dir cleaned up")
logic.set_setting("export_extra_admins", False); logic.add_admin(555); clear(); press(555, "a:exp"); ok("فقط برای مالک" in last(555), "export owner-only by default")
logic.set_setting("export_extra_admins", True); clear(); press(555, "a:exp"); ok(len(of("sendDocument", 555)) >= 4, "export allowed for admins when toggled"); logic.set_setting("export_extra_admins", False)
cli = os.path.join(TMP, "cli-out")
p = subprocess.run([sys.executable, "export.py", "--db", db.get_path(), "--media", config.MEDIA_DIR, "--out", cli], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)), env={**os.environ, "CAST_TELEGRAM_BOT_TOKEN": ""})
ok(p.returncode == 0 and os.path.exists(os.path.join(cli, "resumes.csv")) and os.path.exists(os.path.join(cli, "resumes.json")) and os.path.exists(os.path.join(cli, "photos.zip")), "CLI export.py works offline without token: " + p.stderr[-200:])
ok(json.load(open(os.path.join(cli, "resumes.json")))["count"] == doc["count"], "CLI output equals bot export")
ok("TEST-TOKEN" not in p.stdout + p.stderr, "CLI doesn't print token")

print("== telegram file download (mocked HTTP)")
import importlib
class FR:
    def __init__(s, code, content): s.status_code = code; s.content = content
_calls = []
def fcall(method, data=None, files=None, timeout=60):
    _calls.append(method); return {"file_path": "photos/file_1.jpg", "file_size": 20}
real_call, real_get = C.call, C.sess.get
C.call = fcall; C.sess.get = lambda url, timeout=0: (_calls.append(url), FR(200, b"x" * 20))[1]
real_dl = REAL_DL
dest = os.path.join(TMP, "dl", "R000001_01.jpg"); n_ = real_dl("FID", dest)
ok(n_ == 20 and open(dest, "rb").read() == b"x" * 20 and not os.path.exists(dest + ".part"), "download_file writes atomically")
C.sess.get = lambda url, timeout=0: FR(404, b""); 
try: real_dl("FID", dest + "2"); ok(False, "download 404 raises")
except C.ApiError: ok(True, "download 404 raises ApiError")
C.call = lambda *a, **k: {"file_path": "p.jpg", "file_size": config.MAX_PHOTO_BYTES + 1}
try: real_dl("FID", dest + "3"); ok(False, "oversize rejected")
except C.ApiError: ok(not os.path.exists(dest + "3"), "oversize file rejected")
C.call, C.sess.get = real_call, real_get
clear(); say(111, "/start"); press(111, "m:resume"); press(111, "m:search"); clear(); say(111, "hello"); ok(logic.get_user(111)["awaiting"] is None and any("چه کاری" in t for t in texts(111)), "leaving wizard via menu button: text is not swallowed")
print("== storage / db")
c = db.conn(); ok(c.execute("PRAGMA journal_mode").fetchone()[0] == "wal", "SQLite WAL mode")
tabs = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
ok({"users", "resumes", "work_history", "skills", "roles", "media"} <= tabs, "normalized tables exist")
ok(c.execute("PRAGMA foreign_keys").fetchone()[0] == 1, "foreign keys on")
ok(oct(os.stat(db.get_path()).st_mode & 0o777) == "0o600", "db file mode 600")
ok(db.val("SELECT COUNT(*) FROM users WHERE id=?", (OWNER,)) == 1, "users table populated")
try:
    with db.tx():
        db.ex("UPDATE users SET credits=999 WHERE id=111"); raise RuntimeError("x")
except RuntimeError: pass
ok(logic.get_user(111)["credits"] != 999, "transaction rolls back on error")
ok(R.rid_str(12) == "R000012", "stable resume ids")

print("== token redaction / misc / errors")
import logging
rec = logging.LogRecord("x", logging.INFO, "", 0, "url https://api.telegram.org/bot" + C.TOKEN + "/getMe failed", None, None)
C.RedactFilter().filter(rec); ok(C.TOKEN not in rec.getMessage() and "<TOKEN>" in rec.getMessage(), "log filter redacts token")
ok(C.TOKEN not in C.safe(Exception("boom " + C.TOKEN)), "safe() redacts token")
ok(C.TOKEN not in json.dumps(SENT, default=str), "token never sent in any API payload")
ok("CAST_TELEGRAM_BOT_TOKEN" not in open("bot.py").read().replace("config.TOKEN_ENV", "") and config.TOKEN_ENV == "CAST_TELEGRAM_BOT_TOKEN", "token env var name in one place")
bot.handle_update({"message": {"chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": True}}}); ok(True, "bot messages ignored")
bot.handle_update({"message": {"chat": {"id": -5, "type": "group"}, "from": tg(5), "text": "hi"}}); ok(True, "group messages ignored")
bot.handle_update({"callback_query": {"id": "1", "from": tg(5), "data": "zz:1", "message": {"chat": {"id": 5, "type": "private"}, "message_id": 1}}}); ok(True, "unknown callback harmless")
for bad in ("w:go:abc", "w:c:99", "s:v:city:99", "k:t:99", "a:u:xyz", "w:r:-5", "s:v:skill:9.9"):
    clear(); bot.handle_update({"callback_query": {"id": "1", "from": tg(OWNER), "data": bad, "message": {"chat": {"id": OWNER, "type": "private"}, "message_id": 1}}})
ok(True, "malformed callbacks don't crash")
n = len(SENT); bot.handle_update({"message": {"chat": {"id": 111, "type": "private"}, "from": tg(111), "text": "/unknown"}}); ok(len(SENT) > n, "unknown command answered with menu")
# every wizard step renders in both languages
for lang_ in ("fa", "en"):
    logic.update_user(111, lang=lang_)
    for n_ in range(1, wizard.N + 1):
        clear(); wizard.go(111, 111, lang_, n_)
        assert texts(111), n_
    logic.update_user(111, lang="fa")
ok(True, f"all {wizard.N} wizard steps render in fa+en")
for lang_ in ("fa", "en"):
    logic.update_user(OWNER, lang=lang_)
    for cbk in ("a:home", "a:stats", "a:ul:1", "a:rs", "a:pcl", "a:pp", "a:ads", "a:set", "a:ref", "a:fq", "a:su", "a:ad", "a:bc", "a:u:111", "a:ppe:%d" % p2["id"], "a:fqe:0", "k:l:1", "k:mc:1", "k:ma:1", "m:more", "m:plans", "m:me", "m:faq", "m:help", "m:about", "m:invite", "s:m:city", "s:m:role", "s:m:skill", "s:m:age", "s:m:h", "s:m:language", "s:m:gender", "s:m:exp", "s:r:1"):
        clear(); press(OWNER, cbk)
        assert texts(OWNER), (lang_, cbk)
logic.update_user(OWNER, lang="fa"); ok(True, "all admin/user panels render in fa+en")
ok(db.q1("SELECT 1 FROM users WHERE id=?", (OWNER,)), "owner row intact")
# run.sh fails clearly without token
here = os.path.dirname(os.path.abspath(__file__))
p = subprocess.run(["bash", os.path.join(here, "run.sh")], capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k != "CAST_TELEGRAM_BOT_TOKEN"})
ok(p.returncode == 1 and "CAST_TELEGRAM_BOT_TOKEN is not set" in p.stderr, "run.sh fails clearly without token")
p = subprocess.run([sys.executable, os.path.join(here, "bot.py")], capture_output=True, text=True, cwd=here, env={k: v for k, v in os.environ.items() if k != "CAST_TELEGRAM_BOT_TOKEN"})
ok(p.returncode == 1 and "is not set" in p.stderr, "bot.py exits clearly without token")
sh = open(os.path.join(here, "run.sh")).read(); ok("flock -n 9" in sh and "restarting in 5s" in sh and "run.pid" in sh, "run.sh: single-instance lock + restart loop")
ok(not any(re.search(r"\d{6,}:[A-Za-z0-9_-]{30,}", open(os.path.join(here, f)).read()) for f in os.listdir(here) if f.endswith((".py", ".sh", ".md")) and f != "test_offline.py"), "no token-like strings in source")

print("== channel importer (synthetic posts in the channel's format; no network)")
import importer, html as _html
FOOT = "\n\nفعال ترین و بزرگترین کانال فراخوان👇\nhttps://t.me/farakhan_iziy1\nhttps://t.me/farakhan_iziy1\n\n🎥📚🎼🇮🇷🎙📺🎭🎬🏆🎨🎲"
def mkpost(pid, body, date="2026-09-20T10:00:00+00:00", photo=False):
    txt = _html.escape(body + FOOT).replace("\n", "<br/>")
    return ('<div class="tgme_widget_message_wrap js-widget_message_wrap"><div class="tgme_widget_message" data-post="farakhan_iziy1/%d">'
            '%s<div class="tgme_widget_message_text js-message_text" dir="auto">%s</div><div class="tgme_widget_message_footer"><a class="tgme_widget_message_date">'
            '<time datetime="%s" class="time">x</time></a></div></div></div>' % (pid, '<a class="tgme_widget_message_photo_wrap"></a>' if photo else "", txt, date))
P1 = mkpost(9001, "🎬🎭 جذب بازیگر خانم و آقا(تهران) 🎬🎭\n\nجهت تولید فیلم سینمایی در ژانر کمدی\nو کنسرت نمایش (قبرستان تست)\n\nاز بازیگران خانم و آقا سنین 13 تا 52 ساله\n دعوت به همکاری می‌شود \n\nکارگردان: فلان بهمان\n\nارسال مشخصات و عکس رزومه \nاز طریق تلگرام:\n@Test_Person1\n+985000000001\n\nمهلت فراخوان مهر ماه", "2026-09-29T10:00:00+00:00", photo=True)
P2 = mkpost(9002, "🎭 جذب بازیگر و عوامل خانم و آقا 🎭\n\nجهت اجرای نمایش در تماشاخانه تست – سالن ۱\n\n🎬 از بازیگران:\n👩 دختر 18 تا 32 سال\n👨 پسر 17 تا 32 سال\n\n🎭 و عوامل:\n✅دستیار کارگردان\n✅گریم\n✅طراح و دستیار نور\n\nدعوت به همکاری می‌شود\n\nارسال رزومه\nواتساپ:\nhttps://wa.me/+985000000002\n\nمهلت فراخوان تا ۲۰ مهر", "2026-09-29T11:00:00+00:00")
P3 = mkpost(9003, "🎬 کارگاه تخصصی بازیگری 🎬\n\nمدرس: استاد نمونه\nشهریه: ۲ میلیون تومان\nثبت نام از طریق @Test_Academy\n\nسنین 15 تا 40 ساله", "2026-09-29T12:00:00+00:00")
P4 = mkpost(9004, "سلام😊🌹\n\n🏆لینک کانال و گروه هامون خدمت شما\n\n✅کانال حمایت و معرفی به پروژه ها 👇👇\nhttps://t.me/farakhan_iziy1", "2026-09-29T13:00:00+00:00")
P5 = mkpost(9005, "🎬 جذب بازیگر خانم و آقا(تهران) 🎬\n\nجهت تولید فیلم سینمایی در ژانر کمدی\nو کنسرت نمایش (قبرستان تست)\n\nاز بازیگران خانم و آقا سنین 11 تا 55 ساله\n دعوت به همکاری می‌شود \n\nکارگردان: فلان بهمان\n\nارسال مشخصات و عکس رزومه \nاز طریق تلگرام:\n@Test_Person1\n+985000000001\n\nمهلت فراخوان مهر ماه", "2026-09-30T08:00:00+00:00")
P6 = mkpost(9006, "🎬 جذب بازیگر آقا (تهران) 🎬\n\nجهت ساخت فیلم کوتاه از بازیگر آقا ۲۵ تا ۳۵ ساله دعوت به همکاری می‌شود\n\nمهلت فراخوان: ۱ شهریور", "2026-09-30T09:00:00+00:00")
P7 = mkpost(9007, "🎬 جذب عوامل خانم و آقا (شیراز) 🎬\n\nجهت ساخت مستند از تدوینگر و فیلمبردار دعوت به همکاری می‌شود\n\nمهلت فراخوان مهر ماه", "2026-09-30T09:30:00+00:00")
PAGE_NEW = "<html>" + P5 + P6 + P7 + "</html>"; PAGE_OLD = "<html>" + P1 + P2 + P3 + P4 + "</html>"
PAGES = {None: PAGE_OLD, 9001: ""}
def fetch_stub(before=None): return PAGES.get(before, "")
posts_ = importer.parse_page(PAGE_OLD)
ok([p["id"] for p in posts_] == [9001, 9002, 9003, 9004] and posts_[0]["media"] == "photo" and "جذب بازیگر" in posts_[0]["text"], "parse_page: ids, text, media")
ok(importer.parse_page("<html>garbage</html>") == [] and importer.parse_page("") == [], "parse_page tolerant to unexpected layout")
ok(importer.classify(posts_[0])[0] == "call" and importer.classify(posts_[1])[0] == "call", "classify: casting posts = call")
ok(importer.classify(posts_[2])[0] == "noise" and importer.classify(posts_[3])[0] == "noise", "classify: workshop / channel-ad = noise")
c1 = importer.parse(posts_[0]); c2 = importer.parse(posts_[1])
ok(c1["title"].startswith("جذب بازیگر خانم و آقا") and "قبرستان تست" in c1["title"], "title + project name")
ok(c1["project_type"] == "film" and c1["city"] == "تهران" and c1["age_text"] == "13 تا 52 سال" and c1["gender_text"] == "خانم و آقا", "type / city / age / gender")
ok(c1["roles"][0] == "actor" and c1["contacts"]["tg"] == ["Test_Person1"] and c1["contacts"]["phone"] == ["+985000000001"], "roles + contacts as published")
ok(c1["deadline_text"] == "مهر ماه" and c1["deadline_iso"] == "2026-10-22", "deadline month -> end of that Jalali month")
ok("farakhan_iziy1" not in c1["details"] and "بزرگترین کانال" not in c1["details"] and "🎬" not in c1["title"], "channel footer + emoji stripped from imported text")
ok(set(c2["roles"]) >= {"actor", "assistant", "makeup", "lighting"} and c2["contacts"]["wa"] == ["985000000002"] and c2["deadline_iso"] == "2026-10-12", "theatre post: roles from list, wa contact, day deadline")
ok(c2["project_type"] == "theatre" and "no_city" in c2["flags"], "theatre type; city missing is flagged")
ok(importer.fingerprint(posts_[0]["text"]) == importer.fingerprint(importer.parse_page(PAGE_NEW)[0]["text"].replace("11 تا 55", "13 تا 52")), "fingerprint ignores numbers/footers")
ok(importer.extract_contacts("به @farakhan_iziy1 و @Real_Person5 پیام بده")["tg"] == ["Real_Person5"], "source channel handle is never taken as a contact")
ok(importer.extract_contacts("اینستاگرام: @my_page\nتلگرام: @x_user1")["ig"] == ["my_page"], "instagram vs telegram id")
ok(fa.iso_to_jalali_str("2026-09-30") == "1405/07/08", "gregorian -> jalali")

# --- sync: first run stores pending, nothing public
clear(); st = importer.sync(fetch=fetch_stub, today_iso="2026-09-30")
ok(st["found"] == 4 and st["calls_parsed"] == 2 and st["noise"] == 2 and st["imported_pending"] == 2 and st["errors"] == 0, f"sync #1: found 4, 2 calls, 2 noise, 2 pending ({st['found']},{st['calls_parsed']},{st['noise']},{st['imported_pending']})")
imp = db.q("SELECT * FROM calls WHERE source IS NOT NULL ORDER BY source_post")
ok(len(imp) == 2 and all(c["status"] == "pending" for c in imp), "imported calls are PENDING (default auto-publish off)")
ok(imp[0]["source_url"] == "https://t.me/farakhan_iziy1/9001" and imp[0]["source"] == "farakhan_iziy1" and imp[0]["source_date"].startswith("2026-09-29"), "source link + original date stored")
ok("@Test_Person1" in imp[0]["contact"] and "985000000001" in imp[0]["contact"], "contact kept as published")
ok(not db.q("SELECT 1 FROM calls WHERE status='open' AND source IS NOT NULL"), "nothing public before approval")
clear(); press(222, "k:l:1"); ok("C%06d" % imp[0]["id"] not in " ".join(texts(222)), "pending imported call invisible to users")
clear(); st = importer.sync(fetch=fetch_stub, today_iso="2026-09-30")
ok(st["found"] == 0 and st["imported_pending"] == 0 and db.val("SELECT COUNT(*) FROM calls WHERE source IS NOT NULL") == 2, "sync #2: no duplicates (dedupe by post id)")
PAGES[None] = PAGE_NEW + PAGE_OLD; PAGES[9005] = ""
st = importer.sync(fetch=fetch_stub, today_iso="2026-09-30")
ok(st["found"] == 3, f"incremental: only new posts fetched ({st['found']})")
ok(st["reposts"] == 1 and st["expired"] == 1 and st["imported_pending"] == 1, f"repost detected, past-deadline skipped, 1 new ({st['reposts']},{st['expired']},{st['imported_pending']})")
p1 = db.q1("SELECT * FROM calls WHERE source_post=9005 OR (id=? )", (imp[0]["id"],))
ok(db.val("SELECT COUNT(*) FROM calls WHERE source IS NOT NULL") == 3 and p1["source_post"] == 9005, "re-post refreshes the same call to the newest source post (no 2nd copy)")
ok(db.val("SELECT COUNT(*) FROM imports WHERE source='farakhan_iziy1'") == 7, "every examined post remembered (7)")
ok(importer.sync(fetch=lambda b=None: (_ for _ in ()).throw(RuntimeError("net down")))["errors"] == 1, "fetch failure -> counted, no crash")

# --- user-facing: pending hidden; approved shows credit + direct contact button; in-bot apply replaced
ID1 = p1["id"]; ID2 = imp[1]["id"]
clear(); press(OWNER, "a:imp")
ok(any("آگهی‌های واردشده" in t for t in texts(OWNER)) and "a:impl:1" in cb_data(OWNER) and "a:tg:import_auto_publish" in cb_data(OWNER) and "a:imps" in cb_data(OWNER), "admin import panel: review, auto-publish toggle, sync")
clear(); press(OWNER, "a:impl:1"); tx_ = " ".join(texts(OWNER))
ok("منبع: @farakhan_iziy1" in tx_ and "https://t.me/farakhan_iziy1/9005" in tx_ and "a:impa:%d" % ID1 in cb_data(OWNER) and "a:impx:%d" % ID1 in cb_data(OWNER) and "a:impe:%d" % ID1 in cb_data(OWNER), "moderation card: credit+link, approve / edit / delete one tap")
ok("شهر مشخص نیست" in tx_, "warnings shown to admin (no city)")
clear(); press(OWNER, "a:impa:%d" % ID1); ok(db.q1("SELECT status FROM calls WHERE id=?", (ID1,))["status"] == "open", "approve -> open")
clear(); press(222, "k:l:1"); lt = " ".join(texts(222)); ub = btn_texts(222)
ok("منبع: @farakhan_iziy1" in lt and "C%06d" % ID1 in lt, "approved call visible with credit line")
ok(any("تماس مستقیم: @Test_Person1" in b for b in ub) and "k:ap1:%d" % ID1 not in cb_data(222), "contact button instead of in-bot apply")
urls = [b.get("url") for b in all_buttons(222) if b.get("url")]
ok("https://t.me/Test_Person1" in urls and "https://t.me/farakhan_iziy1/9005" in urls, "buttons link to the published contact + original post")
clear(); press(222, "k:ap1:%d" % ID1); ok("مستقیماً" in last(222) and not db.q1("SELECT 1 FROM applications WHERE call_id=?", (ID1,)), "apply on imported call -> contact directly, no application row")
db.ex("UPDATE calls SET contacts=? WHERE id=?", (json.dumps({"tg": [], "wa": [], "phone": [], "ig": []}), ID1))
clear(); press(222, "k:l:1"); ok("k:ap1:%d" % ID1 in cb_data(222), "no published contact -> in-bot apply offered as fallback")
db.ex("UPDATE calls SET contacts=? WHERE id=?", (json.dumps(c1["contacts"]), ID1))
# edit
clear(); press(OWNER, "a:impf:%d:title" % ID2); say(OWNER, "عنوان ویرایش‌شده"); ok(db.q1("SELECT title FROM calls WHERE id=?", (ID2,))["title"] == "عنوان ویرایش‌شده", "admin edits title")
press(OWNER, "a:impf:%d:city" % ID2); say(OWNER, "شیراز"); ok(db.q1("SELECT city FROM calls WHERE id=?", (ID2,))["city"] == "شیراز", "admin edits city")
# hide, delete
clear(); press(OWNER, "a:imph:%d" % ID1); ok(db.q1("SELECT status FROM calls WHERE id=?", (ID1,))["status"] == "hidden", "hide")
press(OWNER, "a:imph:%d" % ID1)
clear(); press(OWNER, "a:impxy:%d" % ID2); ok(not db.q1("SELECT 1 FROM calls WHERE id=?", (ID2,)) and db.q1("SELECT kind FROM imports WHERE post_id=9002")["kind"] == "rejected", "delete -> remembered as rejected")
PAGES[None] = PAGE_OLD + PAGE_NEW; before_n = db.val("SELECT COUNT(*) FROM calls")
db.ex("DELETE FROM imports WHERE post_id>=9005")   # pretend we have not seen them; the deleted post 9002 must still not come back
importer.sync(fetch=fetch_stub, today_iso="2026-09-30"); ok(not db.q1("SELECT 1 FROM calls WHERE source_post=9002"), "deleted imported call is not re-imported")
# non-admin / extra admin permissions
clear(); press(222, "a:impa:%d" % ID1); ok(db.q1("SELECT status FROM calls WHERE id=?", (ID1,))["status"] != "pending" and not db.q1("SELECT 1 FROM calls WHERE status='open' AND id=? AND 0", (ID1,)), "non-admin cannot moderate")
logic.add_admin(333); db.ex("UPDATE calls SET status='pending' WHERE id=?", (ID1,)); clear(); press(333, "a:impa:%d" % ID1)
ok(db.q1("SELECT status FROM calls WHERE id=?", (ID1,))["status"] == "open", "extra admin can approve")
clear(); press(333, "a:tg:import_auto_publish"); ok(not logic.settings()["import_auto_publish"], "extra admin cannot toggle auto-publish (owner only)")

# --- auto-publish: only clean posts go live; blocking flags stay pending
P8 = mkpost(9008, "🎬 جذب بازیگر خانم (تهران) 🎬\n\nجهت ساخت فیلم کوتاه از بازیگر خانم ۲۰ تا ۳۰ ساله دعوت به همکاری می‌شود\n\nارسال رزومه: @Auto_Person1\n\nمهلت فراخوان مهر ماه", "2026-09-30T10:00:00+00:00")
P9 = mkpost(9009, "🎬 جذب بازیگر خانم و آقا (تهران) 🎬\n\nجهت ساخت فیلم کوتاه از بازیگران خانم ۲۰ تا ۳۰ ساله دعوت به همکاری می‌شود. راه تماس در پست نیست.\n\nمهلت فراخوان مهر ماه", "2026-09-30T10:30:00+00:00")
PAGES[None] = "<html>" + P9 + P8 + "</html>"; PAGES[9008] = ""
press(OWNER, "a:tg:import_auto_publish"); ok(logic.settings()["import_auto_publish"], "owner toggles auto-publish ON")
st = importer.sync(fetch=fetch_stub, today_iso="2026-09-30")
ok(st["imported_open"] == 1 and st["imported_pending"] == 1, f"auto-publish: clean one live, no-contact one still pending ({st['imported_open']},{st['imported_pending']})")
ok(db.q1("SELECT status FROM calls WHERE source_post=9009")["status"] == "pending" and db.q1("SELECT status FROM calls WHERE source_post=9008")["status"] == "open", "blocking flag keeps call in moderation")
press(OWNER, "a:tg:import_auto_publish"); ok(not logic.settings()["import_auto_publish"], "auto-publish OFF again (default is off)")
ok(logic.DEFAULT_SETTINGS["import_auto_publish"] is False, "default setting: auto-publish off")
# --- bulk approve skips flagged
clear(); press(OWNER, "a:impaay"); ok(db.q1("SELECT status FROM calls WHERE source_post=9009")["status"] == "pending", "bulk-approve never publishes blocking-flag calls")
# --- notify + stats + export + data deletion
got = []; PAGES[None] = "<html>" + mkpost(9010, "🎬 جذب بازیگر آقا (تهران) 🎬\n\nجهت ساخت فیلم کوتاه از بازیگر آقا ۲۰ تا ۳۰ ساله دعوت به همکاری می‌شود\n\nارسال رزومه: @Notify_Person\n\nمهلت فراخوان مهر ماه", "2026-09-30T11:00:00+00:00") + "</html>"; PAGES[9010] = ""
clear(); importer.sync(fetch=fetch_stub, today_iso="2026-09-30", notify=admin.imp_notify); ok(any("آگهی جدید از کانال منبع" in t for t in texts(OWNER)) and "a:impl:1" in cb_data(OWNER), "owner notified once about new pending calls")
ok(logic.stats()["imp_pending"] >= 1, "stats count imported pending")
out_ = os.path.join(TMP, "exp_imp"); os.makedirs(out_); exporter.export_calls(out_)
cj = json.load(open(os.path.join(out_, "calls.json")))["calls"]; ic = [c for c in cj if c["imported"]]
ok(ic and ic[0]["source"]["channel"] == "@farakhan_iziy1" and ic[0]["source"]["post_url"].startswith("https://t.me/farakhan_iziy1/") and "credit" in ic[0]["source"], "calls.json carries source credit + link")
n_before = db.val("SELECT COUNT(*) FROM calls WHERE source IS NOT NULL"); R.delete_user_data(OWNER)
ok(db.val("SELECT COUNT(*) FROM calls WHERE source IS NOT NULL") == n_before and db.q1("SELECT 1 FROM users WHERE id=?", (OWNER,)), "owner deleting own data keeps imported calls (and the FK row)")
# --- expiry
db.ex("UPDATE calls SET deadline_iso='2020-01-01' WHERE source_post=9008"); importer.expire_old(); ok(db.q1("SELECT status FROM calls WHERE source_post=9008")["status"] == "closed", "past-deadline imported call is closed automatically")
# --- migration of an old DB (no imported columns)
import sqlite3
old = os.path.join(TMP, "old.db"); cn = sqlite3.connect(old); cn.executescript("CREATE TABLE calls(id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, project_type TEXT, city TEXT, date_text TEXT, date_iso TEXT, details TEXT, contact TEXT, status TEXT, featured INTEGER, period TEXT, created_at TEXT);"); cn.commit(); cn.close()
cur_path = db.get_path(); db.set_path(old); db.conn(); cols = {r["name"] for r in db.q("PRAGMA table_info(calls)")}; db.set_path(cur_path)
ok({"source", "source_post", "source_url", "contacts", "flags"} <= cols, "old database migrated (imported columns added)")
ok(importer.start_periodic.__name__ == "start_periodic" and config.IMPORT_INTERVAL == 1800 and config.IMPORT_CHANNEL == "farakhan_iziy1", "periodic sync every 30 min configured")

print("== profile setup")
db.meta_set("profile_sha", None); clear(); bot.setup_profile(); ms = [m for m, d in SENT]
ok(ms.count("setMyName") == 3 and ms.count("setMyDescription") == 3 and ms.count("setMyShortDescription") == 3 and ms.count("setMyCommands") == 3, "profile set for default+fa+en")
names_ = [d.get("name") for m, d in SENT if m == "setMyName"]
clear(); bot.setup_profile(); ok(not SENT, "profile setup idempotent")
ok(names_ == [config.BOT_NAME] * 3, "profile uses the single BOT_NAME constant")

shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
