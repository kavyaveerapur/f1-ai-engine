import os


BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "..",
    "database",
    "f1.db"
)


class Config:

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///"
        + os.path.abspath(DATABASE_PATH)
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.environ.get(
        "F1_SECRET_KEY",
        "f1-ai-engine-development-secret-change-before-deployment"
    )
