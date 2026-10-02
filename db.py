"""SQLite (WAL) storage: normalized tables + tiny helpers. One connection per thread, explicit transactions."""
import os, json, time, sqlite3, threading, logging
from contextlib import contextmanager
import config

log = logging.getLogger("db")
_path = config.DB_PATH
_local = threading.local()
_clock = time.time            # tests may replace db._clock

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY,                -- Telegram numeric id
  username TEXT, name TEXT, lang TEXT, language_code TEXT,
  first_seen TEXT, last_seen TEXT,
  banned INTEGER NOT NULL DEFAULT 0, is_admin INTEGER NOT NULL DEFAULT 0,
  casting_status TEXT NOT NULL DEFAULT 'none',   -- none | pending | approved | rejected
  casting_name TEXT, casting_about TEXT,
  consent_at TEXT,
  referred_by INTEGER, ref_count INTEGER NOT NULL DEFAULT 0, ref_earned INTEGER NOT NULL DEFAULT 0,
  credits INTEGER NOT NULL DEFAULT 0,
  plan_id INTEGER, plan_until INTEGER NOT NULL DEFAULT 0,   -- epoch seconds; 0 = none, -1 = no expiry
  actions_since_ad INTEGER NOT NULL DEFAULT 0,
  awaiting TEXT, await_data TEXT,
  search_filters TEXT
);
CREATE TABLE IF NOT EXISTS resumes(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
  status TEXT NOT NULL DEFAULT 'draft',          -- draft | complete
  visibility TEXT NOT NULL DEFAULT 'public',     -- public | hidden   (chosen by the owner)
  admin_hidden INTEGER NOT NULL DEFAULT 0,       -- hidden by an admin
  featured INTEGER NOT NULL DEFAULT 0,           -- highlighted by an admin
  wiz_step INTEGER NOT NULL DEFAULT 0,
  full_name_fa TEXT, stage_name TEXT, gender TEXT, birth_year INTEGER, city TEXT,
  height_cm INTEGER, weight_kg INTEGER, hair_color TEXT, eye_color TEXT, skin_tone TEXT,
  experience_level TEXT, skills_extra TEXT, education TEXT, awards TEXT,
  phone TEXT, telegram_username TEXT, email TEXT, instagram TEXT, portfolio_links TEXT,
  availability TEXT, travel TEXT, expected_fee TEXT, bio TEXT, demo_reel_url TEXT,
  name_norm TEXT NOT NULL DEFAULT '', city_norm TEXT NOT NULL DEFAULT '', search_text TEXT NOT NULL DEFAULT '',
  created_at TEXT, updated_at TEXT, published_at TEXT
);
CREATE TABLE IF NOT EXISTS work_history(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
  position INTEGER NOT NULL DEFAULT 0,
  title TEXT, work_type TEXT, role TEXT, year INTEGER, director_company TEXT
);
CREATE TABLE IF NOT EXISTS skills(
  resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
  category TEXT NOT NULL, code TEXT NOT NULL,
  PRIMARY KEY(resume_id, category, code)
);
CREATE TABLE IF NOT EXISTS roles(
  resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  PRIMARY KEY(resume_id, role)
);
CREATE TABLE IF NOT EXISTS media(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
  seq INTEGER NOT NULL, kind TEXT NOT NULL DEFAULT 'photo',
  telegram_file_id TEXT, telegram_unique_id TEXT,
  local_path TEXT,                              -- relative to the media dir, e.g. R000012_01.jpg
  bytes INTEGER, sha256 TEXT, is_primary INTEGER NOT NULL DEFAULT 0, created_at TEXT
);
CREATE TABLE IF NOT EXISTS views(
  viewer_id INTEGER NOT NULL, resume_id INTEGER NOT NULL, period TEXT NOT NULL, created_at TEXT,
  PRIMARY KEY(viewer_id, resume_id, period)
);
CREATE TABLE IF NOT EXISTS plans(
  id INTEGER PRIMARY KEY AUTOINCREMENT, position INTEGER NOT NULL DEFAULT 0,
  title TEXT NOT NULL, price TEXT NOT NULL DEFAULT '', duration TEXT NOT NULL DEFAULT '',
  features TEXT NOT NULL DEFAULT '', popular INTEGER NOT NULL DEFAULT 0,
  views_month INTEGER NOT NULL DEFAULT 0, apps_month INTEGER NOT NULL DEFAULT 0, posts_month INTEGER NOT NULL DEFAULT 0,
  days INTEGER NOT NULL DEFAULT 30                -- how long a manual grant lasts (0 = no expiry)
);
CREATE TABLE IF NOT EXISTS ads(
  id INTEGER PRIMARY KEY AUTOINCREMENT, fa TEXT, en TEXT, photo TEXT, url TEXT, btn TEXT,
  slot TEXT NOT NULL DEFAULT 'feed',           -- feed (shown between actions) | sponsor (fixed line)
  enabled INTEGER NOT NULL DEFAULT 1, track INTEGER NOT NULL DEFAULT 0,
  views INTEGER NOT NULL DEFAULT 0, clicks INTEGER NOT NULL DEFAULT 0, created_at TEXT
);
CREATE TABLE IF NOT EXISTS calls(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  title TEXT, project_type TEXT, city TEXT, date_text TEXT, date_iso TEXT, details TEXT, contact TEXT,
  status TEXT NOT NULL DEFAULT 'open',            -- open | closed | hidden | pending (imported, awaiting admin approval)
  featured INTEGER NOT NULL DEFAULT 0, period TEXT, created_at TEXT,
  source TEXT, source_post INTEGER, source_url TEXT, source_date TEXT, source_text TEXT,   -- imported calls only
  gender_text TEXT, age_text TEXT, fee_text TEXT, deadline_text TEXT, deadline_iso TEXT, contacts TEXT, flags TEXT
);
CREATE TABLE IF NOT EXISTS imports(                 -- every channel post we looked at (so deleted/noise posts are never re-imported)
  source TEXT NOT NULL, post_id INTEGER NOT NULL, kind TEXT NOT NULL,   -- call | noise | repost
  reason TEXT, call_id INTEGER, fingerprint TEXT, post_date TEXT, fetched_at TEXT,
  PRIMARY KEY(source, post_id)
);
CREATE TABLE IF NOT EXISTS call_roles(
  call_id INTEGER NOT NULL REFERENCES calls(id) ON DELETE CASCADE, role TEXT NOT NULL,
  PRIMARY KEY(call_id, role)
);
CREATE TABLE IF NOT EXISTS applications(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  call_id INTEGER NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL, resume_id INTEGER NOT NULL,
  period TEXT, created_at TEXT, UNIQUE(call_id, user_id)
);
CREATE INDEX IF NOT EXISTS ix_resumes_city ON resumes(city);
CREATE INDEX IF NOT EXISTS ix_resumes_status ON resumes(status, visibility, admin_hidden);
CREATE INDEX IF NOT EXISTS ix_calls_status ON calls(status, featured);
CREATE INDEX IF NOT EXISTS ix_media_resume ON media(resume_id, seq);
"""

def now():
    return int(_clock())

def now_iso(ts=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now() if ts is None else ts))

def period(ts=None):
    """Quota month, in the box's local time zone (Asia/Tehran)."""
    return time.strftime("%Y-%m", time.localtime(now() if ts is None else ts))

