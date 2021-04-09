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