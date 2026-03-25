"""
Command Parser for handling complex, multi-part commands.
Supports chaining commands with "and", "then", "also", etc.
"""

import re
from typing import List, Tuple

class CommandParser:
    """
    Parses complex commands into individual tasks.
    Supports:
    - Command chaining: "do X and do Y"
    - Sequential execution: "do X then do Y"
    - Parallel execution: "do X and also do Y"
    """
    
    # Keywords that indicate command chaining
    CHAIN_KEYWORDS = ['and', 'then', 'also', 'after that', 'next']
    
    @staticmethod
    def is_chained_command(text: str) -> bool:
        """Check if command contains chaining keywords"""
        text_lower = text.lower()
        
        # Check for chaining keywords
        for keyword in CommandParser.CHAIN_KEYWORDS:
            # Look for keyword surrounded by spaces or at boundaries
            pattern = rf'\b{keyword}\b'
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    @staticmethod
    def split_chained_command(text: str) -> List[str]:
        """
        Split a chained command into individual commands.
        
        Example:
            "open notepad and type hello and take screenshot"
            →  ["open notepad", "type hello", "take screenshot"]
        """
        text_lower = text.lower()
        
        # Build pattern to split on all chain keywords
        # Use word boundaries to avoid partial matches
        pattern = r'\b(' + '|'.join(re.escape(kw) for kw in CommandParser.CHAIN_KEYWORDS) + r')\b'
        
        # Split but keep track of what we're splitting on
        parts = re.split(pattern, text, flags=re.IGNORECASE)
        
        # Extract just the command parts (skip the keywords)
        commands = []
        for i, part in enumerate(parts):
            part_stripped = part.strip()
            # Skip empty parts and the chain keywords themselves
            if part_stripped and part_stripped.lower() not in CommandParser.CHAIN_KEYWORDS:
                commands.append(part_stripped)
        
        return commands if len(commands) > 1 else [text.strip()]
    
    @staticmethod
    def parse_command(text: str) -> Tuple[bool, List[str]]:
        """
        Parse a command and determine if it's chained.
        
        Returns:
            (is_chained, list_of_commands)
        """
        is_chained = CommandParser.is_chained_command(text)
        
        if is_chained:
            commands = CommandParser.split_chained_command(text)
            return (True, commands)
        else:
            return (False, [text])
    
    @staticmethod
    def format_command_for_execution(command: str) -> str:
        """
        Clean up a command for execution.
        Removes extra words that might have been left over from splitting.
        """
        # Common words to clean up
        cleanup_words = ['please', 'can you', 'could you', 'nova']
        
        command_lower = command.lower().strip()
        
        for word in cleanup_words:
            # Remove from start
            if command_lower.startswith(word):
                command = command[len(word):].strip()
                command_lower = command.lower()
        
        return command

# Example usage and tests
if __name__ == "__main__":
    test_commands = [
        "open notepad",
        "open notepad and type hello",
        "open chrome then search for python and take screenshot",
        "play music and also open calculator",
        "type hello world then press enter and take screenshot",
    ]
    
    for cmd in test_commands:
        is_chained, commands = CommandParser.parse_command(cmd)
        print(f"\nOriginal: {cmd}")
        print(f"Chained: {is_chained}")
        print(f"Commands: {commands}")
