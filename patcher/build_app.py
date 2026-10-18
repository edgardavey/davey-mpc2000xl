#!/usr/bin/env python3
import json, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
def read(name): return open(os.path.join(HERE, name), encoding='utf-8').read()   # utf-8 always (Windows defaults to cp1252)
data = read('modules.json')
json.loads(data)
html = read('app_template.html').replace('/*DATA*/', data).replace('/*ENGINE*/', read('engine.js')).replace('/*CHIP*/', read('chiptune.js'))
out = os.path.join(HERE, 'MPC2000XL-DAVEY-Patcher.html')
open(out, 'w', encoding='utf-8', newline='\n').write(html)
print('wrote', out, len(html), 'bytes')
# every script block must parse (an unescaped apostrophe in a tooltip once killed every button); macOS JavaScriptCore
# does the check, else Node (node --check) on Windows/Linux
import re, subprocess, tempfile
JSC = '/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc'
CHK = [JSC] if os.path.exists(JSC) else [shutil.which('node'), '--check'] if shutil.which('node') else None
if CHK:
    for i, b in enumerate(re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)):
        f = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8'); f.write('function __chk(){\n' + b + '\n}'); f.close()
        r = subprocess.run(CHK + [f.name], capture_output=True, text=True); os.remove(f.name)
        if r.returncode or (r.stdout + r.stderr).strip(): raise SystemExit(f'script block {i} does not parse: {(r.stdout + r.stderr).strip()}')
    print('all script blocks parse')
