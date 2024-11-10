from dataclasses import dataclass
from datetime import datetime

from .names import (
    REGISTRY_SUB_PLUGIN_NAME,
    TARGET_GROUP_NAME,
    TARGET_GROUP_OWNER_NAME,
    TARGET_GROUP_NAME_SINGULAR,
)
from ...configuration import DEFAULT_EXPORT_DATA_FORMAT
from ...plugins.commons.export import Export

BILLING_INFO_OUTPUT_EXTENSION: str = DEFAULT_EXPORT_DATA_FORMAT
BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB: str = f"{TARGET_GROUP_NAME}_info"
BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB: str = f"{TARGET_GROUP_OWNER_NAME}_info"
REGISTRY_FILE_NAME_STEM: str = REGISTRY_SUB_PLUGIN_NAME
REGISTRY_FILE_EXTENSION: str = DEFAULT_EXPORT_DATA_FORMAT
REGISTRY_FILE_NAME: str = f"{REGISTRY_SUB_PLUGIN_NAME}.{REGISTRY_FILE_EXTENSION}"
REGISTRY_KEY_TEAMS_INFO_DATE: str = (
    f"{BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB}_date"
)
REGISTRY_KEY_OWNERS_INFO_DATE: str = (
    f"{BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB}_date"
)
OUTPUT_TABLE_FILE_NAME_STUB: str = "output_table"

BILLING_INFO_OUTPUT_DATETIME_PARSE_FORMAT: str = (
    Export.EXPORT_FILE_NAME_PREFIX_FORMAT  # Supported by dateutil parser.isoparse
)
BILLING_INFO_OUTPUT_DATETIME_PARSE_SIMPLE_REGEX_PATTERN: str = r"^\d+-\d{2}-\d{2}_\d{6}"
CLI_DATE_VALID_FORMAT: str = "YYYY-MM"
REGISTRY_TIME_FORMAT: str = "%H:%M:%S"  # Similar to Export.EXPORT_TIME_FORMAT
CLI_DATE_PARSE_SIMPLE_REGEX_PATTERN: str = r"^\d+-\d{2}$"
BILLING_PERIOD: int = 5
BILLING_BASE_DATE: datetime = datetime.today().replace(
    day=1, hour=0, minute=0, second=0, microsecond=0
)  # Base date is not the 15th day of a month but the 1st day of a month.
OUTPUT_TABLE_NAN_INDICATOR: str = "NaN"


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


@dataclass
class _RegistryCommunicationSpecification:
    EXISTS_IN_OWNERS_INFO_BUT_MISSING_IN_TEAMS_INFO: str = (
        "EXISTS_IN_OWNERS_INFO_BUT_MISSING_IN_TEAMS_INFO"
    )
    USER_REQUESTED_FILE_LOG_FOR_MISSING_TEAMS_INFO: str = (
        "USER_REQUESTED_FILE_LOG_FOR_MISSING_TEAMS_INFO"
    )


@dataclass
class RegistryDataSpecification:
    REGISTRY_LAST_UPDATED: str = "last_updated"
    TEAMS_INFO_DATE: str = f"{BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB}_date"
    OWNERS_INFO_DATE: str = f"{BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB}_date"
    TEAM_NAME: str = f"{TARGET_GROUP_NAME_SINGULAR}_name"
    TEAM_ACTIVE_MEMBER_COUNT: str = "active_member_count"
    TEAM_ON_TRIAL: str = "on_trial"
    EXTRAS: str = "extras"
    TEAM_OWNER_NAME: str = f"{TARGET_GROUP_NAME_SINGULAR}_owner_name"
    TEAM_OWNER_EMAIL: str = f"{TARGET_GROUP_NAME_SINGULAR}_owner_email"
    TEAM_BILL_GENERATION_METADATA: str = "bill_generation_metadata"
    BILL_GENERATION_METADATA_INCLUDE_IN_OUTPUT_TABLE: str = "include_in_output_table"
    BILL_GENERATION_METADATA_BILLING_COUNTER: str = "billing_counter"
    BILL_GENERATION_METADATA_LAST_UPDATED: str = REGISTRY_LAST_UPDATED
    REGISTRY_CLI_IMPLICIT_ARG_INCLUDE_ALL_TEAMS: str = "all"
    REGISTRY_CLI_CMD_INCLUDE_TEAM: str = "include"
    REGISTRY_CLI_CMD_EXEMPT_TEAM: str = "exempt"
    REGISTRY_CLI_ARG_INCREMENT_TEAM_BILLING_COUNTER: str = "increment"
    REGISTRY_CLI_ARG_DECREMENT_TEAM_BILLING_COUNTER: str = "decrement"


