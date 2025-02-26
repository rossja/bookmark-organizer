"""
Bookmark Parser Module

Handles parsing of HTML bookmark files from various browsers.
"""
import re
import datetime
from pathlib import Path
from typing import Dict, List, Any, Union, Optional

from bs4 import BeautifulSoup


class BookmarkParser:
    """Parser for browser bookmark HTML files."""

    def __init__(self):
        self.supported_browsers = ["chrome", "firefox", "edge", "safari"]

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a bookmark HTML file into a structured format.

        Args:
            file_path: Path to the bookmarks HTML file

        Returns:
            Structured bookmark data
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Bookmark file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            html_content = f.read()

        return self.parse_html(html_content)

    def parse_html(self, html_content: str) -> Dict[str, Any]:
        """
        Parse HTML content of a bookmarks file.

        Args:
            html_content: HTML string of bookmarks

        Returns:
            Structured bookmark data
        """
        # Detect browser and parse accordingly
        browser = self._detect_browser(html_content)

        # Create soup object
        soup = BeautifulSoup(html_content, "html5lib")

        # Root folder for the bookmarks
        root_folder = {
            "type": "folder",
            "title": "Bookmarks",
            "children": [],
            "dateAdded": int(datetime.datetime.now().timestamp() * 1000)
        }

        # Parse according to browser format
        if browser in ["chrome", "edge"]:
            self._parse_chrome_format(soup, root_folder)
        elif browser == "firefox":
            self._parse_firefox_format(soup, root_folder)
        elif browser == "safari":
            self._parse_safari_format(soup, root_folder)
        else:
            # Generic parsing as fallback
            self._parse_generic_format(soup, root_folder)

        return root_folder

    def _detect_browser(self, html_content: str) -> str:
        """
        Detect which browser the bookmarks file is from.

        Args:
            html_content: HTML string of bookmarks

        Returns:
            Browser name (chrome, firefox, edge, safari, or generic)
        """
        html_lower = html_content.lower()

        if "<!DOCTYPE NETSCAPE-Bookmark-file-1>" in html_content and "firefox" in html_lower:
            return "firefox"
        elif "<!DOCTYPE NETSCAPE-Bookmark-file-1>" in html_content and "chrome" in html_lower:
            return "chrome"
        elif "<!DOCTYPE NETSCAPE-Bookmark-file-1>" in html_content and "edge" in html_lower:
            return "edge"
        elif "<!DOCTYPE html>" in html_content and "safari" in html_lower:
            return "safari"
        else:
            # Most bookmark files use the Netscape format
            if "<!DOCTYPE NETSCAPE-Bookmark-file-1>" in html_content:
                return "chrome"  # Default to Chrome parsing for Netscape format

            return "generic"

    def _parse_chrome_format(self, soup: BeautifulSoup, root_folder: Dict[str, Any]) -> None:
        """
        Parse Chrome/Edge format bookmarks.

        Args:
            soup: BeautifulSoup object of the HTML
            root_folder: Root folder dictionary to populate
        """
        # Find all DL elements (Chrome uses DL/DT/H3 for folders)
        dl_elements = soup.find_all("dl")

        if not dl_elements:
            raise ValueError("No bookmark structure found in Chrome format")

        # Start with the first DL (usually contains all bookmarks)
        main_dl = dl_elements[0]

        # Process this DL into the root folder
        self._process_chrome_folder(main_dl, root_folder)

    def _process_chrome_folder(self, dl_element: Any, parent_folder: Dict[str, Any]) -> None:
        """
        Process a Chrome format folder (DL element).

        Args:
            dl_element: BeautifulSoup DL element
            parent_folder: Parent folder dictionary to populate
        """
        # Get all direct children of the DL
        children = dl_element.find_all(["dt", "h3"], recursive=False)

        current_folder = parent_folder

        for child in dl_element.children:
            if child.name == "dt":
                # This could be a bookmark or a folder
                h3 = child.find("h3", recursive=False)
                a = child.find("a", recursive=False)

                if h3:
                    # This is a folder
                    folder_name = h3.get_text(strip=True)
                    date_added = h3.get("add_date", "0")
                    last_modified = h3.get("last_modified", "0")

                    new_folder = {
                        "type": "folder",
                        "title": folder_name,
                        "children": [],
                        "dateAdded": int(date_added) * 1000 if date_added.isdigit() else 0,
                        "lastModified": int(last_modified) * 1000 if last_modified.isdigit() else 0
                    }

                    parent_folder["children"].append(new_folder)

                    # Process child DL for this folder
                    child_dl = child.find("dl", recursive=False)
                    if child_dl:
                        self._process_chrome_folder(child_dl, new_folder)

                elif a:
                    # This is a bookmark
                    self._add_bookmark_from_anchor(a, parent_folder)

    def _parse_firefox_format(self, soup: BeautifulSoup, root_folder: Dict[str, Any]) -> None:
        """
        Parse Firefox format bookmarks.

        Args:
            soup: BeautifulSoup object of the HTML
            root_folder: Root folder dictionary to populate
        """
        # Firefox uses a similar structure to Chrome but with some differences
        dl_elements = soup.find_all("dl")

        if not dl_elements:
            raise ValueError("No bookmark structure found in Firefox format")

        # Start with the first DL
        main_dl = dl_elements[0]

        # Process this DL into the root folder
        self._process_firefox_folder(main_dl, root_folder)

    def _process_firefox_folder(self, dl_element: Any, parent_folder: Dict[str, Any]) -> None:
        """
        Process a Firefox format folder (DL element).

        Args:
            dl_element: BeautifulSoup DL element
            parent_folder: Parent folder dictionary to populate
        """
        # Similar to Chrome but with Firefox-specific attributes
        for child in dl_element.children:
            if child.name == "dt":
                h3 = child.find("h3", recursive=False)
                a = child.find("a", recursive=False)

                if h3:
                    # This is a folder
                    folder_name = h3.get_text(strip=True)
                    date_added = h3.get("add_date", "0")
                    last_modified = h3.get("last_modified", "0")

                    new_folder = {
                        "type": "folder",
                        "title": folder_name,
                        "children": [],
                        "dateAdded": int(date_added) * 1000 if date_added.isdigit() else 0,
                        "lastModified": int(last_modified) * 1000 if last_modified.isdigit() else 0
                    }

                    parent_folder["children"].append(new_folder)

                    # Process child DL for this folder
                    child_dl = child.find("dl", recursive=False)
                    if child_dl:
                        self._process_firefox_folder(child_dl, new_folder)

                elif a:
                    # This is a bookmark
                    self._add_bookmark_from_anchor(a, parent_folder)

    def _parse_safari_format(self, soup: BeautifulSoup, root_folder: Dict[str, Any]) -> None:
        """
        Parse Safari format bookmarks.

        Args:
            soup: BeautifulSoup object of the HTML
            root_folder: Root folder dictionary to populate
        """
        # Safari has a different format
        # This implementation is simplified as Safari bookmarks can vary

        # Try to find main bookmark elements
        dt_elements = soup.find_all("dt")

        for dt in dt_elements:
            a = dt.find("a")
            if a:
                self._add_bookmark_from_anchor(a, root_folder)

    def _parse_generic_format(self, soup: BeautifulSoup, root_folder: Dict[str, Any]) -> None:
        """
        Generic bookmark parser for unknown formats.

        Args:
            soup: BeautifulSoup object of the HTML
            root_folder: Root folder dictionary to populate
        """
        # Try several common patterns

        # 1. Try DL/DT pattern (most common)
        dl_elements = soup.find_all("dl")
        if dl_elements:
            self._process_chrome_folder(dl_elements[0], root_folder)
            return

        # 2. Try direct anchor tags
        a_elements = soup.find_all("a", href=True)
        for a in a_elements:
            self._add_bookmark_from_anchor(a, root_folder)

    def _add_bookmark_from_anchor(self, a_tag: Any, parent_folder: Dict[str, Any]) -> None:
        """
        Create a bookmark entry from an anchor tag.

        Args:
            a_tag: BeautifulSoup A element
            parent_folder: Parent folder dictionary to populate
        """
        title = a_tag.get_text(strip=True)
        url = a_tag.get("href", "")

        # Skip javascript: URLs, about:, chrome:, etc.
        if not url or url.startswith(("javascript:", "about:", "chrome:", "edge:", "file:")):
            return

        # Get metadata
        date_added = a_tag.get("add_date", a_tag.get("added", "0"))
        last_modified = a_tag.get("last_modified", "0")
        icon = a_tag.get("icon", "")
        tags = a_tag.get("tags", "")

        # Create bookmark object
        bookmark = {
            "type": "bookmark",
            "title": title or "Untitled Bookmark",
            "url": url,
            "dateAdded": int(date_added) * 1000 if date_added.isdigit() else 0,
            "lastModified": int(last_modified) * 1000 if last_modified.isdigit() else 0
        }

        # Add optional fields if present
        if icon:
            bookmark["icon"] = icon

        if tags:
            bookmark["tags"] = [tag.strip() for tag in tags.split(",")]

        parent_folder["children"].append(bookmark)

    def count_bookmarks_and_folders(self, bookmarks: Dict[str, Any]) -> Dict[str, int]:
        """
        Count the number of bookmarks and folders in the structure.

        Args:
            bookmarks: Structured bookmark data

        Returns:
            Dictionary with counts
        """
        result = {"bookmarks": 0, "folders": 0}

        def count_recursive(item):
            if item["type"] == "folder":
                result["folders"] += 1
                for child in item.get("children", []):
                    count_recursive(child)
            else:  # bookmark
                result["bookmarks"] += 1

        count_recursive(bookmarks)

        # Don't count the root folder
        result["folders"] -= 1

        return result
