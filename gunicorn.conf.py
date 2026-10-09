import os

bind = "0.0.0.0:" + os.getenv("PORT", "8000")
# SQLite + one in-process backup scheduler: use a single worker, multiple threads.
workers = 1
threads = 4
timeout = 180
graceful_timeout = 180
accesslog = "-"
errorlog = "-"
preload_app = False
