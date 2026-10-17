#!/bin/bash
# usage: tools/dev/run_script.sh script.txt [disk.img]  -> prints snapshot dir
B="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT=$(realpath "$1")
S=$(MPC2000XL_ALLOW_MOD=1 python3 $B/run.py --system-dir ${SYSDIR:-$B/system-mod} ${2:+--disk $2} --prepare-only 2>&1 | awk '/Private session/{print $3}')
cd $S && MPC_SCRIPT=$SCRIPT MPC2000XL_ALLOW_MOD=1 nice -n 19 $B/build/bin/mpc2000xldiag mpc2000xldiag -noreadconfig -noplugins -noautosave -quik media/MPC2KXL.BIN $( [ -f media/floppy.img ] && echo -flop1 media/floppy.img ) -snapshot_directory snap -autoboot_script $B/tools/dev/drive.lua -autoboot_delay 0 -window -resolution 640x490 -video soft -sound ${SOUNDOPT:-none} ${WAV:+-wavwrite $WAV} -nosamples -skip_gameinfo -seconds_to_run ${CAP:-150} >out.log 2>&1
echo $S/snap/mpc2000xldiag
