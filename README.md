# Bookmark Organizer

An AI/ML assisted Python-based tool to parse, analyze, organize, and clean up browser bookmarks.

Co-written by Claude Sonnet 3.7

## Features

- Import HTML bookmark exports from popular browsers (Chrome, Firefox, Edge, Safari)
- Analyze and extract metadata from bookmarks
- Check for broken links and identify duplicates
- Categorize bookmarks based on content analysis
- Create an optimized folder structure
- Export to various formats (HTML, JSON, CSV)

## Installation

### Prerequisites

- Python 3.8 or higher
- `uv` for dependency management

### Installing `uv`

If you don't have `uv` installed, you can install it using one of the following methods:

#### On macOS/Linux:

```bash
curl -sL https://astral.sh/uv/install.sh | sh
```

#### On Windows:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Installing Bookmark Organizer

1. Clone the repository or download the source code:

```bash
git clone https://github.com/rossja/bookmark-organizer.git
cd bookmark-organizer
```

2. Use `uv` to install dependencies and set up the project:

```bash
# Install dependencies from pyproject.toml and create a .venv directory
uv sync

# Install the package in development mode
uv pip install -e .
```

## Usage

### Running Commands with UV

You can run the bookmark organizer using `uv run`:

```bash
# Basic usage
uv run bookmark-organizer --help

# Or run specific commands
uv run bookmark-organizer import path/to/bookmarks.html
```

Alternatively, if you installed in development mode with `uv pip install -e .`, you can run the commands directly:

```bash
bookmark-organizer --help
```

### Command Line Interface

#### Basic Usage

```bash
# Import and analyze bookmarks
uv run bookmark-organizer import path/to/bookmarks.html

# Validate bookmarks (check for broken links and duplicates)
uv run bookmark-organizer validate path/to/bookmarks.html

# Organize bookmarks into a better structure
uv run bookmark-organizer organize path/to/bookmarks.html -o organized_bookmarks.html
```

#### Extended Options

```bash
# Get help on available commands
uv run bookmark-organizer --help

# Get help on a specific command
uv run bookmark-organizer organize --help

# Organize and remove broken links
uv run bookmark-organizer organize path/to/bookmarks.html --remove-broken

# Organize and merge duplicates
uv run bookmark-organizer organize path/to/bookmarks.html --merge-duplicates

# Export to JSON format
uv run bookmark-organizer organize path/to/bookmarks.html -f json -o bookmarks.json
```

### Python API

You can also use the Bookmark Organizer as a Python library:

```python
from bookmark_organizer.parser import BookmarkParser
from bookmark_organizer.analyzer import BookmarkAnalyzer
from bookmark_organizer.organizer import BookmarkOrganizer
from bookmark_organizer.validator import BookmarkValidator
from bookmark_organizer.exporter import BookmarkExporter

# Parse bookmarks
parser = BookmarkParser()
bookmarks = parser.parse_file("path/to/bookmarks.html")

# Analyze and categorize
analyzer = BookmarkAnalyzer()
categories = analyzer.categorize(bookmarks)

# Find issues
validator = BookmarkValidator()
broken_links = validator.find_broken_links(bookmarks)
duplicates = validator.find_duplicates(bookmarks)

# Organize into a new structure
organizer = BookmarkOrganizer()
organized = organizer.organize(bookmarks, categories)

# Export to various formats
exporter = BookmarkExporter()
exporter.export_html(organized, "path/to/output.html")
exporter.export_json(organized, "path/to/output.json")
exporter.export_csv(organized, "path/to/output.csv")
```

## Exporting Bookmarks from Your Browser

### Chrome

1. Open Chrome and click the three dots in the top-right corner
2. Go to Bookmarks > Bookmark Manager
3. Click the three dots in the bookmark manager and select "Export bookmarks"
4. Save the HTML file

### Firefox

1. Open Firefox and click the three lines in the top-right corner
2. Go to Bookmarks > Manage Bookmarks
3. Click "Import and Backup" > "Export Bookmarks to HTML"
4. Save the HTML file

### Edge

1. Open Edge and click the three dots in the top-right corner
2. Go to Favorites > Manage favorites
3. Click the three dots in the favorites manager and select "Export favorites"
4. Save the HTML file

### Safari

1. Open Safari and click Safari in the menu bar
2. Go to File > Export Bookmarks
3. Save the HTML file

## Development

To set up a development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/bookmark-organizer.git
cd bookmark-organizer

# Install dependencies and create a virtual environment
uv sync

# Install development dependencies
uv sync --dev

# Install the package in development mode
uv pip install -e .

# Run tests
uv run pytest
```

### Dependency Management

For updating dependencies:

```bash
# Update all dependencies to their latest compatible versions
uv pip sync --upgrade

# Add a new dependency
uv pip add new-package-name

# Add a development dependency
uv pip add --dev new-dev-package
```

## Project Structure

```
bookmark_organizer/
├── pyproject.toml         # Project definition and dependencies
├── README.md
├── .gitignore
├── bookmark_organizer/
│   ├── __init__.py
│   ├── main.py          # CLI interface
│   ├── parser.py        # HTML bookmark parser
│   ├── analyzer.py      # Bookmark analysis and categorization
│   ├── organizer.py     # Bookmark restructuring
│   ├── validator.py     # Broken link checking and duplicate finding
│   └── exporter.py      # Export to various formats
└── tests/
    ├── __init__.py
    ├── test_parser.py
    ├── test_analyzer.py
    ├── test_organizer.py
    └── test_validator.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.