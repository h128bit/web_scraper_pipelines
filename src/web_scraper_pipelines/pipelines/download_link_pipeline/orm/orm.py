import os
import logging

import peewee

from web_scraper_pipelines.utils.db import init_db
from web_scraper_pipelines.pipelines.download_link_pipeline.orm.models import TempUrlTable, DownloadLinkTable



class URLFilesTableOrm:
    """
    ORM manager for handling temporary and main database operations for URLs.
    """
    def __init__(self, 
                 temp_db_path: str|None=None, 
                 db_path_or_url: str|None=None,
                 db_name: str|None=None,
                 db_user: str|None=None,
                 db_port: int|None=None,
                 db_password: str|None=None):
        """
        Initialize the database connections for temporary and main storage.

        Args:
            temp_db_path (str | None): Path to the temporary database file. Defaults to "tmp.db".
            db_path_or_url (str | None): Path or connection URL to the main database. Defaults to "download_link.db".
            db_name (str | None): Name of the main database.
            db_user (str | None): Username for the main database connection.
            db_port (int | None): Port number for the main database connection.
            db_password (str | None): Password for the main database connection.
        """

        self._logger = logging.getLogger(self.__class__.__name__)

        temp_db_path = temp_db_path if temp_db_path else "tmp.db"
        db_path_or_url = db_path_or_url if db_path_or_url else "download_link.db"

        self.tem_db = init_db(temp_db_path, TempUrlTable)
        db_params = {"db_name": db_name, "db_user": db_user, "db_port": db_port, "db_password": db_password}
        self.db = init_db(db_path_or_url, DownloadLinkTable, **db_params)

        self._logger.info("Temp db created successful")

        self.temp_db_path = temp_db_path


    def _add_lines(self, model, db, lines: list[dict]) -> None:
        """
        Insert multiple records into the specified database model.

        Args:
            model (Model): The Peewee Model class to insert data into.
            db (Database): The Peewee Database instance to use for the operation.
            lines (list[dict]): A list of dictionaries representing the records to insert.
        """

        self._logger.info("Starting pushing items into temp db")
        for line in lines:
            with db:
                with db.atomic():
                    try:
                        model.insert_many([line]).execute()
                    except peewee.IntegrityError as e:
                        self._logger.debug(f"Line {line} alredy in temp db")
                        pass
        self._logger.info("The items successful pushed into temp db")


    def add_lines_to_temp(self, lines: list[dict]) -> None:
        """
        Add a list of records to the temporary database.

        Args:
            lines (list[dict]): A list of dictionaries representing the records to insert.
        """

        self._add_lines(TempUrlTable, self.tem_db, lines)


    def add_lines_to_db(self, lines: list[dict]) -> None:
        """
        Add a list of records to the main database.

        Args:
            lines (list[dict]): A list of dictionaries representing the records to insert.
        """
        self._add_lines(DownloadLinkTable, self.db, lines)
        self._logger.info("Successful added item in db")


    def get_link_line_from_tmp(self, link_type: str="link") -> dict:
        """
        Retrieve and remove a single link record from the temporary database.

        Args:
            link_type (str): The type of link to retrieve. Defaults to "link".

        Returns:
            dict: A dictionary containing the 'name' and 'url' of the retrieved record. 
                Returns an empty dictionary if no matching record is found.
        """
        res = {}
        with self.tem_db:
            with self.tem_db.atomic():
                query = TempUrlTable.select().where(TempUrlTable.ttype == link_type).first()
                if query:
                    res["name"] = query.name
                    res["url"] = query.url

                    query.delete_instance()
            return res
    

    def push_direct_link_to_db(self):
        """
        Transfer all 'direct' type links from the temporary database to the main database.
        """
        while (direct_link_dict := self.get_link_line_from_tmp("direct")):
            self.add_lines_to_db([direct_link_dict])


    def remove_tmp_db(self):
        """
        Close the temporary database connection and delete the temporary database file.
        """
        
        try:
            if not self.tem_db.is_closed:
                self.tem_db.close()
            os.remove(self.temp_db_path)
            self._logger.info("Temp db removed")
        except Exception as e:
            self._logger.error(f"ERROR IN REMOVE TEMP DB. Messenge: {e}")


        

    


