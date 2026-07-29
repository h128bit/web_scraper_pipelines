import logging
from typing import Any
import pydantic
from pathlib import Path 

from websearchagent.agents import SimpleWebLinkParserSync

from web_scraper_pipelines.utils.web import crawl
from web_scraper_pipelines.pipelines._abstract_pipelines import _BaseAbstractPipeline
from web_scraper_pipelines.pipelines.scrape_journal_pipeline.orm import ViewedURLTableOrm
from web_scraper_pipelines.pipelines.scrape_journal_pipeline.pydantic_models import URLList



class ScrapeJournalPipelineSync(_BaseAbstractPipeline):
    """
    Synchronous pipeline for scraping journal websites and extracting article links.
    """
    def __init__(self, config_path: str|Path, task_name: str="web_scrape_journal_task", stop_if_find_exist: bool=True):
        """
        Initialize the synchronous journal scraping pipeline.

        Args:
            config_path (str | Path): Path to the configuration file or directory.
            task_name (str): Name of the task for the parsing agent. Defaults to "web_scrape_journal_task".
            stop_if_find_exist (bool): Flag indicating whether to stop the pipeline if an already viewed URL is encountered. Defaults to True.
        """

        super().__init__(config_path)

        self._logger = logging.getLogger(self.__class__.__name__)
        
        db_params = self._get_db_params() 

        self.orm = ViewedURLTableOrm(db_path_or_url=self.db_path_or_url, **db_params)

        self.agent = SimpleWebLinkParserSync(
            llm_url=self._llm_url,
            model=self._model,
            api_key=self._api_key,
            task_name=task_name,
            parser_config_path=self.task_config_path,
            response_model=URLList
            )
        
        self.stop_if_find_exist = stop_if_find_exist
        
        
    def run_pipeline(self, url: str) -> list[str]:
        """
        Execute the scraping pipeline starting from a given URL.

        Args:
            url (str): The starting URL for scraping.

        Returns:
            list[str]: A list of newly discovered article URLs.
        """

        url_set: set[str] = set()
        url_set.add(url) 
        viewed_urls_set: set[str] = set()
        result: list[str] = []

        self._logger.info("Start Scrape Journal pipeline")

        # init run, update `url_set`. Need for correct process first page on sites with pagination 
        self._logger.debug("init pipeline step") 
        _, _, url_set, viewed_urls_set = self.pipeline_step(url_set, viewed_urls_set, False)

        while url_set:
            exists_flag, step_result, url_set, viewed_urls_set = self.pipeline_step(url_set, viewed_urls_set)
            result.extend(step_result)

            if self.stop_if_find_exist and exists_flag:
                break
        
        return result


    def pipeline_step(self, url_set: set, viewed_urls_set: set, _check_on_existing: bool=True) -> tuple[bool, list[str], set, set]:
        """
        Process a single step of the scraping pipeline.

        Args:
            url_set (set): A set of URLs to be processed in the current step.
            viewed_urls_set (set): A set of URLs that have already been processed.
            _check_on_existing (bool): Flag indicating whether to check for already processed URLs in the database. Defaults to True.

        Returns:
            tuple[bool, list[str], set, set]: A tuple containing:
                - exists_flag (bool): True if an already existing URL was found, False otherwise.
                - step_result (list[str]): A list of newly discovered article URLs added to the database.
                - url_set (set): The updated set of URLs to process.
                - viewed_urls_set (set): The updated set of viewed URLs.
        """

        step_result = []
        exists_flag = False 

        url = sorted(list(url_set)).pop(0)

        self._logger.debug(f"Number urls for process: {len(url_set)}")
        self._logger.debug(f"Process url: {url}")

        new_urls_list = self.agent_step(url)["items"]
        viewed_urls_set.add(url)

        surls = "\n\t".join(url_set)
        self._logger.debug(f"URLS: \n{surls}\n",)
        self._logger.debug(f"Find new urls: {len(new_urls_list)}")


        for item in new_urls_list:
            print(item["ttype"])
            if item["ttype"].upper() == "PAG":
                url_set.add(item["url"])
                continue
            
            if _check_on_existing:
                item.pop("ttype")

                if not self.orm.check_existing(item):
                    self.orm.add_line(item)
                    step_result.append(item["url"])
                    self._logger.info("Article card url add to db")
                else:
                    exists_flag = True 
                    self._logger.debug("Find repeat -----------")

        url_set = url_set - viewed_urls_set

        return exists_flag, step_result, url_set, viewed_urls_set


    def agent_step(self, url) -> dict:
        """
        Fetch and parse a single URL using the configured agent.

        Args:
            url (str): The URL to fetch and parse.

        Returns:
            dict: A dictionary representation of the parsed Pydantic model containing the extracted links.
        """
        
        markdown_page = crawl(url)
        res: pydantic.BaseModel = self.agent.parse({"url": url, "markdown": markdown_page})
        return res.model_dump()