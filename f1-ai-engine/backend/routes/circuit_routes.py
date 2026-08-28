from flask import Blueprint, jsonify

from backend.models import Circuit


circuit_bp = Blueprint(
    "circuits",
    __name__,
    url_prefix="/api/circuits"
)


@circuit_bp.route("/", methods=["GET"])
def get_circuits():

    circuits = Circuit.query.all()

    return jsonify([
        circuit.to_dict()
        for circuit in circuits
    ])