import re
from pathlib import Path
from typing import Union, Optional, Tuple

from ...api.endpoint import FixedEndpoint
from ...path import ProperPath
from ...core_validators import ValidationError, Validator


class FixedExperimentEndpoint:
    def __new__(cls):
        return FixedEndpoint("experiments")


class ExperimentIDValidator(Validator):
    def __init__(
        self,
        experiment_id: Union[str, int],
    ):
        self.experiment_id = experiment_id
        self._experiment_endpoint = FixedExperimentEndpoint()

    @property
    def experiment_id(self) -> str:
        return self._experiment_id

    @experiment_id.setter
    def experiment_id(self, value):
        if value is None:
            raise ValidationError(f"Experiment ID cannot be '{type(None)}'.")
        if not hasattr(value, "__str__"):
            raise ValidationError(
                f"Experiment ID '{self.experiment_id}' couldn't be validated "
                f"because it couldn't be converted to a string."
            )
        self._experiment_id = str(value)

    def validate(self) -> str:
        if re.match(r"^\d+$|^me$", self.experiment_id, re.IGNORECASE):
            try:
                experiment_id = self._experiment_endpoint.get(
                    endpoint_id=self.experiment_id
                ).json()["id"]
            except KeyError:
                self._experiment_endpoint.close()
                raise ValidationError(
                    f"Experiment ID '{self.experiment_id}' could not be found!"
                )
            else:
                self._experiment_endpoint.close()
                return experiment_id
        if re.match(r"^\d+-\w+$", self.experiment_id, re.IGNORECASE):
            try:
                elab_id = (
                    _experiment_data := self._experiment_endpoint.get(
                        query={"q": self.experiment_id}
                    ).json()[0]
                )["elabid"]
            except (KeyError, IndexError):
                self._experiment_endpoint.close()
                raise ValidationError(
                    f"Experiment ID (detected as Unique eLabID) '{self.experiment_id}' could not be found!"
                )
            else:
                self._experiment_endpoint.close()
                if elab_id == self.experiment_id:
                    return _experiment_data["id"]
                raise ValidationError(
                    f"Experiment ID (detected as Unique eLabID) '{self.experiment_id}' could not be found!"
                )
        raise ValidationError(
            f"Experiment ID '{self.experiment_id}' could not be validated "
            "because it didn't match any valid pattern for experiment IDs!"
        )


def append_to_experiment(
    experiment_id: Union[str, int],
    content: str,
    markdown_to_html: bool = False,
) -> None:
    session = FixedExperimentEndpoint()
    current_body: Optional[str] = (
        experiment_metadata := (_response := session.get(experiment_id)).json()
    )["body"]
    if current_body is None:
        current_body: str = ""
    if markdown_to_html:
        # content_type == 1 => existing experiment is HTML-only, 2 => existing experiment is Markdown-only
        if _is_html := experiment_metadata["content_type"] & 1:
            from mistune import HTMLRenderer, Markdown
            from mistune.plugins.url import url
            from mistune.plugins.table import table
            from mistune.plugins.task_lists import task_lists
            from mistune.plugins.def_list import def_list
            from mistune.plugins.abbr import abbr
            from mistune.plugins.formatting import superscript, subscript
            from mistune.plugins.math import math

            renderer = HTMLRenderer()
            markdown = Markdown(
                renderer,
                plugins=[
                    url,
                    table,
                    task_lists,
                    def_list,
                    abbr,
                    superscript,
                    subscript,
                    math,
                ],
            )
            content = markdown(content)

    session.patch(
        experiment_id,
        data={"body": current_body + content},
    )
    session.close()


# noinspection PyArgumentList
def attach_to_experiment(
    experiment_id: Union[str, int],
    *,
    file_path: Union[str, Path],
    attachment_name: Optional[str] = None,
    comment: Optional[str] = None,
) -> None:
    experiment_endpoint = FixedExperimentEndpoint()
    with (file_path := ProperPath(file_path)).open(mode="rb") as f:
        experiment_endpoint.post(
            endpoint_id=experiment_id,
            sub_endpoint_name="uploads",
            files={
                "file": (attachment_name or file_path.expanded.name, f),
                "comment": (None, comment or ""),
            },
        )
    experiment_endpoint.close()


def download_attachment(
    experiment_id: Union[str, int], attachment_id: Union[str, int]
) -> Tuple[bytes, str, str, str, str, str]:
    session = FixedExperimentEndpoint()
    response = session.get(experiment_id, sub_endpoint_name="uploads")
    for attachment_metadata in response.json():
        if re.match(rf"^{attachment_id}$", str(attachment_metadata["id"])) or (
            len(attachment_id) >= 6
            and re.match(rf"^{attachment_id}", attachment_metadata["hash"])
        ):
            real_id = str(attachment_metadata["id"])
            _extension: str = "".join(Path(attachment_metadata["real_name"]).suffixes)
            _name: str = attachment_metadata["real_name"].rstrip(_extension)
            _extension = _extension.lstrip(".")
            _hash: str = attachment_metadata["hash"]
            _created_at: str = attachment_metadata["created_at"]
            attachment = session.get(
                experiment_id,
                sub_endpoint_name="uploads",
                sub_endpoint_id=real_id,
                query={"format": "binary"},
            ).content
            session.close()
            return attachment, real_id, _name, _extension, _hash, _created_at
    session.close()
    raise ValueError(
        f"Attachment with ID '{attachment_id}' couldn't be found on experiment with ID '{experiment_id}'."
    )
