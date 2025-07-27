import DML
from config import BOTTOKEN, topics, spam_rate, spam_time_rate
import recommendation
from models import sentiment_model
import telebot
from telebot import types
import time
import datetime
from telebot.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, KeyboardButton, ReplyKeyboardMarkup
import logging
import threading
import sys
print("importing done.")
telebot_logger = logging.getLogger("TeleBot")
telebot_logger.setLevel(logging.CRITICAL)

# Remove any handlers attached to it
for handler in telebot_logger.handlers:
    telebot_logger.removeHandler(handler)
    
    
urllib_logger = logging.getLogger("urllib3.connectionpool")
urllib_logger.setLevel(logging.CRITICAL)

# Remove any handlers attached to it
for handler in urllib_logger.handlers:
    urllib_logger.removeHandler(handler)
    
    
    
sql_logger = logging.getLogger("mysql.connector")
sql_logger.setLevel(logging.CRITICAL)

# Remove any handlers attached to it
for handler in sql_logger.handlers:
    sql_logger.removeHandler(handler)   
     
    
def escape_markdown(text):
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return ''.join([f"\\{x}" if x in escape_chars else x for x in text])
            



# User status storage
status = {} # {cid: status, ...}

spammer_identifier = {}# {cid: {"previous_time": None, "rate": 0, "has_sent_ban_message": False}, ...}

selected_topics_helper = {} # {cid: [selected topics, ...]}

saved_news_to_img = {} # {saved_news_massege_id: saved_news_image_massage_id, ...}

selected_time_helper = {} # {cid: [selected hours...]}


bot = telebot.TeleBot(BOTTOKEN)
print("connecting to api done")

commands = {
    "راهنما ❓"  :   "نمایش کامند های موجود",
    "/start" :   "شروع کردن ربات",
    "خبر جدید 📰" :  "گرفتن خبر جدید",
    "حالت اخبار 📳" : "تغییر حالت اخبار",
    "مشاهده ذخیره شده 📂" : "دیدن اخبار ذخیره شده",
    "تغییر سرفصل ها 🔝": "تغییر سرفصل های مورد علاقه",
    "زمان گذاری ⏲️" : "گذاشتن زمان برای ارسال خبر"
}

bot.set_my_commands([
    types.BotCommand("start", "شروع")
])


print("bot started \n---------------------------")
logging.info("bot started")



def listen(messages):
    for m in messages:
        try:
            cid = m.chat.id
            text= m.text
            username = m.from_user.username
            (f"userid: {cid}, user name: {username}, message: {text}")
            logging.info(f"userid: {cid}, user name: {username}, message: {text}")
        except Exception as e:
            print(f"error happend in listener: {e}")
            logging.error(f"error happend in listener: {e}")


bot.set_update_listener(listener=listen)





def add_spam(cid):
    """
    this function adds newest user message to spam detection dictionary
    """
    try:
        global spammer_identifier
        spammer_identifier.setdefault(cid, {"previous_time": None, "rate": 0, "has_sent_ban_message": False})
        
        now = time.time()
        pre_time = spammer_identifier[cid]["previous_time"]
        
        if pre_time is not None:
            diff = now - pre_time
            
            if diff <= spam_time_rate:
                spammer_identifier[cid]["rate"] += 1
            else:
                bonus = (diff * 0.5) // 2
                spammer_identifier[cid]["rate"] = max(0, spammer_identifier[cid]["rate"] - bonus)
        else:
            spammer_identifier[cid]["rate"] = 0

        spammer_identifier[cid]["previous_time"] = now
    except Exception as e:
        print(f"error hapend while adding spams: {e}")

def check_for_spam(chat_id):
    try:
        if spammer_identifier.get(chat_id)["rate"] > spam_rate:
            if not spammer_identifier[chat_id]["has_sent_ban_message"]:
                bot.send_message("💢شما بخاطر اسپم دادن مسدود شدید💢")
                spammer_identifier[chat_id]["has_sent_ban_message"] = True
            logging.DEBUG(f"user: {chat_id} is BANNED")
            return True
        return False
    except:
        return False


