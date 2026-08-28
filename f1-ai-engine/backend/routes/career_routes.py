from flask import Blueprint, jsonify, request, session

from backend.extensions import db
from backend.models import Circuit, Team
from backend.services.season_engine import season_engine


career_bp = Blueprint(
    "career",
    __name__,
    url_prefix="/api/career"
)


# -----------------------------------------------------------------------------
# In-memory active careers
# -----------------------------------------------------------------------------
CAREERS = {}


UPGRADE_CONFIG = {
    "aero": {
        "label": "AERODYNAMICS",
        "description": "Improve downforce efficiency and circuit cornering performance.",
        "attribute": "aero",
        "cost": 5,
    },
    "straight_line_speed": {
        "label": "POWER / STRAIGHT-LINE",
        "description": "Increase straight-line performance and qualifying pace.",
        "attribute": "straight_line_speed",
        "cost": 5,
    },
    "cornering": {
        "label": "CHASSIS / CORNERING",
        "description": "Improve mechanical grip and high-speed/technical corner performance.",
        "attribute": "cornering",
        "cost": 5,
    },
    "energy_efficiency": {
        "label": "ENERGY EFFICIENCY",
        "description": "Improve energy deployment and race-long pace consistency.",
        "attribute": "energy_efficiency",
        "cost": 5,
    },
    "tyre_management": {
        "label": "TYRE MANAGEMENT",
        "description": "Reduce degradation and improve long-run race pace.",
        "attribute": "tyre_management",
        "cost": 5,
    },
    "reliability": {
        "label": "RELIABILITY",
        "description": "Increase reliability and reduce performance loss over a race.",
        "attribute": "reliability",
        "cost": 5,
    },
}

UPGRADE_MAX_LEVEL = 10
UPGRADE_STEP = 2.0
STARTING_DEVELOPMENT_POINTS = 20

# Development points earned during a career.
# Every completed race gives a base reward, with bonuses for scoring,
# podiums and wins. This keeps development limited but renewable.
BASE_RACE_DEVELOPMENT_POINTS = 3
POINTS_FINISH_BONUS = 1
PODIUM_DEVELOPMENT_BONUS = 2
WIN_DEVELOPMENT_BONUS = 3


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _career_key():
    user_id = session.get("user_id")
    if user_id is not None:
        return str(user_id)
    return "guest"


def _team_name(team):
    return str(getattr(team, "name", ""))


def _find_team(teams, team_name):
    target = str(team_name or "").strip().lower()
    for team in teams:
        if _team_name(team).strip().lower() == target:
            return team
    return None


def _find_driver(team, driver_id=None, driver_name=None):
    drivers = getattr(team, "drivers", []) or []

    if driver_id is not None:
        for driver in drivers:
            if str(getattr(driver, "id", "")) == str(driver_id):
                return driver

    target = str(driver_name or "").strip().lower()
    if target:
        for driver in drivers:
            if str(getattr(driver, "name", "")).strip().lower() == target:
                return driver

    return None


def _constructor_standing(standings, team_name):
    target = str(team_name or "").strip().lower()
    for row in standings or []:
        if str(row.get("team", "")).strip().lower() == target:
            return row
    return None


def _driver_standing(standings, driver_id=None, driver_name=None):
    for row in standings or []:
        if driver_id is not None and str(row.get("driver_id")) == str(driver_id):
            return row
        if driver_name and str(row.get("driver", "")).strip().lower() == str(driver_name).strip().lower():
            return row
    return None


def _race_team_points(classification, team_name, fastest_driver=None):
    point_table = {
        1: 25,
        2: 18,
        3: 15,
        4: 12,
        5: 10,
        6: 8,
        7: 6,
        8: 4,
        9: 2,
        10: 1,
    }

    total = 0.0
    for row in classification or []:
        if str(row.get("team", "")).strip().lower() != str(team_name).strip().lower():
            continue

        position = int(row.get("position", 999) or 999)
        points = point_table.get(position, 0)

        if (
            fastest_driver
            and row.get("driver") == fastest_driver
            and position <= 10
        ):
            points += 1

        total += points

    return total


