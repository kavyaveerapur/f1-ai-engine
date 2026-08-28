from backend.extensions import db


class Team(db.Model):

    __tablename__ = "teams"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    principal = db.Column(
        db.String(100),
        nullable=False
    )

    engine = db.Column(
        db.String(100),
        nullable=False
    )

    logo = db.Column(
        db.String(500)
    )

    car_image = db.Column(
        db.String(500)
    )

    background = db.Column(
        db.String(500)
    )

    drivers = db.relationship(
        "Driver",
        back_populates="team",
        cascade="all, delete-orphan"
    )

    car = db.relationship(
        "Car",
        back_populates="team",
        uselist=False,
        cascade="all, delete-orphan"
    )

    car_performance = db.relationship(
        "CarPerformance",
        back_populates="team",
        uselist=False,
        cascade="all, delete-orphan"
    )

    upgrades = db.relationship(
        "Upgrade",
        back_populates="team",
        cascade="all, delete-orphan"
    )

    development = db.relationship(
        "TeamDevelopment",
        back_populates="team",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def to_dict(self):

        return {

            "id":
                self.id,

            "name":
                self.name,

            "principal":
                self.principal,

            "engine":
                self.engine,

            "logo":
                self.logo,

            "car":
                self.car_image,

            "background":
                self.background
        }