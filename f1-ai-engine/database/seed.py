import ast
import os
import re

from backend.app import app
from backend.extensions import db

from backend.models import (
    Team,
    Driver,
    Car
)


DATA_FILE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "frontend",
    "data.js"
)


def clean_url(value):
    """
    Converts Markdown-style image links such as:

    [https://example.com/image.jpg](https://example.com/image.jpg)

    into:

    https://example.com/image.jpg
    """

    if not value:
        return value

    match = re.search(
        r"\]\((https?://[^)]+)\)",
        value
    )

    if match:
        return match.group(1)

    return value


def load_teams_data():

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        content = file.read()

    content = content.strip()

    # Remove JavaScript variable declaration
    if content.startswith("const teamsData"):
        content = content.split("=", 1)[1].strip()

    # Remove trailing semicolon
    if content.endswith(";"):
        content = content[:-1].strip()

    # Convert JavaScript object notation into
    # something Python's ast.literal_eval can understand.
    #
    # The keys in your data.js are already quoted,
    # but nested object keys such as:
    #
    # drivers:
    # principal:
    # engine:
    #
    # are not.
    content = re.sub(
        r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:',
        r'\1"\2":',
        content
    )

    return ast.literal_eval(content)


def seed_database():

    teams_data = load_teams_data()

    print(
        f"Found {len(teams_data)} teams in data.js"
    )

    for team_name, team_data in teams_data.items():

        existing_team = Team.query.filter_by(
            name=team_name
        ).first()

        if existing_team:

            team = existing_team

            team.principal = team_data.get(
                "principal"
            )

            team.engine = team_data.get(
                "engine"
            )

            team.logo = clean_url(
                team_data.get("logo")
            )

            team.background = clean_url(
                team_data.get("bg")
            )

        else:

            team = Team(
                name=team_name,
                principal=team_data.get(
                    "principal"
                ),
                engine=team_data.get(
                    "engine"
                ),
                logo=clean_url(
                    team_data.get("logo")
                ),
                background=clean_url(
                    team_data.get("bg")
                )
            )

            db.session.add(team)

            # Generate the team ID before
            # creating related records.
            db.session.flush()

        # ---------------------------------
        # Drivers
        # ---------------------------------

        existing_driver_names = {
            driver.name
            for driver in team.drivers
        }

        for driver_data in team_data.get(
            "drivers",
            []
        ):

            driver_name = driver_data.get(
                "name"
            )

            if driver_name not in existing_driver_names:

                driver = Driver(
                    name=driver_name,
                    image=clean_url(
                        driver_data.get("img")
                    ),
                    team_id=team.id
                )

                db.session.add(driver)

        # ---------------------------------
        # Car
        # ---------------------------------

        existing_car = Car.query.filter_by(
            team_id=team.id
        ).first()

        if existing_car:

            existing_car.image = clean_url(
                team_data.get("car")
            )

            existing_car.name = (
                f"{team_name} Car"
            )

        else:

            car = Car(
                name=f"{team_name} Car",
                team_id=team.id,
                image=clean_url(
                    team_data.get("car")
                )
            )

            db.session.add(car)

    db.session.commit()

    print(
        "F1 team data seeded successfully."
    )


if __name__ == "__main__":

    with app.app_context():

        seed_database()