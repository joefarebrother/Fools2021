use std::fs::OpenOptions;
use std::io::{BufWriter, Write};
use std::process::exit;

#[derive(Debug)]
struct State {
    seed: [u8; 4],
    rand: [u8; 4],
    chunk_rand: u8,
    chunk_data: Chunk,
}

fn split_bytes(hl: u16) -> (u8, u8) {
    ((hl >> 8) as u8, hl as u8)
}

fn bit(i: usize, a: u8) -> bool {
    a & (1 << i) != 0
}

impl State {
    fn new(sd: u32) -> State {
        let seed: [u8; 4] = [
            ((sd & 0xFF000000) >> 24) as u8,
            ((sd & 0x00FF0000) >> 16) as u8,
            ((sd & 0x0000FF00) >> 8) as u8,
            (sd & 0x000000FF) as u8,
        ];
        State {
            seed: seed,
            rand: [0; 4],
            chunk_rand: 0,
            chunk_data: [[0; 8]; 8],
        }
    }

    fn init_chunk_rand(&mut self, x: u16, y: u16) {
        let tab = [
            0x5, 0xb, 0x6, 0x0, 0xe, 0x5, 0xb, 0x3, 0x9, 0xe, 0x0, 0x0, 0x0, 0xc, 0x0, 0x0, 0x0,
            0xc, 0x5, 0x6, 0x6, 0xd, 0xa, 0x9, 0x9, 0xb, 0x6, 0x0, 0x0, 0x5, 0xa, 0x0, 0x5, 0xb,
            0x6, 0x0, 0xb, 0x6, 0x9, 0x7, 0x0, 0x9, 0x7, 0xa, 0x0, 0x5, 0xa, 0x0, 0x0, 0x9, 0x6,
            0x0, 0x3, 0x6, 0xc, 0x5, 0x0, 0x9, 0xf, 0xa, 0x0, 0x5, 0xa, 0x0, 0x5, 0xa, 0x0, 0x0,
            0xf, 0x6, 0x5, 0x3, 0x9, 0xf, 0xa, 0x0, 0x0, 0xc, 0x0, 0x0, 0x5, 0xb, 0x3, 0x6, 0xe,
            0x0, 0x0, 0xd, 0x9, 0x6, 0x0, 0xc, 0x0, 0xd, 0x3, 0xa, 0x0, 0x9, 0x6, 0x0, 0x6, 0x5,
            0xa, 0x5, 0x9, 0xf, 0x6, 0xc, 0x0, 0xc, 0x9, 0xa, 0x0, 0xc, 0x0, 0x0, 0x3, 0xf, 0x7,
            0x3, 0x0, 0xd, 0xa, 0x0, 0x0, 0xc, 0x0, 0x0,
        ];
        let b = (x & 3) as u8;
        let c = (y & 3) as u8;
        self.init_rand(x & 0xFFFC, y & 0xFFFC);
        let r = self.rand() & 7;
        let a = r << 4 | c << 2 | b;
        self.chunk_rand = tab[a as usize];
        self.rand();
        // biome stuff not relevant
    }

    fn init_rand(&mut self, de: u16, bc: u16) {
        let (d, e) = split_bytes(de);
        let (b, c) = split_bytes(bc);
        self.rand = [
            d ^ self.seed[0],
            e ^ self.seed[1],
            b ^ self.seed[2],
            c ^ self.seed[3],
        ];
        for _ in 0..0x10 {
            self.rand();
        }
    }

    fn rand(&mut self) -> u8 {
        let r = &mut self.rand;
        let mut a = r[0];
        a += 1;
        r[0] = a;
        let mut b = a;
        b ^= r[3];
        b ^= r[1];
        r[1] = b;
        a = r[2];
        a += b;
        r[2] = a;
        a >>= 1;
        a ^= b;
        b = a;
        a = r[3];
        a += b;
        r[3] = a;
        // print!("{:?}\n", self.rand);
        a
    }

