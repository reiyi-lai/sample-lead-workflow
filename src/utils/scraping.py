# utils/scraping.py
# Web scraping utilities with Firecrawl and fallback logic

import os
import requests
from urllib.parse import urlparse
from typing import Optional, Tuple
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

# Load environment variables from .env file
load_dotenv()

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import KNOWN_JS_DOMAINS


def get_firecrawl_client() -> FirecrawlApp:
    """Get Firecrawl client with API key from environment."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY environment variable not set")
    return FirecrawlApp(api_key=api_key)


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    # Remove www. prefix if present
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def is_known_js_domain(url: str) -> bool:
    """Check if URL is from a known JS-rendered domain."""
    domain = extract_domain(url)
    return any(js_domain in domain for js_domain in KNOWN_JS_DOMAINS)


def is_direct_file(url: str) -> bool:
    """Check if URL points to a direct file (PDF, XLSX, etc.)."""
    file_extensions = [".pdf", ".xlsx", ".xls", ".csv", ".doc", ".docx"]
    return any(url.lower().endswith(ext) for ext in file_extensions)


def is_likely_static(url: str) -> bool:
    """Check if URL is likely to be static (no JS rendering needed)."""
    domain = extract_domain(url)
    # Most .org sites are static
    if domain.endswith(".org"):
        return True
    # Direct file links
    if is_direct_file(url):
        return True
    return False


def simple_fetch(url: str, timeout: int = 30) -> Tuple[bool, str]:
    """
    Simple HTTP fetch for static pages.

    Returns:
        Tuple of (success: bool, content: str)
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Check if we got meaningful content
        content = response.text
        if len(content) > 500:
            return True, content
        else:
            return False, "Content too short"
    except requests.RequestException as e:
        return False, str(e)


def firecrawl_scrape(url: str, timeout: int = 30000) -> Tuple[bool, str, dict]:
    """
    Scrape URL using Firecrawl.

    Returns:
        Tuple of (success: bool, markdown_content: str, metadata: dict)
    """
    try:
        client = get_firecrawl_client()
        result = client.scrape_url(
            url,
            params={
                "formats": ["markdown"],
                "timeout": timeout,
            }
        )

        if result and "markdown" in result:
            metadata = result.get("metadata", {})
            return True, result["markdown"], metadata
        else:
            return False, "No markdown content returned", {}

    except Exception as e:
        return False, str(e), {}


def scrape_url(url: str) -> dict:
    """
    Scrape a URL using the appropriate method based on domain.

    Decision logic:
    1. Known JS-rendered domains -> Firecrawl immediately
    2. Known static domains -> Simple fetch
    3. Unknown domains -> Try simple fetch, fallback to Firecrawl

    Returns:
        dict with keys: success, url, tool_used, content, metadata, error
    """
    result = {
        "url": url,
        "success": False,
        "tool_used": None,
        "content": "",
        "metadata": {},
        "error": None,
    }

    domain = extract_domain(url)

    # Rule 1: Known JS-rendered domains -> Firecrawl immediately
    if is_known_js_domain(url):
        result["tool_used"] = "firecrawl"
        success, content, metadata = firecrawl_scrape(url)
        result["success"] = success
        result["content"] = content
        result["metadata"] = metadata
        if not success:
            result["error"] = content
        return result

    # Rule 2: Known static domains -> Simple fetch
    if is_likely_static(url):
        result["tool_used"] = "simple_fetch"
        success, content = simple_fetch(url)
        result["success"] = success
        result["content"] = content
        if not success:
            result["error"] = content
        return result

    # Rule 3: Unknown domains -> Try simple fetch, fallback to Firecrawl
    result["tool_used"] = "simple_fetch"
    success, content = simple_fetch(url)

    if success and len(content) > 500 and has_exhibitor_keywords(content):
        result["success"] = True
        result["content"] = content
        return result

    # Fallback to Firecrawl
    result["tool_used"] = "firecrawl"
    success, content, metadata = firecrawl_scrape(url)
    result["success"] = success
    result["content"] = content
    result["metadata"] = metadata
    if not success:
        result["error"] = content

    return result


def has_exhibitor_keywords(content: str) -> bool:
    """Check if content contains exhibitor-related keywords."""
    keywords = [
        "exhibitor",
        "booth",
        "exhibit",
        "company",
        "vendor",
        "sponsor",
        "floor plan",
        "hall",
    ]
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in keywords)


def scrape_exhibitor_list(url: str, event_name: str = "") -> dict:
    """
    Scrape an exhibitor list page.

    Returns:
        dict with scraping results and metadata about the scrape
    """
    result = scrape_url(url)
    result["event_name"] = event_name
    result["scrape_type"] = "exhibitor_list"

    # Add some basic stats about the content
    if result["success"] and result["content"]:
        content = result["content"]
        result["content_length"] = len(content)
        result["has_exhibitor_keywords"] = has_exhibitor_keywords(content)

        # Count potential company mentions (rough heuristic)
        # Look for patterns that might indicate company listings
        lines = content.split("\n")
        result["line_count"] = len(lines)

    return result
