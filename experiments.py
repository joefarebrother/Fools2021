from itertools import product as prod
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
    # print(hex(a), end=" ")
    return a


# interesting_seeds = [0x002013a1,
#                      0x008902c1,
#                      0x01736411,
#                      0x01b0b791,
#                      0x32e59821,
#                      0x34955d51
#                      ]

# for sd in interesting_seeds:
#     seed = seed = [(sd & 0xFF000000) >> 24, (sd & 0x00FF0000) >>
#                    16, (sd & 0x0000FF00) >> 8, sd & 0x000000FF]
#     print(hex(sd), end=" ")
#     print(rand_from_chunk(1, 2), end=" ")
#     print(hex(chunk_rand), end=" ")
#     print([hex(b) for b in rand])

# for d in rand_table:
#     print(hex(d), end=",")

db35 = data("EB000004003E02EA4CDBEA00403E0AEA0000C93E0318F002CD0000FA4CDB18E7CD5ADB18F6E9CD3FDBCDB50018ED3E03CD3FDB7EF5CD50DBF1C921C0DA0E0411D4F97AABAE535F220D20F73E3B21C0DA8623AE239623AE2377C9CD48DBCD98DBCD3ADBCDF1DBFA00A0BA2001C9CD8036AFE0B03CE0BA21B3DBCD493C18FE0093A7A47FB2A0B5A47FA3A0B3A04FA8B27FA2AEB1B1B4AFB3A4A3E8518FABA4A0B2A47FB1A4A3AEB6ADABAEA0A34FB3A7A47FB2A0B5A47FA5A8ABA4E85701FF1F2101A016552AAA3C570B78B120F7C9CD48DB79A72839FE1330352152A52AA720FC0D20F97DEADDDA7CEADEDA116DCD011200CDB500216DCD7EA7280EFE3E2005367F2318F3C67F2218EE3650C33ADB2139A618D0C5AFCD3FDB2100B77BE6074FCB3ACB1BCB3ACB1BCB3ACB1B06000C37CB100D20FB19D17AA728067EA047C350DB7EB077C350DBAFCD3FDB2100B7010008AFCDE036C350DBAB0045008F035F0CBE105E103F207F20AB004500CEC0FD307A087B08FE04FD04A720602090105010BC0C530326007D00E70405040E080D083A30D3C026007D000000500057030F0C1E103E103F203F2000005000D5C0F53078087808FC04FC0427206020501010100C0C2B0328000000E40404040D080D083030E8C028000000050B06000E050B03090E0000000C0000000C0506060D0A09090B060000050A00050B06000B0609070009070A00050A000009060003060C0500090F0A00050A00050A00000F060503090F0A00000C0000050B03060E00000D0906000C000D030A0009060006050A05090F060C000C090A000C0000030F0703000D0A00000C000000")
manipulable = []
idx = 0
while idx < len(db35):
    val = db35[idx]
    idx += 1
    if 0 < val < 0x13:
        amt = db35[idx]
        if amt < 99:
            manipulable.append((hex(0xdb35+idx), hex(val), hex(amt)))
    idx += 1

# for m in manipulable:
#     print(m)

poss = [
    [4, 1],
    [0x6288, 0x62d4, 0xd488],
    [0xFF],
    [0x02, 0x06],  # 3, 5
    [0x00, 0x01, 0x02, 0x03, 0x04],
    [0xAA]]
stacks = []
for op in prod(*poss):
    # print(op)
    enc = op[0]
    d, e = split_bytes(op[1])
    pw = list(op[2:])
    if e != 0xd4:
        e = pw[1]
    for i in range(enc):
        a = pw[i]
        a = d ^ e ^ a
        pw[i] = a
        d, e = e, a

    if enc == 4:
        a = 0x3b

    # a += pw[0]
    # a ^= pw[1]
    # a -= pw[2]
    # a ^= pw[3]

    # pw.append(a)

    if enc == 4:
        stack = [conc_bytes(pw[1], pw[0]), conc_bytes(0xda, pw[2])]
    else:
        stack = [conc_bytes(pw[0], 00), conc_bytes(pw[2], pw[1])]

    stacks.append(stack)

    if hex(stack[0])[2] != '9':
        print([hex(o) for o in op], '\t', [hex(p)
                                           for p in pw], '\t', [hex(s) for s in stack], '\t', "DEC SP" if enc == 1 else "SP = HL")

stack_firsts = set(hex(s[0]) for s in stacks)
print(stack_firsts)
