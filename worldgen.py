from textwrap import wrap

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


def print_data(d, expect=None):
    print()
    col = 0
    for x in d:
        print(hex(x), end="\t")
        col += 1
        if col == 0x08:
            print("|\t", end="")
        if col == 0x10:
            print()
            col = 0
    if expect:
        if expect == d:
            print(True)
        for i in range(len(d)):
            if d[i] != expect[i]:
                print("Differ at offset " + hex(i))
                break


rand_table = data("050B06000E050B03090E0000000C0000000C0506060D0A09090B060000050A00050B06000B0609070009070A00050A000009060003060C0500090F0A00050A00050A00000F060503090F0A00000C0000050B03060E00000D0906000C000D030A0009060006050A05090F060C000C090A000C0000030F0703000D0A00000C0000")


def rand_from_chunk(x, y):  # de = x, hl = y
    global chunk_rand
    b = x & 3
    c = y & 3
    rand_init(x & 0xFFFC, y & 0xFFFC)
    r = scramble()
    a = (r & 7) << 4 | c << 2 | b
    chunk_rand = rand_table[a]
    chunk_rand |= (scramble() & 0x30)
    if not (x & 0xFC or y & 0xFC):
        chunk_rand &= 0xF


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


focused_edge = 0
chunk_data = chunk_data = [0x0F] * 0x40


def gen_chunk(x, y):
    global focused_edge, chunk_data
    rand_from_chunk(x, y)
    chunk_data = [0x0F] * 0x40

    edges = [0x74, 0x04, 0x47, 0x40]

    for i in range(4):
        if bit(i, chunk_rand):
            focused_edge = edges[i]

    rand_init(x, y)

    for i in range(4):
        if bit(i, chunk_rand):
            gen_rand_path(focused_edge, edges[i], 0x0A)

    add_bumps(0x0A)

    if bit(3, chunk_rand):
        write_to_chunk(3, 0, 0x0A)
        write_to_chunk(4, 0, 0x0A)
    if bit(2, chunk_rand):
        write_to_chunk(3, 7, 0x0A)
        write_to_chunk(4, 7, 0x0A)
    if bit(1, chunk_rand):
        write_to_chunk(0, 3, 0x0A)
        write_to_chunk(0, 4, 0x0A)
    if bit(0, chunk_rand):
        write_to_chunk(7, 3, 0x0A)
        write_to_chunk(7, 4, 0x0A)

    biome = chunk_rand >> 4 & 3
    [biome0, biome1, biome2, biome3][biome]()

    return chunk_data


def biome0():
    replaceSome(0x0A, 0x0B, 0x30)
    add_bumps(0x0B)
    # print_data(chunk_data, expect=data(
    #     "0F0F0A0A0A0F0F0F0F0A0A0A0A0A0F0F0B0A0A0A0A0F0F0F0A0B0F0A0A0A0F0A0B0B0F0B0B0A0A0B0F0B0A0A0B0B0B0B0F0F0A0A0A0F0F0F0F0F0F0A0A0F0F0F"))
    matchPattern(0x0F, 0x6C, 0x20, 0x0F, 0x0A, 0, 0)
    # print_data(chunk_data, expect=data(
    #     "0F0F0A0A0A0F0F0F0F0A0A0A0A0A0F0F0B0A0A0A0A0F0F0F0A0B0F0A0A0A6C0A0B0B0F0B0B0A0A0B0F0B0A0A0B0B0B0B0F0F0A0A0A0F0F0F0F0F0F0A0A0F0F0F"))
    matchPattern(0x0F, 0x6F, 0x20, 0x0A, 0x0F, 0, 0)
    # print_data(chunk_data, expect=data(
    #     "0F0F0A0A0A0F0F0F0F0A0A0A0A0A0F0F0B0A0A0A0A0F0F0F0A0B6F0A0A0A6C0A0B0B0F0B0B0A0A0B0F0B0A0A0B0B0B0B0F0F0A0A0A0F0F0F0F0F0F0A0A0F0F0F"))
    matchPattern(0x0F, 0x6E, 0x20, 0, 0, 0x0A, 0x0F)
    # print_data(chunk_data, expect=data(
    #     "0F0F0A0A0A0F0F0F0F0A0A0A0A0A6E0F0B0A0A0A0A6E0F0F0A0B6F0A0A0A6C0A0B0B0F0B0B0A0A0B0F0B0A0A0B0B0B0B0F0F0A0A0A6E0F0F0F0F0F0A0A0F0F0F"))
    matchPattern(0x0F, 0x6D, 0x20, 0, 0, 0x0F, 0x0A)
    # print_data(chunk_data, expect=data(
    #     "0F0F0A0A0A0F0F0F0F0A0A0A0A0A6E0F0B0A0A0A0A6E0F0F0A0B6F0A0A0A6C0A0B0B0F0B0B0A0A0B0F0B0A0A0B0B0B0B0F6D0A0A0A6E0F0F0F0F0F0A0A0F0F0F"))
    replaceSome(0x0A, 0x74, 0x30)
    # print_data(chunk_data)
    replaceSome(0x0A, 0x7A, 0x30)
    replaceSomeInt(0x6C, 0x33, 0x40)
    replaceSomeInt(0x6D, 0x32, 0x40)
    replaceSomeInt(0x6E, 0x60, 0x40)
    replaceSomeInt(0x6F, 0x34, 0x40)


