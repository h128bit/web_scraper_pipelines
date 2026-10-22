from pathlib import Path
from typing import Any, Collection

import pydantic

from websearchagent.agents import SimpleWebLinkParserSync

from web_scraper_pipelines.utils.web import crawl, is_file_by_url
from web_scraper_pipelines.utils.structures import LinkedNode
from web_scraper_pipelines.pipelines._abstract_pipelines import _BaseAbstractPipeline
from web_scraper_pipelines.pipelines.find_objects_pipeline.pydantic_models import URLList



class FindObjectsPipeline(_BaseAbstractPipeline):
    def __init__(self, 
                 config_path: str | Path, 
                 task_name: str="web_scrape_journal_task",
                 max_depth: int=5, 
                 file_extensions: Collection[str]=(".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg")):
        super().__init__(config_path)

        self.agent = SimpleWebLinkParserSync(
            llm_url=self._llm_url,
            model=self._model,
            api_key=self._api_key,
            task_name=task_name,
            parser_config_path=self.task_config_path,
            response_model=URLList
            )

        self.max_depth = max_depth
        self.file_extensions = file_extensions


        self._viewed_urls = set()

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


    def pipeline_step(self, node: LinkedNode) -> tuple[list[LinkedNode], list[str]]:
        url = node.item

        new_urls: list[dict] = self.agent_step(url)["items"]

        file_urls = []
        new_nodes = []
        pag_nodes = []

        for item in new_urls:
            url = item["url"]
            ttype = item["ttype"].upper()

            if url in self._viewed_urls:
                continue

            # validate what llm correct classysfi given url as link to file
            if is_file_by_url(url, self.file_extensions):
                file_urls.append(url)
            else:
                # if url is pagination link then not increast depth for node
                if ttype == "PAG":
                    depth = node.depth
                    max_depth = node.max_depth
                    pag_node = LinkedNode(url, depth, max_depth)
                    pag_nodes.append(pag_node)
                else:
                    new_nodes.append(url)

            self._viewed_urls.add(url)

        new_nodes = pag_nodes + node.get_children(new_nodes)

        return new_nodes, file_urls


    def run_pipeline(self, start_url: str) -> Any:
        queue = [LinkedNode(start_url, 0, self.max_depth)]
        file_urls_list = []

        self._viewed_urls.clear()
        while True:
            if len(queue) == 0:
                break
            node = queue.pop(0)
            new_nodes, file_urls = self.pipeline_step(node)
            queue.extend(new_nodes)
            file_urls_list.extend(file_urls)

        return file_urls_list