def _race_driver_points(classification, driver_id=None, driver_name=None, fastest_driver=None):
    point_table = {
        1: 25,
        2: 18,
        3: 15,
        4: 12,
        5: 10,
        6: 8,
        7: 6,
        8: 4,
        9: 2,
        10: 1,
    }

    for row in classification or []:
        same_driver = (
            driver_id is not None
            and str(row.get("driver_id")) == str(driver_id)
        ) or (
            driver_name
            and str(row.get("driver", "")).strip().lower()
            == str(driver_name).strip().lower()
        )

        if not same_driver:
            continue

        position = int(row.get("position", 999) or 999)
        points = point_table.get(position, 0)
        if fastest_driver and row.get("driver") == fastest_driver and position <= 10:
            points += 1

        return {
            "position": position if position < 999 else None,
            "points": points,
            "driver": row.get("driver"),
            "team": row.get("team"),
        }

    return {
        "position": None,
        "points": 0,
        "driver": driver_name,
        "team": None,
    }


def _development_reward(driver_result):
    """
    Calculate development points earned after one completed race.

    Base reward:
        +3 DP for completing a race.

    Performance bonuses:
        +1 DP for finishing in the points.
        +2 DP for a podium.
        +3 DP for a win.

    These rewards are intentionally additive but modest so upgrades remain
    a meaningful strategic choice throughout the 24-race season.
    """
    position = driver_result.get("position")

    reward = BASE_RACE_DEVELOPMENT_POINTS
    breakdown = {
        "race_completed": BASE_RACE_DEVELOPMENT_POINTS,
        "points_finish": 0,
        "podium": 0,
        "win": 0,
    }

    if position is not None and position <= 10:
        reward += POINTS_FINISH_BONUS
        breakdown["points_finish"] = POINTS_FINISH_BONUS

    if position is not None and position <= 3:
        reward += PODIUM_DEVELOPMENT_BONUS
        breakdown["podium"] = PODIUM_DEVELOPMENT_BONUS

    if position == 1:
        reward += WIN_DEVELOPMENT_BONUS
        breakdown["win"] = WIN_DEVELOPMENT_BONUS

    breakdown["total"] = reward
    return reward, breakdown


def _capture_car(team):
    performance = getattr(team, "car_performance", None)
    if performance is None:
        return {}

    result = {}
    for config in UPGRADE_CONFIG.values():
        attr = config["attribute"]
        value = getattr(performance, attr, None)
        if value is not None:
            result[attr] = float(value)
    return result


def _restore_car(team, baseline):
    performance = getattr(team, "car_performance", None)
    if performance is None:
        return

    for attr, value in (baseline or {}).items():
        if hasattr(performance, attr):
            setattr(performance, attr, float(value))


def _upgrade_state(career, team):
    performance = getattr(team, "car_performance", None)
    upgrades = career.setdefault("upgrades", {})

    output = []
    for key, config in UPGRADE_CONFIG.items():
        attr = config["attribute"]
        value = float(getattr(performance, attr, 75.0)) if performance is not None else 75.0
        level = int(upgrades.get(key, 0))
        cost = config["cost"]

        output.append({
            "key": key,
            "label": config["label"],
            "description": config["description"],
            "attribute": attr,
            "value": round(value, 2),
            "level": level,
            "max_level": UPGRADE_MAX_LEVEL,
            "cost": cost,
            "can_buy": (
                level < UPGRADE_MAX_LEVEL
                and int(career.get("development_points", 0)) >= cost
            ),
        })

    return output


def _standings_dict(rows, key):
    result = {}
    for row in rows or []:
        value = row.get(key)
        if value is not None:
            result[value] = dict(row)
    return result


def _next_circuit(circuits, round_number):
    if round_number < 1 or round_number > len(circuits):
        return None
    return circuits[round_number - 1]


