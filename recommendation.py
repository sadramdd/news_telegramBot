from sklearn.metrics.pairwise import cosine_similarity
import DML
import random
import datetime
import logging
import joblib
from config import topics
"""
later on, im going to build a AI to do the jobs for both of functions blew (recommendations)
"""

vectorizer = joblib.load(r"telegram_bot_project\tfidf_vectorizer.pkl")


def is_recent(datetimeObject: datetime.datetime,
              highly_fresh_limit: int=5,
              moderate_fresh_limit: int=24,
              highly_fresh_score: int=2,
              moderate_fresh_score: int=1,
              old_score: int=-1):
    """helper for recommend_topic function,
    return the score for freshness of a datetimeObject (for news)"""
    now = datetime.datetime.now()
    delta = now - datetimeObject
    seconds = delta.total_seconds()
    if seconds <= highly_fresh_limit * 3600: # 1 hour
        return highly_fresh_score #highly recent
    elif seconds <= moderate_fresh_limit * 3600: # 5 hours
        return moderate_fresh_score #medium recent
    else: # more than 5 hours
        return old_score #not recent


def recommend_topic(user_id: int, 
    topics,
    low_exploration_chance: float= 0.1,
    mid_exploration_chance: float = 0.3,
    loved_topic_boost: int= 10,
    positive_interaction_score: int= 5,
    negative_interaction_score: int= -2):
    
    #get data from DBM (with error handling)
    try:
        user_data = DML.get_user_info(user_id)
        loved_topics = user_data.get("topics", [])
        interactions = DML.get_interaction_byTelegramid(user_id)
    except Exception as e:
        logging.error(f"Error occurred while fetching user data: {e}")
        return None

    try:
        topic_score = {code:0.0 for code in topics} # {topic_name:average_score}
        # adding freshness score for each topic(very low if not availabel)
        for topic in topics:
            recent_scores = []
            
            for news in DML.get_new_byTopic_generator(topic): # each news in the topic
                
                try:
                    if isinstance(news[5], str):
                        publish_date = datetime.strptime(news[5], "%Y-%m-%d %H:%M:%S")  # string → datetime
                    else:
                        publish_date = news[5]  # already datetime

                    recent_scores.append(is_recent(publish_date))
                except Exception as e:
                    logging.error(f'error accured: {e}')
                    return None
                
                
            if recent_scores:
                topic_score[topic] = sum(recent_scores) / len(recent_scores)
    except Exception as e:
        print(f"error happned while calculating freshness score for user: {user_id}\n error: {e}")
        logging.error(f"error happned while calculating freshness score for user: {user_id} error: {e}")
        
        
    try:
        # adding loved topics scores for each topic 
        if loved_topics:
            for love_topic in loved_topics:
                if love_topic in topic_score:
                    topic_score[love_topic] += loved_topic_boost
                else:
                    logging.error(f"{love_topic} not found in topics!")
    except Exception as e:
        print(f"error happned while calculating choosed topics score for user: {user_id}\n error: {e}")
        logging.error(f"error happned while calculating choosed topics score for user: {user_id} error: {e}")       
        
    
  
    # adding interaction scores for each topic
    if interactions:
        for interacted_tuple in interactions:
            try:
                interacted_new_code = int(interacted_tuple[1])
                interacted_topic_code = DML.get_new_byNewcode(int(interacted_new_code))[0]
                interacted_topic = DML.get_topic_name(int(interacted_topic_code))
                if not interacted_topic:
                    logging.error(f"interacted topic doesnt exist")
                    continue
                interacted_topic = interacted_topic[0]
                
                if interacted_topic in topic_score.keys():
                    interaction_type = interacted_tuple[0]
                    if interaction_type == "positive":
                        topic_score[interacted_topic] += positive_interaction_score
                    else:
                        topic_score[interacted_topic] += negative_interaction_score
                else:
                    logging.error(f"{interacted_topic} not in topics")
            except Exception as e:
                print(f"error happned while calculating interactions score for user: {user_id}\n error: {e}")
                logging.error(f"error happned while calculating interactions score for user: {user_id} error: {e}")      
        
      

    scaled_exploration_chance = low_exploration_chance / max(len(topics), 1)  # protect against div-by-zero
    sorted_topics = sorted(topic_score, key=topic_score.get)

    if random.random() < scaled_exploration_chance:
        return sorted_topics[0]  # lowest scoring topic

    chances_index = random.random()
    if chances_index < mid_exploration_chance:
        return sorted_topics[int(chances_index * len(sorted_topics))]  # mid-range randomness

    return max(topic_score, key=topic_score.get) if topic_score else None