def send_news_function(cid,image_url, new,
                       title, markup=None, sentiment_message="",
                       new_code=None, firsttime=True, picture_mid=None,
                       text_mid=None, save_interacion=True):
    new_text = f"{new} \n " + sentiment_message 
    sent = False
    if len(new_text) >= 4096:
        return False
    try:
        if not firsttime:
            media = types.InputMediaPhoto(media=image_url)
            # edit photo
            bot.edit_message_media(media=media, chat_id=cid, message_id=picture_mid)
            #edit photo caption
            bot.edit_message_caption(f"**{escape_markdown(title)}**", cid, picture_mid, parse_mode="MarkdownV2")
            # edit text messgae
            bot.edit_message_text(new_text,cid,text_mid, reply_markup=markup)

        else:
            # send photo with caption = title
            picture = bot.send_photo(cid, image_url, caption=f"**{escape_markdown(title)}**", parse_mode="MarkdownV2") 
            # send text message
            message = bot.send_message(cid, new_text,reply_markup=markup)
            # save the text mid to picture mid
            saved_news_to_img[message.message_id] = picture.message_id
            sent = True
        
    except Exception as e:
        print(f"photo sending failed: {e}")        
        if not firsttime:
            # just edit the text message because there is no image 
            bot.edit_message_text(new_text,cid,text_mid, reply_markup=markup)
            
            try:
                bot.delete_message(cid, picture)
            except Exception as e:
                print(f"can't delete news photo: {e}")
                logging.ERROR(f"can't delete news photo: {e}")
                
        else:
            # just send the text message
            bot.send_message(cid, new_text, reply_markup=markup)
            sent = True
            
            
    if save_interacion:
        DML.add_interaction(cid, int(new_code), "natural")
    return sent

#--------------------------------------------

# help command handler
@bot.message_handler(func= lambda x: x.text == "راهنما ❓")
def command_help(m):
    cid = int(m.chat.id)

    if check_for_spam(cid): return
    add_spam(cid)
    
    status.pop(cid,None)
    
    help_text = "کامند های موجود: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += f"{key} : {commands[key]} \n \n"
    bot.send_message(cid, help_text + " ")  # send the generated help page
  
#------------------------------------------------    


@bot.message_handler(func= lambda x: x.text == "حالت اخبار 📳")
def command_news_mode(m):
    cid = int(m.chat.id)
    status.pop(cid,None)
    if check_for_spam(cid): return
    add_spam(cid)
    mode_markup = InlineKeyboardMarkup()
    mode_btn1 = InlineKeyboardButton("خلاصه خبر 🗞️", callback_data="change_to_summarized_news_mode")
    mode_btn2 = InlineKeyboardButton("خبر کامل 📰", callback_data="change_to_whole_news_mode")
    mode_markup.row(mode_btn1, mode_btn2)
    bot.send_message(cid, "کدام نوع از خبر را میخواهید؟", reply_markup=mode_markup)

# button callback handler
@bot.callback_query_handler(func= lambda call: "news_mode" in call.data)
def handle_mode_buttons(call):
    user_id = int(call.from_user.id)
    cid = int(call.message.chat.id)
    if call.data == "change_to_summarized_news_mode":
        bot.answer_callback_query(call.id, "حالت اخبار به خلاصه تغییر کرد ✅")
        DML.change_news_mode_byTelegramid(user_id, "summarize")   
    else:
        bot.answer_callback_query(call.id, "حالت اخبار به معمولی تغییر کرد ✅")
        DML.change_news_mode_byTelegramid(user_id, "full")        
        

