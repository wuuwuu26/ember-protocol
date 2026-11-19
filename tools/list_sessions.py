# -*- coding: utf-8 -*-
"""列出 opencode 的所有项目与会话（只读），标出 workbuddy 相关。"""
import sqlite3
import os
import json
from datetime import datetime

DB = os.path.join(os.environ["USERPROFILE"], ".local", "share", "opencode", "opencode.db")
con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
cur = con.cursor()


def ts(v):
    if not v:
        return "-"
    try:
        # 可能是毫秒或秒
        n = float(v)
        if n > 1e12:
            n /= 1000.0
        return datetime.fromtimestamp(n).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(v)[:19]


print("=== PROJECTS (23) ===")
projs = {}
for r in cur.execute("SELECT id, worktree, name, time_created, time_updated, time_archived FROM project ORDER BY time_updated DESC"):
    projs[r[0]] = r
    print("  %s\n      name=%r\n      worktree=%s\n      updated=%s archived=%s" %
          (r[0], r[2], r[1], ts(r[4]), r[5]))

print("\n=== SESSIONS (17) ===")
rows = cur.execute("""
  SELECT s.id, s.project_id, s.title, s.time_created, s.time_updated,
         s.time_archived, s.directory,
         (SELECT COUNT(*) FROM session_message m WHERE m.session_id = s.id) AS nmsg
  FROM session_v2 s ORDER BY s.time_updated DESC""").fetchall()
for r in rows:
    sid, pid, title, tc, tu, ta, d, nmsg = r
    p = projs.get(pid)
    pname = p[2] if p else "?"
    pwt = p[1] if p else "?"
    flag = ""
    if pwt and "workbuddy" in str(pwt).lower():
        flag = "  <<< WORKBUDDY"
    elif d and "workbuddy" in str(d).lower():
        flag = "  <<< WORKBUDDY(dir)"
    print("  %s\n      title=%r\n      project=%s (%s)\n      msgs=%d  created=%s updated=%s archived=%s%s" %
          (sid, title, pid, pname, nmsg, ts(tc), ts(tu), ta, flag))

con.close()
