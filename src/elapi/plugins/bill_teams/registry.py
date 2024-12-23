import json
from datetime import datetime
from pathlib import Path
from typing import Union, Literal

from .names import TARGET_GROUP_NAME, TARGET_GROUP_OWNER_NAME_SINGULAR
from .specification import (
    BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB,
    BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB,
    REGISTRY_TIME_FORMAT,
    owners_spec,
    registry_spec,
    _registry_com_spec,
)
from ...core_validators import Exit
from ...loggers import Logger, FileLogger
from ...path import ProperPath
from ...plugins.commons import Export

logger = Logger()
file_logger = FileLogger()


class _RegistryCommunication(dict):
    def __init__(self):
        DEFAULT_DICT: dict = {
            _registry_com_spec.EXISTS_IN_OWNERS_INFO_BUT_MISSING_IN_TEAMS_INFO: False,
            _registry_com_spec.USER_REQUESTED_FILE_LOG_FOR_MISSING_TEAMS_INFO: False,
        }
        super().__init__(DEFAULT_DICT)

    def __setitem__(self, key, value):
        if key not in self.keys():
            raise AttributeError(
                f"New key '{key}' cannot be added to "
                f"internal communication data storage."
            )
        super().__setitem__(key, value)

    def __delitem__(self, key):
        raise AttributeError(
            "Existing values cannot be deleted in "
            "internal communication data storage."
        )


_registry_communication = _RegistryCommunication()


