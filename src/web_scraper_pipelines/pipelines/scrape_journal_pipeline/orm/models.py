from peewee import Model, TextField, CharField, DatabaseProxy


db_proxy = DatabaseProxy()


class ViewedPagesTable(Model):
    """Table model for storing viewed URLs.

    Attributes:
        url (TextField): The unique URL of the viewed page.
    """
    
    class Meta:
        database = db_proxy

    url = TextField(unique=True)

    @staticmethod
    def get_db():
        """Get the database proxy instance.

        Returns:
            DatabaseProxy: The proxy instance used for the database connection.
        """
        return db_proxy