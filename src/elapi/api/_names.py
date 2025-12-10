from enum import IntEnum
from pathlib import Path


class ElabUserGroups(IntEnum):
    """eLabFTW's default permission groups.
    See: https://github.com/elabftw/elabftw/blob/master/src/Enums/Usergroup.php
    """

    sysadmin = 1
    admin = 2
    user = 4

    @classmethod
    def group_names(cls) -> list[str]:
        return [_.name for _ in cls]

    @classmethod
    def group_values(cls) -> list[int]:
        return [_.value for _ in cls]

    @classmethod
    def get_group_from_admin_status(cls, status: bool) -> int:
        return cls.admin.value if status else cls.user.value


class ElabScopes(IntEnum):
    self = 1
    team = 2
    everything = 3


class ElabVersionDefaults:
    supported_versions: tuple[str, ...] = (
        "5.3.9",
        "5.3.8",
        "5.3.7",
        "5.3.6",
        "5.3.5",
        "5.3.4",
        "5.3.3",
        "5.3.2",
        "5.3.1",
        "5.3.0",
        "5.2.8",
        "5.2.7",
        "5.2.6",
        "5.2.5",
        "5.2.4",
        "5.2.3",
        "5.2.2",
        "5.2.1",
        "5.2.0",
        "5.1.15",
    )
    versions_dir: Path = Path(__file__).parent / "_supported_versions"
    file_ext: str = "json"
