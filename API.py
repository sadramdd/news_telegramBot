import feedparser
from bs4 import BeautifulSoup
import time
import DML
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import topics, RSS_URL
from tf_idf_fitting import fit_news
print("importing done")





def get_webpage_content(url, stop_time: int=10):

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    driver.get(url)
    
    # Wait for Cloudflare to resolve
    time.sleep(stop_time)
    
    content = driver.page_source
    driver.quit()
    return content

def get_xml_dict(url, stop_time=7):
    content = get_webpage_content(url=url)
    if content:
        try:   
            feed_data = feedparser.parse(content)
            if feed_data["bozo"]:
                print("bozo error")

            
            soup = BeautifulSoup(feed_data['feed']['summary'], 'html.parser')
            
            if soup.pre:
                raw_text = soup.pre.get_text()
            else:
                raw_text = soup.get_text()
            raw_text = raw_text.replace("\u200c", " ")
            
            parsed_feed = feedparser.parse(raw_text)
            return parsed_feed

        except Exception as e:
            print(f"error: {e}")
            return False
    else:
        logging.error(f"webdriver cant connect to RSS FEED url: {RSS_URL}")
        return False

def get_full_document(url, stop_time=7):
    content = get_webpage_content(url=url, stop_time=7)
    soup = BeautifulSoup(content)
    document_text = soup.find("div", class_="item-text").get_text()
    document_text =  document_text.replace("\u200c", " ", )
    return document_text 
    
    
def remove_duplicate(text: str):
    sentence_list = text.split(".")
    new_text = []
    for sentence in sentence_list:
        if sentence not in new_text:
            new_text.append(sentence)
    return ".".join(new_text)




def main_loop():
    logging.getLogger('selenium').setLevel(logging.CRITICAL)
    logging.getLogger('urllib3').setLevel(logging.CRITICAL)
    print("getting news started!")
    while True:
        logging.info("Starting new RSS fetch cycle")
        try:
            xml_dict = get_xml_dict(RSS_URL)
            if not xml_dict:
                logging.info("waiting for 60 seconds")
                time.sleep(60)
                continue
                
            counter = 0
            for news_dict in xml_dict.entries:
                try:    
                    if not DML.is_news_in_db_byTitle(news_dict["title"]):
                        try:
                            raw_topic =  news_dict["tags"][0]["term"]
                            topic = raw_topic[0:raw_topic.index(">")-1]
                            if topic in topics:
                                news_topic = topic
                            else:
                                logging.error(f"topic: {topic} not in defined topics")
                                continue
                            image_url = None
                            for link in news_dict["links"]:
                                
                                if link["type"] == 'text/html':
                                    content_link = link["href"]
                                    
                                else:
                                    image_url =  link["href"]
                                
                            date_object = news_dict["updated_parsed"]
                            title = news_dict["title"]
                            
                            full_content = get_full_document(content_link, stop_time=10)
                            if  not full_content:
                                logging.error(f"can't fetch full document from isna")
                                continue
                            polished_content = remove_duplicate(full_content)
                            
                            summary = news_dict["summary"]
                            fit_news(polished_content) # fitting tf_idf everytime getting news
                            result = DML.add_news(
                                topic=news_topic,
                                content=polished_content,
                                title=title,
                                description=summary,
                                publish_date=date_object,
                                image_url=image_url
                            )
                            
                            if result:
                                counter += 1
                                logging.debug(f"Added news: {title[:50]}...")
                                
                        except Exception as e:
                            logging.error(f"Failed to add news: {e}")
                            
                except Exception as e:
                    logging.error(f"Error processing news item: {e}")
                    
            logging.info(f"Cycle completed. Added {counter} new articles")
            
        except Exception as e:
            logging.error(f"Fatal error in main loop: {e}")
            
        logging.info("Waiting 20 minutes...")
        time.sleep(20 * 60)

if __name__ == "__main__":
    logging.info("Starting news aggregator")
    try:
        main_loop()
    except KeyboardInterrupt:
        logging.info("Shutting down")
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
    print("end")