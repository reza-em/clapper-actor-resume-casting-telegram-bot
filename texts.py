"""All user-facing strings, Persian (fa) + English (en) with identical keys. add(key, fa, en)."""
T = {"fa": {}, "en": {}}

def add(key, fa, en):
    assert key not in T["fa"], "duplicate text key " + key
    T["fa"][key] = fa
    T["en"][key] = en

# =============================================================== general
add("pick_lang", "🌐 زبان را انتخاب کن / Choose your language:", "🌐 زبان را انتخاب کن / Choose your language:")
add("welcome", "🎬 <b>به «{name}» خوش اومدی!</b>\n\nاینجا رزومه‌ی هنری‌ات رو خیلی ساده می‌سازی و آگهی‌های بازیگرگیری تئاتر و سینما رو می‌بینی.\nفقط دکمه‌ها رو بزن؛ چیزی لازم نیست تایپ کنی 👇",
    "🎬 <b>Welcome to “{name}”!</b>\n\nBuild your acting/crew resume the easy way and browse casting calls for theatre and film.\nJust tap the buttons — no typing needed 👇")
add("menu_title", "چه کاری می‌خوای بکنی؟ 👇", "What would you like to do? 👇")
add("more_title", "⚙️ بیشتر", "⚙️ More")
add("yes", "✅ بله", "✅ Yes"); add("no", "❌ خیر", "❌ No")
add("yes_delete", "🗑 بله، پاک کن", "🗑 Yes, delete")
add("on", "روشن ✅", "On ✅"); add("off", "خاموش ⛔", "Off ⛔")
add("unexpected", "❌ یه مشکلی پیش اومد. لطفاً دوباره امتحان کن.", "❌ Something went wrong. Please try again.")
add("banned", "🚫 دسترسی تو به ربات مسدود شده است.", "🚫 Your access to this bot has been blocked.")
add("unknown_cmd", "برای شروع فقط دکمه‌های زیر رو بزن 👇", "Just tap the buttons below 👇")
add("lim_unl", "نامحدود ♾", "unlimited ♾")

# main menu + common buttons
add("b_build", "📝 ساخت رزومه", "📝 Build my resume"); add("b_my_resume", "👤 رزومه من", "👤 My resume")
add("b_search", "🔍 جستجو", "🔍 Search"); add("b_calls", "🎭 آگهی‌ها", "🎭 Casting calls")
add("b_support", "📞 پشتیبانی", "📞 Support"); add("b_more", "⚙️ بیشتر", "⚙️ More")
add("b_other_lang", "🌐 English", "🌐 فارسی"); add("b_admin", "🛠 پنل مدیریت", "🛠 Admin panel")
add("b_menu", "🏠 منوی اصلی", "🏠 Main menu"); add("b_back", "⬅️ برگشت", "⬅️ Back"); add("b_skip", "⏭ رد شدن", "⏭ Skip")
add("b_next", "➡️ بعدی", "➡️ Next"); add("b_cancel", "✖️ انصراف", "✖️ Cancel")
add("b_plans", "💎 پلن‌ها", "💎 Plans"); add("b_me", "🧾 حساب من", "🧾 My account")
add("b_invite", "🎁 دعوت دوستان", "🎁 Invite friends"); add("b_faq", "❓ سؤال‌های رایج", "❓ FAQ")
add("b_help", "ℹ️ راهنما", "ℹ️ Help"); add("b_about", "💡 درباره", "💡 About")
add("b_delete_data", "🗑 حذف اطلاعات من", "🗑 Delete my data"); add("b_share", "📤 اشتراک‌گذاری", "📤 Share")
add("b_contact", "💬 پیام به پشتیبانی", "💬 Message support")
add("b_support1", "💬 پشتیبان ۱", "💬 Support 1"); add("b_support2", "💬 پشتیبان ۲", "💬 Support 2")
add("b_start_again", "🏠 شروع دوباره", "🏠 Start again"); add("b_ad_open", "🔗 باز کردن", "🔗 Open")
add("note_one", "📞 پشتیبانی: @{p}", "📞 Support: @{p}"); add("note_two", "📞 پشتیبانی: @{p} یا @{b}", "📞 Support: @{p} or @{b}")
add("sponsor_label", "📢 حامی:", "📢 Sponsor:"); add("ad_label", "📢 <b>تبلیغ</b>", "📢 <b>Ad</b>")
add("ad_click_msg", "🔗 لینک:\n{url}", "🔗 Link:\n{url}")
add("support_text", "📞 <b>پشتیبانی</b>\n\nهر سؤال یا مشکلی داری، مستقیم به پشتیبانی پیام بده 💖\n{note}", "📞 <b>Support</b>\n\nAny question or problem? Message support directly 💖\n{note}")
add("help", "ℹ️ <b>راهنما</b>\n\n📝 «ساخت رزومه»: چند سؤال ساده، هر بار یکی. می‌تونی رد کنی یا برگردی؛ پیشرفتت خودکار ذخیره می‌شه.\n🎭 «آگهی‌ها»: آگهی‌های بازیگرگیری رو ببین و با رزومه‌ات درخواست بده. کارگردان‌ها اینجا آگهی می‌ذارن.\n🔍 «جستجو»: برای کارگردان‌ها و تهیه‌کننده‌ها.\n🔒 رزومه‌ات رو هر وقت خواستی مخفی یا پاک کن.\n\nفقط /start رو بزن و از دکمه‌ها استفاده کن.",
    "ℹ️ <b>Help</b>\n\n📝 “Build resume”: a few simple questions, one at a time. Skip or go back any time; progress is saved automatically.\n🎭 “Casting calls”: browse calls and apply with your resume. Directors post calls here.\n🔍 “Search”: for directors and producers.\n🔒 Hide or delete your resume whenever you like.\n\nJust send /start and use the buttons.")
add("about", "💡 <b>{name}</b>\n\nربات رزومه و بازیگرگیری برای بازیگران و عوامل تئاتر و سینما. رزومه بساز، آگهی ببین، پیدا شو.\n\n📢 برای تبلیغات و همکاری: @{sp}",
    "💡 <b>{name}</b>\n\nA resume & casting bot for actors and crew in theatre and film. Build a resume, browse calls, get discovered.\n\n📢 Ads & cooperation: @{sp}")
add("faq_title", "❓ <b>سؤال‌های رایج</b>", "❓ <b>FAQ</b>"); add("faq_none", "هنوز سؤالی ثبت نشده.", "No questions yet.")

# consent / delete data
add("consent", "🔒 <b>قبل از شروع</b>\n\nبرای ساخت رزومه، اطلاعاتی مثل نام، سن، شهر، تصویر و راه ارتباطی‌ات ذخیره می‌شه. فقط کارگردان‌ها و تهیه‌کننده‌های ثبت‌نام‌شده در ربات (و مدیران) می‌تونن رزومه‌ات رو ببینن، و هر وقت خواستی می‌تونی اون رو مخفی یا کامل پاک کنی («⚙️ بیشتر ← 🗑 حذف اطلاعات من»).\n\nموافقی؟",
    "🔒 <b>Before we start</b>\n\nTo build a resume we store details such as your name, age, city, photos and contact info. Only registered directors/producers in this bot (and admins) can see it, and you can hide or fully delete it any time (“⚙️ More → 🗑 Delete my data”).\n\nDo you agree?")
add("b_agree", "✅ موافقم، شروع کنیم", "✅ I agree, let's start"); add("b_agree_c", "✅ موافقم", "✅ I agree")
add("b_no_agree", "❌ نه، ممنون", "❌ No thanks"); add("consent_ok", "ممنون 💖 شروع می‌کنیم!", "Thank you 💖 Let's go!")
add("deldata_ask", "⚠️ همه‌ی اطلاعاتت (رزومه، عکس‌ها، آگهی‌ها و درخواست‌ها) برای همیشه پاک می‌شه. مطمئنی؟", "⚠️ All your data (resume, photos, calls, applications) will be erased permanently. Are you sure?")
add("deldata_done", "✅ همه‌ی اطلاعاتت پاک شد. هر وقت خواستی دوباره برگرد 💖", "✅ All your data has been erased. Come back any time 💖")

