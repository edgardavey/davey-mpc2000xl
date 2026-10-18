// End-to-end check of "DAVEY MPC PATCHER.exe" on Windows (Node 22+): launches it with a WebView2 debug port, checks the page
// over CDP, then drives the SAVE link through the native Save dialog (save_dialog.ps1) and compares the bytes on disk, and
// checks that Cancel resolves false. Needs no Akai OS: the saved file is random test data.
// usage: node patcher/native/windows/test_win.mjs   (after build_win.py)
import { spawn, execFileSync } from 'node:child_process';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const EXE = path.join(HERE, 'out', 'DAVEY MPC PATCHER.exe');
const PORT = 9333;
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'davey-win-'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
let fails = 0;
const check = (ok, what) => { console.log((ok ? 'PASS ' : 'FAIL ') + what); if (!ok) fails++; };

const app = spawn(EXE, [], { stdio: 'ignore', env: { ...process.env, WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-port=${PORT}` } });
const done = code => { try { app.kill(); } catch {} fs.rmSync(TMP, { recursive: true, force: true }); console.log(fails ? `${fails} FAILED` : 'ALL PASSED'); process.exit(code); };

let page;
for (let i = 0; i < 80 && !page; i++) {
  await sleep(250);
  try { page = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).find(t => t.type === 'page'); } catch {}
}
check(!!page, 'WebView2 window came up');
if (!page) done(1);

const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let id = 0; const pending = new Map(); const errors = [];
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
});
const cdp = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const js = async expr => (await cdp('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;
const dialog = (action, p = '') => {
  try { return execFileSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(HERE, 'save_dialog.ps1'),
    '-ProcId', String(app.pid), '-Action', action, '-Path', p], { encoding: 'utf8' }).trim(); }
  catch (e) { return (e.stdout || '').trim() + ` (exit ${e.status})`; }
};
await cdp('Runtime.enable');
for (let i = 0; i < 40 && (await js('document.readyState')) !== 'complete'; i++) await sleep(250);

const info = await js(`({ title: document.title, pick: !!document.getElementById('pick'), make: !!document.getElementById('make'),
  ns: typeof window.nativeSave, ua: navigator.userAgent })`);
check(info.title === 'DAVEY MPC PATCHER', `page title (${info.title})`);
check(info.pick && info.make, 'patcher UI rendered (pick + make buttons)');
check(info.ns === 'function', 'nativeSave binding present');
check(/Edg\//.test(info.ua), 'running in WebView2');

// SAVE: a blob link with a button inside, as the page builds it; every byte value plus random data
const bytes = crypto.randomBytes(512 * 1024); bytes.set(Array.from({ length: 256 }, (_, i) => i), 0);
const target = path.join(TMP, 'DAVEY_TEST.BIN');
await js(`(() => { const raw = atob('${bytes.toString('base64')}'); const u = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) u[i] = raw.charCodeAt(i);
  const a = document.createElement('a'); a.id = 'tdl'; a.download = 'MPC2KXL_DAVEY.BIN';
  a.href = URL.createObjectURL(new Blob([u], { type: 'application/octet-stream' }));
  a.innerHTML = '<button class="go">SAVE</button>'; document.body.appendChild(a); return true; })()`);
js(`document.querySelector('#tdl button').click(), true`);    // not awaited: the modal Save dialog is open meanwhile
const out = dialog('save', target); console.log('  ' + out.replace(/\n/g, '\n  '));
check(/SUGGESTED "MPC2KXL_DAVEY(\.BIN)?"/.test(out), 'Save dialog suggests the page file name');
for (let i = 0; i < 40 && !fs.existsSync(target); i++) await sleep(250);
await sleep(300);
const got = fs.existsSync(target) ? fs.readFileSync(target) : Buffer.alloc(0);
check(got.equals(bytes), `saved file is byte-identical (${got.length} of ${bytes.length} bytes)`);

// Cancel: nativeSave resolves false
const r = js(`window.nativeSave('MPC2KXL_DAVEY_report.txt', btoa('report'))`);
console.log('  ' + dialog('cancel').replace(/\n/g, '\n  '));
check((await r) === false, 'Cancel resolves false');

await sleep(300);
check(errors.length === 0, 'no page exceptions' + (errors.length ? ': ' + errors.join(' | ') : ''));
ws.close();
done(fails ? 1 : 0);
