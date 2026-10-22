import os
import asyncio
import requests
from typing import Collection
from urllib.parse import urlparse, parse_qs

from crawl4ai import AsyncWebCrawler



async def async_crawl(url: str, param: dict|None=None, verbose: bool=False):
    """
    Asynchronously crawl a given URL and return its content in markdown format.

    Args:
        url (str): The URL of the web page to crawl.
        param (dict | None): Optional parameters to pass to the crawler. Defaults to {"word_count_threshold": 300}.
        verbose (bool): Flag to enable verbose logging for the crawler. Defaults to False.

    Returns:
        str: The crawled web page content formatted as markdown.
    """
    if param is None:
        param = {"word_count_threshold": 300}

    async with AsyncWebCrawler(verbose=verbose) as crawler:
        result = await crawler.arun(url=url, **param)
    return result.markdown



def crawl(url: str, param: dict|None=None, verbose: bool=False):
    """
    Synchronously crawl a given URL and return its content in markdown format.

    This function acts as a synchronous wrapper for the asynchronous crawling process.

    Args:
        url (str): The URL of the web page to crawl.
        param (dict | None): Optional parameters to pass to the crawler. Defaults to {"word_count_threshold": 300}.
        verbose (bool): Flag to enable verbose logging for the crawler. Defaults to False.

    Returns:
        str: The crawled web page content formatted as markdown.
    """
    res = asyncio.run(async_crawl(url, param, verbose))
    return res



def is_file_by_url(url: str, file_extensions: Collection[str]) -> bool:
    HTML_EXTENSIONS = {'.html', '.htm', '.php', '.asp', '.aspx', '.jsp'}

    req_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }

    response_headers = None
    try:
        response = requests.head(url, headers=req_headers, allow_redirects=True, timeout=5)

        if response.status_code in (403, 405, 501):
            with requests.get(url, headers=req_headers, allow_redirects=True, stream=True, timeout=5) as response:
                response_headers = response.headers
        else:
            response_headers = response.headers
            
    except requests.RequestException:
        pass 

    if response_headers:
        content_type = response_headers.get('Content-Type', '').lower()
        content_disposition = response_headers.get('Content-Disposition', '').lower()

        if 'attachment' in content_disposition or 'filename=' in content_disposition:
            return True

        if 'text/html' in content_type or 'application/xhtml+xml' in content_type:
            return False
            
        if content_type and 'text/html' not in content_type:
            return True

    parsed_url = urlparse(url)
    _, ext = os.path.splitext(parsed_url.path)
    ext = ext.lower()
    
    if ext in file_extensions:
        return True
    if ext in HTML_EXTENSIONS:
        return False
        
    query_params = parse_qs(parsed_url.query)
    for key in ['file', 'filename', 'name', 'doc']:
        if key in query_params:
            val = query_params[key][0].lower()
            if any(val.endswith(e) for e in file_extensions):
                return True

    return False