def _populate_registry_file(
    file: Path,
    /,
    teams_info_file_metadata: dict,
    owners_info_file_metadata: dict,
) -> None:
    if file.stat().st_size != 0:
        raise ValueError(f"Non-empty registry file {file} cannot be populated.")
    defaults = {
        registry_spec.REGISTRY_LAST_UPDATED: None,
        registry_spec.TEAMS_INFO_DATE: teams_info_file_metadata["date"].strftime(
            f"{Export.EXPORT_DATE_FORMAT} {REGISTRY_TIME_FORMAT}"
        ),
        registry_spec.OWNERS_INFO_DATE: owners_info_file_metadata["date"].strftime(
            f"{Export.EXPORT_DATE_FORMAT} {REGISTRY_TIME_FORMAT}"
        ),
        TARGET_GROUP_NAME: {},
    }
    teams_info = json.loads(teams_info_file_metadata["file"].read_text())
    owners_info = json.loads(owners_info_file_metadata["file"].read_text())
    for team_id in teams_info:
        team = teams_info[team_id]
        defaults[TARGET_GROUP_NAME][team_id] = {}
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.TEAM_NAME] = team[
            registry_spec.TEAM_NAME
        ]
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.TEAM_ACTIVE_MEMBER_COUNT] = (
            team[registry_spec.TEAM_ACTIVE_MEMBER_COUNT]
        )
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.TEAM_ON_TRIAL] = team[
            registry_spec.TEAM_ON_TRIAL
        ]
    for team_id in owners_info:
        team = owners_info[team_id]
        try:
            defaults[TARGET_GROUP_NAME][team_id]
        except KeyError:
            _registry_communication[
                _registry_com_spec.EXISTS_IN_OWNERS_INFO_BUT_MISSING_IN_TEAMS_INFO
            ] = True
            (
                file_logger
                if _registry_communication[
                    _registry_com_spec.USER_REQUESTED_FILE_LOG_FOR_MISSING_TEAMS_INFO
                ]
                is True
                else logger
            ).warning(
                f"Team ID '{team_id}' exists in '{BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB}' file "
                f"({owners_info_file_metadata['file']}) but is missing "
                f"in '{BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB}' "
                f"file ({teams_info_file_metadata['file']}). Team will not be added to registry."
            )
            continue
        defaults[TARGET_GROUP_NAME][team_id][owners_spec.BILLING_UNIT_COST] = team[
            owners_spec.BILLING_UNIT_COST
        ]
        defaults[TARGET_GROUP_NAME][team_id][owners_spec.TEAM_BILLABLE] = team[
            owners_spec.TEAM_BILLABLE
        ]
        defaults[TARGET_GROUP_NAME][team_id][owners_spec.BILLING_MANAGEMENT_FACTOR] = (
            team[owners_spec.BILLING_MANAGEMENT_FACTOR]
        )
        defaults[TARGET_GROUP_NAME][team_id][owners_spec.BILLING_MANAGEMENT_LIMIT] = (
            team[owners_spec.BILLING_MANAGEMENT_LIMIT]
        )
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.EXTRAS] = {}
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.EXTRAS][
            registry_spec.TEAM_OWNER_NAME
        ] = (
            f"{team[TARGET_GROUP_OWNER_NAME_SINGULAR][owners_spec.TEAM_OWNER_FIRST_NAME]} "
            f"{team[TARGET_GROUP_OWNER_NAME_SINGULAR][owners_spec.TEAM_OWNER_LAST_NAME]}"
        )
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.EXTRAS][
            registry_spec.TEAM_OWNER_EMAIL
        ] = team[TARGET_GROUP_OWNER_NAME_SINGULAR][owners_spec.TEAM_OWNER_EMAIL]
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.EXTRAS][
            owners_spec.BILLING_PERSON_GROUP
        ] = team[owners_spec.BILLING_PERSON_GROUP]
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.EXTRAS][
            owners_spec.BILLING_PERSON_GROUP
        ] = team[owners_spec.BILLING_PERSON_GROUP]
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.EXTRAS][
            owners_spec.BILLING_INSTITUTE1
        ] = team[owners_spec.BILLING_INSTITUTE1]
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.EXTRAS][
            owners_spec.BILLING_INSTITUTE2
        ] = team[owners_spec.BILLING_INSTITUTE2]
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.EXTRAS][
            owners_spec.BILLING_STREET
        ] = team[owners_spec.BILLING_STREET]
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.EXTRAS][
            owners_spec.BILLING_POSTAL_CODE
        ] = team[owners_spec.BILLING_POSTAL_CODE]
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.EXTRAS][
            owners_spec.BILLING_CITY
        ] = team[owners_spec.BILLING_CITY]
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.EXTRAS][
            owners_spec.BILLING_INT_EXT
        ] = team[owners_spec.BILLING_INT_EXT]
        defaults[TARGET_GROUP_NAME][team_id][registry_spec.EXTRAS][
            owners_spec.BILLING_ACCOUNT_UNIT
        ] = team[owners_spec.BILLING_ACCOUNT_UNIT]
    for team_id in defaults[TARGET_GROUP_NAME]:
        defaults[TARGET_GROUP_NAME][team_id][
            registry_spec.TEAM_BILL_GENERATION_METADATA
        ] = {}
        defaults[TARGET_GROUP_NAME][team_id][
            registry_spec.TEAM_BILL_GENERATION_METADATA
        ][registry_spec.BILL_GENERATION_METADATA_INCLUDE_IN_OUTPUT_TABLE] = False
        defaults[TARGET_GROUP_NAME][team_id][
            registry_spec.TEAM_BILL_GENERATION_METADATA
        ][registry_spec.BILL_GENERATION_METADATA_BILLING_COUNTER] = 0
        defaults[TARGET_GROUP_NAME][team_id][
            registry_spec.TEAM_BILL_GENERATION_METADATA
        ][
            registry_spec.BILL_GENERATION_METADATA_LAST_UPDATED
        ] = datetime.now().strftime(
            f"{Export.EXPORT_DATE_FORMAT} {REGISTRY_TIME_FORMAT}"
        )
    with ProperPath(file).open(mode="w", encoding="utf-8") as f:
        json.dump(defaults, f, indent=2, ensure_ascii=False)


def _initialize_registry_file(
    file, /, year: int, month: int, teams_info: dict, owners_info: dict
) -> None:
    if file.exists() is False:
        logger.info(
            f"A new registry file '{file}' "
            f"for month {year}-{month:02d} will be created."
        )
        ProperPath(file).create(verbose=False)
    if file.stat().st_size == 0:
        try:
            _populate_registry_file(file, teams_info, owners_info)
        except ValueError as e:
            logger.error(e)
            raise Exit(1) from e


def modify_registry_file(file, /, new_registry_data: dict) -> None:
    new_registry_data[registry_spec.REGISTRY_LAST_UPDATED] = datetime.now().strftime(
        f"{Export.EXPORT_DATE_FORMAT} {REGISTRY_TIME_FORMAT}"
    )
    with ProperPath(file).open(mode="w+", encoding="utf-8") as file:
        json.dump(new_registry_data, file, indent=2, ensure_ascii=False)


def _str_team_id(team_id: Union[str, int], /) -> str:
    if not isinstance(team_id, (str, int)):
        raise ValueError(f"Team ID must be an integer or string.")
    if not isinstance(team_id, str):
        team_id = str(team_id)
    return team_id


