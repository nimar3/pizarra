from os import environ

import redis
from rq import Connection, Worker

from app import create_app, create_worker_app
from config import config_dict

get_config_mode = environ.get('CONFIG_MODE', 'Debug')

config_mode = []
try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid CONFIG_MODE environment variable entry.')

app = create_worker_app(config_mode)
app.app_context().push()
redis_url = app.config["RQ_DASHBOARD_REDIS_URL"]
redis_connection = redis.from_url(redis_url)
with Connection(redis_connection):
        worker = Worker(app.config["QUEUES"])
        worker.work()

if __name__ == "__main__":
    app.run()


