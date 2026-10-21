"""1/4 timing correct (user request 2026-10-20): the Timing / Note value choice 1/32(3) becomes 1/4.

Stock list (main screen Timing:, TIMING CORRECT window Note value:), stored per sequence (sequence record +7):
  0 OFF, 1 1/8, 2 1/8(3), 3 1/16, 4 1/16(3), 5 1/32, 6 1/32(3)
Every reader of that value (watchpoint on the live value during record, playback, window open and DO IT, 2026-10-20):
  0:4DF6  xlat ds(0FE7):4833  -> grid in ticks (96 PPQN): 1, 48, 32, 24, 16, 12, 8
  0:4E26  [bx + ds(0FE7):483A] -> swing range: 0, 24, 0, 12, 0, 0, 0   (swing only for 1/8 and 1/16)
  267B:3483 xlat ds(2275):12D3 -> shift-timing cap: 0, 23, 15, 11, 7, 5, 3  (half the grid minus one)
  1A9B:105D generic list display (the strings below)
Slot 6 is reused instead of adding values 7/8: a stock OS (or any other unit) loading a DAVEY sequence then simply
reads 1/32(3); a value 7 would make the stock quantizer read past its 7-byte table (grid 0)."""


def apply(img):
    img.patch(0x236ac, b'1/32(3)', b'1/4    ')        # list entry 6 (fixed 7-character slots)
    img.patch(0x146a9, bytes([8]), bytes([96]))        # grid: a quarter note = 96 ticks
    img.patch(0x23a29, bytes([3]), bytes([47]))        # shift-timing cap: 96/2 - 1
    return 0                                           # swing stays 0 for this slot (as for every value except 1/8 and 1/16)
