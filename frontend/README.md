# FireTwin Explorer

This is a dependency-free first Explorer UI for the committed FIRMS next-day forecast assets.

Run it from the repository root with the allowlisted preview server:

```bash
python3 scripts/serve_explorer.py --host 127.0.0.1 --port 8000
```

Then open:

```text
http://localhost:8000/frontend/
```

The app loads `data/manifests/firms_next_day_explorer_manifest.json` and the committed preview PNGs
under `reports/figures/`. It does not require the ignored local Zarr forecast artifacts to render.

Build a deployable static bundle:

```bash
python3 scripts/build_explorer_site.py --output-dir dist/explorer
```

Serve `dist/explorer/` with any static file server. The bundle contains only the Explorer, manifest
and referenced preview PNGs.

Smoke-test the bundle before sharing or deploying it:

```bash
python3 scripts/smoke_explorer_bundle.py --bundle-dir dist/explorer
```
