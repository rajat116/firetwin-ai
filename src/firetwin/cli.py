"""Command-line interface for FireTwin."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from firetwin import __version__
from firetwin.settings import check_optional_dependencies, get_system_info, settings

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="firetwin")
def main():
    """
    FireTwin: A research-grade wildfire digital twin.

    Combines satellite observations, weather, terrain and vegetation with
    physics-guided ML for probabilistic fire-spread forecasting.
    """
    pass


@main.command()
def doctor():
    """
    Run system diagnostics and check configuration.

    Displays:
    - Application version
    - Python environment
    - System platform
    - Optional dependency availability
    - Configuration status
    """
    console.print(
        Panel.fit(
            f"[bold cyan]FireTwin v{__version__}[/bold cyan]\n"
            "[dim]Research prototype - Not for operational use[/dim]",
            title="🔥 FireTwin Doctor",
            border_style="cyan",
        )
    )

    # System Information
    console.print("\n[bold]System Information:[/bold]")
    sys_info = get_system_info()
    sys_table = Table(show_header=False, box=None, padding=(0, 2))
    sys_table.add_column("Key", style="cyan")
    sys_table.add_column("Value", style="white")

    sys_table.add_row("Python", sys_info["python_version"].split()[0])
    sys_table.add_row("Platform", sys_info["platform"])
    sys_table.add_row("Architecture", sys_info["machine"])

    console.print(sys_table)

    # Dependencies
    console.print("\n[bold]Optional Dependencies:[/bold]")
    deps = check_optional_dependencies()
    dep_table = Table(show_header=True, box=None, padding=(0, 2))
    dep_table.add_column("Package", style="cyan")
    dep_table.add_column("Status", style="white")
    dep_table.add_column("Version", style="dim")

    for name, info in deps.items():
        if info["available"]:
            status = "[green]✓ Available[/green]"
            version = info.get("version", "unknown")
            if name == "torch" and info.get("cuda_available"):
                status += " [yellow](CUDA)[/yellow]"
        else:
            status = "[red]✗ Not found[/red]"
            version = "-"

        dep_table.add_row(name, status, version)

    console.print(dep_table)

    # Configuration
    console.print("\n[bold]Configuration:[/bold]")
    config_table = Table(show_header=False, box=None, padding=(0, 2))
    config_table.add_column("Key", style="cyan")
    config_table.add_column("Value", style="white")

    config_table.add_row(
        "Data Root",
        str(settings.data_root.absolute())
        if settings.data_root.exists()
        else f"{settings.data_root} [red](not found)[/red]",
    )
    config_table.add_row("MLflow URI", settings.mlflow_tracking_uri)

    # Credentials status (never show actual values)
    firms_status = "[green]✓ Set[/green]" if settings.firms_map_key else "[yellow]Not set[/yellow]"
    cds_status = "[green]✓ Set[/green]" if settings.cds_api_key else "[yellow]Not set[/yellow]"

    config_table.add_row("FIRMS API Key", firms_status)
    config_table.add_row("CDS API Key", cds_status)

    console.print(config_table)

    # Warnings and recommendations
    warnings = []

    if not settings.data_root.exists():
        warnings.append(
            "[yellow]Data directory does not exist. It will be created on first use.[/yellow]"
        )

    if not settings.firms_map_key:
        warnings.append("[yellow]FIRMS API key not configured. See .env.example[/yellow]")

    if not settings.cds_api_key:
        warnings.append("[yellow]CDS API key not configured. See .env.example[/yellow]")

    if not deps["torch"]["available"]:
        warnings.append("[red]PyTorch not found. Install with: conda install pytorch[/red]")

    if warnings:
        console.print("\n[bold]Recommendations:[/bold]")
        for warning in warnings:
            console.print(f"  • {warning}")

    console.print("\n[green]✓ Doctor check complete[/green]\n")


@main.command()
@click.option("--case-id", default="synthetic_001", help="Unique case identifier")
@click.option("--grid-size", default=100, help="Grid dimension (creates NxN grid)")
@click.option("--resolution", default=30.0, help="Grid resolution in meters")
@click.option("--hours", default=24, help="Hours of fire evolution to generate")
@click.option("--output", type=click.Path(), help="Output path (defaults to data/processed/CASE_ID.zarr)")
@click.option("--seed", type=int, help="Random seed for reproducibility")
def generate_synthetic(case_id, grid_size, resolution, hours, output, seed):
    """Generate a synthetic fire case for testing and validation."""
    from pathlib import Path
    from firetwin.data.synthetic import generate_synthetic_fire_case

    console.print(f"\n[bold cyan]🔥 Generating Synthetic Fire Case: {case_id}[/bold cyan]\n")

    with console.status("[bold green]Creating synthetic terrain, fuels, and fire evolution..."):
        case = generate_synthetic_fire_case(
            case_id=case_id,
            name=f"Synthetic Case {case_id}",
            grid_size=(grid_size, grid_size),
            resolution_m=resolution,
            n_forecast_hours=hours,
            seed=seed,
        )

    # Determine output path
    if output is None:
        output = settings.data_root / "processed" / f"{case_id}.zarr"
    else:
        output = Path(output)

    # Save
    console.print(f"[cyan]Saving to:[/cyan] {output}")
    case.save_to_zarr(output)

    # Summary
    console.print(f"\n[green]✓ Generated {len(case.target_states)} time steps[/green]")
    console.print(f"[green]  Grid: {grid_size}x{grid_size} @ {resolution}m = {(grid_size * resolution / 1000):.1f}km²[/green]\n")


@main.command()
@click.argument("case_path", type=click.Path(exists=True))
@click.option("--horizons", default="3,6,12,24", help="Forecast horizons in hours (comma-separated)")
@click.option("--output-dir", type=click.Path(), help="Output directory for forecasts")
def run_baselines(case_path, horizons, output_dir):
    """Run baseline forecast models on a fire case."""
    from pathlib import Path
    import numpy as np
    from rich.progress import track
    from firetwin.models import PersistenceBaseline, RadialBaseline, EllipticalBaseline
    from firetwin.schemas import FireCase

    console.print("\n[bold cyan]🔥 Running Baseline Forecasts[/bold cyan]\n")

    # Load case
    with console.status(f"[bold green]Loading case from {case_path}..."):
        case = FireCase.load_from_zarr(Path(case_path))

    console.print(f"[cyan]Case:[/cyan] {case.metadata.name} ({case.metadata.case_id})")
    console.print(f"[cyan]Grid:[/cyan] {case.grid_shape} @ {case.resolution_m}m")

    # Parse horizons
    forecast_hours = [float(h) for h in horizons.split(",")]
    console.print(f"[cyan]Horizons:[/cyan] {forecast_hours} hours\n")

    # Initialize models
    models = {
        "persistence": PersistenceBaseline(),
        "radial": RadialBaseline(spread_rate_m_h=100.0),
        "elliptical": EllipticalBaseline(base_spread_rate_m_h=100.0),
    }

    # Set up output
    if output_dir is None:
        output_dir = settings.data_root / "forecasts" / case.metadata.case_id
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run forecasts
    for model_name, model in track(models.items(), description="[green]Running models...", total=len(models)):
        forecasts = model.forecast(case, forecast_hours)

        # Save forecasts
        model_dir = output_dir / model_name
        model_dir.mkdir(exist_ok=True)

        for horizon, forecast_state in forecasts.items():
            forecast_path = model_dir / f"forecast_{horizon}h.npz"
            np.savez(
                forecast_path,
                burned=forecast_state.burned,
                active_front=forecast_state.active_front,
            )

        console.print(f"  [green]✓[/green] {model_name}: {len(forecasts)} forecasts → {model_dir.name}/")

    console.print(f"\n[green]✓ All baselines complete[/green] → {output_dir}\n")


@main.command()
@click.argument("case_path", type=click.Path(exists=True))
@click.argument("forecasts_dir", type=click.Path(exists=True))
@click.option("--horizons", default="3,6,12,24", help="Forecast horizons to evaluate (comma-separated)")
def evaluate(case_path, forecasts_dir, horizons):
    """Evaluate forecast accuracy against ground truth."""
    from pathlib import Path
    import numpy as np
    from firetwin.evaluation import evaluate_forecast
    from firetwin.schemas import FireCase

    console.print("\n[bold cyan]🔥 Evaluating Forecasts[/bold cyan]\n")

    # Load case
    with console.status(f"[bold green]Loading case from {case_path}..."):
        case = FireCase.load_from_zarr(Path(case_path))

    console.print(f"[cyan]Case:[/cyan] {case.metadata.name}")

    # Parse horizons
    forecast_hours = [float(h) for h in horizons.split(",")]

    # Create target lookup
    targets = {
        int((state.timestamp - case.initial_state.timestamp).total_seconds() / 3600): state
        for state in case.target_states
    }

    # Evaluate each model
    models = ["persistence", "radial", "elliptical"]
    forecasts_path = Path(forecasts_dir)

    results_table = Table(title="Forecast Evaluation")
    results_table.add_column("Model", style="cyan")
    results_table.add_column("Horizon (h)", style="yellow")
    results_table.add_column("IoU", style="green")
    results_table.add_column("Dice", style="green")
    results_table.add_column("Boundary (m)", style="magenta")

    for model_name in models:
        model_dir = forecasts_path / model_name
        if not model_dir.exists():
            continue

        for horizon in forecast_hours:
            horizon_int = int(horizon)
            if horizon_int not in targets:
                continue

            forecast_path = model_dir / f"forecast_{horizon}h.npz"
            if not forecast_path.exists():
                continue

            # Load forecast
            forecast_data = np.load(forecast_path)
            predicted = forecast_data["burned"]
            target = targets[horizon_int].burned

            # Evaluate
            metrics = evaluate_forecast(predicted, target, case.resolution_m)

            results_table.add_row(
                model_name,
                str(horizon_int),
                f"{metrics['iou']:.3f}",
                f"{metrics['dice']:.3f}",
                f"{metrics['boundary_distance_mean_m']:.1f}",
            )

    console.print()
    console.print(results_table)
    console.print(f"\n[green]✓ Evaluation complete[/green]\n")


if __name__ == "__main__":
    main()
