# 🌐 Social Media & API Setup Guide

## 1️⃣ API Keys (The Master File)

Nova now uses a single file for all your secrets.

**File:** `data/api_keys.json`

Open this file and fill in:
- `"openai"`: Your OpenAI Key (sk-...)
- `"gemini"`: Your Gemini Key (AI...)
- `"weather_api"`: (Optional) OpenWeatherMap key
- `"news_api"`: (Optional) NewsAPI key

*Note: The old setup scripts still work to set environment variables, but this JSON file is preferred.*

## 2️⃣ Social Media Boundaries

You can control what Nova is allowed to do on social apps.

**File:** `data/social_media_policies.json`

### Example Config:
```json
{
    "permissions": {
        "whatsapp": {
            "send_messages": true,   // Allow sending
            "read_messages": false   // Don't allow reading (privacy)
        },
        "instagram": {
            "post_content": false,   // Don't allow posting without me
            "send_dm": true          // direct messages ok
        }
    },
    "boundaries": {
        "whatsapp": {
            "max_messages_per_day": 20,
            "allowed_hours": {
                "start": 9,  // 9 AM
                "end": 22    // 10 PM
            }
        }
    }
}
```

## 3️⃣ How to Use

Nova will check these rules *before* opening the apps or taking action.

- "Nova, send a WhatsApp message" -> Checks if `send_messages` is true.
- "Nova, post to Instagram" -> Checks if `post_content` is true.
- If it's 3 AM -> "Sorry, outside allowed hours."

Enjoy your safe and controlled assistant! 🛡️
