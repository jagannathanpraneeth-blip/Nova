# 🔑 HOW TO ADD YOUR AI BRAIN (API KEY)

Nova is now supercharged with LLM capabilities! You can choose between **Google Gemini** (Often Free) or **OpenAI** (Standard).

## 🚀 OPTION 1: Google Gemini (Recommended for Free Tier)

### Step 1: Get Key
1. Go to: **[Google AI Studio](https://aistudio.google.com/app/apikey)**
2. Click **"Create API key"**
3. Copy the key (starts with `AI...`)

### Step 2: Setup
Double-click `setup_gemini_key.bat` and paste your key!

---

## 💎 OPTION 2: OpenAI (GPT-4o)

### Step 1: Get Key
1. Go to: **[OpenAI Platform](https://platform.openai.com/api-keys)**
2. Create a new key.
3. Copy the key (starts with `sk-...`)

### Step 2: Setup
Double-click `setup_api_key.bat` and paste your key!

---

## 🔄 AFTER SETUP

1. **Restart** your terminal/PowerShell.
2. Run Nova: `python main.py`
3. Try saying:
   - "Nova, open chrome and search for funny cats"
   - "Nova, what should I do next?"
   - "Nova, analyze this screen"

## ❓ FAQ

**Q: Can I use both?**
A: Yes, but Nova will prioritize Gemini if both are set (it's usually faster/cheaper).

**Q: Is it free?**
A: Gemini has a free tier. OpenAI is paid (but very cheap, cents per request).

**Q: I get "API Key not found"?**
A: Make sure you ran the `.bat` file and **restarted** your terminal.
