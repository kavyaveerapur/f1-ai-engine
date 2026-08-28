from backend.extensions import db


class Driver(db.Model):

    __tablename__ = "drivers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    image = db.Column(
        db.String(500)
    )

    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.id"),
        nullable=False
    )

    team = db.relationship(
        "Team",
        back_populates="drivers"
    )

    performance = db.relationship(
        "DriverPerformance",
        back_populates="driver",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def to_dict(self):

        return {

            "id": self.id,

            "name": self.name,

            "image": self.image,

            "team_id": self.team_id
        }