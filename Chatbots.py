import requests
import re
import yfinance as yf
import streamlit as st
from dotenv import load_dotenv
import os
load_dotenv()
# API URLs
NEWS_URL = "https://newsapi.org/v2/top-headlines"
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
GEOCODE_URL = "http://api.openweathermap.org/geo/1.0/direct"

# API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Debug mode (Set to False to disable debug messages)
DEBUG_MODE = False

# Function to get real-time news
def get_news(category="general", country="in"):
    params = {"category": category, "apiKey": NEWS_API_KEY, "country": country}
    response = requests.get(NEWS_URL, params=params).json()
    
    if DEBUG_MODE:
        print("[DEBUG] News API Response Status:", response.get("status"))
        print("[DEBUG] Total Results:", response.get("totalResults", 0))
    
    if "status" in response and response["status"] != "ok":
        return f"Error fetching news: {response.get('message', 'Unknown error')}"
    
    if "articles" in response and response["articles"]:
        return "\n".join([f"{i+1}. {article['title']} - {article['source']['name']}"
                            for i, article in enumerate(response["articles"][:5])])
     # Try fetching global news if no articles are found in India
    if country == "in":
        return get_news(category, country=None)
    
    return "No news available at the moment. Try again later."

# Function to get coordinates for a location
def get_coordinates(location):
    params = {"q": location, "limit": 1, "appid": WEATHER_API_KEY}
    response = requests.get(GEOCODE_URL, params=params).json()
    
    if not response or len(response) == 0:
        return None, None
    
    lat, lon = response[0].get("lat"), response[0].get("lon")
    if lat is None or lon is None:
        return None, None
    
    return lat, lon

# Function to get real-time weather forecast for any location in India
def get_weather(location="Delhi"):
    lat, lon = get_coordinates(location)
    
    if lat is None or lon is None:
        return f"Location '{location}' not found. Try entering a major city, district, or state in India."
    
    params = {"lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": "metric"}
    response = requests.get(WEATHER_URL, params=params).json()
    
    if "main" not in response:
        return "Weather data not available. Please try another location."
    
    temp = response["main"].get("temp", "N/A")
    description = response["weather"][0].get("description", "N/A")
    return f"Weather in {location}: {temp}°C, {description}."

# Function to get stock price using Yahoo Finance
def get_stock_symbol(company_name):
    """Fetches the stock symbol using the company name from Yahoo Finance API."""
    try:
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={company_name}"
        response = requests.get(url)
        data = response.json()
        
        if "quotes" in data and data["quotes"]:
            return data["quotes"][0]["symbol"]  # Return the first matched symbol
        return None
    except Exception as e:
        return None

def format_stock_symbol(symbol):
    """Ensures the correct format for Indian stock symbols (NSE/BSE)."""
    if "." not in symbol and symbol.isalpha():  # If no exchange suffix, assume NSE first
        return symbol + ".NS"
    return symbol

def get_stock_price(company_name_or_symbol):
    try:
        symbol = company_name_or_symbol.upper()
        if not symbol.isalpha():  # If it's not a direct symbol, find by name
            symbol = get_stock_symbol(company_name_or_symbol) or company_name_or_symbol
        
        symbol = format_stock_symbol(symbol)  # Ensure correct exchange format
        stock = yf.Ticker(symbol)
        stock_info = stock.history(period="1d")
        
        if stock_info.empty:
            return f"Stock data not available for {symbol}. Please check the company name or symbol."
        
        latest_price = stock_info["Close"].iloc[-1]
        return f"Latest stock price of {symbol}: ₹{latest_price:.2f}"
    except Exception as e:
        return f"Stock data retrieval failed: {str(e)}"

def get_stock_change(company_name_or_symbol, period):
    """Fetches the stock price change over a given period (1d, 1mo, 1y)."""
    try:
        symbol = company_name_or_symbol.upper()
        if not symbol.isalpha():
            symbol = get_stock_symbol(company_name_or_symbol) or company_name_or_symbol
        
        symbol = format_stock_symbol(symbol)  # Ensure correct exchange format
        stock = yf.Ticker(symbol)
        stock_info = stock.history(period=period)
        
        if stock_info.empty or len(stock_info) < 2:
            return f"Not enough data to calculate stock price change for {symbol}."
        
        old_price = stock_info["Close"].iloc[0]
        latest_price = stock_info["Close"].iloc[-1]
        change = latest_price - old_price
        change_percent = (change / old_price) * 100
        
        return f"Stock price change for {symbol} over {period}: ₹{change:.2f} ({change_percent:.2f}%)"
    except Exception as e:
        return f"Stock change retrieval failed: {str(e)}"

def parse_stock_change_query(user_input):
    """Extracts company name and time period from user query."""
    match = re.search(r"(?:stock change|change in stock of|change of|price change)\s+(.*?)\s+(?:in|over|around)?\s*(\d+\s*(?:day|month|year|d|mo|y))", user_input)
    if match:
        company = match.group(1).strip()
        period = match.group(2).strip()
        period = period.replace(" day", "d").replace(" month", "mo").replace(" year", "y")  # Normalize time units
        return company, period
    return None, None
def chatbot():
    st.title("Real-Time News, Weather & Stock Chatbot")
    st.write("Type 'news' for latest news, 'news CATEGORY' for specific category, 'weather LOCATION' for weather, 'stock SYMBOL/COMPANY' for stock price, 'stock change SYMBOL/COMPANY PERIOD' for stock change.")
    
    user_input = st.text_input("You:")
    if user_input:
        user_input = user_input.strip().lower()
        if "news" in user_input:
            match = re.search(r"news(.*)", user_input)
            category = match.group(1).strip() if match else "general"
            st.write(f"Latest {category.capitalize()} News: \n{get_news(category)}")
        elif "weather" in user_input:
            match = re.search(r"weather(.*)", user_input)
            location = match.group(1).strip() if match else "Delhi"
            st.write(f"Weather: {get_weather(location)}")
        elif re.search(r"stock change|change in stock of|change of|price change", user_input):
            company_or_symbol, period = parse_stock_change_query(user_input)
            if company_or_symbol and period:
                st.write(f"Change in stock price", get_stock_change(company_or_symbol, period))
            else:
                st.write("Chatbot: Please specify a valid company name and time period (e.g., 'stock change TCS 1 year').")
        elif re.search(r"stock|price of", user_input):
            match = re.search(r"(?:stock|price of)(.*)", user_input)
            company_or_symbol = match.group(1).strip() if match else ""
            if company_or_symbol:
                st.write(f"Stock Price: {get_stock_price(company_or_symbol)}")
            else:
                st.write("Chatbot: Please specify a company name or stock symbol.")
        else:
            st.write("Chatbot: I can provide news, weather, and stock prices. Try asking again!")

if __name__ == "__main__":
    chatbot()