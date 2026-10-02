# Clapper / کلاکت — data schema (v1)

Everything the bot stores lives in **one SQLite file** (`cast.db`, WAL mode) plus **photo files** in `media/`.
All dates are **ISO 8601 UTC** strings (`2026-09-30T16:04:05Z`), except `calls.date_iso` (a plain `YYYY-MM-DD`, Gregorian).
Text is UTF-8; Persian text is stored as typed (ی/ک unified, digits kept as the user wrote them; numbers in numeric
columns are always ASCII integers). Enumerated fields hold **stable English codes** (listed at the bottom and in `resumes.json → enums`
with fa/en labels), never localized text.

Personal data warning: exports contain phone numbers, e-mails and photos. Keep them private, and delete rows of users who asked to be deleted.

## Stable IDs
| entity | in DB | in exports |
|---|---|---|
| resume | `resumes.id` (integer) | `R000012` (`R` + 6 digits) |
| work entry | `work_history.id` | `W000034` |
| media | `media.id` | `M000056` |
| casting call | `calls.id` | `C000007` |
| Telegram user | `users.id` = Telegram numeric id | `user_id` (integer) |

Photo files are named `R<resume id>_<seq>.jpg` (e.g. `R000012_01.jpg`) — the name never changes, `seq` starts at 1 and is per resume.

## Tables (SQLite)
### `resumes` — one row per person (UNIQUE `user_id`)
`id, user_id, status (draft|complete), visibility (public|hidden), admin_hidden (0/1), featured (0/1), wiz_step,`
`full_name_fa, stage_name, gender, birth_year (Gregorian int), city (Persian name), height_cm, weight_kg, hair_color, eye_color, skin_tone,`
`experience_level, skills_extra (free text), education, awards, phone, telegram_username (no @), email, instagram (username),`
`portfolio_links (JSON array of URLs), availability, travel, expected_fee (free text), bio, demo_reel_url,`
`name_norm, city_norm, search_text (internal search index — ignore on import), created_at, updated_at, published_at`

Only resumes with `status='complete'` were confirmed by their owner. Import `visibility='public' AND admin_hidden=0` if you want only what the bot itself shows.
Age is not stored: `age = current_year − birth_year`.

### `roles` — (resume_id, role) multi-select; `role` ∈ role codes
### `skills` — (resume_id, category, code) multi-select; languages are skills with `category='language'`
### `work_history` — many per resume
`id, resume_id, position, title, work_type, role (free text), year (Gregorian int), director_company`
### `media` — many per resume
`id, resume_id, seq, kind ('photo'), telegram_file_id, telegram_unique_id, local_path (file name inside media/, may be NULL if the download failed),`
`bytes, sha256, is_primary (0/1), created_at`
> `telegram_file_id` only works with the same bot token and may expire; the file in `media/` (and the ZIP) is the durable copy. `sha256` lets you verify it.
### `users` — Telegram accounts (id, username, name, lang, banned, is_admin, casting_status, casting_name, plan_id/plan_until, credits, referral counters, consent_at …)
### `calls`, `call_roles`, `applications` — casting calls
`calls(id, user_id, title, project_type, city, date_text, date_iso, details, contact, status open|closed|hidden, featured, created_at)`,
`call_roles(call_id, role)`, `applications(id, call_id, user_id, resume_id, created_at)`
### `plans`, `ads`, `views`, `meta` — bot configuration/monetization (not needed for a website import)

## Export files (admin button «📤 Export» or `python3 export.py`)
| file | content |
|---|---|
| `resumes.csv` | flat, **one row per resume**, UTF-8 with BOM (Excel-friendly). List fields joined with `" | "`; `work_history_json` is a JSON array; text starting with `= @ + -` is prefixed with `'` (spreadsheet formula safety) |
| `resumes.json` | nested full structure + `enums` (code → fa/en labels) + `schema_version` |
| `photos.zip` (or `photos-part1.zip`, … if > 45 MB) | `photos/R000012_01.jpg` … |
| `calls.json` | casting calls with roles and applicants (`resume_id` references); imported calls have `imported: true` + `source` {channel, post_url, post_date, gender, age, fee, deadline, contacts_as_published, credit} |
| `SCHEMA.md` | this file |

