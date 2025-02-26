"""
Bookmark Organizer - Main CLI entry point
"""
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from bookmark_organizer.parser import BookmarkParser
from bookmark_organizer.analyzer import BookmarkAnalyzer
from bookmark_organizer.organizer import BookmarkOrganizer
from bookmark_organizer.validator import BookmarkValidator
from bookmark_organizer.exporter import BookmarkExporter

# Create Typer app
app = typer.Typer(
    name="bookmark_organizer",
    help="A tool to organize and clean up browser bookmarks",
    add_completion=False,
)

console = Console()


@app.command("import")
def import_bookmarks(
    file_path: str = typer.Argument(...,
                                    help="Path to the bookmarks HTML file"),
    output_path: str = typer.Option(
        None, "--output", "-o", help="Path to save parsed bookmarks as JSON"),
):
    """Import and parse bookmarks from an HTML file."""
    console.print(f"[bold blue]Importing bookmarks from:[/] {file_path}")

    try:
        parser = BookmarkParser()
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Parsing bookmarks file...", total=1)
            bookmarks = parser.parse_file(file_path)
            progress.update(task, advance=1)

        count = parser.count_bookmarks_and_folders(bookmarks)
        console.print(
            f"[green]Successfully imported[/] {count['bookmarks']} bookmarks in {count['folders']} folders")

        if output_path:
            exporter = BookmarkExporter()
            exporter.export_json(bookmarks, output_path)
            console.print(f"[green]Bookmarks saved to:[/] {output_path}")

    except Exception as e:
        console.print(f"[bold red]Error importing bookmarks:[/] {str(e)}")
        raise typer.Exit(code=1)


@app.command("validate")
def validate_bookmarks(
    file_path: str = typer.Argument(...,
                                    help="Path to the bookmarks HTML file"),
    check_links: bool = typer.Option(
        True, "--check-links/--no-check-links", help="Check for broken links"),
    find_duplicates: bool = typer.Option(
        True, "--find-duplicates/--no-duplicates", help="Find duplicate bookmarks"),
    output_path: Optional[str] = typer.Option(
        None, "--output", "-o", help="Path to save validation report"),
):
    """Validate bookmarks and check for issues."""
    console.print(f"[bold blue]Validating bookmarks from:[/] {file_path}")

    try:
        # Parse bookmarks
        parser = BookmarkParser()
        bookmarks = parser.parse_file(file_path)

        # Create validator
        validator = BookmarkValidator()

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=console,
        ) as progress:
            # Check for broken links
            broken_links = []
            if check_links:
                task = progress.add_task(
                    "Checking for broken links...", total=1)
                broken_links = validator.find_broken_links(bookmarks)
                progress.update(task, advance=1)

            # Find duplicates
            duplicates = []
            if find_duplicates:
                task = progress.add_task(
                    "Finding duplicate bookmarks...", total=1)
                duplicates = validator.find_duplicates(bookmarks)
                progress.update(task, advance=1)

        # Display results
        console.print(f"\n[bold]Validation Results:[/]")

        if check_links:
            console.print(
                f"Found [bold red]{len(broken_links)}[/] broken links")
            if broken_links:
                console.print("[bold]Top 5 broken links:[/]")
                for idx, link in enumerate(broken_links[:5]):
                    console.print(
                        f"  {idx+1}. [italic]{link['title']}[/] - {link['url']}")

        if find_duplicates:
            console.print(
                f"Found [bold yellow]{len(duplicates)}[/] duplicate bookmarks")
            if duplicates:
                console.print("[bold]Sample duplicates:[/]")
                for idx, group in enumerate(list(duplicates.values())[:3]):
                    console.print(
                        f"  Group {idx+1}: {len(group)} copies of [italic]{group[0]['title']}[/]")

        # Export report if requested
        if output_path:
            report = {
                "broken_links": broken_links if check_links else [],
                "duplicates": duplicates if find_duplicates else {},
            }
            exporter = BookmarkExporter()
            exporter.export_json(report, output_path)
            console.print(
                f"\n[green]Validation report saved to:[/] {output_path}")

    except Exception as e:
        console.print(f"[bold red]Error validating bookmarks:[/] {str(e)}")
        raise typer.Exit(code=1)


