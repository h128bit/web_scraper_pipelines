import os
import time
import random
import logging
import asyncio
import threading
from pathlib import Path

from web_scraper_pipelines.pipelines._abstract_pipelines import _BaseAbstractPipeline
from web_scraper_pipelines.pipelines.download_link_pipeline.orm import URLFilesTableOrm



class BasePipeline(_BaseAbstractPipeline):
    """
    Base class for download link pipelines
    """

    def __init__(self, config_path: str|Path, remove_tmp: bool=True) -> None:
        """Initialize the pipeline with configuration and database settings.

        Args:
            config_path (str | Path): Path to the configuration file or directory.
            remove_tmp (bool): Flag indicating whether to remove the temporary database after execution. Defaults to True.
        """
        super().__init__(config_path)

        tmp_db_path = self._config.get("LINGUISTIC_TEMP_DB_PATH", None)

        db_params = self._get_db_params()
        
        self.orm = URLFilesTableOrm(temp_db_path=tmp_db_path, db_path_or_url=self.db_path_or_url, **db_params)

        self.remove_tmp = remove_tmp


    def _inner_item_process(self, item: dict):
        """Process a single item through the pipeline steps and update the database.

        Args:
            item (dict): The item dictionary containing data to be processed.
        """

        self._logger.info(f"Perform {item}")

        new_links = self.pipeline_step(item)
            
        try:
            new_links = new_links["items"]
            self._logger.info(f"Number found new lines: {len(new_links)}")
            self.orm.add_lines_to_temp(new_links)
        except:
            self._logger.error("Append in DB error.\nITEMS: {new_links}")

        self.orm.push_direct_link_to_db()


    def _input_urls_to_tmp_db(self, link_list: list[str]):
        """Format and insert a list of URL strings into the temporary database.

        Args:
            link_list (list[str]): A list of URL strings to be added to the temporary database.
        """

        links_for_parse = [{"name": "link", "url": url, "ttype": "link"} for url in link_list]
        self.orm.add_lines_to_temp(links_for_parse)


    def run_pipeline(self, link_list: list[str]) -> None:
        """Execute the synchronous pipeline for a given list of URLs.

        Args:
            link_list (list[str]): A list of URL strings to process.
        """
        
        # TODO: add continue execution after error down
        self._logger.info(f"Pipeline start. Number input urls: {len(link_list)}")

        self._input_urls_to_tmp_db(link_list)

        while (item := self.orm.get_link_line_from_tmp()):
            start = time.time()
            self._inner_item_process(item)
            self._logger.info(f"Item processed. Diration {time.time() - start} sec.")

        if self.remove_tmp:
            self.orm.remove_tmp_db()
            self._logger.info("TEMP db was removed")


    def pipeline_step(self, item: dict) -> dict:
        """Define the specific processing step for an item.

        Args:
            item (dict): The item dictionary to process.

        Returns:
            dict: A dictionary containing the processed items, typically under an "items" key.

        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """
        raise NotImplementedError
    


class BaseAsyncPipeline(BasePipeline):
    """
    Extension of the BasePipeline class for asynchronous   
    """

    def __init__(self, config_path: str|Path, remove_tmp: bool=True, nums_workers: int=5):
        """Initialize the asynchronous pipeline with concurrency settings.

        Args:
            config_path (str | Path): Path to the configuration file or directory.
            remove_tmp (bool): Flag indicating whether to remove the temporary database after execution. Defaults to True.
            nums_workers (int): The maximum number of concurrent worker tasks. Defaults to 5.
        """
        super().__init__(config_path, remove_tmp)

        self._semaphore = asyncio.Semaphore(nums_workers)


    async def _async_inner_item_process(self, item):
        """Process a single item asynchronously in a separate thread.

        Args:
            item (dict): The item dictionary containing data to be processed.
        """
        # async with self._semaphore:
        thread_name = threading.current_thread().name + str(random.randint(0, 5000))
        self._logger.info(f"Start thread: thread name: {thread_name}")
        start = time.time()
        await asyncio.to_thread(self._inner_item_process, item)
        self._logger.info(f"Thread end: thread name: {thread_name}. Duration: {time.time() - start} sec.")


    async def _async_pipeline(self):
        """Main asynchronous pipeline execution loop.

        Continuously fetches items from the temporary database and processes them
        concurrently until the database is empty and all active tasks are completed.
        """

        active_tasks = set()
        async with self._semaphore:
            while True:
                item = await asyncio.to_thread(self.orm.get_link_line_from_tmp) 

                if item:
                    task = asyncio.create_task(self._async_inner_item_process(item))
                    active_tasks.add(task)
                    task.add_done_callback(active_tasks.discard)
                else: 
                    if active_tasks:
                        # does not allow stop while loop while exists at least one active task
                        await asyncio.wait(active_tasks, return_when=asyncio.FIRST_COMPLETED)
                    else: 
                        break
                await asyncio.sleep(0)
        

    def run_pipeline(self, link_list: list[str]) -> None:
        """Execute the asynchronous pipeline for a given list of URLs.

        Args:
            link_list (list[str]): A list of URL strings to process.
        """
        self._logger.info(f"Pipeline start. Number input urls: {len(link_list)}")

        self._input_urls_to_tmp_db(link_list)

        asyncio.run(self._async_pipeline())
        



