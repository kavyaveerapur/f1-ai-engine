from collections import Counter

from backend.app import app
from backend.models import Circuit, Team
from backend.services.season_engine import season_engine


with app.app_context():

    circuits = Circuit.query.order_by(
        Circuit.id.asc()
    ).all()

    teams = Team.query.order_by(
        Team.id.asc()
    ).all()

    result = season_engine.run_season(
        circuits=circuits,
        teams=teams,
        season_year=2026
    )

    print("=== RACE VARIATION TEST ===")

    for race in result["races"]:

        top10 = race.get(
            "classification",
            []
        )[:10]

        positions = []

        for driver in top10:

            positions.append(
                f'{driver.get("position")}. '
                f'{driver.get("driver")} '
                f'({driver.get("team")})'
            )

        print(
            f'R{race["round"]} | '
            f'{race["circuit"]} | '
            +
            " | ".join(positions)
        )

    print()
    print("=== WINNERS ===")

    winners = Counter()

    for race in result["races"]:

        classification = race.get(
            "classification",
            []
        )

        if classification:

            winner = classification[0].get(
                "team"
            )

            winners[winner] += 1

    for team, wins in winners.most_common():

        print(
            f"{team} | Wins: {wins}"
        )

    print()
    print("=== PODIUMS BY TEAM ===")

    podiums = Counter()

    for race in result["races"]:

        classification = race.get(
            "classification",
            []
        )

        for driver in classification[:3]:

            team = driver.get(
                "team"
            )

            podiums[team] += 1

    for team, count in podiums.most_common():

        print(
            f"{team} | Podiums: {count}"
        )