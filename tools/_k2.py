import io, glob
out = []
for f in sorted(glob.glob(r'ue/ue_py_*.log')):
    d = open(f, 'rb').read().decode('utf-8', errors='replace')
    for l in d.splitlines():
        if 'LogPython' in l and ('\u5730\u677f\u63a2\u9488' in l or '\u5730\u677f' in l):
            out.append(l.split('LogPython: ')[-1])
io.open(r'docs/_floor_log.txt', 'w', encoding='utf-8').write("\n".join(out[-60:]))
print(len(out))
