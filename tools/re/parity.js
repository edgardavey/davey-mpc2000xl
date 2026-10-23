// jsc parity.js  (run from the repo root): the JS engine must build byte-identical files for every verified selection
load('patcher/engine.js');
const data = JSON.parse(readFile('patcher/modules.json'));
const orig = readFile('build_os/sys_stock/MPC2KXL.BIN', 'binary');
(async () => {
  let n = 0, bad = 0;
  for (const k of Object.keys(data.verified)) {
    const r = await MPCEngine.build(data, orig, k.split(','));
    const ok = r.report.sha256 === data.verified[k]; n++; if (!ok) bad++;
    print((ok ? 'OK  ' : 'BAD ') + r.report.sha256.slice(0, 12) + ' ' + k.slice(0, 70));
  }
  print('parity', n - bad, '/', n);
})().catch(e => print('ERR ' + e));