    fn gen_chunk(&mut self, x: u16, y: u16) {
        self.chunk_data = [[0xF; 8]; 8];
        self.init_chunk_rand(x, y);

        let edges = [(7, 4), (0, 4), (4, 7), (4, 0)];
        let mut foc_edge = (0, 0);
        for i in 0..4 {
            if bit(i, self.chunk_rand) {
                foc_edge = edges[i]
            }
        }

        self.init_rand(x, y);

        for i in 0..4 {
            if bit(i, self.chunk_rand) {
                self.gen_rand_path(foc_edge, edges[i])
            }
        }

        self.bumps(0x0A);

        let edges = [(7, 3, 7, 4), (0, 3, 0, 4), (3, 7, 4, 7), (3, 0, 4, 0)];
        for i in 0..4 {
            if bit(i, self.chunk_rand) {
                let (x0, y0, x1, y1) = edges[i];
                self.write_a(x0, y0);
                self.write_a(x1, y1);
            }
        }

        self.biome0();
    }

    fn biome0(&mut self) {
        self.replace_some(0x0A, 0x0B, 0x30);
        self.bumps(0x0B);
        self.match_pattern(0x0F, 0x6C, 0x20, 0x0F, 0x0A, 0, 0);
        self.match_pattern(0x0F, 0x6F, 0x20, 0x0A, 0x0F, 0, 0);
        self.match_pattern(0x0F, 0x6E, 0x20, 0, 0, 0x0A, 0x0F);
        self.match_pattern(0x0F, 0x6D, 0x20, 0, 0, 0x0F, 0x0A);
        self.replace_some(0x0A, 0x74, 0x30);
        self.replace_some(0x0A, 0x7A, 0x30);
        self.replace_some_internal(0x6C, 0x33, 0x40);
        self.replace_some_internal(0x6D, 0x32, 0x40);
        self.replace_some_internal(0x6E, 0x60, 0x40);
        self.replace_some_internal(0x6F, 0x34, 0x40);
    }

    fn gen_rand_path(&mut self, from: (u8, u8), to: (u8, u8)) {
        let x = self.roll_d6();
        let y = self.roll_d6();
        self.gen_path(from, (x, y));
        self.gen_path((x, y), to);
    }

    fn roll_d6(&mut self) -> u8 {
        loop {
            let a = self.rand() & 7;
            if a != 0 && a != 7 {
                return a;
            }
        }
    }

    fn gen_path(&mut self, from: (u8, u8), to: (u8, u8)) {
        let (mut x0, mut y0) = from;
        let (x1, y1) = to;
        let dx = if x0 > x1 { 0xff } else { 1 };
        let dy = if y0 > y1 { 0xff } else { 1 };
        loop {
            self.write_a(x0, y0);
            if x0 != x1 {
                x0 += dx
            }
            self.write_a(x0, y0);
            if y0 != y1 {
                y0 += dy
            }
            self.write_a(x0, y0);
            if (x0, y0) == (x1, y1) {
                return;
            }
        }
    }

    fn write_a(&mut self, x: u8, y: u8) {
        self.chunk_data[y as usize][x as usize] = 0x0A;
    }

    fn bumps(&mut self, tile: u8) {
        let copy = self.chunk_data.clone();
        for y in 1..7 {
            for x in 1..7 {
                if copy[y][x] == tile {
                    let a = self.rand();
                    let dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)];
                    for j in 0..4 {
                        if bit(j, a) {
                            let (dx, dy) = dirs[j];
                            self.chunk_data[y + dy as usize][x + dx as usize] = tile;
                        }
                    }
                }
            }
        }
    }

    fn replace_some(&mut self, cur: u8, rep: u8, prob: u8) {
        for y in 0..8 {
            for x in 0..8 {
                if self.chunk_data[y][x] == cur {
                    if self.rand() < prob {
                        self.chunk_data[y][x] = rep;
                    }
                }
            }
        }
    }

    fn replace_some_internal(&mut self, cur: u8, rep: u8, prob: u8) {
        for y in 1..7 {
            for x in 1..7 {
                if self.chunk_data[y][x] == cur {
                    if self.rand() < prob {
                        self.chunk_data[y][x] = rep;
                    }
                }
            }
        }
    }

    fn match_pattern(&mut self, cur: u8, rep: u8, prob: u8, up: u8, down: u8, left: u8, right: u8) {
        for y in 1..7 {
            for x in 1..7 {
                if self.chunk_data[y][x] == cur {
                    if self.rand() >= prob {
                        if up != 0 && up != self.chunk_data[y - 1][x] {
                            continue;
                        }
                        if down != 0 && down != self.chunk_data[y + 1][x] {
                            continue;
                        }
                        if left != 0 && left != self.chunk_data[y][x - 1] {
                            continue;
                        }
                        if right != 0 && right != self.chunk_data[y][x + 1] {
                            continue;
                        }
                        self.chunk_data[y][x] = rep;
                    }
                }
            }
        }
    }
}

