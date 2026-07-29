from typing import Any
from pathlib import Path
import logging
from collections import OrderedDict

import toml



class _BaseAbstractPipeline:
    """
    Base abstract class for defining web scraper pipeline structures and configurations.
    """

    def __init__(self, config_path: str|Path):
        """
        Initialize the pipeline with configuration loaded from a TOML file.

        Args:
            config_path (str | Path): Path to the TOML configuration file.

        Raises:
            KeyError: If `WEB_SCRAPER_LLM_URL` or `WEB_SCRAPER_MODEL_NAME` is missing in the configuration.
        """

        self._config: OrderedDict = toml.load(config_path, _dict=OrderedDict)

        self.task_config_path = self._config.get("WEB_SCRAPER_TASK_CONFIG_PATH", None)

        self._llm_url = self._config.get("WEB_SCRAPER_LLM_URL", None)
        self._model = self._config.get("WEB_SCRAPER_MODEL_NAME", None)
        if not self._llm_url:
            raise KeyError(f"Not found `WEB_SCRAPER_LLM_URL` in enviroment variables")
        if not self._model:
            raise KeyError(f"Not found `WEB_SCRAPER_MODEL_NAME` in enviroment variables")
        self._api_key = self._config.get("WEB_SCRAPER_LLM_API_KEY", None)

        self.db_path_or_url = self._config.get("WEB_SCRAPER_DB_PATH_OR_URL", None)

        self._logger = logging.getLogger(self.__class__.__name__)


    def _get_db_params(self) -> dict:
        """
        Extract and format database connection parameters from the configuration.

        Returns:
            dict: A dictionary containing database connection parameters (name, user, port, password).
        """
        db_params = {
            "db_name": self._config.get("WEB_SCRAPER_DB_NAME", None), 
            "db_user": self._config.get("WEB_SCRAPER_DB_USER", None),
            "db_port": int(x) if (x:= self._config.get("WEB_SCRAPER_DB_PORT", None)) else x,
            "db_password": self._config.get("WEB_SCRAPER_DB_PASSWORD", None)
        }  

        return db_params

    def run_pipeline(self, *args, **kwargs) -> Any:
        """
        Execute the main pipeline logic.

        Args:
            *args (Any): Variable length argument list.
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Any: The result of the pipeline execution.

        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """

        raise NotImplementedError

    
    def pipeline_step(self, *args, **kwargs) -> Any:
        """
        Execute a single step of the pipeline logic.

        Args:
            *args (Any): Variable length argument list.
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Any: The result of the pipeline step.

        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """
        raise NotImplementedError