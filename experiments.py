from textwrap import wrap
from collections import defaultdict

seed = [0]*4
rand = [0]*4
chunk_rand = 0


def conc_bytes(h, l):
    return (h << 8) | l


def high_byte(hl):
    return (hl >> 8) & 0xFF


def low_byte(hl):
    return hl & 0xFF


def conc_nibbles(h, l):
    return (h << 4) | l


def high_nibble(a):
    return (a >> 4) & 0xF


def low_nibble(a):
    return a & 0xF


def split_bytes(hl):
    return (high_byte(hl), low_byte(hl))


def split_nibbles(hl):
    return (high_nibble(hl), low_nibble(hl))


def bit(i, a):
    return bool(a & (1 << i))


def data(st):
    d = wrap(st, 2)
    d = [int(b, 16) for b in d]
    return d


rand_table = data("050B06000E050B03090E0000000C0000000C0506060D0A09090B060000050A00050B06000B0609070009070A00050A000009060003060C0500090F0A00050A00050A00000F060503090F0A00000C0000050B03060E00000D0906000C000D030A0009060006050A05090F060C000C090A000C0000030F0703000D0A00000C0000")

allowed = []
for i in range(0x7):
    c1 = rand_table[i << 4 | 9]
    c2 = rand_table[i << 4 | 5]
    if c1 & 9 == 9 and c2 & 6 == 6:
        allowed.append((i, c1, c2))

print(allowed)


def rand_from_chunk(x, y):  # de = x, hl = y
    global chunk_rand
    b = x & 3
    c = y & 3
    rand_init(x & 0xFFFC, y & 0xFFFC)
    r = scramble() & 7
    a = r << 4 | c << 2 | b
    chunk_rand = rand_table[a]
    chunk_rand |= (scramble() & 0x30)
    if not (x & 0xFC or y & 0xFC):
        chunk_rand &= 0xF
    return r


def rand_init(de, bc):
    global rand, seed
    d, e = split_bytes(de)
    b, c = split_bytes(bc)
    rand = [d ^ seed[0], e ^ seed[1], b ^ seed[2], c ^ seed[3]]
    for _ in range(0x10):
        scramble()


def scramble():
    global rand
    a = rand[0]
    a += 1
    a &= 0xFF
    rand[0] = a
    b = a
    b ^= rand[3]
    b ^= rand[1]
    rand[1] = b
    a = rand[2]
    a += b
    a &= 0xFF
    rand[2] = a
    a >>= 1
    a ^= b
    b = a
    a = rand[3]
    a += b
    a &= 0xFF
    rand[3] = a
    #print(hex(a), end=" ")
    return a


interesting_seeds = [0x002013a1,
                     0x008902c1,
                     0x01736411,
                     0x01b0b791,
                     0x32e59821,
                     0x34955d51
                     ]

for sd in interesting_seeds:
    seed = seed = [(sd & 0xFF000000) >> 24, (sd & 0x00FF0000) >>
                   16, (sd & 0x0000FF00) >> 8, sd & 0x000000FF]
    print(hex(sd), end=" ")
    print(rand_from_chunk(1, 2), end=" ")
    print(hex(chunk_rand), end=" ")
    print([hex(b) for b in rand])