# =============================================================== wizard
add("w_progress", "📝 مرحله {n} از {total}\n{bar}", "📝 Step {n} of {total}\n{bar}")
add("w_edit_head", "✏️ ویرایش", "✏️ Edit")
add("w_now", "الان: <b>{v}</b>", "Now: <b>{v}</b>")
add("w_continue", "پیشرفتت ذخیره شده: مرحله {n} از {total} 💾\nمی‌خوای ادامه بدی؟", "Your progress is saved: step {n} of {total} 💾\nContinue?")
add("b_continue", "▶️ ادامه", "▶️ Continue"); add("b_restart", "🔄 از اول", "🔄 From the start")
add("b_preview", "👁 دیدن رزومه", "👁 See my resume"); add("b_edit", "✏️ ویرایش", "✏️ Edit")
add("b_back_resume", "⬅️ برگشت به رزومه", "⬅️ Back to resume"); add("b_clear", "🧹 پاک کردن", "🧹 Clear")
add("b_confirm", "✅ تایید", "✅ Confirm"); add("b_fill_missing", "➕ تکمیل موارد لازم", "➕ Fill in required items")
add("b_other_city", "✍️ شهر دیگه", "✍️ Other city"); add("b_use_my_tg", "✈️ همین @{u}", "✈️ Use @{u}")
add("b_add_work", "➕ افزودن کار", "➕ Add a work"); add("b_del_photo", "🗑 حذف عکس {n}", "🗑 Delete photo {n}")
add("b_back_cats", "⬅️ دسته‌ها", "⬅️ Categories")
add("b_hide", "🙈 مخفی کردن رزومه", "🙈 Hide my resume"); add("b_show", "👀 نمایش رزومه", "👀 Show my resume")
add("b_del_resume", "🗑 حذف رزومه", "🗑 Delete resume")
add("w_saved", "✅ ثبت شد", "✅ Saved"); add("w_use_buttons", "لطفاً از دکمه‌های زیر انتخاب کن 👆", "Please tap one of the buttons above 👆")
add("w_type_city", "اسم شهرت رو بنویس ✍️", "Type your city name ✍️")
add("w_send_photo", "📷 یه عکس بفرست (به‌صورت عکس، نه فایل).", "📷 Please send a photo.")
add("w_photo_not_now", "الان نوبت عکس نیست 🙂 به سؤال بالا جواب بده.", "It's not the photo step 🙂 Please answer the question above.")
add("w_photo_ok", "✅ عکس {n} ذخیره شد. عکس دیگه‌ای هم داری؟ بفرست، یا «بعدی» رو بزن.", "✅ Photo {n} saved. Send another one or tap “Next”.")
add("w_photo_max", "حداکثر {max} عکس می‌تونی داشته باشی. برای عوض کردن، یکی رو حذف کن.", "You can have up to {max} photos. Delete one to add another.")
add("w_photo_dup", "این عکس قبلاً اضافه شده 🙂", "That photo is already added 🙂")
add("w_photo_count", "📷 عکس‌ها: {n} از {max}", "📷 Photos: {n} of {max}")
add("w_skill_cat", "🛠 <b>{cat}</b>\nهرکدوم رو بلدی بزن (دوباره بزنی برداشته می‌شه):", "🛠 <b>{cat}</b>\nTap what you can do (tap again to remove):")
add("w_skill_added", "✅ اضافه شد", "✅ Added")
add("w_work_saved", "✅ کار ذخیره شد", "✅ Work saved"); add("w_too_many", "حداکثر ۳۰ کار می‌تونی ثبت کنی.", "You can add up to 30 works.")
add("w_edit_menu", "کدوم بخش رو می‌خوای ویرایش کنی؟", "Which part do you want to edit?")
add("w_preview_head", "👁 این رزومه‌ی توئه:", "👁 Here is your resume:")
add("w_preview_ask", "همه‌چیز درسته؟ 👇", "Everything looking right? 👇")
add("w_missing", "⚠️ این موارد هنوز لازمه: {items}", "⚠️ These are still needed: {items}")
add("w_published", "🎉 رزومه‌ات ثبت شد! حالا می‌تونی توی «🎭 آگهی‌ها» درخواست بدی.", "🎉 Your resume is saved! Now you can apply in “🎭 Casting calls”.")
add("my_resume_foot", "{status}", "{status}")
add("vis_public", "👀 رزومه‌ات برای کارگردان‌ها قابل دیدنه.", "👀 Your resume is visible to casting directors.")
add("vis_hidden", "🙈 رزومه‌ات مخفیه و کسی نمی‌بینه.", "🙈 Your resume is hidden; nobody can see it.")
add("vis_admin_hidden", "⚠️ مدیر این رزومه رو از جستجو خارج کرده. با پشتیبانی تماس بگیر.", "⚠️ An admin removed this resume from search. Contact support.")
add("vis_featured", "⭐ رزومه‌ات ویژه شده!", "⭐ Your resume is featured!")
add("del_resume_confirm", "رزومه‌ات (با عکس‌ها) پاک بشه؟", "Delete your resume (with photos)?")
add("del_resume_done", "🗑 رزومه پاک شد.", "🗑 Resume deleted.")

# validation errors
add("err_name", "اسم رو درست بنویس (۲ تا ۶۰ حرف) 🙂", "Please write a proper name (2–60 characters) 🙂")
add("err_year", "سال تولد ۴ رقمیه، مثلاً ۱۳۷۵ یا 1996 🙂", "Birth year has 4 digits, e.g. 1375 or 1996 🙂")
add("err_year2", "سال ۴ رقمی بنویس، مثلاً ۱۴۰۲ 🙂", "Please write a 4-digit year, e.g. 2023 🙂")
add("err_city", "اسم شهر رو بنویس (۲ تا ۴۰ حرف) 🙂", "Please write a city name (2–40 characters) 🙂")
add("err_height", "قد رو به سانتی‌متر بنویس، مثلاً ۱۷۵ 🙂", "Height in centimetres, e.g. 175 🙂")
add("err_weight", "وزن رو به کیلو بنویس، مثلاً ۶۸ 🙂", "Weight in kilograms, e.g. 68 🙂")
add("err_phone", "شماره رو با ارقام بنویس، مثلاً 09121234567 🙂", "Please write digits only, e.g. 09121234567 🙂")
add("err_tg", "آیدی تلگرام مثل @myname (حداقل ۵ حرف) 🙂", "Telegram username like @myname (min 5 chars) 🙂")
add("err_email", "ایمیل معتبر نیست؛ مثل name@example.com 🙂", "That email looks invalid; like name@example.com 🙂")
add("err_insta", "آیدی اینستاگرام یا لینک صفحه‌ات رو بفرست 🙂", "Send your Instagram username or profile link 🙂")
add("err_links", "لینک‌ها باید با https:// شروع بشن (حداکثر ۵ تا، با فاصله جدا کن) 🙂", "Links must start with https:// (max 5, separated by spaces) 🙂")
add("err_url", "لینک باید با https:// شروع بشه 🙂", "The link must start with https:// 🙂")
add("err_empty", "چیزی ننوشتی؛ دوباره بنویس یا «رد شدن» رو بزن 🙂", "That looks empty; write again or tap “Skip” 🙂")

