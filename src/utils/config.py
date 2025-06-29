import os


def load_database_config():

    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')

    # Create a dictionary with the database configuration
    db = {
        'host': db_host,
        'port': int(db_port),
        'dbname': db_name,
        'user': db_user,
        'password': db_password
    }

    return db
