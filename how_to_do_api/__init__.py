from app import app
from flask_cors import CORS

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

## API Routes ##
from how_to_do_api.blueprints.users.views import users_api_blueprint


app.register_blueprint(users_api_blueprint, url_prefix='/api/v1/users')

