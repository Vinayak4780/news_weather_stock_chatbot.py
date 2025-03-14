import requests
import re
import yfinance as yf
import streamlit as st
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_random_user_agent():
    """Get a random user agent to avoid detection."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    ]
    return random.choice(user_agents)

def get_times_of_india_headlines() -> List[Dict[str, str]]:
    """
    Fetch top headlines from Times of India.
    
    Returns:
        List[Dict[str, str]]: List of headlines with their details
    """
    try:
        # Try different URLs
        urls = [
            "https://timesofindia.indiatimes.com/india"  # India news section
            "https://timesofindia.indiatimes.com/briefs",  # News briefs
            "https://timesofindia.indiatimes.com"         # Homepage
        ]
        
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,/;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        headlines = []
        
        for url in urls:
            if len(headlines) >= 5:
                break
                
            logger.info(f"Trying URL: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # List of CSS selectors to try
            selectors = [
                '.top-story .w_tle',        # Top stories
                '.headlines-list .w_tle',    # Headlines list
                '.briefs-list .w_tle',      # News briefs
                '.main-content .w_tle',      # Main content
                'span.w_tle',               # General headlines
                '.article-box h3',          # Article headlines
                '.news-card h3',            # News cards
                '.brief_box h3',            # Brief boxes
                'h2 a',                     # Generic headline links
                '.story-card h3',           # Story cards
            ]
            
            for selector in selectors:
                if len(headlines) >= 5:
                    break
                    
                elements = soup.select(selector)
                logger.info(f"Found {len(elements)} elements with selector: {selector}")
                
                for element in elements:
                    # Get the headline text
                    title = element.get_text(strip=True)
                    
                    # Get the link
                    link = None
                    if element.name == 'a':
                        link = element.get('href')
                    else:
                        link_element = element.find_parent('a') or element.find('a')
                        if link_element:
                            link = link_element.get('href')
                    
                    # Make sure the link is absolute
                    if link and not link.startswith('http'):
                        link = f"https://timesofindia.indiatimes.com{link}"
                    
                    # Only add non-empty, unique headlines
                    if title and title not in [h['title'] for h in headlines]:
                        headlines.append({
                            'title': title,
                            'link': link
                        })
                        logger.info(f"Found headline: {title}")
                    
                    if len(headlines) >= 5:
                        break
        
        if headlines:
            logger.info(f"Successfully found {len(headlines)} headlines")
            return format_headlines(headlines[:5])
        else:
            logger.warning("No headlines found")
            return "No headlines found. The website structure might have changed."
            
    except requests.exceptions.Timeout:
        logger.error("Request timed out")
        return "Request timed out. The server might be slow or unavailable."
    except requests.exceptions.ConnectionError:
        logger.error("Connection error occurred")
        return "Connection error. Please check your internet connection or the website might be down."
    except Exception as e:
        logger.error(f"Error fetching headlines: {str(e)}")
        return f"Error: {str(e)}"

def format_headlines(headlines: List[Dict[str, str]]) -> str:
    """Format headlines for display"""
    formatted = []
    for i, h in enumerate(headlines, 1):
        headline = f"{i}. {h['title']}"
        if h.get('link'):
            headline += f"\n   Link: {h['link']}"
        formatted.append(headline)
    
    return "\n\n".join(formatted)

# Debug mode (Set to False to disable debug messages)
DEBUG_MODE = False
# Function to get weather data from wttr.in without API key
def get_weather(location="Delhi"):
    try:
        # Fetch the weather data using wttr.in for the given location
        response = requests.get(f"https://wttr.in/{location}?format=%C+%t")
        
        # If the request is successful (status code 200)
        if response.status_code == 200:
            return f"Weather in {location}: {response.text}"
        else:
            return f"Error fetching weather for {location}."
    
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather: {str(e)}"

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
    st.write("Type 'news' for latest news, 'news' for specific category, 'weather LOCATION' for weather, 'stock SYMBOL/COMPANY' for stock price, 'stock change SYMBOL/COMPANY PERIOD' for stock change.")
    
    user_input = st.text_input("You:")
    if user_input:
        user_input = user_input.strip().lower()
        if "news" in user_input:
            st.write(f"Latest Times of India Headlines: \n{get_times_of_india_headlines()}")
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
