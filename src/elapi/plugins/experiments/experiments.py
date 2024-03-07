import re
from typing import Union

from ...endpoint import FixedEndpoint
from ...validators import ValidationError, Validator


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
        experiments = self._experiment_endpoint.get(endpoint_id=None).json()
        self._experiment_endpoint.close()
        if re.match(r"^\d+$|^me$", self.experiment_id, re.IGNORECASE):
            for experiment in experiments:
                if str(experiment["id"]) == self.experiment_id:
                    # experiment["id"] is returned as an int
                    return self.experiment_id
            raise ValidationError(
                f"Experiment ID '{self.experiment_id}' could not be found!"
            )
        if re.match(r"^\d+-\w+$", self.experiment_id, re.IGNORECASE):
            for experiment in experiments:
                if experiment["elabid"] == self.experiment_id:
                    return experiment["id"]
                raise ValidationError(
                    f"Experiment ID '{self.experiment_id}' could not be found!"
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
    current_body: str = (
        experiment_metadata := (_response := session.get(experiment_id)).json()
    )["body"]
    if markdown_to_html:
        # content_type == 1 => existing experiment is HTML-only, 2 => existing experiment is Markdown-only
        if _is_html := experiment_metadata["content_type"] & 1:
            from mistune import HTMLRenderer, Markdown
            from mistune.plugins.url import url
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
