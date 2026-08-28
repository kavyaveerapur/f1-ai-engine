from backend.app import app
from backend.extensions import db
from backend.models import Team, TeamDevelopment


def seed_development():

    teams = (
        Team.query
        .order_by(Team.id)
        .all()
    )

    if not teams:

        print(
            "No teams found. "
            "Seed teams first."
        )

        return

    created = 0
    existing = 0

    for team in teams:

        development = (
            TeamDevelopment.query
            .filter_by(
                team_id=team.id
            )
            .first()
        )

        if development:

            existing += 1

            continue

        development = TeamDevelopment(

            team_id=team.id,

            budget=1000.0,

            research_points=100.0,

            development_points=100.0,

            aero_level=0,

            power_unit_level=0,

            chassis_level=0,

            tyre_level=0,

            reliability_level=0
        )

        db.session.add(
            development
        )

        created += 1

    db.session.commit()

    print(
        f"Development records created: {created}"
    )

    print(
        f"Development records already existed: {existing}"
    )

    print(
        "Team development successfully initialized."
    )


if __name__ == "__main__":

    with app.app_context():

        seed_development()