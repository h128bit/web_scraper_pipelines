from peewee import Model, SqliteDatabase, PostgresqlDatabase


def init_db(
        db_path: str, 
        model: Model,
        db_name: str|None=None,
        db_user: str|None=None,
        db_port: int|None=None,
        db_password: str|None=None):
    """
    Initialize and configure a Peewee database connection.

    Determines whether to use a local SQLite database or a remote PostgreSQL
    database based on the provided `db_path`. Initializes the database proxy
    for the given model and creates the necessary tables if they do not exist.

    Args:
        db_path (str): Path to the SQLite database file (must end with ".db") 
            or the host address for a PostgreSQL database.
        model (Model): The Peewee Model class to bind to the database and 
            create tables for.
        db_name (str | None): Name of the PostgreSQL database.
        db_user (str | None): Username for the PostgreSQL database connection.
        db_port (int | None): Port number for the PostgreSQL database connection.
        db_password (str | None): Password for the PostgreSQL database connection.

    Returns:
        SqliteDatabase | PostgresqlDatabase: The initialized Peewee database instance.
    """
        
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