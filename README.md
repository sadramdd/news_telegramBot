# 📰 Persian Newsender Telegram Bot

A smart Persian Telegram bot that delivers the latest news to users with personalized features — built using Python and the `telebot` library.

## 🚀 Features

- 📩 **Send News Automatically**
  - Delivers news directly to your Telegram based on your preferences.
  
- 🧠 **Machine Learning Personalization**
  - Analyzes what you've read and your feedback to improve future suggestions.
  
- 📰 **Choose News Format**
  - Get either **summarized** or **full** news articles.

- ⏰ **Schedule News Delivery**
  - Set specific times to receive news updates.

- 💾 **Save News for Later**
  - Bookmark articles inside Telegram.

- ❤️ **Pick Favorite Topics**
  - Choose from a list of interests to get topic-based news.

- 🗃️ **MySQL Integration**
  - Stores user preferences, saved news, and feedback securely in a MySQL database.

- 🔗 **ISNA RSS Feed**
  - Sources news from ISNA's official feed for timely updates.

---

## 🧱 Built With

- **Python**
- **Telebot (PyTelegramBotAPI)**
- **MySQL**
- **ISNA RSS**
- **Scikit-learn / other ML tools** 

---

## 🛠️ How to Run

```bash
git clone https://github.com/yourusername/persian-news-bot.git
cd persian-news-bot
python3 -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt
python bot.py