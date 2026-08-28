from flask import Blueprint, jsonify

from backend.models import Team


team_bp = Blueprint(
    "teams",
    __name__,
    url_prefix="/api/teams"
)


@team_bp.route("/", methods=["GET"])
def get_teams():

    teams = Team.query.all()

    return jsonify([
        team.to_dict()
        for team in teams
    ])


@team_bp.route("/<int:team_id>", methods=["GET"])
def get_team(team_id):

    team = Team.query.get(team_id)

    if not team:

        return jsonify({
            "success": False,
            "message": "Team not found"
        }), 404

    team_data = team.to_dict()

    team_data["drivers"] = [
        driver.to_dict()
        for driver in team.drivers
    ]

    if team.car:

        team_data["car_details"] = {
            "id": team.car.id,
            "name": team.car.name,
            "image": team.car.image
        }

    else:

        team_data["car_details"] = None

    return jsonify({
        "success": True,
        "team": team_data
    })