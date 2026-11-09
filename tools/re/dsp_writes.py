"""dsp_writes.py BIN: load FUNKY, hit pad 1 twice; log every OUT to the L7A1045 ports 0x80-0x87 (port data pc)."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
sysd = os.path.abspath('exp_reloc/sys_probe'); os.makedirs(sysd, exist_ok=True)
open(sysd + '/MPC2KXL.BIN', 'wb').write(open(sys.argv[1], 'rb').read()); H.SYS['pp'] = sysd
WPI = 'lua local cpu=manager.machine.devices[":maincpu"]; local io=cpu.spaces["io"]; DW=io:install_write_tap(0x80,0x8f,"dspw",function(o,d,m) print(string.format("CON WR DSP %x=%04x pc=%x", o, d, cpu.state["PC"].value)) end) print("WPSET")'
L = P.chunk_load() + P.chunk_zone('d', P.FUNKY_CUTS[:3], True) + ['press main', 'wait 1', WPI, 'tap pad1 0', 'wait 0.7', 'tap pad2 0', 'wait 0.7', 'tap pad3 0', 'wait 1.5', 'snap',
  'lua for i,l in ipairs(manager.machine.debugger.consolelog) do if l:find("WR ") then print("CON "..l) end end', 'exit']
r = H.run('dspw', L, 'pp', 'floppy/funky.img', 400, sound=False)
t=H.log_text(r).split('\n')
print(r)
for l in t:
    if l.startswith(('CON','LUAERR')) or 'rror' in l or 'WPSET' in l: print(l)
