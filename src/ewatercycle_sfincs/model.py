"""eWaterCycle wrapper for the Sfincs model."""
from collections.abc import ItemsView
from pathlib import Path
from datetime import datetime, timezone
import shutil
from typing import Any, Optional
import bmipy

from ewatercycle.base.model import ContainerizedModel
from ewatercycle.container import ContainerImage, start_container
from ewatercycle.util import to_absolute_path
from ewatercycle import CFG

from pydantic import model_validator


class Sfincs(ContainerizedModel):
    """The Sfincs eWaterCycle model, with the Container Registry docker image."""

    bmi_image: ContainerImage = ContainerImage(
        "ghcr.io/ewatercycle/sfincs-bmiserver:sfincs-v2.0.2-blockhaus-release-q2-2023"
    )
    # TODO generate forcing with netamprfile, netampfile, netamuamvfile nc files

    _config: dict = {
        'tref': '20000101 000000',
        'tstart': '20000101 000000',
        'tend': '20000101 000000',
    }

    @model_validator(mode="after")
    def _initialize_config(self: "Sfincs") -> "Sfincs":
        """Load config from parameter set and update with forcing info."""
        body = self.parameter_set.config.read_text()
        for line in body.splitlines():
            if "=" in line:
                key, val = line.split("=")
                self._config[key.strip()] = val.strip()

    def _make_cfg_file(self, **kwargs) -> Path:
        """Write model configuration file."""
        if self.forcing:
            # TODO set netamprfile - FEWS type netcdf meteo input with precipitation in mm/hr.
            # TODO set netampfile - FEWS type netcdf meteo input with atmospheric pressure in Pa.
            # TODO set netamuamvfile - FEWS type netcdf meteo input with wind speed in both x-&y-direction in m/s.
            pass

        if "start_time" in kwargs:
            # convert 2020-01-01T00:00:00Z to something like 20131201 000000
            self._config["tstart"] = self._iso8601toscfincs(kwargs["start_time"])
        if "end_time" in kwargs:
            self._config["tstop"] = self._iso8601toscfincs(kwargs["end_time"])
        if "ref_time" in kwargs:
            self._config["tref"] = self._iso8601toscfincs(kwargs["ref_time"])

        # Make all *file parameters relative to the parameter set config file.
        for key, val in self._config.items():
            if key.endswith("file"):
                self._config[key] = to_absolute_path(val, self.parameter_set.config.parent)
        
        config_file = self._cfg_dir / "sfincs.inp"

        with config_file.open(mode="w") as f:
            for key, val in self._config.items():
                f.write(f"{key:<20} = {val}\n")

        return config_file

    def _iso8601toscfincs(self, iso8601: str) -> str:
        """Convert ISO8601 to SFINCS format."""
        return (
            iso8601.replace("-", "")
            .replace(":", "")
            .replace("T", "")
            .replace("Z", "")
            .split(".")[0]
        )

    def _sfincs_to_iso8601(self, dt: str) -> str:
        """Convert SFINCS format to ISO8601."""
        dt_obj = datetime.strptime(dt, "%Y%m%d %H%M%S")
        return dt_obj.isoformat() + "Z"

    @property
    def parameters(self) -> ItemsView[str, Any]:
        """Return the model parameters.

        Exposed sfincs parameters:
            ref_time: Reference date in UTC and ISO format string
                e.g. 'YYYY-MM-DDTHH:MM:SSZ'.
            start_time: Start time of model in UTC and ISO format string
                e.g. 'YYYY-MM-DDTHH:MM:SSZ'.
            end_time: End time of model in  UTC and ISO format string
                e.g. 'YYYY-MM-DDTHH:MM:SSZ'.
        """
        return {
            "ref_time": self._sfincs_to_iso8601(self._config["tref"]),
            "start_time": self._sfincs_to_iso8601(self._config["tstart"]),
            "end_time": self._sfincs_to_iso8601(self._config["tstop"]),
        }.items()

    # container is running on port 50051, but ewc defaults to 55555
    # TODO Change Dockerfile so it runs on 55555, then this override is not needed
    def _make_bmi_instance(self) -> bmipy.Bmi:
        if self.parameter_set:
            self._additional_input_dirs.append(str(self.parameter_set.directory))
        if self.forcing:
            self._additional_input_dirs.append(str(self.forcing.directory))

        return start_container(
            image=self.bmi_image,
            work_dir=self._cfg_dir,
            input_dirs=self._additional_input_dirs,
            image_port=50051,
            timeout=300,
        )
