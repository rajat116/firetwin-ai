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


if __name__ == "__main__":
    main()
