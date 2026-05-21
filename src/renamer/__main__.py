"""CLI entry point."""
import click
from dotenv import load_dotenv

load_dotenv()


@click.group()
def cli() -> None:
    """Context-Aware File Renamer & Organizer."""


@cli.command()
def gui() -> None:
    """Launch the floating GUI."""
    from renamer.gui import main
    main()


@cli.command()
@click.argument("paths", nargs=-1, required=True)
@click.option("--llm", default="ollama", show_default=True)
@click.option("--hours", default=4.0, show_default=True)
@click.option("--dry-run/--apply", default=True, show_default=True)
def watch(paths: tuple[str, ...], llm: str, hours: float, dry_run: bool) -> None:
    """Watch PATHS for HOURS then propose renames."""
    from rich.console import Console
    from renamer.watcher import FolderWatcher
    from renamer.llm import get_llm
    from renamer.engine import build_proposals, apply

    console = Console()
    console.print(f"[bold gold1]Watching[/] {list(paths)} for {hours}h…")
    watcher = FolderWatcher(list(paths))
    records = watcher.watch_for(hours)
    console.print(f"Collected {len(records)} events. Analyzing…")
    raw = get_llm(llm).analyze(records)
    proposals = build_proposals(raw)
    for p in proposals:
        console.print(f"  [dim]•[/] {p}")
    if not dry_run:
        apply(proposals, dry_run=False)
        console.print("[green]Applied.[/]")


if __name__ == "__main__":
    cli()
