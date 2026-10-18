"""OTHER > VER. page: show our own build label instead of plain "1.2" (room for 7 characters)."""
LABEL = '1.2 FR1'
def apply(img):
    assert len(LABEL) <= 7
    img.patch(0x30e43, b'1.2    \x00', LABEL.ljust(7).encode('ascii') + b'\x00')
