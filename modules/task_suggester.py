import datetime
import json
import os
import random
import logging
from typing import List, Dict, Any

class TaskSuggester:
    """
    Suggests tasks based on time of day, day of week, and user habits.
    """
    
    def __init__(self, data_dir: str):
        self.logger = logging.getLogger('TaskSuggester')
        self.data_file = os.path.join(data_dir, 'user_habits.json')
        self.habits = self._load_habits()
        
    def _load_habits(self) -> Dict[str, Any]:
        """Load user habits/rules from JSON"""
        default_habits = {
            "morning": [
                "Check your emails",
                "Review today's calendar",
                "Read the latest tech news",
                "Start your daily standup"
            ],
            "afternoon": [
                "Focus on coding tasks",
                "Check GitHub notifications",
                "Take a hydration break",
                "Review pull requests"
            ],
            "evening": [
                "Review what you accomplished today",
                "Plan for tomorrow",
                "Study a new Python library",
                "Clean up your workspace"
            ],
            "late_night": [
                "Wrap up your work",
                "Watch a relaxing video",
                "Go to sleep",
                "Commit your final changes"
            ],
            "weekend": [
                "Work on personal projects",
                "Learn something new",
                "Organize your files",
                "Backup your data"
            ]
        }
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load habits: {e}")
                return default_habits
        else:
            return default_habits

    def save_habit(self, time_period: str, task: str):
        """Learn a new habit"""
        if time_period in self.habits:
            if task not in self.habits[time_period]:
                self.habits[time_period].append(task)
                self._save_to_disk()
                
    def _save_to_disk(self):
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.habits, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save habits: {e}")

    def get_suggestion(self) -> str:
        """Get a smart suggestion based on current context"""
        now = datetime.datetime.now()
        hour = now.hour
        is_weekend = now.weekday() >= 5  # 5=Saturday, 6=Sunday
        
        # Determine period
        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 17:
            period = "afternoon"
        elif 17 <= hour < 22:
            period = "evening"
        else:
            period = "late_night"
            
        suggestions = []
        
        # Add period specific tasks
        if period in self.habits:
            suggestions.extend(self.habits[period])
            
        # Add weekend specific if applicable
        if is_weekend and "weekend" in self.habits:
            suggestions.extend(self.habits["weekend"])
            
        if not suggestions:
            return "I don't have any specific suggestions right now."
            
        suggestion = random.choice(suggestions)
        
        # Add some conversational flavor
        prefixes = [
            f"It's {period}, maybe you want to",
            "How about you",
            "You could",
            "Suggested task:",
            "Based on the time, you might want to"
        ]
        
        return f"{random.choice(prefixes)} {suggestion.lower()}."

