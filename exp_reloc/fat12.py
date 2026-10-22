"""fat12.py IMG NAME8: print a file's size and its last 16 bytes (follows the FAT12 chain, 1.44 MB layout)."""
import sys
def read(img, name):
    f = open(img, 'rb').read() if isinstance(img, str) else img
    j = f.find(name.encode(), 0x2600)
    cl = int.from_bytes(f[j + 26:j + 28], 'little'); sz = int.from_bytes(f[j + 28:j + 32], 'little')
    def nxt(c):
        o = 0x200 + c * 3 // 2; v = int.from_bytes(f[o:o + 2], 'little'); return (v >> 4) if c & 1 else (v & 0xfff)
    out = b''
    while cl < 0xff8: out += f[0x4200 + (cl - 2) * 512:0x4200 + (cl - 1) * 512]; cl = nxt(cl)
    return out[:sz]
if __name__ == '__main__':
    d = read(sys.argv[1], sys.argv[2]); print(hex(len(d)), d[-16:])
