from backend.app import app
from backend.extensions import db

from backend.models import (
    Team,
    Driver,
    Car,
    Circuit
)


with app.app_context():

    db.create_all()

    print("Database tables created successfully.")