def _race_card(circuit, round_number, completed=False):
    if circuit is None:
        return None
    return {
        "round": round_number,
        "circuit": getattr(circuit, "name", "Unknown Circuit"),
        "country": getattr(circuit, "country", "Unknown"),
        "weather": getattr(circuit, "weather", "Dry"),
        "completed": completed,
        "status": "completed" if completed else "upcoming",
    }


def _build_dashboard(career, teams, circuits):
    result = career.get("season_result") or {}
    driver_standings = result.get("driver_standings", [])
    constructor_standings = result.get("constructor_standings", [])

    my_team = career.get("team")
    driver_id = career.get("driver_id")
    driver_name = career.get("driver_name")

    my_team_standing = _constructor_standing(constructor_standings, my_team) or {}
    my_driver_standing = _driver_standing(
        driver_standings,
        driver_id=driver_id,
        driver_name=driver_name,
    ) or {}

    completed_races = result.get("races", [])
    current_round = int(career.get("current_round", 1))

    if completed_races:
        current_race = dict(completed_races[-1])
        current_race["completed"] = True
        current_race["status"] = "completed"
        current_round_number = int(current_race.get("round", current_round - 1))
        next_round = current_round_number + 1
    else:
        current_round_number = current_round
        current_race = _race_card(
            _next_circuit(circuits, current_round),
            current_round,
            completed=False,
        )
        next_round = current_round + 1

    next_race = _race_card(
        _next_circuit(circuits, next_round),
        next_round,
        completed=False,
    )

    if completed_races:
        classification = current_race.get("classification", [])
        fastest_driver = (current_race.get("fastest_lap") or {}).get("driver")
        driver_result = _race_driver_points(
            classification,
            driver_id=driver_id,
            driver_name=driver_name,
            fastest_driver=fastest_driver,
        )
        current_race["driver_position"] = driver_result["position"]
        current_race["driver_points"] = driver_result["points"]
        current_race["team_points"] = _race_team_points(
            classification,
            my_team,
            fastest_driver=fastest_driver,
        )

    comparison = sorted(
        [dict(row) for row in driver_standings],
        key=lambda row: float(row.get("points", 0)),
        reverse=True,
    )

    return {
        "success": True,
        "started": True,
        "my_team": my_team,
        "driver": {
            "id": driver_id,
            "name": driver_name,
        },
        "career": career,
        "my_standing": my_team_standing,
        "driver_standing": my_driver_standing,
        "standings": constructor_standings,
        "driver_comparison": comparison,
        "current_race": current_race,
        "next_race": next_race,
    }


# -----------------------------------------------------------------------------
# Drivers / start career
# -----------------------------------------------------------------------------
@career_bp.route("/drivers", methods=["GET"])
def career_drivers():
    team_name = request.args.get("team", "")
    teams = Team.query.order_by(Team.id.asc()).all()
    team = _find_team(teams, team_name)

    if team is None:
        return jsonify({"success": False, "message": "Selected team not found."}), 404

    drivers = []
    for driver in getattr(team, "drivers", []) or []:
        performance = getattr(driver, "performance", None)
        drivers.append({
            "id": getattr(driver, "id", None),
            "name": getattr(driver, "name", "Unknown Driver"),
            "performance": {
                "race_pace": float(getattr(performance, "race_pace", 75.0)),
                "tyre_management": float(getattr(performance, "tyre_management", 75.0)),
                "overtaking": float(getattr(performance, "overtaking", 75.0)),
                "consistency": float(getattr(performance, "consistency", 75.0)),
            },
        })

    return jsonify({
        "success": True,
        "team": _team_name(team),
        "drivers": drivers,
    })


