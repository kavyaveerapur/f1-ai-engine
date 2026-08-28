from flask import Blueprint, jsonify

from backend.models import Driver


driver_bp = Blueprint(
    "drivers",
    __name__,
    url_prefix="/api/drivers"
)


@driver_bp.route("/", methods=["GET"])
def get_drivers():

    drivers = Driver.query.all()

    return jsonify([
        driver.to_dict()
        for driver in drivers
    ])