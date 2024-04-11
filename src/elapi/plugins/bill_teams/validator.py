from dataclasses import dataclass
from typing import Optional, Callable, Union

from ...loggers import Logger
from ...styles import FormatError
from ...validators import Validator, ValidationError

logger = Logger()


# noinspection SpellCheckingInspection
@dataclass
class OwnersDataSpecification:
    TEAM_OWNER_ID: str = "team_owner_id"
    TEAM_OWNER_FIRST_NAME: str = "team_owner_firstname"
    TEAM_OWNER_LAST_NAME: str = "team_owner_lastname"
    TEAM_OWNER_EMAIL: str = "team_owner_email"
    TEAM_BILLABLE: str = "team_billable"
    BILLING_UNIT_COST: str = "billing_unitcost"
    BILLING_MANAGEMENT_FACTOR: str = "billing_managementfactor"
    BILLING_MANAGEMENT_LIMITL: str = "billing_managementlimit"
    BILLING_INSTITUTE1: str = "billing_institute1"
    BILLING_INSTITUTE2: str = "billing_institute2"
    BILLING_PERSON_GROUP: str = "billing_persongroup"
    BILLING_STREET: str = "billing_street"
    BILLING_POSTAL_CODE: str = "billing_postalcode"
    BILLING_CITY: str = "billing_city"
    BILLING_INT_EXT: str = "billing_intext"
    BILLING_ACCOUNT_UNIT: str = "billing_accunit"
    TEAM_ACRONYM_EXT: str = "team_acronymext"
    TEAM_ACRONYM_INT: str = "team_acronymint"
    TEAM_GONE: str = "team_gone"
    TEAM_SPECIAL: str = "team_special"
    TEAM_LIME_SURVEY: str = "team_limesurvey"
    TEAM_SIGNED_CONTRACT: str = "team_signedcontract"
    TEAM_END_DATE: str = "team_enddate"


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
                    spec.BILLING_MANAGEMENT_LIMITL,
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
