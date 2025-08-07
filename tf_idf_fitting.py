from sklearn.feature_extraction.text import TfidfVectorizer
import joblib 
import logging
from DML import get_recent_new_generator, get_new_byNewcode

def fit_all_news(save_path, limit=200):
    try:
        print("fitting started")
        docs = [x[-1] for i, x in enumerate(get_recent_new_generator()) if i != limit-1]
        vectorizer = TfidfVectorizer()
        vectorizer.fit(docs)
        
        print("done")   
        joblib.dump(vectorizer, save_path)
        print("saved")
        
    except Exception as e:
        print(f"error happend: {e}")
        logging.error(f"error happend: {e}")
    except:
        print("error happend")
        logging.error("error happend")

def fit_news(content,
             save_path: str="tfidf_vectorizer.pkl"):
    try:
        vectorizer = joblib.load(save_path)
        vectorizer.fit(content) 
        
        joblib.dump(vectorizer, save_path)
        logging.info("vectorizer upgraded!")
         
    except Exception as e:
        print(f"error happend: {e}")
    except:
        print("error happend")
        
    

if __name__ == "__main__":
    fit_all_news("tfidf_vectorizer.pkl")