@career_bp.route("/start", methods=["POST"])
def start_career():
    data = request.get_json(silent=True) or {}
    team_name = str(data.get("team", "")).strip()
    driver_id = data.get("driver_id")
    driver_name = str(data.get("driver_name", "")).strip()
    season_year = int(data.get("season", 2026))

    teams = Team.query.order_by(Team.id.asc()).all()
    circuits = Circuit.query.order_by(Circuit.id.asc()).all()
    selected_team = _find_team(teams, team_name)

    if selected_team is None:
        return jsonify({"success": False, "message": "Selected team not found."}), 404
    if not circuits:
        return jsonify({"success": False, "message": "No circuits found."}), 500

    selected_driver = _find_driver(
        selected_team,
        driver_id=driver_id,
        driver_name=driver_name,
    )

    if selected_driver is None:
        return jsonify({"success": False, "message": "Select a valid driver before starting the career."}), 400

    key = _career_key()

    # If an older career exists in this process, restore its baseline car
    # before creating a fresh championship.
    old = CAREERS.get(key)
    if old and old.get("baseline_car"):
        _restore_car(selected_team, old["baseline_car"])
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    baseline_car = _capture_car(selected_team)

    CAREERS[key] = {
        "team": _team_name(selected_team),
        "team_id": getattr(selected_team, "id", None),
        "driver_id": getattr(selected_driver, "id", None),
        "driver_name": getattr(selected_driver, "name", "Unknown Driver"),
        "season": season_year,
        "current_round": 1,
        "started": True,
        "season_completed": False,
        "development_points": STARTING_DEVELOPMENT_POINTS,
        "upgrades": {},
        "baseline_car": baseline_car,
        "season_result": {
            "races": [],
            "driver_standings": [],
            "constructor_standings": [],
        },
    }

    return jsonify({
        "success": True,
        "message": "Career started.",
        "career": CAREERS[key],
    })


# -----------------------------------------------------------------------------
# Status / dashboard
# -----------------------------------------------------------------------------
@career_bp.route("/status", methods=["GET"])
def career_status():
    career = CAREERS.get(_career_key())
    if career is None:
        return jsonify({"success": True, "started": False, "career": None})
    return jsonify({"success": True, "started": True, "career": career})


@career_bp.route("/dashboard", methods=["GET"])
def career_dashboard():
    career = CAREERS.get(_career_key())
    if career is None:
        return jsonify({"success": True, "started": False, "career": None})

    teams = Team.query.order_by(Team.id.asc()).all()
    circuits = Circuit.query.order_by(Circuit.id.asc()).all()
    return jsonify(_build_dashboard(career, teams, circuits))


# -----------------------------------------------------------------------------
# Incremental career race
# -----------------------------------------------------------------------------
@career_bp.route("/race", methods=["POST"])
def run_career_race():
    key = _career_key()
    career = CAREERS.get(key)

    if career is None:
        return jsonify({
            "success": False,
            "message": "Start a career first."
        }), 400

    if career.get("season_completed"):
        return jsonify({
            "success": False,
            "message": "The 2026 season is already complete."
        }), 400

    teams = Team.query.order_by(Team.id.asc()).all()
    circuits = Circuit.query.order_by(Circuit.id.asc()).all()
    round_number = int(career.get("current_round", 1))

    if not teams:
        return jsonify({
            "success": False,
            "message": "No teams found."
        }), 500

    if not circuits:
        return jsonify({
            "success": False,
            "message": "No circuits found."
        }), 500

    if round_number > len(circuits):
        career["season_completed"] = True
        CAREERS[key] = career

        return jsonify({
            "success": True,
            "season_completed": True,
            "career": career
        })

    previous = career.get("season_result") or {}

    previous_driver = _standings_dict(
        previous.get("driver_standings", []),
        "driver_id",
    )

    previous_constructor = _standings_dict(
        previous.get("constructor_standings", []),
        "team_id",
    )

    try:
        result = season_engine.run_single_round(
            circuits=circuits,
            teams=teams,
            season_year=career.get("season", 2026),
            round_number=round_number,
            previous_driver_standings=previous_driver,
            previous_constructor_standings=previous_constructor,
        )
    except Exception as exc:
        return jsonify({
            "success": False,
            "message": "Race simulation failed.",
            "round": round_number,
            "error": str(exc),
        }), 500

    # run_single_round returns a one-item "races" list.
    round_races = result.get("races", [])
    race = dict(round_races[-1]) if round_races else {}

    races = list(previous.get("races", []))
    races.append(race)

    driver_standings = result.get(
        "driver_standings",
        [],
    )

    constructor_standings = result.get(
        "constructor_standings",
        [],
    )

    driver_result = _race_driver_points(
        race.get("classification", []),
        driver_id=career.get("driver_id"),
        driver_name=career.get("driver_name"),
        fastest_driver=(race.get("fastest_lap") or {}).get("driver"),
    )

    reward, reward_breakdown = _development_reward(
        driver_result
    )

    old_development_points = int(
        career.get(
            "development_points",
            STARTING_DEVELOPMENT_POINTS,
        )
    )

    new_development_points = (
        old_development_points
        + reward
    )

    career["development_points"] = new_development_points

    career["last_development_reward"] = {
        "round": round_number,
        "points_earned": reward,
        "breakdown": reward_breakdown,
        "old_balance": old_development_points,
        "new_balance": new_development_points,
    }

    career["season_result"] = {
        "races": races,
        "driver_standings": driver_standings,
        "constructor_standings": constructor_standings,
    }

    career["current_round"] = (
        round_number + 1
    )

    career["season_completed"] = (
        round_number >= len(circuits)
    )

    CAREERS[key] = career

    dashboard = _build_dashboard(
        career,
        teams,
        circuits,
    )

    dashboard.update({
        "round": round_number,
        "next_round": career["current_round"],
        "season_completed": career["season_completed"],
        "race": race,
        "driver_race_result": driver_result,
        "development_reward": career["last_development_reward"],
        "development_points": new_development_points,
    })

    return jsonify(dashboard)


