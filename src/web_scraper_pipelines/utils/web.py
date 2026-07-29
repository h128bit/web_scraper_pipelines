import asyncio
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

