import os

class Config:
    SECRET_KEY = os.getenv("APP_SECRET", "dev-secret")
    SQLALCHEMY_DATABASE_URI = "sqlite:////app/data/app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CAPTURES_DIR = "/app/captures"
    DEFAULT_TZ = os.getenv("TZ", "Europe/Madrid")

    # En Debian/Ubuntu con chromium/chromedriver instalados por apt
    CHROME_BIN = "/usr/bin/chromium"
    CHROMEDRIVER_BIN = "/usr/bin/chromedriver"
