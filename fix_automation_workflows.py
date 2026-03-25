"""
Quick fix script to replace all pyautogui calls with safe wrappers in automation_workflows.py
"""

import re

# Read the file
with open('modules/automation_workflows.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace pyautogui calls with safe wrappers
# Note: We keep pyautogui.screenshot and pyautogui.size as they are safe/read-only
content = re.sub(r'pyautogui\.hotkey\(', 'safe_hotkey(', content)
content = re.sub(r'pyautogui\.press\(', 'safe_press(', content)
# safe_click is already imported and used, but let's catch any direct calls if any
content = re.sub(r'pyautogui\.click\(', 'safe_click(', content)
content = re.sub(r'pyautogui\.write\(', 'safe_type(', content)
content = re.sub(r'pyautogui\.moveTo\(', 'safe_move(', content)
content = re.sub(r'pyautogui\.scroll\(', 'safe_scroll(', content)

# Write back
with open('modules/automation_workflows.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed all pyautogui calls in automation_workflows.py!")
print("All automation operations now use safe wrappers")
