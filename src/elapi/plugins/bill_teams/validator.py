from dataclasses import dataclass
from typing import Optional, Callable, Union

from ...loggers import Logger
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
                    f"Column '{e}' does not exist in owners data! Owners data might not be valid."
                ) from e
            else:
                return value

    def set(
        self, team_id: Union[str, int], column_name: str, value: Union[str, int]
    ) -> None:
        try:
            self.get(team_id, column_name)
        except KeyError as e:
            raise e
        self.data[team_id][column_name] = value

    def items(self) -> dict:
        return self.data


class OwnersInformationValidator(Validator):
    def __init__(self, owners_information: dict, teams_information: list[dict, ...]):
        self.owners = OwnersInformationContainer(owners_information)
        self.teams = teams_information

    def get_sanitized(
        self, team_id: str, column_name: str, stringent: bool = False
    ) -> Optional[str]:
        import math

        value = self.owners.get(team_id, column_name)
        try:
            if math.isnan(float(value or None)):
                logger.info(
                    f"'NaN' entry in column '{column_name}' of team ID '{team_id}'."
                )
                if stringent:
                    raise ValidationError(
                        f"Column '{column_name}' of '{team_id}' cannot have 'NaN' entries!"
                    )
                return None
        except TypeError as e:
            logger.info(
                f"Blank entry in column '{column_name}' of team ID '{team_id}'."
            )
            if stringent:
                raise ValidationError(
                    f"Null value found! Column '{column_name}' of team ID '{team_id}' cannot have null entries."
                ) from e
            return None
        except ValueError as e:
            if stringent:
                raise ValidationError(
                    f"Invalid value '{value}' in column '{column_name}' of team ID '{team_id}'!"
                ) from e
        return str(value).strip()

    def get_formatted(
        self,
        team_id: str,
        column_name: str,
        expected_pattern: str,
        function_to_apply: Callable,
        sanitize: bool = True,
    ) -> str:
        import re

        value = self.owners.get(team_id, column_name)
        value = (
            self.get_sanitized(team_id, column_name, stringent=True)
            if sanitize
            else value
        )
        if not re.match(rf"{expected_pattern}", value):
            raise ValidationError(
                f"Unexpected value '{value}' in column '{column_name}' of team ID '{team_id}'!"
            )
        return function_to_apply(value)

    # noinspection PyUnboundLocalVariable
    def validate(self):
        spec = OwnersDataSpecification()
        try:
            for team in self.teams:
                team_id = team["id"]
                # Validate team owner identifying information
                self.owners.set(
                    team_id,
                    spec.TEAM_OWNER_ID,
                    self.get_sanitized(team_id, spec.TEAM_OWNER_ID),
                )
                self.owners.set(
                    team_id,
                    spec.TEAM_OWNER_FIRST_NAME,
                    self.get_sanitized(team_id, spec.TEAM_OWNER_FIRST_NAME),
                )
                self.owners.set(
                    team_id,
                    spec.TEAM_OWNER_LAST_NAME,
                    self.get_sanitized(team_id, spec.TEAM_OWNER_LAST_NAME),
                )
                self.owners.set(
                    team_id,
                    spec.TEAM_OWNER_EMAIL,
                    self.get_sanitized(team_id, spec.TEAM_OWNER_EMAIL),
                )
                # Validate team billing factors
                self.owners.set(
                    team_id,
                    spec.TEAM_BILLABLE,
                    self.get_formatted(team_id, spec.TEAM_BILLABLE, r"^[01]$", int),
                )
                self.owners.set(
                    team_id,
                    spec.BILLING_UNIT_COST,
                    self.get_formatted(
                        team_id, spec.BILLING_UNIT_COST, r"^\d*\.?\d+$", float
                    ),
                )
                self.owners.set(
                    team_id,
                    spec.BILLING_MANAGEMENT_FACTOR,
                    self.get_formatted(
                        team_id, spec.BILLING_MANAGEMENT_FACTOR, r"^\d*\.?\d+$", float
                    ),
                )
                self.owners.set(
                    team_id,
                    spec.BILLING_MANAGEMENT_LIMITL,
                    self.get_formatted(
                        team_id,
                        spec.BILLING_MANAGEMENT_LIMITL,
                        r"^\d*\.?\d+$|^-1$",
                        float,
                    ),
                )
                # Validate billing address related information
                self.owners.set(
                    team_id,
                    spec.BILLING_INSTITUTE1,
                    self.get_sanitized(team_id, spec.BILLING_INSTITUTE1),
                )
                self.owners.set(
                    team_id,
                    spec.BILLING_INSTITUTE2,
                    self.get_sanitized(team_id, spec.BILLING_INSTITUTE2),
                )
                self.owners.set(
                    team_id,
                    spec.BILLING_PERSON_GROUP,
                    self.get_sanitized(team_id, spec.BILLING_PERSON_GROUP),
                )
                self.owners.set(
                    team_id,
                    spec.BILLING_STREET,
                    self.get_sanitized(team_id, spec.BILLING_STREET),
                )
                self.owners.set(
                    team_id,
                    spec.BILLING_POSTAL_CODE,
                    self.get_sanitized(team_id, spec.BILLING_POSTAL_CODE),
                )
                self.owners.set(
                    team_id,
                    spec.BILLING_CITY,
                    self.get_sanitized(team_id, spec.BILLING_CITY),
                )
                self.owners.set(
                    team_id,
                    spec.BILLING_INT_EXT,
                    self.get_sanitized(team_id, spec.BILLING_INT_EXT),
                )
                self.owners.set(
                    team_id,
                    spec.BILLING_ACCOUNT_UNIT,
                    self.get_sanitized(team_id, spec.BILLING_ACCOUNT_UNIT),
                )
                self.owners.set(
                    team_id,
                    spec.TEAM_ACRONYM_INT,
                    self.get_sanitized(team_id, spec.TEAM_ACRONYM_INT),
                )
                self.owners.set(
                    team_id,
                    spec.TEAM_ACRONYM_EXT,
                    self.get_sanitized(team_id, spec.TEAM_ACRONYM_EXT),
                )
        except KeyError as e:
            raise ValidationError(str(e).strip('"'))
            # See: https://stackoverflow.com/a/48850520, https://stackoverflow.com/a/24999035

        for team_id in self.owners.items():
            if team_id not in [team["id"] for team in self.teams]:
                logger.info(
                    f"Team ID '{team_id}' exists in owners data that doesn't exist in eLabFTW teams database."
                )
        return self.owners.items()
