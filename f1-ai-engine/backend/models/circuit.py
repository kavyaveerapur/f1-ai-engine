from backend.extensions import db


class Circuit(db.Model):

    __tablename__ = "circuits"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    country = db.Column(
        db.String(100),
        nullable=False
    )

    track_type = db.Column(
        db.String(100)
    )

    downforce_level = db.Column(
        db.String(50)
    )

    tyre_stress = db.Column(
        db.String(50)
    )

    overtaking_difficulty = db.Column(
        db.String(50)
    )

    def to_dict(self):

        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "track_type": self.track_type,
            "downforce_level": self.downforce_level,
            "tyre_stress": self.tyre_stress,
            "overtaking_difficulty": self.overtaking_difficulty
        }