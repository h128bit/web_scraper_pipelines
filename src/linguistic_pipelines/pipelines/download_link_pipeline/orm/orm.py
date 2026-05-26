import os
import logging

import peewee
from peewee import Model, SqliteDatabase, PostgresqlDatabase
from linguistic_pipelines.pipelines.download_link_pipeline.orm.models import TempUrlTable, DownloadLinkTable



def _init_db(
        db_path: str, 
        model: Model,
        db_name: str|None=None,
        db_user: str|None=None,
        db_port: int|None=None,
        db_password: str|None=None,):
        
    if db_path.endswith(".db"):
        db = SqliteDatabase(db_path)
    else: 
        db = PostgresqlDatabase(
        db_name,
        user=db_user,
        password=db_password,
        host=db_path,
        port=db_port
        ) 

    model.get_db().initialize(db)
    with db.atomic():
        db.create_tables([model], safe=True)
    return db


class URLFilesTableOrm:
    def __init__(self, 
                 temp_db_path: str|None=None, 
                 db_path_or_url: str|None=None,
                 db_name: str|None=None,
                 db_user: str|None=None,
                 db_port: int|None=None,
                 db_password: str|None=None):
        self._logger = logging.getLogger(self.__class__.__name__)

        temp_db_path = temp_db_path if temp_db_path else "tmp.db"
        db_path_or_url = db_path_or_url if db_path_or_url else "download_link.db"

        self.tem_db = _init_db(temp_db_path, TempUrlTable)
        db_params = {"db_name": db_name, "db_user": db_user, "db_port": db_port, "db_password": db_password}
        self.db = _init_db(db_path_or_url, DownloadLinkTable, **db_params)

        self._logger.info("Temp db created successful")

        self.temp_db_path = temp_db_path


    def _add_lines(self, model, db, lines: list[dict]) -> None:
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
        self._add_lines(TempUrlTable, self.tem_db, lines)


    def add_lines_to_db(self, lines: list[dict]) -> None:
        self._add_lines(DownloadLinkTable, self.db, lines)
        self._logger.info("Successful added item in db")


    def get_link_line_from_tmp(self, link_type: str="link") -> dict:
        """
        return: dict like {name: url name, 
                           url: url}
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
        while (direct_link_dict := self.get_link_line_from_tmp("direct")):
            self.add_lines_to_db([direct_link_dict])


    def remove_tmp_db(self):
        try:
            if not self.tem_db.is_closed:
                self.tem_db.close()
            os.remove(self.temp_db_path)
            self._logger.info("Temp db removed")
        except Exception as e:
            self._logger.error(f"ERROR IN REMOVE TEMP DB. Messenge: {e}")


        

    


