import json

from src import ProperPath
from src.information import Information

users = Information(unit_name="users")
users_data_path = users.get_extensive_unit_data_path(unit_id=None, ignore_existing_filename=True)
# unit_id=None explicitly sets all users
# ignore_existing_filename=False: Doesn't download data again if filename already exists

teams = Information(unit_name="teams")
teams_data = teams.get_unit_data(unit_id=None)
teams_data_path = teams.export_data(suppress_message=True, data=teams_data,
                                    export_path='cache', ignore_existing_filename=True)

with ProperPath(users_data_path).open(mode="r", encoding="utf-8") as file:
    users_data = json.loads(file.read())

with ProperPath(teams_data_path).open(mode="r", encoding="utf-8") as file:
    teams_data = json.loads(file.read())


def get_team_owners(all_users_data: dict = users_data,
                    all_teams_data: dict = teams_data):
    team_owners = {}
    # Generate team owners
    for u in all_users_data:
        for team in u["teams"]:  # O(n^2): u["teams"] is again an iterable!
            if team["is_owner"] == 1:
                uid = u["userid"]
                owner = {uid: {}}
                owner[uid]["owner_name"] = u['fullname']
                owner[uid]["owner_email"] = u['email']
                owner[uid]["owner_user_id"] = uid  # duplicate information to avoid ambiguity
                if not team_owners.get(team['id']):
                    team_owners[team['id']] = {}
                    team_owners[team['id']]["team_name"] = team['name']
                    team_owners[team["id"]]["owners"] = [owner]
                    team_owners[team["id"]]["team_id"] = team["id"]  # duplicate information to avoid ambiguity
                else:
                    team_owners[team["id"]]["owners"].append(owner)
    # Add team creation date to team owners
    for team in all_teams_data:
        if team['id'] in team_owners.keys():
            team_owners[team['id']]['team_created_at'] = team['created_at']
    return team_owners


if __name__ == '__main__':
    print(get_team_owners())
