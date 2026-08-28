from backend.app import app
from backend.extensions import db

from backend.models import (
    Team,
    Driver,
    CarPerformance,
    DriverPerformance
)


# =========================================================
# CAR PERFORMANCE
# =========================================================
#
# These are INTERNAL simulation/game parameters.
# They are not official F1 telemetry.
#
# Scale:
# 0 - 100
#
# Higher = better performance.
# =========================================================

CAR_PERFORMANCE = {

    "Oracle Red Bull Racing": {
        "aero": 95,
        "straight_line_speed": 92,
        "cornering": 96,
        "energy_efficiency": 91,
        "tyre_management": 94,
        "reliability": 92
    },

    "McLaren Mastercard": {
        "aero": 96,
        "straight_line_speed": 93,
        "cornering": 97,
        "energy_efficiency": 94,
        "tyre_management": 96,
        "reliability": 94
    },

    "Scuderia Ferrari HP": {
        "aero": 92,
        "straight_line_speed": 94,
        "cornering": 93,
        "energy_efficiency": 90,
        "tyre_management": 91,
        "reliability": 91
    },

    "Mercedes-AMG Petronas": {
        "aero": 91,
        "straight_line_speed": 91,
        "cornering": 92,
        "energy_efficiency": 93,
        "tyre_management": 92,
        "reliability": 94
    },

    "Aston Martin Aramco": {
        "aero": 86,
        "straight_line_speed": 84,
        "cornering": 87,
        "energy_efficiency": 86,
        "tyre_management": 88,
        "reliability": 90
    },

    "Visa Cash App RB": {
        "aero": 82,
        "straight_line_speed": 87,
        "cornering": 82,
        "energy_efficiency": 84,
        "tyre_management": 84,
        "reliability": 86
    },

    "Audi Revolut F1 Team": {
        "aero": 80,
        "straight_line_speed": 84,
        "cornering": 80,
        "energy_efficiency": 83,
        "tyre_management": 82,
        "reliability": 84
    },

    "Atlassian Williams": {
        "aero": 78,
        "straight_line_speed": 91,
        "cornering": 76,
        "energy_efficiency": 82,
        "tyre_management": 79,
        "reliability": 87
    },

    "BWT Alpine": {
        "aero": 79,
        "straight_line_speed": 82,
        "cornering": 81,
        "energy_efficiency": 80,
        "tyre_management": 81,
        "reliability": 84
    },

    "TGR Haas": {
        "aero": 77,
        "straight_line_speed": 85,
        "cornering": 78,
        "energy_efficiency": 79,
        "tyre_management": 78,
        "reliability": 82
    },

    "Cadillac Formula 1": {
        "aero": 76,
        "straight_line_speed": 83,
        "cornering": 77,
        "energy_efficiency": 78,
        "tyre_management": 79,
        "reliability": 80
    }
}


# =========================================================
# DRIVER PERFORMANCE
# =========================================================
#
# INTERNAL SIMULATION PARAMETERS.
# Scale: 0 - 100
# =========================================================

