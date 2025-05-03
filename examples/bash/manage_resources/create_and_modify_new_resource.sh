#! /bin/bash
# ╔──────────────────────────────────────╗
# │                                      │
# │    Create and modify new resource    │
# │                                      │
# ╚──────────────────────────────────────╝
# ----------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# We want to create a new resource/item. Note: the endpoint name is "items".
# Then we will modify its title, body and status.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - We need elAPI installed (preferably via pipx for this example).
# - We definitely need an API token with write access.
# - We need an existing resource category (ID) and an existing status (ID)

RANDOM_NUM="$RANDOM" # random number for unique title
resource_id=$(elapi post items --data '{"category_id": 77}' --get-loc | cut -d "," -f 1)
# 1. elapi post items --data '{"category_id": 77}': This will create the resource
# assigned to given category ID. But we also need to know the ID of the newly created
# resource.
# 2. For the new resource ID, we pass the --get-loc. When --get-loc is passed,
# elAPI will print the ID and the URL of the ID to terminal separated by a comma.
# Try running said command with and without --get-loc yourself to see the difference in output!
# 3. We just need the resource ID. We capture the ID with "cut".
# We could do it in many other ways in bash.
echo "New resource/item with ID $resource_id created."

# 4. We now use the new resource ID to make a PATCH request to modify the title,
# body, and status.
elapi patch items --id "$resource_id" --data "{\"title\": \"Resource Material ${RANDOM_NUM}\",
\"body\": \"This resource is created via elAPI.\", \"status\": 6}" 1>/dev/null
# eLabFTW sends the resource data in JSON when the PATCH request goes through.
# elAPI will print that data to STDOUT. We actually don't need that data.
# So, we redirect it to /dev/null/.
# We will check on the browser if our resource creation and modification was successful.
echo "Resource title, body and status successfully changed."

# We could also delete the resource
#elapi delete items --id "$resource_id" 1>/dev/null
#echo "Resource successfully deleted."