### `resumes.csv` columns
`resume_id, user_id, telegram_username_account, status, visibility, admin_hidden, featured, full_name_fa, stage_name, gender, birth_year, age, city,`
`height_cm, weight_kg, hair_color, eye_color, skin_tone, roles, experience_level, skills, languages, skills_extra, education, awards, phone,`
`telegram_username, email, instagram, portfolio_links, availability, travel, expected_fee, bio, demo_reel_url, work_history_count,`
`work_history_json, photo_count, photo_files, photo_file_ids, created_at, updated_at, published_at`

* `roles`: `actor | director` · `skills`: `category:code | category:code` (languages excluded) · `languages`: `persian | english`
* `photo_files`: `photos/R000012_01.jpg | photos/R000012_02.jpg` (paths inside the ZIP)

### `resumes.json` shape
```json
{ "schema_version": 1, "exported_at": "2026-09-30T16:04:05Z", "count": 1,
  "enums": { "role": [{"code":"actor","fa":"بازیگر","en":"Actor"}], "skill": [{"category":"language","code":"english","fa":"انگلیسی","en":"English"}], "...": [] },
  "resumes": [ {
    "resume_id": "R000012", "user_id": 123456789, "account_username": "sara", "status": "complete", "visibility": "public",
    "admin_hidden": false, "featured": false,
    "personal": { "full_name_fa": "سارا احمدی", "stage_name": "Sara Ahmadi", "gender": "female", "birth_year": 1996, "age": 30, "city": "تهران" },
    "appearance": { "height_cm": 170, "weight_kg": 60, "hair_color": "black", "eye_color": "brown", "skin_tone": null },
    "roles": ["actor"], "experience_level": "intermediate",
    "skills": [ {"category": "acting", "code": "drama"}, {"category": "language", "code": "english"} ], "skills_extra": "ژونگلور",
    "work_history": [ {"id":"W000001","position":1,"title":"مرگ فروشنده","type":"theatre","role":"نقش اصلی","year":2023,"director_or_company":"علی رضایی"} ],
    "education": "...", "awards": "...",
    "contact": { "phone": "09121234567", "telegram_username": "sara", "email": "s@example.com", "instagram": "sara_actor", "portfolio_links": ["https://..."] },
    "availability": "full_time", "travel": "domestic", "expected_fee": "توافقی", "bio": "...", "demo_reel_url": "https://...",
    "media": [ {"id":"M000001","seq":1,"kind":"photo","file":"photos/R000012_01.jpg","telegram_file_id":"...","telegram_unique_id":"...","bytes":81234,"sha256":"...","is_primary":true,"created_at":"2026-09-30T16:00:00Z"} ],
    "created_at": "...", "updated_at": "...", "published_at": "..."
  } ] }
```

## Enumerations (codes)
* **gender**: `female, male, other`
* **role**: `actor, director, cinematographer, editor, sound, makeup, costume, set_design, lighting, writer, producer, assistant, other`
* **experience_level**: `beginner, intermediate, professional, veteran`
* **work_type**: `film, series, short, theatre, commercial, music_video, documentary, other`
* **hair_color**: `black, dark_brown, brown, light_brown, blonde, red, gray, white, dyed, bald, other`
* **eye_color**: `black, dark_brown, brown, hazel, green, blue, gray, other`
* **skin_tone**: `very_fair, fair, olive, wheat, tan, brown, dark`
* **availability**: `full_time, part_time, weekends, project, not_now`
* **travel**: `none, domestic, international`
* **skill categories**: `acting, singing, dancing, instrument, language, driving, sport, other` — the full code list (with labels) is in `resumes.json → enums.skill`.

## Import hints (WordPress / any site)
1. Create a custom post type «resume»; use `resume_id` as the unique key (idempotent re-imports: update if it exists).
2. Map `personal/appearance/contact` to post meta; `roles`, `skills` (and `languages`) to taxonomies using the codes as slugs and `enums` for the display names.
3. Upload each `media[].file` from the ZIP to the media library (attach to the post; `is_primary` → featured image). Verify with `sha256`.
4. Store `work_history` as a repeater/child records keyed by its `W…` id.
5. Only publish where `status='complete' AND visibility='public' AND admin_hidden=false`; honour deletions (a resume missing from a newer export was deleted by its owner or an admin).
6. With direct SQLite access you can skip the files entirely: `sqlite3 cast.db` (tables above; copy the DB while the bot is stopped or use `.backup`).
