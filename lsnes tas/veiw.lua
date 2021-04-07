require("utils")

local views = {}
local active = {}

function toggle_view(name)
    active[name] = not active[name]
    gui.repaint()
end

function on_paint() 
    for n,v in pairs(views) do
        if active[n] then
            v()
        end
    end
end

gui.repaint()

function register_view(k, view)
    views[k] = view
    keyhook(k, toggle_view_khook)
end 

function text(x,y,str)
    gui.text(x,y,str,0xffffff, -1, 0x000000)
end

function toggle_view_khook(k, state)
    if state.value == 1 and views[k] then
        toggle_view(k)
    end
end

local col1 = 1
local col2 = 81
local function row(n) 
    return 1 + 12 * (n-1) 
end

register_view('q', function()
    local atk = read(0xdace)
    text(col1, row(1), "Attack:")
    text(col2, row(1), hex(atk)) 
end)

register_view('w', function()
    local dex = read(0xdacf)
    text(col1, row(2), "Pokedex:")
    text(col2, row(2), string.format("%s (%s)", hex(dex), bin(dex)))
end)

register_view('e', function()
    local xchunkl, xchunkh, ychunkl, ychunkh, chunkrand = read(0xdab4), read(0xdab5), read(0xdab6), read(0xdab7), read(0xdabf)
    text(col1, row(3), "X chunk:")
    text(col1, row(4), "Y chunk:")
    text(col1, row(5), "Rand:")
    text(col2, row(3), hex(xchunkh)..hex(xchunkl))
    text(col2, row(4), hex(ychunkh)..hex(ychunkl))
    text(col2, row(5), hex(chunkrand))
end)

register_view('r', function()
    local addr1, addr2 = 0xdb74, 0xdb7e
    text(col1, row(6), hex(addr1)..":")
    text(col1, row(7), hex(addr2)..":")
    text(col2, row(6), hex(read(addr1)))
    text(col2, row(7), hex(read(addr2)))
end)

local itemcol = 300
local item_names = {
"Potion", 
"Super Potion", 
"Hyper Potion", 
"Revival Seed",
"Life Seed",
"Hardened Scale",
"Skip Sandwich",
"Summoning Salt",
"Telltale Orb",
"Glitch Shard",
"Shyhorn",
"Daredevil Potion",
"Bravery Potion",
"Dark Crystal",
"Amber Crystal",
"Fluffy Crystal",
"Sharp Beak",
"Sharp Horn"
}
register_view('t', function()
    local addr = 0xdae4
    local count = read(addr)
    addr = addr+1
    text(itemcol, row(1), string.format("Items: %s (%s)", count, hex(count)))
    for i = 0, count do
        local item = read(addr)
        local qty = read(addr+1)
        local name = item_names[item]
        if not name then
            name = "unk"
        end
        text(itemcol, row(2+i), string.format("%s x %s (%s)", hex(item), qty, name))
        addr = addr+2
    end
end)