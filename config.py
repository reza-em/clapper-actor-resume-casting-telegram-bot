"""Central constants. The bot name is a SINGLE constant here (not final: change BOT_NAME and restart;
the Telegram profile name/description is re-applied automatically)."""
import os

BOT_NAME = "کلاکت | Clapper"          # <- working name, change here only
BOT_NAME_FA = "کلاکت"
BOT_NAME_EN = "Clapper"

TOKEN_ENV = "CAST_TELEGRAM_BOT_TOKEN"

OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "example_owner")       # owner is auto-bound on the first message from this username
OWNER_ID = int(os.environ.get("OWNER_ID", "0") or 0)                 # numeric id, pre-bound on first database creation
DEFAULT_SUPPORT_PRIMARY = os.environ.get("SUPPORT_USERNAME", "example_owner")
DEFAULT_SUPPORT_BACKUP = ""

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("CAST_DB_PATH") or os.path.join(BASE, "cast.db")
MEDIA_DIR = os.environ.get("CAST_MEDIA_DIR") or os.path.join(BASE, "media")

MAX_PHOTO_BYTES = 10 * 1024 * 1024
ZIP_PART_BYTES = 45 * 1024 * 1024     # Telegram bots may upload up to 50 MB per file
PAGE_SIZE = 3
MAX_PHOTOS = 5

# ---- channel importer (casting calls from a public Telegram channel preview) ----
IMPORT_CHANNEL = "farakhan_iziy1"      # public channel; preview at https://t.me/s/<channel>
IMPORT_INTERVAL = 30 * 60              # periodic sync (seconds)
IMPORT_MAX_AGE_DAYS = 30               # posts without a published deadline older than this are skipped as stale
IMPORT_MAX_PAGES = 8                   # safety cap per sync (20 posts/page); later syncs stop at the newest known post