#--------------------------------------      
        
        
def gen_saved_page(cid, user_id, page: int, firsttime: bool=False, mid=None, picture_mid=None, call_id=None):
    news = [x[0] for x in DML.get_saved_newsbyTelegramid_generator(user_id)] # because the generator yields tuples
    
    length = len(news)
    
    if length <= 0:
        bot.send_message(cid, "شما خبر ذخیره شده ای ندارید")
        return
    
    if length < page:
        bot.answer_callback_query(cid, "")
    
    new_code = news[page-1]
    saved_markup = InlineKeyboardMarkup()
    saved_mode_btn1 = InlineKeyboardButton("⬅️ خبر قبلی", callback_data=f"cspt_{page - 1}_saved")
    saved_mode_btn2  = InlineKeyboardButton(f"صفحه {length} از {page}", callback_data="NOTHING1")
    saved_mode_btn3  = InlineKeyboardButton("خبر بعدی ➡️", callback_data=f"cspt_{page + 1}_saved")
    saved_mode_btn4  = InlineKeyboardButton("رفتن به اولین صفحه 1", callback_data=f"cspft_1_current_{page}_saved")
    saved_mode_btn5 = InlineKeyboardButton(f"رفتن به آخرین صفحه {length}", callback_data=f"cspft_{length}_current_{page}_saved")
    
    saved_markup.add(saved_mode_btn1, saved_mode_btn2, saved_mode_btn3)
    saved_markup.row(saved_mode_btn4, saved_mode_btn5)
    news_tuple = DML.get_new_byNewcode(new_code)
    title = news_tuple[3]
    if DML.get_user_news_mode_byTelegramid(user_id)[0] == "summarize":
        new = news_tuple[2]
    else:
        new = news_tuple[1]
    photo_URL = news_tuple[-2]
    
    text = f"{title} \n {new} \n"        
    send_news_function(cid, photo_URL,new,
                       title, saved_markup,
                       new_code=new_code,firsttime=firsttime,
                       picture_mid=picture_mid,text_mid=mid, save_interacion=False)
    

        
@bot.message_handler(func= lambda x: x.text == "مشاهده ذخیره شده 📂")
def command_see_saved(m):
    cid = int(m.chat.id)
    user_id = int(m.from_user.id)
    
    status.pop(cid,None)

    if check_for_spam(cid): return
    add_spam(cid)
    gen_saved_page(cid,user_id, 1, firsttime=True)
        
        
@bot.callback_query_handler(func= lambda call: "saved" in call.data)
def change_saved_markup(call):
    mid = call.message.message_id
    user_id = call.from_user.id
    cid = call.message.chat.id
    data = str(call.data)
    pic_mid = saved_news_to_img.get(mid)
    if data.startswith("cspt"):
        page = int(data.split("_")[-2])
        
        if page != 0:
            gen_saved_page(cid,user_id, page, firsttime=False, picture_mid=pic_mid, mid=mid, call_id=call.id)
        else:
            bot.answer_callback_query(call.id, "کمتر از صفر نمیشود")
            
    else:
        try:
            current_page = int(data.split("_")[-2])
            
            toPage = int(data.split("_")[1])
            
            if current_page == toPage:
                bot.answer_callback_query(call.id, "شما در آن صفحه هستید")
                
            else:
                gen_saved_page(cid,user_id, toPage, firsttime=False,picture_mid=pic_mid ,mid=mid, call_id=call.id)
        except Exception as e:
            print(f"error happend while handling saved news: \n {e}")
            logging.ERROR(f"error happend while handling saved news: \n {e}")
            
            
        
        
    
#--------------------------------------

    
        
