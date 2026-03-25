import requests
import wikipedia
import logging
from modules.utils import load_config

class APIHandler:
    def __init__(self):
        self.logger = logging.getLogger('APIHandler')
        self.config = load_config()
        self.weather_api_key = self.config.get('api_keys', {}).get('weather', '')
        self.news_api_key = self.config.get('api_keys', {}).get('news', '')

    def get_weather(self, city):
        if not self.weather_api_key:
            return "Weather API key is missing."
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric"
            response = requests.get(url)
            data = response.json()
            
            if data["cod"] != "404":
                main = data["main"]
                weather = data["weather"][0]
                temp = main["temp"]
                desc = weather["description"]
                return f"{temp} degrees Celsius with {desc}"
            else:
                return "City not found."
        except Exception as e:
            self.logger.error(f"Weather API error: {e}")
            return "Could not fetch weather data."

    def search_wikipedia(self, query, sentences=2):
        try:
            result = wikipedia.summary(query, sentences=sentences)
            return result
        except wikipedia.exceptions.DisambiguationError as e:
            return "There are multiple results for that query. Please be more specific."
        except wikipedia.exceptions.PageError:
            return "I couldn't find any page matching that query."
        except Exception as e:
            self.logger.error(f"Wikipedia error: {e}")
            return "Error searching Wikipedia."

    def get_news(self, limit=5):
        if not self.news_api_key:
            return "News API key is missing."
            
        try:
            url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={self.news_api_key}"
            response = requests.get(url)
            data = response.json()
            
            if data["status"] == "ok":
                articles = data["articles"][:limit]
                headlines = [article["title"] for article in articles]
                return headlines
            else:
                return "Could not fetch news."
        except Exception as e:
            self.logger.error(f"News API error: {e}")
            return "Error fetching news."