# question, example, label per step (fields of wizard.STEPS)
_S = {
 "full_name_fa": ("اسم و فامیلت رو (فارسی) بنویس", "مثلاً: سارا احمدی", "نام و نام خانوادگی", "What's your full name (in Persian)?", "e.g. Sara Ahmadi", "Full name"),
 "stage_name": ("اسم هنری یا لاتینت چیه؟ (اختیاری)", "مثلاً: Sara Ahmadi", "اسم هنری", "Do you have a stage / Latin name? (optional)", "e.g. Sara Ahmadi", "Stage name"),
 "gender": ("جنسیتت؟", "یکی از دکمه‌ها رو بزن", "جنسیت", "Your gender?", "tap a button", "Gender"),
 "birth_year": ("سال تولدت؟", "مثلاً: ۱۳۷۵ (شمسی) یا 1996 (میلادی)", "سال تولد", "Your birth year?", "e.g. 1375 (Persian) or 1996", "Birth year"),
 "city": ("توی کدوم شهر زندگی می‌کنی؟", "یکی رو بزن، یا «شهر دیگه»", "شهر", "Which city do you live in?", "tap one, or “Other city”", "City"),
 "roles": ("توی چه کاری فعالی؟", "می‌تونی چندتا انتخاب کنی، بعد «بعدی» رو بزن", "نقش‌ها", "What do you work as?", "you may pick several, then tap “Next”", "Roles"),
 "experience_level": ("تجربه‌ات چقدره؟", "یکی از دکمه‌ها", "سطح تجربه", "How experienced are you?", "tap a button", "Experience"),
 "photos": ("یه عکس واضح از خودت بفرست 📷", "عکس پرتره با نور خوب؛ تا چند عکس می‌شه", "عکس‌ها", "Send a clear photo of yourself 📷", "a well-lit portrait; several photos are fine", "Photos"),
 "phone": ("شماره‌ی تماست؟ (اختیاری)", "مثلاً: 09121234567", "تلفن", "Your phone number? (optional)", "e.g. 09121234567", "Phone"),
 "telegram_username": ("آیدی تلگرامت؟ (اختیاری)", "مثلاً: @sara_actor", "آیدی تلگرام", "Your Telegram username? (optional)", "e.g. @sara_actor", "Telegram"),
 "email": ("ایمیلت؟ (اختیاری)", "مثلاً: sara@example.com", "ایمیل", "Your email? (optional)", "e.g. sara@example.com", "Email"),
 "instagram": ("اینستاگرامت؟ (اختیاری)", "مثلاً: sara_actor", "اینستاگرام", "Your Instagram? (optional)", "e.g. sara_actor", "Instagram"),
 "height_cm": ("قدت چند سانتیه؟ (اختیاری)", "مثلاً: ۱۷۰", "قد", "Your height in cm? (optional)", "e.g. 170", "Height"),
 "weight_kg": ("وزنت چند کیلوئه؟ (اختیاری)", "مثلاً: ۶۰", "وزن", "Your weight in kg? (optional)", "e.g. 60", "Weight"),
 "hair_color": ("رنگ موهات؟ (اختیاری)", "یکی از دکمه‌ها", "رنگ مو", "Your hair colour? (optional)", "tap a button", "Hair colour"),
 "eye_color": ("رنگ چشمات؟ (اختیاری)", "یکی از دکمه‌ها", "رنگ چشم", "Your eye colour? (optional)", "tap a button", "Eye colour"),
 "skin_tone": ("رنگ پوستت؟ (اختیاری)", "یکی از دکمه‌ها", "رنگ پوست", "Your skin tone? (optional)", "tap a button", "Skin tone"),
 "skills": ("چه مهارت‌هایی داری؟ (اختیاری)", "یه دسته رو بزن و مهارت‌ها رو تیک بزن؛ مهارت دیگه‌ای داری؟ همینجا بنویس", "مهارت‌ها", "What skills do you have? (optional)", "open a category and tick; or just type any other skill here", "Skills"),
 "history": ("سابقه‌ی کارهات؟ (اختیاری)", "هر کار رو جدا اضافه کن؛ مثلاً یه تئاتر یا فیلم کوتاه", "سابقه کار", "Your work history? (optional)", "add each work separately, e.g. a play or short film", "Work history"),
 "education": ("تحصیلات و دوره‌های هنری؟ (اختیاری)", "مثلاً: کارشناسی بازیگری، دانشگاه هنر؛ کارگاه بازیگری ۱۴۰۱", "تحصیلات", "Education & training? (optional)", "e.g. BA in Acting; acting workshop 2022", "Education"),
 "awards": ("جایزه و جشنواره؟ (اختیاری)", "مثلاً: تندیس بهترین بازیگر جشنواره‌ی فلان", "جوایز", "Awards & festivals? (optional)", "e.g. Best Actor, XYZ Festival", "Awards"),
 "portfolio_links": ("لینک نمونه‌کارها؟ (اختیاری)", "مثلاً: https://example.com/portfolio", "نمونه‌کار", "Portfolio links? (optional)", "e.g. https://example.com/portfolio", "Portfolio"),
 "demo_reel_url": ("لینک دموریل (ویدیوی نمونه)؟ (اختیاری)", "مثلاً: https://youtu.be/xxxx", "دموریل", "Demo reel link? (optional)", "e.g. https://youtu.be/xxxx", "Demo reel"),
 "availability": ("چقدر آزادی؟ (اختیاری)", "یکی از دکمه‌ها", "زمان آزاد", "How available are you? (optional)", "tap a button", "Availability"),
 "travel": ("برای کار سفر می‌کنی؟ (اختیاری)", "یکی از دکمه‌ها", "سفر", "Will you travel for work? (optional)", "tap a button", "Travel"),
 "expected_fee": ("دستمزد مورد انتظار؟ (اختیاری)", "مثلاً: توافقی، یا ۵ میلیون تومان برای هر روز", "دستمزد", "Expected fee? (optional)", "e.g. negotiable, or 5M toman per day", "Expected fee"),
 "bio": ("آخرین مرحله: یه معرفی کوتاه از خودت 🎉", "۱ تا ۳ جمله؛ مثلاً: بازیگر تئاتر با ۵ سال سابقه...", "معرفی کوتاه", "Last step: a short intro about you 🎉", "1–3 sentences, e.g. Stage actor with 5 years of experience...", "Short bio"),
}
for _k, (_qf, _ef, _lf, _qe, _ee, _le) in _S.items():
    add("q_" + _k, _qf, _qe); add("ex_" + _k, _ef, _ee); add("lbl_" + _k, _lf, _le)

# work-history sub-flow
add("wh_head", "🎞 افزودن کار — {n} از {total}", "🎞 Add a work — {n} of {total}")
_H = {"title": ("اسم اثر؟", "مثلاً: نمایش «مرگ فروشنده»", "Title of the work?", "e.g. the play “Death of a Salesman”"),
      "type": ("نوع کار؟", "یکی از دکمه‌ها", "Type of work?", "tap a button"),
      "role": ("چه نقشی داشتی؟", "مثلاً: نقش اصلی، دستیار کارگردان", "Your role?", "e.g. lead role, assistant director"),
      "year": ("چه سالی؟", "مثلاً: ۱۴۰۲", "Which year?", "e.g. 2023"),
      "company": ("کارگردان یا شرکت تولید؟", "مثلاً: علی رضایی", "Director or company?", "e.g. Ali Rezaei")}
for _k, (_qf, _ef, _qe, _ee) in _H.items():
    add("wh_q_" + _k, _qf, _qe); add("wh_ex_" + _k, _ef, _ee)

# =============================================================== search / casting director side
add("s_not_allowed", "🔍 جستجوی رزومه مخصوص کارگردان‌ها و تهیه‌کننده‌هاست.\nاگر کارگردان یا تهیه‌کننده‌ای، ثبت‌نام کن 👇", "🔍 Resume search is for directors and producers.\nIf that's you, register below 👇")
add("s_pending", "⏳ ثبت‌نامت هنوز در انتظار تاییده. کمی صبر کن.", "⏳ Your registration is still waiting for approval.")
add("s_panel", "🔍 <b>جستجوی رزومه</b>\n\nفیلترها: {f}\nنتیجه: <b>{n}</b> رزومه", "🔍 <b>Resume search</b>\n\nFilters: {f}\nResults: <b>{n}</b> resumes")
add("s_no_filters", "بدون فیلتر", "no filters")
add("sb_q", "🔤 متن آزاد", "🔤 Free text"); add("sb_name", "📛 اسم", "📛 Name"); add("sb_city", "🏙 شهر", "🏙 City")
add("sb_role", "🎬 نقش", "🎬 Role"); add("sb_skill", "🛠 مهارت", "🛠 Skill"); add("sb_lang", "🗣 زبان", "🗣 Language")
add("sb_gender", "🚻 جنسیت", "🚻 Gender"); add("sb_exp", "⭐ تجربه", "⭐ Experience"); add("sb_age", "🎂 سن", "🎂 Age")
add("sb_height", "📏 قد", "📏 Height"); add("sb_featured", "⭐ فقط ویژه‌ها", "⭐ Featured only"); add("sb_featured_on", "✅ فقط ویژه‌ها", "✅ Featured only")
add("sb_show", "👁 نمایش نتایج ({n})", "👁 Show results ({n})"); add("sb_clear", "🧹 پاک کردن فیلترها", "🧹 Clear filters")
add("b_any", "♾ فرقی نمی‌کنه", "♾ Any"); add("b_custom_range", "✍️ بازه‌ی دلخواه", "✍️ Custom range")
add("b_change_filters", "🎛 تغییر فیلترها", "🎛 Change filters"); add("b_full_resume", "📄 رزومه کامل", "📄 Full resume")
add("b_back_search", "⬅️ برگشت به جستجو", "⬅️ Back to search")
for _k, _fa, _en in [("city", "🏙 شهر رو انتخاب کن:", "🏙 Pick a city:"), ("role", "🎬 نقش رو انتخاب کن:", "🎬 Pick a role:"),
                     ("gender", "🚻 جنسیت:", "🚻 Gender:"), ("exp", "⭐ سطح تجربه:", "⭐ Experience level:"),
                     ("language", "🗣 زبان:", "🗣 Language:"), ("skill", "🛠 دسته‌ی مهارت:", "🛠 Skill category:"),
                     ("age", "🎂 بازه‌ی سنی:", "🎂 Age range:"), ("h", "📏 بازه‌ی قد (سانتی‌متر):", "📏 Height range (cm):")]:
    add("s_pick_" + _k, _fa, _en)
add("s_ask_q", "🔤 کلمه‌ای که دنبالشی رو بنویس (مثلاً: گریم، تئاتر، ویولن):", "🔤 Type a word to look for (e.g. makeup, theatre, violin):")
add("s_ask_name", "📛 اسم رو بنویس:", "📛 Type the name:")
add("s_ask_city", "🏙 اسم شهر رو بنویس:", "🏙 Type the city name:")
add("s_ask_age", "🎂 بازه‌ی سنی رو بنویس، مثلاً: 20-30", "🎂 Type an age range, e.g. 20-30")
add("s_ask_h", "📏 بازه‌ی قد رو بنویس، مثلاً: 165-180", "📏 Type a height range, e.g. 165-180")
add("s_bad_range", "بازه درست نیست؛ مثل 20-30 بنویس 🙂", "Invalid range; write it like 20-30 🙂")
add("s_none", "😕 رزومه‌ای با این فیلترها پیدا نشد.", "😕 No resumes match these filters.")
add("s_gone", "این رزومه دیگه در دسترس نیست.", "This resume is no longer available.")
add("s_results_head", "🔍 {n} رزومه پیدا شد (صفحه {p} از {pages})", "🔍 {n} resumes found (page {p} of {pages})")
add("s_page_foot", "صفحه‌ها 👇", "Pages 👇")
add("q_views", "👁 دیدن رزومه کامل (این ماه)", "👁 Full resume views (this month)")
add("q_apps", "📨 درخواست به آگهی (این ماه)", "📨 Applications (this month)")
add("q_posts", "📢 ثبت آگهی (این ماه)", "📢 Posting calls (this month)")
add("quota_out_views", "🔒 سهمیه‌ی رایگان دیدن رزومه‌ی کامل این ماه تموم شد.\nبرای فعال‌سازی پلن با پشتیبانی هماهنگ کن (پرداخت بیرون از ربات). شناسه‌ی عددی تو: <code>{uid}</code>\n{note}",
    "🔒 This month's free full-resume views are used up.\nArrange a plan with support (payment happens outside the bot). Your numeric ID: <code>{uid}</code>\n{note}")