# getting news handler
@bot.message_handler(func= lambda x: x.text == "خبر جدید 📰")
def send_news(m, cid=None):
    global topics
    if not cid:
        cid = int(m.chat.id)
    
    status.pop(cid,None)
    
    if check_for_spam(cid): return
    
    add_spam(cid)
    bot.send_message(cid, "لطفا منتظر بمانید ⭕")

    while True:
        bot.send_chat_action(chat_id=cid, action="typing")
        recommended_topic = recommendation.recommend_topic(cid, topics)
        
        print(f"recommended topic: {recommended_topic}")
        
        if recommended_topic:
            new_code = recommendation.recommend_news(recommended_topic, cid)
            if not new_code:
                
                bot.send_message(cid, "در حال حاضر خبر جدیدی نیست 🔕")
                return
        else:
            
            bot.send_message(cid, "در حال حاضر خبر جدیدی نیست 🔕")
            return
        try:
            new_tuple = DML.get_new_byNewcode(new_code)
                
            if DML.get_user_news_mode_byTelegramid(cid)[0] == "full":
                new = new_tuple[1]
            else:
                new = new_tuple[-1]
                
            title =  new_tuple[3]  
            image_url = new_tuple[-2]
            
        except Exception as e:
            logging.error(f"error happend while trying to send news : {e}")
            print(f"error happend while trying to send news : {e}")
            bot.send_message(cid, "در حال حاضر خبر جدیدی نیست 🔕")
            return
            
        markup = InlineKeyboardMarkup()
        btn1 = InlineKeyboardButton("📂 ذخیره", callback_data=f"response_save_new_{new_code}")
        btn2 = InlineKeyboardButton("👍 مثبت", callback_data=f"positive_response_{new_code}")
        btn3 = InlineKeyboardButton("👎 منفی", callback_data=f"negative_response_{new_code}")
        btn4 = InlineKeyboardButton("📝 نوشتن نظر", callback_data=f"write_response_{new_code}")
        title  = "📰 " + title
        markup.add(btn1)
        markup.row(btn2,btn3)
        markup.add(btn4)
        message = "نظرتان راجب این خبر چه بود? 🔔"
        sent = send_news_function(cid, image_url, new, title, markup, message, new_code)
        if sent: break
        DML.delete_news(new_code)
        
    status[cid] = f"wait_response_{new_code}"
    

user_minute_helper = {}  # {cid: x_minutes_ago_sent}
user_hour_helper = {}  # {cid: {has_sent_in_hour: bool, hour:int(hour)}}
def check_for_time(): 
    """
    finds and sends news to users in times they set every 10 
    """                
    while True: 
            #task 1, get all users minutes and hours (if they have) and store in dictionaries: {cid: [hours...]} and {cid: minute}
            all_users = DML.get_users()
            hours = {}
            minute = {}
            
            try:
                for user in all_users:
                    cid = int(user[0])
                    # check if user set minutes or not and add if true
                    user_minutes = DML.get_times(cid, mode="minutes")
                    if user_minutes:
                        minute[cid] = user_minutes[0]
                        
                    #check if user has set hours
                    user_hours = DML.get_times(cid, mode="hour")
                    if user_hours:
                        for hour in user_hours:
                            hours.setdefault(cid, [])
                            hours[cid].append(hour)
            except Exception as e:
                #catching any errors and showing with caused line
                _, _, exc_traceback = sys.exc_info()
                line_number = exc_traceback.tb_lineno
                print(f"error happend in while loop task 1: {e} line: {line_number}")
                logging.error(f"error happend in while loop task 1: {e} line: {line_number}")
            
            try:
                #task2, check for hours
                for cid, hours_list in hours.items():
                    now = datetime.datetime.now().hour
                    user_hour_helper.setdefault(cid, {"has_sent_in_hour": False, "hour": now})
                    
                    if user_hour_helper[cid]["hour"] != now:
                        user_hour_helper[cid] = {"has_sent_in_hour": True, "hour": now} 
                        
                    
                    if now in hours_list and not user_hour_helper[cid]["has_sent_in_hour"]:
                        try:
                            send_news(None, cid=cid)
                        except Exception as e:
                            bot.send_message(cid, "در حال حاضر خبر جدیدی نیست 🔕")
                        print("news sent")
                        user_hour_helper[cid] = {"has_sent_in_hour": True, "hour": now} 
                        
            except Exception as e:
                #catching any errors and showing with caused line
                _, _, exc_traceback = sys.exc_info()
                line_number = exc_traceback.tb_lineno
                print(f"error happend in while loop task 2: {e} line: {line_number}")
                logging.error(f"error happend in while loop task 2: {e} line: {line_number}")
                
            try:           
                #task3, check for minute
                for cid, minute in minute.items():
                    user_minute_helper.setdefault(cid, 0)
                    if user_minute_helper[cid] >= minute * 60: # convert minutes into second beacuse last sent are stred as seconds
                        
                        try:
                            send_news(None, cid=cid)
                            print("news sent in minutes")
                        except Exception as e:
                            bot.send_message(cid, "در حال حاضر خبر جدیدی نیست 🔕")
                            
                        user_minute_helper[cid] = 10
                    else:
                        user_minute_helper[cid] += 10
                time.sleep(10)
            
            except Exception as e:
                #catching any errors and showing with caused line
                _, _, exc_traceback = sys.exc_info()
                line_number = exc_traceback.tb_lineno
                print(f"error happend in  while loop task 3: {e} line: {line_number}")
                logging.error(f"error happend in while loop task 3: {e} line: {line_number}")
                       
                       
                       
