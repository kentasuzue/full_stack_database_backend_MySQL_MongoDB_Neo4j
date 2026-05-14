from dash import  Dash
import config

# Config

CONFIG_FILE = "config.json"
mysql_db, mongo_db, neo4j_db, NEO4JDB = config.config_db(CONFIG_FILE)

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True,)
server = app.server

API_BASE_URL = "http://127.0.0.1:8050/api"
