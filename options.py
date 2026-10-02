"""Enumerations with stable machine codes + fa/en labels. The codes are what the DB and the exports store."""

def _o(*items):
    return [(c, fa, en) for c, fa, en in items]

GENDER = _o(("female", "👩 زن", "👩 Female"), ("male", "👨 مرد", "👨 Male"), ("other", "🧑 سایر", "🧑 Other"))
HAIR = _o(("black", "مشکی", "Black"), ("dark_brown", "قهوه‌ای تیره", "Dark brown"), ("brown", "قهوه‌ای", "Brown"),
          ("light_brown", "قهوه‌ای روشن", "Light brown"), ("blonde", "بلوند", "Blonde"), ("red", "قرمز/حنایی", "Red"),
          ("gray", "خاکستری", "Gray"), ("white", "سفید", "White"), ("dyed", "رنگ‌شده", "Dyed"),
          ("bald", "بدون مو", "Bald"), ("other", "سایر", "Other"))
EYES = _o(("black", "مشکی", "Black"), ("dark_brown", "قهوه‌ای تیره", "Dark brown"), ("brown", "قهوه‌ای", "Brown"),
          ("hazel", "عسلی", "Hazel"), ("green", "سبز", "Green"), ("blue", "آبی", "Blue"), ("gray", "طوسی", "Gray"),
          ("other", "سایر", "Other"))
SKIN = _o(("very_fair", "خیلی روشن", "Very fair"), ("fair", "روشن", "Fair"), ("olive", "زیتونی", "Olive"),
          ("wheat", "گندمی", "Wheat"), ("tan", "برنزه", "Tan"), ("brown", "تیره", "Brown"), ("dark", "خیلی تیره", "Dark"))
ROLES = _o(("actor", "🎭 بازیگر", "🎭 Actor"), ("director", "🎬 کارگردان", "🎬 Director"),
           ("cinematographer", "🎥 فیلم‌بردار", "🎥 Cinematographer"), ("editor", "✂️ تدوین‌گر", "✂️ Editor"),
           ("sound", "🎧 صدابردار/صداگذار", "🎧 Sound"), ("makeup", "💄 گریمور", "💄 Makeup"),
           ("costume", "👗 طراح لباس", "👗 Costume"), ("set_design", "🏛 طراح صحنه", "🏛 Set design"),
           ("lighting", "💡 نورپرداز", "💡 Lighting"), ("writer", "✍️ نویسنده", "✍️ Writer"),
           ("producer", "💼 تهیه‌کننده", "💼 Producer"), ("assistant", "🤝 دستیار", "🤝 Assistant"),
           ("other", "✨ سایر", "✨ Other"))
EXPERIENCE = _o(("beginner", "🌱 مبتدی", "🌱 Beginner"), ("intermediate", "🌿 نیمه‌حرفه‌ای", "🌿 Intermediate"),
                ("professional", "🌳 حرفه‌ای", "🌳 Professional"), ("veteran", "🏆 پیش‌کسوت", "🏆 Veteran"))
WORK_TYPES = _o(("film", "🎞 فیلم سینمایی", "🎞 Feature film"), ("series", "📺 سریال", "📺 Series"),
                ("short", "🎬 فیلم کوتاه", "🎬 Short film"), ("theatre", "🎭 تئاتر", "🎭 Theatre"),
                ("commercial", "📢 تبلیغاتی", "📢 Commercial"), ("music_video", "🎵 موزیک‌ویدیو", "🎵 Music video"),
                ("documentary", "📹 مستند", "📹 Documentary"), ("other", "✨ سایر", "✨ Other"))
AVAILABILITY = _o(("full_time", "⏱ تمام‌وقت", "⏱ Full time"), ("part_time", "🕒 پاره‌وقت", "🕒 Part time"),
                  ("weekends", "📅 آخر هفته‌ها", "📅 Weekends"), ("project", "🎯 پروژه‌ای", "🎯 Per project"),
                  ("not_now", "⛔ فعلاً آزاد نیستم", "⛔ Not available now"))
TRAVEL = _o(("none", "🏠 فقط شهر خودم", "🏠 My city only"), ("domestic", "🚗 داخل کشور", "🚗 Domestic"),
            ("international", "✈️ خارج از کشور هم", "✈️ International too"))