def this_year():
    return time.localtime(now()).tm_year

def set_path(p):
    global _path
    _path = p
    close_all()

def get_path():
    return _path

def close_all():
    c = getattr(_local, "c", None)
    if c:
        try: c[1].close()
        except Exception: pass
    _local.c = None

CALL_EXTRA_COLS = (("source", "TEXT"), ("source_post", "INTEGER"), ("source_url", "TEXT"), ("source_date", "TEXT"), ("source_text", "TEXT"),
                   ("gender_text", "TEXT"), ("age_text", "TEXT"), ("fee_text", "TEXT"), ("deadline_text", "TEXT"),
                   ("deadline_iso", "TEXT"), ("contacts", "TEXT"), ("flags", "TEXT"))

def _migrate(cn):
    """Add the imported-call columns to databases created before the importer existed."""
    have = {r[1] for r in cn.execute("PRAGMA table_info(calls)").fetchall()}
    for col, typ in CALL_EXTRA_COLS:
        if col not in have: cn.execute(f"ALTER TABLE calls ADD COLUMN {col} {typ}")
    cn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_calls_source ON calls(source, source_post) WHERE source IS NOT NULL")

def conn():
    c = getattr(_local, "c", None)
    if c and c[0] == _path:
        return c[1]
    if c:
        try: c[1].close()
        except Exception: pass
    d = os.path.dirname(_path)
    if d:
        os.makedirs(d, exist_ok=True)
    new = not os.path.exists(_path)
    cn = sqlite3.connect(_path, timeout=30, isolation_level=None, check_same_thread=False)
    cn.row_factory = sqlite3.Row
    cn.execute("PRAGMA journal_mode=WAL")
    cn.execute("PRAGMA synchronous=NORMAL")
    cn.execute("PRAGMA foreign_keys=ON")
    cn.execute("PRAGMA busy_timeout=30000")
    cn.executescript(SCHEMA)
    _migrate(cn)
    if new:
        try: os.chmod(_path, 0o600)
        except OSError: pass
    _local.c = (_path, cn)
    _local.depth = 0
    return cn

@contextmanager
def tx():
    cn = conn()
    depth = getattr(_local, "depth", 0)
    if depth:
        _local.depth = depth + 1
        try: yield cn
        finally: _local.depth -= 1
        return
    cn.execute("BEGIN IMMEDIATE")
    _local.depth = 1
    try:
        yield cn
        cn.execute("COMMIT")
    except BaseException:
        cn.execute("ROLLBACK")
        raise
    finally:
        _local.depth = 0

def q(sql, args=()):
    return [dict(r) for r in conn().execute(sql, args).fetchall()]

def q1(sql, args=()):
    r = conn().execute(sql, args).fetchone()
    return dict(r) if r else None

def val(sql, args=(), default=None):
    r = conn().execute(sql, args).fetchone()
    return default if r is None or r[0] is None else r[0]

def ex(sql, args=()):
    return conn().execute(sql, args)

# ---------------- meta (JSON values) ----------------
def meta_get(key, default=None):
    r = conn().execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    if r is None:
        return default
    try:
        return json.loads(r[0])
    except Exception:
        return default

def meta_set(key, value):
    conn().execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                   (key, json.dumps(value, ensure_ascii=False)))

def init():
    """Create schema + first-run defaults (owner id preset, default plans)."""
    conn()
    with tx():
        if meta_get("schema_version") is None:
            meta_set("schema_version", 1)
            meta_set("owner_id", config.OWNER_ID)
            meta_set("support", {"primary": config.DEFAULT_SUPPORT_PRIMARY, "backup": config.DEFAULT_SUPPORT_BACKUP})
