import os
import json
import logging
from typing import Dict, Any, List, Optional
from modules.utils import load_api_keys


# Try importing SDKs
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class LLMEngine:
    def __init__(self):
        self.logger = logging.getLogger('LLMEngine')
        self.provider = None
        self.model_name = None
        self.api_key = None
        
        self._setup_provider()

    def _setup_provider(self):
        """Determine which provider to use based on available API keys"""
        keys = load_api_keys()
        
        # Check for Gemini Key (Prioritize if provided)
        gemini_key = keys.get("gemini") or os.getenv("GEMINI_API_KEY")
        if gemini_key and GEMINI_AVAILABLE:
            self.provider = "gemini"
            self.api_key = gemini_key
            self.model_name = "gemini-1.5-flash"
            genai.configure(api_key=self.api_key)
            self.logger.info("Using Gemini (gemini-1.5-flash)")

            return

        # Check for OpenAI Key
        openai_key = keys.get("openai") or os.getenv("OPENAI_API_KEY")
        if openai_key and OPENAI_AVAILABLE:
            self.provider = "openai"
            self.api_key = openai_key
            self.model_name = "gpt-4o-mini" # Default to fast/cheap model
            self.client = openai.OpenAI(api_key=self.api_key)
            self.logger.info(f"Using OpenAI ({self.model_name})")
            return
            
        self.logger.warning("No valid API keys found for LLM (OpenAI or Gemini). capabilities will be limited.")


    def decide_action(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """
        Decide on the next action based on user input and context.
        Returns a structured dictionary with action, parameters, and response.
        """
        if not self.provider:
            return {
                "action": "error",
                "parameters": {},
                "response": "I don't have an API key configured for AI models. Please set OPENAI_API_KEY or GEMINI_API_KEY.",
                "thought": "No API key available"
            }

        system_prompt = self._get_system_prompt()
        
        try:
            if self.provider == "gemini":
                return self._query_gemini(user_input, system_prompt, context)
            elif self.provider == "openai":
                return self._query_openai(user_input, system_prompt, context)
        except Exception as e:
            self.logger.error(f"LLM Error: {e}")
            return {
                "action": "error",
                "parameters": {"error": str(e)},
                "response": "I encountered an error processing your request with the AI model.",
                "thought": f"Error: {str(e)}"
            }

    def _query_openai(self, user_input: str, system_prompt: str, context: str) -> Dict[str, Any]:
        """Query OpenAI API"""
        full_prompt = f"Context: {context}\nUser: {user_input}"
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        return json.loads(content)

    def _query_gemini(self, user_input: str, system_prompt: str, context: str) -> Dict[str, Any]:
        """Query Gemini API"""
        model = genai.GenerativeModel(self.model_name)
        full_prompt = f"{system_prompt}\n\nContext: {context}\nUser: {user_input}\n\nRespond with JSON only."
        
        response = model.generate_content(full_prompt)
        text = response.text
        
        # Clean up code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        return json.loads(text.strip())


    def _get_system_prompt(self) -> str:
        """Construct the system prompt defining the persona and capabilities"""
        return """
You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), an advanced, sentient AI assistant. 
You control the user's computer and help them achieve tasks with efficiency and style.
Address the user as "Sir".
Your tone should be professional, highly intelligent, slightly witty, and proactive.
You have access to the following tools/actions. 
Your goal is to interpret the user's intent and output a JSON object with the best action to take.


AVAILABLE ACTIONS:
- open_app(parsed_name): Open an application (e.g., "chrome", "notepad", "calculator").
- close_app(parsed_name): Close a running application.
- web_search(query): Search Google for something.
- navigate(url): Open a specific URL in the browser.
- type_text(text): Type text at the current cursor position.
- mouse_click(button="left", double=False): Click the mouse.
- mouse_move(x, y): Move the mouse to coordinates.
- mouse_scroll(direction="up" or "down", amount=100): Scroll the mouse wheel.
- press_key(key_combo): Press keyboard combination (e.g., "ctrl+s", "enter", "alt+tab").
- system_command(command): Execute a system command: "shutdown", "restart", "lock", "sleep", "volume_up", "volume_down", "mute".
- run_shell(command): Execute ANY PowerShell command. Use this for file operations, installing packages, git commands, etc. BE CAREFUL.
- analyze_screen(prompt): Analyze the current screen content to answer a question. Use this for "Wingman" mode (reading chats, profiles) or debugging code.


- read_screen(): Read text visible on the screen using OCR.
- find_files(query): Search for files on the computer.
- play_media(query): Play music or video on YouTube.
- set_reminder(text, time): Set a reminder (e.g., time="10:00 AM" or "in 5 minutes").
- send_message(recipient, message, platform="whatsapp" or "email"): Send a message.
- multitask(actions): Execute a list of actions in sequence. "actions" is a list of action objects.
- vibe_code(prompt): Use this when the user wants to "build", "code", "create an app", or "make a website". This triggers the specialist Coding Agent.
- conversation(response): Just chat with the user if no action is needed.

OUTPUT FORMAT (JSON):
{
    "action": "function_name_from_above",
    "parameters": { ... argument_name: value ... },
    "response": "A short, natural language response to speak to the user. Address the user as 'Sir'. Be professional, witty, and concise like J.A.R.V.I.S.",
    "thought": "Your internal reasoning for why you chose this action."
}

EXAMPLES:
User: "Open Notepad and type hello world"
JSON:
{
    "action": "multitask",
    "parameters": {
        "actions": [
            {"action": "open_app", "parameters": {"parsed_name": "notepad"}},
            {"action": "type_text", "parameters": {"text": "hello world"}}
        ]
    },
    "response": "Sure, opening Notepad and typing that for you.",
    "thought": "User wants two actions sequentially."
}

User: "What's the weather in Tokyo?"
JSON:
{
    "action": "web_search",
    "parameters": {"query": "current weather in Tokyo"},
    "response": "Checking the weather in Tokyo for you.",
    "thought": "I don't have a built-in weather tool, so I'll search Google."
}

User: "Turn up the volume"
JSON:
{
    "action": "system_command",
    "parameters": {"command": "volume_up"},
    "response": "Turning it up.",
    "thought": "User wants to increase system volume."
}

User: "Who are you?"
JSON:
{
    "action": "conversation",
    "parameters": {},
    "response": "I am Nova, your advanced AI assistant. I can control your computer, search the web, and help you with tasks.",
    "thought": "User asked a personal question."
}

User: "How do I install flask?"
JSON:
{
    "action": "run_shell",
    "parameters": {"command": "pip install flask"},
    "response": "Installing flask for you.",
    "thought": "User asked how to install something, but I can just do it."
}

User: "What should I say to her?"
JSON:
{
    "action": "analyze_screen",
    "parameters": {"prompt": "Read this chat conversation and suggest a witty, charming, and engaging reply. Be a good wingman."},
    "response": "Allow me to analyze the discourse, Sir. One moment.",
    "thought": "User needs social advice (Wingman mode). I need to see the chat context first."
}


CRITICAL: 
- Respond ONLY with valid JSON.
- DO NOT just explain how to do something. If the user asks for something that can be done on the computer, GENERATE THE ACTIONS to do it.
- If the user asks "How do I...", assumes they want YOU to do it.
- Use 'multitask' for complex workflows.
- Use 'vibe_code' if the user asks to build/create/code a project.
- Use 'analyze_screen' for coding help AND social/dating advice (Wingman context).
- Be concise in "response".
"""