add("quota_out_apps", "🔒 سهمیه‌ی رایگان درخواست این ماه تموم شد.\nبرای فعال‌سازی پلن با پشتیبانی هماهنگ کن یا دوستانت رو دعوت کن. شناسه‌ی عددی تو: <code>{uid}</code>\n{note}",
    "🔒 This month's free applications are used up.\nArrange a plan with support or invite friends. Your numeric ID: <code>{uid}</code>\n{note}")
add("quota_out_posts", "🔒 سهمیه‌ی رایگان ثبت آگهی این ماه تموم شد.\nبرای فعال‌سازی پلن با پشتیبانی هماهنگ کن. شناسه‌ی عددی تو: <code>{uid}</code>\n{note}",
    "🔒 This month's free call postings are used up.\nArrange a plan with support. Your numeric ID: <code>{uid}</code>\n{note}")

# resume card bits
add("c_age", "{n} ساله", "{n} y/o"); add("c_works", "{n} کار", "{n} works"); add("c_height", "قد {n} سانتی", "{n} cm tall")
add("c_weight", "وزن {n} کیلو", "{n} kg"); add("c_hair", "مو:", "Hair:"); add("c_eyes", "چشم:", "Eyes:"); add("c_skin", "پوست:", "Skin:")
add("c_history", "سابقه‌ی کار", "Work history"); add("c_education", "تحصیلات", "Education"); add("c_awards", "جوایز", "Awards")
add("c_reel", "دموریل", "Demo reel"); add("c_contact", "📇 راه‌های تماس", "📇 Contact")
add("tag_draft", "📝 پیش‌نویس", "📝 Draft"); add("tag_hidden_user", "🙈 مخفی (کاربر)", "🙈 Hidden (user)")
add("tag_hidden_admin", "🚫 مخفی (مدیر)", "🚫 Hidden (admin)"); add("tag_featured", "⭐ ویژه", "⭐ Featured")

# =============================================================== casting calls
add("k_menu", "🎭 <b>آگهی‌ها</b>\n\nآگهی‌های بازیگرگیری و عوامل رو ببین و با رزومه‌ات درخواست بده. کارگردان‌ها اینجا آگهی می‌ذارن.", "🎭 <b>Casting calls</b>\n\nBrowse calls for actors and crew and apply with your resume. Directors post calls here.")
add("b_browse_calls", "📋 دیدن آگهی‌ها", "📋 Browse calls"); add("b_my_apps", "📨 درخواست‌های من", "📨 My applications")
add("b_new_call", "➕ آگهی جدید", "➕ New call"); add("b_my_calls", "📁 آگهی‌های من", "📁 My calls")
add("b_register_casting", "🎬 من کارگردان/تولید هستم", "🎬 I'm a director/producer"); add("b_pending", "⏳ در انتظار تایید", "⏳ Awaiting approval")
add("b_apply", "📨 درخواست می‌دم", "📨 Apply"); add("b_applied", "✅ درخواست دادی", "✅ Applied")
add("b_applicants", "👥 متقاضی‌ها {n}", "👥 Applicants {n}"); add("b_close_call", "🔒 بستن", "🔒 Close"); add("b_reopen_call", "🔓 باز کردن", "🔓 Reopen")
add("b_publish", "✅ انتشار آگهی", "✅ Publish call"); add("b_approve", "✅ تایید", "✅ Approve"); add("b_reject", "❌ رد", "❌ Reject")
add("k_ask_name", "اسمت یا اسم گروه/شرکت تولیدت چیه؟\n💡 مثلاً: گروه تئاتر پرواز", "What's your name or your production/company name?\n💡 e.g. Parvaz Theatre Group")
add("k_pending", "⏳ ثبت‌نامت در انتظار تایید مدیره. وقتی تایید بشه بهت خبر می‌دم.", "⏳ Your registration is awaiting admin approval. I'll let you know.")
add("k_reg_pending", "✅ ثبت‌نام انجام شد و منتظر تایید مدیره. بهت خبر می‌دم 💖", "✅ Registered — waiting for admin approval. I'll notify you 💖")
add("k_reg_ok", "🎉 ثبت‌نام شد! حالا می‌تونی آگهی بذاری و رزومه‌ها رو جستجو کنی.", "🎉 Registered! You can now post calls and search resumes.")
add("k_notify_admin", "🎬 درخواست ثبت‌نام کارگردان/تولید:\n{who}\nنام: {name}", "🎬 New director/producer registration:\n{who}\nName: {name}")
add("u_casting_ok", "🎉 ثبت‌نامت تایید شد! حالا می‌تونی آگهی بذاری.", "🎉 You're approved! You can now post calls.")
add("u_casting_no", "متأسفانه ثبت‌نامت تایید نشد. برای اطلاعات بیشتر به پشتیبانی پیام بده.", "Sorry, your registration was not approved. Contact support for details.")
add("kc_head", "🎬 آگهی جدید — {n} از {total}", "🎬 New call — {n} of {total}")
_K = {"title": ("عنوان آگهی؟", "مثلاً: بازیگر زن برای فیلم کوتاه «سایه»", "Title of the call?", "e.g. Female lead for the short film “Shadow”"),
      "type": ("نوع پروژه؟", "یکی از دکمه‌ها", "Project type?", "tap a button"),
      "roles": ("دنبال چه نقش‌هایی هستی؟", "چندتا می‌تونی انتخاب کنی، بعد «بعدی»", "Which roles do you need?", "pick several, then “Next”"),
      "city": ("شهر پروژه؟", "یکی رو بزن یا اسم شهر رو بنویس", "Project city?", "tap one or type the city"),
      "date": ("تاریخ شروع یا مهلت؟ (اختیاری)", "مثلاً: 1405/08/15", "Start date or deadline? (optional)", "e.g. 2026-11-06 or 1405/08/15"),
      "details": ("توضیحات؟ (اختیاری)", "سن، ظاهر، دستمزد، شرایط...", "Details? (optional)", "age, look, pay, conditions..."),
      "contact": ("راه ارتباط برای متقاضی‌ها؟", "مثلاً: @myid یا 09121234567", "Contact for applicants?", "e.g. @myid or 09121234567")}
for _k, (_qf, _ef, _qe, _ee) in _K.items():
    add("kq_" + _k, _qf, _qe); add("kex_" + _k, _ef, _ee)
add("kc_need_role", "حداقل یک نقش انتخاب کن 🙂", "Pick at least one role 🙂")
add("kc_preview", "👁 پیش‌نمایش آگهی:", "👁 Call preview:")
add("kc_published", "🎉 آگهی منتشر شد!", "🎉 Your call is published!")
add("kc_applicants", "👥 متقاضی‌ها: {n}", "👥 Applicants: {n}")
add("k_list_head", "🎭 {n} آگهی (صفحه {p} از {pages})", "🎭 {n} calls (page {p} of {pages})")
add("k_none", "فعلاً آگهی بازی نیست 🙂", "No open calls right now 🙂"); add("k_none_mine", "هنوز آگهی‌ای نذاشتی.", "You haven't posted any calls yet.")
add("k_none_apps", "هنوز درخواستی ندادی.", "No applications yet."); add("k_my_apps_head", "📨 <b>درخواست‌های من</b>", "📨 <b>My applications</b>")
add("k_status_open", "🟢 باز", "🟢 Open"); add("k_status_closed", "🔒 بسته", "🔒 Closed"); add("k_status_hidden", "🙈 مخفی", "🙈 Hidden")
add("k_closed", "این آگهی بسته شده.", "This call is closed."); add("k_own_call", "این آگهی خودته 🙂", "That's your own call 🙂")
add("k_already", "قبلاً برای این آگهی درخواست دادی ✅", "You've already applied ✅")
add("k_need_resume", "برای درخواست دادن اول باید رزومه‌ات رو کامل کنی 📝", "You need to complete your resume before applying 📝")
add("k_applied", "✅ درخواستت با رزومه‌ات فرستاده شد. موفق باشی 🍀", "✅ Your application was sent with your resume. Good luck 🍀")
add("k_new_applicant", "📨 متقاضی جدید برای «{title}»: {name}", "📨 New applicant for “{title}”: {name}")
add("k_applicants_head", "👥 متقاضی‌های «{title}» — {n} نفر (صفحه {p} از {pages})", "👥 Applicants for “{title}” — {n} (page {p} of {pages})")
add("k_no_applicants", "هنوز متقاضی‌ای نداری.", "No applicants yet.")
add("k_del_confirm", "آگهی پاک بشه؟", "Delete this call?")

