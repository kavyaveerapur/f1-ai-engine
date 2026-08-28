from backend.extensions import db


class Upgrade(db.Model):

    __tablename__ = "upgrades"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.id"),
        nullable=False
    )

    category = db.Column(
        db.String(50),
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    level = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    cost = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    aero_gain = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    straight_line_gain = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    cornering_gain = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    energy_gain = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    tyre_management_gain = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    reliability_gain = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    team = db.relationship(
        "Team",
        back_populates="upgrades"
    )

    def to_dict(self):

        return {

            "id":
                self.id,

            "team_id":
                self.team_id,

            "category":
                self.category,

            "name":
                self.name,

            "level":
                self.level,

            "cost":
                self.cost,

            "effects": {

                "aero":
                    self.aero_gain,

                "straight_line_speed":
                    self.straight_line_gain,

                "cornering":
                    self.cornering_gain,

                "energy_efficiency":
                    self.energy_gain,

                "tyre_management":
                    self.tyre_management_gain,

                "reliability":
                    self.reliability_gain
            }
        }