#!/usr/bin/env python3
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
data = open(os.path.join(HERE, 'modules.json')).read()
json.loads(data)
html = open(os.path.join(HERE, 'app_template.html')).read().replace('/*DATA*/', data).replace('/*ENGINE*/', open(os.path.join(HERE, 'engine.js')).read()).replace('/*CHIP*/', open(os.path.join(HERE, 'chiptune.js')).read())
out = os.path.join(HERE, 'MPC2000XL-DAVEY-Patcher.html')
open(out, 'w').write(html)
print('wrote', out, len(html), 'bytes')
# every script block must parse (an unescaped apostrophe in a tooltip once killed every button); macOS JavaScriptCore does the check
import re, subprocess, tempfile
JSC = '/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc'
if os.path.exists(JSC):
    for i, b in enumerate(re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)):
        f = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False); f.write('function __chk(){\n' + b + '\n}'); f.close()
        r = subprocess.run([JSC, f.name], capture_output=True, text=True); os.remove(f.name)
        if r.returncode or (r.stdout + r.stderr).strip(): raise SystemExit(f'script block {i} does not parse: {(r.stdout + r.stderr).strip()}')
    print('all script blocks parse')
