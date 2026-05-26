import os
import time
import random
import logging
import asyncio
import threading
from pathlib import Path
from datetime import datetime

from linguistic_pipelines.pipelines.download_link_pipeline.orm import URLFilesTableOrm



class BasePipeline:
    def __init__(self, verbose: bool=False, remove_tmp: bool=True) -> None:
        self.agent_config_path = os.getenv("LINGUISTIC_AGENT_CONFIG_PATH", None)
        self.task_config_path = os.getenv("LINGUISTIC_TASK_CONFIG_PATH", None)
        # path_to_log = os.getenv("WEBSEARCH_LOG_PATH", None)

        self._llm_url = os.getenv("LINGUISTIC_LLM_URL", None)
        self._model = os.getenv("LINGUISTIC_MODEL_NAME", None)
        if not self._llm_url:
            raise KeyError(f"Not found `LINGUISTIC_LLM_URL` in enviroment variables")
        if not self._model:
            raise KeyError(f"Not found `LINGUISTIC_MODEL_NAME` in enviroment variables")
        self._api_key = os.getenv("LINGUISTIC_LLM_API_KEY", None)

        tmp_db_path = os.getenv("LINGUISTIC_TEMP_DB_PATH", None)
        db_path_or_url = os.getenv("LINGUISTIC_DB_PATH_OR_URL", None)

        db_params = {
            "db_name": os.getenv("LINGUISTIC_DB_NAME", None), 
            "db_user": os.getenv("LINGUISTIC_DB_USER", None),
            "db_port": int(x) if (x:= os.getenv("LINGUISTIC_DB_PORT", None)) else x,
            "db_password": os.getenv("LINGUISTIC_DB_PASSWORD", None)
        }  

        self._logger = logging.getLogger(self.__class__.__name__)
        
        self.orm = URLFilesTableOrm(temp_db_path=tmp_db_path, db_path_or_url=db_path_or_url, **db_params)

        self.remove_tmp = remove_tmp


    def _inner_item_process(self, item: dict):
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
        links_for_parse = [{"name": "link", "url": url, "ttype": "link"} for url in link_list]
        self.orm.add_lines_to_temp(links_for_parse)


    def run_pipeline(self, link_list: list[str]) -> None:
        
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
        raise NotImplementedError
    


class BaseAsyncPipeline(BasePipeline):
    def __init__(self, verbose: bool=False, remove_tmp: bool=True, nums_workers: int=5):
        super().__init__(verbose, remove_tmp)

        self._semaphore = asyncio.Semaphore(nums_workers)


    async def _async_inner_item_process(self, item):
        # async with self._semaphore:
        thread_name = threading.current_thread().name + str(random.randint(0, 5000))
        self._logger.info(f"Start thread: thread name: {thread_name}")
        start = time.time()
        await asyncio.to_thread(self._inner_item_process, item)
        self._logger.info(f"Thread end: thread name: {thread_name}. Duration: {time.time() - start} sec.")


    async def _async_pipeline(self):
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
                        await asyncio.wait(active_tasks, return_when=asyncio.FIRST_COMPLETED)
                    else: 
                        break
                await asyncio.sleep(0)
        

    def run_pipeline(self, link_list: list[str]) -> None:
        self._logger.info(f"Pipeline start. Number input urls: {len(link_list)}")

        self._input_urls_to_tmp_db(link_list)

        asyncio.run(self._async_pipeline())
        



