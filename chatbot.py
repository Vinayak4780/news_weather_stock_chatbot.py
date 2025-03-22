import streamlit as st
import requests
from bs4 import BeautifulSoup
import feedparser
import re
import urllib.parse
from datetime import datetime
import pytz
import nltk
import yfinance as yf
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

import pandas as pd
import yfinance as yf
import pandas as pd
import yfinance as yf
import streamlit as st
# Load NSE Stock List
def get_nse_stock_list():
    try:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"  # NSE Official Data
        df = pd.read_csv(url)
        df["SYMBOL"] = df["SYMBOL"].astype(str) + ".NS"  # Convert to Yahoo Finance format
        return set(df["SYMBOL"].tolist())  # Return a set of NSE tickers
    except Exception as e:
        return f"❌ Error fetching NSE stock list: {e}"

# Load BSE Stock List
def get_bse_stock_list():
    try:
        url = "https://www.bseindia.com/download/BhavCopy/Equity/EQ20240322_CSV.ZIP"  # Example ZIP URL
        df = pd.read_csv(url)
        df["SC_CODE"] = df["SC_CODE"].astype(str) + ".BO"  # Convert to Yahoo Finance format
        return set(df["SC_CODE"].tolist())  # Return a set of BSE tickers
    except Exception as e:
        return f"❌ Error fetching BSE stock list: {e}"

# Store all tickers
ALL_NSE_TICKERS = get_nse_stock_list()
ALL_BSE_TICKERS = get_bse_stock_list()
def get_nse_bse_stock_price(company_name):
    """
    Fetches stock price for NSE/BSE-listed Indian companies.
    """
    try:
        company_name = company_name.upper().strip()

        # Check if stock is listed in NSE/BSE
        if f"{company_name}.NS" in ALL_NSE_TICKERS:
            ticker = f"{company_name}.NS"
        elif f"{company_name}.BO" in ALL_BSE_TICKERS:
            ticker = f"{company_name}.BO"
        else:
            return f"❌ Error: '{company_name}' not found in NSE or BSE."

        # Fetch stock price
        stock = yf.Ticker(ticker)
        data = stock.history(period="2d")  # Fetch last 2 days

        if len(data) < 2:
            return f"❌ Error: No valid stock data found for '{company_name}'."

        # Get today's price (latest close)
        current_price = data["Close"].iloc[-1]
        # Get yesterday's closing price
        yesterday_price = data["Close"].iloc[-2]

        # Calculate price change
        price_change = current_price - yesterday_price
        percent_change = (price_change / yesterday_price) * 100
        change_sign = "↑" if price_change > 0 else "↓" if price_change < 0 else "→"

        return (f"📈 {company_name} Stock Price ({ticker}): ₹{current_price:.2f}\n"
                f"📉 Change: {change_sign} ₹{abs(price_change):.2f} ({change_sign} {abs(percent_change):.2f}%)\n"
                f"📊 Yesterday's Close: ₹{yesterday_price:.2f}")

    except Exception as e:
        return f"❌ Error fetching NSE/BSE stock data: {e}"


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
        st.write(get_nse_bse_stock_price(stock_name))  

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