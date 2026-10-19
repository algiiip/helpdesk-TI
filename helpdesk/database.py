
import os
import mysql.connector
from config import (
    MYSQL_HOST,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DATABASE,
    MYSQL_PORT,
)

def get_connection():
    config = {
        "host": MYSQL_HOST,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "database": MYSQL_DATABASE,
        "port": MYSQL_PORT,
        "connection_timeout": 15,
    }

    ssl_ca = os.environ.get("MYSQL_SSL_CA")
    if ssl_ca:
        config["ssl_ca"] = ssl_ca
        config["ssl_verify_cert"] = True
        config["ssl_verify_identity"] = True

    elif os.environ.get("RAILWAY_ENVIRONMENT"):
        raise RuntimeError(
            "MYSQL_SSL_CA belum dikonfigurasi untuk koneksi TiDB Cloud."
        )

    return mysql.connector.connect(**config)
