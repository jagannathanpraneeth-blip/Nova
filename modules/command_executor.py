import os
import subprocess
import webbrowser
import datetime
import logging
import pyautogui
from modules.api_handler import APIHandler
from modules.utils import load_json, DATA_DIR

class CommandExecutor:
    def __init__(self, tts_engine):
        self.logger = logging.getLogger('CommandExecutor')
        self.tts = tts_engine
        self.api = APIHandler()
        self.responses = load_json(os.path.join(DATA_DIR, 'responses.json'))
        self.current_lang = "en"

    def execute(self, intent, text, entities):
        self.logger.info(f"Executing intent: {intent}")
        
        response_dict = self.responses.get(self.current_lang, self.responses['en'])

        if intent == "open_browser":
            self.tts.speak(response_dict.get("browser_opened", "Opening Browser"))
            webbrowser.open("https://google.com")
            
        elif intent == "open_notepad":
            self.tts.speak(response_dict.get("notepad_opened", "Opening Notepad"))
            subprocess.Popen(["notepad.exe"])
            
        elif intent == "open_calculator":
            self.tts.speak(response_dict.get("calculator_opened", "Opening Calculator"))
            subprocess.Popen(["calc.exe"])
            
        elif intent == "open_vscode":
            self.tts.speak(response_dict.get("vscode_opened", "Opening VS Code"))
            # Assuming VS Code is in path or standard location
            try:
                subprocess.Popen(["code"])
            except FileNotFoundError:
                self.tts.speak("VS Code not found in path.")

        elif intent == "open_file_explorer":
            self.tts.speak(response_dict.get("explorer_opened", "Opening File Explorer"))
            subprocess.Popen(["explorer"])

        elif intent == "get_time":
            now = datetime.datetime.now().strftime("%H:%M")
            msg = response_dict.get("time_report", "The time is {}").format(now)
            self.tts.speak(msg)
            return msg

        elif intent == "get_date":
            today = datetime.date.today().strftime("%B %d, %Y")
            msg = response_dict.get("date_report", "Today is {}").format(today)
            self.tts.speak(msg)
            return msg

        elif intent == "get_weather":
            # Extract city from entities or text
            city = entities.get("GPE") or entities.get("LOC")
            if not city:
                # Simple fallback extraction: "weather in London"
                if "in " in text:
                    city = text.split("in ")[1].strip()
                else:
                    city = "New York" # Default
            
            self.tts.speak(f"Checking weather for {city}...")
            result = self.api.get_weather(city)
            self.tts.speak(result)
            return result

        elif intent == "search_google":
            query = text.replace("search google for", "").replace("search for", "").replace("google", "").strip()
            self.tts.speak(response_dict.get("searching", "Searching for {}").format(query))
            webbrowser.open(f"https://www.google.com/search?q={query}")

        elif intent == "search_wikipedia":
            query = text.replace("wikipedia", "").replace("search wikipedia for", "").strip()
            self.tts.speak(response_dict.get("searching", "Searching for {}").format(query))
            result = self.api.search_wikipedia(query)
            self.tts.speak(result)
            return result
            
        elif intent == "change_language":
            if "hindi" in text:
                self.current_lang = "hi"
                self.tts.speak("Language switched to Hindi.")
            else:
                self.current_lang = "en"
                self.tts.speak("Language switched to English.")

        elif intent in ["greeting", "goodbye", "thanks", "identity"]:
            # Pick a random response from intents.json logic (handled here or in main)
            # For now, simple response
            pass # Handled by main loop or specific logic if needed
            
        else:
            self.tts.speak(response_dict.get("unknown", "I didn't understand that."))

    def get_response_text(self, intent):
        # Helper to get text response for simple intents
        # This logic might be better placed in NLPEngine or Main
        pass
