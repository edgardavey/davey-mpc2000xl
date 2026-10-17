#!/bin/bash
# usage: tools/dev/live.sh disk.img  -> starts a persistent emulator with sound; send commands by appending lines to $S/cmd.txt
B="$(cd "$(dirname "$0")/../.." && pwd)"
S=$(MPC2000XL_ALLOW_MOD=1 python3 $B/run.py --system-dir ${SYSDIR:-$B/system-fix} ${1:+--disk $1} --prepare-only 2>&1 | awk '/Private session/{print $3}')
: > $S/cmd.txt
cd $S && MPC_CMD=$S/cmd.txt MPC2000XL_ALLOW_MOD=1 nohup $B/build/bin/mpc2000xldiag mpc2000xldiag -noreadconfig -noplugins -noautosave -quik media/MPC2KXL.BIN $( [ -f media/floppy.img ] && echo -flop1 media/floppy.img ) -snapshot_directory snap -autoboot_script $B/tools/dev/drive.lua -autoboot_delay 0 -window -resolution 640x490 -video soft -sound sdl -nosamples -skip_gameinfo -debug -debugger none -seconds_to_run ${CAP:-7200} >out.log 2>&1 &
echo $S
