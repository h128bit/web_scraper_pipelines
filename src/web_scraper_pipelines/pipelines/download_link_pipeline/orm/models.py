from peewee import Model, TextField, CharField, DatabaseProxy

db_tmp_proxy = DatabaseProxy()
db_proxy = DatabaseProxy()

class TempUrlTable(Model):
    """
    Model representing a temporary URL table.

    Attributes:
        name: The name associated with the URL.
        url: The unique URL string.
        ttype: A short type identifier (max 10 characters).
    """

    class Meta:
        database = db_tmp_proxy

    name = TextField()
    url = TextField(unique=True)
    ttype = CharField(max_length=10)

    @staticmethod
    def get_db():
        """
        Get the temporary database proxy instance.

        Returns:
            The DatabaseProxy instance used for the temporary database.
        """

        return db_tmp_proxy


class DownloadLinkTable(Model):
    """
    Model representing a download link table.

    Attributes:
        name: The name associated with the download link.
        url: The URL string for the download.
        annotation: Text annotation for the link.
        annot_summarize: Summarized annotation text.
        text_summarize: Summarized main text content.
    """
    class Meta:
        database = db_proxy

    name = TextField()
    url = TextField()
    annotation = TextField(default="<NOT_SET>")
    annot_summarize = TextField(default="<NOT_SET>")
    text_summarize = TextField(default="<NOT_SET>")

    @staticmethod
    def get_db():
        """
        Get the main database proxy instance.

        Returns:
            The DatabaseProxy instance used for the main database.
        """
        
        return db_proxy