# skills: category -> (label fa, label en, [(code, fa, en)])
SKILL_CATS = {
    "acting": ("🎭 بازیگری", "🎭 Acting", _o(
        ("drama", "درام", "Drama"), ("comedy", "کمدی", "Comedy"), ("method", "متد", "Method"), ("improv", "بداهه", "Improvisation"),
        ("voice_acting", "دوبله/صداپیشگی", "Voice acting"), ("stage_combat", "مبارزه صحنه‌ای", "Stage combat"),
        ("mime", "پانتومیم", "Mime"), ("puppetry", "عروسک‌گردانی", "Puppetry"), ("stunt", "بدل‌کاری", "Stunts"),
        ("narration", "گویندگی", "Narration"))),
    "singing": ("🎤 خوانندگی", "🎤 Singing", _o(
        ("pop", "پاپ", "Pop"), ("traditional", "سنتی/آواز", "Traditional"), ("classical", "کلاسیک", "Classical"),
        ("opera", "اپرا", "Opera"), ("rap", "رپ", "Rap"), ("choir", "گروه کر", "Choir"), ("jazz", "جز", "Jazz"))),
    "dancing": ("💃 رقص", "💃 Dancing", _o(
        ("ballet", "باله", "Ballet"), ("contemporary", "معاصر", "Contemporary"), ("hiphop", "هیپ‌هاپ", "Hip-hop"),
        ("folk", "محلی/فولک", "Folk"), ("ballroom", "سالن", "Ballroom"), ("latin", "لاتین", "Latin"),
        ("street", "خیابانی", "Street"))),
    "instrument": ("🎸 ساز", "🎸 Instruments", _o(
        ("piano", "پیانو", "Piano"), ("guitar", "گیتار", "Guitar"), ("violin", "ویولن", "Violin"), ("tar", "تار", "Tar"),
        ("setar", "سه‌تار", "Setar"), ("santur", "سنتور", "Santur"), ("tonbak", "تنبک", "Tonbak"), ("ney", "نی", "Ney"),
        ("kamancheh", "کمانچه", "Kamancheh"), ("oud", "عود", "Oud"), ("drums", "درام", "Drums"),
        ("daf", "دف", "Daf"), ("flute", "فلوت", "Flute"), ("saxophone", "ساکسیفون", "Saxophone"))),
    "language": ("🗣 زبان", "🗣 Languages", _o(
        ("persian", "فارسی", "Persian"), ("english", "انگلیسی", "English"), ("azeri", "ترکی آذری", "Azeri Turkish"),
        ("kurdish", "کردی", "Kurdish"), ("arabic", "عربی", "Arabic"), ("lori", "لری", "Lori"), ("gilaki", "گیلکی", "Gilaki"),
        ("mazani", "مازنی", "Mazandarani"), ("balochi", "بلوچی", "Balochi"), ("turkish", "ترکی استانبولی", "Turkish"),
        ("french", "فرانسه", "French"), ("german", "آلمانی", "German"), ("russian", "روسی", "Russian"),
        ("spanish", "اسپانیایی", "Spanish"), ("italian", "ایتالیایی", "Italian"), ("chinese", "چینی", "Chinese"))),
    "driving": ("🚗 رانندگی", "🚗 Driving", _o(
        ("car", "خودرو", "Car"), ("motorcycle", "موتورسیکلت", "Motorcycle"), ("truck", "کامیون", "Truck"),
        ("bicycle", "دوچرخه", "Bicycle"))),
    "sport": ("🏅 ورزش", "🏅 Sports", _o(
        ("swimming", "شنا", "Swimming"), ("horse_riding", "اسب‌سواری", "Horse riding"), ("martial_arts", "رزمی", "Martial arts"),
        ("football", "فوتبال", "Football"), ("gym", "بدنسازی", "Gym"), ("climbing", "صخره‌نوردی", "Climbing"),
        ("fencing", "شمشیربازی", "Fencing"), ("archery", "تیراندازی با کمان", "Archery"), ("yoga", "یوگا", "Yoga"),
        ("diving", "غواصی", "Diving"), ("skiing", "اسکی", "Skiing"))),
    "other": ("✨ سایر", "✨ Other", _o(
        ("juggling", "ژونگلور", "Juggling"), ("magic", "شعبده‌بازی", "Magic"), ("drawing", "نقاشی", "Drawing"),
        ("photography", "عکاسی", "Photography"), ("cooking", "آشپزی", "Cooking"), ("public_speaking", "سخنوری", "Public speaking"))),
}
SKILL_CAT_ORDER = list(SKILL_CATS)

REGISTRY = {"gender": GENDER, "hair_color": HAIR, "eye_color": EYES, "skin_tone": SKIN, "role": ROLES,
            "experience_level": EXPERIENCE, "work_type": WORK_TYPES, "availability": AVAILABILITY, "travel": TRAVEL}

def codes(lst):
    return [c for c, _, _ in lst]

def label(lst, code, lang, default=None):
    for c, fa, en in lst:
        if c == code:
            return fa if lang == "fa" else en
    return default if default is not None else (code or "")

def plain(s):
    """strip leading emoji/symbol decoration from a label (for card lines and exports)."""
    s = s.strip()
    while s and not (s[0].isalnum()):
        s = s[1:].lstrip()
    return s

def skill_label(cat, code, lang):
    for c, fa, en in SKILL_CATS[cat][2]:
        if c == code:
            return fa if lang == "fa" else en
    return code

def skill_cat_label(cat, lang):
    fa, en, _ = SKILL_CATS[cat]
    return fa if lang == "fa" else en

def enums_export():
    out = {k: [{"code": c, "fa": plain(fa), "en": plain(en)} for c, fa, en in v] for k, v in REGISTRY.items()}
    out["skill_category"] = [{"code": k, "fa": plain(v[0]), "en": plain(v[1])} for k, v in SKILL_CATS.items()]
    out["skill"] = [{"category": k, "code": c, "fa": fa, "en": en} for k, v in SKILL_CATS.items() for c, fa, en in v[2]]
    return out

# quick city list: (fa canonical name stored in DB, en label)
CITIES = [("تهران", "Tehran"), ("مشهد", "Mashhad"), ("اصفهان", "Isfahan"), ("شیراز", "Shiraz"), ("تبریز", "Tabriz"),
          ("کرج", "Karaj"), ("قم", "Qom"), ("اهواز", "Ahvaz"), ("رشت", "Rasht"), ("کرمانشاه", "Kermanshah"),
          ("ارومیه", "Urmia"), ("یزد", "Yazd"), ("کرمان", "Kerman"), ("ساری", "Sari"), ("همدان", "Hamedan"),
          ("بندرعباس", "Bandar Abbas")]
