"""Production entry point: initialize before serving, then start one backup worker."""
from app import app, init_db

init_db(app)
app.extensions["start_backups"]()
