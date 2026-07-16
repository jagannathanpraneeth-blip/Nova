"""
Nova Communication Agent
========================
Handles communication tasks: sending WhatsApp messages, composing Gmail,
and setting system reminders.
"""

import webbrowser
import urllib.parse
import subprocess
import logging
import time
import re
from typing import Dict, Any

from modules.agents.agent_base import Agent


class CommunicationAgent(Agent):
    """Agent responsible for messaging, emails, and reminders."""

    def __init__(self, tts=None, **kwargs):
        super().__init__(
            name="CommunicationAgent",
            description="Handles messaging (WhatsApp), email composition, and scheduling notifications/reminders.",
            **kwargs
        )
        self.tts = tts
        self.capabilities = ["send_whatsapp", "send_email", "set_reminder"]

    def _do_execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "")
        params = task.get("parameters", {})
        raw_text = params.get("raw_text", task.get("original_text", ""))

        if action == "send_whatsapp":
            return self._send_whatsapp(params, raw_text)
        elif action == "send_email":
            return self._send_email(params, raw_text)
        elif action == "set_reminder":
            return self._set_reminder(params, raw_text)

        return {"success": False, "message": f"Unknown action: {action}", "action": action}

    def _send_whatsapp(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        contact = params.get("contact", "")
        message = params.get("message", "")

        # Try parsing from raw_text if empty
        if not contact or not message:
            text = raw_text.lower()
            if "to" in text:
                parts = text.split("to", 1)[1].strip()
                if "saying" in parts:
                    contact = parts.split("saying")[0].strip()
                    message = parts.split("saying")[1].strip()
                elif "message" in parts:
                    contact = parts.split("message")[0].strip()
                    msg_part = parts.split("message")[1].strip()
                    if msg_part:
                        message = msg_part
                else:
                    contact = parts
                    message = "Hello"
            elif "saying" in text:
                message = text.split("saying")[1].strip()

        if not message:
            message = "Hello"

        if self.tts:
            self.tts.speak(f"Sending WhatsApp message to {contact}")

        try:
            encoded_message = urllib.parse.quote(message)
            url = f"https://web.whatsapp.com/send?text={encoded_message}"
            if contact:
                # If contact name/number is provided
                url = f"https://web.whatsapp.com/send?phone={contact}&text={encoded_message}"

            webbrowser.open(url)
            time.sleep(5)
            if self.tts:
                self.tts.speak("Opening WhatsApp Web, sending in progress.")
            time.sleep(3)

            # Auto-send (press enter)
            from modules.pyautogui_config import safe_press
            safe_press('enter')

            msg = "Message sent successfully"
            if self.tts:
                self.tts.speak(msg)
            return {"success": True, "message": f"WhatsApp sent to {contact}", "action": "send_whatsapp"}
        except Exception as e:
            self.logger.error(f"WhatsApp message failed: {e}")
            return {"success": False, "message": str(e), "action": "send_whatsapp"}

    def _send_email(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        to = params.get("to", "")
        subject = params.get("subject", "")
        body = params.get("body", "")

        # Fallback parsing
        if not to:
            text = raw_text.lower()
            if "to" in text:
                to_part = text.split("to")[1].strip()
                if "subject" in to_part:
                    to = to_part.split("subject")[0].strip()
                    subject_part = to_part.split("subject")[1].strip()
                    if "body" in subject_part or "saying" in subject_part:
                        subject = subject_part.split("body")[0] if "body" in subject_part else subject_part.split("saying")[0]
                        body = subject_part.split("body")[1] if "body" in subject_part else subject_part.split("saying")[1]
                    else:
                        subject = subject_part
                else:
                    to = to_part

        try:
            url = "https://mail.google.com/mail/?view=cm&fs=1"
            if to:
                url += f"&to={urllib.parse.quote(to)}"
            if subject:
                url += f"&su={urllib.parse.quote(subject)}"
            if body:
                url += f"&body={urllib.parse.quote(body)}"

            webbrowser.open(url)
            msg = "Opening Gmail compose window"
            if self.tts:
                self.tts.speak(msg)
            return {"success": True, "message": msg, "action": "send_email"}
        except Exception as e:
            self.logger.error(f"Gmail composition failed: {e}")
            return {"success": False, "message": str(e), "action": "send_email"}

    def _set_reminder(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        reminder_text = params.get("text", raw_text)
        minutes = params.get("time", 5)

        if isinstance(minutes, str):
            # Parse minutes from string
            try:
                minutes = int(re.search(r'\d+', minutes).group())
            except:
                minutes = 5

        # Fallback parsing from text
        time_patterns = [
            (r'in (\d+) minutes?', 1),
            (r'in (\d+) hours?', 60),
            (r'after (\d+) minutes?', 1),
            (r'after (\d+) hours?', 60),
        ]
        for pattern, multiplier in time_patterns:
            match = re.search(pattern, raw_text.lower())
            if match:
                minutes = int(match.group(1)) * multiplier
                reminder_text = re.sub(pattern, '', raw_text.lower()).strip()
                break

        # Clean reminder text
        reminder_text = reminder_text.replace("remind me", "").replace("to", "").replace("that", "").strip()

        try:
            msg_text = f"Reminder: {reminder_text}"
            ps_command = f'''
            Start-Sleep -Seconds {minutes * 60}
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.MessageBox]::Show("{msg_text}", "Nova Reminder")
            '''

            subprocess.Popen(['powershell', '-Command', ps_command],
                             creationflags=subprocess.CREATE_NO_WINDOW)

            msg = f"Reminder set for {minutes} minutes from now"
            if self.tts:
                self.tts.speak(msg)
            return {"success": True, "message": msg, "action": "set_reminder"}
        except Exception as e:
            self.logger.error(f"Reminder creation failed: {e}")
            return {"success": False, "message": str(e), "action": "set_reminder"}
