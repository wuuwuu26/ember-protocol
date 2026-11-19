# -*- coding: utf-8 -*-
"""只读探查 opencode.db：列出会话、按项目分组、统计大小。"""
import sqlite3
import os

DB = os.path.join(os.environ["USERPROFILE"], ".local", "share", "opencode", "opencode.db")
print("db:", DB, os.path.getsize(DB), "bytes")
con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
cur = con.cursor()

tabs = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("tables:", tabs)

for t in tabs:
    try:
        n = cur.execute('SELECT count(*) FROM "%s"' % t).fetchone()[0]
        cols = [c[1] for c in cur.execute('PRAGMA table_info("%s")' % t)]
        print("  %-24s rows=%-8d cols=%s" % (t, n, cols))
    except Exception as e:
        print("  ", t, "err", e)

con.close()
