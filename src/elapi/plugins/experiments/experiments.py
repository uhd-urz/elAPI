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
