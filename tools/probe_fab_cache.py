# -*- coding: utf-8 -*-
"""查 Epic Launcher 的 Fab 本地缓存 listings_v1.db 里有没有已领取/已缓存资产。"""
import sqlite3
import os

p = os.path.join(os.environ["PROGRAMDATA"], "Epic", "EpicGamesLauncher",
                 "VaultCache", "FabLibrary", "listings_v1.db")
print("db:", p, os.path.getsize(p) if os.path.exists(p) else "MISSING")
if not os.path.exists(p):
    raise SystemExit

con = sqlite3.connect(p)
cur = con.cursor()
tabs = [r[0] for r in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table'")]
print("tables:", tabs)
for t in tabs:
    try:
        n = cur.execute('SELECT count(*) FROM "%s"' % t).fetchone()[0]
        cols = [c[1] for c in cur.execute('PRAGMA table_info("%s")' % t)]
        print("  %s: %d rows" % (t, n))
        print("    cols:", cols)
        if n:
            rows = cur.execute('SELECT * FROM "%s" LIMIT 3' % t).fetchall()
            for r in rows:
                print("    sample:", [str(x)[:60] for x in r])
    except Exception as e:
        print("  ", t, "err", e)
con.close()
