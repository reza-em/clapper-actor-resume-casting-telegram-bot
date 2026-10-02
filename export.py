#!/usr/bin/env python3
"""Offline export: python3 export.py [--out DIR] [--db PATH] [--media DIR] [--no-drafts]
Writes resumes.csv, resumes.json, calls.json, photos.zip (+ SCHEMA.md) into DIR (default ./export-YYYYmmdd-HHMMSS).
Needs no token and no network. Contains personal data: keep it private."""
import os, sys, argparse, time

def main():
    ap = argparse.ArgumentParser(description="Export cast-bot resumes (CSV + JSON + photo ZIP)")
    ap.add_argument("--out"); ap.add_argument("--db"); ap.add_argument("--media")
    ap.add_argument("--no-drafts", action="store_true", help="only completed resumes")
    a = ap.parse_args()
    import config
    if a.media: config.MEDIA_DIR = os.path.abspath(a.media)
    import db, resumes
    if a.db: db.set_path(os.path.abspath(a.db))
    elif a.media: pass
    if not os.path.exists(db.get_path()):
        print("database not found: " + db.get_path(), file=sys.stderr); return 1
    import exporter
    out = a.out or os.path.join(config.BASE, time.strftime("export-%Y%m%d-%H%M%S"))
    if a.media or not a.db: resumes.media_dir = lambda: config.MEDIA_DIR
    res = exporter.export_all(out, include_drafts=not a.no_drafts)
    exporter.export_calls(out)
    print("exported %d resumes -> %s" % (res["count"], out))
    for k in ("csv", "json", "schema"): print("  ", res.get(k))
    for p in res["photos"]: print("  ", p)
    os.chmod(out, 0o700)
    return 0

if __name__ == "__main__":
    sys.exit(main())
