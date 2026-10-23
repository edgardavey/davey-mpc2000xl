"""Start at 0 after sampling (user report 2026-10-23): stock sets a new recording's St to the Pre-rec length
(Pre-rec 100ms -> St 4410), so TRIM opens with the start past the beginning. Here St = 0 whatever Pre-rec is; the
pre-recorded audio stays in the sound.
3E19:B6FA  mov ax,[95F4] / mov dx,[95F6]  (pre-rec samples, 32-bit) -> xor ax,ax / xor dx,dx; stored to es:[bx+26] = St."""


def apply(img):
    img.patch(0x3e190 + 0xb6fa, bytes.fromhex('a1f495' '8b16f695'), bytes.fromhex('33c0' '33d2' '909090'))
    return 0
