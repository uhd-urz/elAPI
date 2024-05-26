from dataclasses import dataclass
from datetime import datetime

from ...configuration import DEFAULT_EXPORT_DATA_FORMAT

BILLING_INFO_OUTPUT_EXTENSION: str = DEFAULT_EXPORT_DATA_FORMAT
BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB: str = "teams_info"
BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB: str = "owners_info"
BILLING_INFO_OUTPUT_DATETIME_PARSE_FORMAT: str = (
    "%Y-%m-%d_%H%M%S"  # Supported by dateutil parser.isoparse
)
BILLING_INFO_OUTPUT_DATETIME_PARSE_SIMPLE_REGEX_PATTERN: str = (
    "^\d+-\d{2}-\d{2}_\d{6}"
)
CLI_DATE_VALID_FORMAT: str = "YYYY-MM"
CLI_DATE_PARSE_SIMPLE_REGEX_PATTERN: str = "^\d+-\d{2}$"
BILLING_PERIOD: int = 5
BILLING_BASE_DATE: datetime = datetime.today().replace(
    day=1, hour=0, minute=0, second=0, microsecond=0
)  # Base date is not the 15th day of a month but the 1st day of a month.


@dataclass
class OwnersDataSpecification:
    TEAM_OWNER_ID: str = "team_owner_id"
    TEAM_OWNER_FIRST_NAME: str = "team_owner_firstname"
    TEAM_OWNER_LAST_NAME: str = "team_owner_lastname"
    TEAM_OWNER_EMAIL: str = "team_owner_email"
    TEAM_BILLABLE: str = "team_billable"
    BILLING_UNIT_COST: str = "billing_unitcost"
    BILLING_MANAGEMENT_FACTOR: str = "billing_managementfactor"
    BILLING_MANAGEMENT_LIMIT: str = "billing_managementlimit"
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
