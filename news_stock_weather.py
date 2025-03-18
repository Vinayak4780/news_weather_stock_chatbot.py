import streamlit as st
import requests
from bs4 import BeautifulSoup
import feedparser
import re
import urllib.parse
from datetime import datetime
import pytz
import nltk
from string import punctuation
from nltk.corpus import stopwords
# Download necessary resource
import string

import os

# Text Preprocessing Function
def preprocess_text(text):
    text = text.lower()
    
    # Remove special characters and numbers
    tokens = re.sub(r'[^a-z\s]', '', text)
     
     # Remove stopwords and punctuation
    stop_words = set(stopwords.words("english"))
    tokens = [word for word in tokens if word not in stop_words and word not in punctuation]
    

     # ✅ Remove extra whitespace and join tokens back to string
    return " ".join(tokens)
# News Function
def get_news(count=5):
    feed = feedparser.parse("http://feeds.bbci.co.uk/news/rss.xml")
    return [(entry.title, entry.link) for entry in feed.entries[:count]]

def get_news_insights(news_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(news_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")
    insights = " ".join([p.text for p in paragraphs[:3]])
    return insights if insights else "No insights available."

# Get Weather
def get_weather(city):
    try:
        url = f"https://wttr.in/{city}?format=%C|🌡️ Temperature: %t|💧 Humidity: %h|💨 Wind: %w"
        response = requests.get(url)
        if response.status_code == 200 and response.text.strip():
            weather_data = urllib.parse.unquote(response.text.strip())
            parts = weather_data.split("|")
            weather_condition = parts[0].strip()
            temperature = parts[1].replace("🌡️ Temperature:", "").strip()
            humidity = parts[2].replace("💧 Humidity:", "").strip()
            wind = parts[3].replace("💨 Wind:", "").strip()
            return (f"🌤️ {weather_condition}\n"
                    f"🌡️ **Temperature:** {temperature}\n"
                    f"💧 **Humidity:** {humidity}\n"
                    f"💨 **Wind:** {wind}")
        else:
            return "❌ Could not retrieve weather data. Please check the city name."
    except requests.exceptions.RequestException as e:
        return f"❌ Network error: {e}"

# Get Stock Price
def get_stock_symbol(company_name):
    url = f"https://www.nseindia.com/api/search/autocomplete?q={company_name}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers)  # Establish session
        response = session.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if "symbols" in data and len(data["symbols"]) > 0:
                return data["symbols"][0]["symbol"]  # Return first matched symbol
            else:
                return None
        else:
            return None
    except Exception:
        return None

# ✅ Function to get stock price (Handles both symbols & names)
def get_nse_stock_price(query):
    stock_symbol = query.upper()  # Assume query is stock symbol initially

    # If input is a company name, fetch its symbol
    if not re.match(r"^[A-Z]{2,6}$", stock_symbol):  
        stock_symbol = get_stock_symbol(query)
        if not stock_symbol:
            return f"❌ Could not find stock symbol for '{query}'. Try using the stock symbol."

    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers={"User-Agent": "Mozilla/5.0"})
        nse_url = f"https://www.nseindia.com/api/quote-equity?symbol={stock_symbol}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com"}
        response = session.get(nse_url, headers=headers, timeout=5)

        if response.status_code != 200:
            return f"❌ Error: Could not retrieve stock data for '{stock_symbol}'."

        data = response.json()
        if "priceInfo" not in data:
            return f"❌ Stock price not found for '{stock_symbol}'."

        stock_price = data["priceInfo"]["lastPrice"]
        prev_close = data["priceInfo"]["previousClose"]
        price_change = stock_price - prev_close
        percent_change = (price_change / prev_close) * 100
        change_sign = "↑" if price_change > 0 else "↓" if price_change < 0 else "→"

        return (f"📈 {stock_symbol} Stock Price: ₹{stock_price}\n"
                f"📉 1-Day Change: {change_sign} ₹{abs(price_change):.2f} ({change_sign} {abs(percent_change):.2f}%)")

    except requests.exceptions.RequestException as e:
        return f"❌ Network error: {e}"

# Streamlit UI
st.title("🤖 AI Chatbot")
st.write("Ask me about news, stocks, weather, Wikipedia, currency exchange, or sports scores.")
# ✅ Small Columns for Stock & Weather (Above the Query)
col1, col2 = st.columns([0.2, 0.2])  # Adjusted size for better spacing

with col1:
    st.subheader("📉 Stock")
    col_stock, _ = st.columns([0.6, 0.4])  # Reduce input field width
    with col_stock:
        stock_name = st.text_input("Enter Stock Symbol:", key="stock_input_unique", placeholder="e.g., TCS", label_visibility="collapsed")

    # ✅ Fetch stock price when user presses "Enter"
    if stock_name:
        st.write(get_nse_stock_price(stock_name))  

with col2:
    st.subheader("☀️ Weather")
    col_weather, _ = st.columns([0.6, 0.4])  # Reduce input field width
    with col_weather:
        city_name = st.text_input("Enter City Name:", key="weather_input_unique", placeholder="e.g., Delhi", label_visibility="collapsed")

    # ✅ Fetch weather when user presses "Enter"
    if city_name:
        st.write(get_weather(city_name)) 


# ✅ Main Query Input Below Stock & Weather
user_input = st.text_input("Enter your query:", key="query_input_unique")
news_count = st.number_input("How many news articles?", min_value=1, max_value=50, value=5)

if "history" not in st.session_state:
    st.session_state.history = []

if user_input:
    cleaned_input = preprocess_text(user_input)  # ✅ Apply full preprocessing
    response = ""

    if "news" in user_input:
        st.subheader("📰 Latest News")
        news_list = get_news(news_count)
        response = "\n".join([f"- {title}" for title, _ in news_list]) 
        for idx, (title, link) in enumerate(news_list):
            if st.button(title, key=f"news_{idx}"):
                st.subheader("🔍 News Insights")
                insights = get_news_insights(link)
                st.write(insights)
                st.markdown(f"[Read full article]({link})")