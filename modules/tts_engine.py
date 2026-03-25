import logging
import threading
from modules.utils import load_config

class TTSEngine:
    def __init__(self):
        self.logger = logging.getLogger('TTSEngine')
        self.config = load_config()
        self.engine = None
        self.enabled = False
        self.setup_voice()

    def setup_voice(self):
        try:
            # Try Windows SAPI (native, no dependencies issues)
            import win32com.client
            self.engine = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Rate: -10 (very slow) to 10 (very fast), default 0
            # -1 to -2 is good for clear, slightly slower speech
            speech_rate = self.config.get('speech_rate', -1)
            # Ensure rate is in valid range
            if speech_rate > 10 or speech_rate < -10:
                speech_rate = -1  # Default to slightly slower
            self.engine.Rate = speech_rate
            
            # Volume: 0 to 100
            self.engine.Volume = int(self.config.get('volume', 1.0) * 100)
            
            # Try to set a clear voice (prefer female voices which are often clearer)
            try:
                voices = self.engine.GetVoices()
                for i in range(voices.Count):
                    voice = voices.Item(i)
                    voice_name = voice.GetDescription()
                    # Prefer David (male) or Zira (female) for clarity
                    if "David" in voice_name or "Zira" in voice_name:
                        self.engine.Voice = voice
                        self.logger.info(f"Using voice: {voice_name}")
                        break
            except:
                pass  # Use default voice if selection fails
            
            self.enabled = True
            self.logger.info(f"TTS Engine initialized successfully (Windows SAPI, Rate: {speech_rate})")
        except Exception as e:
            self.logger.error(f"Error setting up TTS engine: {e}")
            self.logger.warning("TTS disabled - commands will execute silently")
            self.enabled = False

    def speak(self, text):
        """Speaks text using Windows SAPI"""
        if not self.enabled:
            self.logger.info(f"[TTS Disabled] Would say: {text}")
            return
            
        self.logger.info(f"Speaking: {text}")
        thread = threading.Thread(target=self._speak_thread, args=(text,))
        thread.daemon = True
        thread.start()

    def _speak_thread(self, text):
        if not self.enabled or not self.engine:
            return
            
        try:
            self.engine.Speak(text)
        except Exception as e:
            self.logger.error(f"Error in speech thread: {e}")

    def stop(self):
        if self.enabled and self.engine:
            try:
                self.engine.Speak("", 2)  # SVSFPurgeBeforeSpeak flag
            except:
                pass

