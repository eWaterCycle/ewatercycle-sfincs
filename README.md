# eWaterCycle plugin for SFINCS

A eWaterCycle plugin for the [SFINCS model](https://github.com/Deltares/SFINCS/tree/main).

The plugin uses the grpc4bmi wrapper for SFINCS, which is available at
https://github.com/eWaterCycle/sfincs-bmi-server

## Installation

Install this package alongside your eWaterCycle installation

```console
pip install ewatercycle-sfincs
```

Then Sfincs becomes available as one of the eWaterCycle models

```python
from ewatercycle.models import Sfincs
```

## License

`ewatercycle-sfincs` is distributed under the terms of the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.
