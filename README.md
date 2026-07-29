# Web parsers pipelines

## LLM-Based pipelines for process web pages.

### What this code does
This code implements a pipeline for automatically crawling web pages and extracting structured data (such as article links and pagination) using a Large Language Model (LLM).

Key features:
- Fetches web pages and converts them into an LLM-friendly format (Markdown).
- Parses pages via an LLM agent to classify links (e.g., `link` for article cards, `PAG` for pagination).
- Manages a task queue using a temporary database (producer-consumer pattern).
- Saves discovered unique links to the main database.
- Tracks already viewed URLs to prevent infinite loops and duplication.
- Supports both synchronous and asynchronous (multi-threaded) execution modes with a configurable worker limit.

### Created files (Databases)
By default, the code creates the following files in the working directory (paths and DB types can be modified via configuration):

1. `tmp.db` — A temporary SQLite database. Used as an operational queue to store URLs awaiting processing. It is automatically deleted after the pipeline finishes successfully (if the `remove_tmp=True` parameter is set).
2. `download_link.db` — The main database (SQLite or PostgreSQL). Stores the final extracted links, their types, and text annotations (`DownloadLinkTable`).
3. `viewed_pages.db` — A database for tracking viewed pages (`ViewedPagesTable`). Used to filter out already processed URLs when crawling paginated sites.

*Note: The code requires an external `.toml` configuration file (containing LLM and DB parameters) to run, but it does not create this file itself; it only reads it.*

### Examples

```python
import os 
import time
from dotenv import load_dotenv

from web_scraper_pipelines.pipelines import DownloadLinkPipelineAsync, ScrapeJournalPipelineSync


try:  # [Optional]
    os.remove(r"viewed_pages.db")
    print("DB file was removed")
except:
    print("DB file was alredy removed")
time.sleep(2)


config_path = r"example_configs\example_config_scrape_pipeline.env"

pipline = ScrapeJournalPipelineSync(config_path=config_path, task_name="web_scrape_journal_task")
links = ["https://link.springer.com/journal/13205/articles?filter-by-volume=all-volumes&filterOpenAccess=true&sortBy=newestFirst",
         "https://link.springer.com/search?query=&advancedSearch=true&content-type=Article&openAccess=true&dateFrom=&dateTo=&journal=3+biotech&sortBy=newestFirst"]

result = pipline.run_pipeline(links[1])
```

## Main Pipeline Classes

### 1. **BasePipeline** (Base Synchronous Pipeline)
Base class for all synchronous pipelines. Implements the common logic for processing URLs via a temporary database.

**Key methods:**
- `run_pipeline(link_list)` — launches the pipeline for a list of URLs
- `_inner_item_process(item)` — processes a single item via `pipeline_step`
- `pipeline_step(item)` — abstract method that must be overridden in subclasses

**Features:**
- Uses a temporary database as a task queue
- Processes URLs sequentially from the queue
- Automatically removes the temporary database after completion

---

### 2. **BaseAsyncPipeline** (Base Asynchronous Pipeline)
Extension of `BasePipeline` for asynchronous processing with multi-threading support.

**Key methods:**
- `_async_pipeline()` — main asynchronous processing loop
- `_async_inner_item_process(item)` — asynchronous processing of a single item via `asyncio.to_thread`

**Features:**
- Uses `asyncio.Semaphore` to limit the number of concurrent workers
- Parallel processing of multiple URLs
- Continues running while there are active tasks

---

### 3. **DownloadLinkPipeline** (Link Extraction Pipeline)
Concrete implementation for parsing web pages and extracting links using an LLM.

**Key methods:**
- `pipeline_step(item)` — loads page HTML, sends it to the LLM agent, receives a structured list of links

**Features:**
- Uses `SimpleWebLinkParserSync` for parsing
- Converts HTML to an LLM-friendly format via `get_llm_friendly_html`
- Returns a Pydantic model `URLList` with classified links

---

### 4. **DownloadLinkPipelineAsync** (Asynchronous Link Extraction Pipeline)
Asynchronous version of `DownloadLinkPipeline`, inheriting from `BaseAsyncPipeline`.

**Features:**
- Combines asynchronous processing from `BaseAsyncPipeline` with parsing logic from `DownloadLinkPipeline`
- Supports configurable number of workers (`num_workers`)
- Parallel processing of multiple pages

---

### 5. **ScrapeJournalPipelineSync** (Journal Crawling Pipeline)
Specialized pipeline for crawling sites with pagination (journals, blogs, catalogs).

**Key methods:**
- `run_pipeline(url)` — starts crawling from an initial URL, returns a list of discovered article links
- `pipeline_step(url_set, viewed_urls_set)` — processes one crawling step, distinguishes between article links and pagination
- `agent_step(url)` — loads and parses a single page

**Features:**
- Automatically follows pagination (`PAG`)
- Tracks already viewed URLs via `ViewedPagesTable`
- Can stop when an already viewed page is detected (`stop_if_find_exist`)
- Returns only unique article links

---

### Common Architecture

All pipelines follow the **producer-consumer** pattern via a temporary database:
1. Input URLs are placed in the queue (`TempUrlTable`)
2. Workers fetch URLs one by one
3. Each URL is processed via the LLM agent
4. Newly discovered URLs (especially pagination) are returned to the queue
5. Final results are saved to the main database