-- Put the generated Items ModuleScript beside this Script in ServerScriptService.
local items = require(script.Parent.Items)
local byId = {}
for _, item in ipairs(items) do
	byId[item.id] = item
end

print("Repair kit costs", byId.toolkit.price)
-- This is configuration, not a purchase handler. Validate funds, ownership,
-- prerequisites and every client request on the server when building a shop.
