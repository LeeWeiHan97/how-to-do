import os
import config
from flask import Flask
from models.base_model import db
from flask_jwt_extended import JWTManager
import os

app = Flask('HOW-TO-DO')
app.secret_key = os.environ.get('SECRET_KEY')

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