# =============================================================== account / plans / referrals
add("plans_title", "💎 <b>پلن‌ها</b>", "💎 <b>Plans</b>")
add("plans_free", "🆓 <b>رایگان (هر ماه)</b>\n{lines}", "🆓 <b>Free (per month)</b>\n{lines}")
add("plans_free_lines", "👁 دیدن رزومه‌ی کامل (کارگردان‌ها): {views}\n📨 درخواست به آگهی: {apps}\n📢 ثبت آگهی: {posts}", "👁 Full resume views (directors): {views}\n📨 Applications: {apps}\n📢 Posting calls: {posts}")
add("plans_card", "💎 <b>{title}</b>\n💰 {price}{dur}{perks}{feats}", "💎 <b>{title}</b>\n💰 {price}{dur}{perks}{feats}")
add("pl_views", "دیدن رزومه: {n} در ماه", "Resume views: {n} / month"); add("pl_apps", "درخواست: {n} در ماه", "Applications: {n} / month")
add("pl_posts", "ثبت آگهی: {n} در ماه", "Call postings: {n} / month"); add("pp_popular", "⭐ <b>محبوب</b>", "⭐ <b>Popular</b>")
add("plans_none", "پلن پولی فعلاً تعریف نشده.", "No paid plans yet.")
add("plans_footer", "💬 پرداخت بیرون از ربات و با هماهنگی پشتیبانی انجام می‌شه؛ ربات هیچ شماره کارت یا رسیدی نمی‌گیره. بعد از هماهنگی، مدیر پلن رو برات فعال می‌کنه.\n🆔 شناسه‌ی عددی تو: <code>{uid}</code>\n{note}",
    "💬 Payment is arranged outside the bot with support; the bot never collects card numbers or receipts. After that an admin activates the plan.\n🆔 Your numeric ID: <code>{uid}</code>\n{note}")
add("me_head", "🧾 <b>حساب تو</b>", "🧾 <b>Your account</b>"); add("me_admin", "👑 نقش: مدیر (نامحدود)", "👑 Role: admin (unlimited)")
add("me_plan", "💎 پلن: {title} — تا {until}", "💎 Plan: {title} — until {until}"); add("me_no_expiry", "بدون انقضا", "no expiry")
add("me_free", "🆓 پلن: رایگان", "🆓 Plan: free"); add("me_resume", "📝 رزومه: {s}", "📝 Resume: {s}")
add("rs_complete", "کامل ✅", "complete ✅"); add("rs_draft", "پیش‌نویس 📝", "draft 📝"); add("rs_none", "ندارد", "none")
add("me_credits", "🎟 اعتبار اضافه: {n}", "🎟 Extra credits: {n}"); add("me_ref", "🎁 دعوت‌ها: {n} (اعتبار گرفته‌شده: {b})", "🎁 Invites: {n} (credits earned: {b})")
add("me_id", "🆔 شناسه‌ی عددی: <code>{uid}</code>", "🆔 Numeric ID: <code>{uid}</code>")
add("invite_text", "🎁 <b>دعوت دوستان</b>\n\nلینک اختصاصی تو:\n{link}\n\nهر دوستی که با این لینک وارد بشه، {bonus} اعتبار بهت می‌رسه.{invitee_line}\n\n👥 دعوت‌شده‌ها: {n} — اعتبار گرفته‌شده: {earned}\n(هر اعتبار = یک بار استفاده‌ی اضافه)",
    "🎁 <b>Invite friends</b>\n\nYour personal link:\n{link}\n\nFor every friend who joins with it you get {bonus} credits.{invitee_line}\n\n👥 Invited: {n} — credits earned: {earned}\n(each credit = one extra use)")
add("invite_invitee_line", "\nدوستت هم {b} اعتبار هدیه می‌گیره.", "\nYour friend also gets {b} credits.")
add("invite_off", "دعوت دوستان فعلاً غیرفعاله.", "Invites are currently off.")
add("invite_share_text", "🎬 رزومه‌ی هنری بساز و آگهی‌های بازیگرگیری ببین:", "🎬 Build your acting resume and browse casting calls:")
add("ref_joined_referrer", "🎉 یه دوست با لینکت وارد شد! {bonus} اعتبار گرفتی.", "🎉 A friend joined with your link! You got {bonus} credits.")
add("ref_joined_invitee", "🎁 {bonus} اعتبار هدیه گرفتی!", "🎁 You received {bonus} bonus credits!")

# =============================================================== admin
add("a_title", "🛠 <b>پنل مدیریت</b>", "🛠 <b>Admin panel</b>")
add("a_bound", "👑 تو به‌عنوان مالک ربات ثبت شدی (شناسه‌ی {uid}). /admin رو بزن.", "👑 You are registered as the bot owner (ID {uid}). Send /admin.")
add("a_denied", "⛔ این بخش فقط برای مالک ربات است.", "⛔ This section is for the owner only.")
add("a_back", "⬅️ برگشت", "⬅️ Back"); add("a_not_found", "پیدا نشد 🤷", "Not found 🤷")
add("a_bad_num", "عدد معتبر بنویس 🙂", "Please send a valid number 🙂")
for _k, _fa, _en in [("stats", "📊 آمار", "📊 Stats"), ("users", "👥 کاربران", "👥 Users"), ("resumes", "🎭 رزومه‌ها / جستجو", "🎭 Resumes / search"),
                     ("calls", "🎬 ثبت‌نام‌های تولید", "🎬 Production sign-ups"), ("export", "📤 خروجی (Export)", "📤 Export"), ("bc", "📣 پیام همگانی", "📣 Broadcast"),
                     ("prices", "💎 پلن‌ها", "💎 Plans"), ("ads", "📢 تبلیغات", "📢 Ads"), ("limits", "⚙️ محدودیت‌ها", "⚙️ Limits & settings"),
                     ("ref", "🎁 دعوت‌ها", "🎁 Referrals"), ("faq", "❓ سؤال‌های رایج", "❓ FAQ"), ("support", "📞 پشتیبانی", "📞 Support contacts"),
                     ("admins", "👮 مدیران", "👮 Admins"), ("usearch", "🔎 جستجوی کاربر", "🔎 Search users"), ("msg", "✉️ پیام به کاربر", "✉️ Message user"),
                     ("grant", "💎 اعطای پلن", "💎 Grant plan"), ("credits", "🎟 افزودن اعتبار", "🎟 Add credits"), ("revoke", "↩️ لغو پلن", "↩️ Revoke plan"),
                     ("ban1", "🚫 مسدود کردن", "🚫 Ban"), ("unban1", "✅ رفع مسدودی", "✅ Unban"), ("promote", "👮 ارتقا به مدیر", "👮 Promote to admin"),
                     ("demote", "🔻 حذف از مدیران", "🔻 Remove admin"), ("view_resume", "🎭 دیدن رزومه", "🎭 View resume"), ("view_user", "👤 کاربر", "👤 User")]:
    add("a_b_" + _k, _fa, _en)
add("a_stats", "📊 <b>آمار</b>\n\n👥 کاربران: {users} (فعال ۷ روز: {active})\n🚫 مسدود: {banned}\n🎭 رزومه‌ی کامل: {resumes} (عمومی: {public}, ⭐ {featured})\n📝 پیش‌نویس: {drafts}\n🖼 عکس‌ها: {photos}\n🎬 تولید تایید‌شده: {casting} (در انتظار: {casting_pending})\n📋 آگهی‌ها: {calls} (باز: {calls_open})\n📥 واردشده در انتظار تایید: {imp_pending}\n📨 درخواست‌ها: {apps}\n💎 دارنده‌ی پلن: {premium}\n🎁 دعوت‌ها: {refs}",
    "📊 <b>Stats</b>\n\n👥 Users: {users} (active 7d: {active})\n🚫 Banned: {banned}\n🎭 Complete resumes: {resumes} (public: {public}, ⭐ {featured})\n📝 Drafts: {drafts}\n🖼 Photos: {photos}\n🎬 Approved productions: {casting} (pending: {casting_pending})\n📋 Calls: {calls} (open: {calls_open})\n📥 Imported pending: {imp_pending}\n📨 Applications: {apps}\n💎 Plan holders: {premium}\n🎁 Referrals: {refs}")
