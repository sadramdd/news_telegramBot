import mysql.connector
from config import DB_CONFIG

def add_table():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        query = "CREATE DATABASE  IF NOT EXISTS TELEGRAMBOT"
        cursor.execute(query)
        query = "USE TELEGRAMBOT"
        cursor.execute(query)
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS user_timer (
                        USER_TIME INT AUTO_INCREMENT PRIMARY KEY,
                        TELEGRAM_ID BIGINT NOT NULL,
                        TIME_VALUE BIGINT,
                        MODE ENUM('minutes', 'hour'),
                        FOREIGN KEY (TELEGRAM_ID) REFERENCES user(TELEGRAM_ID));""")
        connection.commit()
        print("table added")
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
    
    except Exception as e:
        print(f"error occurred: {e}")
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    add_table()