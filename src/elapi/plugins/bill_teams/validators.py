import datetime
from pathlib import Path
from typing import Optional, Callable, Union, Iterable

from .specification import OwnersDataSpecification
from ...loggers import Logger
from ...path import ProperPath
from ...styles import FormatError
from ...core_validators import Validator, ValidationError

logger = Logger()


class SanitizationError(Exception): ...


class OwnersInformationContainer:
    def __init__(self, data: dict, /):
        self.data = data

    def get(self, team_id: Union[str, int], column_name: str) -> Union[int, str]:
        if not isinstance(team_id, int):
            try:
                team_id = int(team_id)
            except (ValueError, TypeError):
                raise ValueError("team_id must be an integer or a string!")
        try:
            team = self.data[team_id]
        except KeyError as e:
            raise KeyError(f"Team ID '{team_id}' does not exist in owners data!") from e
        else:
            try:
                value = team[column_name]
            except KeyError as e:
                raise KeyError(
                    f"Column {e} does not exist in owners data! Owners data might not be valid."
                ) from e
            else:
                return value

    def items(self) -> dict:
        return self.data


class OwnersInformationModifier:
    def __init__(self, owners_data_container: OwnersInformationContainer, /):
        self.owners = owners_data_container

    def set(
        self,
        team_id: Union[str, int],
        column_name: str,
        value: Union[str, int, float, type(None)],
    ) -> None:
        try:
            self.owners.get(team_id, column_name)
        except KeyError as e:
            raise e
        if not isinstance(value, (str, int, float, type(None))):
            raise ValueError(
                "value must be an string or an integer or a float or NoneType!"
            )
        self.owners.items()[team_id][column_name] = value

    @staticmethod
    def _sanitize(
        value: Union[str, int, float, type(None)],
        reference: str,
        allow_null: bool = True,
        stringent: bool = False,
    ) -> Optional[str]:
        import math

        try:
            if math.isnan(float(value or None)):
                if not allow_null:
                    logger.info(f"'NaN' entry in {reference}.")
                if stringent:
                    raise SanitizationError(
                        f"{reference.capitalize()} cannot have 'NaN' entries!"
                    )
                return None
        except TypeError as e:
            if not allow_null:
                logger.info(f"Blank entry in {reference}.")
            if stringent:
                raise SanitizationError(
                    f"Null value found! {reference.capitalize()} cannot have null entries."
                ) from e
            return None
        except ValueError as e:
            if stringent:
                raise SanitizationError(
                    f"Invalid value '{value}' in {reference}!"
                ) from e
        return str(value).strip()

    def format(
        self,
        team_id: Union[str, int],
        column_name: str,
        expected_pattern: Optional[str] = None,
        function_to_apply: Optional[Callable] = None,
        allow_null: bool = True,
        stringent: bool = False,
    ) -> None:
        import re

        reference = f"column '{column_name}' of team ID {team_id}"
        value = self._sanitize(
            self.owners.get(team_id, column_name),
            reference=reference,
            allow_null=allow_null,
            stringent=stringent,
        )
        if expected_pattern is not None:
            if not re.match(rf"{expected_pattern}", value):
                raise FormatError(f"Unexpected value '{value}' in {reference}!")
        if not function_to_apply:
            function_to_apply = lambda x: x  # noqa: E731
        self.set(team_id, column_name, function_to_apply(value))