# -----------------------------------------------------------------------------
# Full-season compatibility endpoint
# -----------------------------------------------------------------------------
@career_bp.route("/run", methods=["POST"])
def run_career_season():
    key = _career_key()
    career = CAREERS.get(key)

    if career is None:
        return jsonify({"success": False, "message": "Start a career first."}), 400

    teams = Team.query.order_by(Team.id.asc()).all()
    circuits = Circuit.query.order_by(Circuit.id.asc()).all()

    result = season_engine.run_season(
        circuits=circuits,
        teams=teams,
        season_year=career.get("season", 2026),
    )

    career["season_result"] = result
    career["current_round"] = len(result.get("races", [])) + 1
    career["season_completed"] = True
    CAREERS[key] = career

    return jsonify({"success": True, "career": career})


# -----------------------------------------------------------------------------
# Championship standings / comparisons
# -----------------------------------------------------------------------------
@career_bp.route("/standings", methods=["GET"])
def standings():
    career = CAREERS.get(_career_key())
    if career is None:
        return jsonify({"success": False, "message": "No active career."}), 404

    result = career.get("season_result") or {}
    return jsonify({
        "success": True,
        "started": True,
        "completed": bool(result.get("races")),
        "standings": result.get("constructor_standings", []),
        "driver_standings": result.get("driver_standings", []),
    })


@career_bp.route("/teams", methods=["GET"])
def team_comparison():
    career = CAREERS.get(_career_key())
    if career is None:
        return jsonify({"success": False, "message": "No active career."}), 404

    teams = Team.query.order_by(Team.id.asc()).all()
    result = career.get("season_result") or {}
    standings = result.get("constructor_standings", [])
    my_team = career.get("team")
    mine = _constructor_standing(standings, my_team) or {}
    my_points = float(mine.get("points", 0))
    my_wins = int(mine.get("wins", 0))
    my_podiums = int(mine.get("podiums", 0))

    output = []
    for team in teams:
        name = _team_name(team)
        standing = _constructor_standing(standings, name) or {}
        points = float(standing.get("points", 0))
        wins = int(standing.get("wins", 0))
        podiums = int(standing.get("podiums", 0))
        output.append({
            "team": name,
            "position": standing.get("position"),
            "points": points,
            "wins": wins,
            "podiums": podiums,
            "is_my_team": name.strip().lower() == str(my_team).strip().lower(),
            "points_delta": points - my_points,
            "wins_delta": wins - my_wins,
            "podiums_delta": podiums - my_podiums,
        })

    return jsonify({"success": True, "my_team": my_team, "teams": output})