#error happend in while loop task 2: cannot access local variable 'user_id' where it is not associated with a value
#error happend in  while loop task 3: '>=' not supported between instances of 'int' and 'list' 
                       
    
# response/save callback handler
@bot.callback_query_handler(func=lambda call: "response" in call.data)
def handle_response_callback(call):
    user_id = int(call.from_user.id)
    mid = int(call.message.message_id)
    cid = int(call.message.chat.id)
    data = str(call.data)
    if data.startswith("response_save_new_"):
        
        new_code = int(data.split("_")[-1])
        saved_news = [x[0] for x in DML.get_saved_newsbyTelegramid_generator(user_id)] # because the generator yields tuples
        if new_code not in saved_news:
            DML.add_saved_news(new_code, user_id)
            bot.answer_callback_query(call.id, "ذخیره شد ✔️")
        else:
            bot.answer_callback_query(call.id, "این خبر قبلا ذخیره شده 💢")
            
        
    elif call.data.startswith("positive_response_"):
        
        new_code = data.split("_")[-1]
        
        DML.change_interaction(user_id, int(new_code), "positive")
        bot.answer_callback_query(call.id, "از اهمیت شما متشکریم 🎗️")
        bot.edit_message_reply_markup(cid, mid, 
                                      reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("📂 ذخیره", callback_data=f"response_save_new_{new_code}")))
        status.pop(cid,  None)   
        
    elif call.data.startswith("negative_response_"):
        
        new_code = data.split("_")[-1]
        
        DML.change_interaction(user_id, int(new_code), "negative")
        bot.answer_callback_query(call.id, "از اهمیت شما متشکریم 🎗️")
        bot.edit_message_reply_markup(cid, mid, 
                                      reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("📂 ذخیره", callback_data=f"response_save_new_{new_code}")))
        status.pop(cid,  None)   
        
    elif data.startswith("write_response_"):
        new_code = data.split("_")[-1]
        bot.send_message(cid, "📝نظر خود را بنویسید: ")
        status[cid] = f"{mid}_wait_comment_{new_code}"
   

# writing response handler
@bot.message_handler(func= lambda m: "comment" in status.get(m.chat.id, " "))
def store_new_interaction(m):
    """
    if users status if about writing their response to the shown news,
    this function will save the entered response analyse to datatbase 
    
    """
    try:
        cid = int(m.chat.id)
        mid = status[cid].split("_")[0]

        if check_for_spam(cid): return
        
        add_spam(cid)
        pred = sentiment_model.predict(m.text, return_soft_en_prediction=True) # predict the emotion of sentence (positive/negative)
        
        new_code = status[cid].split("_")[-1]
        DML.change_interaction(cid, int(new_code), str(pred)) # store to database
        
        bot.send_message(cid, "از اهمیت شما متشکریم 🎗️") 
        bot.edit_message_reply_markup(cid, mid, 
                                      reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("📂 ذخیره", callback_data=f"response_save_new_{new_code}")))
        
        status.pop(cid) # clear users status
        
    except Exception as e:
        print(f"error happend while handling user comment: \n {e}")
        logging.ERROR(f"error happend while handling user comment: {e}")

#-------------------------------------


