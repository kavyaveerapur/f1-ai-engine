from backend.extensions import db


class DriverPerformance(db.Model):

    __tablename__ = "driver_performance"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    driver_id = db.Column(
        db.Integer,
        db.ForeignKey("drivers.id"),
        unique=True,
        nullable=False
    )

    race_pace = db.Column(
        db.Float,
        nullable=False,
        default=75.0
    )

    tyre_management = db.Column(
        db.Float,
        nullable=False,
        default=75.0
    )

    overtaking = db.Column(
        db.Float,
        nullable=False,
        default=75.0
    )

    consistency = db.Column(
        db.Float,
        nullable=False,
        default=75.0
    )

    driver = db.relationship(
        "Driver",
        back_populates="performance"
    )

    def to_dict(self):

        return {

            "id": self.id,

            "driver_id": self.driver_id,

            "race_pace":
                self.race_pace,

            "tyre_management":
                self.tyre_management,

            "overtaking":
                self.overtaking,

            "consistency":
                self.consistency
        }