import speech_recognition as sr
import logging
from modules.utils import load_config

class SpeechEngine:
    def __init__(self):
        self.logger = logging.getLogger('SpeechEngine')
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.config = load_config()
        self.adjust_for_noise()

    def adjust_for_noise(self):
        self.logger.info("Adjusting for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        self.logger.info("Adjustment complete.")

    def listen(self):
        """Listens for a single command."""
        try:
            with self.microphone as source:
                self.logger.info("Listening...")
                # timeout: seconds to wait for phrase to start
                # phrase_time_limit: seconds to allow phrase to continue
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
            self.logger.info("Recognizing...")
            text = self.recognizer.recognize_google(audio)
            self.logger.info(f"Recognized: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            self.logger.debug("Listening timed out.")
            return None
        except sr.UnknownValueError:
            self.logger.debug("Could not understand audio.")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Could not request results; {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error in speech recognition: {e}")
            return None
