from backend.extensions import db


class Car(db.Model):

    __tablename__ = "cars"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.id"),
        nullable=False
    )

    image = db.Column(
        db.String(500)
    )

    team = db.relationship(
        "Team",
        back_populates="car"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "name": self.name,
            "team_id": self.team_id,
            "image": self.image
        }