def gen_topic_markup(cid, selected_topics: list,all_topics: list,
                     new=False,
                     text=None,
                     mid=None):
    new_markup = InlineKeyboardMarkup()

    for topic in all_topics:
        emoji = "✖️" if topic not in selected_topics else "✔️"
        action = "add" if topic not in selected_topics else "delete"            
        new_markup.add(InlineKeyboardButton(f"{topic} {emoji}",
                                            callback_data=f"{action}_topic_{topic}"))
        
    new_markup.add(InlineKeyboardButton("تایید و اضافه کردن سرفصل های مورد علاقه ⏭️", callback_data=f"confirm_topics"))
    
    new_markup.add(InlineKeyboardButton("لغو فرایند 🔙",callback_data=f"cancel_topic"))
    if not new:
        bot.edit_message_reply_markup(cid, mid, reply_markup=new_markup)
    else:
        bot.send_message(cid, text, reply_markup=new_markup)
    
    
@bot.message_handler(func= lambda x: x.text == "تغییر سرفصل ها 🔝")
def command_topic(m):
    try:
        global topics
        cid = int(m.chat.id)
        user_id = int(m.from_user.id)
        
        
        if check_for_spam(cid): return
        
        add_spam(cid)
        text2 = "شما میتونید سرفصل های مورد علاقع خود را انتخاب کنید"
        
        topics_markup = InlineKeyboardMarkup()
        
        if not DML.does_telegram_id_exists(user_id):
            DML.add_user(user_id, datetime.datetime.now())
            logging.info(f"New user added, user_name: , user_id: {user_id}")
            for topic in topics:
                topics_markup.add(InlineKeyboardButton(f"{topic} ✖️",
                                                    callback_data=f"add_topic_{topic}"))
                
            topics_markup.add(InlineKeyboardButton("تایید و اضافه کردن سرفصل های مورد علاقه ⏭️",callback_data=f"confirm_topics"))
            
            topics_markup.add(InlineKeyboardButton("لغو فرایند 🔙",callback_data=f"cancel_topic"))
            
            bot.send_message(cid, text2, reply_markup=topics_markup)
            selected_topics_helper[user_id] = []
            
        else:
            user_dictionary = DML.get_user_info(user_id)
            if user_dictionary:
                selected_topics = user_dictionary["topics"]
            else:
                selected_topics = []
            selected_topics_helper[user_id] = selected_topics
            gen_topic_markup(cid, selected_topics ,topics,  new=True, text=text2)
        
        if status.get(cid) != "wait_response":
            status.pop(cid, None)
            
    except Exception as e:
        print(f"error happened while choosing topics: {e}")
        logging.error(f"error happened while choosing topics: {e}")

                
# Default start and other things handler
@bot.message_handler(commands=["start"])
def command_start(m):
    """
    handles the /start command and new user signup
    
    """
    global topics
    
    cid = int(m.chat.id)
    
    status.pop(cid,None)
    
    text = """
    📢 به ربات خبررسان خوش آمدید!
    با استفاده از این ربات می‌توانید به راحتی به اخبار روز دسترسی داشته باشید، آن‌ها را ذخیره کنید، نظر خود را ثبت کنید و حتی حالت نمایش خبر (خلاصه یا کامل) را تغییر دهید.
    📌 امکانات ربات:
    - دریافت اخبار جدید بر اساس علایق شما
    - ذخیره‌سازی اخبار برای مطالعه بعدی
    - ثبت بازخورد مثبت، منفی یا نوشتاری برای هر خبر
    - تغییر حالت نمایش به خلاصه یا کامل
    - مرور اخبار ذخیره‌شده با قابلیت ورق‌زدن بین صفحات
    🧠 ربات با یادگیری از بازخوردهای شما، اخبار بهتری پیشنهاد خواهد داد!
    """
    
    
    if check_for_spam(cid): return
    

    add_spam(cid)
    keyboard_markup = ReplyKeyboardMarkup()
    for command in commands:
        keyboard_markup.add(KeyboardButton(command))
    
    bot.send_message(cid, text, reply_markup=keyboard_markup)
    command_topic(m)
    


