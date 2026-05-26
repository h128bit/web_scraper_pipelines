import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
import pydantic

from websearchagent.agents import SimpleWebLinkParserSync
from websearchagent.utils.web import get_llm_friendly_html

from linguistic_pipelines.pipelines.download_link_pipeline.pydantic_models import URLList
from linguistic_pipelines.pipelines._base_pipeline import BasePipeline, BaseAsyncPipeline

            

class DownloadLinkPipeline(BasePipeline):
    def __init__(self, verbose: bool=False, remove_tmp: bool=True, task_name: str="web_search_task"):
        super().__init__(verbose, remove_tmp)

        self.agent = SimpleWebLinkParserSync(
            llm_url=self._llm_url,
            model=self._model,
            api_key=self._api_key,
            task_name=task_name,
            parser_config_path=self.task_config_path,
            response_model=URLList
            )
        

    def pipeline_step(self, item: dict) -> dict:
        url = item["url"]

        html = get_llm_friendly_html(url)

        res: pydantic.BaseModel = self.agent.parse({"url": url, "html": html})

        return res.model_dump()
    

class DownloadLinkPipelineAsync(BaseAsyncPipeline, DownloadLinkPipeline):
    def __init__(self, verbose: bool=False, remove_tmp: bool=True, task_name: str="web_search_task", num_workers: int=5):
        BaseAsyncPipeline.__init__(self, verbose, remove_tmp, num_workers)
        DownloadLinkPipeline.__init__(self, verbose, remove_tmp, task_name)
        

    def pipeline_step(self, item: dict) -> dict:
        url = item["url"]

        html = get_llm_friendly_html(url)

        res: pydantic.BaseModel = self.agent.parse({"url": url, "html": html})

        return res.model_dump()
    







        
