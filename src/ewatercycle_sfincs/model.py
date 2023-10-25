"""eWaterCycle wrapper for the Sfincs model."""
from collections.abc import ItemsView
from pathlib import Path
from datetime import datetime
from typing import Any

from ewatercycle.base.model import ContainerizedModel, eWaterCycleModel
from ewatercycle.container import ContainerImage
from pydantic import model_validator


class SfincsMethods(eWaterCycleModel):
    """The eWatercycle Sfincs model.
    
    """
    # TODO from forcing object write config line like `netamprfile          = precip.nc`

    _config: dict = {}

    @model_validator(mode="after")
    def _initialize_config(self: "SfincsMethods") -> "SfincsMethods":
        """Load config from parameter set and update with forcing info."""
        body = self.parameter_set.config.read_text()
        for line in body.splitlines():
            if "=" in line:
                key, val = line.split("=")
                self._config[key.strip()] = val.strip()

    def _make_cfg_file(self, **kwargs) -> Path:
        """Write model configuration file."""
        if self.forcing:
            self._config["netamprfile"] = str(
                self.forcing.directory / self.forcing.pr
            )

        if 'start_time' in kwargs:
            # convert 2020-01-01T00:00:00Z to something like 20131201 000000
            self._config["tstart"] = self._iso8601toscfincs(kwargs['start_time'])
        if 'end_time' in kwargs:
            self._config["tstop"] = self._iso8601toscfincs(kwargs['end_time'])

        config_file = self._cfg_dir / "sfincs.inp"

        with config_file.open(mode="w") as f:
            for key, val in self._config.items():
                f.write(f"{key:<22} = {val}\n")

        return config_file

    def _iso8601toscfincs(self, iso8601: str) -> str:
        """Convert ISO8601 to SFINCS format."""
        return iso8601.replace('-', '').replace(':', '').replace('T', '').replace('Z', '').split('.')[0]

    def _sfincs_to_iso8601(self, dt: str) -> str:
        """Convert SFINCS format to ISO8601."""
        dt_obj = datetime.strptime(dt, '%Y%m%d %H%M%S')
        return dt_obj.isoformat() + 'Z'

    @property
    def parameters(self) -> ItemsView[str, Any]:
        """Return the model parameters.
        
        Exposed sfincs parameters:
            start_time: Start time of model in UTC and ISO format string
                e.g. 'YYYY-MM-DDTHH:MM:SSZ'.
            end_time: End time of model in  UTC and ISO format string
                e.g. 'YYYY-MM-DDTHH:MM:SSZ'.
        """
        return {
            'start_time': self._sfincs_to_iso8601(self._config['tstart']),
            'end_time': self._sfincs_to_iso8601(self._config['tstop'])
        }.items()


class Sfincs(ContainerizedModel, SfincsMethods):
    """The Sfincs eWaterCycle model, with the Container Registry docker image."""
    bmi_image: ContainerImage = ContainerImage(
        "ghcr.io/ewatercycle/sfincs-bmiserver:sfincs-v2.0.2-blockhaus-release-q2-2023"
    )
