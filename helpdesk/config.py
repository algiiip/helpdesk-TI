import os

# Konfigurasi database MySQL /TiDB Cloud
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "invanteris_it")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))

#Kunci keamanan Flask
SECRET_KEY = os.environ,get(
    "SECRET_KEY"
    "change-this-secret-key"
)
