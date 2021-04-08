require('utils')

local old
exec_hook(0xa3c8, function() 
    old = forced_input.A
    forced_input.A=0
end, true)
exec_hook(0xa3d2, function()
    forced_input.A=1
end, true)
exec_hook(0xa3ef, function() 
    forced_input.A=old 
end, true)