"""
Bookmark Validator Module

Validates bookmarks by checking for broken links and finding duplicates.
"""
import concurrent.futures
import hashlib
import logging
import re
import time
from collections import defaultdict
from typing import Dict, List, Any, Set, Tuple, Optional
from urllib.parse import urlparse

import requests
from tqdm import tqdm


class BookmarkValidator:
    """Validator for bookmark data that checks for issues like broken links and duplicates."""

    def __init__(self,
                concurrency: int = 10,
                timeout: int = 5,
                user_agent: str = "Mozilla/5.0 (compatible; BookmarkOrganizer/0.1)"):
        """
        Initialize the bookmark validator.

        Args:
            concurrency: Number of concurrent requests when checking links
            timeout: Timeout for HTTP requests in seconds
            user_agent: User agent string for HTTP requests
        """
        self.logger = logging.getLogger(__name__)
        self.concurrency = concurrency
        self.timeout = timeout
        self.user_agent = user_agent

        # Headers for HTTP requests
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'DNT': '1',  # Do Not Track
        }

        # Create a session object for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def find_broken_links(self, bookmarks: Dict[str, Any],
                         show_progress: bool = True) -> List[Dict[str, Any]]:
        """
        Check for broken links in the bookmarks.

        Args:
            bookmarks: Bookmark data structure
            show_progress: Whether to show a progress bar

        Returns:
            List of broken bookmark references
        """
        # Extract all bookmarks
        all_bookmarks = []
        self._extract_all_bookmarks(bookmarks, all_bookmarks)

        # Remove bookmarks with invalid URLs
        valid_bookmarks = [
            b for b in all_bookmarks if self._is_valid_url(b.get('url', ''))]

        broken_links = []

        # Use concurrent requests for efficiency
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            # Submit all requests
            future_to_bookmark = {
                executor.submit(self._check_link, bookmark): bookmark
                for bookmark in valid_bookmarks
            }

            # Process results as they complete
            if show_progress:
                iterator = tqdm(
                    concurrent.futures.as_completed(future_to_bookmark),
                    total=len(future_to_bookmark),
                    desc="Checking links"
                )
            else:
                iterator = concurrent.futures.as_completed(future_to_bookmark)

            for future in iterator:
                bookmark = future_to_bookmark[future]
                try:
                    is_broken, status = future.result()
                    if is_broken:
                        bookmark_copy = bookmark.copy()
                        bookmark_copy['status'] = status
                        broken_links.append(bookmark_copy)
                except Exception as exc:
                    self.logger.error(
                        f"Error checking {bookmark.get('url')}: {exc}")
                    # Count as broken if an exception occurred
                    bookmark_copy = bookmark.copy()
                    bookmark_copy['status'] = "Error: " + str(exc)
                    broken_links.append(bookmark_copy)

        return broken_links

    def _check_link(self, bookmark: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if a link is broken by making a HEAD request.

        Args:
            bookmark: Bookmark dictionary

        Returns:
            Tuple of (is_broken, status_message)
        """
        url = bookmark.get('url', '')

        try:
            # Skip certain URL types
            if url.startswith(('javascript:', 'file:', 'chrome:', 'edge:', 'about:')):
                return False, "Skipped (non-HTTP URL)"

            # Try HEAD request first (faster)
            response = self.session.head(
                url,
                timeout=self.timeout,
                allow_redirects=True
            )

            # Some servers don't support HEAD, so if we get 405/404/403, try GET instead
            if response.status_code in (403, 404, 405):
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True,
                    stream=True  # Don't download the full response content
                )

                # Close the connection to avoid downloading the whole resource
                response.close()

            # If status code is in 4xx or 5xx range, the link is broken
            if response.status_code >= 400:
                return True, f"HTTP {response.status_code}"

            return False, f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            return True, "Timeout"
        except requests.exceptions.ConnectionError:
            return True, "Connection Error"
        except requests.exceptions.TooManyRedirects:
            return True, "Too Many Redirects"
        except requests.exceptions.RequestException as e:
            return True, str(e)

    def find_duplicates(self,
                       bookmarks: Dict[str, Any],
                       url_normalize: bool = True,
                       title_similarity: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find duplicate bookmarks based on URL and title similarity.

        Args:
            bookmarks: Bookmark data structure
            url_normalize: Whether to normalize URLs for comparison
            title_similarity: Whether to use title similarity for edge cases

        Returns:
            Dictionary mapping canonical URLs to lists of duplicate bookmarks
        """
        # Extract all bookmarks
        all_bookmarks = []
        self._extract_all_bookmarks(bookmarks, all_bookmarks)

        # Group by normalized URL
        url_groups = defaultdict(list)

        for bookmark in all_bookmarks:
            url = bookmark.get('url', '')
            if not url:
                continue

            # Normalize URL if enabled
            if url_normalize:
                norm_url = self._normalize_url(url)
            else:
                norm_url = url

            url_groups[norm_url].append(bookmark)

        # Filter to only groups with duplicates
        duplicates = {url: bookmarks for url,
            bookmarks in url_groups.items() if len(bookmarks) > 1}

        # Apply title similarity for edge cases if enabled
        if title_similarity and len(all_bookmarks) > 0:
            self._refine_with_title_similarity(duplicates)

        return duplicates

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for comparison purposes.

        Args:
            url: URL string

        Returns:
            Normalized URL
        """
        try:
            # Parse URL
            parsed = urlparse(url)

            # Convert to lowercase
            netloc = parsed.netloc.lower()

            # Remove www. prefix
            if netloc.startswith('www.'):
                netloc = netloc[4:]

            # Remove trailing slashes from path
            path = parsed.path.rstrip('/')

            # Some sites use different protocols but are the same resource
            # Standardize on https for comparison
            scheme = 'https'

            # Ignore most query parameters for certain sites
            query = parsed.query
            if ('youtube.com' in netloc or 'youtu.be' in netloc) and 'v=' in query:
                # For YouTube, only keep the video ID
                params = dict(pair.split('=')
                              for pair in query.split('&') if '=' in pair)
                if 'v' in params:
                    query = f"v={params['v']}"
                else:
                    query = ""

            # Remove tracking parameters
            if query:
                query_params = query.split('&')
                filtered_params = []

                # List of common tracking parameters to remove
                tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term',
                                   'utm_content', 'fbclid', 'gclid', 'ref', 'source',
                                   'ref_src', 'ref_url', '_ga'}

                for param in query_params:
                    if '=' in param:
                        name = param.split('=')[0]
                        if name.lower() not in tracking_params:
                            filtered_params.append(param)

                query = '&'.join(filtered_params)

            # Reconstruct the normalized URL
            normalized = f"{scheme}://{netloc}{path}"

            # Add query string if it exists
            if query:
                normalized += f"?{query}"

            return normalized

        except Exception as e:
            # If parsing fails, return the original URL
            self.logger.warning(f"URL normalization failed for {url}: {e}")
            return url

    def _refine_with_title_similarity(self, duplicates: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Refine duplicate detection using title similarity.

        Args:
            duplicates: Dictionary of duplicate groups to refine
        """
        # This would implement title similarity logic
        # For now, we'll just keep the URL-based duplicates
        pass

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

    def _is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid for HTTP/HTTPS requests.

        Args:
            url: URL string

        Returns:
            True if valid, False otherwise
        """
        if not url:
            return False

        # Skip non-web URLs
        if url.startswith(('javascript:', 'file:', 'chrome:', 'edge:', 'about:')):
            return False

        # Basic URL pattern matching
        pattern = re.compile(
            r'^(?:http|https)://'  # http:// or https://
            # domain
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ipv4
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+), re.IGNORECASE)

        return bool(pattern.match(url))