@bot.callback_query_handler(func=lambda call: "topic" in call.data)
def handle_topic_callback(call):
    global topics
    cid = int(call.message.chat.id)
    mid = call.message.message_id
    if call.data.startswith("add"):
        
        selected_topic = call.data.split("_")[2]
        selected_topics_helper[cid].append(selected_topic)
        selected_topics = selected_topics_helper[cid]
        gen_topic_markup(cid, selected_topics,topics, mid=mid) 
        bot.answer_callback_query(call.id, "سرفصل انتخاب شد✔️")
        
    elif call.data.startswith("delete"):
        
        selected_topic = call.data.split("_")[2]
        selected_topics_helper[cid].remove(selected_topic)
        selected_topics = selected_topics_helper[cid]
        gen_topic_markup(cid, selected_topics,topics, mid=mid)
        bot.answer_callback_query(call.id, "سرفصل حذف شد✖️")
        
    elif call.data.startswith("confirm"):
        DML.delete_user_topics(cid)
        selected = selected_topics_helper[cid]
        for topic in selected:
            DML.add_user_topic_ByTelgramid(cid, topic)
        bot.edit_message_reply_markup(chat_id=cid, message_id=mid, reply_markup=None)
        selected_topics_helper.pop(cid)
        
    else:
        bot.edit_message_reply_markup(chat_id=cid, message_id=mid, reply_markup=None)
        selected_topics_helper.pop(cid)
    

#-----------------------------------------------


def gen_a_markup():
    # ask for one of options
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("⌚ انتخاب به صورت دقیقه ای (هر چند دقیقه یک بار) ⌚", callback_data="time_minutes")
    btn2 = InlineKeyboardButton("🕛 انتخاب به صورت ساعتی🕛", callback_data="time_hour")
    btn3 = InlineKeyboardButton("لغو فرایند 🔙", callback_data="cancel_time")
    markup.add(btn1)
    markup.add(btn2)
    markup.add(btn3)
    return markup

def gen_b_markup(selected_hours):
    #show 24hours of day
    markup = InlineKeyboardMarkup()
    for clock in range(24):
        emoji = "✖️" if clock not in selected_hours else "✔️"
        action = "add" if clock not in selected_hours else "delete"    
        btn = InlineKeyboardButton(f"{clock} ساعت {emoji}", callback_data=f"{action}_time_{clock}")
        markup.add(btn)
    btn = InlineKeyboardButton("بازگشت 🔙", callback_data="time_back")
    markup.add(btn)
    btn = InlineKeyboardButton("تایید ☑️", callback_data="confirm_time")
    markup.add(btn)
    return markup   
    
def gen_c_markup(cid):
    #ask for input
    markup = InlineKeyboardMarkup()
    btn = InlineKeyboardButton("بازگشت 🔙", callback_data="time_back")
    markup.add(btn)
    return markup

@bot.message_handler(func=lambda message: message.text == "زمان گذاری ⏲️")
def set_timer(m, cid=None):
    if m:
        cid = int(m.chat.id)
    
    if check_for_spam(cid): return
    add_spam(cid)
    A_markup = gen_a_markup()
    bot.send_message(cid, "⏰لطفا یکی از گزینه ها رو انتخاب کنید⏰", reply_markup=A_markup)


