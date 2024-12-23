from typing import Tuple, Union, Literal

from .registry import _update_registry_team_bill_generation_metadata
from .specification import (
    ot_header_spec,
    owners_spec,
    ignore_billing_spec,
    registry_spec,
)


def get_ot_template() -> dict:
    return {k: "" for k in ot_header_spec.__dict__.values()}


def can_exempt_team(team_registry_data: dict) -> Tuple[bool, str]:
    if (
        team_registry_data[registry_spec.TEAM_BILL_GENERATION_METADATA][
            registry_spec.BILL_GENERATION_METADATA_INCLUDE_IN_OUTPUT_TABLE
        ]
        is False
    ):
        return (
            True,
            f"'{registry_spec.BILL_GENERATION_METADATA_INCLUDE_IN_OUTPUT_TABLE}."
            f"{registry_spec.BILL_GENERATION_METADATA_INCLUDE_IN_OUTPUT_TABLE}' is False",
        )
    return (
        False,
        f"'{registry_spec.BILL_GENERATION_METADATA_INCLUDE_IN_OUTPUT_TABLE}."
        f"{registry_spec.BILL_GENERATION_METADATA_INCLUDE_IN_OUTPUT_TABLE}' is True",
    )


def can_ignore_team(team_registry_data: dict) -> Tuple[bool, str]:
    if team_registry_data["on_trial"] is ignore_billing_spec.ON_TRIAL:
        return True, f"team is still on trial until the given most recent month"
    if (
        team_registry_data[owners_spec.TEAM_BILLABLE]
        == ignore_billing_spec.TEAM_BILLABLE
    ):
        return (
            True,
            f"'{owners_spec.TEAM_BILLABLE}' global parameter is "
            f"{ignore_billing_spec.TEAM_BILLABLE}",
        )
    if (
        team_registry_data[owners_spec.BILLING_MANAGEMENT_FACTOR]
        == ignore_billing_spec.BILLING_MANAGEMENT_FACTOR
    ):
        return (
            True,
            f"'{owners_spec.BILLING_MANAGEMENT_FACTOR}' global parameter is "
            f"{ignore_billing_spec.BILLING_MANAGEMENT_FACTOR}",
        )
    if (
        team_registry_data[owners_spec.BILLING_MANAGEMENT_LIMIT]
        == ignore_billing_spec.BILLING_MANAGEMENT_LIMIT
    ):
        return (
            True,
            f"'{owners_spec.BILLING_MANAGEMENT_LIMIT}' global parameter is "
            f"{ignore_billing_spec.BILLING_MANAGEMENT_LIMIT}",
        )
    return False, (
        f"team is not on trial, "
        f"nor the global billing parameters "
        f"({owners_spec.TEAM_BILLABLE}, {owners_spec.BILLING_MANAGEMENT_FACTOR}, "
        f"{owners_spec.BILLING_MANAGEMENT_LIMIT}) are set to specified ignore values "
        f"({ignore_billing_spec.TEAM_BILLABLE}, {ignore_billing_spec.BILLING_MANAGEMENT_FACTOR}, "
        f"{ignore_billing_spec.BILLING_MANAGEMENT_LIMIT})."
    )


def is_team_on_trial(team_registry_data: dict) -> Tuple[bool, str]:
    if team_registry_data["on_trial"] is ignore_billing_spec.ON_TRIAL:
        return True, f"team is on trial"
    return False, "team is not on trial"


def is_billing_management_limited(team_registry_data: dict) -> Tuple[bool, float]:
    if (
        management_limit := team_registry_data[owners_spec.BILLING_MANAGEMENT_LIMIT]
    ) > 0:  # BILLING_MANAGEMENT_LIMIT is -1 when it doesn't apply
        return True, management_limit
    return False, -1


def get_text_1(billing_management_limited: bool, /, team_name: str):
    if billing_management_limited is True:
        return (
            f'Für die Nutzung des Dienstes “eLabFTW” im Team "{team_name}" '
            "sind die aufgeführten Kosten entstanden. Die einzelnen Positionen "
            "entsprechen den aktiven Accounts im Team im jeweiligen Monat "
            "(Stichtag 15.). Die Gesamtkosten bilden sich aus dem vereinbarten Limit."
        )
    return (
        f'Für die Nutzung des Dienstes “eLabFTW” im Team "{team_name}" '
        "sind die aufgeführten Kosten entstanden. Die einzelnen Positionen "
        "entsprechen den aktiven Accounts im Team im "
        "jeweiligen Monat (Stichtag 15.)."
    )


def get_text_2(team_internal: bool):
    if team_internal is True:
        return (
            "Bitte vervollständigen Sie die beiliegende Auszahlungsanordnung "
            "um den/die Sachauftrag/Kostenstelle. Nach sachlicher Feststellunag "
            "und Unterschrift des Anordnungsbefugten bitte ich um Übersendung "
            "der Auszahlungsanordnung an die Finanzbuchhaltung, Abteilung 4.3"
        )
    return (
        "Bitte überweisen Sie den Rechnungsbetrag unter Angabe "
        "der Rechnungsnummer auf unten stehendes Konto."
    )


def calculate_team_monthly_bill(
    team_registry_data: dict, *, billing_management_factor: Union[float, int]
) -> float:
    return float(
        team_registry_data[owners_spec.BILLING_UNIT_COST]
        * team_registry_data["active_member_count"]
        * billing_management_factor
    )


def _update_registry_single_team_bill_generation_metadata(
    registry_data: dict,
    /,
    *,
    team_id: Union[str, int],
    include_status: Literal["include", "exempt"],  # follows registry_spec
    counter_status: Literal["increment", "decrement", None],  # follows registry_spec
) -> None:
    if team_id == registry_spec.REGISTRY_CLI_IMPLICIT_ARG_INCLUDE_ALL_TEAMS:
        raise ValueError(
            f"All team IDs cannot be targeted with ID "
            f"'{registry_spec.REGISTRY_CLI_IMPLICIT_ARG_INCLUDE_ALL_TEAMS}' for "
            f"function {_update_registry_single_team_bill_generation_metadata.__name__}."
        )
    _update_registry_team_bill_generation_metadata(
        registry_data,
        team_id=team_id,
        include_status=include_status,
        counter_status=counter_status,
    )
