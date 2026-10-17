-- Dev harness: MPC_SCRIPT=file with lines: wait S | press NAME | down NAME | up NAME | snap | exit
local m=manager.machine
local map={f1={":KEYS",1},f2={":KEYS",2},f3={":KEYS",4},f4={":KEYS",8},f5={":KEYS",16},f6={":KEYS",32},
main={":KEYS",256},window={":KEYS",512},enter={":KEYS",16384},minus={":KEYS",64},plus={":KEYS",128},
left={":KEYS",1024},right={":KEYS",2048},up={":KEYS",4096},down={":KEYS",8192},shift={":MODIFIERS",2},
after={":EXTRAS",1},erase={":EXTRAS",8},stepprev={":EXTRAS",16},stepnext={":EXTRAS",32},goto_={":EXTRAS",64},
rec={":EXTRAS",128},overdub={":EXTRAS",256},stop={":EXTRAS",512},play={":EXTRAS",1024},playstart={":EXTRAS",65536},
banka={":EXTRAS",0x1000},bankb={":EXTRAS",0x20000},bankc={":EXTRAS",0x40000},bankd={":EXTRAS",0x80000},full={":EXTRAS",8192},levels={":EXTRAS",16384},undo={":EXTRAS",4},barprev={":EXTRAS",2048},barnext={":EXTRAS",32768}}
for i=0,9 do map["n"..i]={":NUMBERS",({1,2,4,8,16,32,64,128,256,512})[i+1]} end
for i=1,16 do map["pad"..i]={":PADS",1<<(i-1)} end
local cache={}
local function fld(n) local s=map[n] assert(s,"bad key "..n) if not cache[n] then
 for _,f in pairs(m.ioport.ports[s[1]].fields) do if f.mask==s[2] then cache[n]=f end end end return cache[n] end
local ev,t={},0
local function sched(line)
 if line:sub(1,4)=="lua " then local f=load(line:sub(5)) ev[#ev+1]={t,function() local ok,e=pcall(f) if not ok then print("LUAERR "..tostring(e)) end end} return end
 local c,a,b=line:match("^(%S+)%s*(%S*)%s*(%S*)") 
 if c=="wait" then t=t+tonumber(a)
 elseif c=="press" then ev[#ev+1]={t,function() fld(a):set_value(1) end} ev[#ev+1]={t+0.25,function() fld(a):set_value(0) end} t=t+0.6
 elseif c=="tap" then ev[#ev+1]={t,function() fld(a):set_value(1) end} ev[#ev+1]={t+0.12,function() fld(a):set_value(0) end} t=t+(tonumber(b) or 0.5)
 elseif c=="down" then ev[#ev+1]={t,function() fld(a):set_value(1) end} t=t+0.2
 elseif c=="up" then ev[#ev+1]={t,function() fld(a):set_value(0) end} t=t+0.4
 elseif c=="snap" then ev[#ev+1]={t,function() m.video:snapshot() end} t=t+0.3
 elseif c=="mem" then ev[#ev+1]={t,function() local sp=m.devices[":maincpu"].spaces["program"] print(string.format("MEM hits=%d misses=%d gc=%d cave=%d/%d/%d", sp:read_u16(0x749B0+0x4384), sp:read_u16(0x749B0+0x4386), sp:read_u8(0x749B0+0x4110), sp:read_u16(0x76E50), sp:read_u16(0x76E52), sp:read_u16(0x76E54))) end}
 elseif c=="log" then ev[#ev+1]={t,function() logging=(a=="on") end}
 elseif c=="scan" then ev[#ev+1]={t,function()
   local sp=m.devices[":maincpu"].spaces["program"] local n=0
   for addr=0x100000,0x110000,2 do
     if sp:read_u8(addr+4)==0x23 and sp:read_u8(addr+5)==0x01 and sp:read_u8(addr+6)==0xFF and sp:read_u8(addr+7)>=0xF0 then
       local b={} for k=0,7 do b[#b+1]=string.format("%02x",sp:read_u8(addr+k)) end
       print(string.format("EV %s %06x %s",a,addr,table.concat(b," "))) n=n+1 if n>200 then break end
     end
   end end}
 elseif c=="tap_mem" then ev[#ev+1]={t,function()
   local sp=m.devices[":maincpu"].spaces["program"] local cpu=m.devices[":maincpu"] local n=0
   sp:install_write_tap(0x102800,0x10285f,"evtap",function(off,data,mask)
     n=n+1 if n>600 then return end
     local ok,cs=pcall(function() return cpu.state["CS"].value end)
     local ok2,ip=pcall(function() return cpu.state["IP"].value end)
     if not ok2 then ok2,ip=pcall(function() return cpu.state["PC"].value end) end
     print(string.format("W t=%.3f off=%06x data=%04x mask=%04x cs=%s ip=%s",m.time:as_double(),off,data,mask,tostring(cs),tostring(ip)))
   end) end}
 elseif c=="exit" then ev[#ev+1]={t,function() m:exit() end} end
end
if os.getenv("MPC_SCRIPT") then for line in io.lines(os.getenv("MPC_SCRIPT")) do sched(line) end end
local i=1
logging=false
local lasthits=0
local function logframe()
 local sp=m.devices[":maincpu"].spaces["program"]
 local h=sp:read_u16(0x749B0+0x4384)
 if logging and h~=lasthits then
  local parts={}
  for v=0,31 do local base=0x582b0+0x9609+v*20 local b={}
   for k=0,9 do b[#b+1]=string.format("%02x",sp:read_u8(base+k)) end
   parts[#parts+1]=table.concat(b)
  end
  print(string.format("HIT t=%.3f hits=%d %s",m.time:as_double(),h,table.concat(parts," ")))
 end
 lasthits=h
end
local cmdpos=0
local function poll()
 local path=os.getenv("MPC_CMD") if not path then return end
 local f=io.open(path,"r") if not f then return end
 f:seek("set",cmdpos) local data=f:read("a") cmdpos=f:seek("cur") f:close()
 if data and #data>0 then
  local now=m.time:as_double() if t<now then t=now end
  for line in data:gmatch("[^\n]+") do sched(line) end
 end
end
emu.register_frame_done(function() poll() logframe() local now=m.time:as_double() while ev[i] and now>=ev[i][1] do ev[i][2]() i=i+1 end end)
