from backend.extensions import db


class TeamDevelopment(db.Model):

    __tablename__ = "team_development"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.id"),
        unique=True,
        nullable=False
    )

    budget = db.Column(
        db.Float,
        nullable=False,
        default=1000.0
    )

    research_points = db.Column(
        db.Float,
        nullable=False,
        default=100.0
    )

    development_points = db.Column(
        db.Float,
        nullable=False,
        default=100.0
    )

    aero_level = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    power_unit_level = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    chassis_level = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    tyre_level = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    reliability_level = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    team = db.relationship(
        "Team",
        back_populates="development"
    )

    def to_dict(self):

        return {

            "id":
                self.id,

            "team_id":
                self.team_id,

            "budget":
                self.budget,

            "research_points":
                self.research_points,

            "development_points":
                self.development_points,

            "levels": {

                "Aero":
                    self.aero_level,

                "Power Unit":
                    self.power_unit_level,

                "Chassis":
                    self.chassis_level,

                "Tyres":
                    self.tyre_level,

                "Reliability":
                    self.reliability_level
            }
        }