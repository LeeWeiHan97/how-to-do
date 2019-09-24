from dotenv import load_dotenv
load_dotenv()

import os
import config
from flask import Flask
from models.base_model import db
from flask_jwt_extended import JWTManager
import os
from celery import Celery
from helpers.noti import notification

app = Flask('HOW-TO-DO')
app.secret_key = os.environ.get('SECRET_KEY')

celery = Celery(
        app.import_name,
        backend="redis://localhost:6379",
        broker="redis://localhost:6379"
    )

celery.conf.update(app.config)

class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

if os.getenv('FLASK_ENV') == 'production':
    app.config.from_object("config.ProductionConfig")
else:
    app.config.from_object("config.DevelopmentConfig")

jwt = JWTManager(app)

@app.before_request
def before_request():
    db.connect()

@app.teardown_request
def _db_close(exc):
    if not db.is_closed():
        print(db)
        print(db.close())
    return exc

@celery.task
def scheduled_task_notification(registration_id):
    title = "You have a task to do!!!!!"
    body="DO OR DIE!"
    notification(registration_id, title, body)