require("utils")

function manip_item(id)
    local delay = 0

    save_state(10)
    save_state(11)

    local function try()
        local oldA, oldP = forced_input.A, is_paused()

        local h1, h2

        local function restore() 
            h1.cancel()
            h2.cancel()
            forced_input.A = oldA
            set_pause_state(oldP)
        end

        if delay >= 12 then
            print("Failed to manipulate item: too many attempts")
            return
        end
        h1 = exec_hook(0xa6ff, function()
            print("Failed to manipulate item: did not pick up item")
            restore()
        end)
        h2 = exec_hook(0xa730, function()
            restore()
            local a = memory.getregister("a")
            if a ~= id then
               load_state(10)
               delay = delay + 1
               try() 
            end
        end)

        
        forced_input.A = 0
        wait(delay, function() forced_input.A = 1 end)
        set_pause_state(false)
    end

    try()
end

function get_coords() 
    return read(0xd361) * 0x100 + read(0xd362)
end

---- doesn't work
-- function manip_encounter(id, inp, on_success, on_fail, limit)
--     save_state(12)
--     save_state(13)

--     local delay = 1
--     limit = limit or 60

--     on_fail = on_fail or function(reason)
--         print("Failed to manipulate encounter: "..reason)
--     end

--     local old_coords = get_coords()

--     local function try()
--         local oldF, oldP = forced_input, is_paused()

--         if delay >= limit and limit >= 0 then
--             on_fail("too many attempts")
--             return
--         end

--         print(delay)

--         forced_input = {up=0, down=0, left=0, right=0}
--         wait(delay, function()
--             forced_input[inp] = 1
--             local h
--             h = exec_hook(0xa7a4, function() 
--                 forced_input = oldF
--                 if get_coords() ~= old_coords then -- the game seems to try to do this but not correctly
--                     h.cancel()
--                     if read(0xc45d) == 0x52 then -- if on grass
--                         exec_hook(0xa663, function()
--                             local enc = memory.getregister("a")
--                             if (enc == id) or (id == 0xff and enc ~= 0) then
--                                 set_pause_state(oldP)
--                                 if on_success then on_success() end
--                             else
--                                 load_state(13)
--                                 delay = delay + 1
--                                 try()
--                             end
--                         end)
--                     else
--                         on_fail("not on grass")
--                     end
--                 end
--             end, true) 
--         end)
--         set_pause_state(false)
--     end
--     try()
-- end

min_delay = 36
function farm_encounters(check)
    local checkfun = check
    if type(check) == "number" then checkfun = function(a) return a == check end end
    if not check then error("Expecting a number or a function") end

    local should_delay = false
    local delay = min_delay
    local h1, h2
    local function loop()
        if should_delay then
            return
        end
        if read(0xc45d - 40) == 0x52 then
            forced_input.up = 1
            forced_input.down = 0
        else
            forced_input.up = 0
            forced_input.down = 1
        end
        if cur_input.B ~= 1 and read(0xdae4) < 40  then
            wait(2, loop)
        else
            forced_input.up = nil
            forced_input.down = nil
            h1.cancel()
            h2.cancel()
        end
    end

    save_state(12)
    save_state(13)


    h1 = exec_hook(0xb1f5, function()
        local enc = read(0xdac9)
        print(string.format("Encountered %d on frame %d", enc, movie.currentframe()))
        if checkfun(enc) then
            delay = min_delay
        else
            should_delay = true
            load_state(12, function()
                print(string.format("Delaying %d frames", delay))
                cancel_sched()
                forced_input.up = 0
                forced_input.down = 0
                delay = delay + 2
                wait(delay, function()
                    should_delay = false
                    loop()
                end)
            end)
        end
    end, true)

    h2 = exec_hook(0xb510, function()
        print("Saving")
        save_state(12)
    end, true)

    loop()
end