fn gen_chunk(seed: u32, x: u16, y: u16) -> [[u8; 8]; 8] {
    let mut st = State::new(seed);
    st.gen_chunk(x, y);
    st.chunk_data
}

fn player_pos(chunk: &Chunk) -> (i8, i8) {
    for y in 0..8 {
        for x in 0..8 {
            if chunk[y][x] == 0x0A {
                return (x as i8, y as i8);
            }
        }
    }
    return (0, 0);
}

type Chunk = [[u8; 8]; 8];
type Screen = [[u8; 5]; 5];

struct ChunkMap {
    cells: [[Option<Box<Chunk>>; 3]; 4],
    seed: u32,
}

impl ChunkMap {
    fn empty(seed: u32) -> ChunkMap {
        ChunkMap {
            cells: [
                [None, None, None],
                [None, None, None],
                [None, None, None],
                [None, None, None],
            ],
            seed: seed,
        }
    }

    fn populate(&mut self, cx: u16, cy: u16) {
        match self.cells[cy as usize][cx as usize] {
            Some(_) => return,
            None => {
                self.cells[cy as usize][cx as usize] =
                    Some(Box::new(gen_chunk(self.seed, cx as u16, cy as u16)))
            }
        }
    }
    fn tile(&mut self, mut x: i8, mut y: i8, pop: bool) -> u8 {
        let mut cx = 1;
        let mut cy = 2;
        if x < 0 {
            x += 8;
            cx -= 1;
        };
        if x >= 8 {
            x -= 8;
            cx += 1;
        };
        if y < 0 {
            y += 8;
            cy -= 1;
        };
        if y >= 8 {
            y -= 8;
            cy += 1;
        };
        if pop {
            self.populate(cx, cy)
        }
        match &self.cells[cy as usize][cx as usize] {
            None => 0,
            Some(b) => b[y as usize][x as usize],
        }
    }

    fn new(seed: u32) -> ChunkMap {
        let mut s = ChunkMap::empty(seed);
        s.populate(1, 2);
        s
    }

    fn centre(&self) -> &Chunk {
        let o = &self.cells[2][1];
        let b = o.as_ref().unwrap();
        b
    }

    fn screen(&mut self, pop: bool) -> Screen {
        let mut res = [[0; 5]; 5];
        let (px, py) = player_pos(self.centre());
        for y in 0..5 {
            for x in 0..5 {
                res[y as usize][x as usize] = self.tile(px as i8 + x - 2, py as i8 + y - 2, pop)
            }
        }
        res
    }
}

fn check_target(scr: &Screen) -> bool {
    let target = [
        [0x0B, 0x0B, 0x0B, 0x74, 0x0A],
        [0x0F, 0x0B, 0x0F, 0x0A, 0x0A],
        [0x0F, 0x0F, 0x0A, 0x0A, 0x0B],
        [0x0F, 0x0B, 0x0A, 0x0A, 0x0A],
        [0x0B, 0x0B, 0xFF, 0xFF, 0x74],
    ];

    for y in 0..5 {
        for x in 0..5 {
            let actual = scr[y][x];
            let expected = target[y][x];
            if actual == 0 {
                continue;
            }
            if actual == expected {
                continue;
            }
            if expected == 0xFF {
                if actual == 0x0A || actual == 0x6F {
                    continue;
                }
            }
            return false;
        }
    }
    true
}

fn try_seed(seed: u32) -> bool {
    let mut m = ChunkMap::new(seed);
    let scr = m.screen(false);
    if check_target(&scr) {
        let fscr = m.screen(true);
        if check_target(&fscr) {
            println!("Got it! {:x}", seed);
            exit(0);
        }
        return true;
    }
    false
}

fn main() {
    let f = OpenOptions::new()
        .create(true)
        .write(true)
        .append(true)
        .open("interesting")
        .unwrap();
    let mut w = BufWriter::new(f);

    for i in 0..0x0fffffff {
        let seed = i << 4 | 1;
        if try_seed(seed) {
            writeln!(w, "{:x}", seed);
            println!("Interesting: {:x}", seed);
        }

        if seed & 0xffffff == 1 {
            println!("{:x}", seed);
        }
    }
}
