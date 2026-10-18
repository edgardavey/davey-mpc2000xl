/* DAVEY patcher engine (browser). Same algorithm as engine.py; see that file for the data format. */
const MPCEngine = (() => {
  const b64 = s => { const bin = atob(s); const u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return u; };
  const hex = u8 => Array.from(u8, b => b.toString(16).padStart(2, '0')).join('');
  // pure-JS SHA-256 fallback: crypto.subtle is missing on non-secure origins (plain http on a LAN host)
  function sha256js(u8) {
    const K = new Uint32Array([0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]);
    const H = new Uint32Array([0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]);
    const n = u8.length, pad = ((n + 9 + 63) >> 6) << 6, m = new Uint8Array(pad); m.set(u8); m[n] = 0x80;
    const dv = new DataView(m.buffer); dv.setUint32(pad - 8, Math.floor(n / 0x20000000)); dv.setUint32(pad - 4, (n << 3) >>> 0);
    const w = new Uint32Array(64), rr = (x, k) => (x >>> k) | (x << (32 - k));
    for (let o = 0; o < pad; o += 64) {
      for (let i = 0; i < 16; i++) w[i] = dv.getUint32(o + i * 4);
      for (let i = 16; i < 64; i++) { const a = rr(w[i-15],7)^rr(w[i-15],18)^(w[i-15]>>>3), b = rr(w[i-2],17)^rr(w[i-2],19)^(w[i-2]>>>10); w[i] = (w[i-16] + a + w[i-7] + b) >>> 0; }
      let [a,b,c,d,e,f,g,h] = H;
      for (let i = 0; i < 64; i++) {
        const t1 = (h + (rr(e,6)^rr(e,11)^rr(e,25)) + ((e&f)^(~e&g)) + K[i] + w[i]) >>> 0, t2 = ((rr(a,2)^rr(a,13)^rr(a,22)) + ((a&b)^(a&c)^(b&c))) >>> 0;
        h=g; g=f; f=e; e=(d+t1)>>>0; d=c; c=b; b=a; a=(t1+t2)>>>0;
      }
      H[0]+=a; H[1]+=b; H[2]+=c; H[3]+=d; H[4]+=e; H[5]+=f; H[6]+=g; H[7]+=h;
    }
    return Array.from(H, v => v.toString(16).padStart(8, '0')).join('');
  }
  async function sha256(u8) {
    if (typeof crypto !== 'undefined' && crypto.subtle) return hex(new Uint8Array(await crypto.subtle.digest('SHA-256', u8)));
    return sha256js(u8);
  }
  const byId = data => Object.fromEntries(data.modules.map(m => [m.id, m]));
  function closure(data, sel) {
    const mods = byId(data), out = new Set(), todo = [...sel];
    while (todo.length) {
      const x = todo.pop();
      if (out.has(x)) continue;
      if (!mods[x]) throw new Error('unknown module ' + x);
      out.add(x); todo.push(...mods[x].requires);
    }
    for (const x of out) for (const e of (mods[x].excludes || []))
      if (out.has(e)) throw new Error(mods[x].name + ' cannot be combined with ' + mods[e].name);
    return out;
  }
  function dependents(data, id) {            // modules that (directly or not) require id
    const res = new Set(), mods = data.modules;
    let grew = true; res.add(id);
    while (grew) { grew = false; for (const m of mods) if (!res.has(m.id) && m.requires.some(r => res.has(r))) { res.add(m.id); grew = true; } }
    res.delete(id); return res;
  }
  function points(data, S) { const mods = byId(data); let p = 0; for (const x of S) p += mods[x].weight; return p; }
  const key = S => [...S].sort().join(',');
  async function build(data, original, selection) {
    if (original.length !== data.base.size) throw new Error('input is not the original OS 1.20 (size ' + original.length + ')');
    const inSha = await sha256(original);
    if (inSha !== data.base.sha256) throw new Error('input is not the exact original OS 1.20 (sha256 ' + inSha + ')');
    const S = closure(data, selection), d = new Uint8Array(original);
    let patches = 0, xorPatches = 0, setPatches = 0;
    for (const m of data.modules) {
      if (!S.has(m.id) || m.kind !== 'xor') continue;
      for (const p of m.patches) {
        const x = b64(p.xor);
        if (p.offset < 0 || p.offset + x.length > data.finalize.unchanged[0]) throw new Error('module ' + m.id + ': patch outside the OS area');
        for (let i = 0; i < x.length; i++) d[p.offset + i] ^= x[i]; patches++; xorPatches++;
      }
    }
    for (const r of data.rules) {
      if (r.host !== null && !S.has(r.host)) continue;
      let x = b64(r.default);
      for (const v of r.variants) {
        const w = v.when;
        if (w.all.every(a => S.has(a)) && (!w.any.length || w.any.some(a => S.has(a))) && !w.none.some(a => S.has(a))) { x = b64(v.xor); break; }
      }
      for (let i = 0; i < r.length && i < x.length; i++) d[r.offset + i] ^= x[i];
    }
    for (const m of data.modules) {
      if (!S.has(m.id) || m.kind !== 'set') continue;
      for (const p of m.patches) {
        if ((p.when || []).some(w => !S.has(w)) || (p.unless || []).some(w => S.has(w))) continue;
        const o = b64(p.old), n = b64(p.new);
        if (o.length !== n.length || p.offset + n.length > data.finalize.unchanged[0]) throw new Error('module ' + m.id + ': malformed patch at 0x' + p.offset.toString(16));
        for (let i = 0; i < o.length; i++) if (d[p.offset + i] !== o[i])
          throw new Error('module ' + m.id + ': unexpected bytes at 0x' + (p.offset + i).toString(16));
        d.set(n, p.offset); patches++; setPatches++;
      }
    }
    const f = data.finalize, [a, b] = f.checksum.range;
    let s = 0; for (let i = a; i < b; i += 2) s = (s + d[i] + (d[i + 1] << 8)) & 0xffff;
    d[f.checksum.offset] = s & 255; d[f.checksum.offset + 1] = s >> 8;
    const [ua, ub] = f.unchanged;
    for (let i = ua; i < ub; i++) if (d[i] !== original[i]) throw new Error('boot region changed at 0x' + i.toString(16));
    for (const [fa, fb] of (f.forbidden || []))   // RAM the OS uses at runtime (program slots 18-24): must stay as in the original
      for (let i = fa; i < fb; i++) if (d[i] !== original[i]) throw new Error('a module writes into program memory at 0x' + i.toString(16));
    const outSha = await sha256(d);
    const ref = (data.verified || {})[key(S)];
    return { bytes: d, report: { modules: [...S].sort(), points: points(data, S), patches, xorPatches, setPatches, checksum: s, inputSha: inSha, sha256: outSha,
                                 reference: ref ? (ref === outSha ? 'match' : 'MISMATCH') : 'untested-combination' } };
  }
  return { build, closure, dependents, points, sha256, key, sha256js };
})();
if (typeof module !== 'undefined') module.exports = MPCEngine;
