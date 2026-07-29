import pydantic
from pathlib import Path

from websearchagent.agents import SimpleWebLinkParserSync
from websearchagent.utils.web import get_llm_friendly_html

from web_scraper_pipelines.pipelines.download_link_pipeline.pydantic_models import URLList
from web_scraper_pipelines.pipelines.download_link_pipeline._base_pipeline import BasePipeline, BaseAsyncPipeline

            

class DownloadLinkPipeline(BasePipeline):
    """
    Synchronous pipeline for extracting and processing links from web pages.
    """

    def __init__(self, config_path: str|Path, remove_tmp: bool=True, task_name: str="web_search_task"):
        """Initialize the synchronous download link pipeline.

        Args:
            config_path (str | Path): Path to the configuration file or directory.
            remove_tmp (bool): Flag indicating whether to remove the temporary database after execution. Defaults to True.
            task_name (str): Name of the task for the parsing agent. Defaults to "web_search_task".
        """

        super().__init__(config_path, remove_tmp)

        self.agent = SimpleWebLinkParserSync(
            llm_url=self._llm_url,
            model=self._model,
            api_key=self._api_key,
            task_name=task_name,
            parser_config_path=self.task_config_path,
            response_model=URLList
            )
        

    def pipeline_step(self, item: dict) -> dict:
        """Process a single item by fetching its HTML and parsing it for links.

        Args:
            item (dict): A dictionary containing the item data, including the "url" key.

        Returns:
            dict: A dictionary representation of the parsed Pydantic model containing the extracted links.
        """

        url = item["url"]

        html = get_llm_friendly_html(url)

        res: pydantic.BaseModel = self.agent.parse({"url": url, "html": html})

        return res.model_dump()
    

class DownloadLinkPipelineAsync(BaseAsyncPipeline, DownloadLinkPipeline):
    """
    Asynchronous pipeline for extracting and processing links from web pages.
    """

    def __init__(self, config_path: str|Path, remove_tmp: bool=True, task_name: str="web_search_task", num_workers: int=5):
        """Initialize the asynchronous download link pipeline.

        Args:
            config_path (str | Path): Path to the configuration file or directory.
            remove_tmp (bool): Flag indicating whether to remove the temporary database after execution. Defaults to True.
            task_name (str): Name of the task for the parsing agent. Defaults to "web_search_task".
            num_workers (int): The maximum number of concurrent worker tasks. Defaults to 5.
        """

        BaseAsyncPipeline.__init__(self, config_path, remove_tmp, num_workers)
        DownloadLinkPipeline.__init__(self, config_path, remove_tmp, task_name)
        

    def pipeline_step(self, item: dict) -> dict:
        """Process a single item by fetching its HTML and parsing it for links.

        Args:
            item (dict): A dictionary containing the item data, including the "url" key.

        Returns:
            dict: A dictionary representation of the parsed Pydantic model containing the extracted links.
        """

        url = item["url"]

        html = get_llm_friendly_html(url)

        res: pydantic.BaseModel = self.agent.parse({"url": url, "html": html})

        return res.model_dump()
    







        
