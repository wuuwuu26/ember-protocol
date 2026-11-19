import io, sys
d = open(r'ue/ue_py_1.log', 'rb').read().decode('utf-8', errors='replace')
ls = [l for l in d.splitlines() if 'LogPython' in l and ('\u661f' in l or 'ky' in l or '\u6750\u8d28' in l)]
io.open(r'docs/_sky_log.txt', 'w', encoding='utf-8').write("\n".join(ls[-20:]))
print(len(ls))