def biome1():
    pass


def biome2():
    pass


def biome3():
    pass


def replaceSome(cur, rep, prob):
    for (i, x) in enumerate(chunk_data):
        if x != cur:
            continue
        if scramble() < prob:
            chunk_data[i] = rep


def replaceSomeInt(cur, rep, prob):
    for i in range(0x30):
        off = i+0x8
        if chunk_data[off] != cur:
            continue
        if off & 7 in [0, 7]:
            continue
        if scramble() < prob:
            chunk_data[off] = rep


def matchPattern(cur, rep, prob, up, down, left, right):
    for i in range(0x30):
        off = i+0x8
        if chunk_data[off] != cur:
            continue
        if off & 7 in [0, 7]:
            continue
        if scramble() < prob:  # opposite to the other functions!
            continue
        if up and up != chunk_data[off-0x8]:
            continue
        if down and down != chunk_data[off+0x8]:
            continue
        if left and left != chunk_data[off-1]:
            continue
        if right and right != chunk_data[off+1]:
            continue
        chunk_data[off] = rep


def gen_rand_path(b, c, tile):
    d = roll_d6()
    e = roll_d6()
    pt = conc_nibbles(d, e)
    gen_path(b, pt, tile)
    gen_path(pt, c, tile)


def gen_path(p0, p1, tile):
    x0, y0 = split_nibbles(p0)
    x1, y1 = split_nibbles(p1)
    dx = -1 if x0 > x1 else 1
    dy = -1 if y0 > y1 else 1
    while True:
        write_to_chunk(x0, y0, tile)
        if x0 != x1:
            x0 += dx
        write_to_chunk(x0, y0, tile)
        if y0 != y1:
            y0 += dy
        write_to_chunk(x0, y0, tile)
        if x0 == x1 and y0 == y1:
            break


def add_bumps(tile):
    copy = chunk_data[:]
    for i in range(0x30):
        off = i + 0x08
        if copy[off] != tile:
            continue
        if off & 7 in [0, 7]:
            continue
        a = scramble()
        for j in range(4):
            if bit(j, a):
                bump = off + [-1, 1, -8, 8][j]
                chunk_data[bump] = tile


def write_to_chunk(x, y, tile):
    chunk_data[y << 3 | x] = tile


def roll_d6():
    while True:
        a = scramble() & 7
        if 1 <= a <= 6:
            return a


def player_pos(chunk_data):
    for (i, d) in enumerate(chunk_data):
        if d == 0x0A:
            off = i
            break
    else:
        off = 0
    x = off % 8
    y = off // 8
    return (x, y)


player_radius = 2
computed_chunks = {}
wanted_chunks = set()


def pos_in_chunk(x, y, chunk_data):
    return chunk_data[y*8+x]


def pos_in_map(x, y, cx, cy):
    if x < 0:
        x += 8
        cx -= 1
    if x >= 8:
        x -= 8
        cx += 1
    if y < 0:
        y += 8
        cy -= 1
    if y >= 8:
        y -= 8
        cy += 1
    if (cx, cy) in computed_chunks:
        return pos_in_chunk(x, y, computed_chunks[(cx, cy)])
    else:
        wanted_chunks.add((cx, cy))
        return None


def gen_map(sd=0):
    global seed, computed_chunks, wanted_chunks
    seed = [(sd & 0xFF000000) >> 24, (sd & 0x00FF0000) >>
            16, (sd & 0x0000FF00) >> 8, sd & 0x000000FF]
    centre = gen_chunk(1, 2)
    if not centre:
        return
    wanted_chunks = set()
    computed_chunks = {(1, 2): centre}
    m = map_around_player(centre)
    return m


def map_around_player(centre):
    res = []
    (px, py) = player_pos(centre)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            t = pos_in_map(px+dx, py+dy, 1, 2)
            res.append(t)
    return res


def full_map_around_player():
    c = computed_chunks[(1, 2)]
    for (cx, cy) in wanted_chunks:
        computed_chunks[(cx, cy)] = gen_chunk(cx, cy)
    return map_around_player(c)


target_map = (
    [0x0B, 0x0B, 0x0B, 0x74, 0x0A] +
    [0x0F, 0x0B, 0x0F, 0x0A, 0x0A] +
    [0x0F, 0x0F, 0x0A, 0x0A, 0x0B] +
    [0x0F, 0x0B, 0x0A, 0x0A, 0x0A] +
    [0x0B, 0x0B, 0x0A, 0x0A, 0x74])


def print_map(m):
    print()
    col = 0
    for t in m:
        print(hex(t) if t else "-", end="\t")
        col += 1
        if col == 5:
            print()
            col = 0
    print()


print_map(gen_map(1))
print_map(full_map_around_player())


def search_for_map(sd):
    m = gen_map(sd)
    if not m:
        return
    for (t, tar) in zip(m, target_map):
        if t and t != tar:
            return
    else:
        print("Interesting seed! ", hex(sd))
        if full_map_around_player() == target_map:
            print("It's a match!")
            input()


for s in range(0x3700000, 0x0FFFFFFF):
    s = s << 4 | 1
    search_for_map(s)
    if(s & 0xffff == 1):
        print(hex(s))
