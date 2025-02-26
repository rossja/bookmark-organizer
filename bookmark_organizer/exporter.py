"""
Bookmark Exporter Module

Exports organized bookmarks to various formats.
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, TextIO


class BookmarkExporter:
    """Exporter for bookmark data to various formats."""

    def __init__(self):
        """Initialize the bookmark exporter."""
        self.logger = logging.getLogger(__name__)

    def export_html(self,
                    bookmarks: Dict[str, Any],
                    output_path: str,
                    browser_compat: str = "chrome") -> None:
        """
        Export bookmarks to an HTML file that can be imported into browsers.

        Args:
            bookmarks: Bookmark data structure
            output_path: Path to save the HTML file
            browser_compat: Which browser to optimize compatibility for
                (chrome, firefox, edge, or safari)
        """
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(
            os.path.abspath(output_path)), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            # Write HTML header based on browser compatibility
            self._write_html_header(f, browser_compat)

            # Write bookmark data
            self._write_bookmark_html(f, bookmarks)

            # Write HTML footer
            self._write_html_footer(f)

    def _write_html_header(self, f: TextIO, browser_compat: str) -> None:
        """
        Write the HTML header for the bookmarks file.

        Args:
            f: File object to write to
            browser_compat: Browser compatibility mode
        """
        # Current timestamp
        timestamp = int(datetime.now().timestamp())

        if browser_compat.lower() in ("chrome", "edge"):
            f.write('<!DOCTYPE NETSCAPE-Bookmark-file-1>\n')
            f.write('<!-- This is an automatically generated file.\n')
            f.write('     It will be read and overwritten.\n')
            f.write('     DO NOT EDIT! -->\n')
            f.write(
                '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
            f.write(f'<TITLE>Bookmarks</TITLE>\n')
            f.write(f'<H1>Bookmarks</H1>\n')
            f.write(f'<DL><p>\n')

        elif browser_compat.lower() == "firefox":
            f.write('<!DOCTYPE NETSCAPE-Bookmark-file-1>\n')
            f.write('<!-- This is an automatically generated file.\n')
            f.write('     It will be read and overwritten.\n')
            f.write('     DO NOT EDIT! -->\n')
            f.write(
                '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
            f.write(f'<TITLE>Bookmarks</TITLE>\n')
            f.write(f'<H1>Bookmarks Menu</H1>\n')
            f.write(f'<DL><p>\n')

        elif browser_compat.lower() == "safari":
            f.write('<!DOCTYPE html>\n')
            f.write('<html>\n')
            f.write('<head>\n')
            f.write('    <meta charset="UTF-8">\n')
            f.write('    <title>Bookmarks</title>\n')
            f.write('</head>\n')
            f.write('<body>\n')
            f.write(f'<h1>Bookmarks</h1>\n')
            f.write(f'<dl><p>\n')

        else:  # Generic format, compatible with most browsers
            f.write('<!DOCTYPE NETSCAPE-Bookmark-file-1>\n')
            f.write(
                '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
            f.write(f'<TITLE>Bookmarks</TITLE>\n')
            f.write(f'<H1>Bookmarks</H1>\n')
            f.write(f'<DL><p>\n')

    def _write_html_footer(self, f: TextIO) -> None:
        """
        Write the HTML footer for the bookmarks file.

        Args:
            f: File object to write to
        """
        f.write('</DL><p>\n')

    def _write_bookmark_html(self, f: TextIO, bookmark_data: Dict[str, Any], indent: int = 1) -> None:
        """
        Write bookmark data as HTML.

        Args:
            f: File object to write to
            bookmark_data: Bookmark data to write
            indent: Current indentation level
        """
        # Skip the root folder's title, just process its children
        if indent == 1 and bookmark_data['type'] == 'folder':
            for child in bookmark_data.get('children', []):
                self._write_bookmark_html(f, child, indent)
            return

        # Generate indentation
        indent_str = '    ' * indent

        if bookmark_data['type'] == 'folder':
            # Write folder header
            date_added = bookmark_data.get(
                'dateAdded', 0) // 1000  # Convert to seconds
            last_modified = bookmark_data.get(
                'lastModified', date_added) // 1000

            f.write(
                f'{indent_str}<DT><H3 ADD_DATE="{date_added}" LAST_MODIFIED="{last_modified}">')
            f.write(self._escape_html(bookmark_data['title']))
            f.write('</H3>\n')

            # Write folder contents
            f.write(f'{indent_str}<DL><p>\n')

            # Write all children
            for child in bookmark_data.get('children', []):
                self._write_bookmark_html(f, child, indent + 1)

            # Close folder
            f.write(f'{indent_str}</DL><p>\n')

        else:  # Bookmark
            # Write bookmark
            url = bookmark_data.get('url', '')
            title = bookmark_data.get('title', url)
            date_added = bookmark_data.get('dateAdded', 0) // 1000
            last_modified = bookmark_data.get(
                'lastModified', date_added) // 1000
            icon = bookmark_data.get('icon', '')

            f.write(f'{indent_str}<DT><A HREF="{url}" ADD_DATE="{date_added}"')

            # Add icon if available
            if icon:
                f.write(f' ICON="{icon}"')

            # Add last modified if available and different from date added
            if last_modified and last_modified != date_added:
                f.write(f' LAST_MODIFIED="{last_modified}"')

            # Add tags if available
            tags = bookmark_data.get('tags', [])
            if tags:
                tags_str = ','.join(tags)
                f.write(f' TAGS="{tags_str}"')

            f.write('>')
            f.write(self._escape_html(title))
            f.write('</A>\n')

    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;')
                )

    def export_json(self, bookmarks: Dict[str, Any], output_path: str) -> None:
        """
        Export bookmarks to a JSON file.

        Args:
            bookmarks: Bookmark data structure
            output_path: Path to save the JSON file
        """
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(
            os.path.abspath(output_path)), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(bookmarks, f, indent=2, ensure_ascii=False)

    def export_csv(self,
                   bookmarks: Dict[str, Any],
                   output_path: str,
                   include_folders: bool = True) -> None:
        """
        Export bookmarks to a CSV file.

        Args:
            bookmarks: Bookmark data structure
            output_path: Path to save the CSV file
            include_folders: Whether to include folder information
        """
        import csv

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(
            os.path.abspath(output_path)), exist_ok=True)

        # Extract all bookmarks
        all_bookmarks = []
        self._extract_all_bookmarks(bookmarks, all_bookmarks)

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            # Define fields
            if include_folders:
                fieldnames = ['title', 'url', 'folder_path',
                              'date_added', 'last_modified', 'tags']
            else:
                fieldnames = ['title', 'url',
                              'date_added', 'last_modified', 'tags']

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for bookmark in all_bookmarks:
                # Skip non-bookmark items
                if bookmark.get('type') != 'bookmark':
                    continue

                row = {
                    'title': bookmark.get('title', ''),
                    'url': bookmark.get('url', ''),
                    'date_added': self._format_timestamp(bookmark.get('dateAdded', 0)),
                    'last_modified': self._format_timestamp(bookmark.get('lastModified', 0))
                }

                # Add folder path if requested
                if include_folders:
                    folder_path = bookmark.get('folderPath', [])
                    row['folder_path'] = '/'.join(folder_path[1:]
                                                  ) if len(folder_path) > 1 else ''

                # Add tags if available
                tags = bookmark.get('tags', [])
                row['tags'] = ','.join(tags) if tags else ''

                writer.writerow(row)

    def _format_timestamp(self, timestamp: int) -> str:
        """
        Format a timestamp as a readable date string.

        Args:
            timestamp: Timestamp in milliseconds

        Returns:
            Formatted date string
        """
        if not timestamp:
            return ""

        try:
            dt = datetime.fromtimestamp(timestamp / 1000)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return ""

    def _extract_all_bookmarks(self,
                               bookmark_data: Dict[str, Any],
                               result: List[Dict[str, Any]],
                               current_path: List[str] = None) -> None:
        """
        Extract all bookmarks from nested structure into a flat list.

        Args:
            bookmark_data: The bookmark data structure
            result: The list to append bookmarks to
            current_path: The current folder path
        """
        if current_path is None:
            current_path = []

        if bookmark_data['type'] == 'folder':
            folder_path = current_path + [bookmark_data['title']]

            for child in bookmark_data.get('children', []):
                if child['type'] == 'bookmark':
                    # Add folder path information to bookmark
                    child_copy = child.copy()
                    child_copy['folderPath'] = folder_path
                    result.append(child_copy)
                else:  # It's a folder
                    self._extract_all_bookmarks(child, result, folder_path)
