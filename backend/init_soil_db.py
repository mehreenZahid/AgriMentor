import mysql.connector
from config import Config

def init_db():
    print("Connecting to database...")
    db = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT
    )
    cursor = db.cursor()
    
    query = """
    CREATE TABLE IF NOT EXISTS soil_recommendations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        soil_type VARCHAR(100),
        season VARCHAR(100),
        water VARCHAR(100),
        recommended_crops TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    print("Creating soil_recommendations table if not exists...")
    cursor.execute(query)
    db.commit()
    
    cursor.close()
    db.close()
    print("Database updated structure successfully.")

if __name__ == "__main__":
    init_db()
