from backend.extensions import db


class CarPerformance(db.Model):

    __tablename__ = "car_performance"

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

    aero = db.Column(
        db.Float,
        nullable=False,
        default=75.0
    )

    straight_line_speed = db.Column(
        db.Float,
        nullable=False,
        default=75.0
    )

    cornering = db.Column(
        db.Float,
        nullable=False,
        default=75.0
    )

    energy_efficiency = db.Column(
        db.Float,
        nullable=False,
        default=75.0
    )

    tyre_management = db.Column(
        db.Float,
        nullable=False,
        default=75.0
    )

    reliability = db.Column(
        db.Float,
        nullable=False,
        default=75.0
    )

    team = db.relationship(
        "Team",
        back_populates="car_performance"
    )

    def to_dict(self):

        return {

            "id": self.id,

            "team_id": self.team_id,

            "aero": self.aero,

            "straight_line_speed":
                self.straight_line_speed,

            "cornering":
                self.cornering,

            "energy_efficiency":
                self.energy_efficiency,

            "tyre_management":
                self.tyre_management,

            "reliability":
                self.reliability
        }