add("a_users", "👥 <b>کاربران</b> — صفحه {page} از {pages} ({total} نفر)", "👥 <b>Users</b> — page {page} of {pages} ({total})")
add("a_ask_usearch", "🔎 شناسه‌ی عددی، @یوزرنیم یا بخشی از اسم رو بنویس:", "🔎 Send a numeric ID, @username or part of the name:")
add("a_found", "🔎 {n} نتیجه:", "🔎 {n} result(s):")
add("role_owner", "👑 مالک", "👑 Owner"); add("role_admin", "👮 مدیر", "👮 Admin"); add("role_user", "👤 کاربر", "👤 User")
add("cs_none", "ثبت‌نام نکرده", "not registered"); add("cs_pending", "در انتظار تایید ⏳", "pending ⏳"); add("cs_approved", "تایید‌شده ✅", "approved ✅"); add("cs_rejected", "رد‌شده ❌", "rejected ❌")
add("a_no_plan", "بدون پلن", "no plan")
add("a_ban_yes", "🚫 مسدود", "🚫 banned"); add("a_ban_no", "✅ فعال", "✅ active")
add("a_user", "👤 <b>{who}</b>\nنقش: {role}\n🎭 رزومه: {resume}\n🎬 حساب تولید: {casting}\n💎 پلن: {plan}\n🎟 اعتبار: {credits}\n🎁 دعوت‌ها: {refs}\nوضعیت: {ban}\n🕐 آخرین بازدید: {seen}",
    "👤 <b>{who}</b>\nRole: {role}\n🎭 Resume: {resume}\n🎬 Production account: {casting}\n💎 Plan: {plan}\n🎟 Credits: {credits}\n🎁 Invites: {refs}\nStatus: {ban}\n🕐 Last seen: {seen}")
add("a_ask_msg", "✉️ متن پیام برای {who} رو بنویس (از طرف ربات ارسال می‌شه):\n(/cancel برای انصراف)", "✉️ Type the message for {who} (sent via the bot):\n(/cancel to abort)")
add("a_msg_sent", "✅ پیام برای {who} فرستاده شد.", "✅ Message sent to {who}."); add("a_msg_fail", "⚠️ نتونستم پیام رو برای {who} بفرستم.", "⚠️ Couldn't deliver the message to {who}.")
add("a_msg_banned", "این کاربر مسدوده.", "That user is banned.")
add("u_msg_from_admin", "📩 <b>پیام از مدیریت</b>\n\n{text}", "📩 <b>Message from the admins</b>\n\n{text}")
add("a_grant_choice", "💎 برای {who} کدوم پلن فعال بشه؟\n(پرداخت بیرون از ربات انجام شده باشه)", "💎 Which plan for {who}?\n(payment should have been done outside the bot)")
add("a_grant_plan", "💎 فعال‌سازی «{title}»", "💎 Activate “{title}”")
add("a_done_plan", "✅ پلن «{title}» برای {who} فعال شد.", "✅ Plan “{title}” activated for {who}.")
add("u_plan", "💎 پلن «{title}» برات فعال شد (تا {until}). ممنون 💖", "💎 Plan “{title}” is now active for you (until {until}). Thank you 💖")
add("a_done_revoke", "↩️ پلن {who} لغو شد.", "↩️ Plan of {who} revoked."); add("u_revoked", "پلن تو لغو شد.", "Your plan was revoked.")
add("a_ask_num", "🔢 چند اعتبار؟ (عدد منفی = کم کردن)", "🔢 How many credits? (negative = subtract)")
add("a_done_credits", "✅ {n} اعتبار برای {who} ثبت شد.", "✅ {n} credits applied to {who}."); add("u_credits", "🎟 {n} اعتبار بهت اضافه شد!", "🎟 {n} credits were added to your account!")
add("a_done_ban", "🚫 {who} مسدود شد.", "🚫 {who} banned."); add("a_done_unban", "✅ مسدودی {who} برداشته شد.", "✅ {who} unbanned.")
add("a_pending_head", "🎬 <b>ثبت‌نام‌های در انتظار تایید</b>", "🎬 <b>Pending production sign-ups</b>"); add("a_no_pending", "موردی در انتظار نیست ✅", "Nothing pending ✅")
add("a_casting_done", "{who}: {s}", "{who}: {s}")
add("a_ask_rid", "🆔 شناسه‌ی رزومه (مثل R000012 یا 12) رو بنویس:", "🆔 Send the resume ID (like R000012 or 12):")
add("b_hide_admin", "🚫 مخفی", "🚫 Hide"); add("b_unhide", "👀 نمایش", "👀 Unhide"); add("b_feature", "⭐ ویژه کن", "⭐ Feature"); add("b_unfeature", "☆ ویژه نباشه", "☆ Unfeature")
add("b_del_admin", "🗑 حذف", "🗑 Delete")
add("a_resume_hidden", "🚫 رزومه {id} مخفی شد.", "🚫 Resume {id} hidden."); add("a_resume_unhidden", "👀 رزومه {id} دوباره نمایش داده می‌شه.", "👀 Resume {id} is visible again.")
add("a_resume_featured", "⭐ رزومه {id} ویژه شد.", "⭐ Resume {id} featured."); add("a_resume_unfeatured", "☆ ویژه‌بودن رزومه {id} برداشته شد.", "☆ Resume {id} unfeatured.")
add("a_resume_del_confirm", "رزومه {id} برای همیشه پاک بشه؟", "Delete resume {id} permanently?"); add("a_resume_deleted", "🗑 رزومه {id} پاک شد.", "🗑 Resume {id} deleted.")
add("u_featured", "⭐ رزومه‌ات ویژه شد و بالاتر نمایش داده می‌شه!", "⭐ Your resume was featured and will be shown higher!")
add("u_resume_removed", "رزومه‌ات توسط مدیریت حذف شد. برای اطلاعات بیشتر با پشتیبانی تماس بگیر.", "Your resume was removed by the admins. Contact support for details.")
add("a_call_featured", "⭐ آگهی ویژه شد.", "⭐ Call featured."); add("a_call_unfeatured", "☆ آگهی از ویژه خارج شد.", "☆ Call unfeatured.")
add("a_call_toggled", "🙈 وضعیت آگهی تغییر کرد.", "🙈 Call visibility toggled."); add("a_call_deleted", "🗑 آگهی پاک شد.", "🗑 Call deleted.")
# settings / referrals
add("a_settings", "⚙️ <b>محدودیت‌ها و تنظیمات</b>\n(-1 = نامحدود)", "⚙️ <b>Limits & settings</b>\n(-1 = unlimited)")
add("a_s_views", "👁 دیدن رزومه رایگان/ماه: {n}", "👁 Free resume views / month: {n}"); add("a_s_apps", "📨 درخواست رایگان/ماه: {n}", "📨 Free applications / month: {n}")
add("a_s_posts", "📢 آگهی رایگان/ماه: {n}", "📢 Free call postings / month: {n}")
add("a_s_search_casting", "🔍 جستجو برای تولید تایید‌شده: {s}", "🔍 Search for approved productions: {s}")
add("a_s_approval", "✅ تایید دستی ثبت‌نام تولید: {s}", "✅ Manual approval of productions: {s}")
add("a_s_export_extra", "📤 خروجی برای مدیران دیگر: {s}", "📤 Export for other admins: {s}")
add("a_s_ask_num", "🔢 عدد جدید رو بنویس:", "🔢 Send the new number:"); add("a_s_saved", "✅ ذخیره شد", "✅ Saved")
add("a_ref", "🎁 <b>دعوت‌ها</b>\n\nوضعیت: {s}\nکل دعوت‌ها: {total}\nاعتبار دعوت‌کننده: {rb}\nاعتبار دعوت‌شده: {ib}\n\n🏆 برترین‌ها:\n{top}",
    "🎁 <b>Referrals</b>\n\nStatus: {s}\nTotal invites: {total}\nInviter bonus: {rb}\nInvitee bonus: {ib}\n\n🏆 Top:\n{top}")
add("a_ref_none", "هنوز کسی نیست", "nobody yet"); add("a_s_reftoggle", "🔁 دعوت‌ها: {s}", "🔁 Referrals: {s}")
add("a_s_rb", "✏️ اعتبار دعوت‌کننده", "✏️ Inviter bonus"); add("a_s_ib", "✏️ اعتبار دعوت‌شده", "✏️ Invitee bonus")
# broadcast
add("a_bc_who", "📣 پیام همگانی برای چه کسانی؟", "📣 Broadcast to whom?")
add("aud_all", "👥 همه", "👥 Everyone"); add("aud_resume", "🎭 دارندگان رزومه", "🎭 Users with a resume"); add("aud_casting", "🎬 تولید/کارگردان‌ها", "🎬 Productions/directors")
add("a_bc_ask", "✍️ متن پیام رو بنویس:\n(/cancel برای انصراف)", "✍️ Type the message:\n(/cancel to abort)")
add("a_bc_confirm", "📣 این پیام برای {n} نفر فرستاده می‌شه:\n\n{text}\n\nارسال بشه؟", "📣 This will be sent to {n} people:\n\n{text}\n\nSend?")
add("a_bc_none", "پیامی در انتظار نیست.", "Nothing pending."); add("a_bc_sending", "⏳ در حال ارسال...", "⏳ Sending...")
add("a_bc_cancel", "لغو شد 👌", "Cancelled 👌"); add("a_bc_done", "✅ ارسال شد: {ok} — ناموفق: {fail}", "✅ Sent: {ok} — failed: {fail}")
# export
add("exp_working", "⏳ در حال ساخت خروجی...", "⏳ Building the export...")
add("exp_done", "📤 خروجی آماده شد: {n} رزومه، {photos} فایل ZIP عکس (دانلود ناموفق عکس: {bad}).\nفایل‌ها شامل اطلاعات شخصی‌اند؛ محرمانه نگه دارشون. راهنمای ساختار: SCHEMA.md",
    "📤 Export ready: {n} resumes, {photos} photo ZIP file(s) (failed photo downloads: {bad}).\nFiles contain personal data — keep them private. Structure: SCHEMA.md")