class OwnersInformationValidator(Validator):
    def __init__(self, owners_information: dict, teams_information: list[dict, ...]):
        self.owners = OwnersInformationContainer(owners_information)
        self.teams = teams_information

    # noinspection PyUnboundLocalVariable
    def validate(self):
        spec = OwnersDataSpecification()
        formatter = OwnersInformationModifier(self.owners)
        try:
            for team in self.teams:
                team_id = team["id"]
                # Validate team owner identifying information
                formatter.format(team_id, spec.TEAM_OWNER_ID, allow_null=False)
                formatter.format(team_id, spec.TEAM_OWNER_FIRST_NAME)
                formatter.format(team_id, spec.TEAM_OWNER_LAST_NAME)
                formatter.format(team_id, spec.TEAM_OWNER_EMAIL, allow_null=False)
                # Validate team billing factors
                formatter.format(
                    team_id,
                    spec.TEAM_BILLABLE,
                    expected_pattern=r"^[01]$",
                    function_to_apply=int,
                    allow_null=False,
                    stringent=True,
                )
                formatter.format(
                    team_id,
                    spec.BILLING_UNIT_COST,
                    expected_pattern=r"^\d*\.?\d+$",
                    function_to_apply=float,
                    allow_null=False,
                    stringent=True,
                )
                formatter.format(
                    team_id,
                    spec.BILLING_MANAGEMENT_FACTOR,
                    expected_pattern=r"^\d*\.?\d+$",
                    function_to_apply=float,
                    allow_null=False,
                    stringent=True,
                )
                formatter.format(
                    team_id,
                    spec.BILLING_MANAGEMENT_LIMIT,
                    expected_pattern=r"^\d*\.?\d+$|^-1$",
                    function_to_apply=lambda x: -1 if float(x) == -1 else float(x),
                    allow_null=False,
                    stringent=True,
                )
                # Validate billing address related information
                formatter.format(team_id, spec.BILLING_INSTITUTE1)
                formatter.format(team_id, spec.BILLING_INSTITUTE2)
                formatter.format(team_id, spec.BILLING_PERSON_GROUP)
                formatter.format(team_id, spec.BILLING_STREET)
                formatter.format(team_id, spec.BILLING_POSTAL_CODE)
                formatter.format(team_id, spec.BILLING_CITY)
                formatter.format(team_id, spec.BILLING_INT_EXT)
                formatter.format(team_id, spec.BILLING_ACCOUNT_UNIT)
                formatter.format(team_id, spec.TEAM_ACRONYM_INT)
                formatter.format(team_id, spec.TEAM_ACRONYM_EXT)
        except KeyError as e:
            raise ValidationError(str(e).strip('"'))
            # See: https://stackoverflow.com/a/48850520, https://stackoverflow.com/a/24999035
        except (SanitizationError, FormatError) as e:
            raise ValidationError(e)

        for team_id in self.owners.items():
            if team_id not in [team["id"] for team in self.teams]:
                logger.info(
                    f"Team ID '{team_id}' exists in owners data that doesn't exist in eLabFTW teams database."
                )
        return self.owners.items()