@app.command("organize")
def organize_bookmarks(
    file_path: str = typer.Argument(...,
                                    help="Path to the bookmarks HTML file"),
    output_path: str = typer.Option(
        "organized_bookmarks.html", "--output", "-o", help="Path to save organized bookmarks"),
    remove_broken: bool = typer.Option(
        False, "--remove-broken", help="Remove broken links"),
    merge_duplicates: bool = typer.Option(
        False, "--merge-duplicates", help="Merge duplicate bookmarks"),
    export_format: str = typer.Option(
        "html", "--format", "-f", help="Export format (html or json)"),
):
    """Organize bookmarks into a better structure."""
    console.print(f"[bold blue]Organizing bookmarks from:[/] {file_path}")

    try:
        # Parse bookmarks
        parser = BookmarkParser()
        bookmarks = parser.parse_file(file_path)

        # Set up components
        analyzer = BookmarkAnalyzer()
        organizer = BookmarkOrganizer()
        validator = BookmarkValidator()
        exporter = BookmarkExporter()

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=console,
        ) as progress:
            # Handle broken links
            if remove_broken:
                task = progress.add_task(
                    "Checking for broken links...", total=1)
                broken_links = validator.find_broken_links(bookmarks)
                progress.update(task, advance=1)

                if broken_links:
                    task = progress.add_task(
                        "Removing broken links...", total=1)
                    bookmarks = organizer.remove_broken_links(
                        bookmarks, broken_links)
                    progress.update(task, advance=1)
                    console.print(f"Removed {len(broken_links)} broken links")

            # Handle duplicates
            if merge_duplicates:
                task = progress.add_task(
                    "Finding duplicate bookmarks...", total=1)
                duplicates = validator.find_duplicates(bookmarks)
                progress.update(task, advance=1)

                if duplicates:
                    task = progress.add_task(
                        "Merging duplicate bookmarks...", total=1)
                    bookmarks = organizer.merge_duplicates(
                        bookmarks, duplicates)
                    progress.update(task, advance=1)
                    console.print(
                        f"Merged {sum(len(group) - 1 for group in duplicates.values())} duplicate bookmarks")

            # Categorize bookmarks
            task = progress.add_task(
                "Analyzing and categorizing bookmarks...", total=1)
            categories = analyzer.categorize(bookmarks)
            progress.update(task, advance=1)

            # Create organized structure
            task = progress.add_task(
                "Creating optimized folder structure...", total=1)
            organized = organizer.organize(bookmarks, categories)
            progress.update(task, advance=1)

            # Export the result
            task = progress.add_task(
                f"Exporting to {export_format}...", total=1)
            if export_format.lower() == "html":
                exporter.export_html(organized, output_path)
            elif export_format.lower() == "json":
                exporter.export_json(organized, output_path)
            else:
                console.print(
                    f"[bold red]Unsupported format:[/] {export_format}")
                raise typer.Exit(code=1)
            progress.update(task, advance=1)

        # Summary
        count = parser.count_bookmarks_and_folders(organized)
        console.print(
            f"\n[green]Successfully organized[/] {count['bookmarks']} bookmarks into {count['folders']} folders")
        console.print(f"Created {len(categories)} categories")
        console.print(f"[green]Organized bookmarks saved to:[/] {output_path}")

    except Exception as e:
        console.print(f"[bold red]Error organizing bookmarks:[/] {str(e)}")
        raise typer.Exit(code=1)


@app.command("info")
def show_info():
    """Show information about the Bookmark Organizer."""
    console.print("[bold blue]Bookmark Organizer[/]")
    console.print(
        "A tool to parse, analyze, organize, and clean up browser bookmarks.\n")

    console.print("[bold]Features:[/]")
    console.print("  • Import HTML bookmark exports from popular browsers")
    console.print("  • Analyze and extract metadata from bookmarks")
    console.print("  • Check for broken links and identify duplicates")
    console.print("  • Categorize bookmarks based on content analysis")
    console.print("  • Create an optimized folder structure")
    console.print("  • Export to various formats (HTML, JSON)\n")

    console.print("[bold]Usage:[/]")
    console.print("  bookmark_organizer import path/to/bookmarks.html")
    console.print("  bookmark_organizer validate path/to/bookmarks.html")
    console.print(
        "  bookmark_organizer organize path/to/bookmarks.html -o organized.html\n")

    console.print("[bold]Get help on specific commands:[/]")
    console.print("  bookmark_organizer import --help")
    console.print("  bookmark_organizer validate --help")
    console.print("  bookmark_organizer organize --help")


if __name__ == "__main__":
    app()
