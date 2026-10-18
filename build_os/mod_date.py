"""OS date: the stock date line on OTHER > VER. and the binary date record next to it (year word, month, day, 1, 20).
Stock: Jul. 15,2004. The binary record is what the OS stamps on a 'Copy Operating System' file."""
import struct
OLD_TXT = b'Jul. 15,2004'
DATE = (2026, 10, 11)
MONTHS = ['Jan.', 'Feb.', 'Mar.', 'Apr.', 'May.', 'Jun.', 'Jul.', 'Aug.', 'Sep.', 'Oct.', 'Nov.', 'Dec.']

def apply(img):
    y, m, d = DATE
    txt = f'{MONTHS[m - 1]} {d:02d},{y}'.encode()
    assert len(txt) == len(OLD_TXT)
    img.patch(0xfe80, OLD_TXT + struct.pack('<HBBBB', 2004, 7, 15, 1, 20), txt + struct.pack('<HBBBB', y, m, d, 1, 20))
