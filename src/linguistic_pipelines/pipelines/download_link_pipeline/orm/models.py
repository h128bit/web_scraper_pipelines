from peewee import Model, TextField, CharField, DatabaseProxy

db_tmp_proxy = DatabaseProxy()
db_proxy = DatabaseProxy()

class TempUrlTable(Model):
    class Meta:
        database = db_tmp_proxy

    name = TextField()
    url = TextField(unique=True)
    ttype = CharField(max_length=10)

    @staticmethod
    def get_db():
        return db_tmp_proxy


class DownloadLinkTable(Model):
    class Meta:
        database = db_proxy

    name = TextField()
    url = TextField()
    annotation = TextField(default="<NOT_SET>")
    annot_summarize = TextField(default="<NOT_SET>")
    text_summarize = TextField(default="<NOT_SET>")

    @staticmethod
    def get_db():
        return db_proxy

