#!/usr/bin/env python3
"""Writes the 'verified' table (selection key -> sha256) into modules.json from the selections that passed test_matrix.py."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import engine
data = engine.load_data(); orig = open(os.path.join(os.path.dirname(HERE), 'build_os', 'sys_stock', 'MPC2KXL.BIN'), 'rb').read()
passed = [r[0] for r in json.load(open(os.path.join(HERE, 'matrix_result.json'))) if r[3] == 'PASS']
assert passed, 'no passing selections'
sets = {'set_' + k: v for k, v in data['meter']['sets'].items()}
sets['set_recommended_dark'] = data['meter']['sets']['recommended'] + ['dark']
sets['stock_identity'] = []
ver = {}
for n in passed:
    sel = [n[5:]] if n.startswith('only_') else sets[n]
    out, rep = engine.build(data, orig, sel)
    ver[engine.sel_key(engine.closure(data, sel))] = rep['sha256']
data['verified'] = ver
json.dump(data, open(os.path.join(HERE, 'modules.json'), 'w'), indent=1)
print(len(ver), 'tested combinations written')
