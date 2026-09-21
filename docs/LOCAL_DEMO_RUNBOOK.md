# Local Demo Runbook

This runbook starts the artifact-backed Explorer and experimental simulation-surrogate API on a
local machine. FireTwin is a research prototype and must not be used for operational wildfire
response, evacuation planning or safety-critical decisions.

## Environment

Use the project conda environment:

```bash
conda activate firetwin
```

On this machine, if `conda run -n firetwin ...` resolves the wrong Python, use the absolute
interpreter instead:

```bash
/Users/rajat/miniconda3/envs/firetwin/bin/python -m pytest tests/unit -q
```

## Start the API

In terminal 1:

```bash
make api
```

The API listens at `http://127.0.0.1:8001`.

Quick health check:

```bash
curl http://127.0.0.1:8001/health
```

## Start the Explorer

In terminal 2:

```bash
make explorer
```

Open:

```text
http://127.0.0.1:8000/frontend/globe.html?api=http://127.0.0.1:8001
```

The `api` query parameter enables the globe scenario controls to call the local simulation
surrogate endpoints. Without it, the static FIRMS forecast overlays still load, but the scenario
readout remains offline.

## Verify Before Demo

Run the quality gates:

```bash
/Users/rajat/miniconda3/envs/firetwin/bin/python -m ruff check src tests
/Users/rajat/miniconda3/envs/firetwin/bin/python -m ruff format --check src tests
/Users/rajat/miniconda3/envs/firetwin/bin/python -m mypy src --ignore-missing-imports
/Users/rajat/miniconda3/envs/firetwin/bin/python -m pytest tests/unit -q
```

Expected current status:

- Ruff check passes.
- Ruff format check passes.
- MyPy reports no issues.
- Unit tests pass.

## Demo Flow

1. Open the globe URL.
2. Select a pilot fire from the left panel.
3. Toggle Forecast, Observed and Scenario layers.
4. Adjust wind speed, wind turn or spread rate.
5. Click Run Scenario and wait for the status pill to update.
6. Emphasize that scenario overlays are simulator-trained surrogate outputs, not observed wildfire
   truth.