def _update_registry_team_bill_generation_metadata(
    registry_data: dict,
    /,
    *,
    team_id: Union[Literal["all"], str, int],
    include_status: Literal["include", "exempt"],  # follows registry_spec
    counter_status: Literal["increment", "decrement", None],  # follows registry_spec
) -> None:
    STATUS_VALUES: dict = {
        registry_spec.REGISTRY_CLI_CMD_INCLUDE_TEAM: True,
        registry_spec.REGISTRY_CLI_CMD_EXEMPT_TEAM: False,
        registry_spec.REGISTRY_CLI_ARG_INCREMENT_TEAM_BILLING_COUNTER: 1,
        registry_spec.REGISTRY_CLI_ARG_DECREMENT_TEAM_BILLING_COUNTER: -1,
    }

    def _update_team_info(team_info: dict, /) -> None:
        bill_generation_metadata = team_info[
            registry_spec.TEAM_BILL_GENERATION_METADATA
        ]
        bill_generation_metadata[
            registry_spec.BILL_GENERATION_METADATA_INCLUDE_IN_OUTPUT_TABLE
        ] = STATUS_VALUES[include_status]
        if counter_status is not None:
            bill_generation_metadata[
                registry_spec.BILL_GENERATION_METADATA_BILLING_COUNTER
            ] += STATUS_VALUES[counter_status]
        bill_generation_metadata[
            registry_spec.BILL_GENERATION_METADATA_LAST_UPDATED
        ] = datetime.now().strftime(
            f"{Export.EXPORT_DATE_FORMAT} {REGISTRY_TIME_FORMAT}"
        )
        registry_data[TARGET_GROUP_NAME][team_id][  # team_id is read from outer scope
            registry_spec.TEAM_BILL_GENERATION_METADATA
        ] = bill_generation_metadata

    if team_id == registry_spec.REGISTRY_CLI_IMPLICIT_ARG_INCLUDE_ALL_TEAMS:
        for _team_id, _team_info in registry_data[TARGET_GROUP_NAME].items():
            team_id: str = _str_team_id(_team_id)  # team_id is modified
            _update_team_info(_team_info)
    else:
        _update_team_info(registry_data[TARGET_GROUP_NAME][_str_team_id(team_id)])


def _get_team_registry_data(
    registry_data: dict,
    /,
    *,
    team_id: Union[str, int],
) -> dict:
    return registry_data[TARGET_GROUP_NAME][_str_team_id(team_id)]


class BillGenerationMetadataSanityError(Exception):
    def __init__(self, message: str, affected_team_id: str):
        self.message = message
        self.affected_team_id = affected_team_id


def _is_team_bill_generation_metadata_sane(
    registry_data: dict,
    /,
    *,
    registry_file_path: Path,
    team_id: Union[str, int],
    ideal_include_status: Literal["include", "exempt"],
) -> bool:
    IS_SANE: bool = True
    EXPECTED_STATUS_VALUES: dict = {
        registry_spec.REGISTRY_CLI_CMD_INCLUDE_TEAM: True,
        registry_spec.REGISTRY_CLI_CMD_EXEMPT_TEAM: False,
    }

    def _check_sanity(team_info: dict, /) -> None:
        bill_generation_metadata = team_info[
            registry_spec.TEAM_BILL_GENERATION_METADATA
        ]
        is_team_included: bool = bill_generation_metadata[
            registry_spec.BILL_GENERATION_METADATA_INCLUDE_IN_OUTPUT_TABLE
        ]
        billing_counter: int = bill_generation_metadata[
            registry_spec.BILL_GENERATION_METADATA_BILLING_COUNTER
        ]
        if (
            is_team_included != EXPECTED_STATUS_VALUES[ideal_include_status]
            and billing_counter >= 1
        ):
            raise BillGenerationMetadataSanityError(
                f"Team ID '{team_id}' in {registry_file_path} has already been billed "
                f"('{registry_spec.BILL_GENERATION_METADATA_BILLING_COUNTER}': {billing_counter}). ",
                team_id,
            )

    if team_id == registry_spec.REGISTRY_CLI_IMPLICIT_ARG_INCLUDE_ALL_TEAMS:
        for _team_id, _team_info in registry_data[TARGET_GROUP_NAME].items():
            team_id = _str_team_id(_team_id)
            try:
                _check_sanity(_team_info)
            except BillGenerationMetadataSanityError as e:
                IS_SANE = False
                logger.info(e.message)
        return IS_SANE
    try:
        _check_sanity(registry_data[TARGET_GROUP_NAME][_str_team_id(team_id)])
    except BillGenerationMetadataSanityError as e:
        IS_SANE = False
        logger.info(e.message)
    return IS_SANE
