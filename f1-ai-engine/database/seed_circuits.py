from backend.app import app
from backend.extensions import db

from backend.models import Circuit


circuits = [

    {
        "name": "Australian Grand Prix",
        "country": "Australia",
        "track_type": "High Speed",
        "downforce_level": "Medium",
        "tyre_stress": "Medium",
        "overtaking_difficulty": "Medium"
    },

    {
        "name": "Chinese Grand Prix",
        "country": "China",
        "track_type": "Technical",
        "downforce_level": "Medium",
        "tyre_stress": "High",
        "overtaking_difficulty": "Medium"
    },

    {
        "name": "Japanese Grand Prix",
        "country": "Japan",
        "track_type": "High Speed",
        "downforce_level": "High",
        "tyre_stress": "High",
        "overtaking_difficulty": "High"
    },

    {
        "name": "Bahrain Grand Prix",
        "country": "Bahrain",
        "track_type": "Technical",
        "downforce_level": "Medium",
        "tyre_stress": "High",
        "overtaking_difficulty": "Low"
    },

    {
        "name": "Saudi Arabian Grand Prix",
        "country": "Saudi Arabia",
        "track_type": "Street High Speed",
        "downforce_level": "Medium",
        "tyre_stress": "Medium",
        "overtaking_difficulty": "Medium"
    },

    {
        "name": "Miami Grand Prix",
        "country": "United States",
        "track_type": "Mixed",
        "downforce_level": "Medium",
        "tyre_stress": "Medium",
        "overtaking_difficulty": "Medium"
    },

    {
        "name": "Emilia-Romagna Grand Prix",
        "country": "Italy",
        "track_type": "Technical",
        "downforce_level": "High",
        "tyre_stress": "Medium",
        "overtaking_difficulty": "High"
    },

    {
        "name": "Monaco Grand Prix",
        "country": "Monaco",
        "track_type": "Street",
        "downforce_level": "Very High",
        "tyre_stress": "Low",
        "overtaking_difficulty": "Very High"
    },

    {
        "name": "Spanish Grand Prix",
        "country": "Spain",
        "track_type": "Technical",
        "downforce_level": "High",
        "tyre_stress": "High",
        "overtaking_difficulty": "High"
    },

    {
        "name": "Canadian Grand Prix",
        "country": "Canada",
        "track_type": "Power",
        "downforce_level": "Low",
        "tyre_stress": "Medium",
        "overtaking_difficulty": "Low"
    },

    {
        "name": "Austrian Grand Prix",
        "country": "Austria",
        "track_type": "Mixed",
        "downforce_level": "Medium",
        "tyre_stress": "Medium",
        "overtaking_difficulty": "Low"
    },

    {
        "name": "British Grand Prix",
        "country": "United Kingdom",
        "track_type": "High Speed",
        "downforce_level": "High",
        "tyre_stress": "High",
        "overtaking_difficulty": "Medium"
    },

    {
        "name": "Belgian Grand Prix",
        "country": "Belgium",
        "track_type": "High Speed",
        "downforce_level": "Medium",
        "tyre_stress": "High",
        "overtaking_difficulty": "Medium"
    },

    {
        "name": "Hungarian Grand Prix",
        "country": "Hungary",
        "track_type": "Technical",
        "downforce_level": "Very High",
        "tyre_stress": "Medium",
        "overtaking_difficulty": "Very High"
    },

    {
        "name": "Dutch Grand Prix",
        "country": "Netherlands",
        "track_type": "Technical",
        "downforce_level": "High",
        "tyre_stress": "High",
        "overtaking_difficulty": "High"
    },

    {
        "name": "Italian Grand Prix",
        "country": "Italy",
        "track_type": "Power",
        "downforce_level": "Low",
        "tyre_stress": "Medium",
        "overtaking_difficulty": "Low"
    },

    {
        "name": "Azerbaijan Grand Prix",
        "country": "Azerbaijan",
        "track_type": "Street High Speed",
        "downforce_level": "Low",
        "tyre_stress": "Medium",
        "overtaking_difficulty": "Low"
    },

    {
        "name": "Singapore Grand Prix",
        "country": "Singapore",
        "track_type": "Street Technical",
        "downforce_level": "Very High",
        "tyre_stress": "High",
        "overtaking_difficulty": "High"
    },

    {
        "name": "United States Grand Prix",
        "country": "United States",
        "track_type": "Mixed",
        "downforce_level": "Medium",
        "tyre_stress": "High",
        "overtaking_difficulty": "Medium"
    },

    {
        "name": "Mexico City Grand Prix",
        "country": "Mexico",
        "track_type": "Power",
        "downforce_level": "Medium",
        "tyre_stress": "Medium",
        "overtaking_difficulty": "Medium"
    },

    {
        "name": "São Paulo Grand Prix",
        "country": "Brazil",
        "track_type": "Mixed",
        "downforce_level": "Medium",
        "tyre_stress": "High",
        "overtaking_difficulty": "Medium"
    },

    {
        "name": "Las Vegas Grand Prix",
        "country": "United States",
        "track_type": "Street High Speed",
        "downforce_level": "Low",
        "tyre_stress": "Low",
        "overtaking_difficulty": "Low"
    },

    {
        "name": "Qatar Grand Prix",
        "country": "Qatar",
        "track_type": "High Speed",
        "downforce_level": "High",
        "tyre_stress": "Very High",
        "overtaking_difficulty": "High"
    },

    {
        "name": "Abu Dhabi Grand Prix",
        "country": "United Arab Emirates",
        "track_type": "Mixed",
        "downforce_level": "Medium",
        "tyre_stress": "Medium",
        "overtaking_difficulty": "Medium"
    }
]


def seed_circuits():

    for circuit_data in circuits:

        existing = Circuit.query.filter_by(
            name=circuit_data["name"]
        ).first()

        if existing:
            continue

        circuit = Circuit(
            name=circuit_data["name"],
            country=circuit_data["country"],
            track_type=circuit_data["track_type"],
            downforce_level=circuit_data["downforce_level"],
            tyre_stress=circuit_data["tyre_stress"],
            overtaking_difficulty=circuit_data["overtaking_difficulty"]
        )

        db.session.add(circuit)

    db.session.commit()

    print(
        f"Successfully seeded {len(circuits)} circuits."
    )


if __name__ == "__main__":

    with app.app_context():

        seed_circuits()