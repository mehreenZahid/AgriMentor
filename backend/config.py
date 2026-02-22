import os

class Config:
    # -------------------------------------------------
    # SECRET KEY
    # -------------------------------------------------
    SECRET_KEY = "agrimentor_super_secret_key"

    # -------------------------------------------------
    # DATABASE CONFIG (DO NOT MODIFY - ML DEPENDS ON THIS)
    # -------------------------------------------------
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASSWORD = ""
    DB_NAME = "agrimentor"
    DB_PORT = 3307

    # -------------------------------------------------
    # UPLOAD FOLDER (ML USES THIS)
    # -------------------------------------------------
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")

    # -------------------------------------------------
    # GOOGLE OAUTH CONFIG
    # -------------------------------------------------
    GOOGLE_CLIENT_ID = "260133501593-qdg311cidm0hfojnbelke3ch4gj18gpc.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = "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"

    # -------------------------------------------------
    # SESSION SETTINGS
    # -------------------------------------------------
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"
