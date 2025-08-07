import mysql.connector
from config import DB_CONFIG, topics, DB_name

def create_database():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        query = f"CREATE DATABASE IF NOT EXISTS {DB_name}"
        cursor.execute(query)
        query = f"USE {DB_name}"
        cursor.execute(query)
        query = """CREATE TABLE  IF NOT EXISTS user(
                    telegram_id BIGINT PRIMARY KEY NOT NULL UNIQUE,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    news_mode ENUM('full', 'summarize')
                    )"""
        cursor.execute(query)
        query="""CREATE TABLE IF NOT EXISTS topics (
                TOPIC_ID INT AUTO_INCREMENT PRIMARY KEY,
                TOPIC_NAME VARCHAR(100) NOT NULL UNIQUE)"""
        cursor.execute(query)
        query = """CREATE TABLE IF NOT EXISTS news(
                    TOPIC_ID INT NOT NULL,
                    CONTENT MEDIUMTEXT NOT NULL ,
                    SUMM_CONTENT MEDIUMTEXT DEFAULT NULL,
                    TITLE TEXT NOT NULL,
                    NEW_CODE INT AUTO_INCREMENT PRIMARY KEY,
                    PUBLISH_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    IMAGE_URL MEDIUMTEXT,
                    DESCRIPTION MEDIUMTEXT NOT NULL,
                    FOREIGN KEY (TOPIC_ID) REFERENCES topics(TOPIC_ID),
                    INDEX idx_topic_id (TOPIC_ID))"""
        cursor.execute(query)
        query = """CREATE TABLE  IF NOT EXISTS userInteraction(
                    TELEGRAM_ID BIGINT NOT NULL,
                    NEW_CODE INT NOT NULL,
                    INTERACTION_TYPE ENUM('positive', 'negative', 'natural'),
                    FOREIGN KEY (TELEGRAM_ID) REFERENCES user(TELEGRAM_ID),
                    FOREIGN KEY (NEW_CODE) REFERENCES news(NEW_CODE),
                    PRIMARY KEY (TELEGRAM_ID, NEW_CODE))"""
        cursor.execute(query)
        query = """CREATE TABLE  IF NOT EXISTS user_topic(
                    TELEGRAM_ID BIGINT NOT NULL,
                    TOPIC_ID INT NOT NULL,
                    FOREIGN KEY (TELEGRAM_ID) REFERENCES user(TELEGRAM_ID),
                    FOREIGN KEY (TOPIC_ID) REFERENCES topics(TOPIC_ID),
                    PRIMARY KEY (TELEGRAM_ID, TOPIC_ID))"""
        cursor.execute(query)
        query = """CREATE TABLE IF NOT EXISTS user_saved_news(
                    TELEGRAM_ID BIGINT,
                    NEW_CODE INT NOT NULL,
                    FOREIGN KEY (TELEGRAM_ID) REFERENCES user(TELEGRAM_ID),
                    FOREIGN KEY (NEW_CODE) REFERENCES news(NEW_CODE),
                    PRIMARY KEY (TELEGRAM_ID, NEW_CODE))"""
        cursor.execute(query)
        query = """CREATE TABLE IF NOT EXISTS user_timer (
                        USER_TIME INT AUTO_INCREMENT PRIMARY KEY,
                        TELEGRAM_ID BIGINT NOT NULL,
                        TIME_VALUE BIGINT,
                        MODE ENUM('minutes', 'hour'),
                        FOREIGN KEY (TELEGRAM_ID) REFERENCES user(TELEGRAM_ID));"""
        cursor.execute(query)
        connection.commit()
        print("database created with tables: user, topics, news, userinteraction, user_topic, user_saved_news, user_timer")
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
    
    except Exception as e:
        print(f"error occurred: {e}")
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            
            
            
def add_topics(topics):
    try:
        for topic in topics:
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()
            query = """INSERT INTO topics (TOPIC_NAME) VALUES (%s)""" 
            values = (topic,)
            cursor.execute(query, values)
            connection.commit()
        print("all topics added to database")
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
    create_database()
    DB_CONFIG["database"] = DB_name
    add_topics(topics=topics)