add("exp_fail", "❌ ساخت خروجی ناموفق بود (جزئیات در لاگ).", "❌ Export failed (see log).")
# admins / support / faq
add("ad_menu", "👮 <b>مدیریت مدیران</b>\n\n👑 مالک: {owner}\n\n👮 مدیران:\n{lines}\n\nمدیران اضافه: آمار، کاربران، رزومه‌ها و تایید ثبت‌نام‌ها؛ بقیه‌ی بخش‌ها فقط برای مالکه.",
    "👮 <b>Manage admins</b>\n\n👑 Owner: {owner}\n\n👮 Admins:\n{lines}\n\nExtra admins get stats, users, resumes and approvals; everything else is owner-only.")
add("ad_none", "—", "—"); add("ad_add", "➕ افزودن مدیر", "➕ Add admin"); add("ad_owner", "🔁 تغییر مالک", "🔁 Change owner")
add("ad_ask_add", "🆔 شناسه‌ی عددی یا @یوزرنیم مدیر جدید رو بفرست (باید قبلاً ربات رو استارت کرده باشه):\n(/cancel برای انصراف)", "🆔 Send the new admin's numeric ID or @username (they must have started the bot):\n(/cancel to abort)")
add("ad_added", "✅ {who} مدیر شد.", "✅ {who} is now an admin."); add("ad_removed", "✅ {who} از مدیران حذف شد.", "✅ {who} removed from admins.")
add("ad_is_owner", "این کاربر مالکه یا پیدا نشد.", "That user is the owner or unknown.")
add("ad_notify_new", "👮 تو مدیر ربات شدی! /admin رو بزن.", "👮 You are now an admin of this bot! Send /admin."); add("ad_notify_removed", "دسترسی مدیریتت برداشته شد.", "Your admin access was removed.")
add("ad_owner_ask", "🔁 شناسه‌ی عددی یا @یوزرنیم مالک جدید رو بفرست:\n⚠️ بعد از تایید، تو دیگه مالک نیستی.\n(/cancel برای انصراف)", "🔁 Send the new owner's numeric ID or @username:\n⚠️ After confirming you will no longer be the owner.\n(/cancel to abort)")
add("ad_owner_confirm", "مالکیت به {who} منتقل بشه؟", "Transfer ownership to {who}?"); add("ad_owner_done", "✅ مالک جدید: {who}", "✅ New owner: {who}")
add("ad_owner_notify_new", "👑 تو حالا مالک ربات هستی! /admin رو بزن.", "👑 You are now the owner of the bot! Send /admin."); add("ad_owner_same", "این کاربر همین الان مالکه.", "That user is already the owner.")
add("su_menu", "📞 <b>پشتیبانی</b>\n\nاصلی: @{p}\nپشتیبان دوم: {b}", "📞 <b>Support contacts</b>\n\nPrimary: @{p}\nBackup: {b}")
add("su_none", "—", "—"); add("su_b_primary", "✏️ اصلی", "✏️ Primary"); add("su_b_backup", "✏️ پشتیبان دوم", "✏️ Backup"); add("su_b_clear", "🗑 حذف پشتیبان دوم", "🗑 Remove backup")
add("su_ask", "@یوزرنیم رو بفرست:", "Send the @username:"); add("su_bad", "یوزرنیم معتبر نیست (۵ تا ۳۲ حرف انگلیسی/عدد/_).", "Invalid username (5–32 letters/digits/_).")
add("su_saved", "✅ ذخیره شد", "✅ Saved"); add("su_cleared", "✅ پشتیبان دوم حذف شد", "✅ Backup removed")
add("fq_mgr", "❓ <b>سؤال‌های رایج</b> ({n} مورد)", "❓ <b>FAQ</b> ({n} items)"); add("fq_add", "➕ سؤال جدید", "➕ New question")
add("fq_ask_q", "سؤال (فارسی) رو بنویس:", "Type the question (Persian):"); add("fq_ask_a", "پاسخ (فارسی) رو بنویس:", "Type the answer (Persian):")
add("fq_ask_field", "متن جدید رو بنویس:", "Type the new text:"); add("fq_saved", "✅ ذخیره شد", "✅ Saved"); add("fq_deleted", "🗑 پاک شد", "🗑 Deleted")
add("fq_qfa", "✏️ سؤال فارسی", "✏️ Question (fa)"); add("fq_afa", "✏️ پاسخ فارسی", "✏️ Answer (fa)"); add("fq_qen", "✏️ سؤال انگلیسی", "✏️ Question (en)"); add("fq_aen", "✏️ پاسخ انگلیسی", "✏️ Answer (en)")
# plans admin
add("pp_mgr", "💎 <b>مدیریت پلن‌ها</b>\n(فقط نمایشی؛ پلن رو ادمین دستی به کاربر می‌ده)\n\n{lines}", "💎 <b>Manage plans</b>\n(display only; an admin grants a plan manually)\n\n{lines}")
add("pp_line", "{pos}. {star}<b>{title}</b> — {price}{dur}\n   👁 {views} · 📨 {apps} · 📢 {posts} · ⏳ {days} روز{hid}", "{pos}. {star}<b>{title}</b> — {price}{dur}\n   👁 {views} · 📨 {apps} · 📢 {posts} · ⏳ {days} days{hid}")
add("pp_hidden", "  (مخفی: قیمت ندارد)", "  (hidden: no price)"); add("pp_none", "هنوز پلنی نیست.", "No plans yet.")
add("pp_add", "➕ پلن جدید", "➕ New plan"); add("pp_full", "به سقف {n} مورد رسیدی.", "Limit of {n} reached."); add("pp_added", "✅ پلن اضافه شد", "✅ Plan added")
add("pp_deleted", "🗑 پاک شد", "🗑 Deleted"); add("pp_saved", "✅ ذخیره شد", "✅ Saved"); add("pp_gone", "این پلن دیگه نیست.", "That plan no longer exists.")
add("pp_skip", "⏭ رد شدن", "⏭ Skip")
add("pp_ask_title", "نام پلن؟", "Plan name?"); add("pp_ask_price", "قیمت (متن آزاد، مثلاً «۱۵۰ هزار تومان»)؟", "Price (free text)?")
add("pp_ask_dur", "مدت نمایشی (مثلاً «ماهانه»)؟", "Display duration (e.g. “monthly”)?"); add("pp_ask_feat", "ویژگی‌ها (با | جدا کن)؟", "Features (separate with |)?")
add("pp_ask_views", "چند دیدن رزومه‌ی کامل در ماه؟ (0 = ندارد، -1 = نامحدود)", "Resume views per month? (0 = none, -1 = unlimited)")
add("pp_ask_apps", "چند درخواست به آگهی در ماه؟ (0 = ندارد، -1 = نامحدود)", "Applications per month? (0 = none, -1 = unlimited)")
add("pp_ask_posts", "چند آگهی در ماه؟ (0 = ندارد، -1 = نامحدود)", "Call postings per month? (0 = none, -1 = unlimited)")
add("pp_ask_days", "پلن بعد از فعال‌سازی چند روز اعتبار داره؟ (0 = بدون انقضا)", "How many days does a grant last? (0 = no expiry)")
add("pp_ask_pop", "⭐ به‌عنوان «محبوب» نشون داده بشه؟", "⭐ Show as “Popular”?")
add("pp_edit", "✏️ <b>ویرایش پلن</b>\n\n{line}\nویژگی‌ها: {feats}", "✏️ <b>Edit plan</b>\n\n{line}\nFeatures: {feats}")
for _k, _fa, _en in [("title", "نام", "Name"), ("price", "قیمت", "Price"), ("dur", "مدت", "Duration"), ("feat", "ویژگی‌ها (- = حذف)", "Features (- = clear)"),
                     ("views", "دیدن رزومه", "Views"), ("apps", "درخواست", "Applications"), ("posts", "آگهی", "Postings"), ("days", "روزِ اعتبار", "Grant days")]:
    add("pp_e_" + _k, "✏️ " + _fa, "✏️ " + _en)
