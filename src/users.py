import json

import elabapi_python
from src.defaults import api_client
from pathlib import Path
import ast


class Users:
    def __init__(self, item=None, user_data_export_path="./data"):
        self.item = item if item else elabapi_python.UsersApi(api_client)
        self.user_data_export_path = user_data_export_path

    def get_user_data(self, user_id: int = None):
        """Fetches the current user list from direct API response without any changing the format."""
        return self.item.read_users() if not user_id else self.item.read_user(id=user_id)

    def export_users(self, filename: str = None):
        """Writes user data from converted JSON to a JSON file in pre-defined directory"""
        data_path = Path(self.user_data_export_path)
        data_path.mkdir(parents=True, exist_ok=True)  # Creates the directory if it doesn't exist
        with open(data_path / (filename if filename else "user_data.json"), "w", encoding="utf-8") as file:
            file.write(self._convert_to_json(self.get_user_data(user_id=None)))

    @staticmethod
    def _convert_to_dict(data):
        """Converts user data to Python dictionary, so it can be later parsed with ease"""
        return [ast.literal_eval(str(_)) for _ in data]

    def _convert_to_json(self, data):
        """Converts dictionary to JSON"""
        return json.dumps(self._convert_to_dict(data))


if __name__ == '__main__':
    # item = elabapi_python.UsersApi(api_client)
    # print(item.read_users())
    # print(len(item.read_users()))  # only returns the active/unarchived users
    u = Users()
    print(u.get_user_data())
    # u.export_users()