DRIVER_PERFORMANCE = {

    "Max Verstappen": {
        "race_pace": 98,
        "tyre_management": 97,
        "overtaking": 97,
        "consistency": 98
    },

    "Isack Hadjar": {
        "race_pace": 82,
        "tyre_management": 80,
        "overtaking": 81,
        "consistency": 79
    },

    "Lando Norris": {
        "race_pace": 96,
        "tyre_management": 94,
        "overtaking": 92,
        "consistency": 94
    },

    "Oscar Piastri": {
        "race_pace": 95,
        "tyre_management": 94,
        "overtaking": 93,
        "consistency": 95
    },

    "Charles Leclerc": {
        "race_pace": 95,
        "tyre_management": 91,
        "overtaking": 93,
        "consistency": 92
    },

    "Lewis Hamilton": {
        "race_pace": 93,
        "tyre_management": 96,
        "overtaking": 95,
        "consistency": 91
    },

    "George Russell": {
        "race_pace": 92,
        "tyre_management": 90,
        "overtaking": 91,
        "consistency": 93
    },

    "Kimi Antonelli": {
        "race_pace": 88,
        "tyre_management": 84,
        "overtaking": 86,
        "consistency": 83
    },

    "Fernando Alonso": {
        "race_pace": 91,
        "tyre_management": 95,
        "overtaking": 94,
        "consistency": 94
    },

    "Lance Stroll": {
        "race_pace": 80,
        "tyre_management": 81,
        "overtaking": 79,
        "consistency": 78
    },

    "Liam Lawson": {
        "race_pace": 83,
        "tyre_management": 82,
        "overtaking": 84,
        "consistency": 80
    },

    "Arvid Lindblad": {
        "race_pace": 79,
        "tyre_management": 78,
        "overtaking": 80,
        "consistency": 76
    },

    "Nico Hülkenberg": {
        "race_pace": 84,
        "tyre_management": 88,
        "overtaking": 86,
        "consistency": 89
    },

    "Gabriel Bortoleto": {
        "race_pace": 80,
        "tyre_management": 81,
        "overtaking": 79,
        "consistency": 78
    },

    "Alex Albon": {
        "race_pace": 86,
        "tyre_management": 87,
        "overtaking": 85,
        "consistency": 86
    },

    "Carlos Sainz": {
        "race_pace": 89,
        "tyre_management": 92,
        "overtaking": 88,
        "consistency": 91
    },

    "Pierre Gasly": {
        "race_pace": 87,
        "tyre_management": 85,
        "overtaking": 86,
        "consistency": 86
    },

    "Franco Colapinto": {
        "race_pace": 81,
        "tyre_management": 80,
        "overtaking": 82,
        "consistency": 78
    },

    "Esteban Ocon": {
        "race_pace": 84,
        "tyre_management": 84,
        "overtaking": 85,
        "consistency": 84
    },

    "Oliver Bearman": {
        "race_pace": 85,
        "tyre_management": 82,
        "overtaking": 84,
        "consistency": 81
    },

    "Sergio Pérez": {
        "race_pace": 85,
        "tyre_management": 91,
        "overtaking": 88,
        "consistency": 84
    },

    "Valtteri Bottas": {
        "race_pace": 86,
        "tyre_management": 89,
        "overtaking": 85,
        "consistency": 88
    }
}


# =========================================================
# SEED CAR PERFORMANCE
# =========================================================

def seed_car_performance():

    created = 0
    updated = 0

    for team_name, values in CAR_PERFORMANCE.items():

        team = Team.query.filter_by(
            name=team_name
        ).first()

        if not team:
            print(
                f"WARNING: Team not found: {team_name}"
            )
            continue

        performance = CarPerformance.query.filter_by(
            team_id=team.id
        ).first()

        if performance:

            performance.aero = values["aero"]
            performance.straight_line_speed = values[
                "straight_line_speed"
            ]
            performance.cornering = values["cornering"]
            performance.energy_efficiency = values[
                "energy_efficiency"
            ]
            performance.tyre_management = values[
                "tyre_management"
            ]
            performance.reliability = values[
                "reliability"
            ]

            updated += 1

        else:

            performance = CarPerformance(

                team_id=team.id,

                aero=values["aero"],

                straight_line_speed=values[
                    "straight_line_speed"
                ],

                cornering=values["cornering"],

                energy_efficiency=values[
                    "energy_efficiency"
                ],

                tyre_management=values[
                    "tyre_management"
                ],

                reliability=values[
                    "reliability"
                ]
            )

            db.session.add(
                performance
            )

            created += 1


    db.session.commit()

    print(
        f"Car performance seeded: "
        f"{created} created, "
        f"{updated} updated."
    )


# =========================================================
# SEED DRIVER PERFORMANCE
# =========================================================

def seed_driver_performance():

    created = 0
    updated = 0

    for driver_name, values in DRIVER_PERFORMANCE.items():

        driver = Driver.query.filter_by(
            name=driver_name
        ).first()

        if not driver:

            print(
                f"WARNING: Driver not found: "
                f"{driver_name}"
            )

            continue

        performance = DriverPerformance.query.filter_by(
            driver_id=driver.id
        ).first()

        if performance:

            performance.race_pace = values[
                "race_pace"
            ]

            performance.tyre_management = values[
                "tyre_management"
            ]

            performance.overtaking = values[
                "overtaking"
            ]

            performance.consistency = values[
                "consistency"
            ]

            updated += 1

        else:

            performance = DriverPerformance(

                driver_id=driver.id,

                race_pace=values[
                    "race_pace"
                ],

                tyre_management=values[
                    "tyre_management"
                ],

                overtaking=values[
                    "overtaking"
                ],

                consistency=values[
                    "consistency"
                ]
            )

            db.session.add(
                performance
            )

            created += 1


    db.session.commit()

    print(
        f"Driver performance seeded: "
        f"{created} created, "
        f"{updated} updated."
    )


# =========================================================
# MAIN
# =========================================================

def seed_performance():

    print(
        "Starting performance data seeding..."
    )

    seed_car_performance()

    seed_driver_performance()

    print(
        "Performance data seeded successfully."
    )


if __name__ == "__main__":

    with app.app_context():

        seed_performance()