class BillingInformationPathValidator(Validator):
    def __init__(
        self,
        root_dir: Union[None, str, ProperPath, Path],
        year: Union[int, str],
        month: Union[int, str],
        **kwargs,
    ):
        from ...loggers import Logger

        self.root_dir = root_dir
        self.year = year
        self.month = month
        self.err_logger = kwargs.get("err_logger", Logger())

    @property
    def root_dir(self):
        return self._path

    @root_dir.setter
    def root_dir(self, value):
        if not isinstance(value, str) and isinstance(value, Iterable):
            raise ValueError(
                f"{self.__class__.__name__} root path value '{value}' cannot be a "
                f"container (iterable except strings)."
            )
        if not isinstance(value, (str, ProperPath, Path)):
            raise ValueError(f"'{value}' must be an instance of str, ProperPath, Path.")
        self._path = value

    @property
    def year(self) -> str:
        return self._year

    @year.setter
    def year(self, value):
        if isinstance(value, int):
            try:
                value = str(value)
            except TypeError:
                raise ValueError(
                    "year attribute must be an instance of str or integer."
                )
            self._year = value

    @property
    def month(self) -> str:
        return self._month

    @month.setter
    def month(self, value):
        if isinstance(value, int):
            try:
                value = f"{value:02d}"
            except TypeError:
                raise ValueError(
                    "month attribute must be an instance of str or integer."
                )
            self._month = value

    def validate(self) -> tuple[ProperPath, ProperPath]:
        import re
        from dateutil import parser
        from collections import namedtuple
        from .specification import (
            BILLING_INFO_OUTPUT_EXTENSION,
            BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB,
            BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB,
            BILLING_INFO_OUTPUT_DATETIME_PARSE_SIMPLE_REGEX_PATTERN,
        )

        if not isinstance(root := self.root_dir, ProperPath):
            try:
                root = ProperPath(self.root_dir, err_logger=self.err_logger)
            except (ValueError, TypeError):
                # Unlikely this will ever be triggered as we already do an instance check
                raise ValidationError(
                    f"Given root directory '{self.root_dir}' is not a valid path!"
                )
        if not root.expanded.exists():
            raise ValidationError(f"Given root path '{self.root_dir}' doesn't exist!")
        if not (root / self.year).expanded.exists():
            raise ValidationError(
                f"Path in root directory with year {self.year}: '{root / self.year}' doesn't exist!"
            )
        if not (path := root / self.year / self.month).expanded.exists():
            raise ValidationError(
                f"Path in root directory with month '{self.month}' of year '{self.year}': "
                f"'{root / self.year/ self.month}' doesn't exist!"
            )
        PathInfoTuple = namedtuple("PathInfoTuple", ("parent", "name", "date"))
        teams_info_files: list[PathInfoTuple[Path, str, datetime]] = []
        owners_info_files: list[PathInfoTuple[Path, str, datetime]] = []

        for p in path.expanded.iterdir():
            if re.match(
                rf"{BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB[::-1]}",
                str(p).removesuffix(f".{BILLING_INFO_OUTPUT_EXTENSION}")[::-1],
                re.IGNORECASE,
            ):
                if file_date := re.match(
                    rf"{BILLING_INFO_OUTPUT_DATETIME_PARSE_SIMPLE_REGEX_PATTERN}",
                    p.name,
                ):
                    if file_date is None:
                        continue
                    try:
                        date = parser.isoparse(
                            p.name[file_date.start() : file_date.end()]
                        )
                    except ValueError:
                        logger.info(
                            f"Detected '{BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB}' in file '{p}', but "
                            f"the datetime in file name '{p.name}' is not a valid ISO 8601 format. "
                            f"The file will be ignored."
                        )
                        continue
                    else:
                        teams_info_files.append(PathInfoTuple(p.parent, p.name, date))
            if re.match(
                rf"{BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB[::-1]}",
                str(p).removesuffix(f".{BILLING_INFO_OUTPUT_EXTENSION}")[::-1],
                re.IGNORECASE,
            ):
                if file_date := re.match(
                    rf"{BILLING_INFO_OUTPUT_DATETIME_PARSE_SIMPLE_REGEX_PATTERN}",
                    p.name,
                ):
                    if file_date is None:
                        continue
                    try:
                        date = parser.isoparse(
                            p.name[file_date.start() : file_date.end()]
                        )
                    except ValueError:
                        logger.info(
                            f"Detected '{BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB}' file in '{p}', but "
                            f"the datetime in file name '{p.name}' is not a valid ISO 8601 format. "
                            f"The file will be ignored."
                        )
                        continue
                    else:
                        owners_info_files.append(PathInfoTuple(p.parent, p.name, date))
        if not teams_info_files:
            raise ValidationError(
                f"No '{BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB}' file that matches the valid naming format "
                f"was found in path '{path}' for month '{self.month}' of '{self.year}'."
            )
        if not owners_info_files:
            raise ValidationError(
                f"No '{BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB}' file that matches the valid naming format "
                f"was found in path '{path}' for month '{self.month}' of '{self.year}'."
            )
        latest_teams_info_tuple = max(teams_info_files, key=lambda x: x.date)
        latest_owners_info_tuple = max(owners_info_files, key=lambda x: x.date)
        return (
            latest_teams_info_tuple.parent / latest_teams_info_tuple.name,
            latest_owners_info_tuple.parent / latest_owners_info_tuple.name,
        )
