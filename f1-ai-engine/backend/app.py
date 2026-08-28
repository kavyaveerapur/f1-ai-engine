from flask import Flask, jsonify
from flask_cors import CORS

from backend.config import Config
from backend.extensions import db

from backend.routes.strategy_routes import strategy_bp
from backend.routes.team_routes import team_bp
from backend.routes.driver_routes import driver_bp
from backend.routes.circuit_routes import circuit_bp
from backend.routes.auth_routes import auth_bp
from backend.routes.career_routes import career_bp


app = Flask(__name__)

app.config.from_object(Config)

app.secret_key = Config.SECRET_KEY

CORS(
    app,
    supports_credentials=True
)

db.init_app(app)

app.register_blueprint(strategy_bp)
app.register_blueprint(team_bp)
app.register_blueprint(driver_bp)
app.register_blueprint(circuit_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(career_bp)


@app.route("/")
def home():

    return jsonify({
        "message": "F1 AI Engine Backend",
        "status": "running"
    })


@app.route("/api/health")
def health():

    return jsonify({
        "status": "healthy"
    })


with app.app_context():

    db.create_all()


if __name__ == "__main__":

    app.run(
        debug=True
    )
