
class Config:
    SECRET_KEY = "secret"

    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://root:@localhost:3306/SystemPresence"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
