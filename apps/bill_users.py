import json
from pathlib import Path
from src.users import Users

if __name__ == '__main__':
    with open(Path("../data/user_data.json"), mode="r", encoding="utf-8") as file:
        user_data = json.loads(file.read())
        # for u in user_data:
        #     print(f'{u["fullname"]}, {u["email"]}, {u["archived"]}')

    u = Users()
    print(u.get_user_data())  # mine: user_id=12
    # teams = elabapi_python.TeamsApi(api_client)
    # print(teams.read_teams())
    # print(elabapi_python.StatusApi(api_client).read_team_status(id=3))
