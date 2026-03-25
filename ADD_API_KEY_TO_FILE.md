# 🔑 ADD YOUR OPENAI API KEY TO CONFIG FILE

## ✏️ SUPER EASY - EDIT ONE FILE!

### Step 1: Open this file:
```
data/config.json
```

### Step 2: Find this line:
```json
"openai": "YOUR_OPENAI_API_KEY_HERE"
```

### Step 3: Replace `YOUR_OPENAI_API_KEY_HERE` with your actual key:
```json
"openai": "sk-proj-your-actual-key-here"
```

### Step 4: Save the file

### Step 5: Test it:
```powershell
python check_api_key.py
```

---

## 📝 FULL EXAMPLE

Your `data/config.json` should look like this:

```json
{
    "voice_id": "",
    "speech_rate": -1,
    "volume": 1.0,
    "language": "en",
    "wake_word": "nova",
    "user_name": "Sir",
    "api_keys": {
        "weather": "YOUR_API_KEY_HERE",
        "news": "YOUR_API_KEY_HERE",
        "openai": "sk-proj-ABC123xyz..."  ← PUT YOUR KEY HERE!
    }
}
```

---

## ✅ VERIFICATION

After saving, run:
```powershell
python check_api_key.py
```

You should see:
```
✅ Found API key in: data/config.json
✅ Key format looks correct
✅ API key is VALID!
🎉 EVERYTHING IS WORKING PERFECTLY!
```

---

## 🎉 THAT'S IT!

No need to:
- ❌ Set environment variables
- ❌ Use setx commands
- ❌ Restart terminal

Just edit `data/config.json` and you're done! 🚀
