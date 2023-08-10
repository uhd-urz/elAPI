import json
from pathlib import Path
from src.information import Information
from rich import print

users = Information(unit_name="users")
users_data_path = users.get_extensive_unit_data_path(unit_id=None, ignore_existing_filename=True)
# unit_id=None explicitly sets all users
# ignore_existing_filename=False: Doesn't download data again if filename already exists

teams = Information(unit_name="teams")
teams_data = teams.get_unit_data(unit_id=None)
teams_data_path = teams.export_data(suppress_message=True, data=teams_data, export_path='cache',
                                    ignore_existing_filename=True)

with open(Path(users_data_path), mode="r", encoding="utf-8") as file:
    users_data = json.loads(file.read())

with open(Path(teams_data_path), mode="r", encoding="utf-8") as file:
    teams_data = json.loads(file.read())

if __name__ == '__main__':

    team_owners = {}
    for u in users_data:
        for team in u["teams"]:  # O(n^2): u["teams"] is again an iterable!
            if team["is_owner"] == 1:
                team_owners[team['id']] = {}
                team_owners[team['id']]["team_name"] = team['name']
                team_owners[team['id']]["team_id"] = team['id']
                team_owners[team['id']]["owner_name"] = u['fullname']
                team_owners[team['id']]["owner_email"] = u['email']
                team_owners[team['id']]["owner_user_id"] = u["userid"]

    for team in teams_data:
        if team['id'] in team_owners.keys():
            team_owners[team['id']]['team_created_at'] = team['created_at']
    print(team_owners)
