# Nova - Quick Command Reference

## 🚀 NEW COMMANDS (The "Fire" Update)

| What You Want | Say This |
|---------------|----------|
| **Install Extensions** | "Nova install VS Code extensions for web dev" |
| **Setup Project** | "Nova set up a new project folder" |
| **Download Docs** | "Nova download react docs" |
| **Delete File** | "Nova delete the last file I downloaded" |
| **Repeat Action** | "Do that again" |

## 🖥️ SCREEN ANALYSIS COMMANDS

| What You Want | Say This |
|---------------|----------|
| Analyze what's on screen | "Nova, analyze screen" |
| Read screen text | "Nova, read screen" |
| Describe screen content | "Nova, describe what you see" |
| Find something on screen | "Nova, find the submit button on screen" |
| What's displayed | "Nova, what's on screen?" |

## ⌨️ DICTATION COMMANDS

### Starting & Stopping
| What You Want | Say This |
|---------------|----------|
| Start dictation mode | "Nova, start dictation" |
| Stop dictation mode | "stop dictation" (anytime) |
| Type once | "Nova, voice type hello world" |
| Type and press Enter | "Nova, voice type hello and send" |

### Punctuation (While Dictating)
| Say This | Types This |
|----------|-----------|
| period | . |
| comma | , |
| question mark | ? |
| exclamation mark | ! |
| colon | : |
| semicolon | ; |
| dash | - |
| quote | " |
| new line | ↵ |
| new paragraph | ↵↵ |

## 📋 QUICK EXAMPLES

### Advanced Automation:
```
"Nova install VS Code extensions for python"
→ Opens VS Code, installs Python extensions, reloads window.

"Nova set up a new project folder"
→ Creates folder on Desktop, opens VS Code, inits Git, creates starter files.

"Nova delete the last file I downloaded"
→ Checks Downloads folder and deletes the newest file.
```

### Screen Analysis:
```
"Nova, analyze screen"
→ AI describes what's on your screen

"Nova, read my screen"
→ Reads all text visible on screen
```

### Dictation:
```
"Nova, start dictation"
→ Start continuous voice typing

[While dictating:]
"Hello team comma new line new line I have an important update period"
→ Types: "Hello team,\n\nI have an important update."

"stop dictation"
→ Exits dictation mode
```

## ⚙️ SETUP

### For Screen Analysis (Optional):
1. Get OpenAI API key: https://platform.openai.com/api-keys
2. Set environment variable:
   ```powershell
   $env:OPENAI_API_KEY = "sk-your-key-here"
   ```

### For Dictation:
No setup needed! Works immediately after installation.

## 💡 TIPS

1. **Safety First**: Nova will ask for confirmation before deleting files or uninstalling apps.
2. **Memory**: You can say "Do that again" to repeat the last command.
3. **Self-Healing**: If an automation task fails, Nova will try to fix it automatically.

---

**Need help?** Check FEATURES.md for detailed documentation!