add("pp_e_pop", "⭐ محبوب کن", "⭐ Mark popular"); add("pp_e_unpop", "☆ محبوب نباشه", "☆ Unmark popular")
# ads admin
add("ads_mgr", "📢 <b>مدیریت تبلیغات</b>\n📰 = بین کارها، 📌 = خط حامی در منوی اصلی\n\n{lines}", "📢 <b>Manage ads</b>\n📰 = between actions, 📌 = sponsor line in the main menu\n\n{lines}")
add("ads_none", "هنوز تبلیغی نیست.", "No ads yet."); add("ads_add", "➕ تبلیغ جدید", "➕ New ad"); add("ads_toggle", "🔁 تبلیغات: {s}", "🔁 Ads: {s}")
add("ads_every", "📰 هر {n} کار یک تبلیغ", "📰 One ad every {n} actions"); add("ads_bc", "📣 ارسال تبلیغ به کاربران", "📣 Broadcast an ad")
add("ads_ask_fa", "متن فارسی تبلیغ (می‌تونی همراه عکس بفرستی):", "Persian ad text (you may attach a photo):"); add("ads_ask_en", "متن انگلیسی تبلیغ:", "English ad text:")
add("ads_ask_photo", "عکس تبلیغ رو بفرست:", "Send the ad photo:"); add("ads_ask_url", "لینک (https://...) :", "Link (https://...):")
add("ads_ask_btn", "متن دکمه:", "Button text:"); add("ads_bad_url", "لینک باید با http:// یا https:// شروع بشه.", "The link must start with http:// or https://")
add("ads_added", "✅ تبلیغ اضافه شد", "✅ Ad added"); add("ads_deleted", "🗑 پاک شد", "🗑 Deleted"); add("ads_saved", "✅ ذخیره شد", "✅ Saved")
add("ads_edit", "📢 <b>تبلیغ #{id}</b>\n\n🇮🇷 {fa}\n🇬🇧 {en}\n🔗 {url}\n🔘 {btn}\n🖼 {photo}\n📍 جایگاه: {slot}\n👁 {views} · 🖱 {clicks}", "📢 <b>Ad #{id}</b>\n\n🇮🇷 {fa}\n🇬🇧 {en}\n🔗 {url}\n🔘 {btn}\n🖼 {photo}\n📍 Slot: {slot}\n👁 {views} · 🖱 {clicks}")
add("slot_feed", "📰 بین کارها", "📰 between actions"); add("slot_sponsor", "📌 حامی منوی اصلی", "📌 main-menu sponsor"); add("ads_slot_btn", "📍 جایگاه: {slot}", "📍 Slot: {slot}")
for _k, _fa, _en in [("fa", "متن فارسی", "Persian text"), ("en", "متن انگلیسی", "English text"), ("photo", "عکس", "Photo"), ("url", "لینک", "Link"), ("btn", "دکمه", "Button")]:
    add("ads_e_" + _k, "✏️ " + _fa, "✏️ " + _en)
add("ads_e_on", "⛔ غیرفعال کن", "⛔ Disable"); add("ads_e_off", "✅ فعال کن", "✅ Enable")
add("ads_e_track_on", "🖱 شمارش کلیک: روشن", "🖱 Click count: on"); add("ads_e_track_off", "🖱 شمارش کلیک: خاموش", "🖱 Click count: off")
add("ads_bc_pick", "کدوم تبلیغ؟", "Which ad?"); add("ads_bc_confirm", "تبلیغ #{id} برای {n} نفر (بدون دارندگان پلن و مدیران) فرستاده بشه؟", "Send ad #{id} to {n} people (excluding plan holders and admins)?")

# =============================================================== imported calls (channel importer)
add("imp_credit", "📡 منبع: @{ch} — <a href=\"{url}\">پست اصلی</a>", "📡 Source: @{ch} — <a href=\"{url}\">original post</a>")
add("imp_notice", "ℹ️ این آگهی از کانال عمومی @{ch} آورده شده؛ متن و اطلاعات تماس همان است که منتشر شده.", "ℹ️ Imported from the public channel @{ch}; text and contact details are exactly as published there.")
add("imp_gender", "👤 {v}", "👤 {v}"); add("imp_age", "🎂 سن: {v}", "🎂 Age: {v}")
add("imp_fee", "💰 {v}", "💰 {v}"); add("imp_deadline", "⏳ مهلت: {v}", "⏳ Deadline: {v}")
add("imp_posted", "🗓 تاریخ انتشار در منبع: {v}", "🗓 Posted at source: {v}")
add("b_direct_tg", "💬 تماس مستقیم: @{h}", "💬 Contact directly: @{h}"); add("b_direct_wa", "🟢 تماس مستقیم در واتساپ", "🟢 Contact directly on WhatsApp")
add("b_src_post", "🔗 پست اصلی", "🔗 Original post")
add("imp_contact_direct", "📞 برای این آگهی مستقیماً با خود آگهی‌دهنده تماس بگیر (مشخصات و رزومه را به همان روشی که در متن نوشته ارسال کن).", "📞 For this call, contact the poster directly (send your details/resume the way the text says).")
add("a_b_import", "📥 آگهی‌های واردشده", "📥 Imported calls")
add("a_imp_head", "📥 <b>آگهی‌های واردشده از @{ch}</b>\n\n⏳ در انتظار تایید: {pending}\n🟢 منتشرشده: {open}\n🙈 مخفی/بسته: {other}\n🗑 ردشده (حذف‌شده): {rejected}\n\n🤖 انتشار خودکار: {auto}\n🕒 آخرین همگام‌سازی: {last}\n\n⚠️ محتوا متعلق به صاحب کانال است؛ منبع و لینک پست همیشه نمایش داده می‌شود. بهتر است از صاحب کانال اجازه بگیرید.", "📥 <b>Imported calls from @{ch}</b>\n\n⏳ Pending approval: {pending}\n🟢 Published: {open}\n🙈 Hidden/closed: {other}\n🗑 Rejected (deleted): {rejected}\n\n🤖 Auto-publish: {auto}\n🕒 Last sync: {last}\n\n⚠️ The content belongs to the channel owner; the source and post link are always shown. Please get the channel owner's permission.")
add("a_imp_review", "👀 مرور آگهی‌های در انتظار", "👀 Review pending calls"); add("a_imp_sync", "🔄 همگام‌سازی همین حالا", "🔄 Sync now")
add("a_imp_auto", "🤖 انتشار خودکار: {s}", "🤖 Auto-publish: {s}")
add("a_imp_approve_all", "✅ تایید همه‌ی بدون هشدار ({n})", "✅ Approve all without warnings ({n})")
add("a_imp_none", "هیچ آگهی در انتظار تایید نیست ✅", "No imported calls are waiting ✅")
add("a_imp_list_head", "📥 <b>در انتظار تایید</b> — {n} مورد (صفحه‌ی {p} از {pages})", "📥 <b>Pending approval</b> — {n} items (page {p} of {pages})")
add("a_imp_approved", "✅ منتشر شد.", "✅ Published."); add("a_imp_deleted", "🗑 حذف شد و دوباره وارد نمی‌شود.", "🗑 Deleted; it will not be imported again.")
add("a_imp_hidden", "🙈 مخفی شد.", "🙈 Hidden.")
add("a_imp_approve_all_ok", "✅ {n} آگهی منتشر شد.", "✅ {n} calls published."); add("a_imp_approve_all_ask", "{n} آگهیِ بدون هشدار منتشر شود؟", "Publish {n} calls without warnings?")
add("a_imp_sync_start", "🔄 همگام‌سازی شروع شد…", "🔄 Sync started…")
add("a_imp_sync_done", "✅ همگام‌سازی تمام شد.\nپست‌های جدید: {found}\nآگهی‌های در انتظار تایید: {pending}\nمنتشرشده‌ی خودکار: {open}\nتکراری: {reposts} · غیرآگهی: {noise} · منقضی: {expired}\nخطا: {errors}", "✅ Sync done.\nNew posts: {found}\nPending: {pending}\nAuto-published: {open}\nDuplicates: {reposts} · not calls: {noise} · expired: {expired}\nErrors: {errors}")
add("a_imp_sync_busy", "همگام‌سازی در حال اجراست.", "A sync is already running.")
add("a_imp_new", "📥 {n} آگهی جدید از کانال منبع برای بررسی آماده است.", "📥 {n} new calls from the source channel are ready for review.")
add("a_imp_flags", "⚠️ نیاز به بررسی: {f}", "⚠️ Needs a look: {f}")
add("flag_no_contact", "راه تماس پیدا نشد", "no contact found"); add("flag_roles_unclear", "نقش‌ها مشخص نیست", "roles unclear")
add("flag_maybe_course", "شاید کارگاه/دوره باشد", "may be a course/workshop"); add("flag_no_city", "شهر مشخص نیست", "no city")
add("a_imp_edit", "✏️ کدام بخش را ویرایش کنیم؟", "✏️ Which part to edit?")
add("a_imp_f_title", "عنوان", "Title"); add("a_imp_f_city", "شهر", "City"); add("a_imp_f_contact", "تماس", "Contact"); add("a_imp_f_details", "متن", "Text")
add("a_imp_ask_field", "متن جدید را بفرست:", "Send the new value:"); add("a_imp_saved", "✅ ذخیره شد.", "✅ Saved.")
add("a_imp_never", "هنوز نه", "not yet"); add("b_imp_edit", "✏️ ویرایش", "✏️ Edit"); add("b_imp_approve", "✅ تایید و انتشار", "✅ Approve & publish")
