import os

MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "invanteris_it")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "project2-helpdesk-secret-key"
)