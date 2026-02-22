import mysql.connector
from flask_login import UserMixin
from config import Config


# ---------------------------------------------------
# DATABASE CONNECTION (SEPARATE FOR USER MODEL)
# ---------------------------------------------------

def get_db_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT
    )


# ---------------------------------------------------
# USER MODEL
# ---------------------------------------------------

class User(UserMixin):
    def __init__(self, id, name, email, password_hash, role,
                 oauth_provider=None, oauth_id=None, created_at=None):

        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.oauth_provider = oauth_provider
        self.oauth_id = oauth_id

    # ---------------------------------------------------
    # REQUIRED BY FLASK-LOGIN
    # ---------------------------------------------------
    def get_id(self):
        return str(self.id)

    # ---------------------------------------------------
    # GET USER BY ID
    # ---------------------------------------------------
    @staticmethod
    def get_by_id(user_id):
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()

        cursor.close()
        db.close()

        if user_data:
            return User(**user_data)
        return None

    # ---------------------------------------------------
    # GET USER BY EMAIL
    # ---------------------------------------------------
    @staticmethod
    def get_by_email(email):
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()

        cursor.close()
        db.close()

        if user_data:
            return User(**user_data)
        return None

    # ---------------------------------------------------
    # CREATE NEW USER
    # ---------------------------------------------------
    @staticmethod
    def create(name, email, password_hash, role="farmer"):

        if role == "expert" and User.admin_exists():
            raise Exception("Admin already exists. Cannot create another admin.")

        db = get_db_connection()
        cursor = db.cursor()

        query = """
           INSERT INTO users (name, email, password_hash, role)
           VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (name, email, password_hash, role))
        db.commit()

        cursor.close()
        db.close()


    # ---------------------------------------------------
    # CREATE GOOGLE USER
    # ---------------------------------------------------
    @staticmethod
    def create_google_user(name, email, oauth_provider, oauth_id, role="farmer"):
        db = get_db_connection()
        cursor = db.cursor()

        query = """
            INSERT INTO users (name, email, oauth_provider, oauth_id, role)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, email, oauth_provider, oauth_id, role))
        db.commit()

        cursor.close()
        db.close()

    @staticmethod
    def admin_exists():
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE role = 'expert'")
        admin = cursor.fetchone()

        cursor.close()
        db.close()

        return admin is not None

        