@bot.callback_query_handler(func=lambda call: "time" in call.data)
def handle_time_callback(call):
    try:
        cid = int(call.message.chat.id)
        mid = int(call.message.message_id)
        data = call.data
        if data == "invoke_timer_func":
            set_timer(None, cid=cid)
        elif data == "time_hour":
            if DML.has_times(cid):
                selected = DML.get_times(cid)
                selected_time_helper[cid] = selected
                
            else:
                selected = []
                selected_time_helper[cid] = selected
            B_markup = gen_b_markup(selected)
            bot.edit_message_text("🎗️ ربات در هر ساعتی که انتخاب کنید برای شما خبر میفرستد 🎗️", cid, mid, reply_markup=B_markup)
            
        elif data == "time_minutes":
            C_markup = gen_c_markup(cid=cid)
            bot.edit_message_text("(دقیقه باید کمتر از 500 باشد) لطفا دقیقه مورد نظر خود را به انگلیسی بنویسید", cid, mid, reply_markup=C_markup)
            status[cid] = f"type_minutes_{call.id}_{mid}"
            
        elif data == "time_back":
            A_markup = gen_a_markup()
            bot.edit_message_text("⏰لطفا یکی از گزینه ها رو انتخاب کنید⏰", cid, mid, reply_markup=A_markup)
            
        elif data == "cancel_time":
            bot.edit_message_text("فرایند لغو شد", cid, mid, reply_markup=None)
            
        elif data == "confirm_time":
            hours = selected_time_helper.get(cid)
            if hours:
                if DML.has_times(cid):
                    DML.delete_time(cid, mode="hour")
                for hour in hours:
                    DML.add_times(cid, int(hour), mode="hour")
                bot.edit_message_text("☑️ ساعت ها با موفقیت ثبت شد ☑️",cid, mid, reply_markup=None)
                selected_time_helper.pop(cid, None)
            else:
                bot.edit_message_text("☑️ ساعت ها با موفقیت ثبت شد ☑️",cid, mid, reply_markup=None)
                selected_time_helper.pop(cid, None)
                #bot.answer_callback_query(call.id, "💢 باید حداقل یک گزینه انتخاب شود 💢")      
        else:
            hour = int(data.split("_")[-1])
            if data.split("_")[0] == "add":
                selected_time_helper[cid].append(hour)
                selected_hours = selected_time_helper[cid]
                bot.edit_message_reply_markup(cid, mid, reply_markup=gen_b_markup(selected_hours))
                bot.answer_callback_query(call.id, "☑️ ساعت انتخاب شد ☑️")      
            else:
                selected_time_helper[cid].remove(hour)
                selected_hours = selected_time_helper[cid]
                bot.edit_message_reply_markup(cid, mid, reply_markup=gen_b_markup(selected_hours))
                bot.answer_callback_query(call.id, "☑️ ساعت حذف شد ☑️")      
        
    except Exception as e:
        print(f"error happend while handling time callbacks: {e}")
        logging.error(f"error happend while handling time callbacks: {e}")


@bot.message_handler(func= lambda x: status.get(x.chat.id, " ").startswith("type_minutes"))
def handle_minutes_message(message):
    try:
        cid = int(message.chat.id)
        minutes = str(message.text)

        callid = status.get(message.chat.id).split("_")[-2]
        mid = status.get(message.chat.id).split("_")[-1]
        if not minutes.isdigit():
            bot.answer_callback_query(callid, "💢 لطفا دقیقه به انگلیسی باشد 💢")
            status.pop(cid, None)
            return
        if int(minutes) >= 500:
            bot.answer_callback_query(callid, "💢 دقیقه ها باید کمتر از 500 باشند 💢")
            status.pop(cid, None)
            return
        
        if DML.has_times(cid):
            DML.delete_time(cid, mode="minutes")
        added = DML.add_times(cid, int(minutes), mode="minutes")
        if added:
            bot.answer_callback_query(callid, f"✔️ ربات هر {minutes} دقیقه برای شما پیام ارسال خواهد کرد")
            bot.edit_message_text(f" :برای تغییر زمان گذاری \n ✔️ زمان گذاری با موفقیت انجام شد ✔️", cid, mid, reply_markup="invoke_timer_func")
        else:
            bot.answer_callback_query(callid, "💢در حال حاضر مشکلی پیش آمده💢")
        status.pop(cid, None)
    except Exception as e:
        print(f"error happend while handling users minute input: {e}")
        logging.error(f"error happend while handling users minute input: {e}")
#-----------------------------------------------



@bot.message_handler(func=lambda m: True)
def handle_all(m):
    cid = int(m.chat.id)

    if check_for_spam(cid): return
    add_spam(cid)
    bot.send_message(cid, "لطفا فقط از دستور بات استفاده نمایید. 🎗️")
    
threading.Thread(target=check_for_time).start()
    

#----------------------------------------------
#try/except for catching disconnection errors at polling
while True:
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"polling crashed: {e}")
        logging.error(f"polling crashed: {e}")
        print("\n\n --------------------------- \n\n")
        time.sleep(5)


#----------------------------------------------------