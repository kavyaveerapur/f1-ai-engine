from flask import Blueprint, request, jsonify


strategy_bp = Blueprint(
    "strategy",
    __name__,
    url_prefix="/api/strategy"
)


@strategy_bp.route("/analyze", methods=["POST"])
def analyze_strategy():

    data = request.get_json()

    team = data.get("team", "Unknown Team")
    track = data.get("track", "Unknown Circuit")
    weather = data.get("weather", "Unknown")

    analysis = f"""Strategy Analysis

Team: {team}
Circuit: {track}
Weather: {weather}

Backend Status
The Python Flask backend successfully received the strategy request.

Next Step
The real F1 simulation and AI strategy engine will replace this temporary response.
"""

    return jsonify({
        "success": True,
        "analysis": analysis
    })