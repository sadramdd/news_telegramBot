import mysql.connector
from mysql.connector import Error
import datetime
from config import DB_CONFIG
import logging
import time
DB_CONFIG["database"] =  "TELEGRAMBOT"

logging.basicConfig(filename=r"telegram_bot_project\KHABARRESAN_logs.log",
                    level=logging.INFO,  encoding='utf-8',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s') # this method sets the basic configurations for logging libray


print("log created")
#adds
def add_user(telegram_id: int , joinDate: datetime.datetime =datetime.datetime.now()):
    join = joinDate.strftime("%Y-%m-%d %H:%M:%S")

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        query = """INSERT INTO user (TELEGRAM_ID, JOIN_DATE) VALUES (%s, %s)"""
        values = (telegram_id, join)
        cursor.execute(query, values)
        connection.commit()
        print(f"user row with id: {telegram_id} and joindate: {join} created")
        logging.info(f"user row with id: {telegram_id} and joindate: {join} created")
        return True
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

def add_user_topic_ByTelgramid(telegramid: int, topic: str):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()

        cursor.execute("""SELECT TOPIC_ID FROM topics where TOPIC_NAME = %s""", (topic,))
        result = cursor.fetchone()
        if not result:
            logging.error(f"Topic '{topic}' not found.")
            return None
        topic_id = result[0]


        
        query = """INSERT INTO user_topic (TELEGRAM_ID, TOPIC_ID) VALUES (%s, %s)"""
        values = (telegramid, topic_id)
        cursor.execute(query, values)
        connection.commit()
        print(f"user topic added")
        logging.info(f"user topic added")
        
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
    

def add_news(topic: str,
             content: str,
             description: str,
             title: str,
             publish_date: datetime.datetime = datetime.datetime.now(),
             image_url=None,
             summ_content=None):

    try:
        publish = time.strftime("%Y-%m-%d %H:%M:%S", publish_date)
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM topics WHERE TOPIC_NAME = %s", (topic,))
        topic_id = cursor.fetchone()[0]
        
        # Determine which query to use based on provided parameters
        if image_url and summ_content:
            query = """INSERT INTO news (TOPIC_ID, CONTENT, SUMM_CONTENT, TITLE, PUBLISH_DATE, IMAGE_URL, DESCRIPTION) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            values = (topic_id, content, summ_content, title, publish, image_url, description)
        elif image_url:
            query = """INSERT INTO news (TOPIC_ID, CONTENT, TITLE, PUBLISH_DATE, IMAGE_URL, DESCRIPTION) 
                       VALUES (%s, %s, %s, %s, %s, %s)"""
            values = (topic_id, content, title, publish, image_url, description)
        elif summ_content:
            query = """INSERT INTO news (TOPIC_ID, CONTENT, SUMM_CONTENT, TITLE, PUBLISH_DATE, DESCRIPTION) 
                       VALUES (%s, %s, %s, %s, %s, %s)"""
            values = (topic_id, content, summ_content, title, publish, description)
        else:
            query = """INSERT INTO news (TOPIC_ID, CONTENT, TITLE, PUBLISH_DATE, DESCRIPTION) 
                       VALUES (%s, %s, %s, %s, %s)"""
            values = (topic_id, content, title, publish, description)
        cursor.execute(query, values)
        connection.commit()
        print(f"News with topic: {topic} created")
        logging.info(f"News with topic: {topic} created")
        return True
        
    except mysql.connector.Error as sqlerror:
        print(f"MySQL error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return False
    except Exception as e:
        print(f"Error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()


def add_saved_news(new_code: int, telegram_id: int):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """
                INSERT INTO user_saved_news (TELEGRAM_ID, NEW_CODE)
                VALUES (%s, %s)
                """
        values = (telegram_id, new_code)
        cursor.execute(query, values)
        connection.commit()
        print(f"user: {telegram_id } saved the news: {new_code}")
        logging.info(f"user: {telegram_id } saved the news: {new_code}")
        return True
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
        
        
           


def add_interaction(telegram_id: int, new_code: int, interaction_type: str):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """
                INSERT INTO userInteraction (TELEGRAM_ID, NEW_CODE, INTERACTION_TYPE)
                VALUES (%s, %s, %s)
                """
        values = (telegram_id, new_code, interaction_type)
        cursor.execute(query, values)
        connection.commit()
        return True
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()


def add_times(telegramid: int, value: int, mode: str):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """
                INSERT INTO user_timer (TELEGRAM_ID, TIME_VALUE, MODE)
                VALUES (%s, %s, %s)
                """
        values = (telegramid, value, mode)
        cursor.execute(query, values)
        connection.commit()
        return True
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close() 

#gets

def get_users():
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        hours = []
        # Get topic IDs
        cursor.execute("select TELEGRAM_ID from user")
        result = cursor.fetchall()
        return result

    except mysql.connector.Error as sqlerror:
        logging.error(f"mySQL error: {sqlerror}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()


def get_times(telegramid: int, mode="hour"):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        value = []
        # Get topic IDs
        cursor.execute("""
                        SELECT TIME_VALUE, Mode 
                        FROM user_timer 
                        WHERE TELEGRAM_ID = %s
                    """, (telegramid,))
        for time in cursor:
            if time["Mode"] == mode:
                value.append(time["TIME_VALUE"])
        return value

    except mysql.connector.Error as sqlerror:
        logging.error(f"mySQL error: {sqlerror}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
    


def get_user_info(telegramid: int):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()

        # Get join date
        cursor.execute("SELECT join_date FROM user WHERE TELEGRAM_ID = %s", (telegramid,))
        join_date = cursor.fetchone()

        # Get topic IDs
        cursor.execute("SELECT TOPIC_ID FROM user_topic WHERE TELEGRAM_ID = %s", (telegramid,))
        topic_ids = cursor.fetchall()

        # Map IDs to names
        topics = []
        for topic_id in topic_ids:
            cursor.execute("SELECT TOPIC_NAME FROM topics WHERE TOPIC_ID = %s", (topic_id[0],))
            result = cursor.fetchone()
            if result:
                topics.append(result[0])

        return {
            "join_date": join_date[0] if join_date else None,
            "topics": topics
        }

    except mysql.connector.Error as sqlerror:
        logging.error(f"MySQL error: {sqlerror}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

# can be deleted
def get_new_byTopic(topic: str):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """SELECT * FROM news WHERE topic = %s"""
        values = (topic,)
        cursor.execute(query, values)
        result = cursor.fetchall() # returns a list of tuples(list of rows)
        cursor.close()
        connection.close()
        return result
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
        
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()



def get_new_byTopic_generator(topic: str):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM topics WHERE TOPIC_NAME = %s", (topic,))
        topic_id = cursor.fetchone()[0]
        cursor2 = connection.cursor(buffered=False)
        cursor2.execute("SELECT * FROM news WHERE TOPIC_ID = %s", (topic_id,))
        while True:
            res = cursor2.fetchone()
            if res:
                yield res
            else:
                break

    except mysql.connector.Error as sqlerror:
        logging.error(f"MySQL error occurred: {sqlerror}")

    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")

    finally:
        try:
            #fetch any remaining rows to avoid 'Unread result found'
            while cursor.fetchone():
                pass
        except Exception:
            pass  #no more rows or already closed

        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
    

            
            
def get_recent_new_generator():
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor(buffered=False)  # Streaming mode
        cursor.execute("SELECT * FROM news")
        for res in cursor:
            yield res

    except mysql.connector.Error as sqlerror:
        logging.error(f"MySQL error occurred: {sqlerror}")

    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")

    finally:
        
        try:
            #fetch any remaining rows to avoid 'Unread result found'
            while cursor.fetchone():
                pass
        except Exception:
            pass  #no more rows or already closed
        
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
     
def get_new_byNewcode(newcode: int):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """SELECT * FROM news WHERE new_code = %s"""
        values = (newcode,)
        cursor.execute(query, values)
        result = cursor.fetchone() # returns a tuple(rows)
        cursor.close()
        connection.close()
        return result
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()


def get_user_seen_news_byTelegramid(telegramid: int):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """SELECT NEW_CODE FROM userInteraction WHERE TELEGRAM_ID = %s"""
        values = (telegramid,)
        cursor.execute(query, values)
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return result
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

def get_user_news_mode_byTelegramid(telegramid: int):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """SELECT news_mode FROM user WHERE TELEGRAM_ID = %s"""
        values = (telegramid,)
        cursor.execute(query, values)
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
    
    
    
def get_user_news_seen_number_byTelegramid(telegramid: int):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """SELECT NEW_CODE FROM userInteraction WHERE TELEGRAM_ID = %s"""
        values = (telegramid,)
        cursor.execute(query, values)
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return len(result)
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

def get_topic_name(topic_code):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """SELECT TOPIC_NAME FROM topics WHERE TOPIC_ID = %s"""
        values = (topic_code,)
        cursor.execute(query, values)
        result = cursor.fetchone() # returns a tuple
        cursor.close()
        connection.close()
        return result
        
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
        
        
    


def get_interaction_byTelegramid(telegramid: int):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """SELECT INTERACTION_TYPE, NEW_CODE FROM userInteraction WHERE TELEGRAM_ID = %s"""
        values = (telegramid,)
        cursor.execute(query, values)
        result = cursor.fetchall() # returns a list of tuples(list of rows)
        cursor.close()
        connection.close()
        return result
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()


def get_saved_newsbyTelegramid_generator(telegramid: int):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """SELECT NEW_CODE FROM user_saved_news WHERE TELEGRAM_ID = %s"""
        values = (telegramid,)
        cursor.execute(query, values)
        
        while True:
            result = cursor.fetchone()
            if result is None:
                return None                
            yield result
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            
#changes

def change_news_mode_byTelegramid(telegramid: int, mode: str):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """
                UPDATE user
                SET news_mode = %s
                WHERE telegram_id =%s;
                """
        values = (mode, telegramid)
        cursor.execute(query, values)
        connection.commit()
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            
def change_interaction(user_id: int, new_code: int, interaction: str):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """
                UPDATE userInteraction
                SET INTERACTION_TYPE = %s
                WHERE TELEGRAM_ID = %s AND NEW_CODE = %s;
                """
        values = (interaction, user_id, new_code)
        cursor.execute(query, values)
        connection.commit()
        
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
    
            
        
 
def is_news_in_db_byTitle(title: str):
    #needs to be checked
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = "SELECT * FROM news WHERE title = %s"
        values = (title,)
        cursor.execute(query, values)
        res = cursor.fetchall()
        if res:
            return True
        else:
            return False
        
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()



def is_news_with_imagebyNewcode(newcode):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = "SELECT IMAGE_URL FROM news WHERE new_code = %s"
        values = (newcode,)
        cursor.execute(query, values)
        res = cursor.fetchone()
        if res and res[0]:  # res[0] is IMAGE_URL
            return True
        else:
            return False
        
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()        
    
def does_telegram_id_exists(telegramid: int):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """SELECT EXISTS(SELECT 1 FROM user WHERE telegram_id = %s)"""
        cursor.execute(query, (telegramid,))
        if cursor:
            return cursor.fetchone()[0] == 1
        return False
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()      
            
def has_times(telegramid: int):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = """SELECT EXISTS(SELECT 1 FROM user_timer WHERE TELEGRAM_ID = %s)"""
        cursor.execute(query, (telegramid,))
        return cursor.fetchone()[0] == 1
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close() 
    
#removes



def delete_user_topics(telegramid: int):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = "DELETE FROM user_topic WHERE TELEGRAM_ID = %s"
        cursor.execute(query, (telegramid, ))
        connection.commit()
        
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close() 
            
            
            
            
def delete_news(newcode):  
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = "DELETE FROM news WHERE new_code = %s"
        cursor.execute(query, (newcode, ))
        connection.commit()
        
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close() 
            
def delete_minutes(telegramid):
    try:
        connection = mysql.connector.connection.MySQLConnection(**DB_CONFIG)
        cursor = connection.cursor()
        query = "DELETE FROM user_timer WHERE TELEGRAM_ID = %s AND MODE = 'minute'"
        cursor.execute(query, (telegramid, ))
        connection.commit()
        
    except mysql.connector.Error as sqlerror:
        print(f"mysql error occurred: {sqlerror}")
        logging.error(f"mysql error occurred: {sqlerror}")
        return None
    
    except Exception as e:
        print(f"error occurred: {e}")
        logging.error(f"error occurred: {e}")
        return None
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close() 