@career_bp.route("/race-pace", methods=["GET"])
def race_pace():
    career = CAREERS.get(_career_key())
    if career is None:
        return jsonify({"success": False, "message": "No active career."}), 404

    result = career.get("season_result") or {}
    races = result.get("races", [])
    my_team = career.get("team")

    completed = []
    for race in races:
        classification = race.get("classification", [])
        fastest_driver = (race.get("fastest_lap") or {}).get("driver")
        positions = [
            int(row.get("position", 999))
            for row in classification
            if str(row.get("team", "")).strip().lower() == str(my_team).strip().lower()
        ]
        completed.append({
            "round": race.get("round"),
            "circuit": race.get("circuit"),
            "country": race.get("country"),
            "weather": race.get("weather"),
            "position": min(positions) if positions else None,
            "points": _race_team_points(classification, my_team, fastest_driver),
            "status": "completed",
        })

    circuits = Circuit.query.order_by(Circuit.id.asc()).all()
    completed_rounds = {int(r.get("round", 0)) for r in races}
    upcoming = []
    for index, circuit in enumerate(circuits, start=1):
        if index in completed_rounds:
            continue
        upcoming.append({
            "round": index,
            "circuit": getattr(circuit, "name", "Unknown Circuit"),
            "status": "upcoming",
            "expected": {"classification": "Very close", "label": "Very close"},
        })

    return jsonify({
        "success": True,
        "team": my_team,
        "completed": completed,
        "upcoming": upcoming,
    })


# -----------------------------------------------------------------------------
# Car development / upgrades
# -----------------------------------------------------------------------------
@career_bp.route("/upgrades", methods=["GET"])
def career_upgrades():
    career = CAREERS.get(_career_key())
    if career is None:
        return jsonify({"success": False, "message": "Start a career first."}), 404

    teams = Team.query.order_by(Team.id.asc()).all()
    team = _find_team(teams, career.get("team"))
    if team is None:
        return jsonify({"success": False, "message": "Career team not found."}), 404

    return jsonify({
        "success": True,
        "team": career.get("team"),
        "development_points": int(career.get("development_points", 0)),
        "upgrades": _upgrade_state(career, team),
    })


@career_bp.route("/upgrade", methods=["POST"])
def career_upgrade():
    career = CAREERS.get(_career_key())
    if career is None:
        return jsonify({"success": False, "message": "Start a career first."}), 404

    data = request.get_json(silent=True) or {}
    component = str(data.get("component", "")).strip()
    config = UPGRADE_CONFIG.get(component)

    if config is None:
        return jsonify({"success": False, "message": "Unknown upgrade component."}), 400

    level = int(career.setdefault("upgrades", {}).get(component, 0))
    cost = int(config["cost"])
    points = int(career.get("development_points", 0))

    if level >= UPGRADE_MAX_LEVEL:
        return jsonify({"success": False, "message": "This component is already at maximum level."}), 400
    if points < cost:
        return jsonify({"success": False, "message": "Not enough development points."}), 400

    teams = Team.query.order_by(Team.id.asc()).all()
    team = _find_team(teams, career.get("team"))
    if team is None:
        return jsonify({"success": False, "message": "Career team not found."}), 404

    performance = getattr(team, "car_performance", None)
    if performance is None:
        return jsonify({"success": False, "message": "This team has no car-performance record."}), 500

    attr = config["attribute"]
    old_value = float(getattr(performance, attr, 75.0))
    new_value = min(100.0, old_value + UPGRADE_STEP)
    setattr(performance, attr, new_value)

    career["development_points"] = points - cost
    career["upgrades"][component] = level + 1
    CAREERS[_career_key()] = career

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Upgrade could not be saved: {exc}"}), 500

    return jsonify({
        "success": True,
        "component": component,
        "old_value": round(old_value, 2),
        "new_value": round(new_value, 2),
        "development_points": career["development_points"],
        "level": career["upgrades"][component],
    })
