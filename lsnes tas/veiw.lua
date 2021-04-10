require("utils")

local views = {}
local active = {}
local views_ordered = {}

function toggle_view(name)
    active[name] = not active[name]
    gui.repaint()
end

function on_paint() 
    for _,n in ipairs(views_ordered) do
        if active[n] then
            views[n]()
        end
    end
end

gui.repaint()

function register_view(k, view)
    views[k] = view
    table.insert(views_ordered, k)
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

function display_two_cols(r, c1, c2)
    text(col1, row(r), c1)
    text(col2, row(r), c2)
end

function display_addr(r, name, addr)
    display_two_cols(r, name..":", hex(read(addr)))
end

register_view('u', function()
    gui.solidrectangle(0,0,500,500,0)
end)

register_view('q', function()
    display_addr(1, "Attack", 0xdace)
end)

register_view('w', function()
    local dex = read(0xdacf)
    display_two_cols(2, "Pokedex:", string.format("%s (%s)", hex(dex), bin(dex)))
end)

register_view('e', function()
    local xchunkl, xchunkh, ychunkl, ychunkh, chunkrand = read(0xdab4), read(0xdab5), read(0xdab6), read(0xdab7)
    display_two_cols(3, "X chunk:", hex(xchunkh)..hex(xchunkl))
    display_two_cols(4, "Y chunk:", hex(ychunkh)..hex(ychunkl))
    display_addr(5, "Rand", 0xdabf)
end)

register_view('r', function()
    local addr1, addr2 = 0xdb74, 0xdb7e
    display_addr(6, hex(addr1), addr1)
    display_addr(7, hex(addr2), addr2)
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
        local col = (i < 30 and itemcol) or col2
        local row = (i < 30 and row(2+i)) or row(10+i-30)
        if not name then
            name = "unk"
        end
        text(col, row, string.format("%s x %s (%s)", hex(item), qty, name))
        addr = addr+2
    end
end)

register_view('y', function()
    display_addr(8, "Encounter", 0xdac9)
end)