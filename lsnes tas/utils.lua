
function hex(num)
    return string.hex(num, 2)
end

hexToBin = {
    ['0'] = '0000',
    ['1'] = '0001',
    ['2'] = '0010',
    ['3'] = '0011',
    ['4'] = '0100',
    ['5'] = '0101',
    ['6'] = '0110',
    ['7'] = '0111',
    ['8'] = '1000',
    ['9'] = '1001',
    ['A'] = '1010',
    ['B'] = '1011',
    ['C'] = '1100',
    ['D'] = '1101',
    ['E'] = '1110',
    ['F'] = '1111',
}

function bin(num)
    return (hex(num):gsub('.', function(c) return hexToBin[c] end))
end

sram_offset = 0xa000
wram_offset = 0xc000
sram_bank_size = wram_offset - sram_offset

function convert_addr(addr)
    if addr < sram_offset then
        return memory2.ROM, addr
    end
    if addr < wram_offset then
        return memory2.SRAM, addr - sram_offset + 2 * sram_bank_size
    end
    return memory2.WRAM, addr - wram_offset
end

function read(addr)
    local reg, new_addr = convert_addr(addr)
    return reg:byte(new_addr)
end

local sched = {}
local frame_hooks = {}
function on_frame() 
    local fr = movie.currentframe()
    if sched[fr] then
        sched[fr]()
        sched[fr] = nil
    end
    for _,h in ipairs(frame_hooks) do
        h()
    end
end

function frame_hook(h)
    table.insert(frame_hooks, h)
end

function cancel_sched()
    sched = {}
end

function wait(n, cb)
    if n == 0 then
        cb()
        return
    end
    local fr = movie.currentframe() + n
    local cur = sched[fr]
    if cur then
        sched[fr] = function() 
            cur()
            cb()
        end
    else
        sched[fr] = cb
    end
end

keyhooks = {}

function keyhook(k, cb)
    keyhooks[k] = cb
    input.keyhook(k, true)
end

function on_keyhook(k, state)
    if keyhooks[k] then
        keyhooks[k](k, state)
    end
end

function set_pause_state(s) 
    if s ~= is_paused() then
        exec("pause-emulator")
    end
end

function is_paused()
    return gui.get_runmode() == "pause"
end

function save_state(slot)
    exec(string.format("save-state $SLOT:%d", slot))
end

function load_state(slot)
    exec(string.format("load-state $SLOT:%d", slot))
end

buttons = {}
cur_input = {}
for i,b in ipairs(input.controller_info(0,1).buttons) do
    buttons[b.name] = i-1
    cur_input[b.name] = 0
end

forced_input={}
local inp_hooks = {}
function on_input()
    for b,i in pairs(buttons) do
        cur_input[b] = input.get2(0,1,i)
    end 
    for _,h in ipairs(inp_hooks) do
        h()
    end
    for b,v in pairs(forced_input) do
        input.set2(0,1,buttons[b],v)
    end
end

function inp_hook(h) 
    table.insert(inp_hooks, h)
end
        
function exec_hook(addr, cb, persist) 
    persist = persist or false
    local area, new_addr = convert_addr(addr)
    local unreg
    if persist then
        unreg = area:registerexec(new_addr, cb)
    else
        unreg = area:registerexec(new_addr, function(a,v)
            cb(a,v)
            area:unregisterexec(new_addr, unreg)
        end)
    end
    return {cancel = function() area:unregisterexec(new_addr, unreg) end}
end