"""
Bookmark Analyzer Module

Analyzes bookmarks to identify patterns, extract metadata, and categorize them.
"""
import re
import logging
from collections import Counter, defaultdict
from typing import Dict, List, Any, Set, Tuple, Optional
from urllib.parse import urlparse, parse_qs

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import tqdm


class BookmarkAnalyzer:
    """
    Analyzer for bookmark data that extracts patterns, categorizes content,
    and identifies themes across a collection of bookmarks.
    """

    def __init__(self, use_ml: bool = True):
        """
        Initialize the bookmark analyzer.

        Args:
            use_ml: Whether to use machine learning for advanced categorization
        """
        self.logger = logging.getLogger(__name__)
        self.use_ml = use_ml

        # Ensure NLTK data is downloaded
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            self.logger.info("Downloading NLTK data...")
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)

        self.stop_words = set(stopwords.words('english'))

        # Common TLDs to recognize site categories
        self.tld_categories = {
            'edu': 'Education',
            'gov': 'Government',
            'org': 'Non-profit',
            'io': 'Technology',
            'dev': 'Development',
            'tech': 'Technology',
            'ai': 'Artificial Intelligence',
            'shop': 'Shopping',
            'store': 'Shopping',
            'blog': 'Blogs',
            'news': 'News',
        }

        # Domain-specific categories
        self.domain_categories = {
            # Development & Tech
            'github.com': 'Development',
            'gitlab.com': 'Development',
            'bitbucket.org': 'Development',
            'stackoverflow.com': 'Development',
            'medium.com': 'Technology & Development',
            'dev.to': 'Development',
            'hackerrank.com': 'Development',
            'leetcode.com': 'Development',
            'codepen.io': 'Web Development',
            'npmjs.com': 'Web Development',
            'pypi.org': 'Python Development',
            'kaggle.com': 'Data Science',

            # Media
            'youtube.com': 'Videos',
            'youtu.be': 'Videos',
            'vimeo.com': 'Videos',
            'twitch.tv': 'Streaming',
            'netflix.com': 'Entertainment',
            'hulu.com': 'Entertainment',
            'spotify.com': 'Music',
            'soundcloud.com': 'Music',
            'bandcamp.com': 'Music',
            'deezer.com': 'Music',
            'apple.com/music': 'Music',

            # Social Media
            'linkedin.com': 'Professional',
            'facebook.com': 'Social Media',
            'twitter.com': 'Social Media',
            'instagram.com': 'Social Media',
            'pinterest.com': 'Social Media',
            'reddit.com': 'Social Media',
            'tumblr.com': 'Social Media',
            'tiktok.com': 'Social Media',
            'snapchat.com': 'Social Media',
            'discord.com': 'Communication',
            'slack.com': 'Communication',

            # Shopping
            'amazon.com': 'Shopping',
            'amazon.co.uk': 'Shopping',
            'amazon.de': 'Shopping',
            'ebay.com': 'Shopping',
            'etsy.com': 'Shopping',
            'aliexpress.com': 'Shopping',
            'walmart.com': 'Shopping',
            'target.com': 'Shopping',
            'bestbuy.com': 'Shopping',

            # News & Information
            'nytimes.com': 'News',
            'washingtonpost.com': 'News',
            'bbc.com': 'News',
            'bbc.co.uk': 'News',
            'cnn.com': 'News',
            'theguardian.com': 'News',
            'reuters.com': 'News',
            'apnews.com': 'News',
            'wikipedia.org': 'Reference',

            # Productivity
            'notion.so': 'Productivity',
            'trello.com': 'Productivity',
            'asana.com': 'Productivity',
            'evernote.com': 'Productivity',
            'todoist.com': 'Productivity',
            'google.com/docs': 'Documents',
            'google.com/sheets': 'Spreadsheets',
            'google.com/drive': 'Cloud Storage',
            'dropbox.com': 'Cloud Storage',
            'onedrive.live.com': 'Cloud Storage',
            'docs.microsoft.com': 'Documentation',

            # Learning
            'coursera.org': 'Education',
            'udemy.com': 'Education',
            'edx.org': 'Education',
            'khanacademy.org': 'Education',
            'udacity.com': 'Education',
            'pluralsight.com': 'Technology Education',
            'freecodecamp.org': 'Web Development Education',

            # Finance
            'finance.yahoo.com': 'Finance',
            'marketwatch.com': 'Finance',
            'bloomberg.com': 'Finance',
            'investopedia.com': 'Finance Education',
            'paypal.com': 'Payment',
            'chase.com': 'Banking',
            'bankofamerica.com': 'Banking',
            'wellsfargo.com': 'Banking',

            # Travel
            'booking.com': 'Travel',
            'airbnb.com': 'Travel',
            'expedia.com': 'Travel',
            'tripadvisor.com': 'Travel',
            'maps.google.com': 'Maps',

            # Email & Communication
            'gmail.com': 'Email',
            'outlook.com': 'Email',
            'yahoo.com/mail': 'Email',
            'zoom.us': 'Video Conferencing',
            'meet.google.com': 'Video Conferencing',
        }

        # Path-based categorization
        self.path_categories = {
            '/blog': 'Blog',
            '/docs': 'Documentation',
            '/documentation': 'Documentation',
            '/learn': 'Learning',
            '/courses': 'Courses',
            '/news': 'News',
            '/shop': 'Shopping',
            '/store': 'Shopping',
            '/product': 'Product',
            '/forum': 'Forum',
            '/community': 'Community',
            '/support': 'Support',
            '/help': 'Help',
            '/faq': 'FAQ',
            '/wiki': 'Wiki',
            '/about': 'About',
            '/contact': 'Contact',
        }

        # Common title keywords for categorization
        self.title_keywords = {
            'tutorial': 'Tutorials',
            'course': 'Courses',
            'learn': 'Learning',
            'guide': 'Guides',
            'howto': 'How-To',
            'documentation': 'Documentation',
            'reference': 'Reference',
            'cheatsheet': 'Cheat Sheets',
            'recipe': 'Recipes',
            'blog': 'Blogs',
            'news': 'News',
            'article': 'Articles',
            'review': 'Reviews',
            'shop': 'Shopping',
            'store': 'Shopping',
            'buy': 'Shopping',
            'product': 'Products',
            'tool': 'Tools',
            'service': 'Services',
            'api': 'APIs',
            'download': 'Downloads',
            'game': 'Games',
            'video': 'Videos',
            'music': 'Music',
            'audio': 'Audio',
            'podcast': 'Podcasts',
            'book': 'Books',
            'paper': 'Research Papers',
            'research': 'Research',
            'job': 'Jobs',
            'career': 'Careers',
            'portfolio': 'Portfolios',
            'project': 'Projects',
            'forum': 'Forums',
            'community': 'Communities',
            'dashboard': 'Dashboards',
            'analytics': 'Analytics',
            'report': 'Reports',
            'login': 'Logins',
            'account': 'Accounts',
            'profile': 'Profiles',
        }

        # Initialize category patterns for reuse
        self._init_domain_patterns()

    def _init_domain_patterns(self) -> None:
        """Initialize regex patterns for domain matching."""
        # Prepare domain patterns for efficient matching
        self.domain_patterns = {}

        for domain, category in self.domain_categories.items():
            # Handle domains with path components
            if '/' in domain:
                base_domain, path = domain.split('/', 1)
                pattern = re.compile(
                    rf'^(?:www\.)?{re.escape(base_domain)}/.*{re.escape(path)}', re.IGNORECASE)
            else:
                pattern = re.compile(
                    rf'^(?:www\.)?{re.escape(domain)}', re.IGNORECASE)

            self.domain_patterns[pattern] = category

    def categorize(self, bookmarks: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize bookmarks based on their URLs, titles, and metadata.

        Args:
            bookmarks: The parsed bookmark data

        Returns:
            Dictionary mapping category names to lists of bookmark references
        """
        # Extract all bookmarks into flat list
        all_bookmarks = []
        self._extract_all_bookmarks(bookmarks, all_bookmarks)

        # Apply individual categorization techniques
        domain_categories = self._categorize_by_domain(all_bookmarks)
        tld_categories = self._categorize_by_tld(all_bookmarks)
        path_categories = self._categorize_by_path(all_bookmarks)
        title_categories = self._categorize_by_title(all_bookmarks)
        folder_categories = self._categorize_by_folder(bookmarks)

        # Merge all category methods
        merged_categories = self._merge_categories([
            domain_categories,  # Highest priority
            title_categories,
            path_categories,
            folder_categories,
            tld_categories,     # Lowest priority
        ])

        # Apply ML-based clustering if enabled and sufficient data
        if self.use_ml and len(all_bookmarks) > 10:
            ml_categories = self._apply_ml_clustering(
                all_bookmarks, merged_categories)
            merged_categories = ml_categories

        # Filter out categories with too few items and sort
        filtered_categories = self._filter_and_sort_categories(
            merged_categories)

        return filtered_categories

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

    def _categorize_by_domain(self, bookmarks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize bookmarks based on their domain.

        Args:
            bookmarks: List of bookmark dictionaries

        Returns:
            Dictionary mapping domain-based categories to bookmark lists
        """
        categories = defaultdict(list)

        for bookmark in bookmarks:
            url = bookmark.get('url', '')
            if not url:
                continue

            domain = self._extract_domain(url)

            # Check for exact domain matches
            category = None

            # Try to match domain with patterns
            for pattern, cat in self.domain_patterns.items():
                if pattern.match(domain):
                    category = cat
                    break

            if category:
                categories[category].append(bookmark)

        return categories

    def _categorize_by_tld(self, bookmarks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize bookmarks based on TLD.

        Args:
            bookmarks: List of bookmark dictionaries

        Returns:
            Dictionary mapping TLD-based categories to bookmark lists
        """
        categories = defaultdict(list)

        for bookmark in bookmarks:
            url = bookmark.get('url', '')
            if not url:
                continue

            # Parse URL and extract TLD
            parsed_url = urlparse(url)
            domain_parts = parsed_url.netloc.split('.')

            if len(domain_parts) > 1:
                tld = domain_parts[-1].lower()

                # Check if this TLD has a predefined category
                if tld in self.tld_categories:
                    category = self.tld_categories[tld]
                    categories[category].append(bookmark)

        return categories

    def _categorize_by_path(self, bookmarks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize bookmarks based on URL path components.

        Args:
            bookmarks: List of bookmark dictionaries

        Returns:
            Dictionary mapping path-based categories to bookmark lists
        """
        categories = defaultdict(list)

        for bookmark in bookmarks:
            url = bookmark.get('url', '')
            if not url:
                continue

            # Parse URL and extract path
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()

            # Check for matches with known path patterns
            for path_pattern, category in self.path_categories.items():
                if path_pattern in path:
                    categories[category].append(bookmark)
                    break

        return categories

    def _categorize_by_title(self, bookmarks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize bookmarks based on title keywords.

        Args:
            bookmarks: List of bookmark dictionaries

        Returns:
            Dictionary mapping title-based categories to bookmark lists
        """
        categories = defaultdict(list)

        for bookmark in bookmarks:
            title = bookmark.get('title', '').lower()
            if not title:
                continue

            # Tokenize the title
            tokens = self._tokenize_and_clean(title)

            # Check for keyword matches
            for keyword, category in self.title_keywords.items():
                if keyword in tokens:
                    categories[category].append(bookmark)
                    break

        return categories

    def _categorize_by_folder(self, bookmark_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract categories based on existing folder structure.

        Args:
            bookmark_data: The bookmark data structure

        Returns:
            Dictionary mapping folder-based categories to bookmark lists
        """
        categories = defaultdict(list)

        # Extract all bookmarks with their folder paths
        all_bookmarks = []
        self._extract_all_bookmarks(bookmark_data, all_bookmarks)

        # Group by top-level folder
        for bookmark in all_bookmarks:
            folder_path = bookmark.get('folderPath', [])

            # Skip root folder (usually just "Bookmarks")
            if len(folder_path) > 1:
                # Use the first meaningful folder name as category
                category = folder_path[1]
                categories[category].append(bookmark)

        return categories

    def _merge_categories(self, category_sets: List[Dict[str, List[Dict[str, Any]]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Merge multiple categorization results with prioritization.

        Args:
            category_sets: List of category dictionaries in priority order

        Returns:
            Merged categories dictionary
        """
        # Track which bookmarks have been categorized
        categorized_bookmarks = set()
        merged = defaultdict(list)

        # Process each category set in priority order
        for categories in category_sets:
            for category, bookmarks in categories.items():
                for bookmark in bookmarks:
                    # Use the URL as a unique identifier
                    bookmark_id = bookmark.get('url', '')

                    # Only add if not already categorized
                    if bookmark_id and bookmark_id not in categorized_bookmarks:
                        merged[category].append(bookmark)
                        categorized_bookmarks.add(bookmark_id)

        return merged

    def _apply_ml_clustering(self,
                             bookmarks: List[Dict[str, Any]],
                             existing_categories: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Apply ML clustering to discover additional categories.

        Args:
            bookmarks: List of all bookmarks
            existing_categories: Already identified categories

        Returns:
            Enhanced category dictionary
        """
        # Get uncategorized bookmarks
        categorized_urls = set()
        for category, items in existing_categories.items():
            for item in items:
                categorized_urls.add(item.get('url', ''))

        uncategorized = [b for b in bookmarks if b.get(
            'url', '') not in categorized_urls]

        # If we have too few uncategorized items, just return existing categories
        if len(uncategorized) < 5:
            return existing_categories

        # Extract text features
        texts = []
        for bookmark in uncategorized:
            title = bookmark.get('title', '')
            url = bookmark.get('url', '')
            domain = self._extract_domain(url)

            # Combine title and domain for better clustering
            combined_text = f"{title} {domain}"
            texts.append(combined_text)

        # Vectorize text
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2
        )

        try:
            # Transform texts to feature vectors
            X = vectorizer.fit_transform(texts)

            # Apply DBSCAN clustering
            clustering = DBSCAN(eps=0.6, min_samples=2, metric='cosine')
            labels = clustering.fit_predict(X.toarray())

            # Add clusters to results
            result = existing_categories.copy()

            for idx, label in enumerate(labels):
                if label >= 0:  # Skip noise points (label -1)
                    bookmark = uncategorized[idx]
                    cluster_name = self._generate_cluster_name(
                        [uncategorized[i]
                            for i, l in enumerate(labels) if l == label],
                        vectorizer
                    )
                    result[cluster_name].append(bookmark)

            return result

        except Exception as e:
            self.logger.warning(f"ML clustering failed: {str(e)}")
            return existing_categories

    def _generate_cluster_name(self,
                               cluster_bookmarks: List[Dict[str, Any]],
                               vectorizer: TfidfVectorizer) -> str:
        """
        Generate a meaningful name for a cluster.

        Args:
            cluster_bookmarks: Bookmarks in the cluster
            vectorizer: TF-IDF vectorizer used

        Returns:
            Cluster name
        """
        # Extract common words from titles
        title_words = []
        domains = []

        for bookmark in cluster_bookmarks:
            title = bookmark.get('title', '')
            url = bookmark.get('url', '')
            domain = self._extract_domain(url)

            # Add title words
            title_words.extend(self._tokenize_and_clean(title))

            # Add domain
            if domain:
                domains.append(domain)

        # Count word frequencies
        word_counter = Counter(title_words)
        domain_counter = Counter(domains)

        # Get most common words and domain
        common_words = [word for word, count in word_counter.most_common(3)
                        if count > 1 and len(word) > 3]
        common_domain = domain_counter.most_common(
            1)[0][0] if domain_counter else ""

        # If we have common words, use them for the name
        if common_words:
            return " ".join(common_words).title()

        # Otherwise, use the most common domain
        if common_domain:
            return f"{common_domain.split('.')[0].title()} Resources"

        # Fallback name
        return "Related Resources"

    def _filter_and_sort_categories(self,
                                    categories: Dict[str, List[Dict[str, Any]]],
                                    min_items: int = 2) -> Dict[str, List[Dict[str, Any]]]:
        """
        Filter out small categories and sort results.

        Args:
            categories: Dictionary of categories
            min_items: Minimum number of items per category

        Returns:
            Filtered and sorted categories
        """
        # Filter out categories with too few items
        filtered = {cat: items for cat, items in categories.items()
                    if len(items) >= min_items}

        # Sort categories by number of items (descending)
        sorted_cats = dict(sorted(
            filtered.items(),
            key=lambda x: (len(x[1]), x[0]),
            reverse=True
        ))

        return sorted_cats

    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from a URL.

        Args:
            url: URL string

        Returns:
            Domain string
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]

            return domain
        except:
            return ""

    def _tokenize_and_clean(self, text: str) -> List[str]:
        """
        Tokenize text and remove stopwords.

        Args:
            text: Input text

        Returns:
            List of cleaned tokens
        """
        # Convert to lowercase
        text = text.lower()

        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)

        # Tokenize
        tokens = word_tokenize(text)

        # Remove stopwords and short words
        cleaned = [
            word for word in tokens
            if word not in self.stop_words and len(word) > 2
        ]

        return cleaned

    def extract_metadata(self, bookmarks: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract additional metadata from bookmarks.

        Args:
            bookmarks: Bookmark data structure

        Returns:
            Dictionary with metadata statistics
        """
        all_bookmarks = []
        self._extract_all_bookmarks(bookmarks, all_bookmarks)

        # Calculate domain statistics
        domains = {}
        for bookmark in all_bookmarks:
            url = bookmark.get('url', '')
            domain = self._extract_domain(url)

            if domain:
                if domain in domains:
                    domains[domain] += 1
                else:
                    domains[domain] = 1

        # Sort domains by frequency
        top_domains = sorted(
            domains.items(), key=lambda x: x[1], reverse=True)[:20]

        # Count bookmarks by date
        date_counts = defaultdict(int)
        for bookmark in all_bookmarks:
            date_added = bookmark.get('dateAdded', 0)
            if date_added:
                # Convert to date string (year-month)
                date_str = self._timestamp_to_ym(date_added)
                date_counts[date_str] += 1

        # Sort dates
        sorted_dates = sorted(date_counts.items())

        return {
            'totalBookmarks': len(all_bookmarks),
            'topDomains': dict(top_domains),
            'bookmarksByDate': dict(sorted_dates),
            'averagePathDepth': self._calculate_avg_path_depth(all_bookmarks)
        }

    def _timestamp_to_ym(self, timestamp: int) -> str:
        """
        Convert timestamp to year-month string.

        Args:
            timestamp: Unix timestamp (in milliseconds)

        Returns:
            Year-month string (YYYY-MM)
        """
        import datetime

        # Convert from milliseconds to seconds
        seconds = timestamp / 1000
        date = datetime.datetime.fromtimestamp(seconds)

        return date.strftime('%Y-%m')

    def _calculate_avg_path_depth(self, bookmarks: List[Dict[str, Any]]) -> float:
        """
        Calculate average folder path depth.

        Args:
            bookmarks: List of bookmarks

        Returns:
            Average path depth
        """
        depths = [len(bookmark.get('folderPath', []))
                  for bookmark in bookmarks]
        if not depths:
            return 0

        return sum(depths) / len(depths)