def recommend_recent_new(user_id):
    try:
        print("recomending most recent news!")
        logging.debug("recomending most recent news!")
        
        user_seen_news = DML.get_user_seen_news_byTelegramid(user_id)
        user_seen_codes = {int(news[0]) for news in user_seen_news}  
        
        
        for new_tuple in DML.get_recent_new_generator():
            topic_code = int(new_tuple[0])
            topic_name = DML.get_topic_name(topic_code)
            code = int(new_tuple[-4])
            
            if code in user_seen_codes:
                continue
            
            print(f"returning news: {code}")
            logging.debug(f"returning news: {code}")
            return code
        
        print("nothing found")
        return None
    
    except Exception as e:
        print(f"error happend while recommending recent news: \n {e}")
    
    

    
    
    
def recommend_news(recommended_topic, user_id):
    try:
        user_seen_length = DML.get_user_news_seen_number_byTelegramid(user_id) # how many news has user seen so far
        news_scores = []
        if user_seen_length >= 2: # if user seen atleast two news
            
            user_seen_news = DML.get_user_seen_news_byTelegramid(user_id)
            user_seen_codes = {news[0] for news in user_seen_news} # news[0] for first item in tuple (only item)
            

            news_limit = 15
            for i, new_tuple in enumerate(DML.get_new_byTopic_generator(str(recommended_topic))): # generator gives us one news at the time with the given topic
                if i >= news_limit:
                    break
                code = int(new_tuple[-4]) # extract the code
                if code in user_seen_codes:
                    continue
                
                score_average = {"code":code, "average": 0}
                
                summary = new_tuple[-1] # extract the summary

                #dataloader = sentiment_model.tokenize([summary]) #tokenized news
                #summary_embbed = sentiment_model.embedd(dataloader) #embedded news
                summary_vector = vectorizer.transform([summary])

                score_summ = 0 # summ for average 
                count = 0 # count for average

                limit = max(1, user_seen_length // 2)
                
                for index, new_code in enumerate(user_seen_codes): #generator gives us one news code at the time with the given topic
                    if index >= limit:
                        break
                    
                    user_seen_tuple = DML.get_new_byNewcode(new_code)

                    user_seen_summary = user_seen_tuple[-1] # extract the user seen summary
                    
                    #user_seen_dataloader = sentiment_model.tokenize([user_seen_summary]) # tokenized user seen news
                    #user_seen_summary_embbed = sentiment_model.embedd(user_seen_dataloader) # embedded user seen news
                    
                    user_seen_summary_vector = vectorizer.transform([user_seen_summary])

            
                    if summary != user_seen_summary: # if the user has not seen the news 
                        cosine_score = cosine_similarity(summary_vector, user_seen_summary_vector) # how similiar are they
                        score_summ += cosine_score # for average
                        count += 1 # one more
                        
                average = score_summ / count if count > 0 else 0
                score_average["average"] = average
                news_scores.append(score_average)
                
            # Find the news with highest average similarity
            if news_scores:
                
                length = len(news_scores)
                best_match = max(news_scores, key=lambda x: x["average"])
                return best_match["code"]
            
            else:
                # No valid comparisons found
                return recommend_recent_new(user_id=user_id)
            
        else:
            user_seen_news = DML.get_user_seen_news_byTelegramid(user_id)
            user_seen_news = {news[0] for news in user_seen_news}
            
            
            print("user has seen less than 2 news")
            logging.debug("user has seen less than 2 news")
            
            for random_news in DML.get_new_byTopic_generator(recommended_topic):
                if random_news:
                    code = random_news[-4]
                    if code not in user_seen_news:
                        print(f"returning news: {code}")
                        logging.debug(f"returning news: {code}")
                        
                        return code

            # no valid comparisons found
            return recommend_recent_new(user_id=user_id)
    except Exception as e:
        print(f"error happend while recommending news: {e}")