import logging

import peewee 

from web_scraper_pipelines.utils.db import init_db
from web_scraper_pipelines.pipelines.scrape_journal_pipeline.orm.models import ViewedPagesTable


class ViewedURLTableOrm:
    """
    ORM class for managing and checking viewed site pages in the database.
    """ 

    def __init__(self,
                 db_path_or_url: str|None=None,
                 db_name: str|None=None,
                 db_user: str|None=None,
                 db_port: int|None=None,
                 db_password: str|None=None):
        """Initialize the database connection for the viewed pages table.

        Args:
            db_path_or_url (str | None): Path or connection URL to the database. Defaults to "viewed_pages.db".
            db_name (str | None): Name of the database.
            db_user (str | None): Username for the database connection.
            db_port (int | None): Port number for the database connection.
            db_password (str | None): Password for the database connection.
        """
        
        self._logger = logging.getLogger(self.__class__.__name__)
        
        db_path_or_url = db_path_or_url if db_path_or_url else "viewed_pages.db"

        db_params = {"db_name": db_name, "db_user": db_user, "db_port": db_port, "db_password": db_password}
        self.db = init_db(db_path_or_url, ViewedPagesTable, **db_params)


    def add_line(self, line: dict):
        """Add a new record to the viewed pages database.

        Args:
            line (dict): A dictionary containing the record data to insert.
        """

        with self.db:
            with self.db.atomic():
                ViewedPagesTable.insert(**line).execute()


    def check_existing(self, line: dict):
        """Check if a specific record already exists in the database.

        Args:
            line (dict): A dictionary containing the record data to check.

        Returns:
            bool: True if the record exists in the database, False otherwise.
        """
        
        with self.db:
            with self.db.atomic():
                query = ViewedPagesTable.get_or_none(**line)

        exists = not query is None

        return exists
    

    def delete_line(self, line: dict):
        """Delete a specific record from the viewed pages database.

        Args:
            line (dict): A dictionary containing the record data to delete.
        """

        with self.db:
            with self.db.atomic():
                query = ViewedPagesTable.get_or_none(**line)

                if query:
                    query.delete_instance()