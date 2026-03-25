"""
Quick fix script to replace all pyautogui calls with safe wrappers in ai_brain.py
"""

import re

# Read the file
with open('modules/ai_brain.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all pyautogui calls with safe wrappers
content = re.sub(r'pyautogui\.hotkey\(', 'safe_hotkey(', content)
content = re.sub(r'pyautogui\.press\(', 'safe_press(', content)
content = re.sub(r'pyautogui\.click\(', 'safe_click(', content)
content = re.sub(r'pyautogui\.moveTo\(', 'safe_move(', content)
content = re.sub(r'pyautogui\.scroll\(', 'safe_scroll(', content)

# Write back
with open('modules/ai_brain.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed all pyautogui calls in ai_brain.py!")
print("All keyboard/mouse operations now use safe wrappers")
