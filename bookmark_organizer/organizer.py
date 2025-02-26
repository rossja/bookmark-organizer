"""
Bookmark Organizer Module

Organizes bookmarks into a more structured and meaningful hierarchy.
"""
import copy
import logging
from collections import defaultdict
from typing import Dict, List, Any, Set, Tuple, Optional

from tqdm import tqdm


class BookmarkOrganizer:
    """Organizer for bookmark data to create a better folder structure."""

    def __init__(self):
        """Initialize the bookmark organizer."""
        self.logger = logging.getLogger(__name__)

    def organize(self,
                 bookmarks: Dict[str, Any],
                 categories: Dict[str, List[Dict[str, Any]]],
                 max_bookmarks_per_folder: int = 50,
                 preserve_existing: bool = True) -> Dict[str, Any]:
        """
        Organize bookmarks into a new structure based on categories.

        Args:
            bookmarks: Original bookmark data
            categories: Category mapping from analyzer
            max_bookmarks_per_folder: Maximum number of bookmarks per folder
            preserve_existing: Whether to preserve existing folders

        Returns:
            New bookmark structure
        """
        # Create a deep copy to avoid modifying the original
        organized = copy.deepcopy(bookmarks)

        # Create a set of all bookmarks to track which ones have been categorized
        all_bookmarks = []
        self._extract_all_bookmarks(bookmarks, all_bookmarks)

        # Create a set of URLs for quick lookup
        all_urls = {bookmark.get(
            'url', ''): bookmark for bookmark in all_bookmarks if bookmark.get('url')}

        # Track which bookmarks have been assigned to a category
        assigned_urls = set()

        # Clean up the root folder's children (we'll rebuild it)
        # Keep any non-bookmark-related items
        if preserve_existing:
            # Keep existing structure but add new category folders
            root_children = organized['children']
        else:
            # Start fresh
            organized['children'] = []
            root_children = []

        # Add category folders
        for category_name, bookmarks_in_category in categories.items():
            # Skip if the category is empty
            if not bookmarks_in_category:
                continue

            # Create a folder for this category
            category_folder = {
                'type': 'folder',
                'title': category_name,
                'children': [],
                'dateAdded': organized.get('dateAdded', 0)
            }

            # If we have a lot of bookmarks in this category, consider subfolders
            if len(bookmarks_in_category) > max_bookmarks_per_folder:
                # Try to create meaningful subfolders
                subfolders = self._create_subfolders(
                    bookmarks_in_category, max_bookmarks_per_folder)

                # Add bookmarks to subfolders
                for subfolder_name, subfolder_bookmarks in subfolders.items():
                    subfolder = {
                        'type': 'folder',
                        'title': subfolder_name,
                        'children': [],
                        'dateAdded': organized.get('dateAdded', 0)
                    }

                    # Add each bookmark to this subfolder
                    for bookmark in subfolder_bookmarks:
                        url = bookmark.get('url', '')
                        if url and url in all_urls:
                            # Add a copy of the bookmark
                            subfolder['children'].append(
                                copy.deepcopy(all_urls[url]))
                            assigned_urls.add(url)

                    # Only add non-empty subfolders
                    if subfolder['children']:
                        category_folder['children'].append(subfolder)
            else:
                # Add bookmarks directly to the category folder
                for bookmark in bookmarks_in_category:
                    url = bookmark.get('url', '')
                    if url and url in all_urls:
                        # Add a copy of the bookmark
                        category_folder['children'].append(
                            copy.deepcopy(all_urls[url]))
                        assigned_urls.add(url)

            # Only add non-empty category folders
            if category_folder['children']:
                if preserve_existing:
                    # Add to the existing structure
                    organized['children'].append(category_folder)
                else:
                    # Add to our new list
                    root_children.append(category_folder)

        # Create an "Uncategorized" folder for remaining bookmarks
        uncategorized = []
        for url, bookmark in all_urls.items():
            if url and url not in assigned_urls:
                uncategorized.append(copy.deepcopy(bookmark))

        if uncategorized:
            uncategorized_folder = {
                'type': 'folder',
                'title': 'Uncategorized',
                'children': uncategorized,
                'dateAdded': organized.get('dateAdded', 0)
            }

            if preserve_existing:
                organized['children'].append(uncategorized_folder)
            else:
                root_children.append(uncategorized_folder)

        # If not preserving, update the root children
        if not preserve_existing:
            organized['children'] = root_children

        # Sort all folders alphabetically
        self._sort_folders(organized)

        return organized

    def _create_subfolders(self,
                           bookmarks: List[Dict[str, Any]],
                           max_per_folder: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Create meaningful subfolders for a large category.

        Args:
            bookmarks: List of bookmarks in the category
            max_per_folder: Maximum bookmarks per subfolder

        Returns:
            Dictionary mapping subfolder names to lists of bookmarks
        """
        # Try to find meaningful groupings

        # 1. Group by domain (most intuitive grouping)
        domain_groups = defaultdict(list)

        for bookmark in bookmarks:
            url = bookmark.get('url', '')
            if not url:
                continue

            domain = self._extract_domain(url)
            if domain:
                domain_groups[domain].append(bookmark)

        # If we have a reasonable number of domains, use those as subfolders
        if 2 <= len(domain_groups) <= 10:
            # Use domain names as subfolder names
            return {
                self._format_domain_name(domain): bookmarks
                for domain, bookmarks in domain_groups.items()
            }

        # 2. If too many domains, group by TLD or common domain parts
        if len(domain_groups) > 10:
            tld_groups = defaultdict(list)

            for domain, domain_bookmarks in domain_groups.items():
                tld = domain.split('.')[-1] if '.' in domain else 'other'
                tld_groups[tld].extend(domain_bookmarks)

            # If we have a reasonable number of TLDs, use those
            if 2 <= len(tld_groups) <= 10:
                return {
                    f"{tld.upper()} Sites": bookmarks
                    for tld, bookmarks in tld_groups.items()
                }

        # 3. Alphabetical grouping as a fallback
        alpha_groups = defaultdict(list)

        for bookmark in bookmarks:
            title = bookmark.get('title', '')
            if not title:
                continue

            first_letter = title[0].upper() if title else '#'

            # Group non-alphabetic characters
            if not first_letter.isalpha():
                first_letter = '#'

            alpha_groups[first_letter].append(bookmark)

        # Combine small groups
        final_groups = {}
        current_group = []
        current_name = ""

        # Sort the groups
        sorted_groups = sorted(alpha_groups.items())

        for letter, group in sorted_groups:
            if len(current_group) + len(group) <= max_per_folder:
                # Add to current group
                current_group.extend(group)
                if current_name:
                    current_name = f"{current_name}-{letter}"
                else:
                    current_name = letter
            else:
                # Start a new group
                if current_group:
                    final_groups[f"{current_name}"] = current_group
                current_group = group
                current_name = letter

        # Add the last group
        if current_group:
            final_groups[f"{current_name}"] = current_group

        return final_groups

    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from a URL.

        Args:
            url: URL string

        Returns:
            Domain string
        """
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]

            return domain
        except:
            return ""

    def _format_domain_name(self, domain: str) -> str:
        """
        Format domain name for use as a folder name.

        Args:
            domain: Domain string

        Returns:
            Formatted domain name
        """
        # Remove TLD
        name_parts = domain.split('.')
        if len(name_parts) > 1:
            name = name_parts[0]
        else:
            name = domain

        # Capitalize
        return name.capitalize()

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

    def _sort_folders(self, folder: Dict[str, Any]) -> None:
        """
        Sort folders and their children alphabetically.

        Args:
            folder: Folder dictionary to sort
        """
        if folder['type'] != 'folder':
            return

        # Sort direct children
        children = folder.get('children', [])

        # Separate folders and bookmarks
        folders = [child for child in children if child['type'] == 'folder']
        bookmarks = [
            child for child in children if child['type'] == 'bookmark']

        # Sort folders by title
        folders.sort(key=lambda x: x['title'].lower())

        # Sort bookmarks by title
        bookmarks.sort(key=lambda x: x['title'].lower())

        # Update children list
        folder['children'] = folders + bookmarks

        # Recursively sort subfolders
        for subfolder in folders:
            self._sort_folders(subfolder)

    def remove_broken_links(self,
                            bookmarks: Dict[str, Any],
                            broken_links: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Remove broken links from the bookmark structure.

        Args:
            bookmarks: Bookmark data structure
            broken_links: List of broken bookmark references

        Returns:
            Bookmark structure without broken links
        """
        # Create a deep copy
        result = copy.deepcopy(bookmarks)

        # Create a set of broken URLs for quick lookup
        broken_urls = {link.get('url', '') for link in broken_links}

        # Remove broken links
        self._remove_broken_recursive(result, broken_urls)

        return result

    def _remove_broken_recursive(self, folder: Dict[str, Any], broken_urls: Set[str]) -> None:
        """
        Recursively remove broken links from a folder.

        Args:
            folder: Folder dictionary
            broken_urls: Set of broken URLs
        """
        if folder['type'] != 'folder':
            return

        # Filter out broken links
        children = folder.get('children', [])
        filtered_children = []

        for child in children:
            if child['type'] == 'bookmark':
                if child.get('url', '') not in broken_urls:
                    filtered_children.append(child)
            else:  # It's a folder
                # Add the folder (we'll process it recursively)
                filtered_children.append(child)
                self._remove_broken_recursive(child, broken_urls)

        # Update children list
        folder['children'] = filtered_children

    def merge_duplicates(self,
                         bookmarks: Dict[str, Any],
                         duplicates: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Merge duplicate bookmarks, keeping only one copy per unique URL.

        Args:
            bookmarks: Bookmark data structure
            duplicates: Dictionary mapping normalized URLs to lists of duplicate bookmarks

        Returns:
            Bookmark structure with duplicates merged
        """
        # Create a deep copy
        result = copy.deepcopy(bookmarks)

        # For each duplicate group, decide which bookmark to keep
        keep_urls = set()
        remove_urls = set()

        for norm_url, dupes in duplicates.items():
            if not dupes:
                continue

            # Choose the best bookmark to keep
            keep = self._choose_best_bookmark(dupes)

            # Add the URL to keep
            keep_url = keep.get('url', '')
            if keep_url:
                keep_urls.add(keep_url)

            # Add other URLs to remove
            for dupe in dupes:
                dupe_url = dupe.get('url', '')
                if dupe_url and dupe_url != keep_url:
                    remove_urls.add(dupe_url)

        # Remove duplicates from the structure
        self._remove_duplicates_recursive(result, remove_urls)

        return result

    def _choose_best_bookmark(self, duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Choose the best bookmark to keep from a group of duplicates.

        Args:
            duplicates: List of duplicate bookmarks

        Returns:
            The best bookmark to keep
        """
        if not duplicates:
            return {}

        # If only one, return it
        if len(duplicates) == 1:
            return duplicates[0]

        # Choose the one with the most complete data
        scored_bookmarks = []

        for bookmark in duplicates:
            score = 0

            # Prefer bookmarks with titles
            if bookmark.get('title'):
                score += 10

            # Prefer bookmarks with icons
            if bookmark.get('icon'):
                score += 5

            # Prefer bookmarks with shorter folder paths (less deeply nested)
            folder_path = bookmark.get('folderPath', [])
            score -= len(folder_path)

            # Prefer more recently added bookmarks
            if bookmark.get('dateAdded', 0) > 0:
                score += 1

            scored_bookmarks.append((score, bookmark))

        # Sort by score (descending)
        scored_bookmarks.sort(reverse=True)

        # Return the highest-scored bookmark
        return scored_bookmarks[0][1]

    def _remove_duplicates_recursive(self, folder: Dict[str, Any], remove_urls: Set[str]) -> None:
        """
        Recursively remove duplicate bookmarks from a folder.

        Args:
            folder: Folder dictionary
            remove_urls: Set of URLs to remove
        """
        if folder['type'] != 'folder':
            return

        # Filter out duplicates
        children = folder.get('children', [])
        filtered_children = []

        for child in children:
            if child['type'] == 'bookmark':
                if child.get('url', '') not in remove_urls:
                    filtered_children.append(child)
            else:  # It's a folder
                # Add the folder (we'll process it recursively)
                filtered_children.append(child)
                self._remove_duplicates_recursive(child, remove_urls)

        # Update children list
        folder['children'] = filtered_children