@dataclass
class OutputTableHeaderSpecification:
    ACCOUNT_NUMBER: str = "Rechn-Nr"
    COMPANY: str = "Firma"
    DEPARTMENT: str = "Abteilung"
    PERSON_DEPARTMENT: str = "Person-Abteilung"
    STREET: str = "Straße"
    POSTAL_CODE: str = "PLZ"
    CITY: str = "Ort"
    INTERNAL_OR_EXTERNAL: str = "intern/extern"
    DATE: str = "Datum"
    COST_CENTER_ACRONYM: str = "Kostenstelle-Acronym"
    BILLING_TIME_1: str = "Abrechn-Zeit_1"  # Billing month and year
    MEMBER_COUNT_1: str = "Menge_1"  # Number of total active members
    SERVICE_1: str = "Leistung_1"  # Service description
    AMOUNT_1: str = "Betrag_1"  # Monthly fee per member
    TOTAL_1: str = "Gesamt_1"  # Monthly total bill
    BILLING_TIME_2: str = "Abrechn-Zeit_2"
    MEMBER_COUNT_2: str = "Menge_2"
    SERVICE_2: str = "Leistung_2"
    AMOUNT_2: str = "Betrag_2"
    TOTAL_2: str = "Gesamt_2"
    BILLING_TIME_3: str = "Abrechn-Zeit_3"
    MEMBER_COUNT_3: str = "Menge_3"
    SERVICE_3: str = "Leistung_3"
    AMOUNT_3: str = "Betrag_3"
    TOTAL_3: str = "Gesamt_3"
    BILLING_TIME_4: str = "Abrechn-Zeit_4"
    MEMBER_COUNT_4: str = "Menge_4"
    SERVICE_4: str = "Leistung_4"
    AMOUNT_4: str = "Betrag_4"
    TOTAL_4: str = "Gesamt_4"
    BILLING_TIME_5: str = "Abrechn-Zeit_5"
    MEMBER_COUNT_5: str = "Menge_5"
    SERVICE_5: str = "Leistung_5"
    AMOUNT_5: str = "Betrag_5"
    TOTAL_5: str = "Gesamt_5"
    BILLING_TIME_6: str = "Abrechn-Zeit_6"
    MEMBER_COUNT_6: str = "Menge_6"
    SERVICE_6: str = "Leistung_6"
    AMOUNT_6: str = "Betrag_6"
    TOTAL_6: str = "Gesamt_6"
    VAT_RATE: str = "USt.-Satz"
    GRAND_TOTAL: str = "Summe_ges"  # All monthly total
    TAX: str = "Steuer"
    TAXABLE_YES_OR_NO: str = "Steuerpflichtig\nBGA ja, nein"
    TAX_1: str = "Steuer_1"
    GRAND_TOTAL_1: str = "Summe_ges1"
    IN_WORDS: str = "In_Worten"
    COST_CENTER_OR_ORDER: str = "Kostenst./Auftr."
    GL_ACCOUNT_REVENUE: str = "Sachkonto Einnahme"
    GL_ACCOUNT_PAYOUT: str = "Sachkonto Auszahlung"
    ST_KZ: str = "St.Kz."
    TEXT_0: str = "Text0"
    TEXT_1: str = "Text1"
    TEXT_2: str = "Text2"
    FILE: str = "Akte"
    WV: str = "WV:"
    NET_TOTAL: str = "Gesamt netto"
    TOTAL_VAT: str = "Gesamt MWST"


@dataclass
class OutputTableBillingPeriodHeaderSpecification:
    BILLING_TIME: str = "Abrechn-Zeit"  # Billing month and year
    MEMBER_COUNT: str = "Menge"  # Number of total active members
    SERVICE: str = "Leistung"  # Service description
    AMOUNT: str = "Betrag"  # Monthly fee per member
    TOTAL: str = "Gesamt"  # Monthly total bill


@dataclass
class OutputTableFixedTextsSpecification:
    SERVICE: str = "Nutzung “eLabFTW” Abrechnungszeitraum (Account-Monate)"


@dataclass
class IgnoreBillingGlobalParametersSpecification:
    ON_TRIAL: bool = True
    TEAM_BILLABLE: int = 0
    BILLING_MANAGEMENT_FACTOR: int = 0
    BILLING_MANAGEMENT_LIMIT: int = 0


@dataclass
class GermanMonthNames:
    JANUARY: str = "Januar"
    FEBRUARY: str = "Februar"
    MARCH: str = "März"
    APRIL: str = "April"
    MAY: str = "Mai"
    JUNE: str = "Juni"
    JULY: str = "Juli"
    AUGUST: str = "August"
    SEPTEMBER: str = "September"
    OCTOBER: str = "Oktober"
    NOVEMBER: str = "November"
    DECEMBER: str = "Dezember"


owners_spec = OwnersDataSpecification()
ignore_billing_spec = IgnoreBillingGlobalParametersSpecification()
registry_spec = RegistryDataSpecification()
_registry_com_spec = _RegistryCommunicationSpecification()
ot_header_spec = OutputTableHeaderSpecification()
ot_header_billing_period_spec = OutputTableBillingPeriodHeaderSpecification()
ot_fixed_texts_spec = OutputTableFixedTextsSpecification()
de_months = GermanMonthNames()


def get_billing_period_header_entry(entry_name: str, entry_month_no: int):
    if entry_name not in ot_header_billing_period_spec.__dict__.values():
        raise ValueError(
            f"Entry name must be a member of "
            f"{ot_header_billing_period_spec.__class__.__name__}."
        )
    if not 0 < entry_month_no <= BILLING_PERIOD + 1:
        raise ValueError(
            f"Output table is limited to {BILLING_PERIOD + 1} "
            f"months of billing records at the moment."
        )
    return f"{entry_name}_{entry_month_no}"


METADATA_TO_OUTPUT_TABLE_TRANSLATOR: dict = {
    owners_spec.BILLING_INSTITUTE1: ot_header_spec.COMPANY,
    owners_spec.BILLING_INSTITUTE2: ot_header_spec.DEPARTMENT,
    owners_spec.BILLING_PERSON_GROUP: ot_header_spec.PERSON_DEPARTMENT,
    owners_spec.BILLING_STREET: ot_header_spec.STREET,
    owners_spec.BILLING_POSTAL_CODE: ot_header_spec.POSTAL_CODE,
    owners_spec.BILLING_CITY: ot_header_spec.CITY,
    owners_spec.BILLING_INT_EXT: ot_header_spec.INTERNAL_OR_EXTERNAL,
    owners_spec.BILLING_ACCOUNT_UNIT: ot_header_spec.COST_CENTER_ACRONYM,
}

METADATA_BILLING_INTERNAL_EXTERNAL_TO_BOOL: dict = {"int": True, "ext": False}
